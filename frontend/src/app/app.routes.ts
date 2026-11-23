import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./pages/upload/upload.component').then((m) => m.UploadComponent) },
  { path: 'resultats', loadComponent: () => import('./pages/results/results.component').then((m) => m.ResultsComponent) },
  { path: 'sujets/:id', loadComponent: () => import('./pages/subject-detail/subject-detail.component').then((m) => m.SubjectDetailComponent) },
  { path: '**', redirectTo: '' },
];
