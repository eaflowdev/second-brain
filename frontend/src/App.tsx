import { useRef, useState } from "react";
import { streamAsk, type HistoryTurn } from "./lib/api";
import { applyEvent, createAssistantMessage, type ChatMessage } from "./lib/chat";
import { ChatBubble } from "./components/ChatBubble";
import { ChatInput } from "./components/ChatInput";
import { Sidebar } from "./components/Sidebar";

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const closeRef = useRef<(() => void) | null>(null);

  function handleAsk(question: string) {
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
      status: "done",
      steps: [],
      thinking: [],
    };
    const assistantId = crypto.randomUUID();

    // Seuls les tours terminés (question + réponse finale) alimentent la mémoire.
    const history: HistoryTurn[] = messages
      .filter((m) => m.status === "done" && m.content)
      .map((m) => ({ role: m.role, content: m.content }));

    setMessages((prev) => [...prev, userMessage, createAssistantMessage(assistantId)]);
    setStreaming(true);

    closeRef.current = streamAsk(
      question,
      (event) => {
      setMessages((prev) =>
        prev.map((message) => (message.id === assistantId ? applyEvent(message, event) : message)),
      );
      if (event.type === "final_answer" || event.type === "error") {
        setStreaming(false);
      }
      },
      { history },
    );
  }

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100">
      <Sidebar />

      <main className="flex flex-1 flex-col">
        <header className="border-b border-slate-800 px-6 py-4">
          <h2 className="text-sm font-medium text-slate-300">Assistant de révision</h2>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-6">
          <div className="mx-auto flex max-w-2xl flex-col gap-6">
            {messages.length === 0 && (
              <div className="mt-20 text-center text-slate-500">
                <p className="text-2xl">👋</p>
                <p className="mt-2 text-sm">
                  Pose une question sur tes notes, demande un quiz, ou une recherche approfondie.
                </p>
              </div>
            )}
            {messages.map((message) => (
              <ChatBubble key={message.id} message={message} />
            ))}
          </div>
        </div>

        <div className="border-t border-slate-800 px-6 py-4">
          <div className="mx-auto max-w-2xl">
            <ChatInput onSubmit={handleAsk} disabled={streaming} />
          </div>
        </div>
      </main>
    </div>
  );
}
