"""Pydantic schemas for the Soil Classification API."""

from pydantic import BaseModel, Field


class SoilPredictionResponse(BaseModel):
    """Successful response for soil classification."""

    success: bool = True
    predicted_class: str = Field(..., description="Predicted soil class")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Prediction confidence from 0 to 1"
    )
