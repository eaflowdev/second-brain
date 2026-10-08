# Second Brain

Agent IA personnel qui ingère mes notes (Markdown, PDF), les indexe avec des embeddings et sert d'assistant de révision via des sous-agents spécialisés (quiz, recherche web, synthèse). Exposé en API FastAPI, en interface web React, et en serveur MCP utilisable depuis Claude Desktop.

Projet portfolio : chaque étape couvre un concept clé de l'IA appliquée (RAG, recherche hybride vectorielle + BM25, embeddings, boucle agentique, tool use, subagents, skills, MCP, gestion du contexte, prompt caching, sécurité/prompt injection).

## Stack

- **Backend** : Python, FastAPI
- **Frontend** : React, TypeScript, Vite
- **Protocole agent** : MCP (Model Context Protocol)
- **CI** : GitHub Actions (pytest backend, Vitest + build frontend) à chaque push

## Au-delà du prototype

Quelques points traités pour que le projet tienne en conditions réelles, pas seulement sur le cas de démo :

- **Recherche hybride** : fusion (RRF) d'une recherche vectorielle et d'un scoring BM25 maison, pour que les acronymes et termes exacts que l'embedding sous-représente remontent correctement.
- **Indexation incrémentale** : `/embeddings/index` ne réembedde que les documents nouveaux ou modifiés (hash de contenu), au lieu de tout recalculer à chaque appel.
- **Hand-off multi-agents fiable** : le contenu produit par un sous-agent est ajouté à la réponse par le code, pas recopié par le LLM de l'orchestrateur — élimine un point de fragilité classique des architectures multi-agents.
- **Sécurité/robustesse** : détection de prompt injection sur le contenu externe (notes, résultats web), limite de taille d'upload, et rate-limiting par IP sur les endpoints coûteux (agent, RAG, réindexation).

## Structure du repo

```
backend/
  app/
    ingestion/   # chargement des notes (Markdown, PDF) -> Document unifié
    embeddings/  # vectorisation des chunks
    storage/     # vector store / recherche hybride (vectorielle + BM25) / persistance
    agents/      # boucle agentique, orchestrateur, sous-agents, skills
    mcp/         # exposition en serveur MCP
    api/         # routes FastAPI
    core/        # configuration, rate limiting
  tests/
frontend/        # interface web React (chat, streaming SSE, upload de notes)
notes_sample/    # notes de test pour l'ingestion
.github/workflows/ # CI (tests backend + frontend à chaque push)
```

## Lancer le backend

Nécessite Python 3.10+ (SDK MCP).

```bash
cd backend
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Les notes indexées viennent de `notes_dir` (par défaut `notes_sample/` à la racine). Pour pointer vers un dossier réel hors du repo, définis `NOTES_DIR` dans `backend/.env` (voir `.env.example`).

Tests (`requirements-dev.txt` ajoute `pytest-asyncio`, nécessaire aux tests du serveur MCP) :

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
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

Tests (Vitest) :

```bash
cd frontend
npm test
```
