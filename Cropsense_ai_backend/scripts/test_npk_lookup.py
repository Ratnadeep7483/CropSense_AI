#!/usr/bin/env python3
"""Tests for exact-key historical NPK lookups."""

import csv
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402
from app.services.npk_lookup_service import (  # noqa: E402
    DATASET_PATH,
    NPKDatasetError,
    NPKRecordNotFound,
    NPKLookupService,
)


class NPKLookupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.dataset_path = Path(self.temp.name) / "npk.csv"
        self._write_rows(
            [
                ["Example State", "Sample District", "Kharif", 2000, 10, 20, 30, 21, 61, 500],
                ["Example State", "Sample District", "Kharif", 2000, 20, 40, 60, 21, 61, 500],
                ["Example State", "Sample District", "Kharif", 2000, 30, 60, 90, 21, 61, 500],
                ["Example State", "Sample District", "Kharif", 2001, 1, 2, 3, 22, 62, 600],
                ["Other State", "Sample District", "Kharif", 2000, 100, 200, 300, 23, 63, 700],
                ["Example State", "Sample District", "Rabi", 2000, 5, 15, 25, 24, 64, 800],
            ]
        )
        self.service = NPKLookupService(self.dataset_path)

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
                    "crop_year",
                    "N",
                    "P",
                    "K",
                    "temperature",
                    "humidity",
                    "rainfall_mm",
                ]
            )
            writer.writerows(rows)

    def test_valid_lookup_returns_values_for_exact_state_district_and_season(self) -> None:
        self.assertEqual(
            self.service.lookup("Example State", "Sample District", "Rabi"),
            (5.0, 15.0, 25.0, 1),
        )

    def test_missing_district_or_season_returns_not_found(self) -> None:
        for district, season in (
            ("Unknown District", "Kharif"),
            ("Sample District", "Unknown Season"),
        ):
            with self.subTest(district=district, season=season):
                with self.assertRaises(NPKRecordNotFound):
                    self.service.lookup("Example State", district, season)

    def test_multiple_matches_return_mean_npk_and_record_count(self) -> None:
        self.assertEqual(
            self.service.lookup("Example State", "Sample District", "Kharif"),
            (15.25, 30.5, 45.75, 4),
        )

    def test_year_lookup_rejects_unsupported_year(self) -> None:
        for year in (1996, 2016):
            with self.subTest(year=year):
                with self.assertRaisesRegex(ValueError, "between 1997 and 2015"):
                    self.service.lookup(
                        "Example State", "Sample District", "Kharif", year
                    )

    def test_year_lookup_returns_same_group_features_and_explicit_npk_range(self) -> None:
        result = self.service.lookup(
            "Example State", "Sample District", "Kharif", 2000
        )

        self.assertEqual(result.crop_year, 2000)
        self.assertEqual((result.N, result.P, result.K), (20.0, 40.0, 60.0))
        self.assertEqual(result.matched_records, 3)
        self.assertEqual(result.npk_aggregation, "arithmetic_mean")
        self.assertEqual(
            result.npk_ranges,
            {
                "N": {"minimum": 10.0, "maximum": 30.0},
                "P": {"minimum": 20.0, "maximum": 60.0},
                "K": {"minimum": 30.0, "maximum": 90.0},
            },
        )
        self.assertEqual(
            (result.temperature, result.humidity, result.rainfall_mm),
            (21.0, 61.0, 500.0),
        )

    def test_year_lookup_does_not_mix_values_from_other_years(self) -> None:
        result = self.service.lookup(
            "Example State", "Sample District", "Kharif", 2001
        )

        self.assertEqual((result.N, result.P, result.K), (1.0, 2.0, 3.0))
        self.assertEqual(
            (result.temperature, result.humidity, result.rainfall_mm),
            (22.0, 62.0, 600.0),
        )

    def test_year_lookup_rejects_missing_group(self) -> None:
        with self.assertRaises(NPKRecordNotFound):
            self.service.lookup("Example State", "Unknown District", "Kharif", 2000)

    def test_year_lookup_rejects_conflicting_non_npk_values(self) -> None:
        self._write_rows(
            [
                ["Example State", "Sample District", "Kharif", 2000, 10, 20, 30, 21, 61, 500],
                ["Example State", "Sample District", "Kharif", 2000, 20, 40, 60, 22, 61, 500],
            ]
        )
        self.service = NPKLookupService(self.dataset_path)

        with self.assertRaisesRegex(NPKDatasetError, "Conflicting temperature"):
            self.service.lookup(
                "Example State", "Sample District", "Kharif", 2000
            )

    def test_project_dataset_lookup_matches_direct_dataset_aggregation(self) -> None:
        dataset = pd.read_csv(DATASET_PATH)
        matches = dataset.loc[
            (dataset["state_names"] == "Karnataka")
            & (dataset["district_names"] == "BENGALURU URBAN")
            & (dataset["season_names"] == "Kharif"),
            ["N", "P", "K"],
        ]
        expected = (
            float(matches["N"].mean()),
            float(matches["P"].mean()),
            float(matches["K"].mean()),
            len(matches),
        )
        self.assertGreater(len(matches), 0)
        self.assertEqual(
            NPKLookupService().lookup(
                "Karnataka", "BENGALURU URBAN", "Kharif"
            ),
            expected,
        )

    def test_api_returns_mean_values_and_404_for_missing_exact_key(self) -> None:
        with patch("app.routes.crop.npk_lookup_service", self.service):
            with TestClient(app) as client:
                success = client.post(
                    "/api/crop/npk-lookup",
                    json={
                        "state_names": "Example State",
                        "district_names": "Sample District",
                        "season_names": "Kharif",
                    },
                )
                missing = client.post(
                    "/api/crop/npk-lookup",
                    json={
                        "state_names": "Example State",
                        "district_names": "Unknown District",
                        "season_names": "Kharif",
                    },
                )
        self.assertEqual(success.status_code, 200, success.text)
        self.assertEqual(
            success.json(),
            {
                "success": True,
                "state_names": "Example State",
                "district_names": "Sample District",
                "season_names": "Kharif",
                "N": 15.25,
                "P": 30.5,
                "K": 45.75,
                "matched_records": 4,
            },
        )
        self.assertEqual(missing.status_code, 404, missing.text)
        self.assertIn("No historical NPK records", missing.json()["detail"]["error"])

    def test_api_returns_year_features_and_npk_variation(self) -> None:
        with patch("app.routes.crop.npk_lookup_service", self.service):
            with TestClient(app) as client:
                response = client.post(
                    "/api/crop/npk-lookup",
                    json={
                        "state_names": "Example State",
                        "district_names": "Sample District",
                        "season_names": "Kharif",
                        "crop_year": 2000,
                    },
                )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(
            response.json(),
            {
                "success": True,
                "state_names": "Example State",
                "district_names": "Sample District",
                "season_names": "Kharif",
                "crop_year": 2000,
                "N": 20.0,
                "P": 40.0,
                "K": 60.0,
                "matched_records": 3,
                "npk_aggregation": "arithmetic_mean",
                "npk_ranges": {
                    "N": {"minimum": 10.0, "maximum": 30.0},
                    "P": {"minimum": 20.0, "maximum": 60.0},
                    "K": {"minimum": 30.0, "maximum": 90.0},
                },
                "temperature": 21.0,
                "humidity": 61.0,
                "rainfall_mm": 500.0,
            },
        )

    def test_api_rejects_unsupported_years(self) -> None:
        with TestClient(app) as client:
            for year in (1996, 2016):
                with self.subTest(year=year):
                    response = client.post(
                        "/api/crop/npk-lookup",
                        json={
                            "state_names": "Example State",
                            "district_names": "Sample District",
                            "season_names": "Kharif",
                            "crop_year": year,
                        },
                    )
                    self.assertEqual(response.status_code, 422, response.text)

    def test_api_returns_404_for_missing_year_group(self) -> None:
        with patch("app.routes.crop.npk_lookup_service", self.service):
            with TestClient(app) as client:
                response = client.post(
                    "/api/crop/npk-lookup",
                    json={
                        "state_names": "Example State",
                        "district_names": "Sample District",
                        "season_names": "Kharif",
                        "crop_year": 2002,
                    },
                )

        self.assertEqual(response.status_code, 404, response.text)
        self.assertIn("crop year", response.json()["detail"]["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
