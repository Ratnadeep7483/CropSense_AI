"""EfficientNet-B0 plant disease classification model loading and inference."""

import json
import logging
from io import BytesIO
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_MODEL_DIR = Path(__file__).resolve().parent.parent / "ml" / "disease"
_CHECKPOINT_PATH = _MODEL_DIR / "plant_disease_efficientnet_b0.pth"
_LABELS_PATH = _MODEL_DIR / "disease_labels.json"
_MAX_IMAGE_PIXELS = 40_000_000
_SUPPORTED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
_EXPECTED_NUM_CLASSES = 38
_NORMALIZE_MEAN = [0.485, 0.456, 0.406]
_NORMALIZE_STD = [0.229, 0.224, 0.225]


class DiseaseImageError(ValueError):
    """Raised when an upload is not a supported, decodable image."""


class DiseaseService:
    """Singleton-style service that loads the disease model once at startup."""

    def __init__(self) -> None:
        self._model: Any | None = None
        self._torch: Any | None = None
        self._transform: Any | None = None
        self._labels: list[str] = []
        self._is_loaded = False
        self._load_error: str | None = None

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def load_error(self) -> str | None:
        return self._load_error

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(self._labels)

    def load_model(self) -> None:
        """Load the checkpoint and construct the matching EfficientNet-B0."""
        if self._is_loaded:
            return

        self._model = None
        self._torch = None
        self._transform = None
        self._labels = []
        self._load_error = None

        if not _CHECKPOINT_PATH.is_file():
            self._load_error = f"Disease model checkpoint not found: {_CHECKPOINT_PATH}"
            logger.warning(self._load_error)
            return
        if not _LABELS_PATH.is_file():
            self._load_error = f"Disease labels file not found: {_LABELS_PATH}"
            logger.warning(self._load_error)
            return

        try:
            import torch
            from torch import nn
            from torchvision import models, transforms

            labels_data = json.loads(_LABELS_PATH.read_text(encoding="utf-8"))
            if (
                not isinstance(labels_data, list)
                or len(labels_data) != _EXPECTED_NUM_CLASSES
                or any(not isinstance(label, str) or not label.strip() for label in labels_data)
                or len(set(labels_data)) != len(labels_data)
            ):
                raise ValueError(
                    f"Disease labels must be {_EXPECTED_NUM_CLASSES} unique, "
                    "non-empty strings in classifier output order."
                )
            if any(label.count("___") != 1 for label in labels_data):
                raise ValueError(
                    "Each disease label must contain one crop/disease separator '___'."
                )

            checkpoint = torch.load(
                _CHECKPOINT_PATH,
                map_location="cpu",
                weights_only=True,
            )
            if not isinstance(checkpoint, dict):
                raise ValueError("Disease checkpoint must contain a state dictionary.")

            model = models.efficientnet_b0(weights=None)
            model.classifier[1] = nn.Linear(
                model.classifier[1].in_features,
                len(labels_data),
            )
            model.load_state_dict(checkpoint, strict=True)
            model.eval()

            self._torch = torch
            self._model = model
            self._transform = transforms.Compose(
                [
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=_NORMALIZE_MEAN,
                        std=_NORMALIZE_STD,
                    ),
                ]
            )
            self._labels = labels_data
            self._is_loaded = True
            logger.info(
                "EfficientNet-B0 disease classifier loaded with %d labels.",
                len(labels_data),
            )
        except Exception as exc:
            self._model = None
            self._torch = None
            self._transform = None
            self._labels = []
            self._load_error = f"Failed to load disease model: {exc}"
            logger.error(self._load_error, exc_info=True)

    def predict(self, image_bytes: bytes) -> tuple[str, str, float]:
        """Validate an image and return crop, disease, and confidence (0-1)."""
        if (
            not self._is_loaded
            or self._model is None
            or self._torch is None
            or self._transform is None
        ):
            raise RuntimeError(self._load_error or "Disease model is not loaded.")

        from PIL import Image, UnidentifiedImageError

        try:
            with Image.open(BytesIO(image_bytes)) as image:
                if image.format not in _SUPPORTED_IMAGE_FORMATS:
                    raise DiseaseImageError("Upload a JPEG, PNG, or WebP image.")
                width, height = image.size
                if (
                    width <= 0
                    or height <= 0
                    or width * height > _MAX_IMAGE_PIXELS
                ):
                    raise DiseaseImageError(
                        "Image dimensions are invalid or exceed 40 megapixels."
                    )
                image.verify()

            with Image.open(BytesIO(image_bytes)) as image:
                rgb_image = image.convert("RGB")
                rgb_image.load()
        except DiseaseImageError:
            raise
        except (
            Image.DecompressionBombError,
            OSError,
            UnidentifiedImageError,
            ValueError,
        ) as exc:
            raise DiseaseImageError(
                "The uploaded file is not a valid, decodable image."
            ) from exc

        input_tensor = self._transform(rgb_image).unsqueeze(0)
        with self._torch.inference_mode():
            probabilities = self._torch.softmax(self._model(input_tensor), dim=1)[0]
            confidence, predicted_index = self._torch.max(probabilities, dim=0)

        label = self._labels[int(predicted_index.item())]
        predicted_crop, disease_name = label.split("___", maxsplit=1)
        predicted_crop = predicted_crop.replace("_", " ").strip()
        disease_name = disease_name.rstrip("_").replace("_", " ").strip()
        return predicted_crop, disease_name, float(confidence.item())


disease_service = DiseaseService()
