"""
Crop Recommendation Service.

Loads the deployed crop model, preprocessor, and label encoder from
app/ml/crop/model_artifacts/ and provides inference through `predict`.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.schemas.crop import CropRecommendationRequest

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────
_ARTIFACT_DIR = (
    Path(__file__).resolve().parent.parent
    / "ml"
    / "crop"
    / "model_artifacts"
)
_MODEL_PATH = _ARTIFACT_DIR / "crop_xgboost_model.joblib"
_PREPROCESSOR_PATH = _ARTIFACT_DIR / "crop_preprocessor.joblib"
_LABEL_ENCODER_PATH = _ARTIFACT_DIR / "crop_label_encoder.joblib"
_LOCATION_DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "Copy of crop_recommendation_45_with_year_area.csv"
)

FEATURE_COLUMNS: list[str] = [
    "state_names",
    "district_names",
    "season_names",
    "soil_for_crop",
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "rainfall_mm",
    "crop_year",
    "area",
]

_REQUEST_FIELD_ALIASES = {
    "N": "nitrogen",
    "P": "phosphorous",
    "K": "potassium",
    "rainfall_mm": "rainfall",
}

CATEGORICAL_FEATURES = (
    "state_names",
    "district_names",
    "season_names",
    "soil_for_crop",
)


@lru_cache(maxsize=1)
def _load_crop_location_pairs() -> frozenset[tuple[str, str]]:
    """Load exact state/district pairs from the crop feature dataset."""
    try:
        locations = pd.read_csv(
            _LOCATION_DATASET_PATH,
            usecols=["state_names", "district_names"],
        )
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        raise RuntimeError(
            f"Crop location validation data is unavailable: {_LOCATION_DATASET_PATH}"
        ) from exc

    if locations[["state_names", "district_names"]].isna().any().any():
        raise RuntimeError("Crop location validation data contains blank labels.")

    return frozenset(
        (str(state), str(district))
        for state, district in locations.drop_duplicates().itertuples(
            index=False, name=None
        )
    )


class CropService:
    """Singleton-style service that holds the loaded crop model."""

    def __init__(self) -> None:
        self._model: Any | None = None
        self._preprocessor: Any | None = None
        self._label_encoder: Any | None = None
        self._is_loaded: bool = False
        self._load_error: str | None = None

    # ── Public properties ────────────────────────────────────────
    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def load_error(self) -> str | None:
        return self._load_error

    # ── Model loading ────────────────────────────────────────────
    def load_model(self) -> None:
        """Load the crop model and its preprocessing artifacts.

        Called once at application startup.  If the model files have
        not been placed yet, the service records a human-readable
        error but does NOT crash the server.
        """
        self._model = None
        self._preprocessor = None
        self._label_encoder = None
        self._is_loaded = False
        self._load_error = None

        missing = [
            str(path)
            for path in (_MODEL_PATH, _PREPROCESSOR_PATH, _LABEL_ENCODER_PATH)
            if not path.is_file()
        ]

        if missing:
            self._load_error = (
                "Crop model artifacts not found:\n"
                + "\n".join(f"  MISSING: {p}" for p in missing)
            )
            logger.warning(self._load_error)
            return

        loading_path = _MODEL_PATH
        try:
            self._model = joblib.load(loading_path)
            loading_path = _PREPROCESSOR_PATH
            self._preprocessor = joblib.load(loading_path)
            loading_path = _LABEL_ENCODER_PATH
            self._label_encoder = joblib.load(loading_path)
            self._is_loaded = True
            logger.info("Crop recommendation model artifacts loaded successfully.")
        except Exception as exc:
            self._model = None
            self._preprocessor = None
            self._label_encoder = None
            self._load_error = (
                f"Failed to load crop model artifact '{loading_path}': {exc}"
            )
            logger.error(self._load_error, exc_info=True)

    # ── Prediction ───────────────────────────────────────────────
    def predict(self, request: CropRecommendationRequest) -> str:
        """Run inference on the loaded model.

        Builds the raw training-feature DataFrame, applies the saved
        preprocessor, and decodes the predicted crop class.

        Raises RuntimeError if the model is not loaded.
        Raises ValueError if the request lacks required model features.
        """
        if (
            not self._is_loaded
            or self._model is None
            or self._preprocessor is None
            or self._label_encoder is None
        ):
            raise RuntimeError(
                self._load_error
                or "Crop model artifacts are not loaded."
            )

        request_values: dict[str, Any] = {}
        missing_features: list[str] = []
        for feature in FEATURE_COLUMNS:
            request_field = _REQUEST_FIELD_ALIASES.get(feature, feature)
            if not hasattr(request, request_field):
                missing_features.append(feature)
            else:
                request_values[feature] = getattr(request, request_field)

        if missing_features:
            raise ValueError(
                "Crop recommendation request is missing model input features: "
                f"{', '.join(missing_features)}. "
                "Add these required fields to CropRecommendationRequest; "
                "the service does not supply defaults."
            )

        categorical_encoder = self._preprocessor.named_transformers_.get("cat")
        if categorical_encoder is None:
            raise RuntimeError(
                "Crop preprocessor does not expose its fitted categorical encoder."
            )

        category_names = getattr(categorical_encoder, "feature_names_in_", None)
        category_values = getattr(categorical_encoder, "categories_", None)
        if category_names is None or category_values is None:
            raise RuntimeError(
                "Crop preprocessor does not expose its fitted categorical categories."
            )

        categories_by_feature = dict(zip(category_names, category_values))
        for feature in CATEGORICAL_FEATURES:
            categories = categories_by_feature.get(feature)
            if categories is None:
                raise RuntimeError(
                    f"Crop preprocessor has no fitted categories for {feature!r}."
                )

            value = request_values[feature]
            if value in categories:
                continue

            case_matches = [
                str(category)
                for category in categories
                if value.casefold() == str(category).casefold()
            ]
            if len(case_matches) != 1:
                raise ValueError(
                    f"Unsupported {feature} value: {value!r}."
                )
            request_values[feature] = case_matches[0]

        location_pair = (
            request_values["state_names"],
            request_values["district_names"],
        )
        if location_pair not in _load_crop_location_pairs():
            raise ValueError(
                "The selected district does not belong to the selected state "
                "in the crop dataset."
            )

        input_data = pd.DataFrame(
            [[request_values[feature] for feature in FEATURE_COLUMNS]],
            columns=FEATURE_COLUMNS,
        )

        transformed_data = self._preprocessor.transform(input_data)
        prediction = self._model.predict(transformed_data)
        crop_id = int(prediction[0])

        classes = getattr(self._label_encoder, "classes_", None)
        if classes is None or crop_id < 0 or crop_id >= len(classes):
            raise ValueError(f"Invalid predicted crop ID: {crop_id}")

        crop_name = self._label_encoder.inverse_transform([crop_id])[0]
        return str(crop_name)


# ── Module-level singleton ───────────────────────────────────────
crop_service = CropService()
