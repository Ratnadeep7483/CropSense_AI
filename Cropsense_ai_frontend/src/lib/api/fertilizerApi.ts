/**
 * CropSense AI — Fertilizer Recommendation API
 *
 * NOTE: The fertilizer model uses "moisture" (NOT "humidity").
 * Do not silently convert between them.
 */

import { apiFetch } from "./client";

// ── Request ─────────────────────────────────────────────────────

export interface FertilizerRecommendRequest {
  temperature: number;
  moisture: number;
  rainfall: number;
  ph: number;
  nitrogen: number;
  phosphorous: number;
  potassium: number;
  carbon: number;
  soil: string;
  crop: string;
}

// ── Response ────────────────────────────────────────────────────

export interface FertilizerRecommendResponse {
  success: boolean;
  recommended_fertilizer: string;
}

// ── API call ────────────────────────────────────────────────────

/**
 * Call the fertilizer recommendation endpoint.
 *
 * @throws Error with a user-friendly message on failure.
 */
export async function recommendFertilizer(
  data: FertilizerRecommendRequest,
): Promise<FertilizerRecommendResponse> {
  return apiFetch<FertilizerRecommendResponse>("/api/fertilizer/recommend", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
