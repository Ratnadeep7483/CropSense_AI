/**
 * Builds the JSON payload sent to the /recommend-historical endpoint.
 *
 * The farmer-available-area field is no longer collected from the UI;
 * only the location and soil inputs are forwarded to the backend.
 */
export function buildHistoricalCropWorkflowRequest({
  state,
  district,
  season,
  soil,
}) {
  return {
    state_names: state.trim(),
    district_names: district.trim(),
    season_names: season,
    soil_for_crop: soil,
  };
}
