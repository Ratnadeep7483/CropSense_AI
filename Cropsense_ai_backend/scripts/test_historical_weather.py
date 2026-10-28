#!/usr/bin/env python3
"""Mocked unit and route tests for CSV-wide seasonal weather integration."""

import asyncio
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402
from app.services.historical_weather_service import (  # noqa: E402
    CACHE_TTL,
    REGISTRY_PATH,
    SEASON_CATEGORIES,
    SEASON_DEFINITIONS,
    HistoricalWeatherService,
    WeatherDataUnavailable,
    WeatherLocationNotFound,
    WeatherLocationUnresolved,
    WeatherProviderError,
    WeatherProviderTimeout,
    _expected_season_hours,
    _request_date_range,
    _seasons_overlap,
    aggregate_hourly_weather,
    load_location_registry,
    validate_coordinates,
)


def sample_hourly() -> dict[str, list]:
    return {
        "time": [
            "2010-01-01T00:00",
            "2010-03-01T00:00",
            "2010-06-01T00:00",
            "2010-06-01T01:00",
            "2010-09-01T00:00",
            "2010-10-01T00:00",
            "2010-12-01T00:00",
            "2011-01-01T00:00",
            "2011-02-01T00:00",
            "2011-03-01T00:00",
        ],
        "temperature_2m": [10.0, 12.0, 20.0, None, 22.0, 23.0, 15.0, 14.0, 13.0, 19.0],
        "relative_humidity_2m": [40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 85.0, 80.0, 75.0, 65.0],
    }


def provider_payload() -> dict:
    return {
        "latitude": 18.5,
        "longitude": 73.75,
        "elevation": 561.0,
        "hourly_units": {"temperature_2m": "°C", "relative_humidity_2m": "%"},
        "hourly": sample_hourly(),
    }


def belgaum_geocoding_payload() -> dict:
    return {
        "results": [
            {
                "id": 6301035,
                "name": "Belgaum Airport",
                "latitude": 15.85929,
                "longitude": 74.61829,
                "feature_code": "AIRP",
                "country_code": "IN",
                "country": "India",
                "admin1": "Karnataka",
                "admin2": "Belgaum district",
                "admin3": "Belagavi",
            }
        ]
    }


class SeasonDefinitionTests(unittest.TestCase):
    def test_exact_six_training_categories_are_supported(self) -> None:
        self.assertEqual(
            set(SEASON_CATEGORIES),
            {"Autumn", "Kharif", "Rabi", "Summer", "Whole Year", "Winter"},
        )
        self.assertEqual(SEASON_DEFINITIONS["Kharif"].status, "user_defined")
        for season in set(SEASON_CATEGORIES) - {"Kharif"}:
            self.assertEqual(SEASON_DEFINITIONS[season].status, "proposed")

    def test_season_windows_and_cross_year_boundaries(self) -> None:
        self.assertEqual(len(_expected_season_hours("Kharif", 2010)), 3672)
        self.assertEqual(len(_expected_season_hours("Autumn", 2010)), 2184)
        self.assertEqual(len(_expected_season_hours("Rabi", 2010)), 4368)
        self.assertEqual(len(_expected_season_hours("Summer", 2010)), 2928)
        self.assertEqual(len(_expected_season_hours("Winter", 2010)), 2160)
        self.assertEqual(len(_expected_season_hours("Whole Year", 2012)), 8784)
        rabi = _expected_season_hours("Rabi", 2010)
        self.assertIn(datetime(2011, 3, 31, 23), rabi)
        self.assertNotIn(datetime(2011, 4, 1, 0), rabi)
        self.assertEqual(
            _request_date_range()[0].isoformat(),
            "2010-01-01",
        )
        self.assertEqual(_request_date_range()[1].isoformat(), "2020-03-31")

    def test_overlapping_ranges_are_reported_not_resolved(self) -> None:
        self.assertTrue(_seasons_overlap("Kharif", "Autumn", 2010, 2019))
        self.assertTrue(_seasons_overlap("Kharif", "Rabi", 2010, 2019))
        self.assertTrue(_seasons_overlap("Rabi", "Winter", 2010, 2019))
        self.assertTrue(_seasons_overlap("Whole Year", "Summer", 2010, 2019))
        self.assertFalse(_seasons_overlap("Autumn", "Summer", 2010, 2019))


