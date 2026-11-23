# PFE Finder

Dépose ton CV, reçois les sujets de PFE tunisiens qui te correspondent, avec le détail et la procédure pour postuler. Le CV n'est jamais stocké.

## Fonctionnement

1. **Ingestion** : un PFE book (PDF) est lu, un LLM en extrait les sujets (JSON structuré), le code valide (Tunisie, année, date limite), puis chaque sujet est vectorisé (Gemini, 768 dim) et stocké dans Supabase (pgvector). Un chunk = un sujet.
2. **Matching (RAG)** : le CV devient un profil, le profil devient une requête vectorielle, les sujets les plus proches sont récupérés, le LLM explique en une phrase pourquoi chacun convient (uniquement à partir des sujets récupérés).
3. **Agent (LangGraph)** : chaque jour, il cherche de nouveaux PFE books et propose des sources ; le code vérifie (robots.txt, domaines autorisés, quotas) et ingère. Le doute va en quarantaine.

## Structure

| Dossier | Rôle |
|---|---|
| `backend/pfefinder/core` | config, schémas, prompts, LangChain, accès Supabase |
| `backend/pfefinder/api` | API FastAPI (`/api/match`, `/api/subjects/{id}`, `/api/subjects/{id}/apply`) |
| `backend/pfefinder/ingestion` | pipeline PDF -> base, CLI, expiration |
| `backend/pfefinder/agent` | agent LangGraph, garde-fous, `domains.json` |
| `database` | scripts SQL à exécuter dans l'ordre |
| `frontend` | Angular (à créer) |

## Démarrage local

1. Supabase : exécuter `database/001_schema.sql` puis `database/002_match_function.sql` (SQL Editor).
2. Backend :
   ```bash
   cd backend
   python -m venv .venv && .venv\Scripts\activate
   pip install -r requirements-dev.txt
   copy .env.example .env      # puis remplir les clés
   python -m scripts.check_connection
   pytest
   ```
3. Ingérer un PFE book :
   ```bash
   python -m pfefinder.ingestion.cli mon-book.pdf --url https://site.tn/mon-book.pdf
   ```
4. API : `uvicorn pfefinder.api.main:app --reload` puis http://localhost:8000/docs (essayer `POST /api/match` avec un CV PDF).
5. Agent : `python -m pfefinder.agent.run` (nécessite `GOOGLE_CSE_ID` / `GOOGLE_CSE_KEY` pour la recherche web ; sinon utiliser `--no-discovery` pour seulement traiter la file).

## Respect des sources

robots.txt et Content-Signal respectés, aucun accès à LinkedIn/Facebook/etc., ingestion automatique limitée aux domaines de `agent/domains.json`, 10 PDF par jour maximum, aucun PDF hébergé (faits + lien source uniquement). Demandez le retrait d'un sujet via les contacts du dépôt.

Voir `CLAUDE.md` pour les règles de développement.
