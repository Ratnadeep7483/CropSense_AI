"""EfficientNet-B2 soil classification model loading and inference."""

import logging
from io import BytesIO
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_MODEL_DIR = Path(__file__).resolve().parent.parent / "ml" / "soil"
_CHECKPOINT_PATH = _MODEL_DIR / "efficientnet_b2_soil_best.pth"
_MAX_IMAGE_PIXELS = 40_000_000
_SUPPORTED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
_EXPECTED_ARCHITECTURE = "efficientnet-b2"
_EXPECTED_INPUT_SIZE = 288
_EXPECTED_NUM_CLASSES = 6


class SoilImageError(ValueError):
    """Raised when an upload is not a supported, decodable image."""


class SoilService:
    """Singleton-style service that loads the soil model once at startup."""

    def __init__(self) -> None:
        self._model: Any | None = None
        self._torch: Any | None = None
        self._transform: Any | None = None
        self._class_names_by_index: list[str] = []
        self._is_loaded = False
        self._load_error: str | None = None

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def load_error(self) -> str | None:
        return self._load_error

    @property
    def class_names(self) -> tuple[str, ...]:
        return tuple(self._class_names_by_index)

    def load_model(self) -> None:
        """Load only tensor/state-dict checkpoint data and build the model."""
        if self._is_loaded:
            return

        self._model = None
        self._torch = None
        self._transform = None
        self._class_names_by_index = []
        self._load_error = None

        if not _CHECKPOINT_PATH.is_file():
            self._load_error = (
                f"Soil model checkpoint not found: {_CHECKPOINT_PATH}"
            )
            logger.warning(self._load_error)
            return

        try:
            import torch
            from torch import nn
            from torchvision import models, transforms

            checkpoint = torch.load(
                _CHECKPOINT_PATH,
                map_location="cpu",
                weights_only=True,
            )
            if not isinstance(checkpoint, dict):
                raise ValueError("Soil checkpoint must contain a dictionary.")

            architecture = checkpoint.get("architecture")
            if (
                not isinstance(architecture, str)
                or architecture.casefold() != _EXPECTED_ARCHITECTURE
            ):
                raise ValueError(
                    f"Unsupported soil model architecture: {architecture!r}."
                )

            num_classes = checkpoint.get("num_classes")
            input_size = checkpoint.get("input_size")
            if num_classes != _EXPECTED_NUM_CLASSES:
                raise ValueError(
                    f"Expected {_EXPECTED_NUM_CLASSES} soil classes, "
                    f"found {num_classes!r}."
                )
            if input_size != _EXPECTED_INPUT_SIZE:
                raise ValueError(
                    f"Expected input size {_EXPECTED_INPUT_SIZE}, "
                    f"found {input_size!r}."
                )

            class_to_idx = checkpoint.get("class_to_idx")
            class_names = checkpoint.get("class_names")
            if (
                not isinstance(class_to_idx, dict)
                or not isinstance(class_names, list)
                or len(class_names) != num_classes
                or any(not isinstance(name, str) for name in class_names)
                or len(set(class_names)) != num_classes
                or len(class_to_idx) != num_classes
            ):
                raise ValueError("Soil checkpoint class metadata is invalid.")

            class_names_by_index = [""] * num_classes
            for name, index in class_to_idx.items():
                if (
                    not isinstance(name, str)
                    or type(index) is not int
                    or index < 0
                    or index >= num_classes
                    or class_names_by_index[index]
                ):
                    raise ValueError("Soil checkpoint class mapping is invalid.")
                class_names_by_index[index] = name
            if (
                any(not name for name in class_names_by_index)
                or set(class_names_by_index) != set(class_names)
            ):
                raise ValueError(
                    "Soil checkpoint class names and mapping do not agree."
                )

            model = models.efficientnet_b2(weights=None)
            model.classifier[1] = nn.Linear(
                model.classifier[1].in_features,
                num_classes,
            )
            state_dict = checkpoint.get("model_state_dict")
            if not isinstance(state_dict, dict):
                raise ValueError("Soil checkpoint has no model_state_dict.")
            model.load_state_dict(state_dict, strict=True)
            model.eval()

            self._torch = torch
            self._model = model
            self._transform = transforms.Compose(
                [
                    transforms.Resize((input_size, input_size)),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225],
                    ),
                ]
            )
            self._class_names_by_index = class_names_by_index
            self._is_loaded = True
            logger.info(
                "EfficientNet-B2 soil classifier loaded with classes: %s",
                class_names_by_index,
            )
        except Exception as exc:
            self._model = None
            self._torch = None
            self._transform = None
            self._class_names_by_index = []
            self._load_error = f"Failed to load soil model: {exc}"
            logger.error(self._load_error, exc_info=True)

    def predict(self, image_bytes: bytes) -> tuple[str, float]:
        """Validate an image and return the predicted class and confidence."""
        if (
            not self._is_loaded
            or self._model is None
            or self._torch is None
            or self._transform is None
        ):
            raise RuntimeError(self._load_error or "Soil model is not loaded.")

        from PIL import Image, UnidentifiedImageError

        try:
            with Image.open(BytesIO(image_bytes)) as image:
                if image.format not in _SUPPORTED_IMAGE_FORMATS:
                    raise SoilImageError(
                        "Upload a JPEG, PNG, or WebP image."
                    )
                width, height = image.size
                if (
                    width <= 0
                    or height <= 0
                    or width * height > _MAX_IMAGE_PIXELS
                ):
                    raise SoilImageError(
                        "Image dimensions are invalid or exceed 40 megapixels."
                    )
                image.verify()

            with Image.open(BytesIO(image_bytes)) as image:
                rgb_image = image.convert("RGB")
                rgb_image.load()
        except SoilImageError:
            raise
        except (
            Image.DecompressionBombError,
            OSError,
            UnidentifiedImageError,
            ValueError,
        ) as exc:
            raise SoilImageError(
                "The uploaded file is not a valid, decodable image."
            ) from exc

        input_tensor = self._transform(rgb_image).unsqueeze(0)
        with self._torch.inference_mode():
            probabilities = self._torch.softmax(
                self._model(input_tensor), dim=1
            )[0]
            confidence, predicted_index = self._torch.max(probabilities, dim=0)

        return (
            self._class_names_by_index[int(predicted_index.item())],
            float(confidence.item()),
        )


soil_service = SoilService()
