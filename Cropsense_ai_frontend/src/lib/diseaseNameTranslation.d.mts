export type DiseaseLanguage = "en" | "hi";

export const HINDI_DISEASE_NAMES: Readonly<Record<string, string>>;

export function translateDiseaseName(
  diseaseName: string,
  language: DiseaseLanguage,
): string;
