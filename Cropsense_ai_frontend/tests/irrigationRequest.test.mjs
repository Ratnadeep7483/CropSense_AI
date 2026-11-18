import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import {
  buildIrrigationRequest,
  buildIrrigationWeatherRequest,
  IRRIGATION_NUMERIC_FEATURES,
  getIrrigationWeatherSummary,
  IRRIGATION_WEATHER_LIMITATION,
} from "../src/lib/irrigationRequest.mjs";

const validForm = {
  temperature: "27",
  humidity: "65",
  rainfall: "10",
  sunlightHours: "8",
  soilType: "Clay",
  crop: "Rice",
  growthStage: "Vegetative",
  season: "Kharif",
  soilMoisture: "30",
  windSpeed: "5",
  mulchingUsed: "No",
};

test("builds all 11 exact irrigation model features", () => {
  const request = buildIrrigationRequest(validForm);
  assert.deepEqual(request, {
    Temperature_C: 27,
    Humidity: 65,
    Rainfall_mm: 10,
    Sunlight_Hours: 8,
    Soil_Type: "Clay",
    Crop_Type: "Rice",
    Crop_Growth_Stage: "Vegetative",
    Season: "Kharif",
    Soil_Moisture: 30,
    Wind_Speed_kmh: 5,
    Mulching_Used: "No",
  });
  assert.equal(Object.keys(request).length, 11);
});

test("numeric feature names are finite and in the request", () => {
  const request = buildIrrigationRequest(validForm);
  for (const name of IRRIGATION_NUMERIC_FEATURES) {
    assert.equal(typeof request[name], "number");
    assert.equal(Number.isFinite(request[name]), true);
  }
});

test("rejects missing, non-finite, and boolean-like form values", () => {
  assert.throws(
    () => buildIrrigationRequest({ ...validForm, temperature: "" }),
    /Complete all irrigation fields/,
  );
  assert.throws(
    () => buildIrrigationRequest({ ...validForm, humidity: "Infinity" }),
    /Humidity must be a finite number/,
  );
  assert.throws(
    () => buildIrrigationRequest({ ...validForm, soilMoisture: "NaN" }),
    /Soil_Moisture must be a finite number/,
  );
});

test("serialises the direct prediction request cleanly", () => {
  const roundTripped = JSON.parse(
    JSON.stringify(buildIrrigationRequest(validForm)),
  );
  assert.equal(roundTripped.Crop_Type, "Rice");
  assert.equal(roundTripped.Mulching_Used, "No");
});

test("direct request ignores blank weather-only fields", () => {
  const request = buildIrrigationRequest({
    ...validForm,
    state: "",
    district: "",
    date: "",
  });
  assert.equal(request.Crop_Type, "Rice");
  assert.equal(Object.keys(request).length, 11);
  assert.equal(Object.hasOwn(request, "latitude"), false);
  assert.equal(Object.hasOwn(request, "date"), false);
});

test("weather-assisted request keeps soil moisture caller-entered", () => {
  const request = buildIrrigationWeatherRequest({
    state: "Maharashtra",
    district: "PUNE",
    soilMoisture: "30",
    soilType: "Clay",
    crop: "Rice",
    growthStage: "Vegetative",
    season: "Kharif",
    mulchingUsed: "No",
  });
  assert.deepEqual(request, {
    state: "Maharashtra",
    district: "PUNE",
    Soil_Moisture: 30,
    Soil_Type: "Clay",
    Crop_Type: "Rice",
    Crop_Growth_Stage: "Vegetative",
    Season: "Kharif",
    Mulching_Used: "No",
  });
  assert.equal(Object.hasOwn(request, "date"), false);
  assert.equal(Object.hasOwn(request, "Temperature_C"), false);
  assert.equal(Object.hasOwn(request, "Rainfall_mm"), false);
  assert.equal(Object.hasOwn(request, "Sunlight_Hours"), false);
});

test("weather-assisted request rejects missing location and soil moisture inputs", () => {
  const base = {
    state: "Maharashtra",
    district: "PUNE",
    soilMoisture: "30",
    soilType: "Clay",
    crop: "Rice",
    growthStage: "Vegetative",
    season: "Kharif",
    mulchingUsed: "No",
  };
  assert.throws(
    () => buildIrrigationWeatherRequest({ ...base, state: "" }),
    /Complete all weather-assisted/,
  );
  assert.throws(
    () => buildIrrigationWeatherRequest({ ...base, soilMoisture: "Infinity" }),
    /finite number/,
  );
});

test("weather summary exposes units, source, date, and farmer soil moisture", () => {
  const summary = getIrrigationWeatherSummary({
    Temperature_C: 25.2,
    Humidity: 81,
    Rainfall_mm: 3.4,
    Sunlight_Hours: 11.3478,
    Wind_Speed_kmh: 11.3,
    measurement: {
      source: "Open-Meteo",
      provider: "archive",
      date: "2024-06-15",
      timezone: "UTC",
    },
  });
  assert.equal(summary.source, "Open-Meteo");
  assert.equal(summary.provider, "archive");
  assert.equal(summary.date, "2024-06-15");
  assert.equal(summary.Soil_Moisture, "farmer-entered");
  assert.match(summary.Temperature_C, /°C$/);
  assert.match(summary.Rainfall_mm, /mm$/);
  assert.match(summary.Sunlight_Hours, /hours$/);
  assert.equal(summary.Sunlight_Hours, "11.35 hours");
  assert.equal(summary.warning, IRRIGATION_WEATHER_LIMITATION);
});

