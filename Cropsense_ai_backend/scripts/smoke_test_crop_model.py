#!/usr/bin/env python3
"""Run a single-row inference smoke test for the trained 45-crop model."""

import sys
from pathlib import Path

import joblib
import pandas as pd

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.crop_service import (  # noqa: E402
    FEATURE_COLUMNS,
    _LABEL_ENCODER_PATH,
    _MODEL_PATH,
    _PREPROCESSOR_PATH,
)

CSV_PATH = BACKEND_ROOT / "data" / "Copy of crop_recommendation_45_with_year_area.csv"


def main() -> None:
    for artifact_path in (_MODEL_PATH, _PREPROCESSOR_PATH, _LABEL_ENCODER_PATH):
        if not artifact_path.is_file():
            raise FileNotFoundError(f"Required model artifact not found: {artifact_path}")
    if not CSV_PATH.is_file():
        raise FileNotFoundError(f"Crop dataset not found: {CSV_PATH}")

    model = joblib.load(_MODEL_PATH)
    preprocessor = joblib.load(_PREPROCESSOR_PATH)
    label_encoder = joblib.load(_LABEL_ENCODER_PATH)

    dataset = pd.read_csv(CSV_PATH)
    required_columns = [*FEATURE_COLUMNS, "crop_names"]
    missing_columns = [column for column in required_columns if column not in dataset]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")

    complete_rows = dataset.dropna(subset=required_columns)
    if complete_rows.empty:
        raise ValueError("Dataset contains no complete row for smoke testing.")

    sample = complete_rows.iloc[[0]]
    input_data = sample.loc[:, FEATURE_COLUMNS]
    transformed_data = preprocessor.transform(input_data)
    prediction = model.predict(transformed_data)
    predicted_crop = str(label_encoder.inverse_transform(prediction)[0])
    actual_crop = str(sample.iloc[0]["crop_names"])

    print("Single-row crop-model smoke test (not model accuracy)")
    print(f"Predicted crop: {predicted_crop}")
    print(f"Actual crop:    {actual_crop}")
    print(f"Match:          {predicted_crop == actual_crop}")


if __name__ == "__main__":
    main()
