const hindiCropNames = Object.freeze({
  Arecanut: "सुपारी",
  "Arhar/Tur": "अरहर",
  Bajra: "बाजरा",
  Banana: "केला",
  Barley: "जौ",
  "Black pepper": "काली मिर्च",
  "Castor seed": "अरंडी",
  Coriander: "धनिया",
  "Cowpea(Lobia)": "लोबिया",
  "Dry chillies": "सूखी मिर्च",
  "Dry ginger": "सूखी अदरक",
  Garlic: "लहसुन",
  Gram: "चना",
  Groundnut: "मूंगफली",
  "Guar seed": "ग्वार",
  "Horse-gram": "कुल्थी",
  Jowar: "ज्वार",
  Jute: "जूट",
  Khesari: "खेसारी",
  Linseed: "अलसी",
  Maize: "मक्का",
  Masoor: "मसूर",
  Mesta: "मेस्ता",
  "Moong(Green Gram)": "मूंग",
  Moth: "मोठ",
  "Niger seed": "रामतिल",
  Onion: "प्याज",
  "Peas & beans (Pulses)": "मटर एवं फलियाँ (दलहन)",
  Potato: "आलू",
  Ragi: "रागी",
  "Rapeseed &Mustard": "रेपसीड एवं सरसों",
  Rice: "चावल",
  Safflower: "कुसुम",
  Sannhamp: "सनई",
  Sesamum: "तिल",
  "Small millets": "छोटे अनाज",
  Soyabean: "सोयाबीन",
  Sugarcane: "गन्ना",
  Sunflower: "सूरजमुखी",
  "Sweet potato": "शकरकंद",
  Tapioca: "कसावा",
  Tobacco: "तंबाकू",
  Turmeric: "हल्दी",
  Urad: "उड़द",
  Wheat: "गेहूँ",
  Soybean: "सोयाबीन",
  Tomato: "टमाटर",
});

export function translateCropName(cropName, language) {
  if (language !== "hi") return cropName;
  return hindiCropNames[cropName] ?? cropName;
}

export function buildHistoricalCropRecordRequest(record) {
  return {
    state_names: record.state_names,
    district_names: record.district_names,
    season_names: record.season,
    crop_names: record.crop,
    crop_year: record.year,
    soil_for_crop: record.soil_for_crop,
  };
}

export const HINDI_CROP_NAMES = hindiCropNames;
