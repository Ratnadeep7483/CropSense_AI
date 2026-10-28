import { useEffect, useState } from "react";
import { CheckCircle2, Loader2 } from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";
import { predictSoil, type SoilPredictResponse } from "../lib/api/soilApi";
import {
  lookupCropLocationOptions,
  lookupHistoricalArea,
  recommendCropFromHistoricalRecord,
  type HistoricalAreaRecord,
  type HistoricalCropRecordRecommendationResponse,
} from "../lib/api/cropApi";
import { ApiHttpError } from "../lib/api/client";
import {
  buildHistoricalAreaDropdownOptions,
} from "../lib/historicalAreaSelection.mjs";
import {
  buildHistoricalCropRecordRequest,
  translateCropName,
} from "../lib/cropNameTranslation.mjs";

type PageState = "form" | "loading" | "result" | "error";
type AreaState = "idle" | "loading" | "loaded" | "error";
type SoilPredictionState = "idle" | "loading" | "loaded" | "error";
const MAX_SOIL_IMAGE_SIZE = 10 * 1024 * 1024;

export default function CropRecommendation() {
  const { t, language } = useLanguage();
  const [pageState, setPageState] = useState<PageState>("form");
  const [states, setStates] = useState<string[]>([]);
  const [districts, setDistricts] = useState<string[]>([]);
  const [seasons, setSeasons] = useState<string[]>([]);
  const [statesLoading, setStatesLoading] = useState(true);
  const [districtsLoading, setDistrictsLoading] = useState(false);
  const [seasonsLoading, setSeasonsLoading] = useState(false);
  const [locationsError, setLocationsError] = useState("");
  const [records, setRecords] = useState<HistoricalAreaRecord[]>([]);
  const [areaState, setAreaState] = useState<AreaState>("idle");
  const [selectedRecordKey, setSelectedRecordKey] = useState("");
  const [selection, setSelection] = useState({
    state_names: "",
    district_names: "",
    season_names: "",
  });
  const [prediction, setPrediction] =
    useState<HistoricalCropRecordRecommendationResponse | null>(null);
  const [requestError, setRequestError] = useState("");
  const [soilImageUrl, setSoilImageUrl] = useState("");
  const [soilImageFile, setSoilImageFile] = useState<File | null>(null);
  const [soilPrediction, setSoilPrediction] =
    useState<SoilPredictResponse | null>(null);
  const [soilPredictionState, setSoilPredictionState] =
    useState<SoilPredictionState>("idle");
  const [soilImageError, setSoilImageError] = useState("");

  useEffect(() => {
    return () => {
      if (soilImageUrl) URL.revokeObjectURL(soilImageUrl);
    };
  }, [soilImageUrl]);

  useEffect(() => {
    let active = true;
    setStatesLoading(true);
    setLocationsError("");
    void lookupCropLocationOptions()
      .then((response) => {
        if (active) setStates(response.states);
      })
      .catch((error: unknown) => {
        if (active) {
          setLocationsError(
            error instanceof Error ? error.message : t.cropLocationOptionsFailed,
          );
        }
      })
      .finally(() => {
        if (active) setStatesLoading(false);
      });
    return () => {
      active = false;
    };
  }, [t.cropLocationOptionsFailed]);

  useEffect(() => {
    if (!selection.state_names) {
      setDistricts([]);
      setDistrictsLoading(false);
      return;
    }

    let active = true;
    setDistricts([]);
    setDistrictsLoading(true);
    setLocationsError("");
    void lookupCropLocationOptions({ state_names: selection.state_names })
      .then((response) => {
        if (active) setDistricts(response.districts);
      })
      .catch((error: unknown) => {
        if (active) {
          setLocationsError(
            error instanceof Error ? error.message : t.cropLocationOptionsFailed,
          );
        }
      })
      .finally(() => {
        if (active) setDistrictsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [selection.state_names, t.cropLocationOptionsFailed]);

  useEffect(() => {
    if (!selection.state_names || !selection.district_names) {
      setSeasons([]);
      setSeasonsLoading(false);
      return;
    }

    let active = true;
    setSeasons([]);
    setSeasonsLoading(true);
    setLocationsError("");
    void lookupCropLocationOptions({
      state_names: selection.state_names,
      district_names: selection.district_names,
    })
      .then((response) => {
        if (active) setSeasons(response.seasons);
      })
      .catch((error: unknown) => {
        if (active) {
          setLocationsError(
            error instanceof Error ? error.message : t.cropLocationOptionsFailed,
          );
        }
      })
      .finally(() => {
        if (active) setSeasonsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [
    selection.district_names,
    selection.state_names,
    t.cropLocationOptionsFailed,
  ]);

  useEffect(() => {
    if (
      !selection.state_names ||
      !selection.district_names ||
      !selection.season_names
    ) {
      setRecords([]);
      setAreaState("idle");
      return;
    }

    let active = true;
    setRecords([]);
    setSelectedRecordKey("");
    setAreaState("loading");
    void lookupHistoricalArea({
      state_names: selection.state_names,
      district_names: selection.district_names,
      season_names: selection.season_names,
    })
      .then((response) => {
        if (!active) return;
        setRecords(response.records);
        setAreaState("loaded");
      })
      .catch(() => {
        if (active) setAreaState("error");
      });
    return () => {
      active = false;
    };
  }, [
    selection.district_names,
    selection.season_names,
    selection.state_names,
  ]);

  const areaOptions = buildHistoricalAreaDropdownOptions(
    records,
    selection.season_names,
  );
  const selectedOption =
    areaOptions.find((option) => option.value === selectedRecordKey) ?? null;
  const selectedRecord = selectedOption?.record ?? null;
  const canSubmit = Boolean(
    selectedOption?.selectable &&
      selectedRecord?.soil_for_crop &&
      selectedRecord.npk_source,
  );
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedRecord || !canSubmit || pageState === "loading") return;
    const soil = selectedRecord.soil_for_crop;
    if (!soil) return;

    setPageState("loading");
    setRequestError("");
    try {
      const response = await recommendCropFromHistoricalRecord(
        buildHistoricalCropRecordRequest({
          ...selectedRecord,
          soil_for_crop: soil,
        }),
      );
      setPrediction(response);
      setPageState("result");
    } catch (error: unknown) {
      setRequestError(
        error instanceof Error ? error.message : t.apiErrorMessage,
      );
      setPageState("error");
    }
  };

  const handleSoilImageChange = (file: File | undefined) => {
    setSoilImageError("");
    setSoilPrediction(null);
    setSoilPredictionState("idle");
    setSoilImageFile(null);
    if (soilImageUrl) setSoilImageUrl("");
    if (!file) return;
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setSoilImageError(t.invalidSoilImage);
      return;
    }
    if (file.size > MAX_SOIL_IMAGE_SIZE) {
      setSoilImageError(t.soilImageTooLarge);
      return;
    }
    setSoilImageFile(file);
    setSoilImageUrl(URL.createObjectURL(file));
  };

  const handleSoilImagePrediction = async () => {
    if (!soilImageFile || soilPredictionState === "loading") return;
    setSoilPredictionState("loading");
    setSoilImageError("");
    try {
      setSoilPrediction(await predictSoil(soilImageFile));
      setSoilPredictionState("loaded");
    } catch (error: unknown) {
      setSoilPredictionState("error");
      setSoilImageError(
        error instanceof Error ? error.message : t.soilBackendError,
      );
    }
  };

  const inputClass =
    "w-full rounded-xl border border-surface-200 bg-white px-4 py-2.5 text-sm text-surface-900 transition-colors focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 disabled:bg-surface-100";
  const labelClass = "mb-1.5 block text-sm font-medium text-surface-700";

  if (pageState === "loading") {
    return (
      <div className="mx-auto max-w-3xl">
        <div className="flex flex-col items-center justify-center rounded-2xl border border-surface-200 bg-white p-16">
          <Loader2 className="mb-4 h-10 w-10 animate-spin text-primary-500" />
          <p className="text-lg font-semibold text-surface-800">{t.computing}</p>
        </div>
      </div>
    );
  }

  if (pageState === "result" && prediction) {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <header>
          <h1 className="text-2xl font-bold text-surface-900 md:text-3xl">
            {t.datasetPredictionTitle}
          </h1>
          <p className="mt-1 text-surface-500">{t.cropResultSubtitle}</p>
        </header>
        <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-6">
          <div className="flex items-start gap-4">
            <CheckCircle2 className="h-7 w-7 shrink-0 text-emerald-700" />
            <div>
              <p className="text-sm font-medium text-emerald-800">
                {prediction.model_inputs.state_names} ·{" "}
                {prediction.model_inputs.district_names} ·{" "}
                {prediction.model_inputs.season_names}
              </p>
              <h2 className="mt-1 text-2xl font-bold text-emerald-950">
                {translateCropName(prediction.predicted_crop, language)}
              </h2>
            </div>
          </div>
        </section>
        <button
          type="button"
          onClick={() => setPageState("form")}
          className="rounded-xl border border-surface-200 bg-white px-5 py-2.5 text-sm font-semibold text-surface-700 hover:bg-surface-50"
        >
          {t.back}
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-surface-900 md:text-3xl">
          {t.cropRecTitle}
        </h1>
        <p className="mt-1 text-surface-500">{t.cropRecSubtitle}</p>
        <p className="mt-2 text-sm text-surface-500">{t.datasetSelectionHelp}</p>
      </header>

      {pageState === "error" && (
        <div
          className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"
          role="alert"
        >
          {requestError}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="space-y-6 rounded-2xl border border-surface-100 bg-white p-6 shadow-sm md:p-8"
      >
        <div className="grid gap-5 md:grid-cols-2">
          <div>
            <label className={labelClass} htmlFor="crop-state">
              {t.stateName}
            </label>
            <select
              id="crop-state"
              className={inputClass}
              value={selection.state_names}
              disabled={statesLoading}
              required
              onChange={(event) => {
                setSelection({
                  state_names: event.target.value,
                  district_names: "",
                  season_names: "",
                });
                setDistricts([]);
                setSeasons([]);
                setSelectedRecordKey("");
                setRecords([]);
                setAreaState("idle");
                setPrediction(null);
              }}
            >
              <option value="">{t.stateName}...</option>
              {states.map((stateName) => (
                <option key={stateName} value={stateName}>
                  {stateName}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass} htmlFor="crop-district">
              {t.districtName}
            </label>
            <select
              id="crop-district"
              className={inputClass}
              value={selection.district_names}
              disabled={!selection.state_names || districtsLoading}
              required
              onChange={(event) => {
                setSelection((current) => ({
                  ...current,
                  district_names: event.target.value,
                  season_names: "",
                }));
                setSeasons([]);
                setSelectedRecordKey("");
                setRecords([]);
                setAreaState("idle");
              }}
            >
              <option value="">{t.districtName}...</option>
              {districts.map((district) => (
                <option key={district} value={district}>
                  {district}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass} htmlFor="crop-season">
              {t.seasonName}
            </label>
            <select
              id="crop-season"
              className={inputClass}
              value={selection.season_names}
              disabled={
                !selection.district_names || seasonsLoading || seasons.length === 0
              }
              required
              onChange={(event) => {
                setSelection((current) => ({
                  ...current,
                  season_names: event.target.value,
                }));
                setSelectedRecordKey("");
                setRecords([]);
                setAreaState("idle");
              }}
            >
              <option value="">{t.seasonName}...</option>
              {seasons.map((season) => (
                <option key={season} value={season}>
                  {season}
                </option>
              ))}
            </select>
          </div>
        </div>

        {locationsError && (
          <p className="text-sm text-red-700" role="alert">
            {locationsError}
          </p>
        )}

        <section className="rounded-xl border border-surface-200 bg-surface-50 p-4">
          <h2 className="font-semibold text-surface-800">
            {t.historicalAreaTitle}
          </h2>
          <p className="mt-1 text-sm text-surface-600">
            {t.historicalAreaDescription}
          </p>
          {!selection.district_names && (
            <p className="mt-2 text-sm text-surface-600">{t.historicalAreaPrompt}</p>
          )}
          {selection.district_names && !selection.season_names && (
            <p className="mt-2 text-sm text-surface-600">
              {t.historicalAreaSelectSeasonPrompt}
            </p>
          )}
          {areaState === "loading" && (
            <p className="mt-3 flex items-center gap-2 text-sm text-surface-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              {t.historicalAreaLoading}
            </p>
          )}
          {areaState === "error" && (
            <p className="mt-3 text-sm text-red-700" role="alert">
              {t.historicalAreaUnavailable}
            </p>
          )}
          {areaState === "loaded" && areaOptions.length === 0 && (
            <p className="mt-3 text-sm text-surface-600" role="status">
              {t.historicalAreaNoSeasonRecords.replace(
                "{season}",
                selection.season_names,
              )}
            </p>
          )}
          {areaState === "loaded" && areaOptions.length > 0 && (
            <div className="mt-3">
              <label className={labelClass} htmlFor="historical-area-select">
                {t.historicalAreaTitle}
              </label>
              <select
                id="historical-area-select"
                className={inputClass}
                value={selectedRecordKey}
                required
                onChange={(event) => setSelectedRecordKey(event.target.value)}
              >
                <option value="">{t.historicalAreaChooseRecord}</option>
                {areaOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          )}
        </section>

        <section className="space-y-4 rounded-xl border border-surface-200 bg-white p-4">
          <div>
            <h2 className="font-semibold text-surface-800">{t.soilImage}</h2>
            <p className="mt-1 text-sm text-surface-600">
              {t.soilImagePreviewOnly}
            </p>
          </div>
          <label className={labelClass} htmlFor="crop-soil-image">
            {t.soilImage}
          </label>
          <input
            id="crop-soil-image"
            className={inputClass}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            disabled={soilPredictionState === "loading"}
            onChange={(event) =>
              handleSoilImageChange(event.target.files?.[0])
            }
          />
          {soilImageUrl && (
            <img
              src={soilImageUrl}
              alt={t.soilImagePreviewAlt}
              className="max-h-64 rounded-xl border border-surface-200 object-contain"
            />
          )}
          {soilImageError && (
            <p className="text-sm text-red-700" role="alert">
              {soilImageError}
            </p>
          )}
          {soilPredictionState === "loading" && (
            <p className="flex items-center gap-2 text-sm text-surface-600" role="status">
              <Loader2 className="h-4 w-4 animate-spin" />
              {t.classifyingSoil}
            </p>
          )}
          {soilPrediction && (
            <p className="text-sm text-surface-700" role="status">
              <span className="font-medium">{t.predictedSoilClass}: </span>
              <span className="font-semibold">
                {soilPrediction.predicted_class}
              </span>
              {" · "}
              {(soilPrediction.confidence * 100).toFixed(1)}%
            </p>
          )}
          {soilImageFile && soilPredictionState !== "loading" && (
            <button
              type="button"
              onClick={() => void handleSoilImagePrediction()}
              className="rounded-xl border border-primary-600 px-4 py-2 text-sm font-semibold text-primary-700 hover:bg-primary-50"
            >
              {t.classifySoil}
            </button>
          )}
        </section>

        <button
          type="submit"
          disabled={!canSubmit}
          className="w-full rounded-xl bg-primary-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {t.datasetRunPrediction}
        </button>
      </form>
    </div>
  );
}
