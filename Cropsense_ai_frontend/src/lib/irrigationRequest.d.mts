export interface IrrigationFormValues {
  temperature: string;
  humidity: string;
  rainfall: string;
  sunlightHours: string;
  soilType: string;
  crop: string;
  growthStage: string;
  season: string;
  soilMoisture: string;
  windSpeed: string;
  mulchingUsed: string;
}

export const IRRIGATION_NUMERIC_FEATURES: readonly string[];

export function buildIrrigationRequest(form: IrrigationFormValues): {
  Temperature_C: number;
  Humidity: number;
  Rainfall_mm: number;
  Sunlight_Hours: number;
  Soil_Type: "Clay" | "Loamy" | "Sandy" | "Silt";
  Crop_Type: "Cotton" | "Maize" | "Potato" | "Rice" | "Sugarcane" | "Wheat";
  Crop_Growth_Stage: "Flowering" | "Harvest" | "Sowing" | "Vegetative";
  Season: "Kharif" | "Rabi" | "Zaid";
  Soil_Moisture: number;
  Wind_Speed_kmh: number;
  Mulching_Used: "Yes" | "No";
};

export interface IrrigationWeatherFormValues {
  state: string;
  district: string;
  soilMoisture: string;
  soilType: string;
  crop: string;
  growthStage: string;
  season: string;
  mulchingUsed: string;
}

export function buildIrrigationWeatherRequest(form: IrrigationWeatherFormValues): {
  state: string;
  district: string;
  Soil_Moisture: number;
  Soil_Type: "Clay" | "Loamy" | "Sandy" | "Silt";
  Crop_Type: "Cotton" | "Maize" | "Potato" | "Rice" | "Sugarcane" | "Wheat";
  Crop_Growth_Stage: "Flowering" | "Harvest" | "Sowing" | "Vegetative";
  Season: "Kharif" | "Rabi" | "Zaid";
  Mulching_Used: "Yes" | "No";
};

export const IRRIGATION_WEATHER_LIMITATION: string;

export function getIrrigationWeatherSummary(weather: unknown): {
  source: string;
  provider: string;
  date: string;
  timezone: string;
  Temperature_C: string;
  Humidity: string;
  Rainfall_mm: string;
  Sunlight_Hours: string;
  Wind_Speed_kmh: string;
  Soil_Moisture: string;
  warning: string;
};
