import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { errorMessage } from '../../core/error-message';
import { MatchStateService } from '../../core/match-state.service';

@Component({
  selector: 'app-upload',
  standalone: true,
  templateUrl: './upload.component.html',
  styleUrl: './upload.component.scss',
})
export class UploadComponent {
  private readonly api = inject(ApiService);
  private readonly state = inject(MatchStateService);
  private readonly router = inject(Router);

  readonly file = signal<File | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  onFile(event: Event): void {
    const chosen = (event.target as HTMLInputElement).files?.[0] ?? null;
    this.error.set(null);
    if (chosen && chosen.size > 5 * 1024 * 1024) {
      this.file.set(null);
      this.error.set('Fichier trop volumineux (5 Mo maximum).');
      return;
    }
    this.file.set(chosen);
  }

  submit(): void {
    const file = this.file();
    if (!file) return;
    this.loading.set(true);
    this.error.set(null);
    this.api.matchCv(file).subscribe({
      next: (results) => {
        this.state.results.set(results);
        this.router.navigate(['/resultats']);
      },
      error: (err) => {
        this.error.set(errorMessage(err));
        this.loading.set(false);
      },
    });
  }
}
