/**
 * CropSense AI — Crop Recommendation API
 */

import { apiFetch } from "./client";

// ── Request ─────────────────────────────────────────────────────

export interface CropRecommendRequest {
  state_names: string;
  district_names: string;
  season_names: string;
  soil_for_crop: string;
  N: number;
  P: number;
  K: number;
  temperature: number;
  humidity: number;
  rainfall_mm: number;
  crop_year: number;
  area: number;
}

// ── Response ────────────────────────────────────────────────────

export interface CropRecommendResponse {
  success: boolean;
  recommended_crop: string;
}

export interface CropLocationOptionsResponse {
  success: boolean;
  states: string[];
  districts: string[];
  seasons: string[];
}

export interface HistoricalAreaRecord {
  crop: string;
  season: string;
  year: number;
  state_names: string;
  district_names: string;
  soil_for_crop: string | null;
  area_hectares: number | null;
  status: "available" | "ambiguous" | "missing";
  N: number | null;
  P: number | null;
  K: number | null;
  temperature: number | null;
  humidity: number | null;
  rainfall_mm: number | null;
  npk_source: string | null;
  matching_records: number;
  feature_issues: Record<string, string>;
}

export interface HistoricalAreaResponse {
  success: boolean;
  state_names: string;
  district_names: string;
  units: "hectares";
  records: HistoricalAreaRecord[];
}

export interface HistoricalCropRecordRequest {
  state_names: string;
  district_names: string;
  season_names: string;
  crop_names: string;
  crop_year: number;
  soil_for_crop: string;
}

export interface CropModelInputFeatures extends CropRecommendRequest {}

export interface HistoricalCropRecordRecommendationResponse {
  success: boolean;
  predicted_crop: string;
  reference_crop: string;
  npk_source: string;
  area_unit: "hectares";
  matching_records: number;
  model_inputs: CropModelInputFeatures;
}

export interface HistoricalCropWorkflowRequest {
  state_names: string;
  district_names: string;
  season_names: string;
  soil_for_crop: string;
}

export interface HistoricalCropCandidateStatus {
  crop: string;
  status: string;
  historical_area: number | null;
  area_year: number | null;
  experimental_score: number | null;
  error: string | null;
}

export interface HistoricalCropWorkflowResponse {
  success: boolean;
  recommendation_available: boolean;
  recommended_crop?: string | null;
  state_names: string;
  district_names: string;
  season_names: string;
  target_year: number;
  farmer_available_area_acres?: number | null;
  farmer_available_area_hectares?: number | null;
  temperature: number | null;
  humidity: number | null;
  weather_status: string;
  weather_error: string | null;
  rainfall_mm: number | null;
  rainfall_status: string;
  rainfall_error: string | null;
  rainfall_matched_year_count: number | null;
  rainfall_observed_year_start: number | null;
  rainfall_observed_year_end: number | null;
  total_candidates: number;
  area_available: number;
  missing_history: number;
  ambiguous_area: number;
  npk_unavailable_or_unverified: number;
  shared_features_unverified: number;
  validation_failures: number;
  scored_candidates: number;
  ranking_status: string;
  ranking_limitation: string;
  scoring_blockers: string[];
  recommendation_blockers: string[];
  action_required: string;
  candidates: HistoricalCropCandidateStatus[];
}

export interface NPKLookupRequest {
  state_names: string;
  district_names: string;
  season_names: string;
}

export interface NPKLookupResponse extends NPKLookupRequest {
  success: boolean;
  N: number;
  P: number;
  K: number;
  matched_records: number;
}

export interface RainfallLookupResponse extends NPKLookupRequest {
  success: boolean;
  rainfall_mm: number;
  matched_year_count: number;
  observed_year_start: number;
  observed_year_end: number;
  description: string;
}

export type HistoricalWeatherSeason =
  | "Autumn"
  | "Kharif"
  | "Rabi"
  | "Summer"
  | "Whole Year"
  | "Winter";

const historicalWeatherSeasons: readonly HistoricalWeatherSeason[] = [
  "Autumn",
  "Kharif",
  "Rabi",
  "Summer",
  "Whole Year",
  "Winter",
];

export function isHistoricalWeatherSeason(
  value: string,
): value is HistoricalWeatherSeason {
  return historicalWeatherSeasons.includes(value as HistoricalWeatherSeason);
}

export interface HistoricalWeatherRequest {
  state_names: string;
  district_names: string;
  season: HistoricalWeatherSeason;
}

