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

  /** Note de pertinence du sujet (0 à 1) : la note sur 10 donnée par le LLM, ou le score hybride en mode dégradé. */
  strength(s: SubjectSummary): number {
    return Math.min(1, Math.max(0, s.score ?? 0));
  }

  level(s: SubjectSummary): Level {
    return this.strength(s) >= 0.8 ? 'top' : 'good';
  }

  levelLabel(s: SubjectSummary): string {
    return this.level(s) === 'top' ? 'Très pertinent' : 'Pertinent';
  }

  barWidth(s: SubjectSummary): number {
    return Math.round(this.strength(s) * 100);
  }

  /** Nettoie les technologies : points finaux et libellés trop longs pour une pastille. */
  techs(s: SubjectSummary): string[] {
    return s.technos
      .map((t) => t.replace(/[.\s]+$/, ''))
      .filter((t) => t.length > 0 && t.length <= 40)
      .slice(0, 8);
  }
}
