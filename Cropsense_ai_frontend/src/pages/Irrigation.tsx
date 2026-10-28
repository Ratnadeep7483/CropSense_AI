import { useState } from "react";
import { Loader2, Droplets, CloudRain, Clock, AlertCircle } from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";
import { translateCropName } from "../lib/cropNameTranslation.mjs";
import { mockIrrigationResult } from "../data/mockData";

type PageState = "form" | "loading" | "result";

export default function Irrigation() {
  const { t, language } = useLanguage();
  const [state, setState] = useState<PageState>("form");
  const [form, setForm] = useState({
    crop: "",
    soilType: "",
    growthStage: "",
    temperature: "29",
    humidity: "68",
    rainProbability: "75",
    expectedRainfall: "12",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setState("loading");
    setTimeout(() => setState("result"), 1000);
  };

  const inputClass =
    "w-full rounded-xl border border-surface-200 bg-white px-4 py-2.5 text-sm text-surface-900 placeholder-surface-400 transition-colors focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20";
  const labelClass = "mb-1.5 block text-sm font-medium text-surface-700";

  if (state === "loading") {
    return (
      <div className="mx-auto max-w-3xl">
        <div className="flex flex-col items-center justify-center rounded-2xl border border-surface-200 bg-white p-16">
          <Loader2 className="mb-4 h-10 w-10 animate-spin text-blue-500" />
          <p className="text-lg font-semibold text-surface-800">
            {t.checking}
          </p>
        </div>
      </div>
    );
  }

  if (state === "result") {
    const result = mockIrrigationResult;
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 md:text-3xl">
            {t.irrigationTitle}
          </h1>
          <p className="mt-1 text-surface-500">{t.irrigationSubtitle}</p>
        </div>

        {/* Recommendation Card */}
        <div
          className={`rounded-2xl border-2 p-8 shadow-sm ${
            result.shouldIrrigate
              ? "border-blue-200 bg-gradient-to-br from-blue-50 to-white"
              : "border-amber-200 bg-gradient-to-br from-amber-50 to-white"
          }`}
        >
          <div className="mb-4 flex items-center gap-3">
            <div
              className={`rounded-xl p-3 ${
                result.shouldIrrigate ? "bg-blue-100" : "bg-amber-100"
              }`}
            >
              <Droplets
                className={`h-7 w-7 ${
                  result.shouldIrrigate
                    ? "text-blue-600"
                    : "text-amber-600"
                }`}
              />
            </div>
            <div>
              <p className="text-sm font-medium text-surface-500">
                {t.irrigationRecommendation}
              </p>
              <p
                className={`text-2xl font-bold ${
                  result.shouldIrrigate
                    ? "text-blue-700"
                    : "text-amber-700"
                }`}
              >
                {result.shouldIrrigate ? t.irrigateToday : t.doNotIrrigate}
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-start gap-3 rounded-xl bg-white/70 p-4 backdrop-blur">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-surface-400" />
              <div>
                <p className="text-sm font-medium text-surface-700">
                  {t.reason}
                </p>
                <p className="text-sm text-surface-600">{result.reason}</p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-xl bg-white/70 p-4 backdrop-blur">
              <Clock className="mt-0.5 h-5 w-5 shrink-0 text-surface-400" />
              <div>
                <p className="text-sm font-medium text-surface-700">
                  {t.nextRecommendation}
                </p>
                <p className="text-sm text-surface-600">{result.nextTime}</p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-xl bg-white/70 p-4 backdrop-blur">
              <CloudRain className="mt-0.5 h-5 w-5 shrink-0 text-surface-400" />
              <div>
                <p className="text-sm font-medium text-surface-700">
                  {t.expectedRainfall}
                </p>
                <p className="text-sm text-surface-600">
                  {form.expectedRainfall} mm
                </p>
              </div>
            </div>
          </div>
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
          {t.irrigationTitle}
        </h1>
        <p className="mt-1 text-surface-500">{t.irrigationSubtitle}</p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="rounded-2xl border border-surface-100 bg-white p-6 shadow-sm md:p-8"
      >
        <div className="grid gap-5 md:grid-cols-2">
          <div>
            <label className={labelClass}>{t.crop}</label>
            <select
              value={form.crop}
              onChange={(e) => setForm({ ...form, crop: e.target.value })}
              className={inputClass}
              required
            >
              <option value="">{t.crop}...</option>
              <option value="tomato">{translateCropName("Tomato", language)}</option>
              <option value="maize">{translateCropName("Maize", language)}</option>
              <option value="rice">{translateCropName("Rice", language)}</option>
              <option value="wheat">{translateCropName("Wheat", language)}</option>
            </select>
          </div>
          <div>
            <label className={labelClass}>{t.soilType}</label>
            <select
              value={form.soilType}
              onChange={(e) => setForm({ ...form, soilType: e.target.value })}
              className={inputClass}
              required
            >
              <option value="">{t.soilType}...</option>
              <option value="loamy">{t.soilLoamy}</option>
              <option value="clay">{t.soilClay}</option>
              <option value="sandy">{t.soilSandy}</option>
              <option value="black">{t.soilBlack}</option>
            </select>
          </div>
          <div className="md:col-span-2">
            <label className={labelClass}>{t.growthStage}</label>
            <select
              value={form.growthStage}
              onChange={(e) =>
                setForm({ ...form, growthStage: e.target.value })
              }
              className={inputClass}
              required
            >
              <option value="">{t.growthStage}...</option>
              <option value="seedling">{t.stageSeedling}</option>
              <option value="vegetative">{t.stageVegetative}</option>
              <option value="flowering">{t.stageFlowering}</option>
              <option value="fruiting">{t.stageFruiting}</option>
              <option value="harvest">{t.stageHarvest}</option>
            </select>
          </div>
          <div>
            <label className={labelClass}>{t.temperatureField}</label>
            <input
              type="number"
              value={form.temperature}
              onChange={(e) =>
                setForm({ ...form, temperature: e.target.value })
              }
              className={inputClass}
              required
            />
          </div>
          <div>
            <label className={labelClass}>{t.humidityField}</label>
            <input
              type="number"
              value={form.humidity}
              onChange={(e) => setForm({ ...form, humidity: e.target.value })}
              className={inputClass}
              required
            />
          </div>
          <div>
            <label className={labelClass}>{t.rainProbability}</label>
            <input
              type="number"
              value={form.rainProbability}
              onChange={(e) =>
                setForm({ ...form, rainProbability: e.target.value })
              }
              className={inputClass}
              required
            />
          </div>
          <div>
            <label className={labelClass}>{t.expectedRainfall}</label>
            <input
              type="number"
              value={form.expectedRainfall}
              onChange={(e) =>
                setForm({ ...form, expectedRainfall: e.target.value })
              }
              className={inputClass}
              required
            />
          </div>
        </div>
        <button
          type="submit"
          className="mt-6 w-full rounded-xl bg-primary-600 py-3 text-sm font-semibold text-white shadow-sm transition-all hover:bg-primary-700 hover:-translate-y-0.5 md:w-auto md:px-8"
        >
          {t.checkIrrigation}
        </button>
      </form>
    </div>
  );
}
