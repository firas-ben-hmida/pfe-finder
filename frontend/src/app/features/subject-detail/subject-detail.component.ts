import { TagListComponent } from '../../shared/tag-list/tag-list.component';
import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, input, signal } from '@angular/core';
import { Location } from '@angular/common';

import { ApiService } from '../../core/api.service';
import { errorMessage } from '../../core/error-message';
import { ApplyInfo, SubjectDetail } from '../../core/models';

@Component({
  selector: 'app-subject-detail',
  standalone: true,
  imports: [DatePipe, TagListComponent],
  templateUrl: './subject-detail.component.html',
  styleUrl: './subject-detail.component.scss',
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
