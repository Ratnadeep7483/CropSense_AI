"""
Pydantic schemas for the Crop Recommendation API.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

MAX_FARMER_AVAILABLE_AREA_ACRES = 100_000


class CropRecommendationRequest(BaseModel):
    """Request body for POST /api/crop/recommend.

    The 12 raw features expected by the crop recommendation model.
    """

    state_names: str = Field(..., description="State name")
    district_names: str = Field(..., description="District name")
    season_names: str = Field(..., description="Growing season")
    soil_for_crop: str = Field(..., description="Soil category for the crop")
    N: float = Field(..., description="Nitrogen content (N)")
    P: float = Field(..., description="Phosphorus content (P)")
    K: float = Field(..., description="Potassium content (K)")
    temperature: float = Field(..., description="Temperature in °C")
    humidity: float = Field(..., description="Relative humidity in %")
    rainfall_mm: float = Field(..., description="Rainfall in mm")
    crop_year: int = Field(..., description="Crop year")
    area: float = Field(
        ...,
        description=(
            "Historical crop-specific cultivated area in hectares, matching the "
            "training dataset's model feature. This is not farmer-available land."
        ),
    )

    @property
    def nitrogen(self) -> float:
        """Provide the legacy service lookup for the raw N feature."""
        return self.N

    @property
    def phosphorous(self) -> float:
        """Provide the legacy service lookup for the raw P feature."""
        return self.P

    @property
    def potassium(self) -> float:
        """Provide the legacy service lookup for the raw K feature."""
        return self.K

    @property
    def rainfall(self) -> float:
        """Provide the legacy service lookup for the raw rainfall feature."""
        return self.rainfall_mm

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "state_names": "Example State",
                    "district_names": "Example District",
                    "season_names": "Kharif",
                    "soil_for_crop": "Example soil category",
                    "N": 60.0,
                    "P": 70.0,
                    "K": 70.0,
                    "temperature": 25.0,
                    "humidity": 70.0,
                    "rainfall_mm": 100.0,
                    "crop_year": 2024,
                    "area": 1.0,
                }
            ]
        }
    }


class NPKLookupRequest(BaseModel):
    """State/district/season key, optionally restricted to a training year."""

    state_names: str = Field(..., min_length=1, description="Exact dataset state name")
    district_names: str = Field(
        ..., min_length=1, description="Exact dataset district name"
    )
    season_names: str = Field(..., min_length=1, description="Exact dataset season")
    crop_year: int | None = Field(
        None,
        ge=1997,
        le=2015,
        description="Training-data year; supported range is 1997–2015",
    )


class CropLocationOptionsResponse(BaseModel):
    """Dataset-derived state, district, and season options."""

    success: bool = True
    states: list[str]
    districts: list[str] = Field(default_factory=list)
    seasons: list[str] = Field(default_factory=list)


class HistoricalAreaRecord(BaseModel):
    """A crop/year/soil dataset row and its exact model-feature values."""

    crop: str
    season: str
    year: int
    soil_for_crop: str | None
    area_hectares: float | None
    status: Literal["available", "ambiguous", "missing"]
    state_names: str
    district_names: str
    N: float | None
    P: float | None
    K: float | None
    temperature: float | None
    humidity: float | None
    rainfall_mm: float | None
    npk_source: str | None
    matching_records: int
    feature_issues: dict[str, str]


class HistoricalAreaResponse(BaseModel):
    """Historical cultivated-area and matching feature rows for a district."""

    success: bool = True
    state_names: str
    district_names: str
    units: Literal["hectares"] = "hectares"
    records: list[HistoricalAreaRecord]


class HistoricalCropRecordRequest(BaseModel):
    """Exact dataset row selected for assembling model inputs."""

    state_names: str = Field(..., min_length=1)
    district_names: str = Field(..., min_length=1)
    season_names: str = Field(..., min_length=1)
    crop_names: str = Field(..., min_length=1)
    crop_year: int = Field(..., ge=1997, le=2015)
    soil_for_crop: str = Field(..., min_length=1)


class CropModelInputFeatures(BaseModel):
    """The exact 12 raw inputs accepted by the saved crop preprocessor."""

    state_names: str
    district_names: str
    season_names: str
    soil_for_crop: str
    N: float
    P: float
    K: float
    temperature: float
    humidity: float
    rainfall_mm: float
    crop_year: int
    area: float


class HistoricalCropRecordRecommendationResponse(BaseModel):
    """Prediction and provenance from one exact historical training row."""

    success: bool = True
    predicted_crop: str
    reference_crop: str
    npk_source: str
    area_unit: Literal["hectares"] = "hectares"
    matching_records: int
    model_inputs: CropModelInputFeatures


class NPKValueRange(BaseModel):
    """Observed minimum and maximum for an NPK feature in a matching group."""

    minimum: float
    maximum: float


class NPKLookupResponse(BaseModel):
    """Dataset-derived NPK values and, for year lookups, related features."""

    success: bool = True
    state_names: str
    district_names: str
    season_names: str
    crop_year: int | None = None
    N: float
    P: float
    K: float
    matched_records: int = Field(..., ge=1)
    npk_aggregation: str | None = None
    npk_ranges: dict[str, NPKValueRange] | None = None
    temperature: float | None = None
    humidity: float | None = None
    rainfall_mm: float | None = None


class HistoricalFeatureLookupRequest(BaseModel):
    """Candidate crop context used for strictly prior-year feature lookups."""

    state_names: str = Field(..., min_length=1)
    district_names: str = Field(..., min_length=1)
    season_names: str = Field(..., min_length=1)
    soil_for_crop: str = Field(..., min_length=1)
    crop_names: str = Field(..., min_length=1)
    target_year: int = Field(..., ge=1, le=9999)

    @field_validator(
        "state_names",
        "district_names",
        "season_names",
        "soil_for_crop",
        "crop_names",
    )
    @classmethod
    def reject_blank_feature_lookup_keys(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Historical feature lookup keys must not be blank.")
        return value


class HistoricalFeatureLookupResponse(BaseModel):
    """Area and NPK lookups with per-feature status and source provenance."""

    success: bool = True
    state_names: str
    district_names: str
    season_names: str
    soil_for_crop: str
    crop_names: str
    target_year: int
    area: float | None = Field(
        None,
        description=(
            "Raw historical area for this crop/location/season record; it is "
            "not validated as farmer-available land and its unit is not "
            "independently documented by the source publisher."
        ),
    )
    area_year: int | None = Field(
        None,
        description="Historical crop year paired with the returned area value.",
    )
    area_status: str
    area_missing_reason: str | None = None
    N: float | None = None
    P: float | None = None
    K: float | None = None
    npk_year: int | None = None
    npk_source: str | None = None
    npk_status: str
    npk_missing_reason: str | None = None


class HistoricalCropWorkflowRequest(BaseModel):
    """Farmer-provided context; model features are assembled internally."""

    state_names: str = Field(..., min_length=1)
    district_names: str = Field(..., min_length=1)
    season_names: Literal[
        "Autumn",
        "Kharif",
        "Rabi",
        "Summer",
        "Whole Year",
        "Winter",
    ]
    soil_for_crop: str = Field(..., min_length=1)
    farmer_available_area_acres: float | None = Field(
        default=None,
        gt=0,
        le=MAX_FARMER_AVAILABLE_AREA_ACRES,
        allow_inf_nan=False,
        description=(
            "Farmer-reported available land in acres. This is returned as "
            "planning information and is not used as the model's historical "
            "crop-specific area feature."
        ),
    )

    @field_validator("state_names", "district_names", "soil_for_crop")
    @classmethod
    def reject_blank_workflow_context(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Crop workflow context values must not be blank.")
        return value

    @field_validator("farmer_available_area_acres", mode="before")
    @classmethod
    def reject_boolean_area(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("Farmer available area must be a numeric acreage.")
        return value


class HistoricalCropCandidateStatus(BaseModel):
    crop: str
    status: str
    historical_area: float | None = Field(
        None,
        description=(
            "Historical crop-specific dataset area, separate from farmer "
            "available land."
        ),
    )
    area_year: int | None = None
    experimental_score: float | None = None
    error: str | None = None


class HistoricalCropWorkflowResponse(BaseModel):
    """Coverage and experimental scores; never a validated prediction."""

    success: bool = True
    recommendation_available: bool = False
    recommended_crop: str | None = None
    state_names: str
    district_names: str
    season_names: str
    target_year: int
    farmer_available_area_acres: float | None = None
    farmer_available_area_hectares: float | None = None
    temperature: float | None = None
    humidity: float | None = None
    weather_status: str
    weather_error: str | None = None
    rainfall_mm: float | None = None
    rainfall_status: str
    rainfall_error: str | None = None
    rainfall_matched_year_count: int | None = None
    rainfall_observed_year_start: int | None = None
    rainfall_observed_year_end: int | None = None
    total_candidates: int
    area_available: int
    missing_history: int
    ambiguous_area: int
    npk_unavailable_or_unverified: int
    shared_features_unverified: int
    validation_failures: int
    scored_candidates: int
    ranking_status: str
    ranking_limitation: str
    scoring_blockers: list[str]
    recommendation_blockers: list[str]
    action_required: str
    candidates: list[HistoricalCropCandidateStatus]


class RainfallLookupRequest(BaseModel):
    """Exact state/district/season key for historical rainfall data."""

    state_names: str = Field(..., min_length=1, description="Exact dataset state name")
    district_names: str = Field(
        ..., min_length=1, description="Exact dataset district name"
    )
    season_names: Literal[
        "Autumn",
        "Kharif",
        "Rabi",
        "Summer",
        "Whole Year",
        "Winter",
    ]

    @field_validator("state_names", "district_names")
    @classmethod
    def reject_blank_lookup_keys(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Lookup keys must not be blank.")
        return value


class RainfallLookupResponse(BaseModel):
    """Dataset-derived multi-year mean; rainfall semantics are unverified."""

    success: bool = True
    state_names: str
    district_names: str
    season_names: str
    rainfall_mm: float
    matched_year_count: int = Field(..., ge=1)
    observed_year_start: int
    observed_year_end: int
    description: str


class CropRecommendationResponse(BaseModel):
    """Successful response for crop recommendation."""

    success: bool = True
    recommended_crop: str = Field(..., description="The predicted crop name")


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = False
    error: str = Field(..., description="Human-readable error message")
    detail: str | None = Field(
        None, description="Technical detail for debugging"
    )
