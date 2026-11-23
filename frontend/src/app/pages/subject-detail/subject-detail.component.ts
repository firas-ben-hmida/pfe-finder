import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, input, signal } from '@angular/core';
import { Location } from '@angular/common';

import { ApiService } from '../../core/api.service';
import { errorMessage } from '../../core/error-message';
import { ApplyInfo, SubjectDetail } from '../../core/models';

@Component({
  selector: 'app-subject-detail',
  standalone: true,
  imports: [DatePipe],
  template: `
    <a class="back" (click)="back()" href="javascript:void(0)">← Retour aux résultats</a>

    @if (error()) {
      <p class="error">{{ error() }}</p>
    }

    @if (subject(); as s) {
      <article class="card">
        <h1>{{ s.titre }}</h1>
        <p class="muted">
          {{ s.entreprise }}{{ s.ville ? ' · ' + s.ville : '' }}{{ s.annee ? ' · ' + s.annee : '' }}{{ s.numero ? ' · n° ' + s.numero : '' }}
        </p>
        <p class="description">{{ s.description || 'Aucune description disponible.' }}</p>
        <div class="tags">
          @for (t of s.technos; track t) {
            <span class="tag">{{ t }}</span>
          }
        </div>
        @if (s.source_url) {
          <p class="muted">
            Source : <a [href]="s.source_url" target="_blank" rel="noopener noreferrer">catalogue de l'entreprise</a>
            @if (s.page_source) { (page {{ s.page_source }}) }
          </p>
        }
        <button class="primary" (click)="toggleApply()">
          {{ apply() ? 'Masquer' : 'Comment postuler' }}
        </button>
      </article>

      @if (apply(); as a) {
        <article class="card">
          <h2>Comment postuler</h2>
          <p><strong>Mode :</strong> {{ modes[a.mode_candidature] }}</p>
          @if (a.contact_candidature) {
            <p><strong>Contact :</strong> {{ a.contact_candidature }}</p>
          }
          @if (a.documents_requis.length) {
            <p><strong>Documents demandés :</strong></p>
            <ul>
              @for (d of a.documents_requis; track d) { <li>{{ d }}</li> }
            </ul>
          }
          @if (a.etapes_candidature) {
            <p><strong>Étapes :</strong> {{ a.etapes_candidature }}</p>
          }
          @if (a.date_limite) {
            <p><strong>Date limite :</strong> {{ a.date_limite | date: 'dd/MM/yyyy' }}</p>
          }
          @if (a.mode_candidature === 'inconnu' && !a.contact_candidature) {
            <p class="muted">La procédure n'est pas indiquée dans le catalogue : consulte la source.</p>
          }
        </article>
      }
    } @else if (!error()) {
      <p class="muted">Chargement…</p>
    }
  `,
  styles: [
    `
      .description { white-space: pre-line; }
      .tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.8rem 0; }
      .tag { background: #e2e8f0; border-radius: 999px; padding: 0.15rem 0.7rem; font-size: 0.85rem; }
    `,
  ],
})
export class SubjectDetailComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly location = inject(Location);

  /** Paramètre de route :id (withComponentInputBinding). */
  readonly id = input.required<string>();

  readonly subject = signal<SubjectDetail | null>(null);
  readonly apply = signal<ApplyInfo | null>(null);
  readonly error = signal<string | null>(null);

  readonly modes: Record<ApplyInfo['mode_candidature'], string> = {
    email: 'Par email',
    formulaire: 'Via un formulaire en ligne',
    portail: 'Via le portail carrière',
    inconnu: 'Non précisé',
  };

  ngOnInit(): void {
    this.api.getSubject(Number(this.id())).subscribe({
      next: (s) => this.subject.set(s),
      error: (err) => this.error.set(errorMessage(err)),
    });
  }

  toggleApply(): void {
    if (this.apply()) {
      this.apply.set(null);
      return;
    }
    this.api.getApplyInfo(Number(this.id())).subscribe({
      next: (a) => this.apply.set(a),
      error: (err) => this.error.set(errorMessage(err)),
    });
  }

  back(): void {
    this.location.back();
  }
}
