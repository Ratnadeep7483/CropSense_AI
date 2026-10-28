"""Dataset-backed crop locations, historical areas, and model-row lookup."""

import logging
import math
from pathlib import Path
from typing import Literal, TypedDict

import pandas as pd

logger = logging.getLogger(__name__)

DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "Copy of crop_recommendation_45_with_year_area.csv"
)
MODEL_FEATURE_COLUMNS = (
    "state_names",
    "district_names",
    "season_names",
    "soil_for_crop",
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "rainfall_mm",
    "crop_year",
    "area",
)
NUMERIC_FEATURE_COLUMNS = (
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "rainfall_mm",
    "crop_year",
    "area",
)
DATASET_COLUMNS = (
    *MODEL_FEATURE_COLUMNS[:4],
    "crop_names",
    *MODEL_FEATURE_COLUMNS[4:],
    "npk_source",
)


class HistoricalAreaRecord(TypedDict):
    state_names: str
    district_names: str
    crop: str
    season: str
    year: int
    soil_for_crop: str | None
    area_hectares: float | None
    status: Literal["available", "ambiguous", "missing"]
    N: float | None
    P: float | None
    K: float | None
    temperature: float | None
    humidity: float | None
    rainfall_mm: float | None
    npk_source: str | None
    matching_records: int
    feature_issues: dict[str, str]


class HistoricalModelRecord(TypedDict):
    model_inputs: dict[str, str | int | float]
    crop: str
    npk_source: str | None
    matching_records: int


class CropLocationDatasetError(RuntimeError):
    """The crop dataset cannot provide reliable location or area lookups."""


class HistoricalCropRecordNotFound(LookupError):
    """No exact historical crop record matches the selected context."""


class HistoricalCropRecordAmbiguous(LookupError):
    """An exact historical crop key resolves to conflicting dataset rows."""


class HistoricalCropFeaturesUnavailable(ValueError):
    """A matched record lacks one or more required model features."""

    def __init__(self, feature_issues: dict[str, str]) -> None:
        self.feature_issues = feature_issues
        details = ", ".join(
            f"{name}: {reason}" for name, reason in feature_issues.items()
        )
        super().__init__(f"Required dataset features are unavailable ({details}).")