class RegistryTests(unittest.TestCase):
    def test_registry_covers_all_exact_csv_pairs_and_marks_unresolved(self) -> None:
        registry = load_location_registry()
        self.assertEqual(len(registry), 627)
        csv_locations = pd.read_csv(
            BACKEND_ROOT / "data" / "Copy of crop_recommendation_45_with_year_area.csv",
            usecols=["state_names", "district_names"],
        ).drop_duplicates()
        self.assertEqual(
            set(registry),
            {
                (str(state), str(district))
                for state, district in csv_locations.itertuples(index=False, name=None)
            },
        )
        verified = [
            key for key, row in registry.items()
            if row["coordinate_status"] == "verified_reference_point"
        ]
        unresolved = [
            key for key, row in registry.items()
            if row["coordinate_status"] == "unresolved"
        ]
        self.assertEqual(set(verified), {("Maharashtra", "PUNE"), ("Karnataka", "MYSORE")})
        self.assertEqual(len(unresolved), 625)
        for district in ("BILASPUR", "HAMIRPUR", "PRATAPGARH"):
            matches = [
                row for key, row in registry.items() if key[1] == district
            ]
            self.assertEqual(len(matches), 2)
            self.assertTrue(all(row["district_name_ambiguous_across_states"] for row in matches))

    def test_location_lookup_distinguishes_unknown_and_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            service = HistoricalWeatherService(cache_dir=Path(folder))
            with self.assertRaises(WeatherLocationNotFound):
                service.get_registry_entry("Unknown State", "UNKNOWN")
            with self.assertRaises(WeatherLocationUnresolved) as error:
                service.get_registry_entry("Chhattisgarh", "BILASPUR")
            self.assertIn("multiple states", str(error.exception))
            pune = service.get_registry_entry("Maharashtra", "PUNE")
            self.assertEqual(pune["latitude"], 18.51957)
            mysore = service.get_registry_entry("Karnataka", "MYSORE")
            self.assertEqual(mysore["coordinate_status"], "verified_reference_point")
            self.assertEqual(mysore["latitude"], 12.29791)
            self.assertEqual(mysore["longitude"], 76.63925)
            with self.assertRaises(WeatherLocationNotFound):
                service.get_registry_entry("Karnataka", "Mysuru")
            with self.assertRaises(WeatherLocationNotFound):
                service.get_registry_entry("Maharashtra", "pune")

    def test_pending_karnataka_historical_labels_remain_unresolved(self) -> None:
        pending_labels = (
            "BAGALKOT",
            "BANGALORE RURAL",
            "BELGAUM",
            "BELLARY",
            "BIJAPUR",
            "CHIKBALLAPUR",
            "CHIKMAGALUR",
            "DAKSHIN KANNAD",
            "DAVANGERE",
            "GULBARGA",
            "SHIMOGA",
            "TUMKUR",
            "UTTAR KANNAD",
        )
        with tempfile.TemporaryDirectory() as folder:
            service = HistoricalWeatherService(cache_dir=Path(folder))
            for district in pending_labels:
                with self.subTest(district=district):
                    with self.assertRaises(WeatherLocationUnresolved):
                        service.get_registry_entry("Karnataka", district)

    def test_belgaum_unresolved_diagnostic_explains_missing_reviewed_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            service = HistoricalWeatherService(cache_dir=Path(folder))
            with self.assertRaises(WeatherLocationUnresolved) as error:
                service.get_registry_entry("Karnataka", "BELGAUM")

        self.assertIn("coordinates are unresolved", str(error.exception))
        self.assertIn(
            "No reviewed state-qualified administrative crosswalk and coordinate evidence",
            str(error.exception),
        )

    def test_invalid_coordinate_record_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "registry.json"
            payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            pune = next(
                row for row in payload["entries"]
                if row["state"] == "Maharashtra" and row["district"] == "PUNE"
            )
            pune["longitude"] = 190
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_location_registry(path)
        for latitude, longitude in (
            (90.1, 0),
            (-90.1, 0),
            (0, 180.1),
            (0, -180.1),
            (float("nan"), 0),
        ):
            with self.subTest(latitude=latitude, longitude=longitude):
                with self.assertRaises(ValueError):
                    validate_coordinates(latitude, longitude)


