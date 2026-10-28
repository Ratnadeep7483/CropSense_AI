import assert from "node:assert/strict";
import { test } from "node:test";

import {
  assembleNpkFeatureValues,
  classifyHistoricalWeatherError,
  validateHistoricalWeatherLookup,
  validateRainfallLookup,
} from "../src/lib/npkFeatureAssembly.ts";

const currentKey = JSON.stringify(["Karnataka", "MYSORE", "Kharif"]);
const validLookup = {
  key: currentKey,
  data: {
    success: true,
    state_names: "Karnataka",
    district_names: "MYSORE",
    season_names: "Kharif",
    N: 50.5,
    P: 42.25,
    K: 31.75,
    matched_records: 3,
  },
};
const validRainfallLookup = {
  key: currentKey,
  data: {
    success: true,
    state_names: "Karnataka",
    district_names: "MYSORE",
    season_names: "Kharif",
    rainfall_mm: 655.89,
    matched_year_count: 18,
    observed_year_start: 1997,
    observed_year_end: 2014,
    description:
      "Dataset-derived multi-year mean. Rainfall provenance and measurement semantics are unverified.",
  },
};
const validWeatherLookup = {
  key: currentKey,
  data: {
    success: true,
    label: "Historical seasonal average — not a forecast",
    season: "Kharif",
    season_definition: {
      start_month: 6,
      end_month: 10,
      status: "user_defined",
      note: "June through October as specified for this pilot.",
      overlaps_with: ["Autumn", "Rabi", "Summer", "Whole Year", "Winter"],
    },
    location: {
      state: "Karnataka",
      district: "MYSORE",
      reference_place: "Mysore",
    },
    coordinates: {},
    source: "Open-Meteo Historical Weather API",
    source_url: "https://open-meteo.com/en/docs/historical-weather-api",
    model: "ERA5",
    aggregation_method: "Arithmetic mean of valid hourly observations.",
    units: { temperature_2m: "°C", relative_humidity_2m: "%" },
    averages: { temperature_2m: 25.4, relative_humidity_2m: 72.1 },
    period: {
      season: "Kharif",
      season_start_years: Array.from({ length: 10 }, (_, i) => 2010 + i),
      start_date: "2010-06-01",
      end_date: "2019-10-31",
      timezone: "UTC",
      requested_data_start: "2010-01-01",
      requested_data_end: "2019-12-31",
    },
    coverage: {},
    seasonal_coverage: [],
    cache: {
      hit: true,
      fetched_at: "2024-01-01T00:00:00Z",
      expires_at: "2024-01-31T00:00:00Z",
      ttl_days: 30,
    },
  },
};

test("assembles finite NPK values from a lookup for the current selection", () => {
  assert.deepEqual(assembleNpkFeatureValues(validLookup, currentKey), {
    N: 50.5,
    P: 42.25,
    K: 31.75,
  });
});

test("does not assemble missing or stale lookup results", () => {
  assert.equal(assembleNpkFeatureValues(null, currentKey), null);
  assert.equal(assembleNpkFeatureValues(validLookup, null), null);
  assert.equal(
    assembleNpkFeatureValues(
      { ...validLookup, key: "previous-selection" },
      currentKey,
    ),
    null,
  );
});

test("rejects unsuccessful or non-finite NPK values", () => {
  assert.equal(
    assembleNpkFeatureValues(
      { ...validLookup, data: { ...validLookup.data, success: false } },
      currentKey,
    ),
    null,
  );

  for (const invalidValue of [Number.NaN, Number.POSITIVE_INFINITY, "50"]) {
    for (const nutrient of ["N", "P", "K"]) {
      assert.equal(
        assembleNpkFeatureValues(
          {
            ...validLookup,
            data: { ...validLookup.data, [nutrient]: invalidValue },
          },
          currentKey,
        ),
        null,
      );
    }
  }
});

test("adds validated rainfall to existing NPK feature values", () => {
  assert.deepEqual(
    assembleNpkFeatureValues(validLookup, currentKey, validRainfallLookup),
    {
      N: 50.5,
      P: 42.25,
      K: 31.75,
      rainfall_mm: 655.89,
    },
  );
});

test("accepts zero rainfall as a valid value", () => {
  const zeroRainfall = {
    ...validRainfallLookup,
    data: { ...validRainfallLookup.data, rainfall_mm: 0 },
  };
  assert.deepEqual(validateRainfallLookup(zeroRainfall, currentKey), {
    rainfall_mm: 0,
  });
  assert.deepEqual(
    assembleNpkFeatureValues(validLookup, currentKey, zeroRainfall),
    { N: 50.5, P: 42.25, K: 31.75, rainfall_mm: 0 },
  );
});

test("missing, failed, and stale rainfall lookups are not assembled", () => {
  assert.equal(validateRainfallLookup(null, currentKey), null);
  assert.equal(validateRainfallLookup(validRainfallLookup, null), null);
  assert.equal(
    validateRainfallLookup(
      { ...validRainfallLookup, key: "previous-selection" },
      currentKey,
    ),
    null,
  );
  assert.equal(
    validateRainfallLookup(
      {
        ...validRainfallLookup,
        data: { ...validRainfallLookup.data, success: false },
      },
      currentKey,
    ),
    null,
  );
});

