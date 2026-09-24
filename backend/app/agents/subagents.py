from dataclasses import dataclass
from typing import List

from app.agents.loop import run_agent
from app.agents.models import Tool
from app.agents.tools import search_notes_tool, search_web_tool

SUBAGENT_MAX_TURNS = 4


@dataclass
class SubAgent:
    """A narrowly-scoped agent: its own system prompt, its own toolset, and its
    own isolated conversation. Only .run()'s return value crosses back out —
    the caller never sees this subagent's internal reasoning or tool calls."""

    name: str
    description: str
    system_prompt: str
    tools: List[Tool]

    def run(self, task: str) -> str:
        result = run_agent(
            task,
            system_prompt=self.system_prompt,
            tools=self.tools,
            max_turns=SUBAGENT_MAX_TURNS,
        )
        return result["answer"]


QUIZZER = SubAgent(
    name="quizzer",
    description=(
        "Génère un quiz de révision (questions + réponses) à partir des notes "
        "personnelles sur un sujet donné."
    ),
    system_prompt=(
        "Tu es un générateur de quiz de révision. Utilise `search_notes` pour "
        "trouver le contenu pertinent sur le sujet demandé, puis génère 3 à 5 "
        "questions de quiz (avec leurs réponses) strictement basées sur ce "
        "contenu. Si les notes ne couvrent pas assez le sujet, dis-le "
        "clairement plutôt que d'inventer des questions."
    ),
    tools=[search_notes_tool],
)

RESEARCHER = SubAgent(
    name="researcher",
    description=(
        "Fait une recherche approfondie sur un sujet, en combinant notes "
        "personnelles et web, avec sources citées."
    ),
    system_prompt=(
        "Tu es un assistant de recherche. Utilise `search_notes` pour ce que "
        "l'utilisateur a déjà noté, et `search_web` pour compléter avec des "
        "informations à jour. Cite systématiquement tes sources (titre de "
        "note ou URL). Distingue clairement ce qui vient des notes de ce qui "
        "vient du web."
    ),
    tools=[search_notes_tool, search_web_tool],
)

SYNTHESIZER = SubAgent(
    name="synthesizer",
    description=(
        "Produit une synthèse structurée (points clés, plan) d'un sujet à "
        "partir des notes personnelles."
    ),
    system_prompt=(
        "Tu es un assistant de synthèse. Utilise `search_notes` pour "
        "rassembler tout le contenu pertinent sur le sujet, puis produis une "
        "synthèse structurée (titres, points clés) — pas une réponse "
        "conversationnelle, un document de révision clair et concis. Reste "
        "strictement basé sur le contenu trouvé dans les notes : si celui-ci "
        "est court ou incomplet, ta synthèse doit l'être aussi. Ne complète "
        "jamais avec des connaissances générales non présentes dans les notes."
    ),
    tools=[search_notes_tool],
)

SUBAGENTS = {agent.name: agent for agent in [QUIZZER, RESEARCHER, SYNTHESIZER]}
