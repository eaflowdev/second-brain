import type { ChatMessage } from "../lib/chat";
import { StepsTrace } from "./StepsTrace";
import { ThinkingPanel } from "./ThinkingPanel";

export function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`flex max-w-2xl flex-col gap-2 ${isUser ? "items-end" : "items-start"}`}>
        {!isUser && <ThinkingPanel plan={message.plan} thinking={message.thinking} />}
        {!isUser && <StepsTrace steps={message.steps} />}
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
            isUser
              ? "bg-gradient-to-br from-indigo-600 to-violet-600 text-white"
              : message.status === "error"
                ? "border border-red-900/50 bg-red-950/40 text-red-300"
                : "border border-slate-800 bg-slate-900 text-slate-100"
          }`}
        >
          {message.content ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <span className="flex items-center gap-1 text-slate-500">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-500 [animation-delay:-0.3s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-500 [animation-delay:-0.15s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-500" />
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
