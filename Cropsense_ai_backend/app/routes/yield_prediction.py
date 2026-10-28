"""Yield prediction API routes."""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.yield_prediction import (
    YieldHTTPErrorResponse,
    YieldOptionsResponse,
    YieldPredictionRequest,
    YieldPredictionResponse,
)
from app.services.yield_prediction_service import (
    UnsupportedYieldCategoryError,
    yield_prediction_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/yield", tags=["Yield Prediction"])


def _require_model() -> None:
    if not yield_prediction_service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Yield prediction model is not available.",
                "detail": "Model artifacts are unavailable or invalid. Check server logs.",
            },
        )


@router.get(
    "/options",
    response_model=YieldOptionsResponse,
    responses={503: {"model": YieldHTTPErrorResponse}},
    summary="Get saved yield model categories",
)
async def get_yield_options() -> YieldOptionsResponse:
    """Return model categories and training-observed districts by state."""
    _require_model()
    return YieldOptionsResponse(
        features=yield_prediction_service.categories,
        districts_by_state=yield_prediction_service.districts_by_state,
    )


@router.post(
    "/predict",
    response_model=YieldPredictionResponse,
    responses={
        422: {
            "description": "Invalid request or unsupported category/state-district pair.",
            "content": {
                "application/json": {
                    "schema": {
                        "oneOf": [
                            {"$ref": "#/components/schemas/HTTPValidationError"},
                            {"$ref": "#/components/schemas/YieldHTTPErrorResponse"},
                        ]
                    }
                }
            },
        },
        503: {"model": YieldHTTPErrorResponse},
        500: {"model": YieldHTTPErrorResponse},
    },
    summary="Predict yield per area",
    description=(
        "Predicts `yield_per_area` from Crop, State_Name, District_Name, and "
        "Season using the saved LightGBM model and its embedded category schema."
    ),
)
async def predict_yield(
    request: YieldPredictionRequest,
) -> YieldPredictionResponse:
    """Run inference using the exact saved categorical feature schema."""
    _require_model()
    try:
        prediction, canonical_features = yield_prediction_service.predict(
            request.model_dump()
        )
        return YieldPredictionResponse(
            predicted_yield_per_area=prediction,
            features=canonical_features,
        )
    except UnsupportedYieldCategoryError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "success": False,
                "error": "One or more inputs are not supported by the yield model.",
                "detail": str(exc),
            },
        ) from exc
    except RuntimeError as exc:
        logger.error("Yield prediction model is unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Yield prediction model is not available.",
                "detail": "Check server logs for model availability details.",
            },
        ) from exc
    except Exception as exc:
        logger.error("Yield prediction failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Yield prediction failed due to an internal error.",
                "detail": "Check server logs for details.",
            },
        ) from exc
