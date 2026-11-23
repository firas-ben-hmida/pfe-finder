export interface SubjectSummary {
  id: number;
  entreprise: string;
  titre: string;
  technos: string[];
  ville: string | null;
  pays: string | null;
  annee: number | null;
  score: number | null;
  raison: string | null;
}

export interface SubjectDetail extends SubjectSummary {
  numero: string | null;
  description: string | null;
  source_url: string | null;
  page_source: number | null;
  date_limite: string | null;
}

export interface ApplyInfo {
  mode_candidature: 'email' | 'formulaire' | 'portail' | 'inconnu';
  contact_candidature: string | null;
  documents_requis: string[];
  etapes_candidature: string | null;
  date_limite: string | null;
  source_url: string | null;
}
