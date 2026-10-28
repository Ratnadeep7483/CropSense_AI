/**
 * CropSense AI — Soil Classification API
 */

import { apiFetchFormData } from "./client";

export interface SoilPredictResponse {
  success: true;
  predicted_class: string;
  confidence: number;
}

export async function predictSoil(file: File): Promise<SoilPredictResponse> {
  const formData = new FormData();
  formData.append("image", file);

  const response = await apiFetchFormData<SoilPredictResponse>(
    "/api/soil/predict",
    formData,
  );

  if (
    response.success !== true ||
    typeof response.predicted_class !== "string" ||
    !response.predicted_class.trim() ||
    typeof response.confidence !== "number" ||
    !Number.isFinite(response.confidence) ||
    response.confidence < 0 ||
    response.confidence > 1
  ) {
    throw new Error("The soil service returned an invalid prediction.");
  }

  return response;
}
