"""
Crop Recommendation API routes.
"""

import logging
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.schemas.crop import (
    CropLocationOptionsResponse,
    CropModelInputFeatures,
    CropRecommendationRequest,
    CropRecommendationResponse,
    ErrorResponse,
    HistoricalAreaResponse,
    HistoricalCropRecordRecommendationResponse,
    HistoricalCropRecordRequest,
    HistoricalFeatureLookupRequest,
    HistoricalFeatureLookupResponse,
    HistoricalCropCandidateStatus,
    HistoricalCropWorkflowRequest,
    HistoricalCropWorkflowResponse,
    NPKLookupRequest,
    NPKLookupResponse,
    RainfallLookupRequest,
    RainfallLookupResponse,
)
from app.services.crop_service import crop_service
from app.services.crop_location_service import (
    CropLocationDatasetError,
    HistoricalCropFeaturesUnavailable,
    HistoricalCropRecordAmbiguous,
    HistoricalCropRecordNotFound,
    crop_location_service,
)
from app.services.candidate_wise_crop_experiment import (
    candidate_wise_crop_experiment,
)
from app.services.historical_feature_lookup_service import (
    HistoricalFeatureDatasetError,
    historical_feature_lookup_service,
)
from app.services.npk_lookup_service import (
    NPKDatasetError,
    NPKRecordNotFound,
    NPKYearLookupResult,
    npk_lookup_service,
)
from app.services.rainfall_lookup_service import (
    RAINFALL_DESCRIPTION,
    RainfallDatasetError,
    RainfallRecordNotFound,
    rainfall_lookup_service,
)

logger = logging.getLogger(__name__)
ACRES_TO_HECTARES = 0.40468564224

router = APIRouter(prefix="/api/crop", tags=["Crop Recommendation"])


@router.get(
    "/location-options",
    response_model=CropLocationOptionsResponse,
    responses={
        503: {
            "model": ErrorResponse,
            "description": "Crop location dataset unavailable",
        },
    },
    summary="Get dataset-backed crop location options",
)
async def get_crop_location_options(
    state_names: str | None = Query(default=None, min_length=1),
    district_names: str | None = Query(default=None, min_length=1),
) -> CropLocationOptionsResponse:
    """Return only states, districts, and seasons present in the crop dataset."""
    try:
        states, districts, seasons = crop_location_service.get_options(
            state_names,
            district_names,
        )
        return CropLocationOptionsResponse(
            states=states,
            districts=districts,
            seasons=seasons,
        )
    except CropLocationDatasetError as exc:
        logger.error("Crop location options are unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Crop location options are unavailable.",
                "detail": str(exc),
            },
        ) from exc


@router.get(
    "/historical-area",
    response_model=HistoricalAreaResponse,
    responses={
        503: {
            "model": ErrorResponse,
            "description": "Historical crop area dataset unavailable",
        },
    },
    summary="Get district historical cultivated area",
    description=(
        "Returns exact dataset crop/year/soil rows, including area and the "
        "matching NPK and climate feature values. When season_names is supplied, "
        "only records for that season are returned. Area is reported in hectares."
    ),
)
async def get_historical_crop_area(
    state_names: str = Query(..., min_length=1),
    district_names: str = Query(..., min_length=1),
    season_names: str | None = Query(default=None, min_length=1),
) -> HistoricalAreaResponse:
    """Return exact district and, when supplied, season-matched dataset rows."""
    try:
        records = crop_location_service.get_historical_area(
            state_names,
            district_names,
            season_names,
        )
        return HistoricalAreaResponse(
            state_names=state_names,
            district_names=district_names,
            records=records,
        )
    except CropLocationDatasetError as exc:
        logger.error("Historical crop area is unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Historical crop area is unavailable.",
                "detail": str(exc),
            },
        ) from exc


