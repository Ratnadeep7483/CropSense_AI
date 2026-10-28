"""Exact state/district/season lookup for historical crop-dataset NPK values."""

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
    "N",
    "P",
    "K",
)
YEAR_LOOKUP_COLUMNS = (
    *LOOKUP_COLUMNS[:3],
    "crop_year",
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "rainfall_mm",
)
IDENTITY_COLUMNS = LOOKUP_COLUMNS[:3]
NPK_COLUMNS = LOOKUP_COLUMNS[3:]
YEAR_FEATURE_COLUMNS = ("temperature", "humidity", "rainfall_mm")
SUPPORTED_CROP_YEAR_RANGE = range(1997, 2016)


@dataclass(frozen=True)
class NPKYearLookupResult:
    """NPK summary and invariant features from one exact training-data group."""

    crop_year: int
    N: float
    P: float
    K: float
    matched_records: int
    npk_aggregation: str
    npk_ranges: dict[str, dict[str, float]]
    temperature: float
    humidity: float
    rainfall_mm: float


class NPKDatasetError(RuntimeError):
    """The historical crop dataset cannot provide a valid NPK lookup."""


class NPKRecordNotFound(LookupError):
    """No dataset records match the exact state/district/season key."""


class NPKLookupService:
    """Load and cache exact-key mean NPK values from the crop dataset."""

    def __init__(self, dataset_path: Path = DATASET_PATH) -> None:
        self._dataset_path = dataset_path
        self._lookup: dict[tuple[str, str, str], tuple[float, float, float, int]] | None = None
        self._year_dataset: pd.DataFrame | None = None

    def _load_lookup(self) -> dict[tuple[str, str, str], tuple[float, float, float, int]]:
        if self._lookup is not None:
            return self._lookup

        try:
            dataset = pd.read_csv(self._dataset_path, usecols=list(LOOKUP_COLUMNS))
        except FileNotFoundError as exc:
            logger.error("NPK dataset was not found: %s", self._dataset_path)
            raise NPKDatasetError(
                f"Historical NPK dataset was not found: {self._dataset_path}"
            ) from exc
        except ValueError as exc:
            logger.error("NPK dataset is missing required columns: %s", exc)
            raise NPKDatasetError(
                "Historical NPK dataset must contain state_names, "
                "district_names, season_names, N, P, and K columns."
            ) from exc
        except pd.errors.ParserError as exc:
            logger.error("NPK dataset could not be parsed: %s", exc)
            raise NPKDatasetError("Historical NPK dataset could not be read.") from exc
        except OSError as exc:
            logger.error("NPK dataset could not be read: %s", exc)
            raise NPKDatasetError("Historical NPK dataset could not be read.") from exc

        if dataset.loc[:, list(IDENTITY_COLUMNS)].isna().any().any():
            raise NPKDatasetError(
                "Historical NPK dataset contains blank state, district, or season keys."
            )

        try:
            dataset.loc[:, list(NPK_COLUMNS)] = dataset.loc[
                :, list(NPK_COLUMNS)
            ].apply(pd.to_numeric, errors="raise")
        except (TypeError, ValueError) as exc:
            raise NPKDatasetError(
                "Historical NPK dataset contains non-numeric N, P, or K values."
            ) from exc

        if dataset.loc[:, list(NPK_COLUMNS)].isna().any().any():
            raise NPKDatasetError(
                "Historical NPK dataset contains missing N, P, or K values."
            )
        if not dataset.loc[:, list(NPK_COLUMNS)].map(
            lambda value: math.isfinite(float(value))
        ).all().all():
            raise NPKDatasetError(
                "Historical NPK dataset contains non-finite N, P, or K values."
            )

        grouped = (
            dataset.groupby(list(IDENTITY_COLUMNS), sort=False, as_index=False)
            .agg(
                N=("N", "mean"),
                P=("P", "mean"),
                K=("K", "mean"),
                matched_records=("N", "size"),
            )
        )
        self._lookup = {
            (str(row.state_names), str(row.district_names), str(row.season_names)): (
                float(row.N),
                float(row.P),
                float(row.K),
                int(row.matched_records),
            )
            for row in grouped.itertuples(index=False)
        }
        return self._lookup

    def lookup(
        self, state: str, district: str, season: str, crop_year: int | None = None
    ) -> tuple[float, float, float, int] | NPKYearLookupResult:
        """Return legacy NPK means or same-year features for an exact key."""
        if crop_year is not None:
            if crop_year not in SUPPORTED_CROP_YEAR_RANGE:
                raise ValueError(
                    "crop_year must be between 1997 and 2015, inclusive."
                )
            return self._lookup_year(state, district, season, crop_year)

        key = (state, district, season)
        result = self._load_lookup().get(key)
        if result is None:
            raise NPKRecordNotFound(
                "No historical NPK records match the exact state, district, "
                "and season selection."
            )
        return result

    def _load_year_dataset(self) -> pd.DataFrame:
        if self._year_dataset is not None:
            return self._year_dataset

        try:
            dataset = pd.read_csv(
                self._dataset_path,
                usecols=list(YEAR_LOOKUP_COLUMNS),
            )
        except (FileNotFoundError, ValueError, pd.errors.ParserError, OSError) as exc:
            logger.error("Year-specific NPK dataset could not be read: %s", exc)
            raise NPKDatasetError(
                "Year-specific NPK lookup requires state, district, season, "
                "crop_year, N, P, K, temperature, humidity, and rainfall_mm."
            ) from exc

        key_columns = [*IDENTITY_COLUMNS, "crop_year"]
        if dataset[key_columns].isna().any().any():
            raise NPKDatasetError(
                "Year-specific NPK data contains missing lookup keys."
            )

        for column in [*NPK_COLUMNS, *YEAR_FEATURE_COLUMNS]:
            try:
                values = pd.to_numeric(dataset[column], errors="raise")
            except (TypeError, ValueError) as exc:
                raise NPKDatasetError(
                    f"Year-specific NPK data contains non-numeric {column} values."
                ) from exc
            if values.isna().any() or not values.map(
                lambda value: math.isfinite(float(value))
            ).all():
                raise NPKDatasetError(
                    f"Year-specific NPK data contains missing or non-finite "
                    f"{column} values."
                )
            dataset[column] = values

        try:
            years = pd.to_numeric(dataset["crop_year"], errors="raise")
        except (TypeError, ValueError) as exc:
            raise NPKDatasetError(
                "Year-specific NPK data contains non-numeric crop_year values."
            ) from exc
        if not years.map(
            lambda value: math.isfinite(float(value))
            and float(value).is_integer()
        ).all():
            raise NPKDatasetError(
                "Year-specific NPK data contains invalid crop_year values."
            )
        dataset["crop_year"] = years.astype("int64")
        self._year_dataset = dataset
        return self._year_dataset

    def _lookup_year(
        self, state: str, district: str, season: str, crop_year: int
    ) -> NPKYearLookupResult:
        dataset = self._load_year_dataset()
        rows = dataset.loc[
            (dataset["state_names"] == state)
            & (dataset["district_names"] == district)
            & (dataset["season_names"] == season)
            & (dataset["crop_year"] == crop_year)
        ]
        if rows.empty:
            raise NPKRecordNotFound(
                "No training-data records match the exact state, district, "
                "season, and crop year."
            )

        feature_values: dict[str, float] = {}
        for feature in YEAR_FEATURE_COLUMNS:
            unique_values = rows[feature].unique()
            if len(unique_values) != 1:
                raise NPKDatasetError(
                    f"Conflicting {feature} values for "
                    f"{state}/{district}/{season}/{crop_year}; "
                    "the lookup will not select an arbitrary row."
                )
            feature_values[feature] = float(unique_values[0])

        ranges = {
            feature: {
                "minimum": float(rows[feature].min()),
                "maximum": float(rows[feature].max()),
            }
            for feature in NPK_COLUMNS
        }
        return NPKYearLookupResult(
            crop_year=crop_year,
            N=float(rows["N"].mean()),
            P=float(rows["P"].mean()),
            K=float(rows["K"].mean()),
            matched_records=len(rows),
            npk_aggregation="arithmetic_mean",
            npk_ranges=ranges,
            **feature_values,
        )


npk_lookup_service = NPKLookupService()
