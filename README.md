# PFE Finder

Dépose ton CV, reçois les sujets de PFE tunisiens qui te correspondent, avec le détail et la procédure pour postuler. Le CV n'est jamais stocké.

## Fonctionnement

1. **Ingestion** : un PFE book (PDF) est lu, un LLM en extrait les sujets (JSON structuré), le code valide (Tunisie, année, date limite), puis chaque sujet est vectorisé (Gemini, 768 dim) et stocké dans Supabase (pgvector). Un chunk = un sujet.
2. **Matching (RAG)** : le CV (jamais stocké) devient un profil structuré. Les sujets candidats viennent de deux recherches complémentaires : vectorielle (le profil, chaque projet et chaque expérience, séparément) et par mots-clés sur tout le catalogue. Un classement hybride les ordonne, puis un LLM note chaque candidat de 0 à 10 avec une raison courte ; seuls les sujets notés 6 ou plus sont affichés. L'utilisateur peut filtrer par ville.
3. **Agent (LangGraph)** : chaque nuit (GitHub Actions, Ollama pour l'extraction), il cherche de nouveaux PFE books et propose des sources ; le code vérifie (robots.txt, domaines autorisés, quotas) et ingère. Le doute va en quarantaine ; une source en échec reste en file pour le lendemain.

## Structure

| Dossier | Rôle |
|---|---|
| `backend/pfefinder/rag` | le RAG : ingestion, indexation, retrieval, génération |
| `backend/pfefinder/repositories` | accès à Supabase |
| `backend/pfefinder/api` | API FastAPI (`/api/match`, `/api/subjects/{id}`, `/api/subjects/{id}/apply`) |
| `backend/pfefinder/agent` | agent LangGraph, garde-fous, `domains.json` |
| `backend/pfefinder/cli` | ingestion manuelle d'un PDF ou d'un JSON |
| `database` | scripts SQL à exécuter dans l'ordre |
| `frontend` | Angular (upload, résultats, détail) |

Détail du pipeline et correspondance avec les étapes d'un RAG : [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

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
   python -m pfefinder.cli.ingest_book mon-book.pdf --url https://site.tn/mon-book.pdf
   ```
4. API : `uvicorn pfefinder.api.main:app --reload` puis http://localhost:8000/docs (essayer `POST /api/match` avec un CV PDF).
5. Agent : `python -m pfefinder.agent.daily_run` (nécessite `GOOGLE_CSE_ID` / `GOOGLE_CSE_KEY` pour la recherche web ; sinon utiliser `--no-discovery` pour seulement traiter la file).

## Respect des sources

robots.txt et Content-Signal respectés, aucun accès à LinkedIn/Facebook/etc., ingestion automatique limitée aux domaines de `agent/domains.json`, 10 PDF par jour maximum, aucun PDF hébergé (faits + lien source uniquement). Demandez le retrait d'un sujet via les contacts du dépôt.

Voir `CLAUDE.md` pour les règles de développement.
