#!/usr/bin/env python3

import json
import sys
import unittest
from datetime import date
from unittest.mock import patch

import httpx

BACKEND_ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.irrigation_weather_service import (  # noqa: E402
    WeatherApiError,
    geocode_district,
    get_daily_weather,
)


def provider_payload() -> dict:
    return {
        "daily_units": {
            "time": "iso8601",
            "temperature_2m_mean": "°C",
            "relative_humidity_2m_mean": "%",
            "precipitation_sum": "mm",
            "sunshine_duration": "s",
            "wind_speed_10m_mean": "km/h",
        },
        "daily": {
            "time": ["2024-06-15"],
            "temperature_2m_mean": [25.2],
            "relative_humidity_2m_mean": [81],
            "precipitation_sum": [3.4],
            "sunshine_duration": [40852.12],
            "wind_speed_10m_mean": [11.3],
        },
    }


class DailyWeatherTests(unittest.TestCase):
    def test_kerala_district_geocoding_uses_exact_state_and_admin_district(self) -> None:
        response = httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Ern\u0101kulam",
                        "admin1": "Kerala",
                        "admin2": "Ernakulam District",
                        "country_code": "IN",
                        "latitude": 9.96714,
                        "longitude": 76.29036,
                    }
                ]
            },
            request=httpx.Request("GET", "https://geocoding-api.open-meteo.com"),
        )
        with patch(
            "app.services.irrigation_weather_service.httpx.get",
            return_value=response,
        ) as mocked:
            coordinates = geocode_district("Kerala", "ERNAKULAM")

        self.assertEqual(coordinates, (9.96714, 76.29036))
        mocked.assert_called_once()
        self.assertEqual(mocked.call_args.kwargs["params"]["name"], "ERNAKULAM")
        self.assertEqual(mocked.call_args.kwargs["timeout"], 15.0)

    def test_geocoding_retries_transient_transport_failure(self) -> None:
        response = httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Ern\u0101kulam",
                        "admin1": "Kerala",
                        "admin2": "Ernakulam District",
                        "country_code": "IN",
                        "latitude": 9.96714,
                        "longitude": 76.29036,
                    }
                ]
            },
            request=httpx.Request("GET", "https://geocoding-api.open-meteo.com"),
        )
        with patch(
            "app.services.irrigation_weather_service.httpx.get",
            side_effect=[httpx.ConnectError("temporary connection reset"), response],
        ) as mocked:
            with self.assertLogs(
                "app.services.irrigation_weather_service", level="WARNING"
            ) as captured:
                coordinates = geocode_district("Kerala", "ERNAKULAM")

        self.assertEqual(coordinates, (9.96714, 76.29036))
        self.assertEqual(mocked.call_count, 2)
        self.assertIn("temporary connection reset", "\n".join(captured.output))

    def test_geocoding_retries_transient_provider_status(self) -> None:
        failure = httpx.Response(
            503,
            request=httpx.Request("GET", "https://geocoding-api.open-meteo.com"),
        )
        success = httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Ern\u0101kulam",
                        "admin1": "Kerala",
                        "admin2": "Ernakulam District",
                        "country_code": "IN",
                        "latitude": 9.96714,
                        "longitude": 76.29036,
                    }
                ]
            },
            request=httpx.Request("GET", "https://geocoding-api.open-meteo.com"),
        )
        with patch(
            "app.services.irrigation_weather_service.httpx.get",
            side_effect=[failure, success],
        ) as mocked:
            coordinates = geocode_district("Kerala", "ERNAKULAM")

        self.assertEqual(coordinates, (9.96714, 76.29036))
        self.assertEqual(mocked.call_count, 2)

    def test_geocoding_timeout_is_reported_after_one_retry(self) -> None:
        with patch(
            "app.services.irrigation_weather_service.httpx.get",
            side_effect=httpx.ReadTimeout("provider timed out"),
        ) as mocked:
            with self.assertLogs(
                "app.services.irrigation_weather_service", level="WARNING"
            ) as captured:
                with self.assertRaisesRegex(
                    WeatherApiError, "timed out after retry"
                ):
                    geocode_district("Kerala", "ERNAKULAM")

        self.assertEqual(mocked.call_count, 2)
        self.assertIn("provider timed out", "\n".join(captured.output))

    def test_geocoding_matches_accented_district_with_exact_state(self) -> None:
        response = httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Karn\u0101l",
                        "admin1": "Haryana",
                        "admin2": "Karn\u0101l District",
                        "country_code": "IN",
                        "latitude": 29.69197,
                        "longitude": 76.98448,
                    }
                ]
            },
            request=httpx.Request("GET", "https://geocoding-api.open-meteo.com"),
        )
        with patch(
            "app.services.irrigation_weather_service.httpx.get",
            return_value=response,
        ):
            coordinates = geocode_district("Haryana", "KARNAL")

        self.assertEqual(coordinates, (29.69197, 76.98448))

    def test_geocoding_rejects_results_for_a_different_state(self) -> None:
        response = httpx.Response(
            200,
            json={
                "results": [
                    {
                        "name": "Karn\u0101l",
                        "admin1": "Himachal Pradesh",
                        "admin2": "Karn\u0101l District",
                        "country_code": "IN",
                        "latitude": 31.7901,
                        "longitude": 76.88534,
                    }
                ]
            },
            request=httpx.Request("GET", "https://geocoding-api.open-meteo.com"),
        )
        with patch(
            "app.services.irrigation_weather_service.httpx.get",
            return_value=response,
        ):
            with self.assertRaisesRegex(WeatherApiError, "No geocoding result matched"):
                geocode_district("Haryana", "KARNAL")

    def test_archive_mapping_uses_verified_units_and_measurement_period(self) -> None:
        response = httpx.Response(
            200,
            json=provider_payload(),
            request=httpx.Request("GET", "https://archive-api.open-meteo.com"),
        )
        with patch("app.services.irrigation_weather_service.httpx.get", return_value=response):
            weather = get_daily_weather(18.51957, 73.85535, date(2024, 6, 15))

        self.assertAlmostEqual(weather["Temperature_C"], 25.2)
        self.assertEqual(weather["Humidity"], 81)
        self.assertAlmostEqual(weather["Rainfall_mm"], 3.4)
        self.assertAlmostEqual(weather["Sunlight_Hours"], 40852.12 / 3600)
        self.assertAlmostEqual(weather["Wind_Speed_kmh"], 11.3)
        self.assertEqual(weather["measurement"]["period"], "one calendar day")
        self.assertEqual(weather["measurement"]["timezone"], "UTC")
        self.assertEqual(weather["measurement"]["provider"], "archive")
        self.assertEqual(weather["measurement"]["not_mapped"], ["Soil_Moisture"])

    def test_forecast_uses_forecast_provider_for_today_or_future(self) -> None:
        response = httpx.Response(
            200,
            json=provider_payload(),
            request=httpx.Request("GET", "https://api.open-meteo.com"),
        )
        with patch("app.services.irrigation_weather_service.httpx.get", return_value=response) as mocked:
            get_daily_weather(18.51957, 73.85535, date.today())

        self.assertIn("/v1/forecast", mocked.call_args.args[0])

    def test_unexpected_unit_is_rejected(self) -> None:
        payload = provider_payload()
        payload["daily_units"]["temperature_2m_mean"] = "F"
        response = httpx.Response(
            200,
            json=payload,
            request=httpx.Request("GET", "https://archive-api.open-meteo.com"),
        )
        with patch("app.services.irrigation_weather_service.httpx.get", return_value=response):
            with self.assertRaises(WeatherApiError):
                get_daily_weather(18.51957, 73.85535, date(2024, 6, 15))

    def test_missing_field_is_rejected_without_substitution(self) -> None:
        payload = provider_payload()
        payload["daily"]["precipitation_sum"] = [None]
        response = httpx.Response(
            200,
            json=payload,
            request=httpx.Request("GET", "https://archive-api.open-meteo.com"),
        )
        with patch("app.services.irrigation_weather_service.httpx.get", return_value=response):
            with self.assertRaises(WeatherApiError):
                get_daily_weather(18.51957, 73.85535, date(2024, 6, 15))


if __name__ == "__main__":
    unittest.main(verbosity=2)
