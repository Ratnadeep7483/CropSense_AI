import type {
  HistoricalWeatherResponse,
  NPKLookupResponse,
  RainfallLookupResponse,
} from "./api/cropApi";

export interface KeyedNPKLookup {
  key: string;
  data: NPKLookupResponse;
}

export interface NPKFeatureValues {
  N: number;
  P: number;
  K: number;
  rainfall_mm?: number;
  temperature?: number;
  humidity?: number;
}

export interface KeyedRainfallLookup {
  key: string;
  data: RainfallLookupResponse;
}

export interface RainfallFeatureValue {
  rainfall_mm: number;
}

export interface KeyedHistoricalWeatherLookup {
  key: string;
  data: HistoricalWeatherResponse;
}

export interface HistoricalWeatherFeatureValues {
  temperature: number;
  humidity: number;
}

export type HistoricalWeatherLookupError =
  | "unsupportedLocation"
  | "unavailable"
  | "requestFailed";

export function classifyHistoricalWeatherError(
  status: number | null,
): HistoricalWeatherLookupError {
  if (status === 404 || status === 409) return "unsupportedLocation";
  if (status === 502 || status === 503 || status === 504) {
    return "unavailable";
  }
  return "requestFailed";
}

export function validateHistoricalWeatherLookup(
  lookup: KeyedHistoricalWeatherLookup | null,
  currentKey: string | null,
): HistoricalWeatherFeatureValues | null {
  if (
    !lookup ||
    !currentKey ||
    lookup.key !== currentKey ||
    JSON.stringify([
      lookup.data.location?.state,
      lookup.data.location?.district,
      lookup.data.season,
    ]) !== currentKey ||
    lookup.data.success !== true ||
    lookup.data.period?.season !== lookup.data.season ||
    lookup.data.period?.timezone !== "UTC" ||
    !Array.isArray(lookup.data.period?.season_start_years) ||
    lookup.data.period.season_start_years.length !== 10 ||
    lookup.data.period.season_start_years.some(
      (year, index) => year !== 2010 + index,
    ) ||
    typeof lookup.data.period.start_date !== "string" ||
    !lookup.data.period.start_date.trim() ||
    typeof lookup.data.period.end_date !== "string" ||
    !lookup.data.period.end_date.trim() ||
    lookup.data.units?.temperature_2m !== "°C" ||
    lookup.data.units?.relative_humidity_2m !== "%" ||
    lookup.data.model !== "ERA5" ||
    lookup.data.source !== "Open-Meteo Historical Weather API" ||
    !/historical seasonal average/i.test(lookup.data.label ?? "") ||
    !/not a forecast/i.test(lookup.data.label ?? "") ||
    typeof lookup.data.averages?.temperature_2m !== "number" ||
    !Number.isFinite(lookup.data.averages.temperature_2m) ||
    typeof lookup.data.averages?.relative_humidity_2m !== "number" ||
    !Number.isFinite(lookup.data.averages.relative_humidity_2m)
  ) {
    return null;
  }

  return {
    temperature: lookup.data.averages.temperature_2m,
    humidity: lookup.data.averages.relative_humidity_2m,
  };
}

export function validateRainfallLookup(
  lookup: KeyedRainfallLookup | null,
  currentKey: string | null,
): RainfallFeatureValue | null {
  if (
    !lookup ||
    !currentKey ||
    lookup.key !== currentKey ||
    JSON.stringify([
      lookup.data.state_names,
      lookup.data.district_names,
      lookup.data.season_names,
    ]) !== currentKey ||
    lookup.data.success !== true ||
    typeof lookup.data.rainfall_mm !== "number" ||
    !Number.isFinite(lookup.data.rainfall_mm) ||
    lookup.data.rainfall_mm < 0 ||
    !Number.isInteger(lookup.data.matched_year_count) ||
    lookup.data.matched_year_count < 1 ||
    !Number.isInteger(lookup.data.observed_year_start) ||
    !Number.isInteger(lookup.data.observed_year_end) ||
    lookup.data.observed_year_start > lookup.data.observed_year_end ||
    lookup.data.matched_year_count >
      lookup.data.observed_year_end - lookup.data.observed_year_start + 1 ||
    typeof lookup.data.description !== "string" ||
    !lookup.data.description.trim() ||
    !/unverif/i.test(lookup.data.description)
  ) {
    return null;
  }

  return { rainfall_mm: lookup.data.rainfall_mm };
}

export function assembleNpkFeatureValues(
  lookup: KeyedNPKLookup | null,
  currentKey: string | null,
  rainfallLookup: KeyedRainfallLookup | null = null,
  weatherLookup: KeyedHistoricalWeatherLookup | null = null,
): NPKFeatureValues | null {
  if (
    !lookup ||
    !currentKey ||
    lookup.key !== currentKey ||
    lookup.data.success !== true ||
    !Number.isFinite(lookup.data.N) ||
    !Number.isFinite(lookup.data.P) ||
    !Number.isFinite(lookup.data.K)
  ) {
    return null;
  }

  return {
    N: lookup.data.N,
    P: lookup.data.P,
    K: lookup.data.K,
    ...(validateRainfallLookup(rainfallLookup, currentKey) ?? {}),
    ...(validateHistoricalWeatherLookup(weatherLookup, currentKey) ?? {}),
  };
}
