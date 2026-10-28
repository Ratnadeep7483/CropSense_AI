#!/usr/bin/env python3
"""Focused API tests for fertilizer recommendations."""

import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402
from app.schemas.fertilizer import FertilizerRecommendationResponse  # noqa: E402
from app.services.fertilizer_service import fertilizer_service  # noqa: E402


class FertilizerRecommendationApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_context.__exit__(None, None, None)

    def setUp(self) -> None:
        self.request = {
            "temperature": 30.0,
            "moisture": 55.0,
            "rainfall": 120.0,
            "ph": 6.8,
            "nitrogen": 50.0,
            "phosphorous": 40.0,
            "potassium": 45.0,
            "carbon": 1.2,
            "soil": "Loamy Soil",
            "crop": "Rice",
        }

    def test_valid_input_returns_decoded_recommended_fertilizer(self) -> None:
        response = self.client.post(
            "/api/fertilizer/recommend",
            json=self.request,
        )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        validated = FertilizerRecommendationResponse.model_validate(body)
        self.assertEqual(set(body), {"success", "recommended_fertilizer"})
        self.assertTrue(validated.success)
        self.assertIn(
            validated.recommended_fertilizer,
            fertilizer_service._label_encoder.classes_,
        )
        self.assertFalse(validated.recommended_fertilizer.isdigit())

    def test_missing_field_returns_422(self) -> None:
        request = self.request.copy()
        del request["carbon"]

        response = self.client.post("/api/fertilizer/recommend", json=request)

        self.assertEqual(response.status_code, 422, response.text)

    def test_invalid_numeric_value_returns_422(self) -> None:
        request = self.request.copy()
        request["nitrogen"] = "not-a-number"

        response = self.client.post("/api/fertilizer/recommend", json=request)

        self.assertEqual(response.status_code, 422, response.text)


if __name__ == "__main__":
    unittest.main()
