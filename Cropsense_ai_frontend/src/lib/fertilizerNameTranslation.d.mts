export type FertilizerLanguage = "en" | "hi";

export const HINDI_FERTILIZER_NAMES: Readonly<Record<string, string>>;

export function translateFertilizerName(
  fertilizerName: string,
  language: FertilizerLanguage,
): string;
