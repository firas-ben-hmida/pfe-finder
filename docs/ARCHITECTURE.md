# Architecture

## Pipeline RAG et fichiers correspondants

| Étape RAG | Ce qui se passe ici | Fichier |
|---|---|---|
| Chargement | lecture du PDF, marqueurs de page | `rag/ingestion/pdf_loader.py` |
| Extraction / nettoyage | le LLM sort des sujets structurés (Pydantic), rien d'inventé | `rag/ingestion/subject_extractor.py` |
| Validation | le code fixe le statut : actif, quarantaine, expiré | `rag/ingestion/validation_rules.py` |
| Chunking | un chunk = un sujet entier | `rag/indexing/subject_text.py` |
| Embeddings | Gemini 768 dim, `RETRIEVAL_DOCUMENT` / `RETRIEVAL_QUERY` | `rag/embeddings.py` |
| Indexation | Supabase + pgvector (hnsw, cosinus) | `repositories/subjects_repository.py`, `database/*.sql` |
| Orchestration | un seul chemin d'écriture en base | `rag/ingestion/ingestion_pipeline.py` |
| Retrieval | multi-requêtes (profil, projets, expériences) -> fonction SQL `match_sujets`, + recherche par mots-clés | `rag/retrieval/subject_retriever.py`, `rag/retrieval/hybrid_ranking.py` |
| Génération | profil du CV, puis note 0-10 et raison par sujet candidat (LLM) | `rag/generation/matching_chains.py` |

## Flux de matching

CV PDF -> `cv_text_extractor` -> `profile_chain` (profil) -> requêtes (profil, chaque projet, chaque expérience) -> recherche vectorielle + recherche par mots-clés -> classement hybride (0,4 vecteur + 0,6 mots-clés) -> `rerank_chain` (note 0-10 + raison, seuil 6) -> réponse JSON. Si le LLM est indisponible, les 15 meilleurs du classement hybride sont affichés sans raison. Le CV n'est jamais stocké.

LLM : Gemini d'abord, puis Groq en secours (`resilient` dans `rag/chat_model.py`) ; Ollama est réservé à l'extraction nocturne.

## Agent de découverte

`daily_run` : expiration des sujets périmés, puis `discovery_agent` (LangGraph) explore les sites de confiance et propose des sources, puis le code traite la file. L'agent ne peut pas écrire en base : `guardrails.py` (robots.txt, Content-Signal, domaines bloqués, liste blanche, taille, quotas) décide de tout.

## Principes

- Le LLM propose, le code décide.
- Contenu externe (CV, PDF, pages) = donnée, jamais instruction.
- Une couche ne parle qu'à la suivante : routes -> services -> rag / repositories -> Supabase / Gemini.
