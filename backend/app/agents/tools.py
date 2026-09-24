import httpx

from app.agents.models import Tool
from app.agents.skill_loader import get_skill, list_skills
from app.core.config import settings
from app.embeddings.embedder import Embedder
from app.storage.vector_store import get_vector_store

_embedder = Embedder()

TAVILY_URL = "https://api.tavily.com/search"


def _search_notes(query: str, top_k: int = 5) -> str:
    store = get_vector_store()
    query_vector = _embedder.embed([query])[0]
    chunks = store.search(query_vector, top_k=top_k)

    if not chunks:
        return "Aucun passage pertinent trouvé dans les notes."

    return "\n\n---\n\n".join(
        f"[Source: {c['metadata']['title']}] (score={c['score']:.2f})\n{c['text']}" for c in chunks
    )


def _search_web(query: str) -> str:
    if not settings.tavily_api_key:
        return "Recherche web indisponible : TAVILY_API_KEY manquante dans backend/.env."

    try:
        response = httpx.post(
            TAVILY_URL,
            json={"api_key": settings.tavily_api_key, "query": query, "max_results": 5},
            timeout=30,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return f"Recherche web échouée : {exc}"

    results = response.json().get("results", [])
    if not results:
        return "Aucun résultat web trouvé."

    return "\n\n---\n\n".join(
        f"[{r['title']}]({r['url']})\n{r['content']}" for r in results
    )


def _load_skill(name: str) -> str:
    try:
        skill = get_skill(name)
    except KeyError:
        available = ", ".join(s.name for s in list_skills())
        return f"Compétence inconnue : {name}. Compétences disponibles : {available}."
    return skill.body


search_notes_tool = Tool(
    name="search_notes",
    description=(
        "Recherche par similarité sémantique dans les notes personnelles de "
        "l'utilisateur. À utiliser en priorité pour toute question sur son contenu."
    ),
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string", "description": "La question ou les mots-clés à chercher"}},
        "required": ["query"],
    },
    handler=_search_notes,
)

search_web_tool = Tool(
    name="search_web",
    description=(
        "Recherche des informations à jour sur le web. À utiliser si les notes "
        "personnelles ne suffisent pas ou si la question porte sur l'actualité."
    ),
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string", "description": "La requête de recherche web"}},
        "required": ["query"],
    },
    handler=_search_web,
)

load_skill_tool = Tool(
    name="load_skill",
    description=(
        "Charge les instructions détaillées d'une compétence (skill) disponible. "
        "Appelle cet outil dès que la tâche demandée correspond à l'une des "
        "compétences listées dans le system prompt, puis suis ses instructions."
    ),
    parameters={
        "type": "object",
        "properties": {"name": {"type": "string", "description": "Le nom de la compétence à charger"}},
        "required": ["name"],
    },
    handler=_load_skill,
)

TOOLS = {tool.name: tool for tool in [search_notes_tool, search_web_tool, load_skill_tool]}
