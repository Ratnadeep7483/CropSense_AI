export const HECTARES_TO_ACRES = 2.47105381;

export function hectaresToAcres(hectares) {
  if (typeof hectares !== "number" || !Number.isFinite(hectares)) {
    return null;
  }
  return hectares * HECTARES_TO_ACRES;
}

export function getHistoricalAreaCropsForSeason(records, season) {
  return [...new Set(
    records
      .filter((record) => record.season === season)
      .map((record) => record.crop),
  )].sort((left, right) => left.localeCompare(right));
}

export function getLatestHistoricalAreaForCrop(records, crop, season) {
  return records
    .filter(
      (record) => record.crop === crop && record.season === season,
    )
    .reduce(
      (latest, record) =>
        latest === null || record.year > latest.year ? record : latest,
      null,
    );
}

export function getLatestAreaSummaryForSeason(records, season) {
  const crops = getHistoricalAreaCropsForSeason(records, season);
  return crops
    .map((crop) => getLatestHistoricalAreaForCrop(records, crop, season))
    .filter((record) => record !== null);
}

/**
 * Return every exact matching dataset row, preserving unavailable/conflicting
 * values so the UI can explain why a record cannot be used for inference.
 */
export function buildHistoricalAreaDropdownOptions(
  records,
  season,
  labels = {},
) {
  const duplicateKeys = new Map();
  return records
    .filter((record) => record.season === season)
    .map((record) => {
      const area_acres =
        typeof record.area_hectares === "number" &&
        Number.isFinite(record.area_hectares)
          ? hectaresToAcres(record.area_hectares)
          : null;
      const recordKey = JSON.stringify(record);
      const occurrence = duplicateKeys.get(recordKey) ?? 0;
      duplicateKeys.set(recordKey, occurrence + 1);
      return {
        value: JSON.stringify([recordKey, occurrence]),
        label:
          area_acres === null
            ? ""
            : `${area_acres.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })} acres`,
        crop: record.crop,
        year: record.year,
        area_acres,
        area_hectares: record.area_hectares,
        soil_for_crop: record.soil_for_crop,
        status: record.status,
        selectable:
          record.status === "available" &&
          area_acres !== null &&
          typeof record.soil_for_crop === "string" &&
          record.soil_for_crop.trim().length > 0 &&
          typeof record.npk_source === "string" &&
          record.npk_source.trim().length > 0 &&
          Object.keys(record.feature_issues ?? {}).length === 0,
        record,
      };
    })
    .filter(
      (option) =>
        option.area_acres !== null &&
        option.area_acres >= 1 - Number.EPSILON &&
        option.area_acres <= 100 + Number.EPSILON * 100,
    )
    .sort((a, b) => {
      const cropCmp = a.crop.localeCompare(b.crop);
      if (cropCmp !== 0) return cropCmp;
      if (b.year !== a.year) return b.year - a.year;
      return a.value.localeCompare(b.value);
    });
}
