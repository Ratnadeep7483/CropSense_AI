const hindiDiseaseNames = Object.freeze({
  "Apple scab": "सेब का स्कैब रोग",
  "Black rot": "काला सड़न रोग",
  "Cedar apple rust": "सेब का रतुआ रोग",
  healthy: "स्वस्थ",
  "Powdery mildew": "चूर्णिल आसिता",
  "Cercospora leaf spot Gray leaf spot":
    "सर्कोस्पोरा एवं ग्रे पत्ती धब्बा रोग",
  "Common rust": "सामान्य रतुआ रोग",
  "Northern Leaf Blight": "उत्तरी पत्ती झुलसा रोग",
  "Esca (Black Measles)": "एस्का (काला खसरा रोग)",
  "Leaf blight (Isariopsis Leaf Spot)":
    "पत्ती झुलसा (इसारियोप्सिस पत्ती धब्बा रोग)",
  "Haunglongbing (Citrus greening)":
    "हुआंगलोंगबिंग (सिट्रस ग्रीनिंग रोग)",
  "Bacterial spot": "जीवाणु धब्बा रोग",
  "Early blight": "अगेती झुलसा रोग",
  "Late blight": "पछेती झुलसा रोग",
  "Leaf Mold": "पत्ती फफूंद रोग",
  "Septoria leaf spot": "सेप्टोरिया पत्ती धब्बा रोग",
  "Spider mites Two-spotted spider mite":
    "दो-धब्बों वाले मकड़ी कण",
  "Target Spot": "लक्ष्य धब्बा रोग",
  "Tomato Yellow Leaf Curl Virus": "टमाटर पीली पत्ती मोड़क विषाणु",
  "Tomato mosaic virus": "टमाटर मोज़ेक विषाणु",
  "Leaf scorch": "पत्ती झुलसा रोग",
});

export function translateDiseaseName(diseaseName, language) {
  if (language !== "hi") return diseaseName;
  return hindiDiseaseNames[diseaseName] ?? diseaseName;
}

export const HINDI_DISEASE_NAMES = hindiDiseaseNames;
