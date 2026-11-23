import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { MatchStateService } from '../../core/match-state.service';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [RouterLink],
  template: `
    <a routerLink="/" class="back">← Changer de CV</a>
    <h1>Sujets qui te correspondent</h1>

    @if (results().length === 0) {
      <p class="muted">Aucun sujet trouvé pour le moment.</p>
    }

    @for (s of results(); track s.id) {
      <article class="card">
        <header>
          <h2>{{ s.titre }}</h2>
          <span class="muted">{{ s.entreprise }}{{ s.ville ? ' · ' + s.ville : '' }}{{ s.annee ? ' · ' + s.annee : '' }}</span>
        </header>
        @if (s.raison) {
          <p class="reason">{{ s.raison }}</p>
        }
        <div class="tags">
          @for (t of s.technos; track t) {
            <span class="tag">{{ t }}</span>
          }
        </div>
        <a class="primary" [routerLink]="['/sujets', s.id]">Voir le détail</a>
      </article>
    }
  `,
  styles: [
    `
      .reason { background: #f1f5f9; border-left: 4px solid #2563eb; padding: 0.6rem 0.8rem; border-radius: 6px; }
      .tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.8rem 0; }
      .tag { background: #e2e8f0; border-radius: 999px; padding: 0.15rem 0.7rem; font-size: 0.85rem; }
      h2 { margin: 0 0 0.2rem; font-size: 1.15rem; }
    `,
  ],
})
export class ResultsComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly state = inject(MatchStateService);

  readonly results = () => this.state.results() ?? [];

  ngOnInit(): void {
    // Page rechargée : les résultats ne sont pas conservés, retour à l'accueil.
    if (this.state.results() === null) {
      this.router.navigate(['/']);
    }
  }
}
