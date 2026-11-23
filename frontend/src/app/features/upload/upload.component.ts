import { Component, OnInit, inject, signal } from '@angular/core';
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
export class UploadComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly state = inject(MatchStateService);
  private readonly router = inject(Router);

  readonly file = signal<File | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly cities = signal<string[]>([]);
  readonly selectedCities = signal<string[]>([]);

  ngOnInit(): void {
    // Les villes sont facultatives : si la liste n'est pas disponible, on cherche partout.
    this.api.getCities().subscribe({ next: (c) => this.cities.set(c), error: () => this.cities.set([]) });
  }

  toggleCity(city: string): void {
    this.selectedCities.update((list) => (list.includes(city) ? list.filter((c) => c !== city) : [...list, city]));
  }

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
    this.api.matchCv(file, this.selectedCities()).subscribe({
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
