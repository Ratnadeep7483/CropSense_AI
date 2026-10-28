import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";
import type { Translations } from "../i18n/en";
import {
  getYieldOptions,
  predictYield,
  YIELD_FEATURES,
  type YieldFeature,
  type YieldOptionsResponse,
  type YieldPredictionRequest,
  type YieldPredictionResponse,
} from "../lib/api/yieldApi";

type PageState = "form" | "loading" | "result";

const EMPTY_FORM: YieldPredictionRequest = {
  Crop: "",
  State_Name: "",
  District_Name: "",
  Season: "",
};

const FEATURE_LABELS: Record<YieldFeature, keyof Translations> = {
  Crop: "crop",
  State_Name: "yieldState",
  District_Name: "yieldDistrict",
  Season: "yieldSeason",
};

export default function YieldPrediction() {
  const { t } = useLanguage();
  const [state, setState] = useState<PageState>("form");
  const [form, setForm] = useState(EMPTY_FORM);
  const [options, setOptions] = useState<YieldOptionsResponse | null>(null);
  const [result, setResult] = useState<YieldPredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getYieldOptions()
      .then((response) => {
        if (active) setOptions(response);
      })
      .catch((requestError: unknown) => {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Unable to load yield model categories.",
          );
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setState("loading");
    try {
      setResult(await predictYield(form));
      setState("result");
    } catch (requestError: unknown) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Yield prediction failed.",
      );
      setState("form");
    }
  };

  const inputClass =
    "w-full rounded-xl border border-surface-200 bg-white px-4 py-2.5 text-sm text-surface-900 transition-colors focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20";
  const labelClass = "mb-1.5 block text-sm font-medium text-surface-700";

  if (state === "loading") {
    return (
      <div className="mx-auto max-w-3xl">
        <div className="flex flex-col items-center justify-center rounded-2xl border border-surface-200 bg-white p-16">
          <Loader2 className="mb-4 h-10 w-10 animate-spin text-primary-500" />
          <p className="text-lg font-semibold text-surface-800">
            {t.predicting}
          </p>
        </div>
      </div>
    );
  }

  if (state === "result" && result) {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 md:text-3xl">
            {t.yieldTitle}
          </h1>
          <p className="mt-1 text-surface-500">{t.yieldSubtitle}</p>
        </div>
        <div className="rounded-2xl border border-primary-100 bg-gradient-to-br from-primary-50 to-white p-6 shadow-sm">
          <p className="text-sm font-medium text-surface-500">
            {t.yieldPerArea}
          </p>
          <p className="mt-1 text-3xl font-bold text-primary-700">
            {result.predicted_yield_per_area.toFixed(4)}
          </p>
          <p className="mt-2 text-sm text-surface-500">
            {t.yieldModelPeriod}
          </p>
        </div>
        <button
          onClick={() => setState("form")}
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
          {t.yieldTitle}
        </h1>
        <p className="mt-1 text-surface-500">{t.yieldSubtitle}</p>
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
          {YIELD_FEATURES.map((feature) => {
            const categories =
              feature === "District_Name"
                ? (form.State_Name
                    ? options?.districts_by_state[form.State_Name]
                    : undefined) ?? []
                : options?.features[feature] ?? [];

            return (
              <div key={feature}>
                <label htmlFor={feature} className={labelClass}>
                  {t[FEATURE_LABELS[feature]]}
                </label>
                <select
                  id={feature}
                  value={form[feature]}
                  onChange={(event) =>
                    setForm((previous) =>
                      feature === "State_Name"
                        ? {
                            ...previous,
                            State_Name: event.target.value,
                            District_Name: "",
                          }
                        : {
                            ...previous,
                            [feature]: event.target.value,
                          },
                    )
                  }
                  className={inputClass}
                  required
                  disabled={
                    !options ||
                    (feature === "District_Name" && !form.State_Name)
                  }
                >
                  <option value="">
                    {options ? `${t[FEATURE_LABELS[feature]]}...` : t.loading}
                  </option>
                  {categories.map((category) => (
                    <option value={category} key={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </div>
            );
          })}
        </div>
        <button
          type="submit"
          disabled={!options}
          className="mt-6 w-full rounded-xl bg-primary-600 py-3 text-sm font-semibold text-white shadow-sm transition-all hover:bg-primary-700 hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50 md:w-auto md:px-8"
        >
          {t.predictYield}
        </button>
      </form>
    </div>
  );
}
