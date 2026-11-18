import { useState, useCallback, useEffect, useRef } from "react";
import { Loader2, RotateCcw } from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";
import { predictDisease, type DiseasePredictResponse } from "../lib/api/diseaseApi";
import ImageUploader from "../components/disease/ImageUploader";
import ImagePreview from "../components/disease/ImagePreview";
import DiseaseResultComponent from "../components/disease/DiseaseResult";

type PageState = "upload" | "loading" | "result" | "error";

export default function DiseaseDetection() {
  const { t } = useLanguage();
  const [state, setState] = useState<PageState>("upload");
  const [imageUrl, setImageUrl] = useState("");
  const [prediction, setPrediction] = useState<DiseasePredictResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const requestId = useRef(0);

  useEffect(() => {
    return () => {
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    };
  }, [imageUrl]);

  const handleImageSelect = useCallback(async (file: File) => {
    const activeRequestId = ++requestId.current;
    const url = URL.createObjectURL(file);
    setImageUrl(url);
    setPrediction(null);
    setErrorMessage("");
    setState("loading");
    try {
      const result = await predictDisease(file);
      if (requestId.current === activeRequestId) {
        setPrediction(result);
        setState("result");
      }
    } catch (error: unknown) {
      if (requestId.current === activeRequestId) {
        setErrorMessage(
          error instanceof Error ? error.message : t.unableToProcess,
        );
        setState("error");
      }
    }
  }, [t.unableToProcess]);

  const handleClear = useCallback(() => {
    requestId.current += 1;
    setImageUrl("");
    setPrediction(null);
    setErrorMessage("");
    setState("upload");
  }, []);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-surface-900 md:text-3xl">
          {t.diseaseDetectionTitle}
        </h1>
        <p className="mt-1 text-surface-500">
          {t.diseaseDetectionSubtitle}
        </p>
      </div>

      {/* Upload State */}
      {state === "upload" && (
        <ImageUploader onImageSelect={handleImageSelect} />
      )}

      {(state === "loading" || state === "result" || state === "error") &&
        imageUrl && <ImagePreview imageUrl={imageUrl} onClear={handleClear} />}

      {/* Loading State */}
      {state === "loading" && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-surface-200 bg-white p-16">
          <Loader2 className="mb-4 h-10 w-10 animate-spin text-primary-500" />
          <p className="text-lg font-semibold text-surface-800">
            {t.analyzing}
          </p>
          <div className="mt-4 h-2 w-48 overflow-hidden rounded-full bg-surface-100">
            <div className="h-2 animate-pulse rounded-full bg-primary-500" style={{ width: "70%" }} />
          </div>
        </div>
      )}

      {/* Result State */}
      {state === "result" && prediction && (
        <>
          <DiseaseResultComponent
            predictedDisease={prediction.predicted_disease}
            confidence={prediction.confidence}
          />
          <button
            onClick={handleClear}
            className="inline-flex items-center gap-2 rounded-xl border border-surface-200 bg-white px-5 py-2.5 text-sm font-semibold text-surface-700 shadow-sm transition-all hover:bg-surface-50 hover:-translate-y-0.5"
          >
            <RotateCcw className="h-4 w-4" />
            {t.analyzeAnother}
          </button>
        </>
      )}

      {/* Error State */}
      {state === "error" && (
        <div className="flex flex-col items-center rounded-2xl border border-danger-200 bg-danger-50 p-12">
          <p className="mb-4 text-lg font-semibold text-danger-700">
            {t.unableToProcess}
          </p>
          {errorMessage && errorMessage !== t.unableToProcess && (
            <p className="mb-4 text-sm text-danger-700">{errorMessage}</p>
          )}
          <button
            onClick={handleClear}
            className="inline-flex items-center gap-2 rounded-xl bg-danger-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-danger-700"
          >
            <RotateCcw className="h-4 w-4" />
            {t.analyzeAnother}
          </button>
        </div>
      )}
    </div>
  );
}
