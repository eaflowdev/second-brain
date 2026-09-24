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

Nécessite Python 3.10+ (SDK MCP).

```bash
cd backend
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Tests :

```bash
cd backend
pytest tests -q
```

## Serveur MCP (Claude Desktop)

Expose les notes personnelles (recherche, quiz, recherche web, synthèse) comme outils MCP, utilisables directement depuis Claude Desktop.

Dans la config de Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`) :

```json
{
  "mcpServers": {
    "second-brain": {
      "command": "/chemin/absolu/vers/backend/.venv/bin/python",
      "args": ["/chemin/absolu/vers/backend/app/mcp/server.py"]
    }
  }
}
```

Redémarrer Claude Desktop ensuite. Les clés (`OPENROUTER_API_KEY`, `TAVILY_API_KEY`) sont lues depuis `backend/.env` (chemin absolu, indépendant du répertoire de travail utilisé par Claude Desktop pour lancer le process).

## Lancer le frontend

Interface de chat (streaming SSE), upload de notes, et affichage du raisonnement de l'agent en direct.

```bash
cd frontend
npm install
npm run dev
```

Ouvre `http://localhost:5173` (le backend doit tourner sur `http://localhost:8000`).