test("irrigation UI retains both modes and responsive layout classes", () => {
  const page = readFileSync(
    new URL("../src/pages/Irrigation.tsx", import.meta.url),
    "utf8",
  );
  assert.match(page, /Direct input/);
  assert.match(page, /Weather-assisted/);
  assert.match(page, /farmer-entered/);
  assert.doesNotMatch(page, /Weather period limitation/);
  assert.match(page, /weatherSummary\?\.source/);
  assert.match(page, /weatherSummary\?\.Temperature_C/);
  assert.match(page, /weatherSummary\?\.Humidity/);
  assert.match(page, /weatherSummary\?\.Rainfall_mm/);
  assert.match(page, /weatherSummary\?\.Sunlight_Hours/);
  assert.match(page, /weatherSummary\?\.Wind_Speed_kmh/);
  assert.match(page, /grid gap-5 md:grid-cols-2/);
  assert.match(page, /grid gap-2 sm:grid-cols-2/);
  assert.match(page, /break-words text-sm text-red-700/);
  assert.match(page, /whitespace-nowrap/);
  assert.doesNotMatch(page, /mockIrrigationResult/);
});

test("irrigation result card shows only the final recommendation", () => {
  const page = readFileSync(
    new URL("../src/pages/Irrigation.tsx", import.meta.url),
    "utf8",
  );
  assert.match(page, /result\.prediction/);
  assert.doesNotMatch(page, /probabilities\[label\]/);
  assert.doesNotMatch(page, /Predicted class confidence/);
  assert.doesNotMatch(page, /\(\["High", "Low", "Medium"\] as const\)/);
  assert.doesNotMatch(page, /confidence\s*=.*probabilities/);
});

test("irrigation form starts empty and uses placeholders for every input", () => {
  const page = readFileSync(
    new URL("../src/pages/Irrigation.tsx", import.meta.url),
    "utf8",
  );
  assert.match(page, /temperature: ""/);
  assert.match(page, /humidity: ""/);
  assert.match(page, /rainfall: ""/);
  assert.match(page, /sunlightHours: ""/);
  assert.match(page, /soilMoisture: ""/);
  assert.match(page, /windSpeed: ""/);
  assert.match(page, /state: ""/);
  assert.match(page, /district: ""/);
  assert.match(page, /placeholder=\{/);
  assert.match(page, /<option value="">Select crop<\/option>/);
  assert.match(page, /<option value="">Select soil type<\/option>/);
  assert.match(page, /<option value="">Select growth stage<\/option>/);
  assert.match(page, /<option value="">Select season<\/option>/);
  assert.match(page, /<option value="">Select mulching option<\/option>/);
  assert.doesNotMatch(page, /temperature:\s*"29"|humidity:\s*"68"|rainfall:\s*"12"|sunlightHours:\s*"8"|soilMoisture:\s*"30"|windSpeed:\s*"5"/);
});

test("weather-assisted form removes the optional date input and date state", () => {
  const page = readFileSync(
    new URL("../src/pages/Irrigation.tsx", import.meta.url),
    "utf8",
  );
  assert.doesNotMatch(page, /Weather date \(optional\)/);
  assert.doesNotMatch(page, /مौसम तिथि \(वैकल्पिक\)/);
  assert.doesNotMatch(page, /type="date"/);
  assert.doesNotMatch(page, /date:\s*""/);
});

test("weather-assisted form replaces coordinates with state and district dropdowns", () => {
  const page = readFileSync(
    new URL("../src/pages/Irrigation.tsx", import.meta.url),
    "utf8",
  );
  assert.match(page, /Select state/);
  assert.match(page, /Select district/);
  assert.match(page, /lookupCropLocationOptions/);
  assert.match(page, /setDistricts/);
  assert.doesNotMatch(page, /\bLatitude\b/);
  assert.doesNotMatch(page, /\bLongitude\b/);
  assert.doesNotMatch(page, /type="number"[\s\S]*form\.latitude/);
});

test("location and irrigation API clients target the registered backend routes", () => {
  const apiClient = readFileSync(
    new URL("../src/lib/api/client.ts", import.meta.url),
    "utf8",
  );
  const cropApi = readFileSync(
    new URL("../src/lib/api/cropApi.ts", import.meta.url),
    "utf8",
  );
  const irrigationApi = readFileSync(
    new URL("../src/lib/api/irrigationApi.ts", import.meta.url),
    "utf8",
  );
  assert.match(apiClient, /VITE_API_BASE_URL \|\| "http:\/\/127\.0\.0\.1:8001"/);
  assert.match(cropApi, /`\/api\/crop\/location-options\$\{suffix\}`/);
  assert.match(irrigationApi, /\/api\/irrigation\/predict/);
  assert.match(irrigationApi, /\/api\/irrigation\/predict-from-weather/);
  assert.match(irrigationApi, /VITE_API_BASE_URL/);
});
