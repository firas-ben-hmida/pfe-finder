import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', loadComponent: () => import('./features/upload/upload.component').then((m) => m.UploadComponent) },
  { path: 'resultats', loadComponent: () => import('./features/results/results.component').then((m) => m.ResultsComponent) },
  { path: 'sujets/:id', loadComponent: () => import('./features/subject-detail/subject-detail.component').then((m) => m.SubjectDetailComponent) },
  { path: '**', redirectTo: '' },
];