class CropLocationService:
    """Read dataset-derived locations and exact historical training rows."""

    def __init__(self, dataset_path: Path = DATASET_PATH) -> None:
        self._dataset_path = dataset_path
        self._dataset: pd.DataFrame | None = None

    def _load_dataset(self) -> pd.DataFrame:
        if self._dataset is not None:
            return self._dataset

        try:
            dataset = pd.read_csv(
                self._dataset_path,
                usecols=list(DATASET_COLUMNS),
            )
        except (FileNotFoundError, ValueError, pd.errors.ParserError, OSError) as exc:
            logger.error("Crop feature dataset could not be read: %s", exc)
            raise CropLocationDatasetError(
                "Crop location, area, and feature data is unavailable."
            ) from exc

        label_columns = [
            "state_names",
            "district_names",
            "season_names",
            "crop_names",
        ]
        if dataset[label_columns].isna().any().any():
            raise CropLocationDatasetError(
                "Crop dataset contains missing state, district, season, or crop labels."
            )

        try:
            years = pd.to_numeric(dataset["crop_year"], errors="raise")
        except (TypeError, ValueError) as exc:
            raise CropLocationDatasetError(
                "Crop dataset contains invalid crop_year values."
            ) from exc
        if (
            years.isna().any()
            or not years.map(lambda value: math.isfinite(float(value))).all()
            or not years.map(lambda value: float(value).is_integer()).all()
        ):
            raise CropLocationDatasetError(
                "Crop dataset contains invalid crop_year values."
            )
        dataset["crop_year"] = years.astype("int64")

        for column in NUMERIC_FEATURE_COLUMNS:
            if column == "crop_year":
                continue
            dataset[column] = pd.to_numeric(dataset[column], errors="coerce")

        self._dataset = dataset
        return dataset

    @staticmethod
    def _unique_feature_value(
        rows: pd.DataFrame, column: str
    ) -> tuple[str | float | None, str | None]:
        values = rows[column].dropna().unique()
        if len(values) == 0:
            return None, "missing"
        if len(values) > 1:
            return None, "conflicting dataset records"
        value = values[0]
        if column in NUMERIC_FEATURE_COLUMNS:
            numeric_value = float(value)
            if not math.isfinite(numeric_value):
                return None, "non-finite dataset value"
            if column == "crop_year":
                if not numeric_value.is_integer():
                    return None, "invalid year"
                return int(numeric_value), None
            return numeric_value, None
        label = str(value).strip()
        return (label, None) if label else (None, "blank dataset value")

    def get_options(
        self,
        state: str | None = None,
        district: str | None = None,
    ) -> tuple[list[str], list[str], list[str]]:
        """Return states and the exact state/district-specific options."""
        dataset = self._load_dataset()
        states = sorted(dataset["state_names"].drop_duplicates().tolist())
        districts: list[str] = []
        seasons: list[str] = []

        if state is not None:
            state_rows = dataset.loc[dataset["state_names"] == state]
            districts = sorted(state_rows["district_names"].drop_duplicates().tolist())
            if district is not None:
                district_rows = state_rows.loc[
                    state_rows["district_names"] == district
                ]
                seasons = sorted(
                    district_rows["season_names"].drop_duplicates().tolist()
                )

        return states, districts, seasons

    def get_historical_area(
        self,
        state: str,
        district: str,
        season: str | None = None,
    ) -> list[HistoricalAreaRecord]:
        """Return matching crop/year/soil records without averaging feature rows."""
        dataset = self._load_dataset()
        matching = dataset.loc[
            (dataset["state_names"] == state)
            & (dataset["district_names"] == district)
        ]
        if season is not None:
            matching = matching.loc[matching["season_names"] == season]

        records: list[HistoricalAreaRecord] = []
        group_columns = [
            "state_names",
            "district_names",
            "crop_names",
            "season_names",
            "crop_year",
            "soil_for_crop",
        ]
        for key, rows in matching.groupby(
            group_columns,
            sort=True,
            dropna=False,
        ):
            state_name, district_name, crop, season_name, year, _ = key
            extracted: dict[str, str | float | int | None] = {}
            feature_issues: dict[str, str] = {}
            for column in MODEL_FEATURE_COLUMNS:
                value, issue = self._unique_feature_value(rows, column)
                extracted[column] = value
                if issue:
                    feature_issues[column] = issue

            area_value = extracted["area"]
            if "area" in feature_issues:
                area_status: Literal["available", "ambiguous", "missing"] = (
                    "ambiguous"
                    if feature_issues["area"] == "conflicting dataset records"
                    else "missing"
                )
                area_hectares = None
            elif isinstance(area_value, (float, int)):
                area_status = "available"
                area_hectares = float(area_value)
            else:
                area_status = "missing"
                area_hectares = None

            npk_sources = rows["npk_source"].dropna().unique()
            npk_source = (
                str(npk_sources[0]).strip()
                if len(npk_sources) == 1 and str(npk_sources[0]).strip()
                else None
            )
            if npk_source is None:
                feature_issues["NPK provenance"] = (
                    "missing or conflicting npk_source values"
                )

            records.append(
                {
                    "state_names": str(state_name),
                    "district_names": str(district_name),
                    "crop": str(crop),
                    "season": str(season_name),
                    "year": int(year),
                    "soil_for_crop": (
                        str(extracted["soil_for_crop"])
                        if extracted["soil_for_crop"] is not None
                        else None
                    ),
                    "area_hectares": area_hectares,
                    "status": area_status,
                    "N": self._optional_numeric(extracted["N"]),
                    "P": self._optional_numeric(extracted["P"]),
                    "K": self._optional_numeric(extracted["K"]),
                    "temperature": self._optional_numeric(extracted["temperature"]),
                    "humidity": self._optional_numeric(extracted["humidity"]),
                    "rainfall_mm": self._optional_numeric(extracted["rainfall_mm"]),
                    "npk_source": npk_source,
                    "matching_records": len(rows),
                    "feature_issues": feature_issues,
                }
            )

        return records

    @staticmethod
    def _optional_numeric(value: str | float | int | None) -> float | None:
        return float(value) if isinstance(value, (float, int)) else None

    def get_model_record(
        self,
        state: str,
        district: str,
        season: str,
        crop: str,
        year: int,
        soil: str,
    ) -> HistoricalModelRecord:
        """Return the exact 12-feature row, rejecting missing or conflicting data."""
        dataset = self._load_dataset()
        rows = dataset.loc[
            (dataset["state_names"] == state)
            & (dataset["district_names"] == district)
            & (dataset["season_names"] == season)
            & (dataset["crop_names"] == crop)
            & (dataset["crop_year"] == year)
            & (dataset["soil_for_crop"] == soil)
        ]
        if rows.empty:
            raise HistoricalCropRecordNotFound(
                "No dataset record matches the exact state, district, season, "
                "crop, year, and soil selection."
            )

        model_inputs: dict[str, str | int | float] = {}
        feature_issues: dict[str, str] = {}
        for column in MODEL_FEATURE_COLUMNS:
            value, issue = self._unique_feature_value(rows, column)
            if issue or value is None:
                feature_issues[column] = issue or "missing"
            else:
                model_inputs[column] = value

        npk_sources = rows["npk_source"].dropna().unique()
        npk_source = (
            str(npk_sources[0]).strip()
            if len(npk_sources) == 1 and str(npk_sources[0]).strip()
            else None
        )
        if npk_source is None:
            feature_issues["NPK provenance"] = (
                "missing or conflicting npk_source values"
            )

        if any(
            reason == "conflicting dataset records"
            for reason in feature_issues.values()
        ):
            raise HistoricalCropRecordAmbiguous(
                "The selected crop/year/soil key has conflicting dataset values."
            )
        if feature_issues:
            raise HistoricalCropFeaturesUnavailable(feature_issues)

        return {
            "model_inputs": model_inputs,
            "crop": crop,
            "npk_source": npk_source,
            "matching_records": len(rows),
        }


crop_location_service = CropLocationService()
