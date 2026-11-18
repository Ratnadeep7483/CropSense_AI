/** Smart Irrigation API — shared FastAPI backend */

export interface IrrigationPredictionRequest {
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
}

export interface IrrigationPredictionResponse {
  success: boolean;
  prediction: "High" | "Low" | "Medium";
  probabilities: Record<"High" | "Low" | "Medium", number>;
  weather?: IrrigationWeatherResponse;
}

export interface IrrigationWeatherResponse {
  Temperature_C: number;
  Humidity: number;
  Rainfall_mm: number;
  Sunlight_Hours: number;
  Wind_Speed_kmh: number;
  measurement: {
    date: string;
    timezone: string;
    period: string;
    source: string;
    provider: "archive" | "forecast";
    units: Record<string, string>;
    not_mapped: string[];
  };
}

export interface IrrigationWeatherPredictionRequest {
  state: string;
  district: string;
  Soil_Moisture: number;
  Soil_Type: IrrigationPredictionRequest["Soil_Type"];
  Crop_Type: IrrigationPredictionRequest["Crop_Type"];
  Crop_Growth_Stage: IrrigationPredictionRequest["Crop_Growth_Stage"];
  Season: IrrigationPredictionRequest["Season"];
  Mulching_Used: IrrigationPredictionRequest["Mulching_Used"];
}

const IRRIGATION_API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8001";

function validateIrrigationPrediction(
  body: unknown,
): IrrigationPredictionResponse {
  if (typeof body !== "object" || body === null) {
    throw new Error("Irrigation service returned an invalid response.");
  }
  const response = body as Partial<IrrigationPredictionResponse>;
  if (
    response.success !== true ||
    (response.prediction !== "High" &&
      response.prediction !== "Low" &&
      response.prediction !== "Medium") ||
    typeof response.probabilities !== "object" ||
    response.probabilities === null
  ) {
    throw new Error("Irrigation service returned an invalid prediction.");
  }
  const probabilities = response.probabilities;
  const values = [
    probabilities.High,
    probabilities.Low,
    probabilities.Medium,
  ];
  if (
    values.some(
      (value) =>
        typeof value !== "number" ||
        !Number.isFinite(value) ||
        value < 0 ||
        value > 1,
    ) ||
    Math.abs(values.reduce((sum, value) => sum + value, 0) - 1) > 0.001
  ) {
    throw new Error("Irrigation service returned invalid probabilities.");
  }
  return response as IrrigationPredictionResponse;
}

export async function predictIrrigation(
  data: IrrigationPredictionRequest,
): Promise<IrrigationPredictionResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30_000);

  try {
    const response = await fetch(
      `${IRRIGATION_API_BASE_URL}/api/irrigation/predict`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        signal: controller.signal,
      },
    );

    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }

    if (!response.ok) {
      const error =
        typeof body === "object" &&
        body !== null &&
        "error" in body &&
        typeof body.error === "string"
          ? body.error
          : `Irrigation prediction failed (${response.status})`;
      throw new Error(error);
    }

    return validateIrrigationPrediction(body);
  } catch (error: unknown) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("Request timed out. Please try again.");
    }
    if (error instanceof TypeError) {
      throw new Error(
        "Unable to connect to the irrigation service. Make sure the backend is running.",
      );
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function predictIrrigationFromWeather(
  data: IrrigationWeatherPredictionRequest,
): Promise<IrrigationPredictionResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30_000);

  try {
    const response = await fetch(
      `${IRRIGATION_API_BASE_URL}/api/irrigation/predict-from-weather`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        signal: controller.signal,
      },
    );

    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }

    if (!response.ok) {
      const error =
        typeof body === "object" &&
        body !== null &&
        "error" in body &&
        typeof body.error === "string"
          ? body.error
          : `Weather-assisted irrigation prediction failed (${response.status})`;
      throw new Error(error);
    }

    return validateIrrigationPrediction(body);
  } catch (error: unknown) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("Request timed out. Please try again.");
    }
    if (error instanceof TypeError) {
      throw new Error(
        "Unable to connect to the irrigation service. Make sure the backend is running.",
      );
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}
