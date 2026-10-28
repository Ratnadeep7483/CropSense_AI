"""
Fertilizer Recommendation Service.

Loads the trained XGBoost fertilizer model along with its saved
preprocessing artifacts (preprocessor, label encoder, feature config)
and provides inference through the `predict` method.

Required files in app/ml/fertilizer/:
    fertilizer_xgboost.json
    fertilizer_model_metadata.json

Required files in app/ml/fertilizer/preprocessing/:
    fertilizer_feature_config.json
    fertilizer_label_encoder.joblib
    fertilizer_preprocessor.joblib
"""

import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

from app.schemas.fertilizer import FertilizerRecommendationRequest

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────
_ML_DIR = Path(__file__).resolve().parent.parent / "ml" / "fertilizer"
_MODEL_PATH = _ML_DIR / "fertilizer_xgboost.json"
_METADATA_PATH = _ML_DIR / "fertilizer_model_metadata.json"
_PREPROC_DIR = _ML_DIR / "preprocessing"
_FEATURE_CONFIG_PATH = _PREPROC_DIR / "fertilizer_feature_config.json"
_LABEL_ENCODER_PATH = _PREPROC_DIR / "fertilizer_label_encoder.joblib"
_PREPROCESSOR_PATH = _PREPROC_DIR / "fertilizer_preprocessor.joblib"

# All files that must be present for the service to work
_REQUIRED_FILES: list[Path] = [
    _MODEL_PATH,
    _METADATA_PATH,
    _FEATURE_CONFIG_PATH,
    _LABEL_ENCODER_PATH,
    _PREPROCESSOR_PATH,
]


