# Historical weather expansion: registry and seasonal pilot

## Status

The endpoint `GET /api/weather/kharif-historical` remains backward compatible
and accepts exact CSV fields `state_names` and `district_names`. Add the
optional exact `season` query parameter, defaulting to `Kharif`, to retrieve
one of the six historical seasonal aggregates. Responses are explicitly
labeled **Historical seasonal average — not a forecast**. Results are not
connected to crop prediction.

The registry is derived from
`data/Copy of crop_recommendation_45_with_year_area.csv`: **627 exact
state–district pairs across 30 states**. The registry is
`data/weather_location_registry.json`, reproducibly built by
`scripts/build_weather_location_registry.py`.

- Verified city reference points: **2** — Maharashtra / PUNE and Karnataka /
  MYSORE.
- Unresolved pairs: **625**. Their coordinates are null; requests return
  HTTP 409 and do not call a geocoder or weather provider.
- BILASPUR, HAMIRPUR, and PRATAPGARH occur under multiple states. All six
  corresponding entries are marked ambiguous and unresolved.
- Registry entries retain exact CSV labels, coordinate status, coordinates,
  source URLs/record, verification note, and cross-state ambiguity.

The two retained pilot coordinates came from state-specific Open-Meteo
Geocoding API result records and were checked against the respective
district-headquarters contact pages. They identify city reference points, not
district centroids. No complete authoritative administrative coordinate
dataset was available in the project, so no coordinates were invented for
the remaining pairs. A full 627-pair coordinate claim is not made.

## District-resolution source and review workflow