class AggregationTests(unittest.TestCase):
    def test_arithmetic_mean_uses_valid_values_and_reports_coverage(self) -> None:
        averages, coverage, seasons = aggregate_hourly_weather(
            sample_hourly(), "Kharif", start_year=2010, end_year=2010
        )
        self.assertAlmostEqual(averages["temperature_2m"], 65.0 / 3)
        self.assertEqual(averages["relative_humidity_2m"], 75.0)
        self.assertEqual(coverage["temperature_2m"].valid_hours, 3)
        self.assertEqual(coverage["relative_humidity_2m"].valid_hours, 4)
        self.assertEqual(coverage["temperature_2m"].expected_hours, 3672)
        self.assertEqual(coverage["temperature_2m"].missing_hours, 3669)
        self.assertFalse(seasons[0].complete)
        self.assertEqual(seasons[0].start_date, "2010-06-01")
        self.assertEqual(seasons[0].end_date, "2010-10-31")

    def test_missing_nonfinite_and_out_of_range_values_reduce_coverage(self) -> None:
        hourly = {
            "time": [
                "2010-06-01T00:00",
                "2010-06-01T01:00",
                "2010-06-01T02:00",
                "2010-06-01T03:00",
            ],
            "temperature_2m": [18.0, None, float("nan"), 100.0],
            "relative_humidity_2m": [60.0, 101.0, None, 0.0],
        }
        averages, coverage, _ = aggregate_hourly_weather(
            hourly, "Kharif", start_year=2010, end_year=2010
        )
        self.assertEqual(averages["temperature_2m"], 18.0)
        self.assertEqual(averages["relative_humidity_2m"], 30.0)
        self.assertEqual(coverage["temperature_2m"].valid_hours, 1)
        self.assertEqual(coverage["relative_humidity_2m"].valid_hours, 2)

    def test_no_valid_values_are_distinct_from_provider_failure(self) -> None:
        with self.assertRaises(WeatherDataUnavailable):
            aggregate_hourly_weather(
                {
                    "time": ["2010-06-01T00:00"],
                    "temperature_2m": [None],
                    "relative_humidity_2m": [None],
                },
                "Kharif",
                start_year=2010,
                end_year=2010,
            )
        with self.assertRaises(WeatherProviderError):
            aggregate_hourly_weather({"time": [], "temperature_2m": []}, "Kharif")


