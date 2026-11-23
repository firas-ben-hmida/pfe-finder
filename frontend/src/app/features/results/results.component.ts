import { TagListComponent } from '../../shared/tag-list/tag-list.component';
import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { MatchStateService } from '../../core/match-state.service';

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

  readonly results = () => this.state.results() ?? [];

  ngOnInit(): void {
    // Page rechargée : les résultats ne sont pas conservés, retour à l'accueil.
    if (this.state.results() === null) {
      this.router.navigate(['/']);
    }
  }
}