@router.post(
    "/recommend-from-record",
    response_model=HistoricalCropRecordRecommendationResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Dataset row not found"},
        409: {"model": ErrorResponse, "description": "Dataset row is ambiguous"},
        422: {"model": ErrorResponse, "description": "Required dataset features missing"},
        503: {"model": ErrorResponse, "description": "Model or dataset unavailable"},
    },
    summary="Predict from an exact historical training-data row",
    description=(
        "Resolves the selected state/district/season/crop/year/soil key against "
        "the training CSV and supplies that row's exact 12 model features. No "
        "external weather, geocoding, fallback values, or candidate-wise score "
        "ranking is used. The returned class is an unvalidated model output, "
        "not an agronomic recommendation."
    ),
)
async def recommend_crop_from_dataset_record(
    request: HistoricalCropRecordRequest,
) -> HistoricalCropRecordRecommendationResponse:
    """Assemble all model features from one exact dataset record, then predict."""
    if not crop_service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Crop recommendation model is not available.",
                "detail": crop_service.load_error,
            },
        )

    try:
        record = crop_location_service.get_model_record(
            request.state_names,
            request.district_names,
            request.season_names,
            request.crop_names,
            request.crop_year,
            request.soil_for_crop,
        )
        if record["npk_source"] is None:
            raise HistoricalCropFeaturesUnavailable(
                {"NPK provenance": "missing or conflicting npk_source values"}
            )
        model_inputs = CropRecommendationRequest.model_validate(
            record["model_inputs"]
        )
        predicted_crop = crop_service.predict(model_inputs)
    except HistoricalCropRecordNotFound as exc:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": str(exc)},
        ) from exc
    except HistoricalCropRecordAmbiguous as exc:
        raise HTTPException(
            status_code=409,
            detail={"success": False, "error": str(exc)},
        ) from exc
    except HistoricalCropFeaturesUnavailable as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "success": False,
                "error": str(exc),
                "unavailable_features": exc.feature_issues,
            },
        ) from exc
    except CropLocationDatasetError as exc:
        logger.error("Crop feature dataset is unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Crop feature dataset is unavailable.",
                "detail": str(exc),
            },
        ) from exc
    except RuntimeError as exc:
        logger.error("Crop prediction runtime error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Crop recommendation model is not available.",
                "detail": str(exc),
            },
        ) from exc
    except ValueError as exc:
        logger.warning("Crop prediction validation error: %s", exc)
        raise HTTPException(
            status_code=422,
            detail={"success": False, "error": str(exc)},
        ) from exc
    except Exception as exc:
        logger.error("Crop prediction failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Prediction failed due to an internal error.",
                "detail": str(exc),
            },
        ) from exc

    return HistoricalCropRecordRecommendationResponse(
        predicted_crop=predicted_crop,
        reference_crop=record["crop"],
        npk_source=record["npk_source"],
        matching_records=record["matching_records"],
        model_inputs=CropModelInputFeatures.model_validate(
            record["model_inputs"]
        ),
    )


@router.post(
    "/historical-features",
    response_model=HistoricalFeatureLookupResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Invalid lookup key"},
        503: {
            "model": ErrorResponse,
            "description": "Historical feature dataset unavailable",
        },
    },
    summary="Look up prior-year crop features",
    description=(
        "Looks up candidate-specific area and NPK records strictly before "
        "target_year. Area is the raw historical crop/location/season value "
        "and is returned only when unambiguous; it is not validated as "
        "farmer-available land. NPK values are withheld because npk_source "
        "provenance is not documented; the source label and missing-data "
        "status are returned. This endpoint does not invoke model inference."
    ),
)
async def lookup_historical_features(
    request: HistoricalFeatureLookupRequest,
) -> HistoricalFeatureLookupResponse:
    """Return historical feature references without invoking crop inference."""
    try:
        result = historical_feature_lookup_service.lookup(
            request.state_names,
            request.district_names,
            request.season_names,
            request.soil_for_crop,
            request.crop_names,
            request.target_year,
        )
        return HistoricalFeatureLookupResponse(
            state_names=request.state_names,
            district_names=request.district_names,
            season_names=request.season_names,
            soil_for_crop=request.soil_for_crop,
            crop_names=request.crop_names,
            target_year=request.target_year,
            **result.__dict__,
        )
    except HistoricalFeatureDatasetError as exc:
        logger.error("Historical feature lookup is unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Historical feature lookup is unavailable.",
                "detail": str(exc),
            },
        ) from exc


