from app.agents import loop, tools


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
