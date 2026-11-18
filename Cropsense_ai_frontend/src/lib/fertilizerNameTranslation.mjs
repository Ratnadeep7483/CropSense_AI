const hindiFertilizerNames = Object.freeze({
  "Balanced NPK Fertilizer": "संतुलित NPK उर्वरक",
  Compost: "कम्पोस्ट खाद",
  DAP: "डीएपी (डाय-अमोनियम फॉस्फेट)",
  "General Purpose Fertilizer": "सामान्य उपयोग वाला उर्वरक",
  Gypsum: "जिप्सम",
  Lime: "चूना",
  "Muriate of Potash": "म्यूरेट ऑफ पोटाश",
  "Organic Fertilizer": "जैविक उर्वरक",
  Urea: "यूरिया",
  "Water Retaining Fertilizer": "जल धारण करने वाला उर्वरक",
});

export function translateFertilizerName(fertilizerName, language) {
  if (language !== "hi") return fertilizerName;
  return hindiFertilizerNames[fertilizerName] ?? fertilizerName;
}

export const HINDI_FERTILIZER_NAMES = hindiFertilizerNames;