@router.post(
    "/recommend-historical",
    response_model=HistoricalCropWorkflowResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Invalid crop context"},
        503: {"model": ErrorResponse, "description": "Model or dataset unavailable"},
    },
    summary="Assemble historical crop recommendation inputs",
    description=(
        "Runs an experimental candidate-wise coverage diagnostic using the "
        "fitted crop labels, prior-year crop area, and the existing year-specific "
        "NPK lookup. This broad location/season request has no exact crop/year "
        "key, so weather inputs are unavailable and no Weather API or geocoder "
        "is called. Candidate-wise scores are not recommendations; use "
        "/recommend-from-record to assemble a selected dataset row."
    ),
)
async def recommend_crop_from_historical_features(
    request: HistoricalCropWorkflowRequest,
) -> HistoricalCropWorkflowResponse:
    """Report candidate feature availability without returning an unsafe crop."""
    if not crop_service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Crop recommendation model is not available.",
                "detail": crop_service.load_error,
            },
        )

    target_year = date.today().year
    temperature = None
    humidity = None
    weather_status = "unavailable_exact_record_required"
    weather_error = (
        "Temperature and humidity require the exact selected crop/year/soil "
        "training row; this diagnostic request does not identify one."
    )
    rainfall_mm = None
    rainfall_status = "unavailable"
    rainfall_error = None
    rainfall_matched_year_count = None
    rainfall_observed_year_start = None
    rainfall_observed_year_end = None

    try:
        context = candidate_wise_crop_experiment.validate_context(
            state=request.state_names,
            district=request.district_names,
            season=request.season_names,
            soil=request.soil_for_crop,
        )
        try:
            rainfall = rainfall_lookup_service.lookup_before_year(
                context["state_names"],
                context["district_names"],
                context["season_names"],
                target_year,
            )
            rainfall_mm = rainfall.rainfall_mm
            rainfall_status = "available_unverified"
            rainfall_matched_year_count = rainfall.matched_year_count
            rainfall_observed_year_start = rainfall.observed_year_start
            rainfall_observed_year_end = rainfall.observed_year_end
        except RainfallRecordNotFound as exc:
            rainfall_status = "missing_history"
            rainfall_error = str(exc)
        except RainfallDatasetError as exc:
            rainfall_status = "unavailable"
            rainfall_error = str(exc)

        result = candidate_wise_crop_experiment.run_with_existing_npk_lookup(
            state=context["state_names"],
            district=context["district_names"],
            season=context["season_names"],
            soil=context["soil_for_crop"],
            target_year=target_year,
            temperature=temperature,
            humidity=humidity,
            rainfall_mm=rainfall_mm,
        )
    except ValueError as exc:
        logger.warning("Historical crop workflow validation error: %s", exc)
        raise HTTPException(
            status_code=422,
            detail={"success": False, "error": str(exc)},
        ) from exc
    except RuntimeError as exc:
        logger.error("Historical crop workflow is unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Historical crop workflow is unavailable.",
                "detail": str(exc),
            },
        ) from exc

    logger.info(
        "Historical crop lookup context=%s/%s/%s target_year=%s "
        "area_available=%s missing_history=%s ambiguous_area=%s scored=%s/%s",
        context["state_names"],
        context["district_names"],
        context["season_names"],
        result.target_year,
        result.area_available,
        result.missing_history,
        result.ambiguous_area,
        result.scored_candidates,
        result.total_candidates,
    )

    actions: list[str] = []
    if result.missing_history or result.ambiguous_area:
        actions.append(
            "Use a location/season with unambiguous pre-target-year area history "
            "for every candidate, or provide an approved historical source."
        )
    if result.npk_unavailable_or_unverified:
        actions.append(
            "The year-specific NPK lookup is unavailable for some candidate "
            "area years; no NPK values were substituted."
        )
    if result.shared_features_unverified:
        actions.append(
            "Validate that temperature, humidity, and rainfall lookup values "
            "are compatible with the model's training features."
        )
    if weather_status != "available_unverified":
        actions.append(
            "Historical temperature/humidity are unavailable without an exact "
            "crop/year/soil training-row selection; no external weather data is used."
        )
    if rainfall_status == "missing_history":
        actions.append(
            "No rainfall history exists before the target year for this "
            "location and season."
        )
    elif rainfall_status != "available_unverified":
        actions.append(
            "Historical rainfall could not be retrieved; restore the dataset "
            "lookup or select a location/season with prior records."
        )
    if result.validation_failures:
        actions.append(
            "Provide complete model-compatible temperature, humidity, and "
            "rainfall values and resolve any fitted-category validation errors."
        )
    if result.scored_candidates:
        actions.append(
            "Scores are experimental outputs only. Validate candidate-wise "
            "score comparability and ranking on held-out data before using "
            "them to recommend a crop."
        )
    if not actions:
        actions.append(
            "Validate all candidate features and candidate-wise ranking on "
            "held-out data before enabling crop recommendations."
        )

    scoring_blockers: list[str] = []
    if result.missing_history:
        scoring_blockers.append(
            f"Historical crop-specific area is missing for "
            f"{result.missing_history} candidates."
        )
    if result.ambiguous_area:
        scoring_blockers.append(
            f"Historical area is ambiguous for {result.ambiguous_area} candidates."
        )
    if result.npk_unavailable_or_unverified:
        scoring_blockers.append(
            f"Year-matched N, P, and K are unavailable for "
            f"{result.npk_unavailable_or_unverified} candidates."
        )
    if temperature is None or humidity is None:
        scoring_blockers.append(
            "Historical temperature and humidity are required but unavailable."
        )
    if rainfall_mm is None:
        scoring_blockers.append(
            "Pre-target-year historical seasonal rainfall is required but unavailable."
        )
    if result.validation_failures:
        scoring_blockers.append(
            f"Complete model-input validation failed for "
            f"{result.validation_failures} candidates."
        )

    recommendation_blockers = [
        "Candidate-wise score comparability and ranking have not been validated; "
        "experimental scores are not recommendations."
    ]
    if result.shared_features_unverified:
        recommendation_blockers.append(
            "Temperature, humidity, and rainfall compatibility with training "
            "feature semantics remains unverified."
        )
    if result.missing_history or result.ambiguous_area:
        recommendation_blockers.append(
            "Historical area coverage is incomplete or ambiguous for some "
            "candidate crops."
        )

    return HistoricalCropWorkflowResponse(
        state_names=context["state_names"],
        district_names=context["district_names"],
        season_names=context["season_names"],
        target_year=result.target_year,
        farmer_available_area_acres=request.farmer_available_area_acres,
        farmer_available_area_hectares=(
            request.farmer_available_area_acres * ACRES_TO_HECTARES
            if request.farmer_available_area_acres is not None
            else None
        ),
        temperature=temperature,
        humidity=humidity,
        weather_status=weather_status,
        weather_error=weather_error,
        rainfall_mm=rainfall_mm,
        rainfall_status=rainfall_status,
        rainfall_error=rainfall_error,
        rainfall_matched_year_count=rainfall_matched_year_count,
        rainfall_observed_year_start=rainfall_observed_year_start,
        rainfall_observed_year_end=rainfall_observed_year_end,
        total_candidates=result.total_candidates,
        area_available=result.area_available,
        missing_history=result.missing_history,
        ambiguous_area=result.ambiguous_area,
        npk_unavailable_or_unverified=result.npk_unavailable_or_unverified,
        shared_features_unverified=result.shared_features_unverified,
        validation_failures=result.validation_failures,
        scored_candidates=result.scored_candidates,
        ranking_status=result.ranking_status,
        ranking_limitation=result.ranking_limitation,
        scoring_blockers=scoring_blockers,
        recommendation_blockers=recommendation_blockers,
        action_required=" ".join(actions),
        candidates=[
            HistoricalCropCandidateStatus(
                crop=candidate.crop,
                status=candidate.status,
                historical_area=candidate.area,
                area_year=candidate.area_year,
                experimental_score=candidate.score,
                error=candidate.error,
            )
            for candidate in result.candidates
        ],
    )


