#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402
from app.services.irrigation_weather_service import WeatherApiError  # noqa: E402
from app.services.irrigation_service import irrigation_service  # noqa: E402


VALID_PAYLOAD = {
    "Temperature_C": 27,
    "Humidity": 65,
    "Rainfall_mm": 10,
    "Sunlight_Hours": 8,
    "Soil_Type": "Clay",
    "Crop_Type": "Rice",
    "Crop_Growth_Stage": "Vegetative",
    "Season": "Kharif",
    "Soil_Moisture": 30,
    "Wind_Speed_kmh": 5,
    "Mulching_Used": "No",
}


class IrrigationPredictionValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        irrigation_service.load_model()
        self.client = TestClient(app)

    def test_model_status_and_weather_route_are_available(self) -> None:
        status = self.client.get("/api/model-status")
        self.assertEqual(status.status_code, 200)
        self.assertTrue(status.json()["irrigation_model"]["loaded"])
        weather_payload = {
            "Temperature_C": 25.2,
            "Humidity": 81.0,
            "Rainfall_mm": 3.4,
            "Sunlight_Hours": 11.3478,
            "Wind_Speed_kmh": 11.3,
            "measurement": {
                "date": "2024-06-15",
                "timezone": "UTC",
                "period": "one calendar day",
                "source": "Open-Meteo",
                "provider": "archive",
                "source_variables": {},
                "units": {},
                "not_mapped": ["Soil_Moisture"],
            },
        }
        with patch(
            "app.routes.irrigation.get_daily_weather",
            return_value=weather_payload,
        ):
            weather = self.client.get(
                "/api/irrigation/weather",
                params={
                    "latitude": 18.51957,
                    "longitude": 73.85535,
                    "date": "2024-06-15",
                },
            )
        self.assertEqual(weather.status_code, 200)
        self.assertTrue(weather.json()["success"])

    def test_valid_payload_still_returns_decoded_prediction(self) -> None:
        response = self.client.post("/api/irrigation/predict", json=VALID_PAYLOAD)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["prediction"], "Medium")
        self.assertAlmostEqual(sum(body["probabilities"].values()), 1.0, places=6)

    def test_boolean_is_rejected_for_every_numeric_field(self) -> None:
        numeric_fields = [
            "Temperature_C",
            "Humidity",
            "Rainfall_mm",
            "Sunlight_Hours",
            "Soil_Moisture",
            "Wind_Speed_kmh",
        ]
        for field in numeric_fields:
            with self.subTest(field=field):
                payload = dict(VALID_PAYLOAD)
                payload[field] = True
                response = self.client.post("/api/irrigation/predict", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertFalse(response.json()["success"])

    def test_nan_and_infinity_are_rejected(self) -> None:
        for field, value in (
            ("Temperature_C", "NaN"),
            ("Humidity", "Infinity"),
            ("Soil_Moisture", "-Infinity"),
        ):
            with self.subTest(field=field):
                payload = dict(VALID_PAYLOAD)
                payload[field] = value
                response = self.client.post("/api/irrigation/predict", json=payload)
                self.assertEqual(response.status_code, 400)

    def test_missing_extra_and_invalid_category_are_rejected(self) -> None:
        missing = dict(VALID_PAYLOAD)
        missing.pop("Humidity")
        response = self.client.post("/api/irrigation/predict", json=missing)
        self.assertEqual(response.status_code, 400)
        self.assertIn("missing_fields", response.json())

        extra = dict(VALID_PAYLOAD)
        extra["Extra"] = 1
        response = self.client.post("/api/irrigation/predict", json=extra)
        self.assertEqual(response.status_code, 400)
        self.assertIn("unexpected_fields", response.json())

        invalid = dict(VALID_PAYLOAD)
        invalid["Soil_Type"] = "Black"
        response = self.client.post("/api/irrigation/predict", json=invalid)
        self.assertEqual(response.status_code, 400)

    def test_predict_from_weather_preserves_caller_soil_moisture(self) -> None:
        weather = {
            "Temperature_C": 25.2,
            "Humidity": 81.0,
            "Rainfall_mm": 3.4,
            "Sunlight_Hours": 11.3478,
            "Wind_Speed_kmh": 11.3,
            "measurement": {
                "date": "2024-06-15",
                "timezone": "UTC",
                "period": "one calendar day",
                "source": "Open-Meteo",
                "provider": "archive",
                "units": {},
                "not_mapped": ["Soil_Moisture"],
            },
        }
        payload = {
            "state": "Maharashtra",
            "district": "PUNE",
            "Soil_Moisture": 42,
            "Soil_Type": "Clay",
            "Crop_Type": "Rice",
            "Crop_Growth_Stage": "Vegetative",
            "Season": "Kharif",
            "Mulching_Used": "No",
        }
        with (
            patch("app.routes.irrigation.geocode_district", return_value=(18.51957, 73.85535)),
            patch("app.routes.irrigation.get_daily_weather", return_value=weather),
        ):
            response = self.client.post(
                "/api/irrigation/predict-from-weather", json=payload
            )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["prediction"], "Medium")
        self.assertEqual(body["weather"]["measurement"]["not_mapped"], ["Soil_Moisture"])

    def test_district_state_mismatch_is_http_400(self) -> None:
        payload = {
            "state": "Maharashtra",
            "district": "MYSORE",
            "Soil_Moisture": 30,
            "Soil_Type": "Clay",
            "Crop_Type": "Rice",
            "Crop_Growth_Stage": "Vegetative",
            "Season": "Kharif",
            "Mulching_Used": "No",
        }
        response = self.client.post(
            "/api/irrigation/predict-from-weather", json=payload
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("does not match state", response.json()["error"])

    def test_geocoding_failure_is_http_502(self) -> None:
        payload = {
            "state": "Maharashtra",
            "district": "PUNE",
            "Soil_Moisture": 30,
            "Soil_Type": "Clay",
            "Crop_Type": "Rice",
            "Crop_Growth_Stage": "Vegetative",
            "Season": "Kharif",
            "Mulching_Used": "No",
        }
        with patch(
            "app.routes.irrigation.geocode_district",
            side_effect=WeatherApiError("District geocoding provider request failed"),
        ):
            response = self.client.post(
                "/api/irrigation/predict-from-weather", json=payload
            )
        self.assertEqual(response.status_code, 502)
        self.assertIn("geocoding", response.json()["error"])

    def test_weather_provider_failure_is_http_502(self) -> None:
        payload = {
            "state": "Maharashtra",
            "district": "PUNE",
            "Soil_Moisture": 30,
            "Soil_Type": "Clay",
            "Crop_Type": "Rice",
            "Crop_Growth_Stage": "Vegetative",
            "Season": "Kharif",
            "Mulching_Used": "No",
        }
        with (
            patch(
                "app.routes.irrigation.geocode_district",
                return_value=(18.51957, 73.85535),
            ),
            patch(
                "app.routes.irrigation.get_daily_weather",
                side_effect=WeatherApiError("Weather provider request failed"),
            ),
        ):
            response = self.client.post(
                "/api/irrigation/predict-from-weather", json=payload
            )
        self.assertEqual(response.status_code, 502)
        self.assertIn("Weather provider", response.json()["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
