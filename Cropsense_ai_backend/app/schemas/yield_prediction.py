"""Pydantic schemas for yield prediction."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class YieldPredictionRequest(BaseModel):
    """The four categorical features expected by the saved yield model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    Crop: str = Field(..., min_length=1)
    State_Name: str = Field(..., min_length=1)
    District_Name: str = Field(..., min_length=1)
    Season: str = Field(..., min_length=1)


class YieldPredictionResponse(BaseModel):
    success: bool = True
    predicted_yield_per_area: float
    target: Literal["yield_per_area"] = "yield_per_area"
    features: dict[str, str]


class YieldOptionsResponse(BaseModel):
    success: bool = True
    features: dict[str, list[str]]
    districts_by_state: dict[str, list[str]]


class YieldErrorDetail(BaseModel):
    success: bool = False
    error: str
    detail: str | None = None


class YieldHTTPErrorResponse(BaseModel):
    detail: YieldErrorDetail
