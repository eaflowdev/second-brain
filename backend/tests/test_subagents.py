from app.agents import orchestrator, subagents


def test_subagent_run_isolates_context_and_returns_only_answer(monkeypatch):
    captured = {}

    def fake_run_agent(task, system_prompt=None, tools=None, max_turns=None, reasoning=None):
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
    tool = orchestrator.build_delegation_tools([])[0]

    assert tool.name == f"delegate_to_{subagents.QUIZZER.name}"
    assert tool.description == subagents.QUIZZER.description
    assert "task" in tool.parameters["properties"]


def test_delegation_tool_stores_subagent_output_and_acks_the_llm(monkeypatch):
    monkeypatch.setattr(subagents.QUIZZER, "run", lambda task: f"quiz pour: {task}")
    outputs = []

    tool = next(t for t in orchestrator.build_delegation_tools(outputs) if t.name == "delegate_to_quizzer")
    ack = tool.handler(task="les embeddings")

    assert outputs == ["quiz pour: les embeddings"]
    assert "quiz pour" not in ack  # le LLM ne reçoit qu'un accusé de réception


def test_run_orchestrator_appends_subagent_output_verbatim(monkeypatch):
    def fake_run_agent(question, system_prompt=None, tools=None, max_turns=None, reasoning=None):
        # simule le LLM de l'orchestrateur : il délègue puis rédige une phrase de contexte
        delegate = next(t for t in tools if t.name == "delegate_to_quizzer")
        delegate.handler(task="embeddings")
        return {"plan": "", "answer": "Voici ton quiz :", "steps": []}

    monkeypatch.setattr(orchestrator, "run_agent", fake_run_agent)
    monkeypatch.setattr(subagents.QUIZZER, "run", lambda task: "Q1 : ...\nRéponse : ...")

    result = orchestrator.run_orchestrator("fais-moi un quiz")

    assert result["answer"] == "Voici ton quiz :\n\n---\n\nQ1 : ...\nRéponse : ..."


def test_run_orchestrator_uses_its_own_system_prompt_and_delegation_tools(monkeypatch):
    captured = {}

    def fake_run_agent(question, system_prompt=None, tools=None, max_turns=None, reasoning=None):
        captured["system_prompt"] = system_prompt
        captured["tool_names"] = sorted(t.name for t in tools)
        return {"plan": "", "answer": "ok", "steps": []}

    monkeypatch.setattr(orchestrator, "run_agent", fake_run_agent)

    result = orchestrator.run_orchestrator("fais-moi un quiz")

    assert result["answer"] == "ok"
    assert captured["system_prompt"] == orchestrator.ORCHESTRATOR_SYSTEM_PROMPT
    assert captured["tool_names"] == sorted(f"delegate_to_{name}" for name in subagents.SUBAGENTS)


def test_subagents_are_built_from_skill_files():
    from app.agents import skill_loader

    for agent in subagents.SUBAGENTS.values():
        skill = skill_loader.get_skill(agent.name)
        assert agent.description == skill.description
        assert skill.role in agent.system_prompt
        assert [t.name for t in agent.tools] == list(skill.tools)
