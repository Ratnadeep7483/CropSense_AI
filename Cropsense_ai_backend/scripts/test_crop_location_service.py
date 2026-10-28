#!/usr/bin/env python3
"""Tests for dataset-backed crop locations, areas, and model feature rows."""

import csv
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402
from app.services.crop_location_service import (  # noqa: E402
    CropLocationDatasetError,
    CropLocationService,
    HistoricalCropFeaturesUnavailable,
    HistoricalCropRecordAmbiguous,
    HistoricalCropRecordNotFound,
    MODEL_FEATURE_COLUMNS,
)
from app.services.crop_service import FEATURE_COLUMNS  # noqa: E402


class FakeCropService:
    is_loaded = True
    load_error = None
    received = None

    def load_model(self) -> None:
        pass

    def predict(self, request):
        self.received = request
        return "Predicted crop"


class CropLocationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.dataset_path = Path(self.temp.name) / "crop_features.csv"
        self._write_rows(
            [
                ["Example State", "Sample District", "Kharif", "Alluvial", "Rice", 10, 20, 30, 21, 61, 500, 2010, 10, "dataset_57"],
                ["Example State", "Sample District", "Kharif", "Alluvial", "Rice", 10, 20, 30, 21, 61, 500, 2010, 10, "dataset_57"],
                ["Example State", "Sample District", "Rabi", "Black", "Wheat", 11, 21, 31, 22, 62, 600, 2011, 20, "merged_51"],
                ["Example State", "Sample District", "Rabi", "Black", "Maize", 12, 22, 32, 23, 63, 700, 2012, 30, "dataset_57"],
                ["Example State", "Sample District", "Rabi", "Black", "Maize", 12, 22, 32, 23, 63, 700, 2012, 31, "dataset_57"],
                ["Example State", "Sample District", "Rabi", "Black", "Barley", "", "", "", "", "", "", 2013, "", "dataset_57"],
                ["Other State", "Sample District", "Winter", "Alluvial", "Rice", 13, 23, 33, 24, 64, 800, 2010, 99, "dataset_57"],
                ["Example State", "Other District", "Summer", "Alluvial", "Rice", 14, 24, 34, 25, 65, 900, 2010, 88, "dataset_57"],
            ]
        )
        self.service = CropLocationService(self.dataset_path)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_rows(self, rows: list[list[object]]) -> None:
        with self.dataset_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.writer(target)
            writer.writerow(
                [
                    "state_names",
                    "district_names",
                    "season_names",
                    "soil_for_crop",
                    "crop_names",
                    "N",
                    "P",
                    "K",
                    "temperature",
                    "humidity",
                    "rainfall_mm",
                    "crop_year",
                    "area",
                    "npk_source",
                ]
            )
            writer.writerows(rows)

    def test_state_district_and_season_options_are_scoped_to_dataset_records(self) -> None:
        states, districts, seasons = self.service.get_options()
        self.assertEqual(states, ["Example State", "Other State"])
        self.assertEqual(districts, [])
        self.assertEqual(seasons, [])

        _, districts, seasons = self.service.get_options("Example State")
        self.assertEqual(districts, ["Other District", "Sample District"])
        self.assertEqual(seasons, [])

        _, districts, seasons = self.service.get_options(
            "Example State", "Sample District"
        )
        self.assertEqual(districts, ["Other District", "Sample District"])
        self.assertEqual(seasons, ["Kharif", "Rabi"])

    def test_historical_area_records_filter_by_exact_season_and_keep_units(self) -> None:
        records = self.service.get_historical_area(
            "Example State", "Sample District", "Kharif"
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["crop"], "Rice")
        self.assertEqual(records[0]["soil_for_crop"], "Alluvial")
        self.assertEqual(records[0]["area_hectares"], 10.0)
        self.assertEqual(records[0]["status"], "available")
        self.assertEqual(records[0]["matching_records"], 2)
        self.assertEqual(
            (records[0]["N"], records[0]["P"], records[0]["K"]),
            (10.0, 20.0, 30.0),
        )
        self.assertEqual(
            (
                records[0]["temperature"],
                records[0]["humidity"],
                records[0]["rainfall_mm"],
            ),
            (21.0, 61.0, 500.0),
        )

        self.assertEqual(
            {record["crop"] for record in self.service.get_historical_area(
                "Example State", "Sample District", "Rabi"
            )},
            {"Barley", "Maize", "Wheat"},
        )
        self.assertEqual(
            self.service.get_historical_area(
                "Example State", "Sample District", "Winter"
            ),
            [],
        )

    def test_area_and_features_report_missing_or_conflicting_values(self) -> None:
        records = self.service.get_historical_area(
            "Example State", "Sample District", "Rabi"
        )
        by_crop = {record["crop"]: record for record in records}
        self.assertEqual(by_crop["Maize"]["status"], "ambiguous")
        self.assertEqual(
            by_crop["Maize"]["feature_issues"]["area"],
            "conflicting dataset records",
        )
        self.assertEqual(by_crop["Barley"]["status"], "missing")
        self.assertEqual(by_crop["Barley"]["feature_issues"]["N"], "missing")

    def test_model_input_uses_exact_twelve_training_features(self) -> None:
        self.assertEqual(tuple(FEATURE_COLUMNS), MODEL_FEATURE_COLUMNS)
        record = self.service.get_model_record(
            "Example State",
            "Sample District",
            "Kharif",
            "Rice",
            2010,
            "Alluvial",
        )
        self.assertEqual(tuple(record["model_inputs"]), MODEL_FEATURE_COLUMNS)
        self.assertEqual(
            record["model_inputs"],
            {
                "state_names": "Example State",
                "district_names": "Sample District",
                "season_names": "Kharif",
                "soil_for_crop": "Alluvial",
                "N": 10.0,
                "P": 20.0,
                "K": 30.0,
                "temperature": 21.0,
                "humidity": 61.0,
                "rainfall_mm": 500.0,
                "crop_year": 2010,
                "area": 10.0,
            },
        )
        self.assertEqual(record["npk_source"], "dataset_57")

    def test_exact_lookup_fails_explicitly_when_missing_or_ambiguous(self) -> None:
        with self.assertRaises(HistoricalCropRecordNotFound):
            self.service.get_model_record(
                "Example State", "Sample District", "Rabi", "Rice", 2010, "Black"
            )
        with self.assertRaises(HistoricalCropRecordAmbiguous):
            self.service.get_model_record(
                "Example State", "Sample District", "Rabi", "Maize", 2012, "Black"
            )
        with self.assertRaises(HistoricalCropFeaturesUnavailable) as missing:
            self.service.get_model_record(
                "Example State", "Sample District", "Rabi", "Barley", 2013, "Black"
            )
        self.assertIn("temperature", missing.exception.feature_issues)

    def test_unavailable_dataset_raises_a_visible_service_error(self) -> None:
        service = CropLocationService(self.dataset_path.with_name("missing.csv"))
        with self.assertRaises(CropLocationDatasetError):
            service.get_options()

    def test_routes_return_filtered_rows_and_build_prediction_from_dataset(self) -> None:
        fake_crop_service = FakeCropService()
        with (
            patch("app.main.crop_service", fake_crop_service),
            patch("app.routes.crop.crop_service", fake_crop_service),
            patch("app.routes.crop.crop_location_service", self.service),
            TestClient(app) as client,
        ):
            options = client.get(
                "/api/crop/location-options",
                params={
                    "state_names": "Example State",
                    "district_names": "Sample District",
                },
            )
            area = client.get(
                "/api/crop/historical-area",
                params={
                    "state_names": "Example State",
                    "district_names": "Sample District",
                    "season_names": "Kharif",
                },
            )
            prediction = client.post(
                "/api/crop/recommend-from-record",
                json={
                    "state_names": "Example State",
                    "district_names": "Sample District",
                    "season_names": "Kharif",
                    "crop_names": "Rice",
                    "crop_year": 2010,
                    "soil_for_crop": "Alluvial",
                },
            )

        self.assertEqual(options.status_code, 200, options.text)
        self.assertEqual(options.json()["seasons"], ["Kharif", "Rabi"])
        self.assertEqual(area.status_code, 200, area.text)
        self.assertEqual(area.json()["records"][0]["area_hectares"], 10.0)
        self.assertEqual(prediction.status_code, 200, prediction.text)
        self.assertEqual(prediction.json()["reference_crop"], "Rice")
        self.assertEqual(prediction.json()["npk_source"], "dataset_57")
        self.assertEqual(
            list(prediction.json()["model_inputs"]),
            list(MODEL_FEATURE_COLUMNS),
        )
        self.assertEqual(fake_crop_service.received.model_dump()["area"], 10.0)

    def test_api_surfaces_missing_and_ambiguous_dataset_rows(self) -> None:
        fake_crop_service = FakeCropService()
        with (
            patch("app.main.crop_service", fake_crop_service),
            patch("app.routes.crop.crop_service", fake_crop_service),
            patch("app.routes.crop.crop_location_service", self.service),
            TestClient(app) as client,
        ):
            ambiguous = client.post(
                "/api/crop/recommend-from-record",
                json={
                    "state_names": "Example State",
                    "district_names": "Sample District",
                    "season_names": "Rabi",
                    "crop_names": "Maize",
                    "crop_year": 2012,
                    "soil_for_crop": "Black",
                },
            )
            missing = client.post(
                "/api/crop/recommend-from-record",
                json={
                    "state_names": "Example State",
                    "district_names": "Sample District",
                    "season_names": "Rabi",
                    "crop_names": "Barley",
                    "crop_year": 2013,
                    "soil_for_crop": "Black",
                },
            )

        self.assertEqual(ambiguous.status_code, 409, ambiguous.text)
        self.assertEqual(missing.status_code, 422, missing.text)
        self.assertIn("temperature", missing.json()["detail"]["unavailable_features"])


if __name__ == "__main__":
    unittest.main()
