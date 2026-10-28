#!/usr/bin/env python3
"""Exercise the crop recommendation API with one complete dataset row."""

import json
import sys
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402
from app.services.crop_service import (  # noqa: E402
    FEATURE_COLUMNS,
    _LABEL_ENCODER_PATH,
)

CSV_PATH = BACKEND_ROOT / "data" / "Copy of crop_recommendation_45_with_year_area.csv"
ENDPOINT = "/api/crop/recommend"


def main() -> None:
    if not CSV_PATH.is_file():
        raise FileNotFoundError(f"Crop dataset not found: {CSV_PATH}")

    dataset = pd.read_csv(CSV_PATH)
    required_columns = [*FEATURE_COLUMNS, "crop_names"]
    missing_columns = [column for column in required_columns if column not in dataset]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")

    complete_rows = dataset.dropna(subset=required_columns)
    if complete_rows.empty:
        raise ValueError("Dataset contains no complete row for API testing.")

    sample = complete_rows.iloc[[0]]
    request_body = json.loads(sample.loc[:, FEATURE_COLUMNS].to_json(orient="records"))[0]
    expected_historical_model_inputs = {
        column: sample.iloc[0][column] for column in FEATURE_COLUMNS
    }
    actual_crop = str(sample.iloc[0]["crop_names"])

    with TestClient(app) as client:
        response = client.post(ENDPOINT, json=request_body)
        historical_response = client.post(
            "/api/crop/recommend-from-record",
            json={
                "state_names": str(sample.iloc[0]["state_names"]),
                "district_names": str(sample.iloc[0]["district_names"]),
                "season_names": str(sample.iloc[0]["season_names"]),
                "crop_names": actual_crop,
                "crop_year": int(sample.iloc[0]["crop_year"]),
                "soil_for_crop": str(sample.iloc[0]["soil_for_crop"]),
            },
        )

    print(f"Endpoint: POST {ENDPOINT}")
    print(f"Request: {json.dumps(request_body, ensure_ascii=False)}")
    print(f"HTTP status: {response.status_code}")
    if response.status_code != 200:
        raise RuntimeError(f"Crop API request failed: {response.text}")

    response_body = response.json()
    if response_body.get("success") is not True:
        raise AssertionError(f"Unexpected crop API response: {response_body}")
    predicted_crop = response_body.get("recommended_crop")
    if not isinstance(predicted_crop, str) or not predicted_crop:
        raise AssertionError(f"Response omitted recommended_crop: {response_body}")

    label_encoder = __import__("joblib").load(_LABEL_ENCODER_PATH)
    supported_crops = {str(crop) for crop in label_encoder.classes_}
    if predicted_crop not in supported_crops:
        raise AssertionError(
            f"Predicted crop {predicted_crop!r} is not in the model label classes."
        )

    print(f"Response: {json.dumps(response_body, ensure_ascii=False)}")
    print(f"Actual crop: {actual_crop}")
    print("Predicted crop belongs to the model's 45 supported classes: True")

    if historical_response.status_code != 200:
        raise RuntimeError(
            "Dataset-backed crop workflow failed: "
            f"{historical_response.status_code} {historical_response.text}"
        )
    historical_body = historical_response.json()
    if historical_body.get("success") is not True:
        raise AssertionError(
            f"Unexpected dataset-backed response: {historical_body}"
        )
    if historical_body.get("model_inputs") != expected_historical_model_inputs:
        raise AssertionError(
            "Dataset-backed workflow did not return the exact selected "
            "12-feature training row."
        )
    print("Dataset-backed record workflow status: 200")
    print(f"Dataset-backed prediction: {historical_body['predicted_crop']}")


if __name__ == "__main__":
    main()