class ProviderAndCacheTests(unittest.TestCase):
    def test_belgaum_geocoding_uses_exact_admin_match_and_fetches_weather(self) -> None:
        async def exercise() -> None:
            requested_paths: list[str] = []

            async def handler(request: httpx.Request) -> httpx.Response:
                requested_paths.append(request.url.path)
                if request.url.host == "geocoding-api.open-meteo.com":
                    self.assertEqual(
                        request.url.params["name"],
                        "BELGAUM, Karnataka, India",
                    )
                    self.assertEqual(request.url.params["count"], "10")
                    return httpx.Response(200, json=belgaum_geocoding_payload())
                if request.url.host == "archive-api.open-meteo.com":
                    self.assertEqual(request.url.params["latitude"], "15.85929")
                    self.assertEqual(request.url.params["longitude"], "74.61829")
                    return httpx.Response(200, json=provider_payload())
                self.fail(f"Unexpected provider host: {request.url.host}")

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                with tempfile.TemporaryDirectory() as folder:
                    service = HistoricalWeatherService(client, Path(folder))
                    weather = await service.get_historical_average(
                        "Karnataka", "BELGAUM", "Kharif"
                    )

            self.assertEqual(
                requested_paths,
                ["/v1/search", "/v1/archive"],
            )
            self.assertEqual(weather.location["district"], "BELGAUM")
            self.assertEqual(weather.coordinates["requested_latitude"], 15.85929)
            self.assertEqual(weather.coordinates["requested_longitude"], 74.61829)
            self.assertEqual(
                weather.coordinates["verification_status"],
                "geocoded_weather_only",
            )
            self.assertEqual(weather.coordinates["coordinate_source"], "Open-Meteo Geocoding API")
            self.assertEqual(weather.location["reference_place"], "Belgaum Airport")

        asyncio.run(exercise())

    def test_geocoding_rejects_ambiguous_matching_locations(self) -> None:
        async def exercise() -> None:
            async def handler(request: httpx.Request) -> httpx.Response:
                if request.url.host == "geocoding-api.open-meteo.com":
                    payload = belgaum_geocoding_payload()
                    duplicate = dict(payload["results"][0])
                    duplicate["id"] = 123456
                    duplicate["latitude"] = 16.0
                    payload["results"].append(duplicate)
                    return httpx.Response(200, json=payload)
                self.fail("Weather archive must not run for ambiguous geocoding.")

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                with tempfile.TemporaryDirectory() as folder:
                    service = HistoricalWeatherService(client, Path(folder))
                    with self.assertRaisesRegex(
                        WeatherLocationUnresolved, "multiple locations"
                    ):
                        await service.get_historical_average(
                            "Karnataka", "BELGAUM", "Kharif"
                        )

        asyncio.run(exercise())

    def test_geocoding_rejects_wrong_state_country_and_district(self) -> None:
        async def exercise() -> None:
            invalid = belgaum_geocoding_payload()["results"][0]
            invalid["admin1"] = "Maharashtra"

            async def handler(request: httpx.Request) -> httpx.Response:
                if request.url.host == "geocoding-api.open-meteo.com":
                    return httpx.Response(200, json={"results": [invalid]})
                self.fail("Weather archive must not run for a mismatched result.")

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                with tempfile.TemporaryDirectory() as folder:
                    service = HistoricalWeatherService(client, Path(folder))
                    with self.assertRaisesRegex(
                        WeatherLocationUnresolved, "exact country, state, and district"
                    ):
                        await service.get_historical_average(
                            "Karnataka", "BELGAUM", "Kharif"
                        )

        asyncio.run(exercise())

    def test_geocoding_provider_failure_is_explicit(self) -> None:
        async def exercise() -> None:
            async def handler(_: httpx.Request) -> httpx.Response:
                return httpx.Response(503, json={"reason": "unavailable"})

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                with tempfile.TemporaryDirectory() as folder:
                    service = HistoricalWeatherService(client, Path(folder))
                    with self.assertRaisesRegex(
                        WeatherProviderError, "Geocoding API request failed"
                    ):
                        await service.get_historical_average(
                            "Karnataka", "BELGAUM", "Kharif"
                        )

        asyncio.run(exercise())

    def test_geocoding_timeout_is_explicit(self) -> None:
        async def exercise() -> None:
            async def handler(_: httpx.Request) -> httpx.Response:
                raise httpx.ReadTimeout("timed out")

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                with tempfile.TemporaryDirectory() as folder:
                    service = HistoricalWeatherService(client, Path(folder))
                    with self.assertRaisesRegex(
                        WeatherProviderTimeout, "Geocoding API request timed out"
                    ):
                        await service.get_historical_average(
                            "Karnataka", "BELGAUM", "Kharif"
                        )

        asyncio.run(exercise())

    def test_successful_geocoding_resolution_is_persistently_cached(self) -> None:
        async def exercise() -> None:
            geocoding_calls = 0
            archive_calls = 0

            async def handler(request: httpx.Request) -> httpx.Response:
                nonlocal geocoding_calls, archive_calls
                if request.url.host == "geocoding-api.open-meteo.com":
                    geocoding_calls += 1
                    return httpx.Response(200, json=belgaum_geocoding_payload())
                archive_calls += 1
                return httpx.Response(200, json=provider_payload())

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                with tempfile.TemporaryDirectory() as folder:
                    cache_dir = Path(folder)
                    first_service = HistoricalWeatherService(client, cache_dir)
                    await first_service.get_historical_average(
                        "Karnataka", "BELGAUM", "Kharif"
                    )
                    second_service = HistoricalWeatherService(client, cache_dir)
                    await second_service.get_historical_average(
                        "Karnataka", "BELGAUM", "Kharif", force_refresh=True
                    )
                    self.assertEqual(
                        len(list(cache_dir.glob("geocode-*.json"))), 1
                    )

            self.assertEqual(geocoding_calls, 1)
            self.assertEqual(archive_calls, 2)

        asyncio.run(exercise())

    def test_provider_error_and_timeout_are_reported(self) -> None:
        async def exercise() -> None:
            error_calls = 0

            async def error_handler(_: httpx.Request) -> httpx.Response:
                nonlocal error_calls
                error_calls += 1
                return httpx.Response(503, json={"reason": "unavailable"})

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(error_handler)
            ) as client:
                with tempfile.TemporaryDirectory() as folder:
                    service = HistoricalWeatherService(client, Path(folder))
                    with patch(
                        "app.services.historical_weather_service.asyncio.sleep",
                        new_callable=AsyncMock,
                    ):
                        with self.assertRaises(WeatherProviderError):
                            await service.get_historical_average(
                                "Maharashtra", "PUNE", "Kharif"
                            )
            self.assertEqual(error_calls, 2)

            timeout_calls = 0
            async def timeout_handler(_: httpx.Request) -> httpx.Response:
                nonlocal timeout_calls
                timeout_calls += 1
                raise httpx.ReadTimeout("timed out")

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(timeout_handler)
            ) as client:
                with tempfile.TemporaryDirectory() as folder:
                    service = HistoricalWeatherService(client, Path(folder))
                    with patch(
                        "app.services.historical_weather_service.asyncio.sleep",
                        new_callable=AsyncMock,
                    ):
                        with self.assertRaises(WeatherProviderTimeout):
                            await service.get_historical_average(
                                "Maharashtra", "PUNE", "Kharif"
                            )
            self.assertEqual(timeout_calls, 2)

        asyncio.run(exercise())

    def test_provider_retries_transient_failure_then_succeeds(self) -> None:
        async def exercise() -> None:
            calls = 0

            async def handler(_: httpx.Request) -> httpx.Response:
                nonlocal calls
                calls += 1
                if calls == 1:
                    return httpx.Response(503, json={"reason": "temporarily unavailable"})
                return httpx.Response(200, json=provider_payload())

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                with tempfile.TemporaryDirectory() as folder:
                    service = HistoricalWeatherService(client, Path(folder))
                    with patch(
                        "app.services.historical_weather_service.asyncio.sleep",
                        new_callable=AsyncMock,
                    ) as sleep:
                        result = await service.get_historical_average(
                            "Maharashtra", "PUNE", "Kharif"
                        )
                    self.assertEqual(result.source, "Open-Meteo Historical Weather API")
                    sleep.assert_awaited_once_with(0.5)
            self.assertEqual(calls, 2)

        asyncio.run(exercise())

    def test_one_provider_fetch_populates_all_seasons_and_cache(self) -> None:
        async def exercise() -> None:
            calls = 0

            async def handler(request: httpx.Request) -> httpx.Response:
                nonlocal calls
                calls += 1
                self.assertEqual(request.url.host, "archive-api.open-meteo.com")
                self.assertEqual(request.url.path, "/v1/archive")
                self.assertEqual(request.url.params["models"], "era5")
                self.assertEqual(request.url.params["latitude"], "18.51957")
                self.assertEqual(request.url.params["longitude"], "73.85535")
                self.assertEqual(request.url.params["start_date"], "2010-01-01")
                self.assertEqual(request.url.params["end_date"], "2020-03-31")
                self.assertEqual(
                    request.url.params["hourly"],
                    "temperature_2m,relative_humidity_2m",
                )
                self.assertEqual(request.url.params["timezone"], "UTC")
                return httpx.Response(200, json=provider_payload())

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                with tempfile.TemporaryDirectory() as folder:
                    service = HistoricalWeatherService(client, Path(folder))
                    kharif = await service.get_historical_average(
                        "Maharashtra", "PUNE", "Kharif"
                    )
                    autumn = await service.get_historical_average(
                        "Maharashtra", "PUNE", "Autumn"
                    )
                    additional_seasons = [
                        await service.get_historical_average(
                            "Maharashtra", "PUNE", season
                        )
                        for season in ("Rabi", "Summer", "Whole Year", "Winter")
                    ]
                    self.assertFalse(kharif.cache["hit"])
                    self.assertTrue(autumn.cache["hit"])
                    self.assertTrue(all(item.cache["hit"] for item in additional_seasons))
                    self.assertEqual(calls, 1)
                    self.assertEqual(kharif.source, "Open-Meteo Historical Weather API")
                    self.assertEqual(kharif.model, "ERA5")
                    self.assertIn("not a forecast", kharif.label)
                    self.assertEqual(kharif.period["start_date"], "2010-06-01")
                    self.assertEqual(
                        kharif.coordinates["provider_grid_latitude"], 18.5
                    )
                    self.assertEqual(kharif.coverage["temperature_2m"].expected_hours, 36720)
                    self.assertEqual(autumn.season, "Autumn")
                    self.assertEqual(autumn.season_definition["status"], "proposed")
                    self.assertEqual(autumn.cache["ttl_days"], CACHE_TTL.days)
                    self.assertEqual(
                        [item.season for item in additional_seasons],
                        ["Rabi", "Summer", "Whole Year", "Winter"],
                    )

        asyncio.run(exercise())

    def test_force_refresh_fetches_again(self) -> None:
        async def exercise() -> None:
            calls = 0

            async def handler(_: httpx.Request) -> httpx.Response:
                nonlocal calls
                calls += 1
                return httpx.Response(200, json=provider_payload())

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                with tempfile.TemporaryDirectory() as folder:
                    service = HistoricalWeatherService(client, Path(folder))
                    await service.get_historical_average(
                        "Maharashtra", "PUNE", "Kharif"
                    )
                    await service.get_historical_average(
                        "Maharashtra", "PUNE", "Kharif", force_refresh=True
                    )
            self.assertEqual(calls, 2)

        asyncio.run(exercise())

    def test_expired_cache_is_refetched(self) -> None:
        async def exercise() -> None:
            calls = 0

            async def handler(_: httpx.Request) -> httpx.Response:
                nonlocal calls
                calls += 1
                return httpx.Response(200, json=provider_payload())

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                with tempfile.TemporaryDirectory() as folder:
                    service = HistoricalWeatherService(
                        client, Path(folder), cache_ttl=timedelta(0)
                    )
                    first = await service.get_historical_average(
                        "Maharashtra", "PUNE", "Kharif"
                    )
                    second = await service.get_historical_average(
                        "Maharashtra", "PUNE", "Kharif"
                    )
                    self.assertFalse(first.cache["hit"])
                    self.assertFalse(second.cache["hit"])
            self.assertEqual(calls, 2)

        asyncio.run(exercise())

    def test_unmatched_location_never_fetches_historical_weather(self) -> None:
        async def exercise() -> None:
            async def handler(request: httpx.Request) -> httpx.Response:
                if request.url.host == "geocoding-api.open-meteo.com":
                    return httpx.Response(200, json={})
                self.fail("No historical weather request is allowed without a match.")

            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                with tempfile.TemporaryDirectory() as folder:
                    service = HistoricalWeatherService(client, Path(folder))
                    unresolved_locations = [
                        ("Chhattisgarh", "BILASPUR"),
                        ("Karnataka", "BAGALKOT"),
                        ("Karnataka", "BANGALORE RURAL"),
                        ("Karnataka", "BELGAUM"),
                        ("Karnataka", "BELLARY"),
                        ("Karnataka", "BIJAPUR"),
                        ("Karnataka", "CHIKBALLAPUR"),
                        ("Karnataka", "CHIKMAGALUR"),
                        ("Karnataka", "DAKSHIN KANNAD"),
                        ("Karnataka", "DAVANGERE"),
                        ("Karnataka", "GULBARGA"),
                        ("Karnataka", "SHIMOGA"),
                        ("Karnataka", "TUMKUR"),
                        ("Karnataka", "UTTAR KANNAD"),
                    ]
                    for state, district in unresolved_locations:
                        with self.subTest(state=state, district=district):
                            with self.assertRaises(WeatherLocationUnresolved):
                                await service.get_historical_average(
                                    state, district, "Kharif"
                                )

        asyncio.run(exercise())


