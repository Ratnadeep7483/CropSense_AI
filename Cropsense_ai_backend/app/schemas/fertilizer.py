"""
Pydantic schemas for the Fertilizer Recommendation API.
"""

from pydantic import BaseModel, Field


class FertilizerRecommendationRequest(BaseModel):
    """Request body for POST /api/fertilizer/recommend.

    The 10 features expected by the XGBoost fertilizer recommendation model.
    Note: This model uses "moisture" (not "humidity").
    """

    temperature: float = Field(..., description="Temperature in °C")
    moisture: float = Field(
        ..., description="Soil moisture level (NOT humidity)"
    )
    rainfall: float = Field(..., description="Rainfall in mm")
    ph: float = Field(..., description="Soil pH level")
    nitrogen: float = Field(..., description="Nitrogen content (N)")
    phosphorous: float = Field(..., description="Phosphorous content (P)")
    potassium: float = Field(..., description="Potassium content (K)")
    carbon: float = Field(..., description="Soil organic carbon content")
    soil: str = Field(..., description="Soil type (e.g. 'Loamy Soil')")
    crop: str = Field(..., description="Target crop name (e.g. 'Rice')")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "temperature": 30.0,
                    "moisture": 55.0,
                    "rainfall": 120.0,
                    "ph": 6.8,
                    "nitrogen": 50.0,
                    "phosphorous": 40.0,
                    "potassium": 45.0,
                    "carbon": 1.2,
                    "soil": "Loamy Soil",
                    "crop": "Rice",
                }
            ]
        }
    }


class FertilizerRecommendationResponse(BaseModel):
    """Successful response for fertilizer recommendation."""

    success: bool = True
    recommended_fertilizer: str = Field(
        ..., description="The predicted fertilizer name"
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = False
    error: str = Field(..., description="Human-readable error message")
    detail: str | None = Field(
        None, description="Technical detail for debugging"
    )
