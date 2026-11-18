export const IRRIGATION_NUMERIC_FEATURES = [
  "Temperature_C",
  "Humidity",
  "Rainfall_mm",
  "Sunlight_Hours",
  "Soil_Moisture",
  "Wind_Speed_kmh",
];

export function buildIrrigationRequest(form) {
  const directFields = [
    "temperature",
    "humidity",
    "rainfall",
    "sunlightHours",
    "soilType",
    "crop",
    "growthStage",
    "season",
    "soilMoisture",
    "windSpeed",
    "mulchingUsed",
  ];
  if (
    directFields.some(
      (name) =>
        typeof form[name] !== "string" || form[name].trim() === "",
    )
  ) {
    throw new Error("Complete all irrigation fields.");
  }
  const request = {
    Temperature_C: Number(form.temperature),
    Humidity: Number(form.humidity),
    Rainfall_mm: Number(form.rainfall),
    Sunlight_Hours: Number(form.sunlightHours),
    Soil_Type: form.soilType,
    Crop_Type: form.crop,
    Crop_Growth_Stage: form.growthStage,
    Season: form.season,
    Soil_Moisture: Number(form.soilMoisture),
    Wind_Speed_kmh: Number(form.windSpeed),
    Mulching_Used: form.mulchingUsed,
  };

  if (Object.values(request).some((value) => value === "")) {
    throw new Error("Complete all irrigation fields.");
  }
  for (const name of IRRIGATION_NUMERIC_FEATURES) {
    if (!Number.isFinite(request[name])) {
      throw new Error(`${name} must be a finite number.`);
    }
  }
  return request;
}

export function buildIrrigationWeatherRequest(form) {
  const requiredStrings = [
    form.state,
    form.district,
    form.soilMoisture,
    form.soilType,
    form.crop,
    form.growthStage,
    form.season,
    form.mulchingUsed,
  ];
  if (requiredStrings.some((value) => typeof value !== "string" || value.trim() === "")) {
    throw new Error("Complete all weather-assisted irrigation fields.");
  }

  const soilMoisture = Number(form.soilMoisture);
  if (!Number.isFinite(soilMoisture)) {
    throw new Error("Soil_Moisture must be a finite number.");
  }

  const request = {
    state: form.state,
    district: form.district,
    Soil_Moisture: soilMoisture,
    Soil_Type: form.soilType,
    Crop_Type: form.crop,
    Crop_Growth_Stage: form.growthStage,
    Season: form.season,
    Mulching_Used: form.mulchingUsed,
  };
  return request;
}

export const IRRIGATION_WEATHER_LIMITATION =
  "Rainfall is one-calendar-day precipitation sum and sunlight is sunshine seconds converted to hours. These periods are not proven compatible with the model's training rainfall/sunlight feature periods.";

export function getIrrigationWeatherSummary(weather) {
  if (!weather || !weather.measurement) {
    throw new Error("Weather summary is unavailable.");
  }
  return {
    source: weather.measurement.source,
    provider: weather.measurement.provider,
    date: weather.measurement.date,
    timezone: weather.measurement.timezone,
    Temperature_C: `${Number(weather.Temperature_C).toFixed(2)} °C`,
    Humidity: `${Number(weather.Humidity).toFixed(2)} %`,
    Rainfall_mm: `${Number(weather.Rainfall_mm).toFixed(2)} mm`,
    Sunlight_Hours: `${Number(weather.Sunlight_Hours).toFixed(2)} hours`,
    Wind_Speed_kmh: `${Number(weather.Wind_Speed_kmh).toFixed(2)} km/h`,
    Soil_Moisture: "farmer-entered",
    warning: IRRIGATION_WEATHER_LIMITATION,
  };
}
