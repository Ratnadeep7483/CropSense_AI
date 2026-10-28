import assert from "node:assert/strict";
import { test } from "node:test";

import {
  getHistoricalAreaCropsForSeason,
  getLatestHistoricalAreaForCrop,
  getLatestAreaSummaryForSeason,
  buildHistoricalAreaDropdownOptions,
  hectaresToAcres,
} from "../src/lib/historicalAreaSelection.mjs";

const records = [
  {
    crop: "Rice",
    season: "Kharif",
    year: 2022,
    area_hectares: 2,
    soil_for_crop: "Alluvial",
    npk_source: "dataset_57",
    feature_issues: {},
    status: "available",
  },
  {
    crop: "Rice",
    season: "Kharif",
    year: 2020,
    area_hectares: 1,
    soil_for_crop: "Alluvial",
    npk_source: "dataset_57",
    feature_issues: {},
    status: "available",
  },
  {
    crop: "Rice",
    season: "Rabi",
    year: 2021,
    area_hectares: null,
    soil_for_crop: "Alluvial",
    npk_source: "dataset_57",
    feature_issues: {},
    status: "ambiguous",
  },
  {
    crop: "Wheat",
    season: "Rabi",
    year: 2022,
    area_hectares: 40,
    soil_for_crop: "Black",
    npk_source: "dataset_57",
    feature_issues: {},
    status: "available",
  },
];

test("hectares are converted to acres without changing missing data", () => {
  assert.equal(hectaresToAcres(2), 4.94210762);
  assert.equal(hectaresToAcres(null), null);
  assert.equal(hectaresToAcres(Number.NaN), null);
});

test("crop options come only from the selected season", () => {
  assert.deepEqual(
    getHistoricalAreaCropsForSeason(records, "Kharif"),
    ["Rice"],
  );
  assert.deepEqual(getHistoricalAreaCropsForSeason(records, "Summer"), []);
});

test("summary uses the latest actual record for the selected crop and season", () => {
  assert.deepEqual(
    getLatestHistoricalAreaForCrop(records, "Rice", "Kharif"),
    records[0],
  );
  assert.equal(
    getLatestHistoricalAreaForCrop(records, "Wheat", "Kharif"),
    null,
  );
});

test("latest ambiguous area remains unavailable rather than using an older value", () => {
  const laterConflict = {
    crop: "Rice",
    season: "Kharif",
    year: 2023,
    area_hectares: null,
    status: "ambiguous",
  };
  assert.deepEqual(
    getLatestHistoricalAreaForCrop(
      [...records, laterConflict],
      "Rice",
      "Kharif",
    ),
    laterConflict,
  );
});
test("getLatestAreaSummaryForSeason returns latest record for each crop", () => {
  const multiYearRecords = [
    { crop: "Maize", season: "Kharif", year: 2019, area_hectares: 5, status: "available" },
    { crop: "Maize", season: "Kharif", year: 2021, area_hectares: 7, status: "available" },
    { crop: "Maize", season: "Kharif", year: 2015, area_hectares: 3, status: "available" },
  ];
  const summary = getLatestAreaSummaryForSeason(multiYearRecords, "Kharif");
  assert.equal(summary.length, 1);
  assert.equal(summary[0].year, 2021);
  assert.equal(summary[0].area_hectares, 7);
});

// ── buildHistoricalAreaDropdownOptions ───────────────────────────────────────

test("dropdown includes only records from the selected season", () => {
  const opts = buildHistoricalAreaDropdownOptions(records, "Kharif");
  assert.equal(opts.length, 2);
  assert.ok(opts.every((o) => o.crop === "Rice"));
});

test("dropdown omits records without a recorded area", () => {
  const opts = buildHistoricalAreaDropdownOptions(records, "Rabi");
  assert.equal(opts.length, 1);
  assert.equal(opts[0].crop, "Wheat");
  assert.equal(opts[0].selectable, true);
});

test("dropdown returns empty array for a season with no available records", () => {
  const opts = buildHistoricalAreaDropdownOptions(records, "Summer");
  assert.deepEqual(opts, []);
});

test("each dropdown option carries the correct fields", () => {
  const opts = buildHistoricalAreaDropdownOptions(records, "Kharif");
  const rice2022 = opts.find((o) => o.crop === "Rice" && o.year === 2022);
  assert.ok(rice2022, "Rice 2022 option should exist");
  assert.equal(typeof rice2022.value, "string");
  assert.ok(rice2022.value.length > 0);
  // area_acres = 2 * 2.47105381 = 4.94210762
  assert.ok(
    Math.abs(rice2022.area_acres - 4.94210762) < 1e-6,
    `area_acres expected ~4.942, got ${rice2022.area_acres}`,
  );
  assert.equal(rice2022.area_hectares, 2);
  assert.equal(rice2022.label, "4.94 acres");
});

test("same-area records have area-only labels and distinct record keys", () => {
  const sameAreaRecords = [
    {
      ...records[0],
      crop: "Rice",
      year: 2022,
      area_hectares: 3,
      soil_for_crop: "Alluvial",
    },
    {
      ...records[0],
      crop: "Maize",
      year: 2021,
      area_hectares: 3,
      soil_for_crop: "Black",
    },
  ];
  const options = buildHistoricalAreaDropdownOptions(
    sameAreaRecords,
    "Kharif",
  );
  assert.equal(options.length, 2);
  assert.ok(options.every((option) => option.label === "7.41 acres"));
  assert.notEqual(options[0].value, options[1].value);
  assert.notEqual(options[0].record.crop, options[1].record.crop);
});

