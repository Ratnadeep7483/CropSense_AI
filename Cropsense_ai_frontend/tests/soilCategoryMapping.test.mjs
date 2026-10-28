import assert from "node:assert/strict";
import { test } from "node:test";

import { mapSoilClassToCropCategory } from "../src/lib/soilCategoryMapping.ts";

const soilCategoryCases = [
  ["Alluvial_Soil", "Alluvial"],
  ["Arid_Soil", "Arid (Desert)"],
  ["Black_Soil", "Black"],
  ["Laterite_Soil", "Laterite"],
  ["Mountain_Soil", "Mountain (Forest)"],
  ["Red_Soil", "Red"],
];

test("maps all soil classifier labels to exact crop preprocessor categories", () => {
  for (const [classifierLabel, cropCategory] of soilCategoryCases) {
    assert.equal(mapSoilClassToCropCategory(classifierLabel), cropCategory);
  }
});

test("rejects unknown and missing soil classifier labels", () => {
  assert.equal(mapSoilClassToCropCategory("Unknown_Soil"), null);
  assert.equal(mapSoilClassToCropCategory(""), null);
  assert.equal(mapSoilClassToCropCategory(undefined), null);
  assert.equal(mapSoilClassToCropCategory(null), null);
});
