import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { MatchStateService } from '../../core/match-state.service';
import { SubjectSummary } from '../../core/models';
import { TagListComponent } from '../../shared/tag-list/tag-list.component';

type Level = 'top' | 'good';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [RouterLink, TagListComponent],
  templateUrl: './results.component.html',
  styleUrl: './results.component.scss',
})
export class ResultsComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly state = inject(MatchStateService);

  readonly selectedCompany = signal<string | null>(null);

  readonly all = computed(() => this.state.results() ?? []);

  /** Entreprises présentes dans les résultats, avec leur nombre de sujets. */
  readonly companies = computed(() => {
    const counts = new Map<string, number>();
    for (const s of this.all()) {
      counts.set(s.entreprise, (counts.get(s.entreprise) ?? 0) + 1);
    }
    return [...counts.entries()].map(([name, count]) => ({ name, count }));
  });

  readonly visible = computed(() => {
    const company = this.selectedCompany();
    return company ? this.all().filter((s) => s.entreprise === company) : this.all();
  });

  ngOnInit(): void {
    // Page rechargée : les résultats ne sont pas conservés, retour à l'accueil.
    if (this.state.results() === null) {
      this.router.navigate(['/']);
    }
  }

  select(company: string | null): void {
    this.selectedCompany.set(company);
  }

  /** Position du sujet dans l'échelle des scores de cette recherche (0 à 1) : pertinence relative, pas un pourcentage. */
  strength(s: SubjectSummary): number {
    const scores = this.all().map((x) => x.score ?? 0);
    const hi = Math.max(...scores);
    const lo = Math.min(...scores);
    return hi === lo ? 1 : ((s.score ?? lo) - lo) / (hi - lo);
  }

  level(s: SubjectSummary): Level {
    return this.strength(s) >= 0.66 ? 'top' : 'good';
  }

  levelLabel(s: SubjectSummary): string {
    return this.level(s) === 'top' ? 'Très pertinent' : 'Pertinent';
  }

  barWidth(s: SubjectSummary): number {
    return Math.round(35 + 65 * this.strength(s));
  }

  /** Nettoie les technologies : points finaux et libellés trop longs pour une pastille. */
  techs(s: SubjectSummary): string[] {
    return s.technos
      .map((t) => t.replace(/[.\s]+$/, ''))
      .filter((t) => t.length > 0 && t.length <= 40)
      .slice(0, 8);
  }
}
