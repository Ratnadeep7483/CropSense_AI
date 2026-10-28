import { useLanguage } from "../../contexts/LanguageContext";

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void;
}

export default function SuggestedQuestions({
  onSelect,
}: SuggestedQuestionsProps) {
  const { t, language } = useLanguage();

  const questions =
    language === "en"
      ? [t.sq1, t.sq2, t.sq3, t.sq4]
      : [t.sq1, t.sq2, t.sq3, t.sq4];

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-surface-500">
        {t.suggestedQuestions}
      </p>
      <div className="flex flex-wrap gap-2">
        {questions.map((q) => (
          <button
            key={q}
            onClick={() => onSelect(q)}
            className="rounded-xl border border-surface-200 bg-white px-3.5 py-2 text-sm text-surface-700 transition-all hover:border-primary-300 hover:bg-primary-50 hover:text-primary-700 hover:-translate-y-0.5"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
