import { useState, useCallback } from "react";
import { Bot, Loader2 } from "lucide-react";
import { useLanguage } from "../contexts/LanguageContext";
import {
  mockChatMessages,
  mockAiResponses,
  type ChatMessage,
} from "../data/mockData";
import ChatWindow from "../components/assistant/ChatWindow";
import ChatInput from "../components/assistant/ChatInput";
import SuggestedQuestions from "../components/assistant/SuggestedQuestions";

export default function Assistant() {
  const { t } = useLanguage();
  const [messages, setMessages] = useState<ChatMessage[]>(mockChatMessages);
  const [isTyping, setIsTyping] = useState(false);

  const addMessage = useCallback(
    (text: string) => {
      const now = new Date();
      const time = now.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });

      // Add farmer message
      const farmerMsg: ChatMessage = {
        id: `f-${Date.now()}`,
        sender: "farmer",
        text,
        timestamp: time,
      };
      setMessages((prev) => [...prev, farmerMsg]);

      // Simulate AI typing
      setIsTyping(true);
      setTimeout(() => {
        const aiText =
          mockAiResponses[text] ||
          (t === undefined
            ? "I'm here to help with your farming questions!"
            : `Thank you for your question. Based on current agricultural data, I'd recommend consulting the relevant tool in CropSense AI for a detailed analysis. You can use Crop Recommendation, Disease Detection, or Smart Irrigation tools for specific guidance.`);

        const aiMsg: ChatMessage = {
          id: `a-${Date.now()}`,
          sender: "ai",
          text: aiText,
          timestamp: time,
        };
        setMessages((prev) => [...prev, aiMsg]);
        setIsTyping(false);
      }, 1000);
    },
    [t]
  );

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      {/* Header */}
      <div className="border-b border-surface-200 bg-white px-4 py-4 md:px-6">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-primary-100 p-2.5">
            <Bot className="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-surface-900">
              {t.assistantTitle}
            </h1>
            <p className="text-sm text-surface-500">{t.assistantSubtitle}</p>
          </div>
        </div>
      </div>

      {/* Suggested Questions (shown when few messages) */}
      {messages.length <= 2 && (
        <div className="border-b border-surface-100 bg-surface-50 p-4 md:px-6">
          <SuggestedQuestions onSelect={addMessage} />
        </div>
      )}

      {/* Chat Messages */}
      <div className="flex-1 overflow-hidden bg-surface-50">
        <ChatWindow messages={messages} />
        {isTyping && (
          <div className="flex items-center gap-2 px-4 pb-3 md:px-6">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-primary-600">
              <Bot className="h-4 w-4" />
            </div>
            <div className="flex items-center gap-1.5 rounded-2xl border border-surface-100 bg-white px-4 py-2.5">
              <Loader2 className="h-4 w-4 animate-spin text-primary-500" />
              <span className="text-sm text-surface-500">{t.loading}</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput onSend={addMessage} />
    </div>
  );
}
