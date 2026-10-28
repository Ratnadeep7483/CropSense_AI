import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildHistoricalCropRecordRequest,
  HINDI_CROP_NAMES,
  translateCropName,
} from "../src/lib/cropNameTranslation.mjs";

const datasetCrops = [
  "Arecanut",
  "Arhar/Tur",
  "Bajra",
  "Banana",
  "Barley",
  "Black pepper",
  "Castor seed",
  "Coriander",
  "Cowpea(Lobia)",
  "Dry chillies",
  "Dry ginger",
  "Garlic",
  "Gram",
  "Groundnut",
  "Guar seed",
  "Horse-gram",
  "Jowar",
  "Jute",
  "Khesari",
  "Linseed",
  "Maize",
  "Masoor",
  "Mesta",
  "Moong(Green Gram)",
  "Moth",
  "Niger seed",
  "Onion",
  "Peas & beans (Pulses)",
  "Potato",
  "Ragi",
  "Rapeseed &Mustard",
  "Rice",
  "Safflower",
  "Sannhamp",
  "Sesamum",
  "Small millets",
  "Soyabean",
  "Sugarcane",
  "Sunflower",
  "Sweet potato",
  "Tapioca",
  "Tobacco",
  "Turmeric",
  "Urad",
  "Wheat",
];

test("all exact crop classes from the dataset have Hindi display names", () => {
  assert.equal(datasetCrops.length, 45);
  for (const crop of datasetCrops) {
    assert.ok(HINDI_CROP_NAMES[crop], `Missing Hindi display name for ${crop}`);
  }
});

test("Black pepper has English and Hindi display names", () => {
  assert.equal(translateCropName("Black pepper", "en"), "Black pepper");
  assert.equal(translateCropName("Black pepper", "hi"), "काली मिर्च");
});

test("unmapped or differently-cased crop labels fall back to the original", () => {
  assert.equal(translateCropName("Unknown crop", "hi"), "Unknown crop");
  assert.equal(translateCropName("black pepper", "hi"), "black pepper");
});

test("display translation does not change the English crop name in API request data", () => {
  const record = {
    state_names: "Kerala",
    district_names: "IDUKKI",
    season: "Whole Year",
    crop: "Black pepper",
    year: 2012,
    soil_for_crop: "Laterite",
  };
  assert.equal(translateCropName(record.crop, "hi"), "काली मिर्च");
  assert.deepEqual(buildHistoricalCropRecordRequest(record), {
    state_names: "Kerala",
    district_names: "IDUKKI",
    season_names: "Whole Year",
    crop_names: "Black pepper",
    crop_year: 2012,
    soil_for_crop: "Laterite",
  });
});
