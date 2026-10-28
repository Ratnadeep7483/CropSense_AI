# Weather location-resolution evidence package

This package prepares evidence inputs for the 625 CSV state–district pairs
without assigning LGD IDs, aliases, or coordinates. The operational weather
registry is unchanged by preparing the templates; unresolved entries remain
blocked before provider requests.

## Current work queue

The authoritative crop-location labels come from
`data/Copy of crop_recommendation_45_with_year_area.csv`. The current audit
contains 627 exact pairs: 2 existing reviewed pilot references and 625
unresolved pairs. Those 625 consist of 6 ambiguous state-qualified pairs and
619 unmatched pairs. The three repeated labels are BILASPUR (Chhattisgarh and
Himachal Pradesh), HAMIRPUR (Himachal Pradesh and Uttar Pradesh), and
PRATAPGARH (Rajasthan and Uttar Pradesh).

Generate or refresh the input files from the audit:

```powershell
.\.venv\Scripts\python.exe scripts\resolve_weather_locations.py --prepare-inputs
```

The output directory is `data/weather_location_resolution/`:

- `required_lgd_states.csv` lists the state labels appearing in the unresolved
  work queue. It is a checklist; fill its LGD state identifiers only from the
  official snapshot.
- `crop_to_lgd_crosswalk.csv` contains the exact CSV labels for all 625
  unresolved pairs. LGD identifiers and approvals are deliberately blank.
  The six known repeated-name pairs begin as `ambiguous`; other rows begin as
  `pending`.
- `lgd_district_snapshot_template.csv` has the normalized input header for
  official LGD records.
- `coordinate_evidence_template.csv` has the normalized input header for
  independently reviewed coordinate evidence.

Do not edit the crop labels in the queue. Keep the original downloaded LGD
file in the same evidence package (or controlled project storage) as received.
The normalized snapshot CSV is a working copy, not a substitute for the
original source export.

## Official LGD administrative snapshot

LGD is used to establish current administrative identity and codes, not
coordinates. The official portal says it is hosted and maintained by the
National Informatics Centre and that the contents are owned, updated, and
managed by Panchayats and State Panchayati Raj departments under the Ministry
of Panchayati Raj: <https://lgdirectory.gov.in/>.

The portal was inspected on 2026-10-20. Its home page exposes the
**Download Directory** page at
<https://lgdirectory.gov.in/downloadDirectory.do>. The page's report selector
includes **All Districts of India** and **All Districts of a State**; its
download format choices include `xls`. The separate **Districts** /
**LGD Codes of Districts** public directory is available at
<https://lgdirectory.gov.in/globalviewdistrictforcitizen.do> and supports
state-scoped district records. Use these as the procedure:

1. Open the official LGD home page and choose **Download Directory**.
2. Select **All Districts of India** (preferred to obtain one coherent
   current snapshot). If the full export is unavailable, download **All
   Districts of a State** for each state in `required_lgd_states.csv`; record
   each report selection and URL separately.
3. Select the spreadsheet (`xls`) download option. Preserve the downloaded
   file unchanged, its full source/report URL, and the retrieval date. Do not
   use a third-party mirror as the administrative source.
4. Confirm the export provides a state identifier/name and district
   identifier/name. Use the exact LGD IDs and names from the file; keep IDs as
   text in CSV so leading zeroes, if present, are not lost.
5. Normalize a working copy to UTF-8 CSV with the resolver's required fields:
   `state_lgd_code`, `district_lgd_code`, `source_record_id`, `state_name`,
   `district_name`, `source_url`, `source_downloaded_at`. Set
   `source_record_id` to the district LGD code from that source row, preserving
   it as text. For each record, `source_url` must identify the actual
   report/page used, and `source_downloaded_at` must be an ISO date or
   timestamp. The resolver requires unique state/district ID pairs and rejects
   absent IDs or provenance.
6. Compare state and district records against the exact crop pairs using both
   LGD state and district codes. Do not resolve a repeated district name using
   its name alone. A current LGD name that differs from a CSV label needs an
   evidence-backed alias or historical-rename review.

