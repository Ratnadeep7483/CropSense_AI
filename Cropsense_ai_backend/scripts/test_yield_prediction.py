#!/usr/bin/env python3
"""Focused API checks for the saved LightGBM yield model."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import _DEFAULT_ALLOWED_ORIGINS, _get_allowed_origins, app  # noqa: E402
import app.services.yield_prediction_service as yield_service_module  # noqa: E402
from app.services.yield_prediction_service import (  # noqa: E402
    YieldPredictionService,
    yield_prediction_service,
)


class YieldPredictionApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_context.__exit__(None, None, None)

    def test_options_return_saved_category_schema(self) -> None:
        response = self.client.get("/api/yield/options")

        self.assertEqual(response.status_code, 200, response.text)
        features = response.json()["features"]
        self.assertEqual(
            list(features),
            ["Crop", "State_Name", "District_Name", "Season"],
        )
        self.assertEqual(len(features["Crop"]), 104)
        self.assertEqual(len(features["State_Name"]), 33)
        self.assertEqual(len(features["District_Name"]), 646)
        self.assertEqual(len(features["Season"]), 6)
        districts_by_state = response.json()["districts_by_state"]
        self.assertEqual(len(districts_by_state), 33)
        self.assertEqual(
            sum(len(districts) for districts in districts_by_state.values()),
            652,
        )
        self.assertIn("KRISHNA", districts_by_state["Andhra Pradesh"])
        self.assertNotIn("KRISHNA", districts_by_state["Assam"])

    def test_model_status_reports_yield_model(self) -> None:
        response = self.client.get("/api/model-status")

        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["yield_model"]["loaded"])

    def test_cors_configuration_uses_explicit_origins(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(_get_allowed_origins(), list(_DEFAULT_ALLOWED_ORIGINS))

        allowed_response = self.client.get(
            "/api/yield/options",
            headers={"Origin": "http://localhost:5173"},
        )
        blocked_response = self.client.get(
            "/api/yield/options",
            headers={"Origin": "https://untrusted.example"},
        )
        self.assertEqual(
            allowed_response.headers.get("access-control-allow-origin"),
            "http://localhost:5173",
        )
        self.assertNotIn("access-control-allow-origin", blocked_response.headers)

        with patch.dict(
            "os.environ",
            {"CORS_ORIGINS": " https://app.example.com/ , https://admin.example.com "},
            clear=True,
        ):
            self.assertEqual(
                _get_allowed_origins(),
                ["https://app.example.com", "https://admin.example.com"],
            )

        with patch.dict("os.environ", {"CORS_ORIGINS": "*"}, clear=True):
            with self.assertRaises(ValueError):
                _get_allowed_origins()
        with patch.dict(
            "os.environ",
            {"CORS_ORIGINS": "https://app.example.com/path"},
            clear=True,
        ):
            with self.assertRaises(ValueError):
                _get_allowed_origins()

    def test_unavailable_model_returns_safe_503(self) -> None:
        with (
            patch.object(yield_prediction_service, "_is_loaded", False),
            patch.object(
                yield_prediction_service,
                "_load_error",
                "Missing artifact at C:\\private\\deployment\\model.joblib",
            ),
        ):
            response = self.client.get("/api/yield/options")
            status_response = self.client.get("/api/model-status")

        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private", response.text)
        self.assertEqual(
            response.json()["detail"]["error"],
            "Yield prediction model is not available.",
        )
        self.assertNotIn("private", status_response.text)
        self.assertEqual(
            status_response.json()["yield_model"]["error"],
            "Model is not available. Check server logs.",
        )

    def test_missing_model_files_leave_service_unavailable(self) -> None:
        service = YieldPredictionService()
        missing_path = BACKEND_ROOT / "missing-yield-artifact"
        with (
            patch.object(yield_service_module, "_MODEL_PATH", missing_path),
            patch.object(yield_service_module, "_METADATA_PATH", missing_path),
            patch.object(yield_service_module, "_LOCATION_DATA_PATH", missing_path),
        ):
            service.load_model()

        self.assertFalse(service.is_loaded)
        self.assertIn("Yield model files not found", service.load_error or "")

    def test_inference_error_returns_safe_500(self) -> None:
        request = {
            "Crop": "Rice",
            "State_Name": "Andhra Pradesh",
            "District_Name": "KRISHNA",
            "Season": "Kharif",
        }
        with patch.object(
            yield_prediction_service,
            "predict",
            side_effect=ValueError("private internal failure"),
        ):
            response = self.client.post("/api/yield/predict", json=request)

        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private internal failure", response.text)
        self.assertEqual(
            response.json()["detail"]["error"],
            "Yield prediction failed due to an internal error.",
        )

    def test_openapi_documents_http_error_envelopes(self) -> None:
        schema = self.client.get("/openapi.json").json()
        predict_responses = schema["paths"]["/api/yield/predict"]["post"]["responses"]

        self.assertIn(
            "oneOf",
            predict_responses["422"]["content"]["application/json"]["schema"],
        )
        self.assertEqual(
            predict_responses["503"]["content"]["application/json"]["schema"]["$ref"],
            "#/components/schemas/YieldHTTPErrorResponse",
        )

    def test_verified_example_and_case_normalization(self) -> None:
        request = {
            "Crop": "Rice",
            "State_Name": "Andhra Pradesh",
            "District_Name": "KRISHNA",
            "Season": "Kharif",
        }
        response = self.client.post("/api/yield/predict", json=request)

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertAlmostEqual(body["predicted_yield_per_area"], 3.0835, places=4)
        self.assertEqual(body["features"], request)
        self.assertEqual(body["target"], "yield_per_area")

        normalized_response = self.client.post(
            "/api/yield/predict",
            json={key: value.lower() for key, value in request.items()},
        )
        self.assertEqual(normalized_response.status_code, 200)
        self.assertEqual(
            normalized_response.json()["features"],
            request,
        )
        self.assertEqual(
            normalized_response.json()["predicted_yield_per_area"],
            body["predicted_yield_per_area"],
        )

    def test_unsupported_category_and_extra_feature_are_rejected(self) -> None:
        request = {
            "Crop": "not a saved crop",
            "State_Name": "Andhra Pradesh",
            "District_Name": "KRISHNA",
            "Season": "Kharif",
        }
        unsupported_response = self.client.post(
            "/api/yield/predict",
            json=request,
        )
        self.assertEqual(unsupported_response.status_code, 422)

        request["Crop"] = "Rice"
        request["Year"] = "2015"
        extra_response = self.client.post("/api/yield/predict", json=request)
        self.assertEqual(extra_response.status_code, 422)

    def test_unobserved_state_district_pair_is_rejected(self) -> None:
        response = self.client.post(
            "/api/yield/predict",
            json={
                "Crop": "Rice",
                "State_Name": "Assam",
                "District_Name": "KRISHNA",
                "Season": "Kharif",
            },
        )

        self.assertEqual(response.status_code, 422, response.text)
        self.assertIn(
            "not observed for the selected state",
            response.json()["detail"]["detail"],
        )


if __name__ == "__main__":
    unittest.main()