test("dropdown is sorted crop-asc then year-desc within each crop", () => {
  const mixed = [
    { crop: "Wheat", season: "Kharif", year: 2021, area_hectares: 10, status: "available" },
    { crop: "Rice", season: "Kharif", year: 2020, area_hectares: 1, status: "available" },
    { crop: "Rice", season: "Kharif", year: 2022, area_hectares: 2, status: "available" },
    { crop: "Maize", season: "Kharif", year: 2019, area_hectares: 5, status: "available" },
  ];
  const opts = buildHistoricalAreaDropdownOptions(mixed, "Kharif");
  assert.equal(opts[0].crop, "Maize");        // M before R
  assert.equal(opts[1].crop, "Rice");
  assert.equal(opts[1].year, 2022);           // newer Rice first
  assert.equal(opts[2].crop, "Rice");
  assert.equal(opts[2].year, 2020);
  assert.equal(opts[3].crop, "Wheat");        // W last
});

test("unit conversion uses 2.47105381 factor", () => {
  const oneHectare = [
    { crop: "Crop", season: "Kharif", year: 2000, area_hectares: 1, status: "available" },
  ];
  const opts = buildHistoricalAreaDropdownOptions(oneHectare, "Kharif");
  assert.equal(opts.length, 1);
  assert.ok(
    Math.abs(opts[0].area_acres - 2.47105381) < 1e-9,
    `Expected 2.47105381, got ${opts[0].area_acres}`,
  );
});

test("options from a different season are excluded", () => {
  const opts = buildHistoricalAreaDropdownOptions(records, "Winter");
  assert.deepEqual(opts, []);
});

test("empty season string returns empty dropdown options", () => {
  const opts = buildHistoricalAreaDropdownOptions(records, "");
  assert.deepEqual(opts, []);
});

test("unit conversion handles various decimal and large hectare values with exact factor", () => {
  const sampleRecords = [
    { crop: "Cotton", season: "Kharif", year: 2020, area_hectares: 10.5, status: "available" },
    { crop: "Barley", season: "Kharif", year: 2018, area_hectares: 0.25, status: "available" },
  ];
  const opts = buildHistoricalAreaDropdownOptions(sampleRecords, "Kharif");
  assert.equal(opts.length, 1);
  const cotton = opts.find((o) => o.crop === "Cotton");
  const barley = opts.find((o) => o.crop === "Barley");
  assert.ok(cotton);
  assert.equal(barley, undefined);
  assert.ok(Math.abs(cotton.area_acres - 10.5 * 2.47105381) < 1e-9);
});

test("missing/non-finite area values are not offered as area options", () => {
  const invalidRecords = [
    { crop: "Paddy", season: "Kharif", year: 2021, area_hectares: null, status: "available" },
    { crop: "Paddy", season: "Kharif", year: 2020, area_hectares: Number.NaN, status: "available" },
    { crop: "Paddy", season: "Kharif", year: 2019, area_hectares: Number.POSITIVE_INFINITY, status: "available" },
    { crop: "Paddy", season: "Kharif", year: 2018, area_hectares: 15, status: "available" },
  ];
  const opts = buildHistoricalAreaDropdownOptions(invalidRecords, "Kharif");
  assert.equal(opts.length, 1);
  assert.equal(opts.find((option) => option.year === 2018).area_hectares, 15);
});

test("dropdown labels show only the converted area in acres", () => {
  const opts = buildHistoricalAreaDropdownOptions(
    [
      {
        crop: "Rice",
        season: "Kharif",
        year: 2020,
        area_hectares: 2,
        soil_for_crop: "Alluvial",
        status: "available",
        feature_issues: {},
      },
    ],
    "Kharif",
  );
  assert.equal(opts[0].label, "4.94 acres");
});

test("dropdown includes converted areas from 1 through 100 acres, inclusive", () => {
  const acresToHectares = (acres) => acres / 2.47105381;
  const rangeRecords = [
    {
      crop: "Below lower bound",
      season: "Kharif",
      year: 2023,
      area_hectares: acresToHectares(0.999),
      status: "available",
    },
    {
      crop: "At lower bound",
      season: "Kharif",
      year: 2023,
      area_hectares: acresToHectares(1),
      status: "available",
    },
    {
      crop: "At upper bound",
      season: "Kharif",
      year: 2023,
      area_hectares: acresToHectares(100),
      status: "available",
    },
    {
      crop: "Above upper bound",
      season: "Kharif",
      year: 2023,
      area_hectares: acresToHectares(100.004),
      status: "available",
    },
  ];
  const options = buildHistoricalAreaDropdownOptions(
    rangeRecords,
    "Kharif",
  );
  assert.deepEqual(
    options.map((option) => option.crop),
    ["At lower bound", "At upper bound"],
  );
  assert.ok(Math.abs(options[0].area_acres - 1) < Number.EPSILON);
  assert.ok(Math.abs(options[1].area_acres - 100) < Number.EPSILON * 100);
  assert.equal(options[1].record.area_hectares, acresToHectares(100));
});
