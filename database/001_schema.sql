-- Schéma initial. À exécuter une fois dans l'éditeur SQL de Supabase.

create extension if not exists vector;

-- Sujets de PFE. statut : actif | quarantaine | expire
create table if not exists sujets (
  id bigint generated always as identity primary key,
  hash_sujet text unique not null,
  entreprise text not null,
  numero text,
  titre text not null,
  description text,
  technos text[] default '{}',
  ville text,
  pays text default 'Tunisie',
  annee int,
  mode_candidature text default 'inconnu',
  contact_candidature text,
  documents_requis text[] default '{}',
  etapes_candidature text,
  date_limite date,
  statut text default 'quarantaine',
  confiance real,
  source_url text,
  page_source int,
  embedding vector(768),
  created_at timestamptz default now()
);

-- Documents (PFE books) déjà traités, pour ne jamais les retraiter.
create table if not exists documents_traites (
  id bigint generated always as identity primary key,
  url_normalisee text unique,
  hash_fichier text unique,
  entreprise text,
  annee int,
  statut text default 'traite',
  origine text default 'manuel',
  created_at timestamptz default now()
);

-- File d'attente alimentée par l'agent de découverte.
create table if not exists sources_a_traiter (
  id bigint generated always as identity primary key,
  url text not null,
  url_normalisee text unique not null,
  titre text,
  annee int,
  statut text default 'a_traiter',
  created_at timestamptz default now()
);

create index if not exists sujets_embedding_idx
  on sujets using hnsw (embedding vector_cosine_ops);
