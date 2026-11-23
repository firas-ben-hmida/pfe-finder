import { HttpErrorResponse } from '@angular/common/http';

export function errorMessage(err: unknown): string {
  if (err instanceof HttpErrorResponse) {
    if (err.status === 0) return "Impossible de joindre le serveur. Vérifie que l'API est démarrée.";
    if (err.status === 429) return 'Trop de demandes, réessaie dans une minute.';
    if (typeof err.error?.detail === 'string') return err.error.detail;
  }
  return 'Une erreur est survenue.';
}