The Local Government Directory (LGD, <https://lgdirectory.gov.in/>) is the
selected source for **administrative identity**, not for coordinates. Its
official site says it is hosted and maintained by the National Informatics
Centre and that its contents are owned, updated, and managed by Panchayats and
State Panchayati Raj departments under the Ministry of Panchayati Raj. LGD
state and district codes are the required identity keys for future matching.
An LGD snapshot must be exported or obtained from its official district
directory interface and saved with its source URL and retrieval date.

No complete, authoritative national dataset of verified district-HQ
coordinates was confirmed during this work. The inspected NGA Geographic
Names Server India package is not sufficient: it had 309 populated records,
only five feature-code families (including generic populated places), and
state administrative codes for only two states; its entries do not establish
district identity or headquarters status. It is not used to populate the
registry. The Open-Meteo geocoder is retained only for the two already-reviewed
pilot references, not treated as an administrative coordinate authority.

The offline resolver at `scripts/resolve_weather_locations.py` implements a
strict input/review contract:

1. An LGD snapshot contains `state_lgd_code`, `district_lgd_code`,
   `source_record_id`, official state/district names, `source_url`, and
   `source_downloaded_at`. Duplicate district IDs or missing provenance are
   rejected as suspicious.
2. A crosswalk explicitly maps the exact CSV state/district pair to both LGD
   codes. `exact_name` must agree with the LGD names after case/whitespace
   normalization. `reviewed_alias` and `historical_rename` require an evidence
   URL, review note, reviewer, and ISO review date. The original CSV labels
   remain the registry/API labels.
3. Coordinate evidence is keyed by both LGD codes and records coordinates,
   reference place/type, source URL and record, independent verification URL
   and note, ISO review date, and reviewer. Coordinates must fall within
   geographic ranges and a broad India sanity envelope. Only a source-verified
   district headquarters coordinate may be promoted. A city point, district
   centroid, or generic geocoder result is not interchangeable with an HQ.
4. Conflicting mappings/evidence, missing IDs, unsupported match methods,
   invalid coordinates, and unsubstantiated aliases are marked suspicious.
   Repeated labels without a state-qualified mapping are ambiguous; absent
   reviewed evidence is unmatched. Only a fully reviewed record receives
   `verified_reference_point`.
5. The command writes a candidate registry and an audit report to explicit
   output paths. It does not overwrite the operational registry by default.
   The weather service continues to reject unresolved entries before making
   any provider request.

The input CSV column names are enforced by the resolver:

- LGD snapshot: `state_lgd_code`, `district_lgd_code`, `source_record_id`,
  `state_name`, `district_name`, `source_url`, `source_downloaded_at`.
- Crosswalk: `crop_state`, `crop_district`, `state_lgd_code`,
  `district_lgd_code`, `match_method`, `review_status`, `evidence_url`,
  `review_note`, `reviewed_at`, `reviewed_by`.
- Coordinate evidence: `state_lgd_code`, `district_lgd_code`, `latitude`,
  `longitude`, `reference_place`, `reference_type`, `coordinate_source`,
  `coordinate_source_url`, `coordinate_source_record`,
  `verification_source_url`, `verification_status`, `verification_note`,
  `verified_at`, `verified_by`.

For `reference_type`, only `district_headquarters` is accepted for promotion.
`official_boundary_centroid` and city or generic geocoder points are rejected
for this HQ registry. This is a human-reviewed evidence workflow, not an
automatic geocoder.

Example after obtaining the source files:

```powershell
.\.venv\Scripts\python.exe scripts\resolve_weather_locations.py `
  --lgd-snapshot data\weather_location_resolution\lgd_districts.csv `
  --crosswalk data\weather_location_resolution\crop_to_lgd_crosswalk.csv `
  --coordinate-evidence data\weather_location_resolution\coordinate_evidence.csv `
  --registry-output data\weather_location_registry.candidate.json `
  --audit-output data\weather_location_resolution_audit.candidate.json
```

The current audit is saved as
`data/weather_location_resolution_audit.json`. It records all exact CSV pairs,
the matching policy, counts, examples, and source-quality checks. Current
findings: **627** supported pairs (30 states; 624 distinct district labels),
**2 verified** existing pilot references, **6 ambiguous** pairs (the two
state-qualified occurrences each of BILASPUR, HAMIRPUR, and PRATAPGARH),
**619 unmatched**, and **0 suspicious** current registry records. The CSV has
no missing/blank state or district values and no case/whitespace-normalized
spelling collisions. These checks do not imply that the 625 unresolved pairs
have been matched to current LGD identities. District name aliases and
administrative reorganizations remain unreviewed.

## Season definitions

CSV/model categories, preserving exact spelling and capitalization:
`Autumn`, `Kharif`, `Rabi`, `Summer`, `Whole Year`, `Winter`.

No verified month-to-season mapping or location-specific crop calendar exists
in the project. The pilot therefore distinguishes the one user-defined
window from explicitly proposed windows:

| Exact category | Inclusive months | Status | Season year interpretation |
|---|---|---|---|
| Autumn | September–November | Proposed | Calendar year containing September |
| Kharif | June–October | User-defined for this pilot | Calendar year containing June |
| Rabi | October–March | Proposed | October start year; ends in March of following year |
| Summer | March–June | Proposed | Calendar year containing March |
| Whole Year | January–December | Proposed | Calendar year |
| Winter | December–February | Proposed | December start year; ends in February of following year |

These windows are pilot definitions, not authoritative agricultural
recommendations or recovered model-training rules. Windows are evaluated
independently. They intentionally overlap; no month is assigned a single
exclusive season. Each response includes definition status and overlapping
categories. The UI's manual season selection is unchanged.

The 2010–2019 reference period is defined by each season's start year. Rabi
2019 and Winter 2019 therefore extend into 2020. Whole Year includes leap day
in 2012. Requested archive coverage runs from 2010-01-01 through 2020-03-31
to encompass every proposed window.

## Provider and aggregation

- Source: [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- Model: ERA5 (`models=era5`), consistently specified for every request.
- Variables: hourly `temperature_2m` (°C) and `relative_humidity_2m` (%).
- Time zone: UTC.
- Mean: arithmetic mean of valid hourly values for a given season over the
  ten season-start years 2010–2019. Null and non-finite values, temperatures
  outside −90 to 60 °C, and relative humidity outside 0–100% are excluded.
- Coverage: each variable reports expected, valid, missing, and percent
  hourly values, plus incomplete season count. Each season-start year reports
  its date bounds, expected/valid counts, and completeness. Absent timestamps
  count as missing; partial means are returned with their actual coverage.
- If a variable has no valid data for the full requested period, the endpoint
  returns HTTP 503. Provider errors return 502; provider timeouts return 504.
  Unknown registry pairs return 404; known unresolved pairs return 409.

Every result includes requested reference coordinates, provider-snapped grid
coordinates and elevation, source and record provenance, model, dates, units,
method, overall/per-year coverage, and cache metadata.

## Cache and batch generation

On the first request for a verified location, the service makes one archive
request for the complete 2010-01-01–2020-03-31 UTC window and calculates all
six season aggregates. The resulting summaries are written atomically to
`data/weather_cache/`, keyed by exact state/district, coordinates, model,
date period, and cache schema version. The directory is git-ignored.

Cache entries are reused for **30 days**; `--refresh` forces replacement.
This avoids refetching identical history once the location cache exists.
The route coalesces concurrent misses inside one backend process. A multi-
worker deployment can race on its first simultaneous miss; atomic replacement
protects cache-file integrity, but a shared distributed lock is not
implemented.

Optional sequential batch generation is explicit and does not run in tests:

```powershell
.\.venv\Scripts\python.exe scripts\generate_historical_weather_cache.py --all-verified
.\.venv\Scripts\python.exe scripts\generate_historical_weather_cache.py --state Maharashtra --district PUNE --refresh
```

The batch only requests locations already marked verified; it never calls a
geocoder. Current registry size means the all-verified operation is two
requests at most, not a run against all 627 names. As additional locations are
reviewed and added, each new uncached location requires one archive request.

## Pilot samples and remaining blockers

Live historical ERA5 samples were validated at the Pune reference point for
all six categories. Each variable had complete hourly coverage in every
season-start year:

| Season | Mean 2 m temperature | Mean 2 m relative humidity | Valid / expected hourly values per variable |
|---|---:|---:|---:|
| Autumn | 24.5091 °C | 76.3967% | 21,840 / 21,840 (100%) |
| Kharif | 24.9638 °C | 85.5582% | 36,720 / 36,720 (100%) |
| Rabi | 23.6352 °C | 61.4944% | 43,752 / 43,752 (100%) |
| Summer | 27.5652 °C | 63.3707% | 29,280 / 29,280 (100%) |
| Whole Year | 24.9374 °C | 69.9460% | 87,648 / 87,648 (100%) |
| Winter | 22.1824 °C | 58.6056% | 21,672 / 21,672 (100%) |

The Mysore Kharif sample is 24.1345 °C / 79.5757% RH, with 36,720 / 36,720
hours (100%) for each variable. These are historical seasonal averages at
city/grid reference points, not forecasts or district-wide summaries. Each
request checks provider data/coverage; no live mass fetch was performed for
this expansion.

The training CSV's temperature/humidity provenance and temporal meaning
remain unknown. The proposed season windows, city reference points, and ERA5
averages have not been validated as semantically equivalent to the model
features. Weather values remain disconnected from crop prediction.

## Validation

Run tests without provider access:

```powershell
.\.venv\Scripts\python.exe scripts\test_historical_weather.py
.\.venv\Scripts\python.exe scripts\test_crop_weather_contract.py
```

Use only explicitly selected locations for live smoke tests; do not make
hundreds of archive requests as part of unit or regression test runs.

At the time of this implementation, the mocked historical-weather suite had
17 tests passing, the existing crop weather contract had 5 passing tests, the
crop API/model smoke checks passed, and the soil API passed with a real image.
Two explicitly selected live Kharif requests (PUNE and MYSORE) returned full
36,720/36,720 coverage for both variables. No frontend source changed.
