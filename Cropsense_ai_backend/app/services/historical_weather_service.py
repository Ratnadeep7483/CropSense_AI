"""Cached Open-Meteo ERA5 historical weather for CSV season categories."""

import asyncio
import hashlib
import json
import logging
import math
import os
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

import httpx

from app.schemas.weather import (
    HistoricalWeatherResponse,
    SeasonCoverage,
    WeatherVariableCoverage,
)

logger = logging.getLogger(__name__)

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
SOURCE_NAME = "Open-Meteo Historical Weather API"
SOURCE_URL = "https://open-meteo.com/en/docs/historical-weather-api"
MODEL_NAME = "ERA5"
MODEL_PARAM = "era5"
START_YEAR = 2010
END_YEAR = 2019
REQUEST_TIMEOUT_SECONDS = 120.0
GEOCODING_TIMEOUT_SECONDS = 10.0
PROVIDER_REQUEST_ATTEMPTS = 2
PROVIDER_RETRY_BASE_DELAY_SECONDS = 0.5
CACHE_TTL = timedelta(days=30)
GEOCODING_CACHE_TTL = timedelta(days=365)
CACHE_SCHEMA_VERSION = 2
VARIABLES = ("temperature_2m", "relative_humidity_2m")
WEATHER_ONLY_DISTRICT_ADMIN_ALIASES = {
    ("karnataka", "belgaum"): {
        "admin2": "belgaum district",
        "admin3": "belagavi",
    }
}

SeasonName = Literal["Autumn", "Kharif", "Rabi", "Summer", "Whole Year", "Winter"]


class WeatherProviderError(RuntimeError):
    """The upstream provider returned an error or unusable response."""


class WeatherProviderTimeout(WeatherProviderError):
    """The upstream provider did not respond before the request timeout."""


class WeatherDataUnavailable(RuntimeError):
    """Provider data contains no valid values for a requested season."""


class WeatherLocationNotFound(LookupError):
    """The state/district pair is not in the CSV-derived registry."""


class WeatherLocationUnresolved(LookupError):
    """The pair exists in the registry but has no verified coordinates."""


@dataclass(frozen=True)
class SeasonDefinition:
    start_month: int
    end_month: int
    status: str
    note: str


# Non-Kharif windows are explicit pilot proposals, not dataset-derived rules.
# Season years refer to the calendar year containing the start month.
SEASON_DEFINITIONS: dict[str, SeasonDefinition] = {
    "Autumn": SeasonDefinition(
        9, 11, "proposed", "September through November; proposal only."
    ),
    "Kharif": SeasonDefinition(
        6, 10, "user_defined", "June through October as specified for this pilot."
    ),
    "Rabi": SeasonDefinition(
        10, 3, "proposed", "October through March of the following year; proposal only."
    ),
    "Summer": SeasonDefinition(
        3, 6, "proposed", "March through June; proposal only."
    ),
    "Whole Year": SeasonDefinition(
        1, 12, "proposed", "January through December; proposal only."
    ),
    "Winter": SeasonDefinition(
        12, 2, "proposed", "December through February of the following year; proposal only."
    ),
}
SEASON_CATEGORIES: tuple[str, ...] = tuple(SEASON_DEFINITIONS)

REGISTRY_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "weather_location_registry.json"
)
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "weather_cache"


def validate_coordinates(latitude: float, longitude: float) -> None:
    """Reject non-finite or out-of-range geographic coordinates."""
    if (
        isinstance(latitude, bool)
        or isinstance(longitude, bool)
        or not isinstance(latitude, (int, float))
        or not isinstance(longitude, (int, float))
        or not math.isfinite(latitude)
        or not math.isfinite(longitude)
        or not -90 <= latitude <= 90
        or not -180 <= longitude <= 180
    ):
        raise ValueError("Latitude or longitude is outside its valid range.")


def _normalize_location_label(value: str) -> str:
    return " ".join(value.split()).casefold()


