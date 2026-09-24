from app.agents import loop, tools
from app.core.llm import LLMError


def test_tool_to_schema_is_openai_compatible():
    schema = tools.search_notes_tool.to_schema()

    assert schema["type"] == "function"
    assert schema["function"]["name"] == "search_notes"
    assert "query" in schema["function"]["parameters"]["properties"]


def test_search_web_without_key_returns_message_not_crash(monkeypatch):
    monkeypatch.setattr(tools.settings, "tavily_api_key", None)

    result = tools._search_web("actualités IA")

    assert "TAVILY_API_KEY" in result


def test_run_agent_executes_tool_then_returns_final_answer(monkeypatch):
    calls = []

    def fake_chat(messages, tools=None, max_tokens=1024, model=None):
        if tools is None:
            return {"role": "assistant", "content": "1. Chercher dans les notes", "tool_calls": None}
        if len(calls) == 0:
            calls.append(1)
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {"name": "search_notes", "arguments": '{"query": "embedding"}'},
                    }
                ],
            }
        return {"role": "assistant", "content": "Un embedding est un vecteur.", "tool_calls": None}

    monkeypatch.setattr(loop, "chat", fake_chat)
    monkeypatch.setattr(
        loop.TOOLS["search_notes"], "handler", lambda query: "note pertinente sur les embeddings"
    )

    result = loop.run_agent("c'est quoi un embedding ?")

    assert result["plan"] == "1. Chercher dans les notes"
    assert result["answer"] == "Un embedding est un vecteur."
    assert result["steps"] == [
        {
            "tool": "search_notes",
            "input": {"query": "embedding"},
            "output": "note pertinente sur les embeddings",
        }
    ]


def test_run_agent_stops_after_max_turns(monkeypatch):
    def always_calls_tool(messages, tools=None, max_tokens=1024, model=None):
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {"id": "call_x", "function": {"name": "search_notes", "arguments": "{\"query\": \"x\"}"}}
            ],
        }

    monkeypatch.setattr(loop, "chat", always_calls_tool)
    monkeypatch.setattr(loop.TOOLS["search_notes"], "handler", lambda query: "observation")

    result = loop.run_agent("question sans fin", max_turns=2)

    assert "n'ai pas réussi" in result["answer"]
    assert len(result["steps"]) == 2


def test_run_agent_detects_repeated_identical_tool_call(monkeypatch):
    handler_calls = []

    def always_repeats_same_call(messages, tools=None, max_tokens=1024, model=None):
        if tools is None:
            return {"role": "assistant", "content": "plan", "tool_calls": None}
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {"id": "call_y", "function": {"name": "search_notes", "arguments": '{"query": "x"}'}}
            ],
        }

    def counting_handler(query):
        handler_calls.append(query)
        return "observation"

    monkeypatch.setattr(loop, "chat", always_repeats_same_call)
    monkeypatch.setattr(loop.TOOLS["search_notes"], "handler", counting_handler)

    result = loop.run_agent("question répétitive", max_turns=3)

    # le handler ne doit être exécuté qu'une fois : les tours suivants avec les
    # mêmes arguments doivent être court-circuités
    assert len(handler_calls) == 1
    assert "déjà appelé" in result["steps"][1]["output"]


def test_chat_with_retry_recovers_from_one_transient_failure(monkeypatch):
    attempts = []

    def flaky_chat(messages, tools=None, model=None):
        attempts.append(1)
        if len(attempts) == 1:
            raise LLMError("erreur transitoire")
        return {"role": "assistant", "content": "ok", "tool_calls": None}

    monkeypatch.setattr(loop, "chat", flaky_chat)

    result = loop._chat_with_retry([{"role": "user", "content": "x"}])

    assert result["content"] == "ok"
    assert len(attempts) == 2
