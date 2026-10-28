#!/usr/bin/env python3
"""Run isolated candidate-wise inference with the deployed crop artifacts."""

import asyncio
import json
import math
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.candidate_wise_crop_experiment import (  # noqa: E402
    candidate_wise_crop_experiment,
)
from app.services.crop_service import crop_service  # noqa: E402
from app.services.historical_weather_service import (  # noqa: E402
    HistoricalWeatherService,
)
from app.services.rainfall_lookup_service import (  # noqa: E402
    rainfall_lookup_service,
)


async def run_experiment() -> dict[str, Any]:
    if not crop_service.is_loaded:
        crop_service.load_model()
    if not crop_service.is_loaded:
        raise RuntimeError(
            "Existing crop model artifacts could not be loaded: "
            f"{crop_service.load_error}"
        )

    state = "Karnataka"
    district = "MYSORE"
    season = "Kharif"
    soil = "Black"
    target_year = date.today().year
    context = candidate_wise_crop_experiment.validate_context(
        state=state,
        district=district,
        season=season,
        soil=soil,
    )

    with tempfile.TemporaryDirectory(prefix="crop-weather-experiment-") as cache_dir:
        weather = await HistoricalWeatherService(
            cache_dir=Path(cache_dir)
        ).get_historical_average(
            context["state_names"],
            context["district_names"],
            context["season_names"],
        )

    weather_years = weather.period.get("season_start_years", [])
    if not weather_years or any(year >= target_year for year in weather_years):
        raise RuntimeError(
            "Weather service did not return exclusively pre-target-year data."
        )
    temperature = weather.averages.get("temperature_2m")
    humidity = weather.averages.get("relative_humidity_2m")
    if (
        not isinstance(temperature, (int, float))
        or isinstance(temperature, bool)
        or not math.isfinite(float(temperature))
        or not isinstance(humidity, (int, float))
        or isinstance(humidity, bool)
        or not math.isfinite(float(humidity))
    ):
        raise RuntimeError("Weather service returned missing or invalid values.")

    rainfall = rainfall_lookup_service.lookup_before_year(
        context["state_names"],
        context["district_names"],
        context["season_names"],
        target_year,
    )
    if rainfall.observed_year_end >= target_year:
        raise RuntimeError("Rainfall lookup included target-year or future data.")

    result = candidate_wise_crop_experiment.run_with_existing_npk_lookup(
        state=context["state_names"],
        district=context["district_names"],
        season=context["season_names"],
        soil=context["soil_for_crop"],
        target_year=target_year,
        temperature=float(temperature),
        humidity=float(humidity),
        rainfall_mm=rainfall.rainfall_mm,
    )

    scores = [
        {"crop": candidate.crop, "score": candidate.score}
        for candidate in result.candidates
        if candidate.score is not None
    ]
    return {
        "experiment": "isolated_candidate_wise_real_artifacts",
        "target_year": target_year,
        "location": {
            "state": context["state_names"],
            "district": context["district_names"],
            "season": context["season_names"],
            "soil": context["soil_for_crop"],
        },
        "weather": {
            "temperature_c": float(temperature),
            "humidity_percent": float(humidity),
            "source_years": weather_years,
            "compatibility_verified": False,
        },
        "rainfall": {
            "rainfall_mm": rainfall.rainfall_mm,
            "observed_year_start": rainfall.observed_year_start,
            "observed_year_end": rainfall.observed_year_end,
            "matched_year_count": rainfall.matched_year_count,
            "compatibility_verified": False,
        },
        "candidate_count": result.total_candidates,
        "area_available": result.area_available,
        "missing_area_history": result.missing_history,
        "ambiguous_area": result.ambiguous_area,
        "missing_or_invalid_npk": result.npk_unavailable_or_unverified,
        "validation_failures": result.validation_failures,
        "scored_candidates": result.scored_candidates,
        "scores": scores,
        "ranking_status": result.ranking_status,
        "ranking_limitation": result.ranking_limitation,
        "recommendation_available": False,
        "recommendation_reason": (
            "Weather/rainfall compatibility with model training and "
            "candidate-wise score comparability are unvalidated."
        ),
        "candidate_statuses": [
            {
                "crop": candidate.crop,
                "status": candidate.status,
                "area_year": candidate.area_year,
                "error": candidate.error,
            }
            for candidate in result.candidates
        ],
    }


def main() -> None:
    print(json.dumps(asyncio.run(run_experiment()), indent=2))


if __name__ == "__main__":
    main()
