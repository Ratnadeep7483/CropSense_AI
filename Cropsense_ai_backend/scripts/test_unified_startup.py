#!/usr/bin/env python3

import json
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_ROOT = BACKEND_ROOT.parent / "Cropsense_ai_frontend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402
from app.services.irrigation_service import irrigation_service  # noqa: E402


class UnifiedStartupTests(unittest.TestCase):
    def test_dev_full_is_the_single_startup_command(self) -> None:
        package = json.loads(
            (FRONTEND_ROOT / "package.json").read_text(encoding="utf-8")
        )
        dev_full = package["scripts"]["dev:full"]
        self.assertIn("uvicorn app.main:app", dev_full)
        self.assertIn("--port 8001", dev_full)
        self.assertIn("npm run dev", dev_full)
        self.assertIn("--port 5173", dev_full)
        self.assertNotIn("irrigation_api.py", dev_full)
        self.assertNotIn("port 8002", dev_full)

    def test_unified_backend_exposes_health_models_and_irrigation(self) -> None:
        irrigation_service.load_model()
        client = TestClient(app)

        health = client.get("/health")
        self.assertEqual(health.status_code, 200)

        location_options = client.get(
            "/api/crop/location-options",
            params={"state_names": "Haryana"},
        )
        self.assertEqual(location_options.status_code, 200)
        self.assertIn("KARNAL", location_options.json()["districts"])

        status = client.get("/api/model-status")
        self.assertEqual(status.status_code, 200)
        self.assertTrue(status.json()["irrigation_model"]["loaded"])

        direct = client.post(
            "/api/irrigation/predict",
            json={
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
            },
        )
        self.assertEqual(direct.status_code, 200)
        self.assertEqual(direct.json()["prediction"], "Medium")


if __name__ == "__main__":
    unittest.main(verbosity=2)
