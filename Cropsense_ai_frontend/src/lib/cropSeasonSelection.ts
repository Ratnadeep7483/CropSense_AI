import cropSeasons from "../data/cropSeasons.json" with { type: "json" };

export const cropSeasonCategories = cropSeasons.map(({ name }) => name);

export type CropSeason = (typeof cropSeasonCategories)[number];

export function parseCropSeason(value: string): CropSeason | null {
  return cropSeasonCategories.find((season) => season === value) ?? null;
}

/** No verified month-to-season rules exist, so valid months remain unassigned. */
export function inferCropSeasonFromMonth(month: number): null {
  if (!Number.isInteger(month) || month < 1 || month > 12) {
    throw new RangeError("Month must be an integer from 1 to 12.");
  }

  return null;
}
