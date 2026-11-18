import { useLanguage } from "../../contexts/LanguageContext";
import { translateDiseaseName } from "../../lib/diseaseNameTranslation.mjs";

interface DiseaseResultProps {
  predictedDisease: string;
  confidence: number;
}

export default function DiseaseResult({
  predictedDisease,
  confidence,
}: DiseaseResultProps) {
  const { language, t } = useLanguage();

  return (
    <div className="rounded-2xl border border-surface-100 bg-white p-6 shadow-sm">
      <div className="mb-4">
        <p className="text-sm font-medium text-surface-500">
          {t.predictedDisease}
        </p>
        <p className="mt-1 text-2xl font-bold text-surface-900">
          {translateDiseaseName(predictedDisease, language)}
        </p>
      </div>
      <div>
        <div className="mb-1.5 flex items-center justify-between">
          <span className="text-sm font-medium text-surface-600">
            {t.predictionConfidence}
          </span>
          <span className="text-sm font-bold text-primary-600">
            {(confidence * 100).toFixed(1)}%
          </span>
        </div>
        <div className="h-3 rounded-full bg-surface-100">
          <div
            className="h-3 rounded-full bg-gradient-to-r from-primary-400 to-primary-600 transition-all duration-1000"
            style={{ width: `${confidence * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}
