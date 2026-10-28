import { Bot, User } from "lucide-react";
import type { ChatMessage as ChatMessageType } from "../../data/mockData";

interface ChatMessageProps {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isAi = message.sender === "ai";

  return (
    <div
      className={`flex gap-3 animate-fade-in-up ${
        isAi ? "" : "flex-row-reverse"
      }`}
    >
      {/* Avatar */}
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isAi
            ? "bg-primary-100 text-primary-600"
            : "bg-surface-200 text-surface-600"
        }`}
      >
        {isAi ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isAi
            ? "bg-white border border-surface-100 text-surface-800"
            : "bg-primary-600 text-white"
        }`}
      >
        <p className="text-sm leading-relaxed">{message.text}</p>
        <p
          className={`mt-1.5 text-xs ${
            isAi ? "text-surface-400" : "text-primary-200"
          }`}
        >
          {message.timestamp}
        </p>
      </div>
    </div>
  );
}
