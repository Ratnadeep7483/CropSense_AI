"""Response schemas for historical seasonal weather pilot data."""

from pydantic import BaseModel, Field


class WeatherVariableCoverage(BaseModel):
    """Hourly completeness for one weather variable."""

    expected_hours: int = Field(..., ge=0)
    valid_hours: int = Field(..., ge=0)
    missing_hours: int = Field(..., ge=0)
    coverage_percent: float = Field(..., ge=0, le=100)
    incomplete_seasons: int = Field(..., ge=0)


class SeasonCoverage(BaseModel):
    """Coverage for one season-start year."""

    year: int
    start_date: str
    end_date: str
    expected_hours: int
    temperature_valid_hours: int
    humidity_valid_hours: int
    complete: bool


class HistoricalWeatherResponse(BaseModel):
    """Historical seasonal means with provenance and cache information."""

    success: bool = True
    label: str = "Historical seasonal average — not a forecast"
    season: str
    season_definition: dict[str, object]
    location: dict[str, str]
    coordinates: dict[str, object]
    source: str
    source_url: str
    model: str
    period: dict[str, object]
    units: dict[str, str]
    aggregation_method: str
    averages: dict[str, float]
    coverage: dict[str, WeatherVariableCoverage]
    seasonal_coverage: list[SeasonCoverage]
    cache: dict[str, object]
