-- Recherche vectorielle appelée par l'API (supabase.rpc("match_sujets", ...)).
-- Ne renvoie que les sujets actifs. similarity = 1 - distance cosinus.

create or replace function match_sujets(
  query_embedding vector(768),
  match_count int default 8,
  filter_pays text default 'Tunisie'
)
returns table (
  id bigint,
  entreprise text,
  titre text,
  technos text[],
  ville text,
  pays text,
  annee int,
  similarity float
)
language sql
stable
as $$
  select
    s.id,
    s.entreprise,
    s.titre,
    s.technos,
    s.ville,
    s.pays,
    s.annee,
    1 - (s.embedding <=> query_embedding) as similarity
  from sujets s
  where s.statut = 'actif'
    and s.embedding is not null
    and (filter_pays is null or s.pays = filter_pays)
  order by s.embedding <=> query_embedding
  limit match_count;
$$;
