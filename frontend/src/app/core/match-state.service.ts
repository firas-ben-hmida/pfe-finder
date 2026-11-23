import { Injectable, signal } from '@angular/core';

import { SubjectSummary } from './models';

/** Résultats du dernier matching, gardés en mémoire seulement (rien n'est stocké dans le navigateur). */
@Injectable({ providedIn: 'root' })
export class MatchStateService {
  readonly results = signal<SubjectSummary[] | null>(null);
}
