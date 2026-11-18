/**
 * CropSense AI — Plant Disease Classification API
 */

import { apiFetchFormData } from "./client";

export interface DiseasePredictResponse {
  success: true;
  predicted_crop: string;
  predicted_disease: string;
  confidence: number;
}

export async function predictDisease(file: File): Promise<DiseasePredictResponse> {
  const formData = new FormData();
  formData.append("image", file);

  const response = await apiFetchFormData<DiseasePredictResponse>(
    "/api/disease/predict",
    formData,
  );
  if (
    response.success !== true ||
    typeof response.predicted_crop !== "string" ||
    !response.predicted_crop.trim() ||
    typeof response.predicted_disease !== "string" ||
    !response.predicted_disease.trim() ||
    typeof response.confidence !== "number" ||
    !Number.isFinite(response.confidence) ||
    response.confidence < 0 ||
    response.confidence > 1
  ) {
    throw new Error("The disease service returned an invalid prediction.");
  }
  return response;
}