class FertilizerService:
    """Singleton-style service that holds the loaded fertilizer model."""

    def __init__(self) -> None:
        self._model: xgb.Booster | None = None
        self._preprocessor: object | None = None
        self._label_encoder: object | None = None
        self._feature_config: dict | None = None
        self._metadata: dict | None = None
        self._is_loaded: bool = False
        self._load_error: str | None = None

    # ── Public properties ────────────────────────────────────────
    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def load_error(self) -> str | None:
        return self._load_error

    @property
    def preprocessor_loaded(self) -> bool:
        return self._preprocessor is not None

    @property
    def label_encoder_loaded(self) -> bool:
        return self._label_encoder is not None

    # ── Model loading ────────────────────────────────────────────
    def load_model(self) -> None:
        """Attempt to load all fertilizer model artifacts from disk.

        Called once at application startup.  If any required file has
        not been placed yet, the service records a human-readable
        error but does NOT crash the server.
        """
        self._model = None
        self._preprocessor = None
        self._label_encoder = None
        self._feature_config = None
        self._metadata = None
        self._is_loaded = False
        self._load_error = None

        missing: list[str] = [
            str(p) for p in _REQUIRED_FILES if not p.exists()
        ]

        if missing:
            self._load_error = (
                "Fertilizer model files not found. Please copy the following "
                "files into the indicated locations:\n"
                + "\n".join(f"  MISSING: {p}" for p in missing)
            )
            logger.warning(self._load_error)
            return

        try:
            # 1. Load feature configuration
            with open(_FEATURE_CONFIG_PATH, encoding="utf-8") as f:
                self._feature_config = json.load(f)
            logger.info("Fertilizer feature config loaded.")

            # 2. Load metadata
            with open(_METADATA_PATH, encoding="utf-8") as f:
                self._metadata = json.load(f)
            logger.info("Fertilizer model metadata loaded.")

            # 3. Load preprocessing pipeline
            self._preprocessor = joblib.load(_PREPROCESSOR_PATH)
            logger.info("Fertilizer preprocessor loaded.")

            # 4. Load label encoder
            self._label_encoder = joblib.load(_LABEL_ENCODER_PATH)
            logger.info("Fertilizer label encoder loaded.")

            # 5. Load the XGBoost model
            booster = xgb.Booster()
            booster.load_model(str(_MODEL_PATH))

            numerical_features = self._feature_config.get("numerical_features")
            categorical_features = self._feature_config.get("categorical_features")
            feature_order = self._feature_config.get("all_features")
            preprocessor_features = getattr(
                self._preprocessor, "feature_names_in_", None
            )
            if (
                not isinstance(numerical_features, list)
                or not isinstance(categorical_features, list)
                or not isinstance(feature_order, list)
                or feature_order != numerical_features + categorical_features
                or len(feature_order) != 10
                or self._feature_config.get("original_feature_count") != 10
                or self._metadata.get("feature_count") != 10
                or preprocessor_features is None
                or list(preprocessor_features) != feature_order
            ):
                raise ValueError(
                    "Fertilizer input feature configuration, metadata, and "
                    "preprocessor must agree on the ordered 10 input features."
                )

            transformed_feature_count = self._feature_config.get(
                "transformed_feature_count"
            )
            if (
                transformed_feature_count != 44
                or self._metadata.get("transformed_feature_count") != 44
                or len(self._preprocessor.get_feature_names_out()) != 44
                or booster.num_features() != 44
            ):
                raise ValueError(
                    "Fertilizer preprocessor and model must agree on 44 "
                    "transformed features."
                )

            configured_classes = self._feature_config.get("classes")
            metadata_classes = self._metadata.get("classes")
            encoder_classes = getattr(self._label_encoder, "classes_", None)
            if (
                not isinstance(configured_classes, list)
                or configured_classes != metadata_classes
                or encoder_classes is None
                or encoder_classes.tolist() != configured_classes
                or self._feature_config.get("number_of_classes")
                != len(configured_classes)
            ):
                raise ValueError(
                    "Fertilizer label encoder classes do not match the "
                    "feature config and model metadata."
                )

            self._model = booster
            self._is_loaded = True
            logger.info("Fertilizer XGBoost model loaded.")
            logger.info(
                "Fertilizer recommendation service fully loaded."
            )
        except Exception as exc:
            self._model = None
            self._preprocessor = None
            self._label_encoder = None
            self._feature_config = None
            self._metadata = None
            self._is_loaded = False
            self._load_error = f"Failed to load fertilizer model: {exc}"
            logger.error(self._load_error, exc_info=True)

    # ── Prediction ───────────────────────────────────────────────
    def predict(self, request: FertilizerRecommendationRequest) -> str:
        """Run inference on the loaded model.

        Applies the saved preprocessing pipeline, runs XGBoost
        prediction, and decodes the label with the saved encoder.

        Returns the predicted fertilizer name as a string.
        Raises RuntimeError if the model is not loaded.
        """
        if not self._is_loaded or self._model is None:
            raise RuntimeError(
                self._load_error
                or "Fertilizer model is not loaded. Please copy the model files."
            )

        # Build a single-row DataFrame preserving the column names
        # expected by the saved preprocessor.
        input_data = pd.DataFrame([{
            "Temperature": request.temperature,
            "Moisture": request.moisture,
            "Rainfall": request.rainfall,
            "PH": request.ph,
            "Nitrogen": request.nitrogen,
            "Phosphorous": request.phosphorous,
            "Potassium": request.potassium,
            "Carbon": request.carbon,
            "Soil": request.soil,
            "Crop": request.crop,
        }])

        # If the feature config specifies column order, reorder
        if self._feature_config and "feature_order" in self._feature_config:
            ordered_cols = self._feature_config["feature_order"]
            # Only use columns that exist in input_data
            valid_cols = [c for c in ordered_cols if c in input_data.columns]
            input_data = input_data[valid_cols]

        # Apply the saved preprocessing pipeline
        try:
            transformed = self._preprocessor.transform(input_data)  # type: ignore[union-attr]
        except Exception as exc:
            raise RuntimeError(
                f"Preprocessing failed: {exc}. "
                "Make sure input values match the training data format."
            ) from exc

        # Convert to DMatrix for XGBoost
        dmatrix = xgb.DMatrix(transformed)
        raw_prediction = self._model.predict(dmatrix)

        # Determine class index
        if raw_prediction.ndim == 2:
            class_idx = int(np.argmax(raw_prediction, axis=1)[0])
        else:
            class_idx = int(raw_prediction[0])

        # Decode with label encoder
        try:
            label = self._label_encoder.inverse_transform([class_idx])  # type: ignore[union-attr]
            return str(label[0])
        except Exception as exc:
            raise RuntimeError(
                f"Fertilizer label decoding failed for class index {class_idx}."
            ) from exc


# ── Module-level singleton ───────────────────────────────────────
fertilizer_service = FertilizerService()
