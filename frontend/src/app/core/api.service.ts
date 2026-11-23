import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_URL } from './api.config';
import { ApplyInfo, SubjectDetail, SubjectSummary } from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  matchCv(file: File, cities: string[] = []): Observable<SubjectSummary[]> {
    const form = new FormData();
    form.append('file', file);
    cities.forEach((city) => form.append('villes', city));
    return this.http.post<SubjectSummary[]>(`${API_URL}/match`, form);
  }

  getCities(): Observable<string[]> {
    return this.http.get<string[]>(`${API_URL}/cities`);
  }

  getSubject(id: number): Observable<SubjectDetail> {
    return this.http.get<SubjectDetail>(`${API_URL}/subjects/${id}`);
  }

  getApplyInfo(id: number): Observable<ApplyInfo> {
    return this.http.get<ApplyInfo>(`${API_URL}/subjects/${id}/apply`);
  }
}
