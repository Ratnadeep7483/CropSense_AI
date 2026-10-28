import type {
  HistoricalAreaRecord,
  HistoricalCropRecordRequest,
} from "./api/cropApi";

export function translateCropName(
  cropName: string,
  language: "en" | "hi",
): string;

export function buildHistoricalCropRecordRequest(
  record: HistoricalAreaRecord & { soil_for_crop: string },
): HistoricalCropRecordRequest;

export const HINDI_CROP_NAMES: Readonly<Record<string, string>>;
