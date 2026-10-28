"""Isolated candidate-wise scoring experiment for the existing crop model."""

import logging
import math
from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd

from app.services.crop_service import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    _load_crop_location_pairs,
    crop_service,
)
from app.services.historical_feature_lookup_service import (
    HistoricalFeatureLookupService,
    historical_feature_lookup_service,
)
from app.services.npk_lookup_service import (
    NPKDatasetError,
    NPKRecordNotFound,
    NPKYearLookupResult,
    NPKLookupService,
    npk_lookup_service,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VerifiedNPKFeatures:
    """Candidate-specific NPK inputs with an explicit provenance assertion."""

    N: float
    P: float
    K: float
    crop_year: int
    source: str
    provenance_verified: bool


@dataclass(frozen=True)
class CandidateScore:
    """Per-crop historical coverage, validation result, and optional score."""

    crop: str
    area: float | None
    area_year: int | None
    status: str
    score: float | None = None
    error: str | None = None


@dataclass(frozen=True)
class CandidateWiseExperimentResult:
    """Experiment summary; scores are never treated as a validated ranking."""

    target_year: int
    total_candidates: int
    area_available: int
    missing_history: int
    ambiguous_area: int
    npk_unavailable_or_unverified: int
    shared_features_unverified: int
    validation_failures: int
    scored_candidates: int
    complete_trustworthy_prediction_available: bool
    ranking_status: str
    ranking_limitation: str
    candidates: tuple[CandidateScore, ...]


class CandidateWiseCropExperiment:
    """Score each encoder class using its own latest strictly prior area row.

    This class is deliberately not called by the production crop API. Candidate
    scores are experimental, and score comparability has not been established.
    """

    def __init__(
        self,
        historical_lookup: HistoricalFeatureLookupService = (
            historical_feature_lookup_service
        ),
        model_service: Any = crop_service,
        npk_lookup: NPKLookupService = npk_lookup_service,
    ) -> None:
        self._historical_lookup = historical_lookup
        self._model_service = model_service
        self._npk_lookup = npk_lookup

    def run(
        self,
        *,
        state: str,
        district: str,
        season: str,
        soil: str,
        target_year: int,
        temperature: float | None,
        humidity: float | None,
        rainfall_mm: float | None,
        verified_npk_by_crop: Mapping[str, VerifiedNPKFeatures] | None = None,
        shared_features_verified: bool = False,
        use_existing_npk_lookup: bool = False,
        allow_unverified_sources_for_experiment: bool = False,
    ) -> CandidateWiseExperimentResult:
        """Run candidate coverage and, only with complete inputs, model scoring."""
        label_encoder = getattr(self._model_service, "_label_encoder", None)
        model = getattr(self._model_service, "_model", None)
        preprocessor = getattr(self._model_service, "_preprocessor", None)
        if label_encoder is None:
            raise RuntimeError("The crop label encoder is not loaded.")

        candidates = tuple(str(crop) for crop in label_encoder.classes_)
        output: list[CandidateScore] = []
        area_available = 0
        missing_history = 0
        ambiguous_area = 0
        npk_unavailable = 0
        shared_features_unverified = 0
        validation_failures = 0
        scored_candidates = 0

        shared_values = {
            "state_names": state,
            "district_names": district,
            "season_names": season,
            "soil_for_crop": soil,
            "temperature": temperature,
            "humidity": humidity,
            "rainfall_mm": rainfall_mm,
        }
        shared_missing = [
            name for name, value in shared_values.items()
            if value is None or (isinstance(value, str) and not value.strip())
        ]

        for crop in candidates:
            historical = self._historical_lookup.lookup(
                state,
                district,
                season,
                soil,
                crop,
                target_year,
            )
            if historical.area_status == "not_found":
                missing_history += 1
                output.append(
                    CandidateScore(
                        crop=crop,
                        area=None,
                        area_year=None,
                        status="missing_history",
                        error=historical.area_missing_reason,
                    )
                )
                continue
            if historical.area_status != "available":
                ambiguous_area += 1
                output.append(
                    CandidateScore(
                        crop=crop,
                        area=None,
                        area_year=historical.area_year,
                        status="ambiguous_area",
                        error=historical.area_missing_reason,
                    )
                )
                continue

            area_available += 1
            if not shared_features_verified:
                shared_features_unverified += 1

            npk_features = (
                verified_npk_by_crop.get(crop)
                if verified_npk_by_crop is not None
                else None
            )
            if npk_features is None and use_existing_npk_lookup:
                try:
                    existing_npk = self._npk_lookup.lookup(
                        state,
                        district,
                        season,
                        crop_year=historical.area_year,
                    )
                except (NPKDatasetError, NPKRecordNotFound, ValueError) as exc:
                    npk_error = (
                        "Existing year-specific NPK lookup failed for the "
                        f"candidate's area year {historical.area_year}: {exc}"
                    )
                    npk_unavailable += 1
                    output.append(
                        CandidateScore(
                            crop=crop,
                            area=historical.area,
                            area_year=historical.area_year,
                            status="npk_unavailable",
                            error=npk_error,
                        )
                    )
                    continue
                if not isinstance(existing_npk, NPKYearLookupResult):
                    npk_unavailable += 1
                    output.append(
                        CandidateScore(
                            crop=crop,
                            area=historical.area,
                            area_year=historical.area_year,
                            status="npk_unavailable",
                            error=(
                                "Existing NPK lookup did not return a "
                                "year-specific result."
                            ),
                        )
                    )
                    continue
                npk_features = VerifiedNPKFeatures(
                    N=existing_npk.N,
                    P=existing_npk.P,
                    K=existing_npk.K,
                    crop_year=existing_npk.crop_year,
                    source=(
                        "existing NPK lookup: exact location/season/year "
                        f"arithmetic mean across {existing_npk.matched_records} "
                        "matching dataset records; owner-confirmed source"
                    ),
                    provenance_verified=True,
                )
            npk_error = self._validate_npk(
                npk_features,
                required_year=historical.area_year,
                allow_unverified_source=allow_unverified_sources_for_experiment,
            )
            if npk_error:
                npk_unavailable += 1
                if verified_npk_by_crop is None or crop not in verified_npk_by_crop:
                    npk_error = (
                        "Historical NPK source "
                        f"{historical.npk_source!r} is unavailable for trusted "
                        f"scoring: {historical.npk_missing_reason}"
                        if historical.npk_source
                        else npk_error
                    )
                output.append(
                    CandidateScore(
                        crop=crop,
                        area=historical.area,
                        area_year=historical.area_year,
                        status="npk_unavailable",
                        error=npk_error,
                    )
                )
                continue

            if (
                not shared_features_verified
                and not allow_unverified_sources_for_experiment
            ):
                output.append(
                    CandidateScore(
                        crop=crop,
                        area=historical.area,
                        area_year=historical.area_year,
                        status="shared_features_unverified",
                        error=(
                            "Temperature, humidity, and rainfall sources have "
                            "not been validated as compatible with the training "
                            "features."
                        ),
                    )
                )
                continue

            if shared_missing:
                validation_failures += 1
                output.append(
                    CandidateScore(
                        crop=crop,
                        area=historical.area,
                        area_year=historical.area_year,
                        status="input_validation_failed",
                        error=(
                            "Missing shared model features: "
                            + ", ".join(shared_missing)
                        ),
                    )
                )
                continue

            invalid_shared_numeric = [
                name
                for name in ("temperature", "humidity", "rainfall_mm")
                if not self._is_finite(shared_values[name])
            ]
            if invalid_shared_numeric:
                validation_failures += 1
                output.append(
                    CandidateScore(
                        crop=crop,
                        area=historical.area,
                        area_year=historical.area_year,
                        status="input_validation_failed",
                        error=(
                            "Invalid shared numeric model features: "
                            + ", ".join(invalid_shared_numeric)
                        ),
                    )
                )
                continue

            if model is None or preprocessor is None:
                validation_failures += 1
                output.append(
                    CandidateScore(
                        crop=crop,
                        area=historical.area,
                        area_year=historical.area_year,
                        status="model_unavailable",
                        error="The existing crop model or preprocessor is not loaded.",
                    )
                )
                continue

            request_values: dict[str, Any] = {
                **shared_values,
                "N": float(npk_features.N),
                "P": float(npk_features.P),
                "K": float(npk_features.K),
                "crop_year": historical.area_year,
                "area": historical.area,
            }
            try:
                request_values = self._validate_model_inputs(
                    request_values,
                    preprocessor,
                )
                input_data = pd.DataFrame(
                    [[request_values[feature] for feature in FEATURE_COLUMNS]],
                    columns=FEATURE_COLUMNS,
                )
                transformed = preprocessor.transform(input_data)
                probabilities = model.predict_proba(transformed)
                class_id = int(label_encoder.transform([crop])[0])
                model_classes = getattr(model, "classes_", None)
                if model_classes is None:
                    raise ValueError("The model does not expose its fitted classes.")
                class_positions = [
                    index for index, value in enumerate(model_classes)
                    if int(value) == class_id
                ]
                if len(class_positions) != 1:
                    raise ValueError(
                        f"Model output does not contain exactly one class for {crop!r}."
                    )
                score = float(probabilities[0][class_positions[0]])
                if not math.isfinite(score):
                    raise ValueError("The model returned a non-finite candidate score.")
                if score < 0 or score > 1:
                    raise ValueError("The model returned a candidate score outside [0, 1].")
            except (AttributeError, IndexError, TypeError, ValueError) as exc:
                validation_failures += 1
                logger.info(
                    "Candidate-wise model input failed validation for %s: %s",
                    crop,
                    exc,
                )
                output.append(
                    CandidateScore(
                        crop=crop,
                        area=historical.area,
                        area_year=historical.area_year,
                        status="input_validation_failed",
                        error=str(exc),
                    )
                )
                continue

            scored_candidates += 1
            output.append(
                CandidateScore(
                    crop=crop,
                    area=historical.area,
                    area_year=historical.area_year,
                    status=(
                        "scored_experimental"
                        if allow_unverified_sources_for_experiment
                        and not shared_features_verified
                        else "scored"
                    ),
                    score=score,
                    error=(
                        "Experimental score uses climate values whose "
                        "compatibility with the model's training features is "
                        "unverified."
                        if allow_unverified_sources_for_experiment
                        and not shared_features_verified
                        else None
                    ),
                )
            )

        return CandidateWiseExperimentResult(
            target_year=target_year,
            total_candidates=len(candidates),
            area_available=area_available,
            missing_history=missing_history,
            ambiguous_area=ambiguous_area,
            npk_unavailable_or_unverified=npk_unavailable,
            shared_features_unverified=shared_features_unverified,
            validation_failures=validation_failures,
            scored_candidates=scored_candidates,
            complete_trustworthy_prediction_available=False,
            ranking_status="not_validated",
            ranking_limitation=(
                "Candidate rows use different crop-specific historical area/year "
                "values and may use location/season/year-aggregated NPK values. "
                "Climate compatibility with training data has not been "
                "validated. Cross-candidate score comparability and ranking "
                "have not been validated against held-out data."
            ),
            candidates=tuple(output),
        )

    def run_with_existing_npk_lookup(
        self,
        *,
        state: str,
        district: str,
        season: str,
        soil: str,
        target_year: int,
        temperature: float | None,
        humidity: float | None,
        rainfall_mm: float | None,
    ) -> CandidateWiseExperimentResult:
        """Run the isolated experiment with existing NPK lookup values.

        This deliberately accepts unverified NPK/climate sources for an
        experimental model-input check only. It does not enable production
        inference or validate cross-candidate score ranking.
        """
        return self.run(
            state=state,
            district=district,
            season=season,
            soil=soil,
            target_year=target_year,
            temperature=temperature,
            humidity=humidity,
            rainfall_mm=rainfall_mm,
            use_existing_npk_lookup=True,
            allow_unverified_sources_for_experiment=True,
        )

    def validate_context(
        self,
        *,
        state: str,
        district: str,
        season: str,
        soil: str,
    ) -> dict[str, Any]:
        """Apply the fitted categorical and state/district checks to context."""
        preprocessor = getattr(self._model_service, "_preprocessor", None)
        if preprocessor is None:
            raise RuntimeError("The crop preprocessor is not loaded.")
        return self._validate_model_inputs(
            {
                "state_names": state,
                "district_names": district,
                "season_names": season,
                "soil_for_crop": soil,
            },
            preprocessor,
        )

    @staticmethod
    def _validate_npk(
        features: VerifiedNPKFeatures | None,
        required_year: int | None,
        allow_unverified_source: bool = False,
    ) -> str | None:
        if features is None:
            return "No candidate-specific NPK values were supplied."
        if not features.provenance_verified and not allow_unverified_source:
            return (
                f"NPK source {features.source!r} has not been verified; "
                "candidate score withheld."
            )
        if required_year is None or features.crop_year != required_year:
            return (
                "Candidate NPK values do not come from the same historical year "
                "as the selected area record."
            )
        for name, value in (("N", features.N), ("P", features.P), ("K", features.K)):
            try:
                is_finite = math.isfinite(float(value))
            except (TypeError, ValueError):
                is_finite = False
            if not is_finite:
                return f"NPK feature {name} is not finite."
        if not isinstance(features.source, str) or not features.source.strip():
            return "Verified NPK source label must not be blank."
        return None

    @staticmethod
    def _is_finite(value: Any) -> bool:
        try:
            return math.isfinite(float(value))
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _validate_model_inputs(
        values: Mapping[str, Any],
        preprocessor: Any,
    ) -> dict[str, Any]:
        normalized = dict(values)
        categorical_encoder = preprocessor.named_transformers_.get("cat")
        if categorical_encoder is None:
            raise ValueError(
                "Crop preprocessor does not expose its fitted categorical encoder."
            )
        category_names = getattr(categorical_encoder, "feature_names_in_", None)
        category_values = getattr(categorical_encoder, "categories_", None)
        if category_names is None or category_values is None:
            raise ValueError(
                "Crop preprocessor does not expose fitted categorical categories."
            )
        categories_by_feature = dict(zip(category_names, category_values))
        for feature in CATEGORICAL_FEATURES:
            categories = categories_by_feature.get(feature)
            if categories is None:
                raise ValueError(
                    f"Crop preprocessor has no fitted categories for {feature!r}."
                )
            value = normalized[feature]
            if value in categories:
                continue
            case_matches = [
                str(category)
                for category in categories
                if value.casefold() == str(category).casefold()
            ]
            if len(case_matches) != 1:
                raise ValueError(f"Unsupported {feature} value: {value!r}.")
            normalized[feature] = case_matches[0]

        location_pair = (
            normalized["state_names"],
            normalized["district_names"],
        )
        if location_pair not in _load_crop_location_pairs():
            raise ValueError(
                "The selected district does not belong to the selected state "
                "in the crop dataset."
            )
        return normalized


candidate_wise_crop_experiment = CandidateWiseCropExperiment()
