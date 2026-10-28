# Historical Kharif weather pilot

> This document records the original Kharif sample and its two verified
> locations. The current six-season registry, proposed windows, cache policy,
> and unresolved-pair counts are documented in
> [historical-weather-expansion.md](./historical-weather-expansion.md).

## Purpose and status

`GET /api/weather/kharif-historical` returns a historical seasonal average,
**not a forecast**. It is an isolated pilot and its output is not connected to
crop recommendation or any trained-model artifact.

The initial candidate reference period is 2010–2019. Open-Meteo returned data
for every expected hourly timestamp for both pilot locations in the live
validation run. The endpoint still reports coverage on each call; partial
provider data is not silently presented as complete.

Example:

```text
GET /api/weather/kharif-historical?state_names=Maharashtra&district_names=PUNE
GET /api/weather/kharif-historical?state_names=Karnataka&district_names=MYSORE
```

Only the exact state/district pairs above currently have verified coordinates.
Other pairs in the generated registry are unresolved and return HTTP 409;
unknown pairs return 404. Neither case triggers geocoding.

## Data source and calculation

- Provider: [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- Reanalysis model: **ERA5**, explicitly selected with the API `models=era5`
  parameter. This uses ECMWF ERA5 hourly single-level reanalysis, not the
  current-weather/forecast API.
- Variables: `temperature_2m` (°C) and `relative_humidity_2m` (%).
- Requested time zone: UTC.
- Period: June 1 through October 31 inclusive for each year 2010–2019.
- Expected hours: 153 days × 24 hours × 10 years = **36,720** per variable.
- Aggregation: arithmetic mean over valid hourly values in the complete
  selected Kharif windows. Null, non-finite, temperature outside −90 to 60 °C,
  and relative humidity outside 0–100% are excluded. Coverage counts missing,
  excluded, or absent hours against all 36,720 expected hours.
- Incomplete seasons are shown individually in `seasonal_coverage`. Means
  use the valid values that were returned; completeness is never implied by a
  mean alone.

Every response contains the source, model, reference coordinates, provider's
snapped grid coordinates and elevation, date range, units, aggregation rule,
variable-level coverage, and per-year coverage. The result is returned by the
API; the backend caches only the derived seasonal summaries rather than
persisting the raw hourly provider archive.

## Verified pilot reference points

These coordinates identify the city reference point at each district
headquarters, not the district centroid or a district-wide average. Geocoding
was resolved once and manually disambiguated using country and administrative
hierarchy; runtime requests use only this fixed allowlist.

| CSV state | CSV district | Reference place | Latitude | Longitude | Coordinate record |
|---|---|---|---:|---:|---|
| Maharashtra | PUNE | Pune city | 18.51957 | 73.85535 | Open-Meteo geocoding result `1259229`, India / Maharashtra / Pune |
| Karnataka | MYSORE | Mysuru city | 12.29791 | 76.63925 | Open-Meteo geocoding result `1262321`, India / Karnataka / Mysuru |

The Pune point is corroborated by the [Pune district collector office contact
page](https://pune.gov.in/en/contact-us/), which locates the office on Station
Road, Pune. The Mysuru point is corroborated by the [Mysuru district deputy
commissioner contact page](https://mysore.nic.in/en/contact-us/), which
identifies the Deputy Commissioner's Office, Mysuru District, Mysuru. The
underlying geocoding lookup URLs and record details are included in every
response.

## Live sample results

Retrieved from Open-Meteo Historical Weather API using ERA5, UTC, the
2010–2019 period, and all ten June–October periods. These are historical
seasonal averages at the selected city/grid points, not a forecast:

| State / district | Reference coordinates | Provider grid coordinates | Mean 2 m temperature | Mean 2 m relative humidity | Valid / expected hours per variable |
|---|---|---|---:|---:|---:|
| Maharashtra / PUNE | 18.51957, 73.85535 | 18.50, 73.75 | 24.9638 °C | 85.5582% | 36,720 / 36,720 (100%) |
| Karnataka / MYSORE | 12.29791, 76.63925 | 12.25, 76.75 | 24.1345 °C | 79.5757% | 36,720 / 36,720 (100%) |

Those figures are sample pilot outputs, not model inputs or crop
recommendations. Provider availability and coverage are checked again for
each API request.

## API error behavior

- Unsupported state/district pair: HTTP 404.
- Provider timeout: HTTP 504.
- Provider HTTP/API error, unexpected units, or malformed response: HTTP 502.
- Coordinate bounds and finite-value checks guard the allowlisted references
  and the returned provider grid location.

## Remaining limitations

The exact provenance and temporal meaning of the crop-training CSV's
temperature/humidity features remain undocumented. This pilot's ERA5 point
means and explicit Kharif window have not been verified as semantically
equivalent to those training features. The points also represent city
reference locations rather than district-area averages. No pilot output is
used for crop inference.
