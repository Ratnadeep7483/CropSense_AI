"""Pydantic response schemas for plant disease classification."""

from pydantic import BaseModel, Field


class DiseasePredictionResponse(BaseModel):
    """Successful response for plant disease image classification."""

    success: bool = True
    predicted_crop: str = Field(..., description="Crop name from the model label")
    predicted_disease: str = Field(..., description="Disease name from the model label")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model confidence from 0 to 1"
    )
