# Merged LGD District Workbook Audit

**Audit date:** 2026-10-21  
**Scope:** Read-only review of `data/All_Districts_Merged.xlsx` and source material present in the project. No Excel file or application data was changed.

## Executive summary

The merged workbook contains one `Districts` sheet with 781 district records, 35 state/UT names, and nine columns. Internal integrity checks found no blank state names, English district names, state codes, district codes, or district versions; no duplicate state–district pairs; no repeated district codes; and no state-name/state-code conflicts.

Three English district names occur in more than one state: Bilaspur, Hamirpur, and Pratapgarh. These are state-qualified records, not evidence of incorrect assignments. They demonstrate why district names must not be used as identity keys without the state.

The workbook itself does **not** preserve a source URL, LGD download date, source filename, or source worksheet/row. Its `District Version` field is populated, but that is a district-level version value, not source-file version/provenance. No original state-wise Excel source files were located. A separate normalized Karnataka CSV snapshot is available; its 31 records match the workbook's 31 Karnataka rows on state code, district code, English district name, and district version. This limited comparison does not authenticate or verify the other 750 rows against their original sources.

**Conclusion:** The workbook is internally consistent based on the checks below, but its national source provenance remains unverified. Do not treat internal consistency as official source verification.

## Workbook structure and identifiers

| Sheet | Rows including header | Data records | Columns |
|---|---:|---:|---:|
| `Districts` | 782 | 781 | 9 |

| Column | Available information | Nonblank records |
|---|---|---:|
| `S. No.` | Sequence number | 781 |
| `State Name` | State/UT name | 781 |
| `State Code` | State identifier; 35 distinct values | 781 |
| `District Code` | District identifier; 781 distinct values | 781 |
| `District Version` | District version value; 20 distinct values | 781 |
| `District Name (In English)` | English district name | 781 |
| `District Name (In Local)` | Local-language district name | 746 |
| `Census 2001 Code` | Census identifier | 612 |
| `Census 2011 Code` | Census identifier | 759 |

The `State Code`, `District Code`, and `District Version` cells are stored as numeric Excel cells. Census code cells are stored as text. Keep identifiers as text when exporting or transforming data to avoid spreadsheet type coercion.

### Records by state/UT

| State/UT | Records | State/UT | Records |
|---|---:|---|---:|
| Andaman And Nicobar Islands | 3 | Andhra Pradesh | 28 |
| Arunachal Pradesh | 27 | Assam | 35 |
| Bihar | 38 | Chandigarh | 1 |
| Chhattisgarh | 33 | Delhi | 13 |
| Goa | 3 | Gujarat | 34 |
| Haryana | 23 | Himachal Pradesh | 12 |
| Jammu And Kashmir | 20 | Jharkhand | 24 |
| Karnataka | 31 | Kerala | 14 |
| Ladakh | 2 | Lakshadweep | 1 |
| Madhya Pradesh | 55 | Maharashtra | 36 |
| Manipur | 16 | Meghalaya | 12 |
| Mizoram | 11 | Nagaland | 17 |
| Odisha | 30 | Puducherry | 2 |
| Punjab | 23 | Rajasthan | 41 |
| Sikkim | 6 | Tamil Nadu | 38 |
| Telangana | 33 | Tripura | 8 |
| Uttar Pradesh | 75 | Uttarakhand | 13 |
| West Bengal | 23 | **Total** | **781** |

## Integrity checks

| Check | Result |
|---|---|
| Blank state names | 0 |
| Blank English district names | 0 |
| Blank state codes | 0 |
| Blank district codes | 0 |
| Blank district versions | 0 |
| Duplicate state–English-district pairs | 0 |
| Duplicate state-qualified district codes | 0 |
| Duplicate district codes across the workbook | 0 |
| State names mapped to multiple state codes | 0 |
| State codes mapped to multiple state names | 0 |

Optional/auxiliary name and census columns do contain blanks: 35 local-language district names, 169 Census 2001 codes, and 22 Census 2011 codes. Examples include the missing local name for Anjaw (worksheet row 48), missing Census 2001 code for North And Middle Andaman (row 4), and missing Census 2011 code for Markapuram (row 31). These are column-completeness findings; this audit did not establish whether those fields are required or validate their values against the census authorities.

### Repeated district names across states

The following normalized English names appear in two different states:

| District name | State/UTs |
|---|---|
| Bilaspur | Chhattisgarh; Himachal Pradesh |
| Hamirpur | Himachal Pradesh; Uttar Pradesh |
| Pratapgarh | Rajasthan; Uttar Pradesh |

