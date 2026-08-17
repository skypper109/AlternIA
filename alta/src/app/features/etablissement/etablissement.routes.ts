import { Routes } from '@angular/router';
import { LayoutEtablissementComposant } from '../../layout/layout-etablissement/layout-etablissement.composant';
import { etablissementGarde } from '../../core/gardes/etablissement.garde';

export const etablissementRoutes: Routes = [
  {
    path: '',
    component: LayoutEtablissementComposant,
    canActivate: [etablissementGarde],
    children: [
      {
        path: 'tableau-de-bord',
        loadComponent: () => import('./tableau-de-bord/tableau-de-bord-etablissement.composant').then(m => m.TableauDeBordEtablissementComposant),
        title: 'Tableau de bord – Alternia Établissement',
      },

      {
        path: 'insights',
        loadComponent: () => import('./insights/alternia-insights.composant').then(m => m.AlternIAInsightsComposant),
        title: 'AlternIA Insights – Intelligence Pédagogique',
      },
      {
        path: 'supervision-boitiers',
        loadComponent: () => import('./apprenants/liste-apprenants.composant').then(m => m.ListeApprenantsComposant),
        title: 'Supervision des Boîtiers – Alternia',
      },
      {
        path: 'statistiques',
        loadComponent: () => import('./statistiques/statistiques-pedagogiques.composant').then(m => m.StatistiquesPedagogiquesComposant),
        title: 'Statistiques – Alternia',
      },
      {
        path: 'avatars',
        loadComponent: () => import('./avatars/gestion-avatars.composant').then(m => m.GestionAvatarsComposant),
        title: 'Avatars – Alternia',
      },
      {
        path: 'studio-vocal',
        loadComponent: () => import('./studio-vocal/studio-vocal.composant').then(m => m.StudioVocalComposant),
        title: 'Studio vocal – Alternia',
      },
      {
        path: 'rapports',
        loadComponent: () => import('./rapports/rapports.composant').then(m => m.RapportsComposant),
        title: 'Rapports – Alternia',
      },
      {
        path: 'parametres',
        loadComponent: () => import('./parametres/parametres-etablissement.composant').then(m => m.ParametresEtablissementComposant),
        title: 'Paramètres – Alternia',
      },
      {
        path: '',
        redirectTo: 'tableau-de-bord',
        pathMatch: 'full',
      },
    ],
  },
];
