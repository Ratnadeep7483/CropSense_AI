"""Pilot endpoints for historical seasonal weather."""

import logging

from fastapi import APIRouter, HTTPException, Query

from app.schemas.weather import HistoricalWeatherResponse
from app.services.historical_weather_service import (
    SEASON_CATEGORIES,
    SeasonName,
    WeatherDataUnavailable,
    WeatherLocationNotFound,
    WeatherLocationUnresolved,
    WeatherProviderError,
    WeatherProviderTimeout,
    historical_weather_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/weather", tags=["Historical Weather Pilot"])


@router.get(
    "/kharif-historical",
    response_model=HistoricalWeatherResponse,
    responses={
        404: {"description": "Location is not in the CSV-derived registry"},
        409: {"description": "Location is registered but unresolved"},
        503: {"description": "No usable historical weather data"},
        502: {"description": "Weather provider or response error"},
        504: {"description": "Weather provider timeout"},
    },
    summary="Get cached historical seasonal weather averages",
    description=(
        "Returns historical ERA5 hourly seasonal averages for a verified "
        "CSV state/district reference point. Kharif uses June–October; other "
        "season windows are explicitly marked proposals. This is not a "
        "forecast and is not used for crop recommendations."
    ),
)
async def get_historical_weather(
    state_names: str = Query(..., min_length=1),
    district_names: str = Query(..., min_length=1),
    season: SeasonName = Query(
        "Kharif",
        description=f"Exact category: {', '.join(SEASON_CATEGORIES)}",
    ),
) -> HistoricalWeatherResponse:
    """Return historical hourly aggregate for a verified location and season."""
    try:
        return await historical_weather_service.get_historical_average(
            state_names, district_names, season
        )
    except WeatherLocationNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WeatherLocationUnresolved as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except WeatherProviderTimeout as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except WeatherProviderError as exc:
        logger.warning("Historical weather provider error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except WeatherDataUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
