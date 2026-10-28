import assert from "node:assert/strict";
import test from "node:test";
import {
  buildHistoricalCropWorkflowRequest,
} from "../src/lib/cropWorkflowRequest.mjs";

test("workflow request trims state and district, keeps season and soil", () => {
  const request = buildHistoricalCropWorkflowRequest({
    state: " Karnataka ",
    district: " BELGAUM ",
    season: "Kharif",
    soil: "Black",
  });

  assert.deepEqual(request, {
    state_names: "Karnataka",
    district_names: "BELGAUM",
    season_names: "Kharif",
    soil_for_crop: "Black",
  });
});

test("workflow request does not include internal model feature fields", () => {
  const request = buildHistoricalCropWorkflowRequest({
    state: "Karnataka",
    district: "BELGAUM",
    season: "Kharif",
    soil: "Black",
  });

  for (const internalFeature of [
    "N",
    "P",
    "K",
    "area",
    "crop_year",
    "temperature",
    "humidity",
    "rainfall_mm",
    "farmer_available_area_acres",
  ]) {
    assert.equal(Object.hasOwn(request, internalFeature), false);
  }
});

test("workflow request serialises cleanly to JSON", () => {
  const request = buildHistoricalCropWorkflowRequest({
    state: "Karnataka",
    district: "BELGAUM",
    season: "Kharif",
    soil: "Red",
  });

  const roundTripped = JSON.parse(JSON.stringify(request));
  assert.deepEqual(roundTripped, request);
});
