import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_URL } from './api.config';
import { ApplyInfo, SubjectDetail, SubjectSummary } from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  matchCv(file: File): Observable<SubjectSummary[]> {
    const form = new FormData();
    form.append('file', file);
    return this.http.post<SubjectSummary[]>(`${API_URL}/match`, form);
  }

  getSubject(id: number): Observable<SubjectDetail> {
    return this.http.get<SubjectDetail>(`${API_URL}/subjects/${id}`);
  }

  getApplyInfo(id: number): Observable<ApplyInfo> {
    return this.http.get<ApplyInfo>(`${API_URL}/subjects/${id}/apply`);
  }
}
