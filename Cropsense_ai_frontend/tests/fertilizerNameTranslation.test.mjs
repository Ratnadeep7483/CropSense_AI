import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import {
  HINDI_FERTILIZER_NAMES,
  translateFertilizerName,
} from "../src/lib/fertilizerNameTranslation.mjs";

const metadata = JSON.parse(
  readFileSync(
    new URL(
      "../../Cropsense_ai_backend/app/ml/fertilizer/fertilizer_model_metadata.json",
      import.meta.url,
    ),
    "utf8",
  ),
);

test("English keeps the original fertilizer class name", () => {
  assert.equal(translateFertilizerName("Urea", "en"), "Urea");
  assert.equal(
    translateFertilizerName("Unknown fertilizer", "en"),
    "Unknown fertilizer",
  );
});

test("Hindi translates every supported fertilizer class", () => {
  assert.equal(metadata.classes.length, 10);

  for (const className of metadata.classes) {
    assert.ok(
      HINDI_FERTILIZER_NAMES[className],
      `Missing Hindi translation for ${className}`,
    );
    assert.equal(
      translateFertilizerName(className, "hi"),
      HINDI_FERTILIZER_NAMES[className],
    );
  }
});

test("translation does not change the original backend class name", () => {
  const backendClassName = "Urea";

  assert.equal(translateFertilizerName(backendClassName, "hi"), "यूरिया");
  assert.equal(backendClassName, "Urea");
});

test("unknown fertilizer names fall back to their original display text", () => {
  assert.equal(
    translateFertilizerName("Unknown fertilizer", "hi"),
    "Unknown fertilizer",
  );
});
