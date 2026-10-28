// ============================================================
// CropSense AI — Mock Data
// Structured for easy replacement with real API responses.
// ============================================================

// ---------- Weather ----------
export interface WeatherCurrent {
  temperature: number;
  condition: string;
  humidity: number;
  rainfall: number;
  wind: number;
  location: string;
}

export interface WeatherDay {
  day: string;
  icon: string;
  tempHigh: number;
  condition: string;
  rainfall: number;
}

export const mockCurrentWeather: WeatherCurrent = {
  temperature: 28,
  condition: "Partly Cloudy",
  humidity: 68,
  rainfall: 2,
  wind: 12,
  location: "Belagavi",
};

export const mockForecast: WeatherDay[] = [
  { day: "Monday", icon: "☀️", tempHigh: 28, condition: "Sunny", rainfall: 0 },
  {
    day: "Tuesday",
    icon: "🌧️",
    tempHigh: 25,
    condition: "Rainy",
    rainfall: 14,
  },
  {
    day: "Wednesday",
    icon: "🌧️",
    tempHigh: 26,
    condition: "Rainy",
    rainfall: 8,
  },
  {
    day: "Thursday",
    icon: "☀️",
    tempHigh: 29,
    condition: "Sunny",
    rainfall: 0,
  },
  {
    day: "Friday",
    icon: "☀️",
    tempHigh: 30,
    condition: "Sunny",
    rainfall: 0,
  },
];

export const mockWeatherChart = [
  { day: "Mon", temp: 28, rainfall: 0 },
  { day: "Tue", temp: 25, rainfall: 14 },
  { day: "Wed", temp: 26, rainfall: 8 },
  { day: "Thu", temp: 29, rainfall: 0 },
  { day: "Fri", temp: 30, rainfall: 0 },
];

// ---------- Disease Detection ----------
export interface DiseaseResult {
  disease: string;
  confidence: number;
  severity: string;
  treatment: string;
  prevention: string[];
}

export const mockDiseaseResult: DiseaseResult = {
  disease: "Late Blight",
  confidence: 96.4,
  severity: "Moderate",
  treatment:
    "Follow appropriate crop protection guidance and consult local agricultural experts before applying chemicals. Apply copper-based fungicides early and remove infected leaves.",
  prevention: [
    "Use disease-resistant crop varieties",
    "Ensure proper spacing between plants for air circulation",
    "Avoid overhead irrigation to reduce leaf wetness",
    "Remove and destroy infected plant debris",
    "Rotate crops every season to break disease cycles",
  ],
};

// ---------- Crop Recommendation ----------
export interface CropResult {
  name: string;
  emoji: string;
  suitability: number;
  reasons: string[];
}

export const mockCropRecommendation: CropResult = {
  name: "Maize",
  emoji: "🌽",
  suitability: 92,
  reasons: [
    "Suitable soil conditions",
    "Suitable temperature",
    "Suitable rainfall",
  ],
};

export const mockAlternativeCrops: CropResult[] = [
  {
    name: "Rice",
    emoji: "🌾",
    suitability: 85,
    reasons: ["Good moisture levels", "Suitable pH"],
  },
  {
    name: "Soybean",
    emoji: "🫘",
    suitability: 78,
    reasons: ["Nitrogen-fixing crop", "Suitable climate"],
  },
  {
    name: "Wheat",
    emoji: "🌾",
    suitability: 72,
    reasons: ["Cool season crop", "Moderate water needs"],
  },
];

// ---------- Yield Prediction ----------
export interface YieldResult {
  estimatedYield: number;
  unit: string;
  rangeLow: number;
  rangeHigh: number;
  productivity: number;
  productivityUnit: string;
}

export const mockYieldResult: YieldResult = {
  estimatedYield: 2850,
  unit: "kg",
  rangeLow: 2600,
  rangeHigh: 3100,
  productivity: 1140,
  productivityUnit: "kg/acre",
};

export const mockYieldChart = [
  { label: "Low", value: 2600 },
  { label: "Predicted", value: 2850 },
  { label: "High", value: 3100 },
];

