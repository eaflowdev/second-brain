from app.agents import orchestrator, subagents


def test_subagent_run_isolates_context_and_returns_only_answer(monkeypatch):
    captured = {}

    def fake_run_agent(task, system_prompt=None, tools=None, max_turns=None):
        captured["task"] = task
        captured["system_prompt"] = system_prompt
        captured["tools"] = tools
        return {
            "plan": "un plan interne au sous-agent",
            "answer": "3 questions de quiz sur les embeddings",
            "steps": [{"tool": "search_notes", "input": {}, "output": "..."}],
        }

    monkeypatch.setattr(subagents, "run_agent", fake_run_agent)

    result = subagents.QUIZZER.run("fais-moi un quiz sur les embeddings")

    # seul le texte final traverse la frontière du sous-agent, pas le plan ni les steps
    assert result == "3 questions de quiz sur les embeddings"
    assert captured["system_prompt"] == subagents.QUIZZER.system_prompt
    assert captured["tools"] == subagents.QUIZZER.tools


def test_delegation_tool_schema_matches_subagent():
    tool = orchestrator.DELEGATION_TOOLS[0]

    assert tool.name == f"delegate_to_{subagents.QUIZZER.name}"
    assert tool.description == subagents.QUIZZER.description
    assert "task" in tool.parameters["properties"]


def test_delegation_tool_handler_calls_the_right_subagent(monkeypatch):
    monkeypatch.setattr(subagents.QUIZZER, "run", lambda task: f"quiz pour: {task}")

    tool = next(t for t in orchestrator.DELEGATION_TOOLS if t.name == "delegate_to_quizzer")

    assert tool.handler(task="les embeddings") == "quiz pour: les embeddings"


def test_run_orchestrator_uses_delegation_tools(monkeypatch):
    captured = {}

    def fake_run_agent(question, system_prompt=None, tools=None, max_turns=None):
        captured["system_prompt"] = system_prompt
        captured["tools"] = tools
        return {"plan": "", "answer": "ok", "steps": []}

    monkeypatch.setattr(orchestrator, "run_agent", fake_run_agent)

    result = orchestrator.run_orchestrator("fais-moi un quiz")

    assert result["answer"] == "ok"
    assert captured["system_prompt"] == orchestrator.ORCHESTRATOR_SYSTEM_PROMPT
    assert captured["tools"] == orchestrator.DELEGATION_TOOLS