No duplicate state-qualified record was found for these names. Retain both the state and district identifiers in any downstream matching.

## Comparison with local source material

### Files found

- `data/All_Districts_Merged.xlsx` — the workbook under review.
- `data/weather_location_resolution/lgd_district_snapshot_karnataka.csv` — a normalized Karnataka working snapshot. It records source metadata including the source filename `KARNATAKA 2.xlsx`, the URL `https://lgdirectory.gov.in/downloadDirectory.do`, download date `2026-10-20`, report-generated time `2026-10-20 23:39`, source worksheet `Report`, and source worksheet row/record references.
- `data/weather_location_resolution/merged_lgd_workbook_audit.json` — a separate audit artifact describing the workbook and comparisons. This is not an original LGD export and is not a substitute for source files.

### Original state-wise files not located

No state-wise `.xls`, `.xlsx`, or `.xlsm` source workbook was found in the project apart from the merged workbook itself. The only original workbook filename named in the available normalized snapshot is `KARNATAKA 2.xlsx`; that file was not located. The available project material does not identify the filenames of the other state-wise workbooks, so they cannot be enumerated individually from local evidence.

### Direct comparison possible

The Karnataka snapshot contains 31 records, matching the merged workbook's 31 Karnataka records. All 31 state-code/district-code keys are present in both files, with no records unique to either side. There are **zero differences** in state code, district code, normalized English district name, or district version.

This is a comparison against a normalized CSV snapshot—not the original `KARNATAKA 2.xlsx`. Its row-level metadata provides traceability claims, but the raw workbook was unavailable for independent verification. No equivalent state-level snapshot or original source workbook was located for the other states/UTs.

## Provenance and version preservation

| Item | In merged workbook? | Finding |
|---|---|---|
| Source URL | No | Not present in the sheet columns or workbook core properties. |
| LGD download date | No | The workbook's created/modified timestamp is file metadata, not evidence of the LGD retrieval date. |
| Source filename and source worksheet/row | No | Not preserved in the merged sheet. They are present for the Karnataka records in the separate normalized CSV only. |
| LGD district code | Yes | `District Code` is populated on all 781 rows. |
| LGD state code | Yes | `State Code` is populated on all 781 rows. |
| District version | Yes | `District Version` is populated on all 781 rows. It does not by itself identify the source file's version or export date. |
| Original export/report version or complete record history | No | No source export is available locally to establish this. |

The workbook's core properties identify `openpyxl` as creator and give created/modified timestamps of `2026-10-20T19:02:43Z`. Those properties describe the workbook file and do not authenticate its LGD source.

## Verified findings versus unverified information

**Verified from the local workbook or project files**

- Sheet names, dimensions, headers, row counts, values, blank counts, and internal duplicate/state-code consistency described above.
- The 31-row Karnataka comparison against the local normalized CSV snapshot.
- The source URL, date, report-generated time, and `KARNATAKA 2.xlsx` source-filename claim recorded in that CSV.
- No separate state-wise Excel workbook was found in the project search.

**Not verified**

- Whether the merged workbook is a complete or current official LGD export.
- Whether each record matches the original state-wise file or an official LGD publication.
- Whether the source filename, source date, and report timestamp in the normalized Karnataka CSV accurately describe the unavailable original.
- Whether blank census/local-language values are acceptable for their intended use.
- Whether district names or codes are correct against the LGD authority; internal consistency alone cannot establish that.

## Recommended corrections and next step

1. Obtain the original state-wise exports used to build the merged workbook, especially the missing `KARNATAKA 2.xlsx`, or retrieve a fresh official all-district export. Preserve each source unchanged.
2. Record, per source and preferably per row, the official source URL, download/retrieval date, report-generated date, filename, worksheet, source-row reference, and a file checksum in a companion provenance manifest.
3. Reconcile the merged records to those originals using state code and district code, then verify district name and district version. Record additions, omissions, duplicates, and changed versions explicitly.
4. Keep LGD identifiers as text in future exports and transformations. Decide from the intended requirements whether the blank local-language and census fields need correction; do not fill them by inference.
5. Until the source reconciliation is complete, treat the workbook as internally consistent but not source-verified. Do not use this audit to approve district aliases or infer coordinates.

**Simple-language summary:** The workbook has 781 district rows and looks consistent within itself: required names and IDs are filled, and no duplicate district records were detected. The local Karnataka snapshot agrees with the Karnataka portion, but the original state-wise Excel files are missing, including the named Karnataka source file. The next step is to recover or re-download the official original exports and verify every merged record while preserving source links and dates.
