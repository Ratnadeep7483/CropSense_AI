#!/usr/bin/env python3
"""Focused tests for crop recommendation categorical input validation."""

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib
import pandas as pd
from fastapi import HTTPException

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.routes.crop import recommend_crop  # noqa: E402
from app.schemas.crop import CropRecommendationRequest  # noqa: E402
from app.services.crop_service import (  # noqa: E402
    FEATURE_COLUMNS,
    _PREPROCESSOR_PATH,
    CropService,
    crop_service,
)

CSV_PATH = BACKEND_ROOT / "data" / "Copy of crop_recommendation_45_with_year_area.csv"


class CapturingPreprocessor:
    def __init__(self, fitted_preprocessor: object) -> None:
        self.named_transformers_ = fitted_preprocessor.named_transformers_
        self.captured: pd.DataFrame | None = None

    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        self.captured = data.copy()
        return data


class FixedModel:
    def predict(self, _: pd.DataFrame) -> list[int]:
        return [0]


class FixedLabelEncoder:
    classes_ = ["test crop"]

    def inverse_transform(self, _: list[int]) -> list[str]:
        return ["test crop"]


class CropInputValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = pd.read_csv(CSV_PATH)
        cls.fitted_preprocessor = joblib.load(_PREPROCESSOR_PATH)

    def setUp(self) -> None:
        sample = self.dataset.loc[
            (self.dataset["state_names"] == "Karnataka")
            & (self.dataset["district_names"] == "BELGAUM")
            & (self.dataset["season_names"] == "Kharif")
            & (self.dataset["soil_for_crop"] == "Black")
        ].iloc[0]
        self.request_data = sample.loc[FEATURE_COLUMNS].to_dict()
        self.preprocessor = CapturingPreprocessor(self.fitted_preprocessor)
        self.service = CropService()
        self.service._is_loaded = True
        self.service._preprocessor = self.preprocessor
        self.service._model = FixedModel()
        self.service._label_encoder = FixedLabelEncoder()

    def test_valid_trained_labels_are_passed_unchanged(self) -> None:
        request = CropRecommendationRequest.model_validate(self.request_data)

        self.assertEqual(self.service.predict(request), "test crop")
        self.assertIsNotNone(self.preprocessor.captured)
        self.assertEqual(
            self.preprocessor.captured.loc[0, "state_names"],
            "Karnataka",
        )
        self.assertEqual(
            self.preprocessor.captured.loc[0, "district_names"],
            "BELGAUM",
        )
        self.assertEqual(
            self.preprocessor.captured.loc[0, "season_names"],
            "Kharif",
        )
        self.assertEqual(
            self.preprocessor.captured.loc[0, "soil_for_crop"],
            "Black",
        )

    def test_legacy_request_and_response_contract_are_unchanged(self) -> None:
        request = CropRecommendationRequest.model_validate(self.request_data)
        self.assertEqual(list(request.model_dump()), FEATURE_COLUMNS)
        self.assertFalse(hasattr(request, "farmer_available_area_acres"))

        with (
            patch.object(crop_service, "_is_loaded", True),
            patch.object(crop_service, "_preprocessor", self.preprocessor),
            patch.object(crop_service, "_model", FixedModel()),
            patch.object(crop_service, "_label_encoder", FixedLabelEncoder()),
        ):
            response = asyncio.run(recommend_crop(request))

        self.assertEqual(
            response.model_dump(),
            {"success": True, "recommended_crop": "test crop"},
        )

    def test_case_only_values_are_normalized_to_trained_labels(self) -> None:
        request = CropRecommendationRequest.model_validate(
            {
                **self.request_data,
                "state_names": "karnataka",
                "district_names": "belgaum",
                "season_names": "kharif",
                "soil_for_crop": "black",
            }
        )

        self.service.predict(request)

        self.assertIsNotNone(self.preprocessor.captured)
        for field, expected in (
            ("state_names", "Karnataka"),
            ("district_names", "BELGAUM"),
            ("season_names", "Kharif"),
            ("soil_for_crop", "Black"),
        ):
            self.assertEqual(self.preprocessor.captured.loc[0, field], expected)

    def test_unknown_categorical_values_are_rejected(self) -> None:
        for field in (
            "state_names",
            "district_names",
            "season_names",
            "soil_for_crop",
        ):
            with self.subTest(field=field):
                request = CropRecommendationRequest.model_validate(
                    {**self.request_data, field: "unknown label"}
                )
                with self.assertRaisesRegex(ValueError, field):
                    self.service.predict(request)
                self.assertIsNone(self.preprocessor.captured)

    def test_district_must_belong_to_selected_state(self) -> None:
        request = CropRecommendationRequest.model_validate(
            {**self.request_data, "state_names": "Maharashtra"}
        )

        with self.assertRaisesRegex(ValueError, "does not belong"):
            self.service.predict(request)
        self.assertIsNone(self.preprocessor.captured)

    def test_district_missing_from_fitted_encoder_returns_http_422(self) -> None:
        namsai_row = self.dataset.loc[
            self.dataset["district_names"] == "NAMSAI"
        ].iloc[0]
        request_data = namsai_row.loc[FEATURE_COLUMNS].to_dict()
        request = CropRecommendationRequest.model_validate(request_data)

        with self.assertRaisesRegex(ValueError, "Unsupported district_names"):
            self.service.predict(request)
        self.assertIsNone(self.preprocessor.captured)

        with (
            patch.object(crop_service, "_is_loaded", True),
            patch.object(crop_service, "_preprocessor", self.preprocessor),
            patch.object(crop_service, "_model", FixedModel()),
            patch.object(crop_service, "_label_encoder", FixedLabelEncoder()),
        ):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(recommend_crop(request))
        self.assertEqual(error.exception.status_code, 422)

    def test_invalid_categories_and_location_return_http_422(self) -> None:
        invalid_requests = (
            {**self.request_data, "state_names": "unknown state"},
            {**self.request_data, "district_names": "unknown district"},
            {**self.request_data, "season_names": "unknown season"},
            {**self.request_data, "soil_for_crop": "unknown soil"},
            {**self.request_data, "state_names": "Maharashtra"},
        )
        with (
            patch.object(crop_service, "_is_loaded", True),
            patch.object(crop_service, "_preprocessor", self.preprocessor),
            patch.object(crop_service, "_model", FixedModel()),
            patch.object(crop_service, "_label_encoder", FixedLabelEncoder()),
        ):
            for request_data in invalid_requests:
                with self.subTest(request=request_data):
                    request = CropRecommendationRequest.model_validate(request_data)
                    with self.assertRaises(HTTPException) as error:
                        asyncio.run(recommend_crop(request))
                    self.assertEqual(error.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
