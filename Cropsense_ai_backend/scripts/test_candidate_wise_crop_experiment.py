#!/usr/bin/env python3
"""Focused tests for the isolated candidate-wise crop scoring experiment."""

import csv
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.candidate_wise_crop_experiment import (  # noqa: E402
    CandidateWiseCropExperiment,
    VerifiedNPKFeatures,
)
from app.services.crop_service import FEATURE_COLUMNS  # noqa: E402
from app.services.historical_feature_lookup_service import (  # noqa: E402
    HistoricalFeatureLookupService,
)
from app.services.npk_lookup_service import (  # noqa: E402
    NPKRecordNotFound,
    NPKYearLookupResult,
)


class FakeLabelEncoder:
    def __init__(self, classes: list[str]) -> None:
        self.classes_ = np.asarray(classes)
        self._ids = {crop: index for index, crop in enumerate(classes)}

    def transform(self, labels: list[str]) -> np.ndarray:
        return np.asarray([self._ids[label] for label in labels])


class FakePreprocessor:
    def __init__(self) -> None:
        names = [
            "state_names",
            "district_names",
            "season_names",
            "soil_for_crop",
        ]
        categories = [
            np.asarray(["Karnataka"]),
            np.asarray(["BELGAUM"]),
            np.asarray(["Kharif"]),
            np.asarray(["Black"]),
        ]
        self.named_transformers_ = {
            "cat": SimpleNamespace(
                feature_names_in_=np.asarray(names),
                categories_=categories,
            )
        }
        self.inputs = []

    def transform(self, values):
        self.inputs.append(values.copy())
        return values


class FakeModel:
    def __init__(self, class_count: int) -> None:
        self.classes_ = np.arange(class_count)
        self.calls = 0

    def predict_proba(self, _):
        self.calls += 1
        return np.asarray([[index / 100 for index in range(len(self.classes_))]])


class FakeCropModelService:
    def __init__(self, classes: list[str]) -> None:
        self._label_encoder = FakeLabelEncoder(classes)
        self._preprocessor = FakePreprocessor()
        self._model = FakeModel(len(classes))


class FakeYearNPKLookup:
    def __init__(self, missing_year: int | None = None) -> None:
        self.missing_year = missing_year
        self.looked_up_years = []

    def lookup(self, state, district, season, crop_year):
        self.looked_up_years.append(crop_year)
        if crop_year == self.missing_year:
            raise NPKRecordNotFound("No NPK record for this historical year.")
        return NPKYearLookupResult(
            crop_year=crop_year,
            N=11.0,
            P=22.0,
            K=33.0,
            matched_records=3,
            npk_aggregation="arithmetic_mean",
            npk_ranges={
                "N": {"minimum": 10.0, "maximum": 12.0},
                "P": {"minimum": 20.0, "maximum": 24.0},
                "K": {"minimum": 30.0, "maximum": 36.0},
            },
            temperature=20.0,
            humidity=60.0,
            rainfall_mm=500.0,
        )


class CandidateWiseCropExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.crops = [f"Crop {index:02d}" for index in range(45)]

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.dataset_path = Path(self.temp.name) / "features.csv"
        self._write_dataset()
        self.lookup = HistoricalFeatureLookupService(self.dataset_path)
        self.model_service = FakeCropModelService(self.crops)
        self.experiment = CandidateWiseCropExperiment(
            historical_lookup=self.lookup,
            model_service=self.model_service,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_dataset(self, unsupported_location: bool = False) -> None:
        columns = [
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
        ]
        rows = []
        for index, crop in enumerate(self.crops):
            rows.append(
                {
                    "state_names": "Karnataka",
                    "district_names": "BELGAUM",
                    "season_names": "Kharif",
                    "soil_for_crop": "Black",
                    "crop_names": crop,
                    "crop_year": 2019 + (index % 2),
                    "area": 10.0 + index,
                    "N": 1,
                    "P": 2,
                    "K": 3,
                    "npk_source": "unverified_source",
                }
            )
        rows.extend(
            [
                {
                    **rows[0],
                    "crop_year": 2021,
                    "area": 999.0,
                },
                {
                    **rows[0],
                    "crop_year": 2018,
                    "area": 5.0,
                },
            ]
        )
        if unsupported_location:
            rows.extend(
                {
                    **row,
                    "state_names": "Unsupported State",
                }
                for row in rows[: len(self.crops)]
            )
        with self.dataset_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

    def _verified_npk(self) -> dict[str, VerifiedNPKFeatures]:
        return {
            crop: VerifiedNPKFeatures(
                N=float(index + 1),
                P=float(index + 2),
                K=float(index + 3),
                crop_year=2019 + (index % 2),
                source="owner-validated-test-source",
                provenance_verified=True,
            )
            for index, crop in enumerate(self.crops)
        }

    def _run(self, **overrides):
        args = {
            "state": "Karnataka",
            "district": "BELGAUM",
            "season": "Kharif",
            "soil": "Black",
            "target_year": 2021,
            "temperature": 20.0,
            "humidity": 60.0,
            "rainfall_mm": 500.0,
            "verified_npk_by_crop": None,
            "shared_features_verified": True,
        }
        args.update(overrides)
        return self.experiment.run(**args)

    def test_enumerates_45_candidates_and_withholds_scores_without_verified_npk(self):
        result = self._run()

        self.assertEqual(result.total_candidates, 45)
        self.assertEqual(result.area_available, 45)
        self.assertEqual(result.npk_unavailable_or_unverified, 45)
        self.assertEqual(result.scored_candidates, 0)
        self.assertFalse(result.complete_trustworthy_prediction_available)
        self.assertTrue(
            all(candidate.status == "npk_unavailable" for candidate in result.candidates)
        )
        self.assertEqual(self.model_service._model.calls, 0)

    def test_unverified_candidate_npk_is_withheld(self):
        npk_by_crop = self._verified_npk()
        npk_by_crop[self.crops[0]] = VerifiedNPKFeatures(
            N=1.0,
            P=2.0,
            K=3.0,
            crop_year=2019,
            source="estimated_ranges",
            provenance_verified=False,
        )

        result = self._run(verified_npk_by_crop=npk_by_crop)

        self.assertEqual(result.npk_unavailable_or_unverified, 1)
        self.assertEqual(result.scored_candidates, 44)
        self.assertEqual(result.candidates[0].status, "npk_unavailable")
        self.assertIsNone(result.candidates[0].score)
        self.assertFalse(result.complete_trustworthy_prediction_available)

    def test_scores_use_each_candidates_paired_prior_area_and_year(self):
        result = self._run(verified_npk_by_crop=self._verified_npk())

        self.assertEqual(result.scored_candidates, 45)
        self.assertFalse(result.complete_trustworthy_prediction_available)
        self.assertEqual(result.ranking_status, "not_validated")
        self.assertEqual(len(self.model_service._preprocessor.inputs), 45)
        first_candidate = self.model_service._preprocessor.inputs[0].iloc[0]
        self.assertEqual(first_candidate["area"], 10.0)
        self.assertEqual(first_candidate["crop_year"], 2019)
        self.assertNotEqual(first_candidate["crop_year"], 2021)
        self.assertEqual(
            list(self.model_service._preprocessor.inputs[0].columns),
            FEATURE_COLUMNS,
        )
        first_candidate = self.model_service._preprocessor.inputs[0].iloc[0]
        self.assertEqual(
            {
                "state_names": first_candidate["state_names"],
                "district_names": first_candidate["district_names"],
                "season_names": first_candidate["season_names"],
                "soil_for_crop": first_candidate["soil_for_crop"],
            },
            {
                "state_names": "Karnataka",
                "district_names": "BELGAUM",
                "season_names": "Kharif",
                "soil_for_crop": "Black",
            },
        )
        for feature in (
            "N",
            "P",
            "K",
            "temperature",
            "humidity",
            "rainfall_mm",
            "crop_year",
            "area",
        ):
            self.assertIsInstance(first_candidate[feature], (int, float, np.number))
        self.assertEqual(
            tuple(first_candidate[feature] for feature in FEATURE_COLUMNS),
            (
                "Karnataka",
                "BELGAUM",
                "Kharif",
                "Black",
                1.0,
                2.0,
                3.0,
                20.0,
                60.0,
                500.0,
                2019,
                10.0,
            ),
        )
        self.assertEqual(result.candidates[0].score, 0.0)

    def test_missing_shared_feature_is_reported_for_each_area_match(self):
        result = self._run(
            temperature=None,
            verified_npk_by_crop=self._verified_npk(),
        )

        self.assertEqual(result.validation_failures, 45)
        self.assertEqual(result.scored_candidates, 0)
        self.assertTrue(
            all(
                candidate.status == "input_validation_failed"
                for candidate in result.candidates
            )
        )
        self.assertEqual(self.model_service._model.calls, 0)

    def test_missing_humidity_or_rainfall_blocks_all_model_inputs(self):
        for missing_feature in ("humidity", "rainfall_mm"):
            with self.subTest(missing_feature=missing_feature):
                result = self._run(
                    **{missing_feature: None},
                    verified_npk_by_crop=self._verified_npk(),
                )

                self.assertEqual(result.validation_failures, 45)
                self.assertEqual(result.scored_candidates, 0)
                self.assertEqual(self.model_service._model.calls, 0)

    def test_unverified_shared_climate_features_block_scores(self):
        result = self._run(verified_npk_by_crop=self._verified_npk(),
                           shared_features_verified=False)

        self.assertEqual(result.shared_features_unverified, 45)
        self.assertEqual(result.scored_candidates, 0)
        self.assertTrue(
            all(
                candidate.status == "shared_features_unverified"
                for candidate in result.candidates
            )
        )
        self.assertEqual(self.model_service._model.calls, 0)

    def test_existing_npk_lookup_scores_only_with_present_values_and_marks_scores_experimental(self):
        npk_lookup = FakeYearNPKLookup()
        experiment = CandidateWiseCropExperiment(
            historical_lookup=self.lookup,
            model_service=self.model_service,
            npk_lookup=npk_lookup,
        )

        result = experiment.run_with_existing_npk_lookup(
            state="Karnataka",
            district="BELGAUM",
            season="Kharif",
            soil="Black",
            target_year=2021,
            temperature=20.0,
            humidity=60.0,
            rainfall_mm=500.0,
        )

        self.assertEqual(result.scored_candidates, 45)
        self.assertEqual(result.npk_unavailable_or_unverified, 0)
        self.assertEqual(result.shared_features_unverified, 45)
        self.assertEqual(result.ranking_status, "not_validated")
        self.assertFalse(result.complete_trustworthy_prediction_available)
        self.assertTrue(
            all(
                candidate.status == "scored_experimental"
                for candidate in result.candidates
            )
        )
        self.assertTrue(
            all(
                "climate values" in (candidate.error or "")
                for candidate in result.candidates
            )
        )
        self.assertEqual(len(npk_lookup.looked_up_years), 45)
        first_row = self.model_service._preprocessor.inputs[0].iloc[0]
        self.assertEqual((first_row["N"], first_row["P"], first_row["K"]), (11, 22, 33))
        self.assertEqual(first_row["crop_year"], npk_lookup.looked_up_years[0])

    def test_missing_existing_npk_history_does_not_score_that_year_group(self):
        npk_lookup = FakeYearNPKLookup(missing_year=2019)
        experiment = CandidateWiseCropExperiment(
            historical_lookup=self.lookup,
            model_service=self.model_service,
            npk_lookup=npk_lookup,
        )

        result = experiment.run_with_existing_npk_lookup(
            state="Karnataka",
            district="BELGAUM",
            season="Kharif",
            soil="Black",
            target_year=2021,
            temperature=20.0,
            humidity=60.0,
            rainfall_mm=500.0,
        )

        expected_missing = sum(year == 2019 for year in npk_lookup.looked_up_years)
        self.assertGreater(expected_missing, 0)
        self.assertEqual(result.npk_unavailable_or_unverified, expected_missing)
        self.assertEqual(result.scored_candidates, 45 - expected_missing)
        self.assertTrue(
            all(
                candidate.status == "npk_unavailable"
                for candidate in result.candidates
                if candidate.area_year == 2019
            )
        )

    def test_candidate_npk_from_different_year_is_not_used(self):
        npk_by_crop = self._verified_npk()
        npk_by_crop[self.crops[0]] = VerifiedNPKFeatures(
            N=1.0,
            P=2.0,
            K=3.0,
            crop_year=2020,
            source="owner-validated-test-source",
            provenance_verified=True,
        )

        result = self._run(verified_npk_by_crop=npk_by_crop)

        self.assertEqual(result.npk_unavailable_or_unverified, 1)
        self.assertEqual(result.candidates[0].status, "npk_unavailable")
        self.assertIn("same historical year", result.candidates[0].error or "")

    def test_fitted_category_validation_failures_are_recorded(self):
        self._write_dataset(unsupported_location=True)
        self.lookup = HistoricalFeatureLookupService(self.dataset_path)
        self.experiment = CandidateWiseCropExperiment(
            historical_lookup=self.lookup,
            model_service=self.model_service,
        )
        result = self._run(
            state="Unsupported State",
            verified_npk_by_crop=self._verified_npk(),
        )

        self.assertEqual(result.validation_failures, 45)
        self.assertEqual(result.scored_candidates, 0)
        self.assertIn("Unsupported state_names", result.candidates[0].error or "")

    def test_missing_prior_area_is_reported_and_not_scored(self):
        result = self._run(
            target_year=2018,
            verified_npk_by_crop=self._verified_npk(),
        )

        self.assertEqual(result.area_available, 0)
        self.assertEqual(result.missing_history, 45)
        self.assertEqual(result.scored_candidates, 0)
        self.assertTrue(
            all(candidate.status == "missing_history" for candidate in result.candidates)
        )

    def test_missing_area_for_one_candidate_does_not_block_others(self):
        with self.dataset_path.open(encoding="utf-8", newline="") as source:
            rows = list(csv.DictReader(source))
        rows = [row for row in rows if row["crop_names"] != self.crops[1]]
        with self.dataset_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        self.lookup = HistoricalFeatureLookupService(self.dataset_path)
        self.experiment = CandidateWiseCropExperiment(
            historical_lookup=self.lookup,
            model_service=self.model_service,
        )

        result = self._run(verified_npk_by_crop=self._verified_npk())

        self.assertEqual(result.total_candidates, 45)
        self.assertEqual(result.area_available, 44)
        self.assertEqual(result.missing_history, 1)
        self.assertEqual(result.scored_candidates, 44)
        self.assertEqual(result.candidates[1].crop, self.crops[1])
        self.assertEqual(result.candidates[1].status, "missing_history")
        self.assertIsNone(result.candidates[1].score)
        self.assertEqual(self.model_service._model.calls, 44)


if __name__ == "__main__":
    unittest.main(verbosity=2)
