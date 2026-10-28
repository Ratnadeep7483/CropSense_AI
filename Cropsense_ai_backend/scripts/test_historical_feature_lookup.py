#!/usr/bin/env python3
"""Focused tests for strictly prior-year crop feature lookups."""

import asyncio
import csv
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.historical_feature_lookup_service import (  # noqa: E402
    HistoricalFeatureLookupService,
)
from app.routes.crop import lookup_historical_features  # noqa: E402
from app.schemas.crop import HistoricalFeatureLookupRequest  # noqa: E402


class HistoricalFeatureLookupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.dataset_path = Path(self.temp.name) / "features.csv"
        self._write_rows(
            [
                self._row("Kharif", "Black", "Rice", 2018, 12.0, 10, 20, 30, "dataset_57"),
                self._row("Kharif", "Black", "Rice", 2020, 24.0, 11, 21, 31, "merged_51"),
                self._row("Kharif", "Black", "Rice", 2022, 99.0, 12, 22, 32, "estimated_ranges"),
                self._row("Kharif", "Red", "Rice", 2021, 30.0, 40, 50, 60, "dataset_31_valid_rows"),
                self._row("Rabi", "Black", "Rice", 2021, 31.0, 41, 51, 61, "dataset_57"),
                self._row("Kharif", "Black", "Wheat", 2021, 32.0, 42, 52, 62, "merged_51"),
                {
                    **self._row(
                        "Kharif", "Black", "Rice", 2020, 24.0, 11, 21, 31, "merged_51"
                    ),
                    "district_names": "Other District",
                },
            ]
        )
        self.service = HistoricalFeatureLookupService(self.dataset_path)

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _row(
        season: str,
        soil: str,
        crop: str,
        year: int,
        area: float,
        nitrogen: float,
        phosphorus: float,
        potassium: float,
        source: str,
    ) -> dict[str, object]:
        return {
            "state_names": "Example State",
            "district_names": "Sample District",
            "season_names": season,
            "soil_for_crop": soil,
            "crop_names": crop,
            "crop_year": year,
            "area": area,
            "N": nitrogen,
            "P": phosphorus,
            "K": potassium,
            "npk_source": source,
        }

    def _write_rows(self, rows: list[dict[str, object]]) -> None:
        with self.dataset_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def _lookup(self, target_year: int):
        return self.service.lookup(
            "Example State",
            "Sample District",
            "Kharif",
            "Black",
            "Rice",
            target_year,
        )

    def test_returns_latest_matching_prior_area_and_paired_year(self) -> None:
        result = self._lookup(2021)

        self.assertEqual((result.area, result.area_year), (24.0, 2020))
        self.assertEqual(result.area_status, "available")
        self.assertIsNone(result.area_missing_reason)
        self.assertEqual(result.npk_year, 2020)
        self.assertEqual(result.npk_source, "merged_51")

    def test_target_and_future_years_are_excluded(self) -> None:
        result = self._lookup(2020)

        self.assertEqual((result.area, result.area_year), (12.0, 2018))
        self.assertEqual(result.npk_year, 2018)
        self.assertNotEqual(result.area, 24.0)

    def test_returns_clear_missing_data_when_no_prior_match_exists(self) -> None:
        result = self._lookup(2018)

        self.assertIsNone(result.area)
        self.assertIsNone(result.area_year)
        self.assertEqual(result.area_status, "not_found")
        self.assertIn("only at or after target_year 2018", result.area_missing_reason or "")
        self.assertIn(
            "strict cutoff excludes years [2018, 2020, 2021, 2022]",
            result.area_missing_reason or "",
        )
        self.assertIsNone(result.npk_year)
        self.assertEqual(result.npk_status, "not_found")
        self.assertIsNone(result.N)
        self.assertIsNone(result.P)
        self.assertIsNone(result.K)

    def test_missing_crop_diagnostic_identifies_exact_area_lookup_key(self) -> None:
        result = self.service.lookup(
            "Example State",
            "Sample District",
            "Kharif",
            "Black",
            "Not in Dataset",
            2021,
        )

        self.assertEqual(result.area_status, "not_found")
        self.assertIn("state='Example State'", result.area_missing_reason or "")
        self.assertIn("district='Sample District'", result.area_missing_reason or "")
        self.assertIn("season='Kharif'", result.area_missing_reason or "")
        self.assertIn("crop='Not in Dataset'", result.area_missing_reason or "")
        self.assertIn("matching trims/collapses whitespace", result.area_missing_reason or "")
        self.assertIn("does not filter by soil", result.area_missing_reason or "")

    def test_area_lookup_normalizes_case_whitespace_and_ignores_soil(self) -> None:
        matching_area = self.service.lookup(
            "  EXAMPLE STATE ",
            " sample   district ",
            " kharif ",
            "Loamy",
            " rice ",
            2021,
        )
        self.assertEqual(
            (matching_area.area, matching_area.area_year),
            (24.0, 2020),
        )
        self.assertIsNone(matching_area.npk_year)
        self.assertEqual(matching_area.npk_status, "not_found")

        matching_soil = self.service.lookup(
            "  EXAMPLE STATE ",
            " sample   district ",
            " kharif ",
            " black ",
            " rice ",
            2021,
        )
        self.assertEqual(matching_soil.npk_year, 2020)
        self.assertEqual(matching_soil.npk_status, "unverified_source")

    def test_missing_exact_season_does_not_fall_back_to_another_season(self) -> None:
        result = self.service.lookup(
            "Example State",
            "Sample District",
            "Rabi",
            "Black",
            "Wheat",
            2021,
        )

        self.assertIsNone(result.area)
        self.assertEqual(result.area_status, "not_found")
        self.assertIn("other season labels ['Kharif']", result.area_missing_reason or "")
        self.assertIn("cross-season fallback is not used", result.area_missing_reason or "")
        self.assertIsNone(result.area_year)

    def test_area_normalization_accepts_dataset_label_variants(self) -> None:
        rows = [
            self._row(
                "  kHaRiF  ",
                " BLACK ",
                "  rIcE   ",
                2020,
                24.0,
                11,
                21,
                31,
                "merged_51",
            )
        ]
        rows[0]["state_names"] = " Example   State "
        rows[0]["district_names"] = " sample district "
        self._write_rows(rows)
        self.service = HistoricalFeatureLookupService(self.dataset_path)

        result = self.service.lookup(
            "example state",
            "SAMPLE DISTRICT ",
            "KHARIF",
            "black",
            "Rice",
            2021,
        )

        self.assertEqual((result.area, result.area_year), (24.0, 2020))
        self.assertEqual(result.area_status, "available")

    def test_npk_values_are_withheld_when_source_provenance_is_undocumented(self) -> None:
        result = self._lookup(2021)

        self.assertEqual(result.npk_status, "unverified_source")
        self.assertIn("do not document", result.npk_missing_reason or "")
        self.assertIsNone(result.N)
        self.assertIsNone(result.P)
        self.assertIsNone(result.K)

    def test_area_conflicts_at_latest_year_are_not_arbitrarily_selected(self) -> None:
        rows = [
            self._row("Kharif", "Black", "Rice", 2020, 24.0, 11, 21, 31, "merged_51"),
            self._row("Kharif", "Red", " rice ", 2020, 25.0, 12, 22, 32, "dataset_57"),
        ]
        self._write_rows(rows)
        self.service = HistoricalFeatureLookupService(self.dataset_path)

        result = self._lookup(2021)

        self.assertIsNone(result.area)
        self.assertEqual(result.area_year, 2020)
        self.assertEqual(result.area_status, "ambiguous")

    def test_api_response_exposes_area_pairing_and_npk_missing_status(self) -> None:
        request = HistoricalFeatureLookupRequest(
            state_names="Example State",
            district_names="Sample District",
            season_names="Kharif",
            soil_for_crop="Black",
            crop_names="Rice",
            target_year=2021,
        )
        with patch(
            "app.routes.crop.historical_feature_lookup_service", self.service
        ):
            response = asyncio.run(lookup_historical_features(request))

        self.assertEqual((response.area, response.area_year), (24.0, 2020))
        self.assertEqual(response.npk_status, "unverified_source")
        self.assertIsNone(response.N)
        self.assertIsNone(response.P)
        self.assertIsNone(response.K)


if __name__ == "__main__":
    unittest.main(verbosity=2)
