import { useState, useCallback } from "react";
import { Loader2, RotateCcw } from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";
import { mockDiseaseResult } from "../data/mockData";
import ImageUploader from "../components/disease/ImageUploader";
import ImagePreview from "../components/disease/ImagePreview";
import DiseaseResultComponent from "../components/disease/DiseaseResult";

type PageState = "upload" | "preview" | "loading" | "result" | "error";

export default function DiseaseDetection() {
  const { t } = useLanguage();
  const [state, setState] = useState<PageState>("upload");
  const [imageUrl, setImageUrl] = useState("");

  const handleImageSelect = useCallback((file: File) => {
    const url = URL.createObjectURL(file);
    setImageUrl(url);
    setState("preview");

    // Auto-start mock analysis after a short delay
    setTimeout(() => {
      setState("loading");
      setTimeout(() => {
        setState("result");
      }, 2000);
    }, 500);
  }, []);

  const handleClear = useCallback(() => {
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    setImageUrl("");
    setState("upload");
  }, [imageUrl]);

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

      {/* Preview State */}
      {state === "preview" && imageUrl && (
        <ImagePreview imageUrl={imageUrl} onClear={handleClear} />
      )}

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
      {state === "result" && (
        <>
          {imageUrl && (
            <ImagePreview imageUrl={imageUrl} onClear={handleClear} />
          )}
          <DiseaseResultComponent result={mockDiseaseResult} />
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
