"""Plant Disease Classification API routes."""

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.disease import DiseasePredictionResponse
from app.services.disease_service import DiseaseImageError, disease_service

logger = logging.getLogger(__name__)

_MAX_UPLOAD_BYTES = 10 * 1024 * 1024

router = APIRouter(prefix="/api/disease", tags=["Plant Disease Detection"])


@router.post(
    "/predict",
    response_model=DiseasePredictionResponse,
    responses={
        413: {"description": "Image is too large"},
        422: {"description": "Invalid image"},
        503: {"description": "Model not loaded"},
        500: {"description": "Prediction failed"},
    },
    summary="Classify a plant disease from an image",
)
async def predict_disease(
    image: UploadFile = File(..., description="Plant leaf image"),
) -> DiseasePredictionResponse:
    if not disease_service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Plant disease classification model is not available.",
                "detail": disease_service.load_error,
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
        predicted_crop, predicted_disease, confidence = disease_service.predict(
            image_bytes
        )
        return DiseasePredictionResponse(
            success=True,
            predicted_crop=predicted_crop,
            predicted_disease=predicted_disease,
            confidence=confidence,
        )
    except DiseaseImageError as exc:
        raise HTTPException(
            status_code=422,
            detail={"success": False, "error": str(exc)},
        ) from exc
    except RuntimeError as exc:
        logger.error("Disease prediction runtime error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Plant disease classification model is not available.",
            },
        ) from exc
    except Exception as exc:
        logger.error("Disease prediction failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Disease prediction failed due to an internal error.",
            },
        ) from exc
