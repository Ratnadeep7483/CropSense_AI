#!/usr/bin/env python3
"""Explicit batch generation for verified locations; no test invokes this."""

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.historical_weather_service import (  # noqa: E402
    HistoricalWeatherService,
    WeatherDataUnavailable,
    WeatherLocationNotFound,
    WeatherLocationUnresolved,
    WeatherProviderError,
    load_location_registry,
)


async def generate(
    service: HistoricalWeatherService,
    locations: list[tuple[str, str]],
    refresh: bool,
) -> None:
    failures = 0
    for index, (state, district) in enumerate(locations, start=1):
        try:
            result = await service.get_historical_average(
                state, district, "Kharif", force_refresh=refresh
            )
        except (
            WeatherDataUnavailable,
            WeatherLocationNotFound,
            WeatherLocationUnresolved,
            WeatherProviderError,
            OSError,
        ) as exc:
            print(f"[{index}/{len(locations)}] {state}/{district}: FAILED: {exc}")
            failures += 1
            continue
        print(
            f"[{index}/{len(locations)}] {state}/{district}: "
            f"{'refreshed' if refresh else 'cached' if result.cache['hit'] else 'fetched'} "
            f"ERA5 catalog; expires {result.cache['expires_at']}"
        )
    if failures:
        raise SystemExit(f"{failures} weather cache generation(s) failed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch one full hourly ERA5 window per verified registry point and "
            "cache aggregates for all six season categories."
        )
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all-verified", action="store_true")
    group.add_argument("--state")
    parser.add_argument("--district")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    if args.state and not args.district:
        parser.error("--district is required with --state")
    registry = load_location_registry()
    verified = [
        (state, district)
        for (state, district), entry in registry.items()
        if entry["coordinate_status"] == "verified_reference_point"
    ]
    if args.all_verified:
        locations = verified
    else:
        pair = (args.state, args.district)
        if pair not in registry:
            parser.error("The exact pair is not in the CSV-derived registry.")
        if registry[pair]["coordinate_status"] != "verified_reference_point":
            parser.error("The pair has no verified coordinates; no request sent.")
        locations = [pair]

    asyncio.run(generate(HistoricalWeatherService(), locations, args.refresh))


if __name__ == "__main__":
    main()
