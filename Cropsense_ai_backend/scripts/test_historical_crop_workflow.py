#!/usr/bin/env python3
"""Tests that the legacy experimental route never fetches external weather."""

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from pydantic import ValidationError

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.routes.crop import (  # noqa: E402
    recommend_crop_from_historical_features,
)
from app.schemas.crop import HistoricalCropWorkflowRequest  # noqa: E402
from app.services.candidate_wise_crop_experiment import (  # noqa: E402
    CandidateScore,
    CandidateWiseExperimentResult,
)
from app.services.historical_weather_service import (  # noqa: E402
    historical_weather_service,
)


class FakeCropService:
    is_loaded = True
    load_error = None


class FakeExperiment:
    def validate_context(self, **values):
        return {
            "state_names": values["state"],
            "district_names": values["district"],
            "season_names": values["season"],
            "soil_for_crop": values["soil"],
        }

    def run_with_existing_npk_lookup(self, **values):
        self.run_arguments = values
        return CandidateWiseExperimentResult(
            target_year=values["target_year"],
            total_candidates=1,
            area_available=0,
            missing_history=1,
            ambiguous_area=0,
            npk_unavailable_or_unverified=1,
            shared_features_unverified=1,
            validation_failures=0,
            scored_candidates=0,
            complete_trustworthy_prediction_available=False,
            ranking_status="not_validated",
            ranking_limitation="Candidate ranking has not been validated.",
            candidates=(
                CandidateScore(
                    crop="Crop",
                    area=None,
                    area_year=None,
                    status="missing_history",
                    score=None,
                    error="No prior record.",
                ),
            ),
        )


class FakeRainfallService:
    def lookup_before_year(self, state, district, season, target_year):
        return type(
            "Rainfall",
            (),
            {
                "rainfall_mm": 100.0,
                "matched_year_count": 1,
                "observed_year_start": target_year - 1,
                "observed_year_end": target_year - 1,
            },
        )()


class HistoricalCropWorkflowTests(unittest.TestCase):
    @staticmethod
    def _request() -> HistoricalCropWorkflowRequest:
        return HistoricalCropWorkflowRequest(
            state_names="Karnataka",
            district_names="BELGAUM",
            season_names="Kharif",
            soil_for_crop="Black",
            farmer_available_area_acres=3.0,
        )

    def test_legacy_diagnostic_does_not_call_weather_api_or_rank_candidates(self) -> None:
        experiment = FakeExperiment()
        get_weather = AsyncMock(
            side_effect=AssertionError("external weather must not be called")
        )
        with (
            patch("app.routes.crop.crop_service", FakeCropService()),
            patch("app.routes.crop.candidate_wise_crop_experiment", experiment),
            patch(
                "app.routes.crop.rainfall_lookup_service",
                FakeRainfallService(),
            ),
            patch.object(historical_weather_service, "get_historical_average", get_weather),
        ):
            response = asyncio.run(
                recommend_crop_from_historical_features(self._request())
            )

        get_weather.assert_not_awaited()
        self.assertEqual(response.farmer_available_area_acres, 3.0)
        self.assertNotIn(
            "farmer_available_area_acres",
            experiment.run_arguments,
        )
        self.assertEqual(
            response.weather_status,
            "unavailable_exact_record_required",
        )
        self.assertIn("exact selected crop/year/soil", response.weather_error)
        self.assertFalse(response.recommendation_available)
        self.assertIsNone(response.recommended_crop)
        self.assertEqual(response.ranking_status, "not_validated")

    def test_legacy_diagnostic_rejects_unavailable_model(self) -> None:
        class UnloadedCropService:
            is_loaded = False
            load_error = "Artifacts are missing."

        with patch("app.routes.crop.crop_service", UnloadedCropService()):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(recommend_crop_from_historical_features(self._request()))
        self.assertEqual(error.exception.status_code, 503)

    def test_farmer_area_contract_rejects_invalid_values(self) -> None:
        for acres in (0, -1, float("inf"), float("nan"), True, 100_001):
            with self.subTest(acres=acres):
                with self.assertRaises(ValidationError):
                    HistoricalCropWorkflowRequest.model_validate(
                        {
                            **self._request().model_dump(),
                            "farmer_available_area_acres": acres,
                        }
                    )


if __name__ == "__main__":
    unittest.main()