class RouteTests(unittest.TestCase):
    def test_route_distinguishes_invalid_and_unresolved_locations(self) -> None:
        client = TestClient(app)
        unknown = client.get(
            "/api/weather/kharif-historical",
            params={"state_names": "Unknown", "district_names": "UNKNOWN"},
        )
        unregistered_alias = client.get(
            "/api/weather/kharif-historical",
            params={"state_names": "Karnataka", "district_names": "Mysuru"},
        )
        with patch(
            "app.routes.weather.historical_weather_service.get_historical_average",
            side_effect=[
                WeatherLocationUnresolved(
                    "Geocoding returned multiple locations matching the district."
                ),
                WeatherLocationUnresolved(
                    "Geocoding found no exact district match."
                ),
            ],
        ):
            unresolved = client.get(
                "/api/weather/kharif-historical",
                params={
                    "state_names": "Chhattisgarh",
                    "district_names": "BILASPUR",
                },
            )
            pending_karnataka = client.get(
                "/api/weather/kharif-historical",
                params={
                    "state_names": "Karnataka",
                    "district_names": "BAGALKOT",
                },
            )
        client.close()
        self.assertEqual(unknown.status_code, 404)
        self.assertEqual(unresolved.status_code, 409)
        self.assertIn("multiple locations", unresolved.json()["detail"])
        self.assertEqual(pending_karnataka.status_code, 409)
        self.assertIn("no exact district match", pending_karnataka.json()["detail"])
        self.assertEqual(unregistered_alias.status_code, 404)

    def test_route_maps_provider_timeout_and_accepts_season(self) -> None:
        with patch(
            "app.routes.weather.historical_weather_service.get_historical_average",
            side_effect=WeatherProviderTimeout("timed out"),
        ):
            client = TestClient(app)
            response = client.get(
                "/api/weather/kharif-historical",
                params={
                    "state_names": "Maharashtra",
                    "district_names": "PUNE",
                    "season": "Winter",
                },
            )
            client.close()
        self.assertEqual(response.status_code, 504)

        client = TestClient(app)
        bad_season = client.get(
            "/api/weather/kharif-historical",
            params={
                "state_names": "Maharashtra",
                "district_names": "PUNE",
                "season": "winter",
            },
        )
        unsupported_season = client.get(
            "/api/weather/kharif-historical",
            params={
                "state_names": "Maharashtra",
                "district_names": "PUNE",
                "season": "Monsoon",
            },
        )
        client.close()
        self.assertEqual(bad_season.status_code, 422)
        self.assertEqual(unsupported_season.status_code, 422)

    def test_route_distinguishes_no_data_and_provider_failure(self) -> None:
        for exception, status_code in (
            (WeatherDataUnavailable("no valid hours"), 503),
            (WeatherProviderError("upstream failure"), 502),
        ):
            with self.subTest(status_code=status_code):
                with patch(
                    "app.routes.weather.historical_weather_service.get_historical_average",
                    side_effect=exception,
                ):
                    client = TestClient(app)
                    response = client.get(
                        "/api/weather/kharif-historical",
                        params={
                            "state_names": "Maharashtra",
                            "district_names": "PUNE",
                        },
                    )
                    client.close()
                self.assertEqual(response.status_code, status_code)


if __name__ == "__main__":
    unittest.main(verbosity=2)
