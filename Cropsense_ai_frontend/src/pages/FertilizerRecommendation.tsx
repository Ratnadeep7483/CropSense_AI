import { useState } from "react";
import { Loader2 } from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";
import type { Translations } from "../i18n/en";
import {
  recommendFertilizer,
  type FertilizerRecommendRequest,
} from "../lib/api/fertilizerApi";

type FertilizerForm = Record<keyof FertilizerRecommendRequest, string>;

const EMPTY_FORM: FertilizerForm = {
  temperature: "",
  moisture: "",
  rainfall: "",
  ph: "",
  nitrogen: "",
  phosphorous: "",
  potassium: "",
  carbon: "",
  soil: "",
  crop: "",
};

const NUMERIC_FIELDS = [
  "temperature",
  "moisture",
  "rainfall",
  "ph",
  "nitrogen",
  "phosphorous",
  "potassium",
  "carbon",
] as const satisfies readonly (keyof FertilizerRecommendRequest)[];

const FIELD_LABELS: Record<
  keyof FertilizerRecommendRequest,
  keyof Translations
> = {
  temperature: "fertilizerTemperature",
  moisture: "fertilizerMoisture",
  rainfall: "fertilizerRainfall",
  ph: "fertilizerPh",
  nitrogen: "fertilizerNitrogen",
  phosphorous: "fertilizerPhosphorous",
  potassium: "fertilizerPotassium",
  carbon: "fertilizerCarbon",
  soil: "fertilizerSoil",
  crop: "fertilizerCrop",
};

export default function FertilizerRecommendation() {
  const { t } = useLanguage();
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recommendation, setRecommendation] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);

    const request: FertilizerRecommendRequest = {
      ...form,
      temperature: Number(form.temperature),
      moisture: Number(form.moisture),
      rainfall: Number(form.rainfall),
      ph: Number(form.ph),
      nitrogen: Number(form.nitrogen),
      phosphorous: Number(form.phosphorous),
      potassium: Number(form.potassium),
      carbon: Number(form.carbon),
    };

    try {
      const response = await recommendFertilizer(request);
      setRecommendation(response.recommended_fertilizer);
    } catch (requestError: unknown) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : t.fertilizerRequestFailed,
      );
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "w-full rounded-xl border border-surface-200 bg-white px-4 py-2.5 text-sm text-surface-900 transition-colors focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20";
  const labelClass = "mb-1.5 block text-sm font-medium text-surface-700";

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl">
        <div className="flex flex-col items-center justify-center rounded-2xl border border-surface-200 bg-white p-16">
          <Loader2 className="mb-4 h-10 w-10 animate-spin text-primary-500" />
          <p className="text-lg font-semibold text-surface-800">
            {t.fertilizerLoading}
          </p>
        </div>
      </div>
    );
  }

  if (recommendation) {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 md:text-3xl">
            {t.fertilizerTitle}
          </h1>
          <p className="mt-1 text-surface-500">{t.fertilizerSubtitle}</p>
        </div>
        <div className="rounded-2xl border border-primary-100 bg-gradient-to-br from-primary-50 to-white p-6 shadow-sm">
          <p className="text-sm font-medium text-surface-500">
            {t.fertilizerResultLabel}
          </p>
          <p className="mt-1 text-3xl font-bold text-primary-700">
            {recommendation}
          </p>
        </div>
        <button
          type="button"
          onClick={() => setRecommendation(null)}
          className="inline-flex items-center gap-2 rounded-xl border border-surface-200 bg-white px-5 py-2.5 text-sm font-semibold text-surface-700 shadow-sm transition-all hover:bg-surface-50"
        >
          {t.back}
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-surface-900 md:text-3xl">
          {t.fertilizerTitle}
        </h1>
        <p className="mt-1 text-surface-500">{t.fertilizerSubtitle}</p>
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="rounded-2xl border border-surface-100 bg-white p-6 shadow-sm md:p-8"
      >
        <div className="grid gap-5 md:grid-cols-2">
          {(Object.keys(EMPTY_FORM) as (keyof FertilizerRecommendRequest)[]).map(
            (field) => {
              const numeric = NUMERIC_FIELDS.includes(
                field as (typeof NUMERIC_FIELDS)[number],
              );
              return (
                <div key={field}>
                  <label htmlFor={field} className={labelClass}>
                    {t[FIELD_LABELS[field]]}
                  </label>
                  <input
                    id={field}
                    type={numeric ? "number" : "text"}
                    step={numeric ? "any" : undefined}
                    value={form[field]}
                    onChange={(event) =>
                      setForm((previous) => ({
                        ...previous,
                        [field]: event.target.value,
                      }))
                    }
                    className={inputClass}
                    required
                  />
                </div>
              );
            },
          )}
        </div>
        <button
          type="submit"
          className="mt-6 w-full rounded-xl bg-primary-600 py-3 text-sm font-semibold text-white shadow-sm transition-all hover:-translate-y-0.5 hover:bg-primary-700 md:w-auto md:px-8"
        >
          {t.fertilizerSubmit}
        </button>
      </form>
    </div>
  );
}
