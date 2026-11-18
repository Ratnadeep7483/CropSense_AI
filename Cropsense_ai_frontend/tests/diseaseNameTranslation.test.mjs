import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import {
  HINDI_DISEASE_NAMES,
  translateDiseaseName,
} from "../src/lib/diseaseNameTranslation.mjs";

const diseaseClassIds = JSON.parse(
  readFileSync(
    new URL(
      "../../Cropsense_ai_backend/app/ml/disease/disease_labels.json",
      import.meta.url,
    ),
    "utf8",
  ),
);

function getDiseaseName(classId) {
  return classId
    .split("___")[1]
    .replace(/_+$/, "")
    .replaceAll("_", " ")
    .trim();
}

test("English keeps the original disease display name", () => {
  assert.equal(translateDiseaseName("Leaf scorch", "en"), "Leaf scorch");
  assert.equal(translateDiseaseName("Unknown disease", "en"), "Unknown disease");
});

test("Hindi translates every disease label supported by the model", () => {
  assert.equal(diseaseClassIds.length, 38);

  for (const classId of diseaseClassIds) {
    const diseaseName = getDiseaseName(classId);
    assert.ok(
      HINDI_DISEASE_NAMES[diseaseName],
      `Missing Hindi translation for ${classId}`,
    );
    assert.equal(
      translateDiseaseName(diseaseName, "hi"),
      HINDI_DISEASE_NAMES[diseaseName],
    );
  }
});

test("translation preserves the original model class identifier", () => {
  const classId = "Strawberry___Leaf_scorch";
  const diseaseName = getDiseaseName(classId);

  assert.equal(translateDiseaseName(diseaseName, "hi"), "पत्ती झुलसा रोग");
  assert.equal(classId, "Strawberry___Leaf_scorch");
});

test("unknown disease names fall back to their original display text", () => {
  assert.equal(translateDiseaseName("Unknown disease", "hi"), "Unknown disease");
});
