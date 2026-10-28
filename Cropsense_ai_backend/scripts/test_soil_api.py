#!/usr/bin/env python3
"""Exercise soil classification with a user-provided real soil image."""

import argparse
import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402
from app.services.soil_service import soil_service  # noqa: E402

ENDPOINT = "/api/soil/predict"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Path to a real soil image")
    image_path = parser.parse_args().image
    if not image_path.is_file():
        raise FileNotFoundError(f"Soil image not found: {image_path}")

    with TestClient(app) as client:
        with image_path.open("rb") as image_file:
            response = client.post(
                ENDPOINT,
                files={
                    "image": (
                        image_path.name,
                        image_file,
                    )
                },
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"Soil API request failed ({response.status_code}): "
                f"{response.text}"
            )

        body = response.json()
        if body.get("success") is not True:
            raise AssertionError(f"Unexpected soil API response: {body}")
        if body.get("predicted_class") not in soil_service.class_names:
            raise AssertionError(
                f"Predicted class is not in the checkpoint mapping: {body}"
            )
        confidence = body.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise AssertionError(f"Invalid prediction confidence: {body}")

        invalid_response = client.post(
            ENDPOINT,
            files={"image": ("invalid.jpg", b"not an image", "image/jpeg")},
        )
        if invalid_response.status_code != 422:
            raise AssertionError(
                "Invalid image should return HTTP 422; got "
                f"{invalid_response.status_code}: {invalid_response.text}"
            )

    print(f"Endpoint: POST {ENDPOINT}")
    print(f"Image: {image_path}")
    print(f"Response: {body}")
    print("Invalid-image validation: HTTP 422")


if __name__ == "__main__":
    main()
