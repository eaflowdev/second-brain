import { describe, expect, it } from "vitest";
import { applyEvent, createAssistantMessage } from "./chat";

describe("applyEvent", () => {
  it("attaches a tool_result to the matching pending tool_call", () => {
    let message = createAssistantMessage("m1");
    message = applyEvent(message, { type: "tool_call", tool: "search_notes", input: { query: "rag" } });
    message = applyEvent(message, { type: "tool_result", tool: "search_notes", output: "trouvé" });

    expect(message.steps).toEqual([
      { tool: "search_notes", input: { query: "rag" }, output: "trouvé" },
    ]);
  });

  it("ignores a tool_result whose tool does not match the last pending call", () => {
    let message = createAssistantMessage("m1");
    message = applyEvent(message, { type: "tool_call", tool: "search_web", input: {} });
    message = applyEvent(message, { type: "tool_result", tool: "search_notes", output: "hors sujet" });

    expect(message.steps[0].output).toBeUndefined();
  });

  it("does not overwrite the output of an already completed step", () => {
    let message = createAssistantMessage("m1");
    message = applyEvent(message, { type: "tool_call", tool: "search_notes", input: {} });
    message = applyEvent(message, { type: "tool_result", tool: "search_notes", output: "premier" });
    message = applyEvent(message, { type: "tool_result", tool: "search_notes", output: "second" });

    expect(message.steps[0].output).toBe("premier");
  });

  it("marks the message done with the final answer", () => {
    const message = applyEvent(createAssistantMessage("m1"), {
      type: "final_answer",
      content: "Voici la réponse",
    });

    expect(message.status).toBe("done");
    expect(message.content).toBe("Voici la réponse");
  });

  it("marks the message as error and shows the error text", () => {
    const message = applyEvent(createAssistantMessage("m1"), {
      type: "error",
      message: "Provider LLM indisponible",
    });

    expect(message.status).toBe("error");
    expect(message.content).toBe("Provider LLM indisponible");
  });

  it("accumulates thinking traces in order", () => {
    let message = createAssistantMessage("m1");
    message = applyEvent(message, { type: "thinking", content: "étape 1" });
    message = applyEvent(message, { type: "thinking", content: "étape 2" });

    expect(message.thinking).toEqual(["étape 1", "étape 2"]);
  });

  it("does not mutate the previous message state", () => {
    const before = createAssistantMessage("m1");
    applyEvent(before, { type: "plan", content: "un plan" });

    expect(before.plan).toBeUndefined();
  });
});