The public directory is dynamic, and the portal can change its export
controls. If the reported report type or file format is no longer available,
use the official district code directory and retain its exact URL, selected
state, and retrieval date; do not infer that another download is equivalent.
The downloaded snapshot, not this procedure text, is the evidence for each
LGD ID.

## Crosswalk and aliases

The resolver requires these crosswalk columns:

`crop_state`, `crop_district`, `state_lgd_code`, `district_lgd_code`,
`match_method`, `review_status`, `evidence_url`, `review_note`, `reviewed_at`,
`reviewed_by`.

For a `match_method` of `exact_name`, the normalized state and district names
must agree with the LGD record. For `reviewed_alias` or `historical_rename`,
provide an official state/district notification, government gazette, official
district history, or other primary government record explicitly connecting
the CSV label to the current LGD identity. Put the source URL in
`evidence_url` and explain the particular name/administrative transition in
`review_note`. Record an ISO review date and accountable reviewer. Similar
spelling, a shared district name, or a search-engine result alone is not
evidence of identity. Unresolved historical districts created by splits or
boundary changes should remain ambiguous unless the evidence identifies the
appropriate present-day administrative unit; do not map them to multiple new
districts or pick one arbitrarily.

## Headquarters coordinate evidence

No complete authoritative national dataset of district-headquarters
coordinates was verified during this work. LGD establishes administrative
identity but does not provide the HQ coordinate fields required here. Do not
use a district centroid as an HQ location, and do not treat a city gazetteer
entry, address geocode, Open-Meteo geocoding result, or generic map pin as a
verified district-HQ coordinate.

For each proposed reference point, obtain a source that explicitly identifies
the coordinate as the district headquarters: preferably a state or district
government GIS/administrative directory record keyed to the district, or an
official district administration publication that states the HQ coordinate.
The source record must distinguish the headquarters from district boundary
centroids, municipal centres, collectorate branches, and similarly named
places. If such a source cannot be obtained, leave the coordinate row empty
and the pair unresolved. An official district portal that gives only a
collectorate address is not, by itself, coordinate evidence.

The coordinate input fields are:

`state_lgd_code`, `district_lgd_code`, `latitude`, `longitude`,
`reference_place`, `reference_type`, `coordinate_source`,
`coordinate_source_url`, `coordinate_source_record`,
`verification_source_url`, `verification_status`, `verification_note`,
`verified_at`, `verified_by`.

Use `reference_type=district_headquarters` only when the source explicitly
supports that designation. The resolver does not promote
`official_boundary_centroid`; it is not a headquarters coordinate. City
centres and generic geocoder results are likewise not accepted as substitutes.
Include units (decimal degrees, WGS84) and axis order in `verification_note`.
The source record should identify its feature/row/record ID and quoted
designation. The verification URL should be independent confirming evidence,
not merely a repeated geocoder result. The resolver checks numeric coordinates,
finite values, geographic limits, and a broad India sanity envelope, but those
checks do not establish correctness or district identity.

## Candidate registry generation

After populating all three input CSVs, build a candidate registry and audit
report (the command does not replace the operational registry):

```powershell
.\.venv\Scripts\python.exe scripts\resolve_weather_locations.py `
  --lgd-snapshot data\weather_location_resolution\lgd_district_snapshot.csv `
  --crosswalk data\weather_location_resolution\crop_to_lgd_crosswalk.reviewed.csv `
  --coordinate-evidence data\weather_location_resolution\coordinate_evidence.reviewed.csv `
  --registry-output data\weather_location_registry.candidate.json `
  --audit-output data\weather_location_resolution_audit.candidate.json
```

Copy the templates to these completed filenames, populate them from the
official sources, and retain the original LGD spreadsheet alongside them. The
generator preserves the two existing Pune/Mysore pilot points. Only an
approved, state-qualified LGD mapping plus complete verified coordinate
evidence can add a new reference point. Inspect and review every candidate
record before any separately authorized operational registry update.

The working data files are templates; no source IDs or coordinates are
pre-filled. At this stage there are still **625 unresolved locations** and
weather requests for them remain blocked.
