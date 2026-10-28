import assert from "node:assert/strict";
import { test } from "node:test";

import {
  cropSeasonCategories,
  inferCropSeasonFromMonth,
  parseCropSeason,
} from "../src/lib/cropSeasonSelection.ts";

const expectedCategories = [
  "Autumn",
  "Kharif",
  "Rabi",
  "Summer",
  "Whole Year",
  "Winter",
];

test("season categories preserve the exact trained model labels", () => {
  assert.deepEqual(cropSeasonCategories, expectedCategories);
  for (const category of expectedCategories) {
    assert.equal(parseCropSeason(category), category);
  }
});

test("empty, unsupported, and differently-cased values have no fallback", () => {
  assert.equal(parseCropSeason(""), null);
  assert.equal(parseCropSeason("kharif"), null);
  assert.equal(parseCropSeason("Monsoon"), null);
});

test("Whole Year is accepted only as an explicit exact category", () => {
  assert.equal(parseCropSeason("Whole Year"), "Whole Year");
  assert.equal(inferCropSeasonFromMonth(1), null);
  assert.equal(inferCropSeasonFromMonth(12), null);
});

test("months without verified rules remain unassigned, including boundaries", () => {
  for (let month = 1; month <= 12; month += 1) {
    assert.equal(inferCropSeasonFromMonth(month), null);
  }
  assert.throws(() => inferCropSeasonFromMonth(0), RangeError);
  assert.throws(() => inferCropSeasonFromMonth(13), RangeError);
  assert.throws(() => inferCropSeasonFromMonth(1.5), RangeError);
});