def load_location_registry(path: Path = REGISTRY_PATH) -> dict[tuple[str, str], dict[str, Any]]:
    """Load and validate exact state/district records from the generated registry."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Weather location registry cannot be read: {path}") from exc

    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise RuntimeError("Weather location registry has no entries list.")

    registry: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        state = entry.get("state")
        district = entry.get("district")
        if not isinstance(state, str) or not isinstance(district, str):
            raise RuntimeError("Weather location registry has an invalid identity.")
        identity = (state, district)
        if identity in registry:
            raise RuntimeError(f"Duplicate weather registry pair: {identity}")
        status = entry.get("coordinate_status")
        if status == "verified_reference_point":
            validate_coordinates(entry.get("latitude"), entry.get("longitude"))
            for field in (
                "coordinate_source",
                "coordinate_source_url",
                "coordinate_source_record",
                "verification_source_url",
            ):
                if not entry.get(field):
                    raise RuntimeError(
                        f"Verified weather location {identity} is missing {field}."
                    )
        elif status != "unresolved":
            raise RuntimeError(f"Unknown coordinate status for {identity}: {status}")
        registry[identity] = entry
    return registry


def _season_bounds(season: str, season_year: int) -> tuple[datetime, datetime]:
    definition = SEASON_DEFINITIONS[season]
    start = datetime.combine(date(season_year, definition.start_month, 1), time.min)
    end_year = season_year + (definition.end_month < definition.start_month)
    if definition.end_month == 12:
        end = datetime.combine(date(end_year + 1, 1, 1), time.min)
    else:
        end = datetime.combine(date(end_year, definition.end_month + 1, 1), time.min)
    return start, end


def _expected_season_hours(season: str, season_year: int) -> set[datetime]:
    start, stop = _season_bounds(season, season_year)
    expected: set[datetime] = set()
    current = start
    while current < stop:
        expected.add(current)
        current += timedelta(hours=1)
    return expected


def _request_date_range() -> tuple[date, date]:
    first_day = min(
        _season_bounds(season, START_YEAR)[0]
        for season in SEASON_CATEGORIES
    ).date()
    final_boundary = max(
        _season_bounds(season, END_YEAR)[1]
        for season in SEASON_CATEGORIES
    )
    return first_day, (final_boundary - timedelta(days=1)).date()


def _valid_value(value: Any, variable: str) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    if not math.isfinite(result):
        return None
    if variable == "temperature_2m" and not -90 <= result <= 60:
        return None
    if variable == "relative_humidity_2m" and not 0 <= result <= 100:
        return None
    return result


def aggregate_hourly_weather(
    hourly: dict[str, Any],
    season: str,
    start_year: int = START_YEAR,
    end_year: int = END_YEAR,
) -> tuple[dict[str, float], dict[str, WeatherVariableCoverage], list[SeasonCoverage]]:
    """Average valid hourly observations and count absent/invalid timestamps."""
    if season not in SEASON_DEFINITIONS:
        raise ValueError(f"Unsupported season category: {season}")
    if start_year > end_year:
        raise ValueError("start_year must not be after end_year.")

    times = hourly.get("time")
    temperatures = hourly.get("temperature_2m")
    humidities = hourly.get("relative_humidity_2m")
    if not all(isinstance(values, list) for values in (times, temperatures, humidities)):
        raise WeatherProviderError("The provider response omitted hourly arrays.")
    if not (len(times) == len(temperatures) == len(humidities)):
        raise WeatherProviderError("The provider returned misaligned hourly arrays.")

    expected_by_year = {
        year: _expected_season_hours(season, year)
        for year in range(start_year, end_year + 1)
    }
    expected_to_year = {
        timestamp: year
        for year, timestamps in expected_by_year.items()
        for timestamp in timestamps
    }
    valid_values: dict[str, list[float]] = {variable: [] for variable in VARIABLES}
    valid_by_year = {
        year: {variable: 0 for variable in VARIABLES}
        for year in expected_by_year
    }
    seen: set[datetime] = set()

    for index, raw_time in enumerate(times):
        try:
            timestamp = datetime.fromisoformat(raw_time)
        except (TypeError, ValueError) as exc:
            raise WeatherProviderError(
                "The provider returned an invalid timestamp."
            ) from exc
        if timestamp.tzinfo is not None:
            timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)
        year = expected_to_year.get(timestamp)
        if year is None:
            continue
        if timestamp in seen:
            raise WeatherProviderError(
                "The provider returned a duplicate hourly timestamp."
            )
        seen.add(timestamp)
        for variable, raw_values in (
            ("temperature_2m", temperatures),
            ("relative_humidity_2m", humidities),
        ):
            value = _valid_value(raw_values[index], variable)
            if value is not None:
                valid_values[variable].append(value)
                valid_by_year[year][variable] += 1

    if any(not values for values in valid_values.values()):
        raise WeatherDataUnavailable(
            f"The provider returned no valid {season} values for the requested period."
        )

    expected_hours = sum(len(timestamps) for timestamps in expected_by_year.values())
    averages = {
        variable: math.fsum(values) / len(values)
        for variable, values in valid_values.items()
    }
    coverage = {
        variable: WeatherVariableCoverage(
            expected_hours=expected_hours,
            valid_hours=len(values),
            missing_hours=expected_hours - len(values),
            coverage_percent=100 * len(values) / expected_hours,
            incomplete_seasons=sum(
                counts[variable] != len(expected_by_year[year])
                for year, counts in valid_by_year.items()
            ),
        )
        for variable, values in valid_values.items()
    }
    seasonal_coverage = []
    for year, counts in valid_by_year.items():
        expected = len(expected_by_year[year])
        start, end = _season_bounds(season, year)
        seasonal_coverage.append(
            SeasonCoverage(
                year=year,
                start_date=start.date().isoformat(),
                end_date=(end - timedelta(days=1)).date().isoformat(),
                expected_hours=expected,
                temperature_valid_hours=counts["temperature_2m"],
                humidity_valid_hours=counts["relative_humidity_2m"],
                complete=(
                    counts["temperature_2m"] == expected
                    and counts["relative_humidity_2m"] == expected
                ),
            )
        )
    return averages, coverage, seasonal_coverage


def _all_season_windows(hourly: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        season: _aggregate_to_cache(hourly, season)
        for season in SEASON_CATEGORIES
    }


def _aggregate_to_cache(hourly: dict[str, Any], season: str) -> dict[str, Any]:
    try:
        averages, coverage, seasonal_coverage = aggregate_hourly_weather(
            hourly, season
        )
    except WeatherDataUnavailable as exc:
        return {"unavailable": str(exc)}
    return {
        "averages": averages,
        "coverage": {
            variable: coverage_data.model_dump()
            for variable, coverage_data in coverage.items()
        },
        "seasonal_coverage": [
            coverage_data.model_dump() for coverage_data in seasonal_coverage
        ],
    }


class HistoricalWeatherService:
    """Cache full hourly-window aggregates for accepted weather reference points."""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        cache_dir: Path = DEFAULT_CACHE_DIR,
        registry_path: Path = REGISTRY_PATH,
        cache_ttl: timedelta = CACHE_TTL,
    ) -> None:
        self._client = client
        self._cache_dir = cache_dir
        self._cache_ttl = cache_ttl
        self._registry = load_location_registry(registry_path)
        self._cache_lock = asyncio.Lock()

    @staticmethod
    def _geocoding_cache_key(state: str, district: str) -> str:
        key = json.dumps(
            {
                "state": _normalize_location_label(state),
                "district": _normalize_location_label(district),
                "country": "india",
                "schema": 1,
            },
            sort_keys=True,
        )
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _geocoding_cache_path(self, state: str, district: str) -> Path:
        return self._cache_dir / f"geocode-{self._geocoding_cache_key(state, district)}.json"

    def _geocoding_result_matches(
        self, state: str, district: str, result: Any
    ) -> bool:
        if not isinstance(result, dict):
            return False
        try:
            validate_coordinates(result.get("latitude"), result.get("longitude"))
        except ValueError:
            return False
        if not isinstance(result.get("name"), str) or not result["name"].strip():
            return False
        if (
            result.get("country_code") != "IN"
            or _normalize_location_label(str(result.get("country", ""))) != "india"
            or _normalize_location_label(str(result.get("admin1", "")))
            != _normalize_location_label(state)
        ):
            return False

        state_key = _normalize_location_label(state)
        district_key = _normalize_location_label(district)
        district_admin = _normalize_location_label(
            str(result.get("admin2", ""))
        )
        lower_admin = _normalize_location_label(str(result.get("admin3", "")))
        alias = WEATHER_ONLY_DISTRICT_ADMIN_ALIASES.get(
            (state_key, district_key)
        )
        if alias:
            return (
                district_admin == alias["admin2"]
                and lower_admin == alias["admin3"]
            )
        return district_admin in {district_key, f"{district_key} district"}

    def _geocoded_weather_entry(
        self, registry_entry: dict[str, Any], result: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            latitude = result["latitude"]
            longitude = result["longitude"]
            validate_coordinates(latitude, longitude)
            place_name = result["name"]
            if not isinstance(place_name, str) or not place_name.strip():
                raise ValueError("The geocoding result has no place name.")
        except (KeyError, TypeError, ValueError) as exc:
            raise WeatherLocationUnresolved(
                "The geocoding result for this location has invalid coordinates "
                "or no reference place."
            ) from exc

        source_record = {
            key: result.get(key)
            for key in (
                "id",
                "name",
                "feature_code",
                "country",
                "country_code",
                "admin1",
                "admin2",
                "admin3",
            )
        }
        return {
            **registry_entry,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "reference_place": place_name.strip(),
            "coordinate_status": "geocoded_weather_only",
            "coordinate_source": "Open-Meteo Geocoding API",
            "coordinate_source_url": GEOCODING_URL,
            "coordinate_source_record": json.dumps(
                source_record, ensure_ascii=False, sort_keys=True
            ),
            "verification_source_url": GEOCODING_URL,
            "verification_note": (
                "Weather-only geocoder result matched exact country, state, "
                "and district administrative metadata; it is not a reviewed "
                "registry coordinate or district-headquarters reference."
            ),
            "verification_status": "strict_admin_match_weather_only",
        }

    def _read_geocoding_cache(
        self, state: str, district: str
    ) -> dict[str, Any] | None:
        cache_path = self._geocoding_cache_path(state, district)
        if not cache_path.is_file():
            return None
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            fetched_at = datetime.fromisoformat(cached["fetched_at"])
            age = datetime.now(timezone.utc) - fetched_at
            if age < timedelta(0) or age > GEOCODING_CACHE_TTL:
                return None
            if (
                cached.get("schema_version") != 1
                or cached.get("state_key") != _normalize_location_label(state)
                or cached.get("district_key")
                != _normalize_location_label(district)
                or not self._geocoding_result_matches(
                    state, district, cached.get("result")
                )
            ):
                return None
            return cached["result"]
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            logger.warning("Ignoring invalid weather geocoding cache: %s", cache_path)
            return None

    async def _resolve_geocoded_weather_entry(
        self, registry_entry: dict[str, Any]
    ) -> dict[str, Any]:
        state = registry_entry["state"]
        district = registry_entry["district"]
        cache_path = self._geocoding_cache_path(state, district)
        async with self._cache_lock:
            result = self._read_geocoding_cache(state, district)
            if result is None:
                params = {
                    "name": f"{district}, {state}, India",
                    "count": "10",
                    "language": "en",
                    "format": "json",
                }
                try:
                    if self._client is None:
                        async with httpx.AsyncClient(
                            timeout=httpx.Timeout(GEOCODING_TIMEOUT_SECONDS)
                        ) as client:
                            response = await client.get(
                                GEOCODING_URL, params=params
                            )
                    else:
                        response = await self._client.get(
                            GEOCODING_URL,
                            params=params,
                            timeout=GEOCODING_TIMEOUT_SECONDS,
                        )
                    response.raise_for_status()
                    payload = response.json()
                except httpx.TimeoutException as exc:
                    raise WeatherProviderTimeout(
                        "Open-Meteo Geocoding API request timed out."
                    ) from exc
                except httpx.HTTPError as exc:
                    logger.warning("Open-Meteo geocoding request failed: %s", exc)
                    raise WeatherProviderError(
                        "Open-Meteo Geocoding API request failed."
                    ) from exc
                except ValueError as exc:
                    raise WeatherProviderError(
                        "Open-Meteo Geocoding API returned invalid JSON."
                    ) from exc

                if not isinstance(payload, dict) or payload.get("error"):
                    reason = (
                        payload.get("reason", "The provider returned an error.")
                        if isinstance(payload, dict)
                        else "The provider returned an invalid response."
                    )
                    raise WeatherProviderError(
                        f"Open-Meteo Geocoding API error: {reason}"
                    )
                results = payload.get("results", [])
                if not isinstance(results, list):
                    raise WeatherProviderError(
                        "Open-Meteo Geocoding API returned an invalid results list."
                    )
                matches = [
                    candidate
                    for candidate in results
                    if self._geocoding_result_matches(
                        state, district, candidate
                    )
                ]
                if len(matches) != 1:
                    if len(matches) > 1:
                        reason = (
                            "Geocoding returned multiple locations matching the "
                            "requested country, state, and district; weather lookup "
                            "was not attempted."
                        )
                    else:
                        reason = (
                            "Geocoding did not return a location with an exact "
                            "country, state, and district match; weather lookup "
                            "was not attempted."
                        )
                    raise WeatherLocationUnresolved(reason)
                result = matches[0]
                self._write_cache(
                    cache_path,
                    {
                        "schema_version": 1,
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                        "state_key": _normalize_location_label(state),
                        "district_key": _normalize_location_label(district),
                        "result": result,
                    },
                )
            return self._geocoded_weather_entry(registry_entry, result)

    def get_registry_entry(self, state: str, district: str) -> dict[str, Any]:
        entry = self._registry.get((state, district))
        if entry is None:
            raise WeatherLocationNotFound(
                "The exact state/district pair is not in the CSV-derived registry."
            )
        if entry["coordinate_status"] != "verified_reference_point":
            ambiguity = entry.get("ambiguity_note")
            ambiguity_detail = f" {ambiguity}" if ambiguity else ""
            unresolved_reason = entry.get("unresolved_reason")
            reason_detail = (
                f" Registry reason: {unresolved_reason}"
                if unresolved_reason
                else ""
            )
            verification_note = entry.get("verification_note")
            verification_detail = (
                f" {verification_note}" if verification_note else ""
            )
            raise WeatherLocationUnresolved(
                "This CSV state/district pair is registered, but its coordinates "
                "are unresolved and no weather lookup was attempted."
                f"{reason_detail}{verification_detail}{ambiguity_detail}"
            )
        return entry

    async def _get_weather_entry(
        self, state: str, district: str
    ) -> dict[str, Any]:
        entry = self._registry.get((state, district))
        if entry is None:
            raise WeatherLocationNotFound(
                "The exact state/district pair is not in the CSV-derived registry."
            )
        if entry["coordinate_status"] == "verified_reference_point":
            return entry
        return await self._resolve_geocoded_weather_entry(entry)

    def _cache_path(self, entry: dict[str, Any]) -> Path:
        identity = json.dumps(
            {
                "state": entry["state"],
                "district": entry["district"],
                "latitude": entry["latitude"],
                "longitude": entry["longitude"],
                "model": MODEL_PARAM,
                "start_year": START_YEAR,
                "end_year": END_YEAR,
                "schema": CACHE_SCHEMA_VERSION,
            },
            sort_keys=True,
        )
        key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{key}.json"

    def _read_cache(self, cache_path: Path) -> dict[str, Any] | None:
        if not cache_path.is_file():
            return None
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            fetched_at = datetime.fromisoformat(cached["fetched_at"])
            if datetime.now(timezone.utc) - fetched_at > self._cache_ttl:
                return None
            if cached.get("cache_schema_version") != CACHE_SCHEMA_VERSION:
                return None
            return cached
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            logger.warning("Ignoring invalid historical weather cache: %s", cache_path)
            return None

    def _write_cache(self, cache_path: Path, payload: dict[str, Any]) -> None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        handle, temp_path = tempfile.mkstemp(
            prefix=f"{cache_path.stem}-", suffix=".tmp", dir=cache_path.parent
        )
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as cache_file:
                json.dump(payload, cache_file, ensure_ascii=False, separators=(",", ":"))
            os.replace(temp_path, cache_path)
        except Exception:
            try:
                os.unlink(temp_path)
            except OSError:
                logger.exception("Failed to clean temporary weather cache file.")
            raise

    async def _get_provider_response(
        self, params: dict[str, str]
    ) -> dict[str, Any]:
        async def request_with_retries(
            client: httpx.AsyncClient,
        ) -> dict[str, Any]:
            for attempt in range(PROVIDER_REQUEST_ATTEMPTS):
                try:
                    response = await client.get(ARCHIVE_URL, params=params)
                    response.raise_for_status()
                except httpx.TimeoutException as exc:
                    if attempt == PROVIDER_REQUEST_ATTEMPTS - 1:
                        raise WeatherProviderTimeout(
                            "Open-Meteo Historical Weather API request timed out "
                            "after retries."
                        ) from exc
                    logger.warning(
                        "Open-Meteo historical weather request timed out; retry %d/%d",
                        attempt + 1,
                        PROVIDER_REQUEST_ATTEMPTS - 1,
                    )
                except httpx.HTTPStatusError as exc:
                    status = exc.response.status_code
                    if status != 429 and not 500 <= status <= 599:
                        raise WeatherProviderError(
                            f"Open-Meteo Historical Weather API returned HTTP {status}."
                        ) from exc
                    if attempt == PROVIDER_REQUEST_ATTEMPTS - 1:
                        raise WeatherProviderError(
                            "Open-Meteo Historical Weather API request failed after "
                            f"retries (HTTP {status})."
                        ) from exc
                    logger.warning(
                        "Open-Meteo historical weather API returned HTTP %d; retry %d/%d",
                        status,
                        attempt + 1,
                        PROVIDER_REQUEST_ATTEMPTS - 1,
                    )
                except httpx.TransportError as exc:
                    if attempt == PROVIDER_REQUEST_ATTEMPTS - 1:
                        logger.warning(
                            "Open-Meteo historical weather request failed after retries: %s",
                            exc,
                        )
                        raise WeatherProviderError(
                            "Open-Meteo Historical Weather API request failed "
                            "after retries."
                        ) from exc
                    logger.warning(
                        "Open-Meteo historical weather transport failed; retry %d/%d: %s",
                        attempt + 1,
                        PROVIDER_REQUEST_ATTEMPTS - 1,
                        exc,
                    )
                else:
                    try:
                        payload = response.json()
                    except ValueError as exc:
                        raise WeatherProviderError(
                            "Open-Meteo returned invalid JSON."
                        ) from exc

                    if not isinstance(payload, dict) or payload.get("error"):
                        message = (
                            payload.get("reason", "The provider returned an error.")
                            if isinstance(payload, dict)
                            else "The provider returned an invalid response."
                        )
                        raise WeatherProviderError(str(message))
                    return payload

                await asyncio.sleep(
                    PROVIDER_RETRY_BASE_DELAY_SECONDS * (2**attempt)
                )

            raise WeatherProviderError(
                "Open-Meteo Historical Weather API request failed after retries."
            )

        if self._client is None:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(REQUEST_TIMEOUT_SECONDS)
            ) as client:
                return await request_with_retries(client)
        return await request_with_retries(self._client)

    async def _fetch_location_catalog(
        self, entry: dict[str, Any]
    ) -> dict[str, Any]:
        request_start, request_end = _request_date_range()
        params = {
            "latitude": str(entry["latitude"]),
            "longitude": str(entry["longitude"]),
            "start_date": request_start.isoformat(),
            "end_date": request_end.isoformat(),
            "hourly": "temperature_2m,relative_humidity_2m",
            "models": MODEL_PARAM,
            "timezone": "UTC",
        }
        payload = await self._get_provider_response(params)
        hourly = payload.get("hourly")
        if not isinstance(hourly, dict):
            raise WeatherProviderError("The provider response omitted hourly data.")
        hourly_units = payload.get("hourly_units")
        if (
            not isinstance(hourly_units, dict)
            or hourly_units.get("temperature_2m") != "°C"
            or hourly_units.get("relative_humidity_2m") != "%"
        ):
            raise WeatherProviderError("The provider returned unexpected weather units.")
        try:
            raw_grid_latitude = payload["latitude"]
            raw_grid_longitude = payload["longitude"]
            validate_coordinates(raw_grid_latitude, raw_grid_longitude)
            grid_latitude = float(raw_grid_latitude)
            grid_longitude = float(raw_grid_longitude)
            grid_elevation = float(payload["elevation"])
            if not math.isfinite(grid_elevation):
                raise ValueError("Provider returned an invalid elevation.")
        except (KeyError, TypeError, ValueError) as exc:
            raise WeatherProviderError(
                "The provider returned invalid location metadata."
            ) from exc

        windows = _all_season_windows(hourly)
        if all("unavailable" in result for result in windows.values()):
            raise WeatherDataUnavailable(
                "The provider returned no valid weather data in any supported season."
            )
        return {
            "cache_schema_version": CACHE_SCHEMA_VERSION,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + self._cache_ttl).isoformat(),
            "source": SOURCE_NAME,
            "source_url": SOURCE_URL,
            "model": MODEL_NAME,
            "units": {"temperature_2m": "°C", "relative_humidity_2m": "%"},
            "location": {
                "state": entry["state"],
                "district": entry["district"],
                "reference_place": entry["reference_place"],
            },
            "coordinates": {
                "requested_latitude": entry["latitude"],
                "requested_longitude": entry["longitude"],
                "provider_grid_latitude": grid_latitude,
                "provider_grid_longitude": grid_longitude,
                "provider_grid_elevation_m": grid_elevation,
                "coordinate_source": entry["coordinate_source"],
                "coordinate_source_url": entry["coordinate_source_url"],
                "coordinate_source_record": entry["coordinate_source_record"],
                "verification_source_url": entry["verification_source_url"],
                "verification_status": entry["coordinate_status"],
                "verification_note": entry["verification_note"],
            },
            "season_windows": windows,
        }

    async def _get_location_catalog(
        self, entry: dict[str, Any], force_refresh: bool = False
    ) -> tuple[dict[str, Any], bool]:
        cache_path = self._cache_path(entry)
        async with self._cache_lock:
            cached = None if force_refresh else self._read_cache(cache_path)
            if cached is not None:
                return cached, True
            catalog = await self._fetch_location_catalog(entry)
            self._write_cache(cache_path, catalog)
            return catalog, False

    async def get_historical_average(
        self,
        state: str,
        district: str,
        season: SeasonName = "Kharif",
        force_refresh: bool = False,
    ) -> HistoricalWeatherResponse:
        if season not in SEASON_DEFINITIONS:
            raise ValueError(f"Unsupported season category: {season}")
        entry = await self._get_weather_entry(state, district)
        catalog, cached = await self._get_location_catalog(entry, force_refresh)
        season_data = catalog["season_windows"].get(season)
        if not season_data or "unavailable" in season_data:
            detail = (
                season_data.get("unavailable")
                if isinstance(season_data, dict)
                else None
            )
            raise WeatherDataUnavailable(
                detail or f"No cached weather data is available for {season}."
            )

        definition = SEASON_DEFINITIONS[season]
        overlapping = sorted(
            other
            for other in SEASON_CATEGORIES
            if other != season
            and _seasons_overlap(season, other, START_YEAR, END_YEAR)
        )
        start_date = min(item["start_date"] for item in season_data["seasonal_coverage"])
        end_date = max(item["end_date"] for item in season_data["seasonal_coverage"])
        method = (
            "Arithmetic mean of valid hourly 2 m temperature and 2 m relative "
            f"humidity values in the proposed/defined {season} month window "
            f"({definition.start_month:02d}–{definition.end_month:02d}) for "
            f"season-start years {START_YEAR}–{END_YEAR}, UTC. Missing or "
            "invalid hours are excluded from the mean and counted against all "
            "expected hourly timestamps."
        )
        return HistoricalWeatherResponse(
            label="Historical seasonal average — not a forecast",
            season=season,
            season_definition={
                "start_month": definition.start_month,
                "end_month": definition.end_month,
                "status": definition.status,
                "note": definition.note,
                "overlaps_with": overlapping,
            },
            location=catalog["location"],
            coordinates=catalog["coordinates"],
            source=catalog["source"],
            source_url=catalog["source_url"],
            model=catalog["model"],
            period={
                "season": season,
                "season_start_years": list(range(START_YEAR, END_YEAR + 1)),
                "start_date": start_date,
                "end_date": end_date,
                "timezone": "UTC",
                "requested_data_start": _request_date_range()[0].isoformat(),
                "requested_data_end": _request_date_range()[1].isoformat(),
            },
            units=catalog["units"],
            aggregation_method=method,
            averages=season_data["averages"],
            coverage=season_data["coverage"],
            seasonal_coverage=season_data["seasonal_coverage"],
            cache={
                "hit": cached,
                "fetched_at": catalog["fetched_at"],
                "expires_at": catalog["expires_at"],
                "ttl_days": self._cache_ttl.days,
            },
        )

    async def get_kharif_average(
        self, state: str, district: str
    ) -> HistoricalWeatherResponse:
        """Preserve the existing pilot service call."""
        return await self.get_historical_average(state, district, "Kharif")


def _seasons_overlap(
    first: str, second: str, start_year: int, end_year: int
) -> bool:
    def month_interval(season: str, year: int) -> tuple[int, int]:
        definition = SEASON_DEFINITIONS[season]
        start = year * 12 + definition.start_month - 1
        end_year = year + (definition.end_month < definition.start_month)
        end = end_year * 12 + definition.end_month - 1
        return start, end

    for year in range(start_year - 1, end_year + 2):
        first_start, first_end = month_interval(first, year)
        for other_year in (year - 1, year, year + 1):
            second_start, second_end = month_interval(second, other_year)
            if max(first_start, second_start) <= min(first_end, second_end):
                return True
    return False


historical_weather_service = HistoricalWeatherService()
