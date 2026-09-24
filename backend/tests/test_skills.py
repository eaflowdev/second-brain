import pytest

from app.agents import skill_loader, tools


def test_list_skills_parses_frontmatter_and_body():
    skills = skill_loader.list_skills()
    names = {skill.name for skill in skills}

    assert {"quizzer", "researcher", "synthesizer"}.issubset(names)
    quizzer = skill_loader.get_skill("quizzer")
    assert "search_notes" in quizzer.body
    assert quizzer.description  # non-empty one-line summary


def test_get_skill_unknown_raises():
    with pytest.raises(KeyError):
        skill_loader.get_skill("does-not-exist")


def test_load_skill_tool_returns_body_for_known_skill():
    result = tools._load_skill("quizzer")

    assert result == skill_loader.get_skill("quizzer").body


def test_load_skill_tool_returns_helpful_message_for_unknown_skill():
    result = tools._load_skill("does-not-exist")

    assert "inconnue" in result
    assert "quizzer" in result  # liste les compétences disponibles
