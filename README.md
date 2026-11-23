# PFE Finder

Application web qui aide les étudiants en génie logiciel à trouver les sujets de PFE (projet de fin d'études) en Tunisie les plus adaptés à leur profil.

L'étudiant dépose son CV, l'application affiche les sujets classés par pertinence (avec la raison du match), puis lui permet de consulter le détail d'un sujet et la procédure pour postuler.

## Principes

- **Sans compte, sans stockage du CV** : le CV est lu en mémoire, transformé en profil, et jamais enregistré.
- **RAG** : la recherche de sujets repose sur des embeddings (Gemini) et une recherche vectorielle (Supabase / pgvector). Le LLM ne répond qu'à partir des données de la base.
- **Alimentation automatique** : un agent (LangGraph) découvre de nouveaux PFE books et alimente la base, avec des garde-fous codés dans ses outils (robots.txt, quotas, quarantaine).
- **Gratuit** : Supabase, Gemini, GitHub Actions et Render, dans leurs offres gratuites.

## Architecture

```
pfe-finder/
├─ frontend/        Angular (à créer)
├─ backend/         API FastAPI
│  └─ app/
│     ├─ api/routes/     routes HTTP (health, profile, matching, subjects)
│     ├─ core/           configuration, erreurs, limite de requêtes
│     ├─ services/       logique métier (lecture du CV, profil, matching)
│     ├─ rag/            client Gemini, embeddings, LLM, prompts
│     ├─ repositories/   accès à Supabase
│     └─ schemas/        modèles Pydantic
├─ agent/           agent de découverte (LangGraph) - à venir
├─ ingestion/       PDF -> sujets JSON -> embeddings -> base - à venir
├─ database/        scripts SQL
└─ .github/workflows/
```

Chaque couche ne parle qu'à la suivante :
`Angular -> routes -> services -> rag / repositories -> Supabase / Gemini`

## Flux principal

1. `POST /api/profile` : le PDF du CV est lu, le LLM en extrait un profil JSON (rien n'est stocké).
2. `POST /api/matching` : le profil devient un embedding, la base renvoie les sujets les plus proches, le LLM explique chaque match en une phrase.
3. `GET /api/subjects/{id}` : détail d'un sujet.
4. `GET /api/subjects/{id}/apply` : comment postuler (mode, contact, documents, date limite).

## Démarrage

Prérequis : Python 3.11+, un projet Supabase, une clé Gemini.

1. Dans l'éditeur SQL de Supabase, exécuter `database/001_schema.sql` puis `database/002_match_function.sql`.
2. Dans `backend/`, copier `.env.example` en `.env` et renseigner les clés (clé `service_role` de Supabase, jamais côté front).
3. Installer et lancer :

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/macOS : source .venv/bin/activate)
pip install -r requirements-dev.txt
python test_connexion.py        # vérifie Supabase + Gemini
uvicorn app.main:app --reload   # http://localhost:8000/docs
pytest
```

## Feuille de route

- [x] Squelette de l'API et schéma de base
- [ ] Ingestion de premiers PFE books
- [ ] Front Angular (upload du CV, liste, détail, comment postuler)
- [ ] Déploiement gratuit (Render + Supabase)
- [ ] Agent de découverte planifié (GitHub Actions)
- [ ] Génération de lettre de motivation et adaptation du CV

## Données et sources

Les PFE books appartiennent à leurs entreprises. Le projet ne stocke que des informations factuelles et des liens vers les sources, ne réhéberge pas les PDF (ils sont ignorés par git), respecte `robots.txt` et les conditions des sites, et prévoit le retrait d'un contenu à la demande de son propriétaire.
