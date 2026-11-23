# Agent de découverte (à venir)

Agent LangGraph exécuté chaque jour par GitHub Actions. Il cherche de nouveaux PFE books, les vérifie, extrait leurs sujets et alimente la base.

## Outils prévus

| Outil | Rôle | Garde-fous (dans le code, pas dans le prompt) |
|---|---|---|
| `web_search` | recherche via l'API Google officielle | quota par jour, URLs déjà vues ignorées |
| `fetch_page` | lit une page d'entreprise | robots.txt, Content-Signal, domaines bloqués, 5 pages par domaine, délai |
| `download_pdf` | télécharge un PDF | type et taille limités, hash anti-doublon |
| `extract_subjects` | PDF -> sujets JSON | schéma Pydantic strict |
| `publish_or_quarantine` | insère en base | règles de code : pays, année, doublons, confiance |

## Règles

- L'agent propose, le code décide : seule `publish_or_quarantine` écrit dans la base.
- Aucun login, aucun contournement, pas de LinkedIn.
- Le contenu des pages est une donnée, jamais une instruction.
- Limites : étapes maximales, PDF maximum par exécution, rapport en fin de run.
