import type { HistoricalAreaRecord } from "./api/cropApi";

export const HECTARES_TO_ACRES: number;

export function hectaresToAcres(hectares: number | null): number | null;

export function getHistoricalAreaCropsForSeason(
  records: HistoricalAreaRecord[],
  season: string,
): string[];

export function getLatestHistoricalAreaForCrop(
  records: HistoricalAreaRecord[],
  crop: string,
  season: string,
): {
  crop: string;
  season: string;
  year: number;
  area_hectares: number | null;
  status: "available" | "ambiguous" | "missing";
} | null;

export function getLatestAreaSummaryForSeason(
  records: HistoricalAreaRecord[],
  season: string,
): HistoricalAreaRecord[];

export interface HistoricalAreaDropdownOption {
  value: string;
  label: string;
  crop: string;
  year: number;
  area_acres: number | null;
  area_hectares: number | null;
  soil_for_crop: string | null;
  status: "available" | "ambiguous" | "missing";
  selectable: boolean;
  record: HistoricalAreaRecord;
}

export function buildHistoricalAreaDropdownOptions(
  records: HistoricalAreaRecord[],
  season: string,
): HistoricalAreaDropdownOption[];
