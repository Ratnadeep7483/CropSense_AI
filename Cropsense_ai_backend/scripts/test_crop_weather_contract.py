#!/usr/bin/env python3
"""Check crop weather feature requirements and data provenance constraints."""

import unittest
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from pydantic import ValidationError

BACKEND_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = BACKEND_ROOT / "data" / "Copy of crop_recommendation_45_with_year_area.csv"
PREPROCESSOR_PATH = (
    BACKEND_ROOT
    / "app"
    / "ml"
    / "crop"
    / "model_artifacts"
    / "crop_preprocessor.joblib"
)

import sys

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.schemas.crop import CropRecommendationRequest  # noqa: E402
from app.services.crop_service import (  # noqa: E402
    FEATURE_COLUMNS,
    CropService,
)

LEGACY_KARNATAKA_DISTRICTS = (
    "BAGALKOT",
    "BANGALORE RURAL",
    "BELGAUM",
    "BELLARY",
    "BIJAPUR",
    "CHIKBALLAPUR",
    "CHIKMAGALUR",
    "DAKSHIN KANNAD",
    "DAVANGERE",
    "GULBARGA",
    "SHIMOGA",
    "TUMKUR",
    "UTTAR KANNAD",
)


class CropWeatherContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = pd.read_csv(CSV_PATH)
        cls.preprocessor = joblib.load(PREPROCESSOR_PATH)

    def test_model_and_request_use_raw_temperature_and_humidity_fields(self) -> None:
        self.assertIn("temperature", FEATURE_COLUMNS)
        self.assertIn("humidity", FEATURE_COLUMNS)
        self.assertEqual(
            CropRecommendationRequest.model_fields["temperature"].description,
            "Temperature in °C",
        )
        self.assertEqual(
            CropRecommendationRequest.model_fields["humidity"].description,
            "Relative humidity in %",
        )

    def test_crop_model_labels_remain_exact_and_are_not_resolved_to_lgd_names(self) -> None:
        training_pairs = set(
            self.dataset.loc[
                self.dataset["state_names"] == "Karnataka",
                ["state_names", "district_names"],
            ].itertuples(index=False, name=None)
        )
        self.assertTrue(
            all(("Karnataka", district) in training_pairs
                for district in LEGACY_KARNATAKA_DISTRICTS)
        )

        sample = self.dataset.loc[
            (self.dataset["state_names"] == "Karnataka")
            & (self.dataset["district_names"] == "BAGALKOT")
        ].iloc[0]
        request = CropRecommendationRequest.model_validate(
            sample.loc[FEATURE_COLUMNS].to_dict()
        )
        captured: dict[str, pd.DataFrame] = {}

        class CapturingPreprocessor:
            def __init__(self, fitted_preprocessor: object) -> None:
                self.named_transformers_ = fitted_preprocessor.named_transformers_

            def transform(self, data: pd.DataFrame) -> pd.DataFrame:
                captured["input"] = data.copy()
                return data

        class FixedModel:
            def predict(self, _: pd.DataFrame) -> list[int]:
                return [0]

        class FixedLabelEncoder:
            classes_ = ["rice"]

            def inverse_transform(self, _: list[int]) -> list[str]:
                return ["rice"]

        service = CropService()
        service._is_loaded = True
        service._preprocessor = CapturingPreprocessor(self.preprocessor)
        service._model = FixedModel()
        service._label_encoder = FixedLabelEncoder()

        self.assertEqual(service.predict(request), "rice")
        self.assertEqual(captured["input"].loc[0, "state_names"], "Karnataka")
        self.assertEqual(captured["input"].loc[0, "district_names"], "BAGALKOT")

        categorical_encoder = self.preprocessor.named_transformers_["cat"]
        categories = {
            column: set(values)
            for column, values in zip(
                categorical_encoder.feature_names_in_,
                categorical_encoder.categories_,
            )
        }
        self.assertIn("Karnataka", categories["state_names"])
        self.assertIn("BAGALKOT", categories["district_names"])

    def test_weather_values_are_required_and_not_imputed(self) -> None:
        request = {
            "state_names": "Example State",
            "district_names": "Example District",
            "season_names": "Kharif",
            "soil_for_crop": "Alluvial",
            "N": 60,
            "P": 70,
            "K": 70,
            "rainfall_mm": 100,
            "crop_year": 2010,
            "area": 1,
        }
        with self.assertRaises(ValidationError):
            CropRecommendationRequest.model_validate(request)
        with self.assertRaises(ValidationError):
            CropRecommendationRequest.model_validate(
                {**request, "temperature": None, "humidity": 70}
            )
        with self.assertRaises(ValidationError):
            CropRecommendationRequest.model_validate(
                {**request, "temperature": 25, "humidity": None}
            )

    def test_preprocessor_passes_weather_features_through_without_scaling(self) -> None:
        numeric_transformer = dict(
            (name, transformer)
            for name, transformer, _ in self.preprocessor.transformers_
        )["num"]
        numeric_columns = dict(
            (name, columns)
            for name, _, columns in self.preprocessor.transformers_
        )["num"]
        self.assertIn("temperature", numeric_columns)
        self.assertIn("humidity", numeric_columns)
        sample = pd.DataFrame(
            [
                {
                    column: 25.0 if column == "temperature" else 70.0
                    for column in numeric_columns
                }
            ]
        )
        transformed = numeric_transformer.transform(sample).to_numpy()
        self.assertEqual(
            transformed[0, numeric_columns.index("temperature")], 25.0
        )
        self.assertEqual(
            transformed[0, numeric_columns.index("humidity")], 70.0
        )

    def test_csv_weather_values_are_present_and_finite(self) -> None:
        for feature in ("temperature", "humidity"):
            values = self.dataset[feature]
            self.assertEqual(int(values.isna().sum()), 0)
            self.assertTrue(np.isfinite(values.to_numpy()).all())

    def test_csv_weather_records_are_season_and_year_grouped_without_coordinates(self) -> None:
        self.assertTrue(
            {"state_names", "district_names", "season_names", "crop_year"}
            .issubset(self.dataset.columns)
        )
        lower_columns = {column.casefold() for column in self.dataset.columns}
        self.assertFalse(
            {"latitude", "longitude", "month", "date"}.intersection(
                lower_columns
            )
        )
        groups = self.dataset.groupby(
            ["state_names", "district_names", "season_names", "crop_year"],
            dropna=False,
        )
        for feature in ("temperature", "humidity"):
            self.assertTrue(groups[feature].nunique().eq(1).all())


if __name__ == "__main__":
    unittest.main(verbosity=2)
