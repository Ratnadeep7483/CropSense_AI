import { useEffect, useState } from "react";
import { Loader2, Droplets, AlertCircle } from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";
import { translateCropName } from "../lib/cropNameTranslation.mjs";
import {
  predictIrrigation,
  predictIrrigationFromWeather,
  type IrrigationPredictionResponse,
} from "../lib/api/irrigationApi";
import {
  buildIrrigationRequest,
  buildIrrigationWeatherRequest,
  getIrrigationWeatherSummary,
} from "../lib/irrigationRequest.mjs";
import { lookupCropLocationOptions } from "../lib/api/cropApi";

type PageState = "form" | "loading" | "result" | "error";
type PredictionMode = "direct" | "weather";

export default function Irrigation() {
  const { t, language } = useLanguage();
  const [state, setState] = useState<PageState>("form");
  const [result, setResult] =
    useState<IrrigationPredictionResponse | null>(null);
  const [mode, setMode] = useState<PredictionMode>("direct");
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    crop: "",
    soilType: "",
    growthStage: "",
    season: "",
    mulchingUsed: "",
    temperature: "",
    humidity: "",
    rainfall: "",
    sunlightHours: "",
    soilMoisture: "",
    windSpeed: "",
    state: "",
    district: "",
  });
  const [states, setStates] = useState<string[]>([]);
  const [districts, setDistricts] = useState<string[]>([]);
  const [locationsLoading, setLocationsLoading] = useState(false);
  const [locationsError, setLocationsError] = useState("");

  useEffect(() => {
    let active = true;
    setLocationsLoading(true);
    setLocationsError("");
    void lookupCropLocationOptions()
      .then((response) => {
        if (active) setStates(response.states);
      })
      .catch((locationError: unknown) => {
        if (active) {
          setLocationsError(
            locationError instanceof Error
              ? locationError.message
              : "Unable to load state options.",
          );
        }
      })
      .finally(() => {
        if (active) setLocationsLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!form.state) {
      setDistricts([]);
      return;
    }
    let active = true;
    setLocationsLoading(true);
    setLocationsError("");
    void lookupCropLocationOptions({ state_names: form.state })
      .then((response) => {
        if (active) setDistricts(response.districts);
      })
      .catch((locationError: unknown) => {
        if (active) {
          setDistricts([]);
          setLocationsError(
            locationError instanceof Error
              ? locationError.message
              : "Unable to load district options.",
          );
        }
      })
      .finally(() => {
        if (active) setLocationsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [form.state]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setState("loading");
    setError("");
    try {
      const prediction =
        mode === "weather"
          ? await predictIrrigationFromWeather(
              buildIrrigationWeatherRequest(form),
            )
          : await predictIrrigation(buildIrrigationRequest(form));
      setResult(prediction);
      setState("result");
    } catch (submitError: unknown) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Unable to get an irrigation prediction.",
      );
      setState("error");
    }
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

  if (state === "error") {
    return (
      <div className="mx-auto w-full min-w-0 max-w-3xl space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 md:text-3xl">
            {t.irrigationTitle}
          </h1>
        </div>
        <div className="w-full min-w-0 rounded-2xl border border-red-200 bg-red-50 p-4 sm:p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
            <p className="min-w-0 break-words text-sm text-red-700">{error}</p>
          </div>
        </div>
        <button
          onClick={() => setState("form")}
          className="inline-flex rounded-xl border border-surface-200 bg-white px-5 py-2.5 text-sm font-semibold text-surface-700"
        >
          {t.back}
        </button>
      </div>
    );
  }

  if (state === "result" && result) {
    const weatherSummary = result.weather
      ? getIrrigationWeatherSummary(result.weather)
      : null;
    return (
      <div className="mx-auto w-full min-w-0 max-w-3xl space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 md:text-3xl">
            {t.irrigationTitle}
          </h1>
          <p className="mt-1 text-surface-500">{t.irrigationSubtitle}</p>
        </div>

        {/* Recommendation Card */}
        <div
          className={`w-full min-w-0 rounded-2xl border-2 p-4 shadow-sm sm:p-8 ${
            result.prediction === "High"
              ? "border-blue-200 bg-gradient-to-br from-blue-50 to-white"
              : "border-amber-200 bg-gradient-to-br from-amber-50 to-white"
          }`}
        >
          <div className="mb-4 flex items-center gap-3">
            <div
              className={`rounded-xl p-3 ${
                result.prediction === "High" ? "bg-blue-100" : "bg-amber-100"
              }`}
            >
              <Droplets
                className={`h-7 w-7 ${
                  result.prediction === "High" ? "text-blue-600" : "text-amber-600"
                }`}
              />
            </div>
            <div>
              <p className="text-sm font-medium text-surface-500">
                {t.irrigationRecommendation}
              </p>
              <p
                className={`text-2xl font-bold ${
                  result.prediction === "High" ? "text-blue-700" : "text-amber-700"
                }`}
              >
                {result.prediction}
              </p>
            </div>
          </div>
        </div>

        {result.weather && (
          <div className="rounded-xl border border-sky-200 bg-sky-50 p-4">
            <p className="break-words text-sm font-semibold text-surface-800">
              {language === "hi" ? "मौसम इनपुट" : "Weather inputs"}
            </p>
            <p className="mt-1 text-xs text-surface-600">
              {weatherSummary?.source} · {weatherSummary?.provider} ·{" "}
              {weatherSummary?.date} · {weatherSummary?.timezone}
            </p>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              <p className="text-sm">Temperature: {weatherSummary?.Temperature_C}</p>
              <p className="text-sm">Humidity: {weatherSummary?.Humidity}</p>
              <p className="text-sm">Rainfall: {weatherSummary?.Rainfall_mm}</p>
              <p className="text-sm">Sunlight: {weatherSummary?.Sunlight_Hours}</p>
              <p className="text-sm">Wind: {weatherSummary?.Wind_Speed_kmh}</p>
              <p className="text-sm">Soil moisture: {weatherSummary?.Soil_Moisture}, not mapped from weather</p>
            </div>
          </div>
        )}

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
    <div className="mx-auto w-full min-w-0 max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-surface-900 md:text-3xl">
          {t.irrigationTitle}
        </h1>
        <p className="mt-1 text-surface-500">{t.irrigationSubtitle}</p>
      </div>

      <div className="flex w-full min-w-0 rounded-xl border border-surface-200 bg-white p-1">
        <button
          type="button"
          onClick={() => setMode("direct")}
          className={`min-w-0 flex-1 whitespace-nowrap rounded-lg px-2 py-2 text-sm font-semibold sm:px-4 ${
            mode === "direct"
              ? "bg-primary-600 text-white"
              : "text-surface-600"
          }`}
        >
          {language === "hi" ? "सीधा इनपुट" : "Direct input"}
        </button>
        <button
          type="button"
          onClick={() => setMode("weather")}
          className={`min-w-0 flex-1 whitespace-nowrap rounded-lg px-2 py-2 text-sm font-semibold sm:px-4 ${
            mode === "weather"
              ? "bg-primary-600 text-white"
              : "text-surface-600"
          }`}
        >
          {language === "hi" ? "मौसम सहायता" : "Weather-assisted"}
        </button>
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
              <option value="">Select crop</option>
              <option value="Cotton">{translateCropName("Cotton", language)}</option>
              <option value="Maize">{translateCropName("Maize", language)}</option>
              <option value="Potato">{translateCropName("Potato", language)}</option>
              <option value="Rice">{translateCropName("Rice", language)}</option>
              <option value="Sugarcane">{translateCropName("Sugarcane", language)}</option>
              <option value="Wheat">{translateCropName("Wheat", language)}</option>
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
              <option value="">Select soil type</option>
              <option value="Clay">{t.soilClay}</option>
              <option value="Loamy">{t.soilLoamy}</option>
              <option value="Sandy">{t.soilSandy}</option>
              <option value="Silt">{language === "hi" ? "सिल्ट" : "Silt"}</option>
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
              <option value="">Select growth stage</option>
              <option value="Flowering">{language === "hi" ? "फूलन" : "Flowering"}</option>
              <option value="Harvest">{language === "hi" ? "कटाई" : "Harvest"}</option>
              <option value="Sowing">{language === "hi" ? "बुवाई" : "Sowing"}</option>
              <option value="Vegetative">{t.stageVegetative}</option>
            </select>
          </div>
          <div>
            <label className={labelClass}>{t.seasonName}</label>
            <select
              value={form.season}
              onChange={(e) => setForm({ ...form, season: e.target.value })}
              className={inputClass}
              required
            >
              <option value="">Select season</option>
              <option value="Kharif">Kharif</option>
              <option value="Rabi">Rabi</option>
              <option value="Zaid">Zaid</option>
            </select>
          </div>
          <div>
            <label className={labelClass}>{language === "hi" ? "मल्चिंग" : "Mulching Used"}</label>
            <select
              value={form.mulchingUsed}
              onChange={(e) => setForm({ ...form, mulchingUsed: e.target.value })}
              className={inputClass}
              required
            >
              <option value="">Select mulching option</option>
              <option value="No">{language === "hi" ? "नहीं" : "No"}</option>
              <option value="Yes">{language === "hi" ? "हाँ" : "Yes"}</option>
            </select>
          </div>
          {mode === "weather" && (
            <>
              <div>
                <label className={labelClass}>{language === "hi" ? "राज्य" : "State"}</label>
                <select
                  value={form.state}
                  onChange={(e) =>
                    setForm({ ...form, state: e.target.value, district: "" })
                  }
                  className={inputClass}
                  required
                  disabled={locationsLoading}
                >
                  <option value="">Select state</option>
                  {states.map((state) => (
                    <option key={state} value={state}>{state}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className={labelClass}>{language === "hi" ? "जिला" : "District"}</label>
                <select
                  value={form.district}
                  onChange={(e) =>
                    setForm({ ...form, district: e.target.value })
                  }
                  className={inputClass}
                  required
                  disabled={!form.state || locationsLoading}
                >
                  <option value="">Select district</option>
                  {districts.map((district) => (
                    <option key={district} value={district}>{district}</option>
                  ))}
                </select>
              </div>
              {locationsError && (
                <p className="text-xs text-red-600 md:col-span-2">{locationsError}</p>
              )}
            </>
          )}
          {mode === "direct" && (
            <>
          <div>
            <label className={labelClass}>{t.temperatureField}</label>
            <input
              type="number"
              step="any"
              value={form.temperature}
              onChange={(e) =>
                setForm({ ...form, temperature: e.target.value })
              }
              className={inputClass}
              placeholder={language === "hi" ? "तापमान दर्ज करें" : "Enter temperature in °C"}
              required
            />
          </div>
            </>
          )}
          {mode === "direct" && (
            <>
          <div>
            <label className={labelClass}>{t.humidityField}</label>
            <input
              type="number"
              step="any"
              value={form.humidity}
              onChange={(e) => setForm({ ...form, humidity: e.target.value })}
              className={inputClass}
              placeholder={language === "hi" ? "आर्द्रता दर्ज करें" : "Enter humidity %"}
              required
            />
          </div>
            </>
          )}
          {mode === "direct" && (
            <>
          <div>
            <label className={labelClass}>{t.rainfallField}</label>
            <input
              type="number"
              step="any"
              value={form.rainfall}
              onChange={(e) =>
                setForm({ ...form, rainfall: e.target.value })
              }
              className={inputClass}
              placeholder={language === "hi" ? "वर्षा दर्ज करें" : "Enter rainfall in mm"}
              required
            />
          </div>
          <div>
            <label className={labelClass}>
              {language === "hi" ? "धूप के घंटे" : "Sunlight Hours"}
            </label>
            <input
              type="number"
              step="any"
              value={form.sunlightHours}
              onChange={(e) =>
                setForm({ ...form, sunlightHours: e.target.value })
              }
              className={inputClass}
              placeholder={language === "hi" ? "धूप के घंटे दर्ज करें" : "Enter sunlight hours"}
              required
            />
          </div>
          </>
          )}
          <div>
          <label className={labelClass}>
            {language === "hi" ? "मृदा नमी (किसान दर्ज)" : "Soil Moisture (farmer-entered)"}
          </label>
          <input
            type="number"
            step="any"
            value={form.soilMoisture}
            onChange={(e) =>
              setForm({ ...form, soilMoisture: e.target.value })
            }
            className={inputClass}
            placeholder={language === "hi" ? "मृदा नमी दर्ज करें" : "Enter soil moisture"}
            required
          />
          </div>
          {mode === "direct" && (
            <>
          <div>
            <label className={labelClass}>
              {language === "hi" ? "पवन गति (km/h)" : "Wind Speed (km/h)"}
            </label>
            <input
              type="number"
                step="any"
              value={form.windSpeed}
              onChange={(e) =>
                setForm({ ...form, windSpeed: e.target.value })
              }
              className={inputClass}
                placeholder={language === "hi" ? "पवन गति दर्ज करें" : "Enter wind speed in km/h"}
              required
            />
          </div>
            </>
          )}
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
