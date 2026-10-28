"""Strictly prior-year crop-specific feature lookups from the training CSV."""

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
    "soil_for_crop",
    "crop_names",
    "crop_year",
    "area",
    "N",
    "P",
    "K",
    "npk_source",
)
NPK_COLUMNS = ("N", "P", "K")
NORMALIZED_COLUMNS = {
    "state_names": "_state_key",
    "district_names": "_district_key",
    "season_names": "_season_key",
    "soil_for_crop": "_soil_key",
    "crop_names": "_crop_key",
}


def _normalize_label(value: str) -> str:
    """Normalize label casing and whitespace without fuzzy/alias matching."""
    return " ".join(value.split()).casefold()


@dataclass(frozen=True)
class HistoricalFeatureLookupResult:
    """Historical feature values and explicit availability/provenance details."""

    area: float | None
    area_year: int | None
    area_status: str
    area_missing_reason: str | None
    N: float | None
    P: float | None
    K: float | None
    npk_year: int | None
    npk_source: str | None
    npk_status: str
    npk_missing_reason: str | None


class HistoricalFeatureDatasetError(RuntimeError):
    """The historical feature dataset is unreadable or malformed."""


class HistoricalFeatureLookupService:
    """Look up prior area and candidate-specific NPK without aggregation.

    NPK source labels are retained for transparency, but the notebook does
    not define their provenance or validate them as interchangeable. Until
    that evidence exists, this service does not expose NPK values for inference.
    """

    def __init__(self, dataset_path: Path = DATASET_PATH) -> None:
        self._dataset_path = dataset_path
        self._dataset: pd.DataFrame | None = None

    def _load_dataset(self) -> pd.DataFrame:
        if self._dataset is not None:
            return self._dataset

        try:
            dataset = pd.read_csv(
                self._dataset_path,
                usecols=list(LOOKUP_COLUMNS),
            )
        except (FileNotFoundError, ValueError, pd.errors.ParserError, OSError) as exc:
            logger.error("Historical feature dataset could not be read: %s", exc)
            raise HistoricalFeatureDatasetError(
                "Historical feature lookup dataset is unavailable or malformed."
            ) from exc

        if dataset.loc[:, list(LOOKUP_COLUMNS)].isna().any().any():
            raise HistoricalFeatureDatasetError(
                "Historical feature dataset contains missing lookup values."
            )

        for column in ("crop_year", "area", *NPK_COLUMNS):
            try:
                values = pd.to_numeric(dataset[column], errors="raise")
            except (TypeError, ValueError) as exc:
                raise HistoricalFeatureDatasetError(
                    f"Historical feature dataset contains non-numeric {column}."
                ) from exc
            if values.isna().any() or not values.map(
                lambda value: math.isfinite(float(value))
            ).all():
                raise HistoricalFeatureDatasetError(
                    f"Historical feature dataset contains invalid {column} values."
                )
            dataset[column] = values

        if not dataset["crop_year"].map(
            lambda value: float(value).is_integer()
        ).all():
            raise HistoricalFeatureDatasetError(
                "Historical feature dataset contains non-integer crop years."
            )
        dataset["crop_year"] = dataset["crop_year"].astype("int64")
        for column, normalized_column in NORMALIZED_COLUMNS.items():
            dataset[normalized_column] = dataset[column].map(_normalize_label)
        self._dataset = dataset
        return dataset

    def lookup(
        self,
        state: str,
        district: str,
        season: str,
        soil: str,
        crop: str,
        target_year: int,
    ) -> HistoricalFeatureLookupResult:
        """Return latest unambiguous area/NPK matches strictly before target year."""
        dataset = self._load_dataset()
        state_key = _normalize_label(state)
        district_key = _normalize_label(district)
        season_key = _normalize_label(season)
        soil_key = _normalize_label(soil)
        crop_key = _normalize_label(crop)
        matching = dataset.loc[
            (dataset["_state_key"] == state_key)
            & (dataset["_district_key"] == district_key)
            & (dataset["_season_key"] == season_key)
            & (dataset["_crop_key"] == crop_key)
            & (dataset["crop_year"] < target_year)
        ]

        area_rows = matching.sort_values("crop_year", ascending=False)
        area = None
        area_year = None
        area_status = "not_found"
        exact_key_rows = dataset.loc[
            (dataset["_state_key"] == state_key)
            & (dataset["_district_key"] == district_key)
            & (dataset["_season_key"] == season_key)
            & (dataset["_crop_key"] == crop_key)
        ]
        area_missing_reason = ""
        if not area_rows.empty:
            latest_area_year = int(area_rows.iloc[0]["crop_year"])
            latest_area_rows = area_rows.loc[
                area_rows["crop_year"] == latest_area_year
            ]
            unique_areas = latest_area_rows["area"].unique()
            area_year = latest_area_year
            if len(unique_areas) == 1:
                area = float(unique_areas[0])
                area_status = "available"
                area_missing_reason = None
            else:
                area_status = "ambiguous"
                area_missing_reason = (
                    "The latest matching year "
                    f"{latest_area_year} has conflicting area values."
                )
        elif exact_key_rows.empty:
            same_location_crop = dataset.loc[
                (dataset["_state_key"] == state_key)
                & (dataset["_district_key"] == district_key)
                & (dataset["_crop_key"] == crop_key)
            ]
            eligible_other_seasons = same_location_crop.loc[
                same_location_crop["crop_year"] < target_year
            ]
            if not same_location_crop.empty:
                other_seasons = sorted(
                    str(season_name)
                    for season_name in same_location_crop[
                        "season_names"
                    ].unique()
                )
                if not eligible_other_seasons.empty:
                    area_missing_reason = (
                        "No eligible historical area matches the normalized "
                        "state/district/season/crop key "
                        f"(state={state!r}, district={district!r}, "
                        f"season={season!r}, crop={crop!r}). Records exist for "
                        f"this location/crop only under other season labels "
                        f"{other_seasons}; cross-season fallback is not used. "
                        "Area lookup does not filter by soil."
                    )
                else:
                    other_years = sorted(
                        int(year)
                        for year in same_location_crop["crop_year"].unique()
                    )
                    area_missing_reason = (
                        "No eligible historical area matches the normalized "
                        "state/district/season/crop key "
                        f"(state={state!r}, district={district!r}, "
                        f"season={season!r}, crop={crop!r}). Same-location "
                        f"crop rows exist only for other season labels "
                        f"{other_seasons} and years {other_years}; cross-season "
                        "fallback is not used. Area lookup does not filter by soil."
                    )
            else:
                area_missing_reason = (
                    "No dataset rows match the normalized exact area lookup key "
                    f"(state={state!r}, district={district!r}, season={season!r}, "
                    f"crop={crop!r}); matching trims/collapses whitespace and "
                    "ignores case. No other-season fallback is used, and area "
                    "lookup does not filter by soil."
                )
        else:
            excluded_years = sorted(
                int(year) for year in exact_key_rows["crop_year"].unique()
            )
            area_missing_reason = (
                "Normalized exact-key historical rows exist only at or after "
                "target_year "
                f"{target_year}; the strict cutoff excludes years "
                f"{excluded_years}. Area lookup does not filter by soil."
            )

        npk_rows = matching.loc[matching["_soil_key"] == soil_key].sort_values(
            "crop_year", ascending=False
        )
        N = P = K = None
        npk_year = None
        npk_source = None
        npk_status = "not_found"
        npk_missing_reason = (
            "No matching crop/soil NPK record exists strictly before the target year."
        )
        if not npk_rows.empty:
            latest_npk_year = int(npk_rows.iloc[0]["crop_year"])
            latest_npk_rows = npk_rows.loc[
                npk_rows["crop_year"] == latest_npk_year
            ]
            npk_year = latest_npk_year
            value_rows = latest_npk_rows[
                [*NPK_COLUMNS, "npk_source"]
            ].drop_duplicates()
            if len(value_rows) != 1:
                npk_status = "ambiguous"
                npk_missing_reason = (
                    "The latest matching year has conflicting NPK values "
                    "or source labels."
                )
            else:
                npk_source = str(value_rows.iloc[0]["npk_source"])
                npk_status = "unverified_source"
                npk_missing_reason = (
                    "NPK values are withheld because the dataset and notebook "
                    "do not document or validate npk_source provenance."
                )

        return HistoricalFeatureLookupResult(
            area=area,
            area_year=area_year,
            area_status=area_status,
            area_missing_reason=area_missing_reason,
            N=N,
            P=P,
            K=K,
            npk_year=npk_year,
            npk_source=npk_source,
            npk_status=npk_status,
            npk_missing_reason=npk_missing_reason,
        )


historical_feature_lookup_service = HistoricalFeatureLookupService()
