import type { AgentEvent } from "../lib/api";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: "streaming" | "done" | "error";
  plan?: string;
  steps: Array<{ tool: string; input: Record<string, unknown>; output?: string }>;
  thinking: string[];
}

export function createAssistantMessage(id: string): ChatMessage {
  return { id, role: "assistant", content: "", status: "streaming", steps: [], thinking: [] };
}

/** Folds one streamed AgentEvent into the running assistant message state. */
export function applyEvent(message: ChatMessage, event: AgentEvent): ChatMessage {
  switch (event.type) {
    case "plan":
      return { ...message, plan: event.content };
    case "tool_call":
      return {
        ...message,
        steps: [...message.steps, { tool: event.tool, input: event.input }],
      };
    case "tool_result":
      return {
        ...message,
        steps: message.steps.map((step, index) =>
          index === message.steps.length - 1 && step.tool === event.tool && step.output === undefined
            ? { ...step, output: event.output }
            : step,
        ),
      };
    case "thinking":
      return { ...message, thinking: [...message.thinking, event.content] };
    case "final_answer":
      return { ...message, content: event.content, status: "done" };
    case "error":
      return { ...message, content: event.message, status: "error" };
    default:
      return message;
  }
}
