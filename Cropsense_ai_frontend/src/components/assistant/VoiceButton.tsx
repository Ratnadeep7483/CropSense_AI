import { useState } from "react";
import { Mic, MicOff } from "lucide-react";
import { useLanguage } from "../../contexts/LanguageContext";

interface VoiceButtonProps {
  onTranscript?: (text: string) => void;
}

export default function VoiceButton({ onTranscript: _onTranscript }: VoiceButtonProps) {
  const { t } = useLanguage();
  const [isListening, setIsListening] = useState(false);

  const handleToggle = () => {
    if (isListening) {
      setIsListening(false);
    } else {
      setIsListening(true);
      // Mock: stop listening after 3 seconds
      setTimeout(() => setIsListening(false), 3000);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={handleToggle}
        className={`rounded-xl p-2.5 transition-all ${
          isListening
            ? "bg-danger-500 text-white shadow-lg shadow-danger-500/30 animate-pulse-gentle"
            : "bg-surface-100 text-surface-600 hover:bg-surface-200"
        }`}
        aria-label={isListening ? t.tapToStop : t.voice}
      >
        {isListening ? (
          <MicOff className="h-5 w-5" />
        ) : (
          <Mic className="h-5 w-5" />
        )}
      </button>
      {isListening && (
        <div className="absolute bottom-full left-1/2 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg bg-surface-900 px-3 py-1.5 text-xs text-white shadow-lg">
          {t.listening}
          <div className="absolute -bottom-1 left-1/2 h-2 w-2 -translate-x-1/2 rotate-45 bg-surface-900" />
        </div>
      )}
    </div>
  );
}