// ---------- Irrigation ----------
export interface IrrigationResult {
  shouldIrrigate: boolean;
  recommendation: string;
  reason: string;
  nextTime: string;
}

export const mockIrrigationResult: IrrigationResult = {
  shouldIrrigate: false,
  recommendation: "DO NOT IRRIGATE TODAY",
  reason: "Rain is expected within the next 12 hours.",
  nextTime: "Tomorrow, 6:00 AM – 7:00 AM",
};

// ---------- Chat Messages ----------
export interface ChatMessage {
  id: string;
  sender: "farmer" | "ai";
  text: string;
  timestamp: string;
}

export const mockChatMessages: ChatMessage[] = [
  {
    id: "1",
    sender: "farmer",
    text: "मेरे टमाटर के पत्ते पीले क्यों हो रहे हैं?",
    timestamp: "10:30 AM",
  },
  {
    id: "2",
    sender: "ai",
    text: "टमाटर की पत्तियां पीली होने के कई कारण हो सकते हैं, जैसे पोषक तत्वों की कमी, अधिक पानी या बीमारी। यदि आप पत्ते की फोटो अपलोड करते हैं, तो मैं बेहतर तरीके से मदद कर सकता हूं।",
    timestamp: "10:30 AM",
  },
];

export const mockAiResponses: Record<string, string> = {
  "Why are my tomato leaves turning yellow?":
    "Yellowing tomato leaves can be caused by several factors including nutrient deficiency (especially nitrogen or iron), overwatering, underwatering, or disease. Check the pattern of yellowing — if lower leaves yellow first, it's likely nitrogen deficiency. If you can upload a photo, I can help identify the exact issue.",
  "Which crop should I grow?":
    "Based on typical conditions in your region, Maize, Rice, and Soybean are excellent choices for this season. I'd recommend using the Crop Recommendation tool with your specific soil and weather data for a personalized suggestion.",
  "Should I irrigate today?":
    "Based on current weather data showing 75% rain probability in your area, I'd recommend waiting. Rain is expected within the next 12 hours. Check the Smart Irrigation tool for a detailed recommendation.",
  "What disease is affecting my plant?":
    "To identify the disease, please upload a clear photo of the affected plant leaves using the Disease Detection tool. I can analyze the image and provide treatment recommendations.",
  "मेरे टमाटर के पत्ते पीले क्यों हो रहे हैं?":
    "टमाटर की पत्तियां पीली होने के कई कारण हो सकते हैं, जैसे पोषक तत्वों की कमी (विशेषकर नाइट्रोजन या आयरन), अधिक पानी, कम पानी या बीमारी। यदि निचली पत्तियां पहले पीली हो रही हैं, तो यह नाइट्रोजन की कमी हो सकती है। कृपया पत्ते की फोटो अपलोड करें ताकि मैं सही समस्या पहचान सकूं।",
  "मुझे कौन सी फसल उगानी चाहिए?":
    "आपके क्षेत्र की सामान्य परिस्थितियों के आधार पर, इस मौसम के लिए मक्का, चावल और सोयाबीन उत्कृष्ट विकल्प हैं। व्यक्तिगत सुझाव के लिए अपनी मिट्टी और मौसम डेटा के साथ फसल अनुशंसा उपकरण का उपयोग करें।",
  "क्या मुझे आज सिंचाई करनी चाहिए?":
    "वर्तमान मौसम डेटा आपके क्षेत्र में 75% बारिश की संभावना दिखा रहा है, इसलिए मैं प्रतीक्षा करने की सलाह दूंगा। अगले 12 घंटों में बारिश की उम्मीद है। विस्तृत सिफारिश के लिए स्मार्ट सिंचाई उपकरण देखें।",
  "मेरी फसल में कौन सा रोग है?":
    "रोग की पहचान के लिए, कृपया रोग पहचान उपकरण का उपयोग करके प्रभावित पौधे की पत्तियों की स्पष्ट फोटो अपलोड करें। मैं तस्वीर का विश्लेषण करके उपचार सिफारिशें प्रदान कर सकता हूं।",
};
