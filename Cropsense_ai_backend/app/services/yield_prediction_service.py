"""Load and run inference with the saved LightGBM yield model."""

import json
import logging
import math
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

logger = logging.getLogger(__name__)

_ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "ml" / "yield"
_MODEL_PATH = _ARTIFACT_DIR / "cropsense_yield_tuned_deployment.joblib"
_METADATA_PATH = _ARTIFACT_DIR / "model_metadata.json"
_LOCATION_DATA_PATH = _ARTIFACT_DIR / "crop_final.csv"

FEATURE_COLUMNS = ["Crop", "State_Name", "District_Name", "Season"]
TARGET_COLUMN = "yield_per_area"


class UnsupportedYieldCategoryError(ValueError):
    """Raised when a request contains a category absent from the saved schema."""


class YieldPredictionService:
    """Holds the saved model and its embedded categorical schema."""

    def __init__(self) -> None:
        self._model: Any | None = None
        self._categories: dict[str, list[str]] = {}
        self._location_pairs: frozenset[tuple[str, str]] = frozenset()
        self._prediction_clip_min: float | None = None
        self._is_loaded = False
        self._load_error: str | None = None

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def load_error(self) -> str | None:
        return self._load_error

    @property
    def categories(self) -> dict[str, list[str]]:
        return {feature: values.copy() for feature, values in self._categories.items()}

    @property
    def districts_by_state(self) -> dict[str, list[str]]:
        """Return training-observed districts in saved category order."""
        return {
            state: [
                district
                for district in self._categories["District_Name"]
                if (state.casefold(), district.casefold()) in self._location_pairs
            ]
            for state in self._categories["State_Name"]
        }

    def load_model(self) -> None:
        """Load and verify the saved artifact without modifying it."""
        self._model = None
        self._categories = {}
        self._location_pairs = frozenset()
        self._prediction_clip_min = None
        self._is_loaded = False
        self._load_error = None

        missing = [
            str(path)
            for path in (_MODEL_PATH, _METADATA_PATH, _LOCATION_DATA_PATH)
            if not path.is_file()
        ]
        if missing:
            self._load_error = "Yield model files not found:\n" + "\n".join(missing)
            logger.warning(self._load_error)
            return

        try:
            with _METADATA_PATH.open(encoding="utf-8") as metadata_file:
                metadata = json.load(metadata_file)
            if metadata.get("features") != FEATURE_COLUMNS:
                raise ValueError("Yield metadata feature order does not match the API.")
            if metadata.get("target") != TARGET_COLUMN:
                raise ValueError("Yield metadata target does not match the API.")

            bundle = joblib.load(_MODEL_PATH)
            if not isinstance(bundle, dict):
                raise ValueError("Yield artifact is not the expected model bundle.")
            if bundle.get("features") != FEATURE_COLUMNS:
                raise ValueError("Yield artifact feature order does not match the API.")
            if bundle.get("target") != TARGET_COLUMN:
                raise ValueError("Yield artifact target does not match the API.")
            if bundle.get("categorical_columns") != FEATURE_COLUMNS:
                raise ValueError("Yield artifact categorical columns are incompatible.")

            categories = bundle.get("category_schema")
            if not isinstance(categories, dict) or list(categories) != FEATURE_COLUMNS:
                raise ValueError("Yield artifact category schema is invalid.")
            normalized_categories: dict[str, list[str]] = {}
            for feature in FEATURE_COLUMNS:
                values = categories[feature]
                if (
                    not isinstance(values, list)
                    or not values
                    or any(not isinstance(value, str) or not value for value in values)
                ):
                    raise ValueError(f"Yield category list is invalid for {feature}.")
                lookup = [value.strip().casefold() for value in values]
                if len(lookup) != len(set(lookup)):
                    raise ValueError(f"Yield categories are ambiguous for {feature}.")
                normalized_categories[feature] = values.copy()

            category_lookup = {
                feature: {
                    value.strip().casefold(): value
                    for value in normalized_categories[feature]
                }
                for feature in ("State_Name", "District_Name")
            }
            locations = pd.read_csv(
                _LOCATION_DATA_PATH,
                usecols=["State_Name", "District_Name"],
                dtype=str,
            )
            if locations.empty or locations.isna().any().any():
                raise ValueError(
                    "Yield location data contains no valid state/district pairs."
                )
            location_pairs: set[tuple[str, str]] = set()
            for state, district in locations.drop_duplicates().itertuples(
                index=False, name=None
            ):
                canonical_state = category_lookup["State_Name"].get(
                    state.strip().casefold()
                )
                canonical_district = category_lookup["District_Name"].get(
                    district.strip().casefold()
                )
                if canonical_state is None or canonical_district is None:
                    raise ValueError(
                        "Yield location data contains labels absent from the saved "
                        "category schema."
                    )
                location_pairs.add(
                    (canonical_state.casefold(), canonical_district.casefold())
                )

            model = bundle.get("model")
            if list(getattr(model, "feature_names_in_", [])) != FEATURE_COLUMNS:
                raise ValueError("Yield model feature order does not match the API.")
            embedded_categories = getattr(
                getattr(model, "booster_", None),
                "pandas_categorical",
                None,
            )
            if embedded_categories != [
                normalized_categories[feature] for feature in FEATURE_COLUMNS
            ]:
                raise ValueError("Yield artifact categories do not match the model.")

            clip_min = bundle.get("prediction_clip_min")
            if not isinstance(clip_min, (int, float)) or not math.isfinite(clip_min):
                raise ValueError("Yield artifact prediction clipping value is invalid.")

            self._model = model
            self._categories = normalized_categories
            self._location_pairs = frozenset(location_pairs)
            self._prediction_clip_min = float(clip_min)
            self._is_loaded = True
            logger.info("Yield prediction model loaded successfully.")
        except Exception as exc:
            self._model = None
            self._categories = {}
            self._location_pairs = frozenset()
            self._prediction_clip_min = None
            self._load_error = f"Failed to load yield model artifact: {exc}"
            logger.error(self._load_error, exc_info=True)

    def predict(self, features: dict[str, str]) -> tuple[float, dict[str, str]]:
        """Predict with canonical saved labels and the original feature order."""
        if (
            not self._is_loaded
            or self._model is None
            or self._prediction_clip_min is None
        ):
            raise RuntimeError(self._load_error or "Yield model is not loaded.")

        canonical_features: dict[str, str] = {}
        for feature in FEATURE_COLUMNS:
            value = features.get(feature)
            if not isinstance(value, str):
                raise UnsupportedYieldCategoryError(
                    f"A valid {feature} category is required."
                )
            lookup = value.strip().casefold()
            canonical = next(
                (
                    category
                    for category in self._categories[feature]
                    if category.strip().casefold() == lookup
                ),
                None,
            )
            if canonical is None:
                raise UnsupportedYieldCategoryError(
                    f"Unsupported {feature} category: {value}."
                )
            canonical_features[feature] = canonical

        location_pair = (
            canonical_features["State_Name"].casefold(),
            canonical_features["District_Name"].casefold(),
        )
        if location_pair not in self._location_pairs:
            raise UnsupportedYieldCategoryError(
                "The selected district is not observed for the selected state."
            )

        frame = pd.DataFrame(
            [[canonical_features[feature] for feature in FEATURE_COLUMNS]],
            columns=FEATURE_COLUMNS,
        )
        for feature in FEATURE_COLUMNS:
            frame[feature] = pd.Categorical(
                frame[feature],
                categories=self._categories[feature],
            )

        prediction = float(self._model.predict(frame)[0])
        if not math.isfinite(prediction):
            raise RuntimeError("Yield model returned a non-finite prediction.")
        return max(prediction, self._prediction_clip_min), canonical_features


yield_prediction_service = YieldPredictionService()
