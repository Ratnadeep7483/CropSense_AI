/** Yield Prediction API */

import { apiFetch } from "./client";

export const YIELD_FEATURES = [
  "Crop",
  "State_Name",
  "District_Name",
  "Season",
] as const;

export type YieldFeature = (typeof YIELD_FEATURES)[number];

export interface YieldPredictionRequest {
  Crop: string;
  State_Name: string;
  District_Name: string;
  Season: string;
}

export interface YieldOptionsResponse {
  success: boolean;
  features: Record<YieldFeature, string[]>;
  districts_by_state: Record<string, string[]>;
}

export interface YieldPredictionResponse {
  success: boolean;
  predicted_yield_per_area: number;
  target: "yield_per_area";
  features: YieldPredictionRequest;
}

export function getYieldOptions(): Promise<YieldOptionsResponse> {
  return apiFetch<YieldOptionsResponse>("/api/yield/options");
}

export function predictYield(
  data: YieldPredictionRequest,
): Promise<YieldPredictionResponse> {
  return apiFetch<YieldPredictionResponse>("/api/yield/predict", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
