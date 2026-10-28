import { useState } from "react";
import { Send, ImagePlus } from "lucide-react";
import { useLanguage } from "../../contexts/LanguageContext";
import VoiceButton from "./VoiceButton";

interface ChatInputProps {
  onSend: (message: string) => void;
}

export default function ChatInput({ onSend }: ChatInputProps) {
  const { t } = useLanguage();
  const [text, setText] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    onSend(text.trim());
    setText("");
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-2 border-t border-surface-200 bg-white p-4"
    >
      {/* Image upload button */}
      <label
        className="shrink-0 cursor-pointer rounded-xl bg-surface-100 p-2.5 text-surface-600 transition-colors hover:bg-surface-200"
        aria-label={t.uploadImage}
      >
        <ImagePlus className="h-5 w-5" />
        <input type="file" accept="image/*" className="hidden" />
      </label>

      {/* Voice */}
      <VoiceButton />

      {/* Text input */}
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={t.askCropSensePlaceholder}
        className="min-w-0 flex-1 rounded-xl border border-surface-200 bg-surface-50 px-4 py-2.5 text-sm text-surface-900 placeholder-surface-400 transition-colors focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
      />

      {/* Send */}
      <button
        type="submit"
        disabled={!text.trim()}
        className="shrink-0 rounded-xl bg-primary-600 p-2.5 text-white shadow-sm transition-all hover:bg-primary-700 disabled:opacity-40 disabled:hover:bg-primary-600"
        aria-label={t.send}
      >
        <Send className="h-5 w-5" />
      </button>
    </form>
  );
}