export interface HistoricalWeatherResponse {
  success: boolean;
  label: string;
  season: HistoricalWeatherSeason;
  season_definition: {
    start_month: number;
    end_month: number;
    status: string;
    note: string;
    overlaps_with: HistoricalWeatherSeason[];
  };
  location: {
    state: string;
    district: string;
    reference_place: string;
  };
  coordinates: Record<string, unknown>;
  source: string;
  source_url: string;
  model: string;
  aggregation_method: string;
  units: {
    temperature_2m: string;
    relative_humidity_2m: string;
  };
  averages: {
    temperature_2m: number;
    relative_humidity_2m: number;
  };
  period: {
    season: HistoricalWeatherSeason;
    season_start_years: number[];
    start_date: string;
    end_date: string;
    timezone: string;
    requested_data_start: string;
    requested_data_end: string;
  };
  coverage: Record<
    string,
    {
      expected_hours: number;
      valid_hours: number;
      missing_hours: number;
      coverage_percent: number;
      incomplete_seasons: number;
    }
  >;
  seasonal_coverage: Array<{
    year: number;
    start_date: string;
    end_date: string;
    expected_hours: number;
    temperature_valid_hours: number;
    humidity_valid_hours: number;
    complete: boolean;
  }>;
  cache: {
    hit: boolean;
    fetched_at: string;
    expires_at: string;
    ttl_days: number;
  };
}

// ── API call ────────────────────────────────────────────────────

/** Retrieve state, district, and season options from the crop dataset. */
export async function lookupCropLocationOptions(data: {
  state_names?: string;
  district_names?: string;
} = {}): Promise<CropLocationOptionsResponse> {
  const query = new URLSearchParams();
  if (data.state_names) query.set("state_names", data.state_names);
  if (data.district_names) query.set("district_names", data.district_names);
  const suffix = query.size > 0 ? `?${query.toString()}` : "";
  return apiFetch<CropLocationOptionsResponse>(
    `/api/crop/location-options${suffix}`,
    { method: "GET" },
  );
}

/** Retrieve raw historical crop-area records for the exact selected district. */
export async function lookupHistoricalArea(
  data: Pick<NPKLookupRequest, "state_names" | "district_names"> & {
    season_names?: string;
  },
): Promise<HistoricalAreaResponse> {
  const query = new URLSearchParams({
    state_names: data.state_names,
    district_names: data.district_names,
  });
  if (data.season_names) query.set("season_names", data.season_names);
  return apiFetch<HistoricalAreaResponse>(
    `/api/crop/historical-area?${query.toString()}`,
    { method: "GET" },
  );
}

/** Resolve a selected historical row on the server and predict from its features. */
export async function recommendCropFromHistoricalRecord(
  data: HistoricalCropRecordRequest,
): Promise<HistoricalCropRecordRecommendationResponse> {
  return apiFetch<HistoricalCropRecordRecommendationResponse>(
    "/api/crop/recommend-from-record",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

/**
 * Look up mean NPK values for an exact dataset state/district/season key.
 */
export async function lookupHistoricalNpk(
  data: NPKLookupRequest,
): Promise<NPKLookupResponse> {
  return apiFetch<NPKLookupResponse>("/api/crop/npk-lookup", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Look up the dataset-derived multi-year rainfall mean for an exact key.
 */
export async function lookupHistoricalRainfall(
  data: NPKLookupRequest,
): Promise<RainfallLookupResponse> {
  return apiFetch<RainfallLookupResponse>("/api/crop/rainfall-lookup", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Retrieve historical seasonal temperature and humidity for a verified location.
 */
export async function lookupHistoricalWeather(
  data: HistoricalWeatherRequest,
): Promise<HistoricalWeatherResponse> {
  const query = new URLSearchParams({
    state_names: data.state_names,
    district_names: data.district_names,
    season: data.season,
  });
  return apiFetch<HistoricalWeatherResponse>(
    `/api/weather/kharif-historical?${query.toString()}`,
    { method: "GET" },
  );
}

/**
 * Call the crop recommendation endpoint.
 *
 * @throws Error with a user-friendly message on failure.
 */
export async function recommendCrop(
  data: CropRecommendRequest,
): Promise<CropRecommendResponse> {
  return apiFetch<CropRecommendResponse>("/api/crop/recommend", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Assemble candidate-wise historical coverage without enabling production
 * prediction or sending farmer-entered model feature values.
 */
export async function recommendCropFromHistoricalFeatures(
  data: HistoricalCropWorkflowRequest,
): Promise<HistoricalCropWorkflowResponse> {
  return apiFetch<HistoricalCropWorkflowResponse>(
    "/api/crop/recommend-historical",
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}
