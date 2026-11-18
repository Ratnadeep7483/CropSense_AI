#!/usr/bin/env python3
"""Verify plant disease model loading, label mapping, and HTTP inference."""

import io
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402
from app.services.disease_service import disease_service  # noqa: E402

ENDPOINT = "/api/disease/predict"


def _image_bytes() -> bytes:
    image = Image.new("RGB", (64, 48), color=(74, 128, 42))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _display_name(value: str) -> str:
    return value.rstrip("_").replace("_", " ").strip()


def main() -> None:
    with TestClient(app) as client:
        if not disease_service.is_loaded:
            raise AssertionError(
                f"Disease model did not load: {disease_service.load_error}"
            )
        if len(disease_service.labels) != 38:
            raise AssertionError(
                f"Expected 38 class labels, found {len(disease_service.labels)}"
            )

        image_bytes = _image_bytes()
        from PIL import Image as PillowImage

        with PillowImage.open(io.BytesIO(image_bytes)) as image:
            input_tensor = disease_service._transform(image.convert("RGB"))
        if tuple(input_tensor.shape) != (3, 224, 224):
            raise AssertionError(f"Unexpected transformed shape: {input_tensor.shape}")

        torch = disease_service._torch
        with torch.inference_mode():
            logits = disease_service._model(input_tensor.unsqueeze(0))[0]
            probabilities = torch.softmax(logits, dim=0)
            predicted_index = int(torch.argmax(probabilities).item())
        crop_label, disease_label = disease_service.labels[predicted_index].split(
            "___", maxsplit=1
        )

        response = client.post(
            ENDPOINT,
            files={"image": ("plant.png", image_bytes, "image/png")},
        )
        if response.status_code != 200:
            raise AssertionError(
                f"Disease API failed ({response.status_code}): {response.text}"
            )
        body = response.json()
        expected = {
            "success": True,
            "predicted_crop": _display_name(crop_label),
            "predicted_disease": _display_name(disease_label),
        }
        if any(body.get(key) != value for key, value in expected.items()):
            raise AssertionError(
                f"Response does not match model output index {predicted_index}: "
                f"expected {expected}, received {body}"
            )
        if abs(body["confidence"] - float(probabilities[predicted_index].item())) > 1e-6:
            raise AssertionError("Response confidence does not match model score.")
        if not 0 <= body["confidence"] <= 1:
            raise AssertionError(f"Invalid confidence value: {body['confidence']}")

        invalid_response = client.post(
            ENDPOINT,
            files={"image": ("invalid.png", b"not an image", "image/png")},
        )
        if invalid_response.status_code != 422:
            raise AssertionError(
                "Invalid image should return HTTP 422; got "
                f"{invalid_response.status_code}: {invalid_response.text}"
            )

    print(f"Endpoint: POST {ENDPOINT}")
    print(f"Labels mapped: {len(disease_service.labels)}")
    print(f"Prediction: {body}")
    print("Invalid-image validation: HTTP 422")


if __name__ == "__main__":
    main()