@router.post(
    "/npk-lookup",
    response_model=NPKLookupResponse,
    response_model_exclude_none=True,
    responses={
        404: {"model": ErrorResponse, "description": "No matching dataset records"},
        422: {"model": ErrorResponse, "description": "Invalid lookup key"},
        503: {"model": ErrorResponse, "description": "NPK dataset unavailable"},
    },
    summary="Look up historical NPK values",
    description=(
        "Without crop_year, returns the legacy mean NPK for the exact state, "
        "district, and season. With crop_year (1997–2015), returns matching "
        "training-data NPK means and ranges, plus temperature, humidity, and "
        "rainfall from that same group. NPK variation is reported explicitly."
    ),
)
async def lookup_historical_npk(
    request: NPKLookupRequest,
) -> NPKLookupResponse:
    """Return dataset feature values without invoking crop-model inference."""
    try:
        result = npk_lookup_service.lookup(
            request.state_names,
            request.district_names,
            request.season_names,
            request.crop_year,
        )
        year_features = (
            {
                "npk_aggregation": result.npk_aggregation,
                "npk_ranges": result.npk_ranges,
                "temperature": result.temperature,
                "humidity": result.humidity,
                "rainfall_mm": result.rainfall_mm,
            }
            if isinstance(result, NPKYearLookupResult)
            else {}
        )
        return NPKLookupResponse(
            success=True,
            state_names=request.state_names,
            district_names=request.district_names,
            season_names=request.season_names,
            crop_year=request.crop_year,
            N=result.N if isinstance(result, NPKYearLookupResult) else result[0],
            P=result.P if isinstance(result, NPKYearLookupResult) else result[1],
            K=result.K if isinstance(result, NPKYearLookupResult) else result[2],
            matched_records=(
                result.matched_records if isinstance(result, NPKYearLookupResult)
                else result[3]
            ),
            **year_features,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"success": False, "error": str(exc)},
        ) from exc
    except NPKRecordNotFound as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": str(exc),
            },
        ) from exc
    except NPKDatasetError as exc:
        logger.error("Historical NPK lookup is unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Historical NPK lookup is unavailable.",
                "detail": str(exc),
            },
        ) from exc