test("rejects invalid rainfall numbers, key echoes, and year metadata", () => {
  for (const rainfall of [
    Number.NaN,
    Number.POSITIVE_INFINITY,
    -0.01,
    "12",
  ]) {
    assert.equal(
      validateRainfallLookup(
        {
          ...validRainfallLookup,
          data: { ...validRainfallLookup.data, rainfall_mm: rainfall },
        },
        currentKey,
      ),
      null,
    );
  }

  const invalidMetadata = [
    { matched_year_count: 0 },
    { matched_year_count: 1.5 },
    { observed_year_start: 2015, observed_year_end: 2014 },
    { observed_year_start: 1997.5 },
    { matched_year_count: 19 },
    { description: "Dataset mean; measurement is known." },
  ];
  for (const metadata of invalidMetadata) {
    assert.equal(
      validateRainfallLookup(
        {
          ...validRainfallLookup,
          data: { ...validRainfallLookup.data, ...metadata },
        },
        currentKey,
      ),
      null,
    );
  }
  assert.equal(
    validateRainfallLookup(
      {
        ...validRainfallLookup,
        data: { ...validRainfallLookup.data, district_names: "PUNE" },
      },
      currentKey,
    ),
    null,
  );
});

test("rainfall failure does not invalidate an otherwise valid NPK feature set", () => {
  assert.deepEqual(
    assembleNpkFeatureValues(validLookup, currentKey, null),
    { N: 50.5, P: 42.25, K: 31.75 },
  );
});

test("validates historical temperature and humidity for the exact current key", () => {
  assert.deepEqual(
    validateHistoricalWeatherLookup(validWeatherLookup, currentKey),
    { temperature: 25.4, humidity: 72.1 },
  );
  assert.deepEqual(
    assembleNpkFeatureValues(
      validLookup,
      currentKey,
      validRainfallLookup,
      validWeatherLookup,
    ),
    {
      N: 50.5,
      P: 42.25,
      K: 31.75,
      rainfall_mm: 655.89,
      temperature: 25.4,
      humidity: 72.1,
    },
  );
});

test("rejects missing, stale, mismatched, and invalid weather responses", () => {
  assert.equal(validateHistoricalWeatherLookup(null, currentKey), null);
  assert.equal(
    validateHistoricalWeatherLookup(validWeatherLookup, null),
    null,
  );
  assert.equal(
    validateHistoricalWeatherLookup(
      { ...validWeatherLookup, key: "previous-selection" },
      currentKey,
    ),
    null,
  );

  const invalidResponses = [
    { success: false },
    { location: { ...validWeatherLookup.data.location, district: "PUNE" } },
    { season: "Rabi" },
    { units: { ...validWeatherLookup.data.units, temperature_2m: "F" } },
    { units: { ...validWeatherLookup.data.units, relative_humidity_2m: "fraction" } },
    { averages: { temperature_2m: Number.NaN } },
    { averages: { temperature_2m: Number.POSITIVE_INFINITY } },
    { averages: { relative_humidity_2m: "72" } },
    { period: { ...validWeatherLookup.data.period, season: "Rabi" } },
    {
      period: {
        ...validWeatherLookup.data.period,
        season_start_years: [2010, 2011],
      },
    },
    { period: { ...validWeatherLookup.data.period, start_date: "" } },
    { period: { ...validWeatherLookup.data.period, timezone: "local" } },
    { model: "Other" },
    { source: "Unknown" },
  ];
  for (const patch of invalidResponses) {
    assert.equal(
      validateHistoricalWeatherLookup(
        {
          ...validWeatherLookup,
          data: {
            ...validWeatherLookup.data,
            ...patch,
            ...(patch.averages && {
              averages: { ...validWeatherLookup.data.averages, ...patch.averages },
            }),
            ...(patch.units && {
              units: { ...validWeatherLookup.data.units, ...patch.units },
            }),
            ...(patch.location && {
              location: {
                ...validWeatherLookup.data.location,
                ...patch.location,
              },
            }),
            ...(patch.period && {
              period: { ...validWeatherLookup.data.period, ...patch.period },
            }),
          },
        },
        currentKey,
      ),
      null,
    );
  }
});

test("classifies unsupported, unavailable, and failed weather requests", () => {
  assert.equal(classifyHistoricalWeatherError(404), "unsupportedLocation");
  assert.equal(classifyHistoricalWeatherError(409), "unsupportedLocation");
  assert.equal(classifyHistoricalWeatherError(502), "unavailable");
  assert.equal(classifyHistoricalWeatherError(503), "unavailable");
  assert.equal(classifyHistoricalWeatherError(504), "unavailable");
  assert.equal(classifyHistoricalWeatherError(null), "requestFailed");
  assert.equal(classifyHistoricalWeatherError(400), "requestFailed");
});
