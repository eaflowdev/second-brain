# Second Brain

Agent IA personnel qui ingère mes notes (Markdown, PDF), les indexe avec des embeddings et sert d'assistant de révision via des sous-agents spécialisés (quiz, recherche web, synthèse). Exposé en API FastAPI, en interface web React, et en serveur MCP utilisable depuis Claude Desktop.

Projet portfolio : chaque étape couvre un concept clé de l'IA appliquée (RAG, embeddings, boucle agentique, tool use, subagents, skills, MCP, gestion du contexte, prompt caching, sécurité/prompt injection).

## Stack

- **Backend** : Python, FastAPI
- **Frontend** : React
- **Protocole agent** : MCP (Model Context Protocol)

## Structure du repo

```
backend/
  app/
    ingestion/   # chargement des notes (Markdown, PDF) -> Document unifié
    embeddings/  # vectorisation des chunks
    storage/     # vector store / persistance
    agents/      # boucle agentique, sous-agents, skills
    mcp/         # exposition en serveur MCP
    api/         # routes FastAPI
    core/        # configuration
  tests/
frontend/        # interface web React
notes_sample/    # notes de test pour l'ingestion
```

## Lancer le backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Tests :

```bash
cd backend
pytest tests -q
```
