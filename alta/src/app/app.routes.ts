import { Routes } from '@angular/router';
import { ROUTES_APP } from './core/constantes/routes.constantes';

export const routes: Routes = [
  // Auth
  {
    path: 'auth',
    loadChildren: () => import('./features/auth/auth.routes').then(m => m.authRoutes),
  },

  // Portail Établissement
  {
    path: 'etablissement',
    loadChildren: () => import('./features/etablissement/etablissement.routes').then(m => m.etablissementRoutes),
  },

  // Portail Parent
  {
    path: 'parent',
    loadChildren: () => import('./features/parent/parent.routes').then(m => m.parentRoutes),
  },

  // Root redirect → connexion
  {
    path: '',
    redirectTo: ROUTES_APP.AUTH.CONNEXION,
    pathMatch: 'full',
  },

  // Wildcard → connexion
  {
    path: '**',
    redirectTo: ROUTES_APP.AUTH.CONNEXION,
  },
];
