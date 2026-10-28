export function buildHistoricalCropWorkflowRequest(input: {
  state: string;
  district: string;
  season: string;
  soil: string;
}): {
  state_names: string;
  district_names: string;
  season_names: string;
  soil_for_crop: string;
};
