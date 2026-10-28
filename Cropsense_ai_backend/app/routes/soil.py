"""Soil Classification API routes."""

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.soil import SoilPredictionResponse
from app.services.soil_service import SoilImageError, soil_service

logger = logging.getLogger(__name__)

_MAX_UPLOAD_BYTES = 10 * 1024 * 1024

router = APIRouter(prefix="/api/soil", tags=["Soil Classification"])


@router.post(
    "/predict",
    response_model=SoilPredictionResponse,
    responses={
        413: {"description": "Image is too large"},
        422: {"description": "Invalid image"},
        503: {"description": "Model not loaded"},
        500: {"description": "Prediction failed"},
    },
    summary="Classify soil from an image",
    description=(
        "Upload a JPEG, PNG, or WebP image to receive the predicted soil "
        "class and model confidence."
    ),
)
async def predict_soil(
    image: UploadFile = File(..., description="Soil image file"),
) -> SoilPredictionResponse:
    if not soil_service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Soil classification model is not available.",
                "detail": soil_service.load_error,
            },
        )

    image_bytes = await image.read(_MAX_UPLOAD_BYTES + 1)
    if len(image_bytes) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail={
                "success": False,
                "error": "Image exceeds the 10 MB upload limit.",
            },
        )

    try:
        predicted_class, confidence = soil_service.predict(image_bytes)
        return SoilPredictionResponse(
            success=True,
            predicted_class=predicted_class,
            confidence=confidence,
        )
    except SoilImageError as exc:
        raise HTTPException(
            status_code=422,
            detail={"success": False, "error": str(exc)},
        ) from exc
    except Exception as exc:
        logger.error("Soil prediction failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Soil prediction failed due to an internal error.",
            },
        ) from exc
