#!/usr/bin/env python3
"""Offline tests for the reviewed weather-location resolution workflow."""

import csv
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

from openpyxl import Workbook

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from scripts.resolve_weather_locations import (  # noqa: E402
    audit_current_registry,
    audit_lgd_reports,
    build_reviewed_registry,
    _parse_lgd_report,
    write_input_templates,
)


class WeatherLocationResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.crop = self.root / "crop.csv"
        self.lgd = self.root / "lgd.csv"
        self.crosswalk = self.root / "crosswalk.csv"
        self.coordinates = self.root / "coordinates.csv"

        self._write(
            self.crop,
            ["state_names", "district_names"],
            [
                ["Example State", "SAMPLE"],
                ["Other State", "SAMPLE"],
                ["Example State", "UNMATCHED"],
                ["Example State", "ALIAS"],
            ],
        )
        self._write(
            self.lgd,
            [
                "state_lgd_code",
                "district_lgd_code",
                "district_version",
                "source_record_id",
                "state_name",
                "district_name",
                "source_url",
                "source_downloaded_at",
                "source_report_generated_at",
                "source_file",
                "source_worksheet",
                "source_worksheet_row",
            ],
            [
                ["10", "101", "2", "101", "Example State", "Sample", "https://lgdirectory.gov.in/", "2026-06-01", "2026-06-01 10:00", "test.xlsx", "Report", "6"],
                ["10", "102", "4", "102", "Example State", "Current Name", "https://lgdirectory.gov.in/", "2026-06-01", "2026-06-01 10:00", "test.xlsx", "Report", "7"],
                ["20", "201", "1", "201", "Other State", "Sample", "https://lgdirectory.gov.in/", "2026-06-01", "2026-06-01 10:00", "test.xlsx", "Report", "8"],
            ],
        )
        self._write(
            self.crosswalk,
            [
                "crop_state",
                "crop_district",
                "state_lgd_code",
                "district_lgd_code",
                "official_lgd_district_name",
                "district_version",
                "source_record_id",
                "match_method",
                "review_status",
                "evidence_url",
                "review_note",
                "reviewed_at",
                "reviewed_by",
            ],
            [
                ["Example State", "SAMPLE", "10", "101", "Sample", "2", "101", "exact_name", "approved", "", "Exact state and district identity.", "2026-06-01", "reviewer"],
                ["Example State", "ALIAS", "10", "102", "Current Name", "4", "102", "historical_rename", "approved", "https://example.gov/district-history", "Official district history maps the legacy CSV label.", "2026-06-01", "reviewer"],
            ],
        )
        self._write(
            self.coordinates,
            [
                "state_lgd_code",
                "district_lgd_code",
                "latitude",
                "longitude",
                "reference_place",
                "reference_type",
                "coordinate_source",
                "coordinate_source_url",
                "coordinate_source_record",
                "verification_source_url",
                "verification_status",
                "verification_note",
                "verified_at",
                "verified_by",
            ],
            [
                [
                    "10",
                    "101",
                    "20",
                    "75",
                    "Sample district headquarters",
                    "district_headquarters",
                    "Official district site",
                    "https://example.gov/map",
                    "HQ marker record",
                    "https://example.gov/about",
                    "verified",
                    "HQ reference checked against the official district site.",
                    "2026-06-01",
                    "reviewer",
                ],
                [
                    "10",
                    "102",
                    "21",
                    "76",
                    "Current district headquarters",
                    "district_headquarters",
                    "Official district site",
                    "https://example.gov/map",
                    "HQ marker record",
                    "https://example.gov/about",
                    "verified",
                    "HQ reference checked against the official district site.",
                    "2026-06-01",
                    "reviewer",
                ],
            ],
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _write(path: Path, fields: list[str], rows: list[list[str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.writer(target)
            writer.writerow(fields)
            writer.writerows(rows)

    def test_state_qualified_crosswalk_verifies_and_preserves_csv_label(self) -> None:
        registry, audit = build_reviewed_registry(
            self.lgd, self.crosswalk, self.coordinates, self.crop
        )
        row = next(
            entry for entry in registry["entries"]
            if entry["state"] == "Example State" and entry["district"] == "SAMPLE"
        )
        self.assertEqual(row["coordinate_status"], "verified_reference_point")
        self.assertEqual(row["district"], "SAMPLE")
        self.assertEqual(row["administrative_identifier"], "101")
        self.assertEqual(row["official_lgd_district_name"], "Sample")
        self.assertEqual(row["district_version"], "2")
        self.assertEqual(audit["counts"]["verified"], 2)

    def test_unmapped_repeated_name_is_ambiguous_and_single_name_is_unmatched(self) -> None:
        _, audit = build_reviewed_registry(
            self.lgd, self.crosswalk, self.coordinates, self.crop
        )
        statuses = {(row["state"], row["district"]): row["status"] for row in audit["records"]}
        self.assertEqual(statuses[("Other State", "SAMPLE")], "ambiguous")
        self.assertEqual(statuses[("Example State", "UNMATCHED")], "unmatched")

    def test_alias_requires_review_evidence(self) -> None:
        rows = self._read_rows(self.crosswalk)
        rows[1]["evidence_url"] = ""
        self._rewrite_rows(self.crosswalk, rows)
        _, audit = build_reviewed_registry(
            self.lgd, self.crosswalk, self.coordinates, self.crop
        )
        alias = next(row for row in audit["records"] if row["district"] == "ALIAS")
        self.assertEqual(alias["status"], "suspicious")

    def test_crosswalk_name_version_and_source_record_must_match_snapshot(self) -> None:
        rows = self._read_rows(self.crosswalk)
        rows[0]["district_version"] = "9"
        self._rewrite_rows(self.crosswalk, rows)
        _, audit = build_reviewed_registry(
            self.lgd, self.crosswalk, self.coordinates, self.crop
        )
        sample = next(row for row in audit["records"] if row["district"] == "SAMPLE")
        self.assertEqual(sample["status"], "suspicious")
        self.assertIn("district version", sample["reason"])

    def test_invalid_or_non_indian_coordinate_is_suspicious(self) -> None:
        rows = self._read_rows(self.coordinates)
        for latitude, longitude in (("20", "181"), ("0", "0")):
            with self.subTest(latitude=latitude, longitude=longitude):
                rows[0]["latitude"] = latitude
                rows[0]["longitude"] = longitude
                self._rewrite_rows(self.coordinates, rows)
                _, audit = build_reviewed_registry(
                    self.lgd, self.crosswalk, self.coordinates, self.crop
                )
                sample = next(
                    row for row in audit["records"] if row["district"] == "SAMPLE"
                )
                self.assertEqual(sample["status"], "suspicious")

    def test_boundary_centroid_is_not_accepted_as_headquarters(self) -> None:
        rows = self._read_rows(self.coordinates)
        rows[0]["reference_type"] = "official_boundary_centroid"
        self._rewrite_rows(self.coordinates, rows)
        _, audit = build_reviewed_registry(
            self.lgd, self.crosswalk, self.coordinates, self.crop
        )
        sample = next(row for row in audit["records"] if row["district"] == "SAMPLE")
        self.assertEqual(sample["status"], "suspicious")
        self.assertIn("not interchangeable", sample["reason"])

    def test_conflicting_crosswalk_rows_are_suspicious(self) -> None:
        with self.crosswalk.open("a", encoding="utf-8", newline="") as target:
            writer = csv.writer(target)
            writer.writerow(
                ["Example State", "SAMPLE", "10", "102", "reviewed_alias", "approved", "https://example.gov/x", "conflict"]
            )
        _, audit = build_reviewed_registry(
            self.lgd, self.crosswalk, self.coordinates, self.crop
        )
        sample = next(row for row in audit["records"] if row["district"] == "SAMPLE")
        self.assertEqual(sample["status"], "suspicious")

    def test_candidate_generation_preserves_existing_reviewed_pilot_reference(self) -> None:
        current_registry = self.root / "current_registry.json"
        current_registry.write_text(
            json.dumps(
                {
                    "entries": [
                        {
                            "state": "Example State",
                            "district": "UNMATCHED",
                            "coordinate_status": "verified_reference_point",
                            "latitude": 20,
                            "longitude": 75,
                            "coordinate_source": "Reviewed pilot source",
                            "coordinate_source_url": "https://example.gov/coordinates",
                            "coordinate_source_record": "Pilot record",
                            "verification_source_url": "https://example.gov/district",
                            "verification_note": "Existing pilot reviewed record.",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        registry, audit = build_reviewed_registry(
            self.lgd,
            self.crosswalk,
            self.coordinates,
            self.crop,
            current_registry,
        )
        preserved = next(
            row for row in registry["entries"] if row["district"] == "UNMATCHED"
        )
        self.assertEqual(preserved["coordinate_status"], "verified_reference_point")
        self.assertEqual(preserved["coordinate_source_record"], "Pilot record")
        newly_reviewed = next(
            row for row in registry["entries"] if row["district"] == "SAMPLE"
        )
        self.assertEqual(
            newly_reviewed["coordinate_status"],
            "verified_reference_point",
        )
        self.assertEqual(newly_reviewed["latitude"], 20.0)
        self.assertEqual(newly_reviewed["longitude"], 75.0)
        self.assertEqual(
            newly_reviewed["administrative_identifier"],
            "101",
        )
        self.assertEqual(
            next(row for row in audit["records"] if row["district"] == "UNMATCHED")[
                "status"
            ],
            "verified",
        )
        self.assertEqual(
            next(row for row in audit["records"] if row["district"] == "SAMPLE")[
                "status"
            ],
            "verified",
        )

    def test_current_audit_counts_existing_coverage_without_promoting(self) -> None:
        report = audit_current_registry()
        self.assertEqual(report["counts"]["supported_pairs"], 627)
        self.assertEqual(report["counts"]["state_count"], 30)
        self.assertEqual(report["counts"]["district_label_count"], 624)
        self.assertEqual(report["counts"]["verified"], 2)
        self.assertEqual(report["counts"]["ambiguous"], 6)
        self.assertEqual(report["counts"]["unmatched"], 619)
        self.assertEqual(report["counts"]["suspicious"], 0)
        self.assertEqual(report["counts"]["source_missing_values"], 0)
        self.assertEqual(report["counts"]["normalized_spelling_conflicts"], 0)
        self.assertEqual(len(report["records"]), 627)

    def test_prepared_templates_cover_only_unresolved_pairs_without_fabricating_ids(self) -> None:
        paths = write_input_templates(self.root / "templates")
        crosswalk = self._read_rows(paths["crosswalk"])
        states = self._read_rows(paths["required_states"])
        lgd = self._read_rows(paths["lgd_snapshot"])
        coordinates = self._read_rows(paths["coordinate_evidence"])
        report = audit_current_registry()
        unresolved = {
            (row["state"], row["district"])
            for row in report["records"]
            if row["status"] != "verified"
        }
        self.assertEqual(len(crosswalk), 625)
        self.assertEqual(
            {(row["crop_state"], row["crop_district"]) for row in crosswalk},
            unresolved,
        )
        self.assertEqual(len(states), 30)
        self.assertEqual(lgd, [])
        self.assertEqual(coordinates, [])
        self.assertTrue(
            all(
                not row["state_lgd_code"] and not row["district_lgd_code"]
                for row in crosswalk
            )
        )
        self.assertEqual(
            sum(row["review_status"] == "ambiguous" for row in crosswalk),
            6,
        )

    def test_template_refresh_preserves_existing_reviewed_crosswalk_values(self) -> None:
        directory = self.root / "preserve"
        directory.mkdir()
        template = directory / "crop_to_lgd_crosswalk.csv"
        fields = [
            "crop_state",
            "crop_district",
            "state_lgd_code",
            "district_lgd_code",
            "official_lgd_district_name",
            "district_version",
            "source_record_id",
            "match_method",
            "review_status",
            "evidence_url",
            "review_note",
            "reviewed_at",
            "reviewed_by",
        ]
        self._write(
            template,
            fields,
            [
                [
                    "Andhra Pradesh",
                    "ANANTAPUR",
                    "28",
                    "401",
                    "Anantapur",
                    "1",
                    "row-1",
                    "exact_name",
                    "approved",
                    "https://lgdirectory.gov.in/",
                    "reviewed exact identity",
                    "2026-10-20",
                    "reviewer",
                ]
            ],
        )
        write_input_templates(directory)
        preserved = next(
            row
            for row in self._read_rows(template)
            if row["crop_state"] == "Andhra Pradesh"
            and row["crop_district"] == "ANANTAPUR"
        )
        self.assertEqual(preserved["district_lgd_code"], "401")
        self.assertEqual(preserved["review_status"], "approved")

    def _write_lgd_xlsx(self, path: Path, state: str = "Example State") -> None:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Report"
        sheet["A1"] = f"All Districts of {state} (State Code:10) State"
        for row in (
            ["S. No.", "District Code", "District Version", "District Name", "District Name"],
            ["", "", "", "(In English)", "(In Local)"],
            [1, 101, 2, "Sample", "sample-local"],
            [2, 102, 4, "Current Name", "current-local"],
            ["Jun 1, 2026, 10:00 AM"],
        ):
            sheet.append(row)
        workbook.save(path)

    def test_lgd_batch_imports_state_identified_xlsx_and_audits_missing_state(self) -> None:
        reports = self.root / "reports"
        output = self.root / "snapshots"
        reports.mkdir()
        output.mkdir()
        self._write_lgd_xlsx(reports / "example.xlsx")
        crosswalk_rows = self._read_rows(self.crosswalk)
        crosswalk_rows[1]["source_record_id"] = "example.xlsx:Report!B5:D5"
        self._rewrite_rows(self.crosswalk, crosswalk_rows)
        result = audit_lgd_reports(
            reports,
            output,
            self.crop,
            self.crosswalk,
        )
        self.assertEqual(result["counts"]["processed_state_count"], 1)
        self.assertEqual(result["counts"]["missing_report_count"], 1)
        self.assertEqual(result["missing_reports"], ["Other State"])
        state_audit = result["per_state"]["Example State"]
        self.assertEqual(state_audit["report_status"], "processed")
        self.assertEqual(
            [row["crop_district"] for row in state_audit["direct_matches"]],
            ["SAMPLE"],
        )
        self.assertEqual(
            [row["crop_district"] for row in state_audit["reviewed_aliases"]],
            ["ALIAS"],
        )
        self.assertEqual(state_audit["unresolved_names"], ["UNMATCHED"])
        imported = self._read_rows(output / "lgd_district_snapshot_example_state.csv")
        self.assertEqual(len(imported), 2)
        self.assertEqual(imported[0]["state_lgd_code"], "10")
        self.assertEqual(imported[0]["source_worksheet"], "Report")
        self.assertEqual(imported[0]["source_report_generated_at"], "2026-06-01 10:00")

    def test_lgd_batch_rejects_report_for_unexpected_state(self) -> None:
        reports = self.root / "reports"
        output = self.root / "snapshots"
        reports.mkdir()
        output.mkdir()
        self._write_lgd_xlsx(reports / "wrong-state.xlsx", "Another State")
        result = audit_lgd_reports(
            reports,
            output,
            self.crop,
            self.crosswalk,
        )
        self.assertEqual(result["counts"]["processed_state_count"], 0)
        self.assertEqual(result["counts"]["missing_report_count"], 2)
        self.assertEqual(len(result["rejected_reports"]), 1)
        self.assertIn("not an exact crop CSV state label", result["rejected_reports"][0]["reason"])
        self.assertEqual(list(output.glob("lgd_district_snapshot_*.csv")), [])

    def test_xls_report_reader_uses_xlrd_for_legacy_workbooks(self) -> None:
        report = self.root / "legacy.xls"
        report.write_bytes(b"mock xls")

        class Sheet:
            name = "Report"
            rows = [
                ["All Districts of Example State (State Code:10) State"],
                ["", "District Code", "District Version", "District Name"],
                ["", "", "", "(In English)"],
                ["", 101, 2, "Sample"],
                ["Jun 1, 2026, 10:00 AM"],
            ]
            nrows = len(rows)

            def row_values(self, index: int) -> list[object]:
                return self.rows[index]

        class Book:
            def sheets(self) -> list[Sheet]:
                return [Sheet()]

            def release_resources(self) -> None:
                pass

        xlrd_stub = types.ModuleType("xlrd")
        xlrd_stub.open_workbook = lambda *args, **kwargs: Book()  # type: ignore[attr-defined]
        previous = sys.modules.get("xlrd")
        sys.modules["xlrd"] = xlrd_stub
        try:
            state, code, records = _parse_lgd_report(report, "2026-06-01")
        finally:
            if previous is None:
                del sys.modules["xlrd"]
            else:
                sys.modules["xlrd"] = previous
        self.assertEqual((state, code), ("Example State", "10"))
        self.assertEqual(records[0]["district_lgd_code"], "101")
        self.assertEqual(records[0]["district_name"], "Sample")

    def test_lgd_batch_audit_flags_duplicate_crosswalk_rows(self) -> None:
        reports = self.root / "reports"
        output = self.root / "snapshots"
        reports.mkdir()
        output.mkdir()
        self._write_lgd_xlsx(reports / "example.xlsx")
        crosswalk_rows = self._read_rows(self.crosswalk)
        crosswalk_rows.append(dict(crosswalk_rows[0]))
        self._rewrite_rows(self.crosswalk, crosswalk_rows)
        result = audit_lgd_reports(
            reports,
            output,
            self.crop,
            self.crosswalk,
        )
        state_audit = result["per_state"]["Example State"]
        self.assertEqual(state_audit["report_status"], "conflicting_records")
        self.assertEqual(len(state_audit["direct_matches"]), 1)
        self.assertTrue(
            any("Multiple crosswalk records" in conflict
                for conflict in state_audit["conflicting_records"])
        )

    def test_current_audit_flags_duplicate_verified_records(self) -> None:
        from scripts.resolve_weather_locations import CURRENT_REGISTRY_PATH
        import json

        payload = json.loads(CURRENT_REGISTRY_PATH.read_text(encoding="utf-8"))
        pune = next(
            row for row in payload["entries"]
            if row["state"] == "Maharashtra" and row["district"] == "PUNE"
        )
        payload["entries"].append(dict(pune))
        with (self.root / "registry.json").open("w", encoding="utf-8") as target:
            json.dump(payload, target)
        report = audit_current_registry(
            registry_path=self.root / "registry.json"
        )
        self.assertEqual(report["counts"]["suspicious"], 1)

    @staticmethod
    def _read_rows(path: Path) -> list[dict[str, str]]:
        with path.open(encoding="utf-8", newline="") as source:
            return list(csv.DictReader(source))

    @staticmethod
    def _rewrite_rows(path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main(verbosity=2)
