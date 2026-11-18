from datetime import date as date_type
import math
from typing import Any

from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse

from app.schemas.irrigation import (
    IrrigationPredictionRequest,
    IrrigationPredictionResponse,
    IrrigationWeatherPredictionRequest,
)
from app.services.irrigation_service import (
    CATEGORICAL_VALUES,
    FEATURES,
    irrigation_service,
)
from app.services.irrigation_weather_service import (
    WeatherApiError,
    geocode_district,
    get_daily_weather,
)
from app.services.crop_location_service import crop_location_service


router = APIRouter(prefix="/api/irrigation", tags=["Smart Irrigation"])


def _error(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "error": message},
    )


def _field_error(
    status_code: int,
    message: str,
    field_name: str,
    fields: list[str],
) -> JSONResponse:
    content: dict[str, Any] = {"success": False, "error": message}
    content[field_name] = fields
    return JSONResponse(status_code=status_code, content=content)


def _finite_number(payload: dict, name: str) -> tuple[float | None, JSONResponse | None]:
    if name not in payload:
        return None, _error(400, f"Missing fields: {name}")
    value = payload[name]
    if isinstance(value, bool):
        return None, _error(400, f"{name} must be numeric")
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return None, _error(400, f"{name} must be numeric")
    if not math.isfinite(converted):
        return None, _error(400, f"{name} must be numeric")
    return converted, None


def _validate_direct_payload(payload: Any) -> tuple[dict | None, JSONResponse | None]:
    if not isinstance(payload, dict):
        return None, _error(400, "A JSON request body is required")

    missing = [name for name in FEATURES if name not in payload]
    if missing:
        return None, _field_error(
            400, "Missing fields", "missing_fields", missing
        )

    extra = [name for name in payload if name not in FEATURES]
    if extra:
        return None, _field_error(
            400, "Unexpected fields", "unexpected_fields", extra
        )

    numeric_fields = [
        "Temperature_C",
        "Humidity",
        "Rainfall_mm",
        "Sunlight_Hours",
        "Soil_Moisture",
        "Wind_Speed_kmh",
    ]
    converted = dict(payload)
    for name in numeric_fields:
        value, error = _finite_number(payload, name)
        if error is not None:
            return None, error
        converted[name] = value

    for name, allowed in CATEGORICAL_VALUES.items():
        if payload[name] not in allowed:
            return None, _error(
                400,
                f"{name} must be one of {allowed}",
            )
    try:
        IrrigationPredictionRequest.model_validate(converted)
    except Exception as exc:
        return None, _error(400, str(exc))
    return converted, None


@router.get("/weather")
async def get_irrigation_weather(
    latitude: float = Query(...),
    longitude: float = Query(...),
    date: str | None = Query(default=None),
) -> JSONResponse:
    try:
        weather_date = date_type.today() if date is None else date_type.fromisoformat(date)
    except (TypeError, ValueError):
        return _error(400, "date must use YYYY-MM-DD")
    try:
        weather = get_daily_weather(latitude, longitude, weather_date)
    except WeatherApiError as exc:
        return JSONResponse(status_code=502, content={"success": False, "error": str(exc)})
    return JSONResponse(content={"success": True, "weather": weather})


@router.post("/predict", response_model=IrrigationPredictionResponse)
async def predict(payload: Any = Body(...)) -> JSONResponse:
    converted, error = _validate_direct_payload(payload)
    if error is not None:
        return error
    try:
        prediction, probabilities = irrigation_service.predict(converted)
    except RuntimeError as exc:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": str(exc)},
        )
    return JSONResponse(
        content={
            "success": True,
            "prediction": prediction,
            "probabilities": probabilities,
        }
    )


@router.post("/predict-from-weather", response_model=IrrigationPredictionResponse)
async def predict_from_weather(payload: Any = Body(...)) -> JSONResponse:
    if not isinstance(payload, dict):
        return _error(400, "A JSON request body is required")

    required = [
        "state",
        "district",
        "Soil_Moisture",
        "Soil_Type",
        "Crop_Type",
        "Crop_Growth_Stage",
        "Season",
        "Mulching_Used",
    ]
    missing = [name for name in required if name not in payload]
    if missing:
        return _field_error(400, "Missing fields", "missing_fields", missing)

    extra = [name for name in payload if name not in set(required)]
    if extra:
        return _field_error(400, "Unexpected fields", "unexpected_fields", extra)

    soil_moisture, moisture_error = _finite_number(payload, "Soil_Moisture")
    if moisture_error is not None:
        return moisture_error

    state = str(payload["state"]).strip()
    district = str(payload["district"]).strip()
    try:
        _, districts, _ = crop_location_service.get_options(state)
        if district not in districts:
            return _error(
                400,
                f"District {district} does not match state {state}",
            )
    except Exception as exc:
        return _error(503, f"State-district location data is unavailable: {exc}")

    for name, allowed in CATEGORICAL_VALUES.items():
        if name in payload and payload[name] not in allowed:
            return _error(400, f"{name} must be one of {allowed}")

    try:
        IrrigationWeatherPredictionRequest.model_validate(
            {
                "state": state,
                "district": district,
                "Soil_Moisture": soil_moisture,
                "Soil_Type": payload["Soil_Type"],
                "Crop_Type": payload["Crop_Type"],
                "Crop_Growth_Stage": payload["Crop_Growth_Stage"],
                "Season": payload["Season"],
                "Mulching_Used": payload["Mulching_Used"],
            }
        )
    except Exception as exc:
        return _error(400, str(exc))

    try:
        latitude, longitude = geocode_district(state, district)
        weather_date = date_type.today()
        weather = get_daily_weather(latitude, longitude, weather_date)
    except WeatherApiError as exc:
        return JSONResponse(status_code=502, content={"success": False, "error": str(exc)})

    model_payload = {
        "Temperature_C": weather["Temperature_C"],
        "Humidity": weather["Humidity"],
        "Rainfall_mm": weather["Rainfall_mm"],
        "Sunlight_Hours": weather["Sunlight_Hours"],
        "Soil_Type": payload["Soil_Type"],
        "Crop_Type": payload["Crop_Type"],
        "Crop_Growth_Stage": payload["Crop_Growth_Stage"],
        "Season": payload["Season"],
        "Soil_Moisture": soil_moisture,
        "Wind_Speed_kmh": weather["Wind_Speed_kmh"],
        "Mulching_Used": payload["Mulching_Used"],
    }
    try:
        prediction, probabilities = irrigation_service.predict(model_payload)
    except RuntimeError as exc:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": str(exc)},
        )
    return JSONResponse(
        content={
            "success": True,
            "prediction": prediction,
            "probabilities": probabilities,
            "weather": weather,
        }
    )
