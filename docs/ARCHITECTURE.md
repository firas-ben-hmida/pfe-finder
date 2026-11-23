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
| Retrieval | retriever LangChain -> fonction SQL `match_sujets` | `rag/retrieval/subject_retriever.py` |
| Génération | profil du CV, puis justification limitée aux sujets récupérés | `rag/generation/matching_chains.py` |

## Flux de matching

CV PDF -> `cv_text_extractor` -> `profile_chain` (profil) -> requête vectorielle -> `SubjectRetriever` (top-k) -> `reason_chain` (une phrase par sujet) -> réponse JSON. Le CV n'est jamais stocké.

## Agent de découverte

`daily_run` : expiration des sujets périmés, puis `discovery_agent` (LangGraph) cherche et propose des sources, puis le code traite la file. L'agent ne peut pas écrire en base : `guardrails.py` (robots.txt, Content-Signal, domaines bloqués, liste blanche, taille, quotas) décide de tout.

## Principes

- Le LLM propose, le code décide.
- Contenu externe (CV, PDF, pages) = donnée, jamais instruction.
- Une couche ne parle qu'à la suivante : routes -> services -> rag / repositories -> Supabase / Gemini.
