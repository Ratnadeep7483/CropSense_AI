# Crop model weather-feature and historical pilot status

## Current status

An isolated Open-Meteo ERA5 historical-weather pilot is available for the
verified locations in the CSV-derived registry. The registry lists all 627
state/district pairs, but only two currently have verified reference points;
the other 625 are unresolved. The service supports the six CSV season labels,
with only Kharif's June–October window user-defined and the other five ranges
explicitly labeled proposals. It is not a forecast and is not connected to
crop recommendation. Do not substitute its values for the model's historical /
season-associated training values. The crop form intentionally keeps
`modelFeatures` unavailable and the recommendation action disabled while
required integrations are missing.

See [historical-weather-expansion.md](./historical-weather-expansion.md) for
the location registry, season proposals, cache, aggregation, coverage, and
remaining blockers.

## Verified model contract

The crop model's `FEATURE_COLUMNS` and saved preprocessor use the raw numeric
features `temperature` and `humidity`. The request schema documents temperature
in degrees Celsius and relative humidity as a percent. Both features are
required; the request schema does not allow null/missing values. The saved
numeric `FunctionTransformer` passes values through unchanged; it does not
scale or impute them.

The training CSV
`data/Copy of crop_recommendation_45_with_year_area.csv` contains 218,189 rows.
Both weather columns are non-null and finite:

| Feature | Schema unit | Observed CSV minimum | Observed CSV maximum |
|---|---:|---:|---:|
| `temperature` | °C | -8.356 | 35.222 |
| `humidity` | % relative humidity | 17.9925 | 92.728 |

These are observed training-data bounds, not a validated physical or
inference-acceptance range. The API does not declare explicit feature bounds.

Weather values are associated with state, district, season, and `crop_year`
(1997–2015). Within the CSV, every such group has one temperature and humidity
value, repeated across its crop rows. The `npk_source` field has labels such as
`estimated_ranges`, `merged_51_point_jitter`, and `dataset_57`; its name and
row patterns concern NPK-source variants, not weather provenance. No source
metadata explains how weather values were observed, estimated, averaged, or
joined. Therefore their exact temporal interpretation (historical observation,
seasonal average, or another constructed value) is unverified.

The CSV and the location dropdown asset provide state/district names, not
coordinates. District labels alone are not a reliable geocoder input: names
may be ambiguous across states, may be legacy spellings, and do not identify a
representative location or the area aggregation used during training.

## Weather pilot boundary and remaining model-integration blockers

The pilot uses Open-Meteo Historical Weather API and explicitly requests ERA5.
That historical reanalysis product is distinct from the current Weather API's
latest forecast/model time series. The API response's snapped model-grid
coordinates are included alongside the requested reference-point coordinates.
Currently verified points are Pune and Mysuru district-HQ city references;
they are not district centroids or area averages. Unresolved pairs return an
explicit conflict response and do not trigger geocoding.

This pilot does not settle the following issues needed for crop-model
integration:

1. Provenance for the CSV weather fields and a definition of their aggregation
   period and summary statistic.
2. Verified season-to-date ranges and year semantics compatible with the
   historical source. Kharif's June–October interval is an explicit pilot
   requirement; the other ranges are transparent proposals, not recovered
   training-data rules.
3. A decision on how to supply values for requested crop years outside the
   training-data period, plus range/missing-data policy.
4. Verified coordinates (or a representative-point policy) for unresolved
   state/district pairs and a mapping from city points / area aggregation to
   model features.

The pilot makes no crop-model feature fallback. The frontend pending-
integration message continues to note that historical training-compatible
weather is not supplied and current weather is not a substitute.

## Validation

Run the local contract checks and the existing crop model/API smoke tests:

```powershell
.\.venv\Scripts\python.exe scripts\test_crop_weather_contract.py
.\.venv\Scripts\python.exe scripts\test_historical_weather.py
.\.venv\Scripts\python.exe scripts\smoke_test_crop_model.py
.\.venv\Scripts\python.exe scripts\test_crop_api.py
```
