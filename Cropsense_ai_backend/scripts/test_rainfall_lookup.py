#!/usr/bin/env python3
"""Tests for exact-key multi-year historical rainfall lookups."""

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
from app.services.rainfall_lookup_service import (  # noqa: E402
    DATASET_PATH,
    RAINFALL_DESCRIPTION,
    RainfallDatasetError,
    RainfallLookupService,
    RainfallRecordNotFound,
)


class RainfallLookupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.dataset_path = Path(self.temp.name) / "rainfall.csv"
        self.service = RainfallLookupService(self.dataset_path)

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
                    "rainfall_mm",
                ]
            )
            writer.writerows(rows)
        self.service = RainfallLookupService(self.dataset_path)

    def test_exact_key_uses_only_matching_state_district_and_season(self) -> None:
        self._write_rows(
            [
                ["Example State", "Sample District", "Kharif", 2000, 10],
                ["Example State", "Sample District", "Kharif", 2001, 30],
                ["Other State", "Sample District", "Kharif", 2000, 900],
                ["Example State", "Other District", "Kharif", 2000, 800],
                ["Example State", "Sample District", "Rabi", 2000, 700],
            ]
        )

        result = self.service.lookup(
            "Example State", "Sample District", "Kharif"
        )

        self.assertEqual(result.rainfall_mm, 20.0)
        self.assertEqual(result.matched_year_count, 2)
        self.assertEqual(result.observed_year_start, 2000)
        self.assertEqual(result.observed_year_end, 2001)

    def test_averages_one_value_per_year_not_repeated_crop_rows(self) -> None:
        self._write_rows(
            [
                ["Example State", "Sample District", "Kharif", 2000, 100],
                *[
                    ["Example State", "Sample District", "Kharif", 2000, 100]
                    for _ in range(9)
                ],
                ["Example State", "Sample District", "Kharif", 2001, 300],
            ]
        )

        result = self.service.lookup(
            "Example State", "Sample District", "Kharif"
        )

        self.assertEqual(result.rainfall_mm, 200.0)
        self.assertEqual(result.matched_year_count, 2)

    def test_conflicting_values_within_a_year_are_dataset_error(self) -> None:
        self._write_rows(
            [
                ["Example State", "Sample District", "Kharif", 2000, 100],
                ["Example State", "Sample District", "Kharif", 2000, 101],
            ]
        )

        with self.assertRaisesRegex(RainfallDatasetError, "conflicting"):
            self.service.lookup("Example State", "Sample District", "Kharif")

    def test_missing_exact_key_does_not_fall_back_to_partial_match(self) -> None:
        self._write_rows(
            [["Example State", "Sample District", "Kharif", 2000, 100]]
        )

        for state, district, season in (
            ("Other State", "Sample District", "Kharif"),
            ("Example State", "Other District", "Kharif"),
            ("Example State", "Sample District", "Rabi"),
        ):
            with self.subTest(state=state, district=district, season=season):
                with self.assertRaises(RainfallRecordNotFound):
                    self.service.lookup(state, district, season)

    def test_missing_years_are_not_interpolated(self) -> None:
        self._write_rows(
            [
                ["Example State", "Sample District", "Kharif", 2000, 10],
                ["Example State", "Sample District", "Kharif", 2002, 30],
            ]
        )

        result = self.service.lookup(
            "Example State", "Sample District", "Kharif"
        )

        self.assertEqual(result.rainfall_mm, 20.0)
        self.assertEqual(result.matched_year_count, 2)
        self.assertEqual(result.observed_year_start, 2000)
        self.assertEqual(result.observed_year_end, 2002)

    def test_pre_target_lookup_excludes_target_and_future_years(self) -> None:
        self._write_rows(
            [
                ["Example State", "Sample District", "Kharif", 2000, 10],
                ["Example State", "Sample District", "Kharif", 2001, 30],
                ["Example State", "Sample District", "Kharif", 2002, 900],
                ["Example State", "Sample District", "Kharif", 2003, 700],
            ]
        )

        result = self.service.lookup_before_year(
            "Example State", "Sample District", "Kharif", 2002
        )

        self.assertEqual(result.rainfall_mm, 20.0)
        self.assertEqual(result.matched_year_count, 2)
        self.assertEqual(result.observed_year_start, 2000)
        self.assertEqual(result.observed_year_end, 2001)

    def test_pre_target_lookup_reports_missing_prior_history(self) -> None:
        self._write_rows(
            [["Example State", "Sample District", "Kharif", 2002, 10]]
        )

        with self.assertRaisesRegex(RainfallRecordNotFound, "before the target year"):
            self.service.lookup_before_year(
                "Example State", "Sample District", "Kharif", 2002
            )

    def test_zero_rainfall_is_valid(self) -> None:
        self._write_rows(
            [
                ["Example State", "Sample District", "Kharif", 2000, 0],
                ["Example State", "Sample District", "Kharif", 2001, 20],
            ]
        )

        self.assertEqual(
            self.service.lookup("Example State", "Sample District", "Kharif").rainfall_mm,
            10.0,
        )

    def test_missing_nonnumeric_nonfinite_and_negative_rainfall_fail(self) -> None:
        invalid_values: list[tuple[str, object]] = [
            ("missing", ""),
            ("nonnumeric", "not-a-number"),
            ("nonfinite", "inf"),
            ("negative", -1),
        ]
        for label, invalid_value in invalid_values:
            with self.subTest(value=label):
                self._write_rows(
                    [
                        [
                            "Example State",
                            "Sample District",
                            "Kharif",
                            2000,
                            invalid_value,
                        ]
                    ]
                )
                with self.assertRaises(RainfallDatasetError):
                    self.service.lookup(
                        "Example State", "Sample District", "Kharif"
                    )

    def test_api_returns_year_metadata_and_uncertainty_description(self) -> None:
        self._write_rows(
            [
                ["Example State", "Sample District", "Kharif", 2000, 10],
                ["Example State", "Sample District", "Kharif", 2002, 30],
            ]
        )
        with patch("app.routes.crop.rainfall_lookup_service", self.service):
            with TestClient(app) as client:
                response = client.post(
                    "/api/crop/rainfall-lookup",
                    json={
                        "state_names": "Example State",
                        "district_names": "Sample District",
                        "season_names": "Kharif",
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
                "rainfall_mm": 20.0,
                "matched_year_count": 2,
                "observed_year_start": 2000,
                "observed_year_end": 2002,
                "description": RAINFALL_DESCRIPTION,
            },
        )
        self.assertIn("unverified", response.json()["description"])

    def test_api_rejects_blank_keys_and_unsupported_seasons(self) -> None:
        with TestClient(app) as client:
            for body in (
                {
                    "state_names": " ",
                    "district_names": "Sample District",
                    "season_names": "Kharif",
                },
                {
                    "state_names": "Example State",
                    "district_names": "Sample District",
                    "season_names": "Monsoon",
                },
            ):
                with self.subTest(body=body):
                    response = client.post("/api/crop/rainfall-lookup", json=body)
                    self.assertEqual(response.status_code, 422, response.text)

    def test_api_returns_404_for_missing_key_and_503_for_bad_dataset(self) -> None:
        self._write_rows(
            [["Example State", "Sample District", "Kharif", 2000, 10]]
        )
        with patch("app.routes.crop.rainfall_lookup_service", self.service):
            with TestClient(app) as client:
                missing = client.post(
                    "/api/crop/rainfall-lookup",
                    json={
                        "state_names": "Other State",
                        "district_names": "Sample District",
                        "season_names": "Kharif",
                    },
                )
        self.assertEqual(missing.status_code, 404, missing.text)

        self._write_rows(
            [
                ["Example State", "Sample District", "Kharif", 2000, -2],
            ]
        )
        with patch("app.routes.crop.rainfall_lookup_service", self.service):
            with TestClient(app) as client:
                unavailable = client.post(
                    "/api/crop/rainfall-lookup",
                    json={
                        "state_names": "Example State",
                        "district_names": "Sample District",
                        "season_names": "Kharif",
                    },
                )
        self.assertEqual(unavailable.status_code, 503, unavailable.text)

    def test_project_dataset_lookup_collapses_rows_by_observed_year(self) -> None:
        result = RainfallLookupService().lookup(
            "Karnataka", "MYSORE", "Kharif"
        )
        self.assertEqual(result.matched_year_count, 18)
        self.assertEqual(result.observed_year_start, 1997)
        self.assertEqual(result.observed_year_end, 2014)
        self.assertAlmostEqual(result.rainfall_mm, 655.8944444444445)
        self.assertTrue(DATASET_PATH.is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
