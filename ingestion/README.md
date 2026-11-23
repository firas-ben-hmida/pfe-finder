# Ingestion (à venir)

Pipeline qui transforme un PFE book en sujets exploitables par l'API.

```
PDF -> texte par page (PyMuPDF) -> sujets JSON (Gemini, schéma Pydantic)
    -> hash anti-doublons -> embeddings (RETRIEVAL_DOCUMENT) -> table sujets
```

## À prévoir

- Hash du fichier et de chaque sujet (`documents_traites`, `hash_sujet`).
- Extraction de la section « Comment postuler » de chaque entreprise.
- Statut `quarantaine` par défaut, `actif` si les contrôles passent.
- Plafond de PDF par exécution pour rester dans le quota gratuit.
- Les PDF ne sont jamais versionnés ni hébergés : on garde le texte extrait et le lien vers la source.
