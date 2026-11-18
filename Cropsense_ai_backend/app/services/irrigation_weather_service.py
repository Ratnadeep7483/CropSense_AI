import logging
import unicodedata
from datetime import date
from math import isfinite
from typing import Any

import httpx


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY_VARIABLES = (
    "temperature_2m_mean",
    "relative_humidity_2m_mean",
    "precipitation_sum",
    "sunshine_duration",
    "wind_speed_10m_mean",
)

EXPECTED_UNITS = {
    "temperature_2m_mean": "°C",
    "relative_humidity_2m_mean": "%",
    "precipitation_sum": "mm",
    "sunshine_duration": "s",
    "wind_speed_10m_mean": "km/h",
}

logger = logging.getLogger(__name__)


class WeatherApiError(RuntimeError):
    pass


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
GEOCODING_TIMEOUT_SECONDS = 15.0
GEOCODING_REQUEST_ATTEMPTS = 2


def _normalize_location_label(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_diacritics = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return " ".join(without_diacritics.casefold().split())


def geocode_district(state: str, district: str) -> tuple[float, float]:
    params = {
        "name": district,
        "count": 10,
        "language": "en",
        "format": "json",
    }
    for attempt in range(GEOCODING_REQUEST_ATTEMPTS):
        try:
            response = httpx.get(
                GEOCODING_URL,
                params=params,
                timeout=GEOCODING_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            if attempt == GEOCODING_REQUEST_ATTEMPTS - 1:
                logger.warning("District geocoding timed out after retry: %s", exc)
                raise WeatherApiError(
                    "District geocoding request timed out after retry"
                ) from exc
            logger.warning("District geocoding timed out; retrying: %s", exc)
            continue
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status != 429 and not 500 <= status <= 599:
                raise WeatherApiError(
                    f"District geocoding provider returned HTTP {status}"
                ) from exc
            if attempt == GEOCODING_REQUEST_ATTEMPTS - 1:
                logger.warning(
                    "District geocoding provider returned HTTP %d after retry",
                    status,
                )
                raise WeatherApiError(
                    f"District geocoding provider failed after retry (HTTP {status})"
                ) from exc
            logger.warning(
                "District geocoding provider returned HTTP %d; retrying", status
            )
            continue
        except httpx.TransportError as exc:
            if attempt == GEOCODING_REQUEST_ATTEMPTS - 1:
                logger.warning(
                    "District geocoding transport failed after retry: %s", exc
                )
                raise WeatherApiError(
                    "District geocoding provider request failed after retry"
                ) from exc
            logger.warning("District geocoding transport failed; retrying: %s", exc)
            continue
        except httpx.RequestError as exc:
            logger.warning("District geocoding request failed: %s", exc)
            raise WeatherApiError(
                "District geocoding provider request failed"
            ) from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise WeatherApiError(
                "District geocoding provider returned invalid JSON"
            ) from exc
        break

    if not isinstance(payload, dict):
        raise WeatherApiError("District geocoding provider returned invalid data")
    results = payload.get("results")
    if not isinstance(results, list):
        raise WeatherApiError("District geocoding provider returned no matching location")

    normalized_district = _normalize_location_label(district)
    normalized_state = _normalize_location_label(state)
    for result in results:
        if not isinstance(result, dict):
            continue
        admin1 = _normalize_location_label(str(result.get("admin1", "")))
        admin2 = _normalize_location_label(str(result.get("admin2", "")))
        country = str(result.get("country_code", "")).strip().upper()
        if admin2 not in {normalized_district, f"{normalized_district} district"}:
            continue
        if country != "IN":
            continue
        if admin1 != normalized_state:
            continue
        latitude = result.get("latitude")
        longitude = result.get("longitude")
        if (
            isinstance(latitude, (int, float))
            and not isinstance(latitude, bool)
            and isinstance(longitude, (int, float))
            and not isinstance(longitude, bool)
        ):
            latitude = float(latitude)
            longitude = float(longitude)
            if isfinite(latitude) and isfinite(longitude):
                return latitude, longitude

    raise WeatherApiError(
        f"No geocoding result matched district {district} within state {state}"
    )


def get_daily_weather(latitude: float, longitude: float, weather_date: date) -> dict[str, Any]:
    if not isfinite(latitude) or not -90 <= latitude <= 90:
        raise WeatherApiError("latitude must be between -90 and 90")
    if not isfinite(longitude) or not -180 <= longitude <= 180:
        raise WeatherApiError("longitude must be between -180 and 180")

    iso_date = weather_date.isoformat()
    base_url = ARCHIVE_URL if weather_date < date.today() else FORECAST_URL
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": iso_date,
        "end_date": iso_date,
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": "UTC",
    }

    try:
        response = httpx.get(base_url, params=params, timeout=15.0)
        response.raise_for_status()
        payload = response.json()
    except httpx.TimeoutException as exc:
        raise WeatherApiError("Weather provider request timed out") from exc
    except httpx.HTTPStatusError as exc:
        raise WeatherApiError(
            f"Weather provider returned HTTP {exc.response.status_code}"
        ) from exc
    except httpx.RequestError as exc:
        raise WeatherApiError("Weather provider request failed") from exc
    except ValueError as exc:
        raise WeatherApiError("Weather provider returned invalid JSON") from exc

    daily = payload.get("daily")
    units = payload.get("daily_units")
    if not isinstance(daily, dict) or not isinstance(units, dict):
        raise WeatherApiError("Weather provider omitted daily data")

    for variable, expected_unit in EXPECTED_UNITS.items():
        if units.get(variable) != expected_unit:
            raise WeatherApiError(
                f"Unexpected unit for {variable}: expected {expected_unit}"
            )

    mapped_source: dict[str, Any] = {}
    for variable in DAILY_VARIABLES:
        values = daily.get(variable)
        if not isinstance(values, list) or len(values) != 1:
            raise WeatherApiError(f"Weather provider omitted {variable}")
        value = values[0]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise WeatherApiError(f"Weather provider returned no value for {variable}")
        numeric = float(value)
        if not isfinite(numeric):
            raise WeatherApiError(f"Weather provider returned invalid value for {variable}")
        mapped_source[variable] = numeric

    sunshine_seconds = mapped_source["sunshine_duration"]
    return {
        "Temperature_C": mapped_source["temperature_2m_mean"],
        "Humidity": mapped_source["relative_humidity_2m_mean"],
        "Rainfall_mm": mapped_source["precipitation_sum"],
        "Sunlight_Hours": sunshine_seconds / 3600.0,
        "Wind_Speed_kmh": mapped_source["wind_speed_10m_mean"],
        "measurement": {
            "date": iso_date,
            "timezone": "UTC",
            "period": "one calendar day",
            "source": "Open-Meteo",
            "provider": "archive" if weather_date < date.today() else "forecast",
            "source_variables": {
                "Temperature_C": "temperature_2m_mean",
                "Humidity": "relative_humidity_2m_mean",
                "Rainfall_mm": "precipitation_sum",
                "Sunlight_Hours": "sunshine_duration / 3600",
                "Wind_Speed_kmh": "wind_speed_10m_mean",
            },
            "units": {
                "Temperature_C": "°C",
                "Humidity": "%",
                "Rainfall_mm": "mm",
                "Sunlight_Hours": "hours",
                "Wind_Speed_kmh": "km/h",
            },
            "not_mapped": ["Soil_Moisture"],
        },
    }
