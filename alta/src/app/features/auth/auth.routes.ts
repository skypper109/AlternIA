import { Routes } from '@angular/router';

export const authRoutes: Routes = [
  {
    path: 'connexion',
    loadComponent: () => import('./connexion/connexion.composant').then(m => m.ConnexionComposant),
    title: 'Connexion – Alternia',
  },
  {
    path: 'inscription-etablissement',
    loadComponent: () => import('./inscription-etablissement/inscription-etablissement.composant').then(m => m.InscriptionEtablissementComposant),
    title: 'Inscription Établissement – Alternia',
  },
  {
    path: 'inscription-parent',
    loadComponent: () => import('./inscription-parent/inscription-parent.composant').then(m => m.InscriptionParentComposant),
    title: 'Inscription Parent – Alternia',
  },
  {
    path: '',
    redirectTo: 'connexion',
    pathMatch: 'full',
  },
];
