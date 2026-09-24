export const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type AgentEvent =
  | { type: "plan"; content: string }
  | { type: "tool_call"; tool: string; input: Record<string, unknown> }
  | { type: "tool_result"; tool: string; output: string }
  | { type: "thinking"; content: string }
  | { type: "final_answer"; content: string }
  | { type: "error"; message: string };

export interface HistoryTurn {
  role: "user" | "assistant";
  content: string;
}

export interface NoteDocument {
  id: string;
  title: string;
  doc_type: string;
  source_path: string;
  content_preview: string;
}

/**
 * Opens an EventSource against /agent/ask/stream and forwards each parsed
 * event to onEvent as it arrives. Returns a cleanup function to close the
 * connection early (e.g. if the component unmounts mid-stream).
 */
export function streamAsk(
  question: string,
  onEvent: (event: AgentEvent) => void,
  options?: { reasoningEffort?: string; history?: HistoryTurn[] },
): () => void {
  const params = new URLSearchParams({ question });
  if (options?.history?.length) {
    // EventSource = GET uniquement : l'historique passe en JSON dans l'URL.
    params.set("history", JSON.stringify(options.history));
  }
  if (options?.reasoningEffort) {
    params.set("reasoning_effort", options.reasoningEffort);
  }

  const source = new EventSource(`${API_BASE_URL}/agent/ask/stream?${params.toString()}`);

  source.onmessage = (message) => {
    const event = JSON.parse(message.data) as AgentEvent;
    onEvent(event);
    if (event.type === "final_answer" || event.type === "error") {
      source.close();
    }
  };

  source.onerror = () => {
    onEvent({ type: "error", message: "Connexion au serveur interrompue." });
    source.close();
  };

  return () => source.close();
}

export async function uploadNote(file: File): Promise<{ filename: string; saved_to: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/ingestion/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? "Échec de l'upload");
  }

  return response.json();
}

export async function reindexNotes(): Promise<{ documents_indexed: number; chunks_indexed: number }> {
  const response = await fetch(`${API_BASE_URL}/embeddings/index`, { method: "POST" });
  if (!response.ok) {
    throw new Error("Échec de la ré-indexation");
  }
  return response.json();
}

export async function scanNotes(): Promise<{ count: number; documents: NoteDocument[] }> {
  const response = await fetch(`${API_BASE_URL}/ingestion/scan`);
  if (!response.ok) {
    throw new Error("Échec de la lecture des notes");
  }
  return response.json();
}
