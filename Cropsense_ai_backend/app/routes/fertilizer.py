"""
Fertilizer Recommendation API routes.
"""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.fertilizer import (
    ErrorResponse,
    FertilizerRecommendationRequest,
    FertilizerRecommendationResponse,
)
from app.services.fertilizer_service import fertilizer_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fertilizer", tags=["Fertilizer Recommendation"])


@router.post(
    "/recommend",
    response_model=FertilizerRecommendationResponse,
    responses={
        503: {"model": ErrorResponse, "description": "Model not loaded"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Prediction failed"},
    },
    summary="Get fertilizer recommendation",
    description=(
        "Submit soil, environmental, and crop parameters to receive an "
        "AI-powered fertilizer recommendation from the trained XGBoost "
        "model with saved preprocessing."
    ),
)
async def recommend_fertilizer(
    request: FertilizerRecommendationRequest,
) -> FertilizerRecommendationResponse:
    """Predict the best fertilizer given soil, environmental, and crop data."""
    if not fertilizer_service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Fertilizer recommendation model is not available.",
                "detail": fertilizer_service.load_error,
            },
        )

    try:
        predicted_fertilizer = fertilizer_service.predict(request)
        return FertilizerRecommendationResponse(
            success=True,
            recommended_fertilizer=predicted_fertilizer,
        )
    except RuntimeError as exc:
        logger.error("Fertilizer prediction runtime error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Fertilizer recommendation model is not available.",
                "detail": str(exc),
            },
        )
    except Exception as exc:
        logger.error(
            "Fertilizer prediction failed: %s", exc, exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Prediction failed due to an internal error.",
                "detail": str(exc),
            },
        )
