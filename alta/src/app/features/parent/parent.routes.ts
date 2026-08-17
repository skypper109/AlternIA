import { Routes } from '@angular/router';
import { LayoutParentComposant } from '../../layout/layout-parent/layout-parent.composant';
import { parentGarde } from '../../core/gardes/parent.garde';

export const parentRoutes: Routes = [
  {
    path: '',
    component: LayoutParentComposant,
    canActivate: [parentGarde],
    children: [
      {
        path: 'tableau-de-bord',
        loadComponent: () => import('./tableau-de-bord/tableau-de-bord-parent.composant').then(m => m.TableauDeBordParentComposant),
        title: 'Mon espace – Alternia Parent',
      },
      {
        path: 'enseignant-ia',
        loadComponent: () => import('./enseignant-ia/enseignant-ia.composant').then(m => m.EnseignantIaComposant),
        title: 'Profils pédagogiques – Alternia Parent',
      },
      {
        path: 'programme-revision',
        loadComponent: () => import('./programme-revision/programme-revision.composant').then(m => m.ProgrammeRevisionComposant),
        title: 'Programme de Révision – Alternia Parent',
      },
      {
        path: 'progression-enfant',
        loadComponent: () => import('./progression-enfant/progression-enfant.composant').then(m => m.ProgressionEnfantComposant),
        title: 'Progression – Alternia Parent',
      },
      {
        path: 'historique',
        loadComponent: () => import('./historique/historique-apprentissage.composant').then(m => m.HistoriqueApprentissageComposant),
        title: 'Historique – Alternia Parent',
      },
      {
        path: 'alertes',
        loadComponent: () => import('./alertes/alertes.composant').then(m => m.AlertesComposant),
        title: 'Alertes – Alternia Parent',
      },
      {
        path: 'boitier',
        loadComponent: () => import('./boitier/gestion-boitier.composant').then(m => m.GestionBoitierComposant),
        title: 'Mon boîtier – Alternia Parent',
      },
      {
        path: 'parametres',
        loadComponent: () => import('./parametres/parametres-parent.composant').then(m => m.ParametresParentComposant),
        title: 'Paramètres – Alternia Parent',
      },
      {
        path: '',
        redirectTo: 'tableau-de-bord',
        pathMatch: 'full',
      },
    ],
  },
];