@router.post(
    "/rainfall-lookup",
    response_model=RainfallLookupResponse,
    responses={
        404: {"model": ErrorResponse, "description": "No matching dataset records"},
        422: {"model": ErrorResponse, "description": "Invalid lookup key"},
        503: {"model": ErrorResponse, "description": "Rainfall dataset unavailable"},
    },
    summary="Look up a multi-year rainfall mean",
    description=(
        "Returns the unweighted mean of one validated rainfall value per "
        "observed crop year for an exact state/district/season key. Rainfall "
        "provenance and measurement semantics are unverified."
    ),
)
async def lookup_historical_rainfall(
    request: RainfallLookupRequest,
) -> RainfallLookupResponse:
    """Return exact-key multi-year rainfall statistics without inference."""
    try:
        result = rainfall_lookup_service.lookup(
            request.state_names,
            request.district_names,
            request.season_names,
        )
        return RainfallLookupResponse(
            success=True,
            state_names=request.state_names,
            district_names=request.district_names,
            season_names=request.season_names,
            rainfall_mm=result.rainfall_mm,
            matched_year_count=result.matched_year_count,
            observed_year_start=result.observed_year_start,
            observed_year_end=result.observed_year_end,
            description=RAINFALL_DESCRIPTION,
        )
    except RainfallRecordNotFound as exc:
        raise HTTPException(
            status_code=404,
            detail={"success": False, "error": str(exc)},
        ) from exc
    except RainfallDatasetError as exc:
        logger.error("Historical rainfall lookup is unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Historical rainfall lookup is unavailable.",
                "detail": str(exc),
            },
        ) from exc


@router.post(
    "/recommend",
    response_model=CropRecommendationResponse,
    responses={
        503: {"model": ErrorResponse, "description": "Model not loaded"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Prediction failed"},
    },
    summary="Get crop recommendation",
    description=(
        "Submit state, district, season, soil, nutrient, environmental, "
        "year, and area features to receive an AI-powered crop "
        "recommendation from the trained model."
    ),
)
async def recommend_crop(
    request: CropRecommendationRequest,
) -> CropRecommendationResponse:
    """Pass the complete validated raw feature request to the crop service."""
    if not crop_service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Crop recommendation model is not available.",
                "detail": crop_service.load_error,
            },
        )

    try:
        predicted_crop = crop_service.predict(request)
        return CropRecommendationResponse(
            success=True,
            recommended_crop=predicted_crop,
        )
    except RuntimeError as exc:
        logger.error("Crop prediction runtime error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Crop recommendation model is not available.",
                "detail": str(exc),
            },
        )
    except ValueError as exc:
        logger.warning("Crop prediction validation error: %s", exc)
        raise HTTPException(
            status_code=422,
            detail={
                "success": False,
                "error": str(exc),
                "detail": "Invalid input value for crop recommendation.",
            },
        )
    except Exception as exc:
        logger.error("Crop prediction failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Prediction failed due to an internal error.",
                "detail": str(exc),
            },
        )
