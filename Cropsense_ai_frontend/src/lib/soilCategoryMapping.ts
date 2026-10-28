const soilCategoryMapping = {
  Alluvial_Soil: "Alluvial",
  Arid_Soil: "Arid (Desert)",
  Black_Soil: "Black",
  Laterite_Soil: "Laterite",
  Mountain_Soil: "Mountain (Forest)",
  Red_Soil: "Red",
} as const;

export type CropSoilCategory =
  (typeof soilCategoryMapping)[keyof typeof soilCategoryMapping];

function isSoilClassifierLabel(
  label: string,
): label is keyof typeof soilCategoryMapping {
  return Object.prototype.hasOwnProperty.call(soilCategoryMapping, label);
}

export function mapSoilClassToCropCategory(
  label: unknown,
): CropSoilCategory | null {
  if (typeof label !== "string" || !isSoilClassifierLabel(label)) {
    return null;
  }

  return soilCategoryMapping[label];
}
