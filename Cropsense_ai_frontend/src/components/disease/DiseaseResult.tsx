import { AlertTriangle, ShieldCheck, ShieldAlert } from "lucide-react";
import { useLanguage } from "../../contexts/LanguageContext";
import type { DiseaseResult as DiseaseResultType } from "../../data/mockData";

interface DiseaseResultProps {
  result: DiseaseResultType;
}

export default function DiseaseResult({ result }: DiseaseResultProps) {
  const { t } = useLanguage();

  const severityConfig: Record<
    string,
    { color: string; bg: string; icon: typeof ShieldCheck }
  > = {
    Low: { color: "text-primary-600", bg: "bg-primary-50", icon: ShieldCheck },
    Moderate: {
      color: "text-amber-600",
      bg: "bg-amber-50",
      icon: AlertTriangle,
    },
    High: {
      color: "text-danger-600",
      bg: "bg-danger-50",
      icon: ShieldAlert,
    },
  };

  const severityCfg =
    severityConfig[result.severity] || severityConfig["Moderate"];

  return (
    <div className="space-y-5">
      {/* Main Result Card */}
      <div className="rounded-2xl border border-surface-100 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-surface-500">{t.disease}</p>
            <p className="mt-1 text-2xl font-bold text-surface-900">
              {result.disease}
            </p>
          </div>
          <div className={`rounded-xl p-2.5 ${severityCfg.bg}`}>
            <severityCfg.icon className={`h-6 w-6 ${severityCfg.color}`} />
          </div>
        </div>

        {/* Confidence */}
        <div className="mb-4">
          <div className="mb-1.5 flex items-center justify-between">
            <span className="text-sm font-medium text-surface-600">
              {t.confidence}
            </span>
            <span className="text-sm font-bold text-primary-600">
              {result.confidence}%
            </span>
          </div>
          <div className="h-3 rounded-full bg-surface-100">
            <div
              className="h-3 rounded-full bg-gradient-to-r from-primary-400 to-primary-600 transition-all duration-1000"
              style={{ width: `${result.confidence}%` }}
            />
          </div>
        </div>

        {/* Severity */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-surface-600">
            {t.severity}:
          </span>
          <span
            className={`inline-flex items-center gap-1 rounded-lg px-2.5 py-1 text-sm font-semibold ${severityCfg.bg} ${severityCfg.color}`}
          >
            {result.severity}
          </span>
        </div>
      </div>

      {/* Treatment */}
      <div className="rounded-2xl border border-surface-100 bg-white p-6 shadow-sm">
        <h3 className="mb-3 text-lg font-semibold text-surface-900">
          {t.treatmentRecommendation}
        </h3>
        <p className="text-sm leading-relaxed text-surface-600">
          {result.treatment}
        </p>
      </div>

      {/* Prevention */}
      <div className="rounded-2xl border border-surface-100 bg-white p-6 shadow-sm">
        <h3 className="mb-3 text-lg font-semibold text-surface-900">
          {t.prevention}
        </h3>
        <ul className="space-y-2.5">
          {result.prevention.map((tip, i) => (
            <li
              key={i}
              className="flex items-start gap-2 text-sm text-surface-600"
            >
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-primary-500" />
              {tip}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
