"""Exact-key multi-year rainfall lookup from the crop recommendation dataset."""

import logging
import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "Copy of crop_recommendation_45_with_year_area.csv"
)
LOOKUP_COLUMNS = (
    "state_names",
    "district_names",
    "season_names",
    "crop_year",
    "rainfall_mm",
)
LOCATION_SEASON_COLUMNS = LOOKUP_COLUMNS[:3]
YEAR_COLUMN = "crop_year"
RAINFALL_COLUMN = "rainfall_mm"
RAINFALL_DESCRIPTION = (
    "Dataset-derived multi-year mean. Rainfall provenance and measurement "
    "semantics are unverified."
)
class RainfallDatasetError(RuntimeError):
    """The rainfall dataset cannot provide a valid lookup."""


class RainfallRecordNotFound(LookupError):
    """No dataset records match the exact state/district/season key."""


@dataclass(frozen=True)
class RainfallLookupResult:
    rainfall_mm: float
    matched_year_count: int
    observed_year_start: int
    observed_year_end: int


class RainfallLookupService:
    """Cache exact-key means over one validated rainfall value per observed year."""

    def __init__(self, dataset_path: Path = DATASET_PATH) -> None:
        self._dataset_path = dataset_path
        self._lookup: dict[
            tuple[str, str, str], RainfallLookupResult
        ] | None = None
        self._yearly_lookup: dict[
            tuple[str, str, str], tuple[tuple[int, float], ...]
        ] | None = None

    def _load_lookup(
        self,
    ) -> dict[tuple[str, str, str], RainfallLookupResult]:
        if self._lookup is not None:
            return self._lookup

        try:
            dataset = pd.read_csv(
                self._dataset_path,
                usecols=list(LOOKUP_COLUMNS),
            )
        except FileNotFoundError as exc:
            logger.error("Rainfall dataset was not found: %s", self._dataset_path)
            raise RainfallDatasetError(
                f"Historical rainfall dataset was not found: {self._dataset_path}"
            ) from exc
        except ValueError as exc:
            logger.error("Rainfall dataset is missing required columns: %s", exc)
            raise RainfallDatasetError(
                "Historical rainfall dataset must contain state_names, "
                "district_names, season_names, crop_year, and rainfall_mm."
            ) from exc
        except pd.errors.ParserError as exc:
            logger.error("Rainfall dataset could not be parsed: %s", exc)
            raise RainfallDatasetError(
                "Historical rainfall dataset could not be read."
            ) from exc
        except OSError as exc:
            logger.error("Rainfall dataset could not be read: %s", exc)
            raise RainfallDatasetError(
                "Historical rainfall dataset could not be read."
            ) from exc

        if dataset.loc[:, list(LOCATION_SEASON_COLUMNS)].isna().any().any():
            raise RainfallDatasetError(
                "Historical rainfall dataset contains missing state, district, "
                "or season keys."
            )
        if dataset.loc[:, list(LOCATION_SEASON_COLUMNS)].apply(
            lambda column: column.map(
                lambda value: isinstance(value, str) and not value.strip()
            )
        ).any().any():
            raise RainfallDatasetError(
                "Historical rainfall dataset contains blank state, district, "
                "or season keys."
            )

        if dataset[YEAR_COLUMN].isna().any():
            raise RainfallDatasetError(
                "Historical rainfall dataset contains missing crop_year values."
            )
        try:
            years = pd.to_numeric(dataset[YEAR_COLUMN], errors="raise")
        except (TypeError, ValueError) as exc:
            raise RainfallDatasetError(
                "Historical rainfall dataset contains non-numeric crop_year values."
            ) from exc
        if not years.map(
            lambda value: math.isfinite(float(value))
            and float(value).is_integer()
        ).all():
            raise RainfallDatasetError(
                "Historical rainfall dataset contains invalid crop_year values."
            )
        dataset[YEAR_COLUMN] = years.astype("int64")

        raw_rainfall = dataset[RAINFALL_COLUMN]
        if raw_rainfall.isna().any():
            raise RainfallDatasetError(
                "Historical rainfall dataset contains missing rainfall_mm values."
            )
        rainfall = pd.to_numeric(raw_rainfall, errors="coerce")
        if rainfall.isna().any():
            raise RainfallDatasetError(
                "Historical rainfall dataset contains non-numeric rainfall_mm values."
            )
        if not rainfall.map(lambda value: math.isfinite(float(value))).all():
            raise RainfallDatasetError(
                "Historical rainfall dataset contains non-finite rainfall_mm values."
            )
        if (rainfall < 0).any():
            raise RainfallDatasetError(
                "Historical rainfall dataset contains negative rainfall_mm values."
            )
        dataset[RAINFALL_COLUMN] = rainfall

        year_keys = [*LOCATION_SEASON_COLUMNS, YEAR_COLUMN]
        per_year = dataset.groupby(year_keys, sort=False, dropna=False)[
            RAINFALL_COLUMN
        ].agg(unique_values="nunique", **{RAINFALL_COLUMN: "first"})
        if (per_year["unique_values"] != 1).any():
            raise RainfallDatasetError(
                "Historical rainfall dataset contains conflicting rainfall_mm "
                "values for a state/district/season/year group."
            )

        per_year = per_year.reset_index()
        grouped = per_year.groupby(
            list(LOCATION_SEASON_COLUMNS),
            sort=False,
            dropna=False,
        ).agg(
            rainfall_mean=(
                RAINFALL_COLUMN,
                lambda values: math.fsum(values) / len(values),
            ),
            matched_year_count=(YEAR_COLUMN, "size"),
            observed_year_start=(YEAR_COLUMN, "min"),
            observed_year_end=(YEAR_COLUMN, "max"),
        )
        self._lookup = {
            (str(state), str(district), str(season)): RainfallLookupResult(
                rainfall_mm=float(row.rainfall_mean),
                matched_year_count=int(row.matched_year_count),
                observed_year_start=int(row.observed_year_start),
                observed_year_end=int(row.observed_year_end),
            )
            for (state, district, season), row in grouped.iterrows()
        }
        self._yearly_lookup = {}
        for (state, district, season), rows in per_year.groupby(
            list(LOCATION_SEASON_COLUMNS),
            sort=False,
            dropna=False,
        ):
            self._yearly_lookup[(str(state), str(district), str(season))] = tuple(
                (int(row[YEAR_COLUMN]), float(row[RAINFALL_COLUMN]))
                for _, row in rows.iterrows()
            )
        return self._lookup

    def lookup(
        self,
        state: str,
        district: str,
        season: str,
    ) -> RainfallLookupResult:
        """Return the exact-key mean across distinct observed years."""
        key = (state, district, season)
        result = self._load_lookup().get(key)
        if result is None:
            raise RainfallRecordNotFound(
                "No historical rainfall records match the exact state, district, "
                "and season selection."
            )
        return result

    def lookup_before_year(
        self,
        state: str,
        district: str,
        season: str,
        target_year: int,
    ) -> RainfallLookupResult:
        """Return a mean of distinct matching years strictly before target_year."""
        self._load_lookup()
        yearly_lookup = self._yearly_lookup
        if yearly_lookup is None:
            raise RainfallDatasetError("Historical rainfall lookup was not initialized.")
        records = yearly_lookup.get((state, district, season), ())
        prior_records = [
            (year, rainfall) for year, rainfall in records if year < target_year
        ]
        if not prior_records:
            raise RainfallRecordNotFound(
                "No historical rainfall records match the exact state, district, "
                "and season before the target year."
            )
        values = [rainfall for _, rainfall in prior_records]
        return RainfallLookupResult(
            rainfall_mm=math.fsum(values) / len(values),
            matched_year_count=len(values),
            observed_year_start=min(year for year, _ in prior_records),
            observed_year_end=max(year for year, _ in prior_records),
        )


rainfall_lookup_service = RainfallLookupService()
