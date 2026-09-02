import { Component, signal, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ThemeService } from '../../core/services/theme.service';
import { NotificationService } from '../../core/services/notification.service';
import { ROUTES_APP } from '../../core/constantes/routes.constantes';

interface NavItem {
  label: string;
  route: string;
  icon: string;
  badge?: number;
}

@Component({
  selector: 'app-layout-etablissement',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './layout-etablissement.composant.html',
  styleUrl: './layout-etablissement.composant.scss',
})
export class LayoutEtablissementComposant {
  private readonly authService = inject(AuthService);
  private readonly themeService = inject(ThemeService);
  private readonly notifService = inject(NotificationService);

  readonly routes = ROUTES_APP;
  readonly utilisateur = this.authService.utilisateurCourant;
  readonly estModeNuit = computed(() => this.themeService.theme() === 'dark');

  sidebarExpanded = signal(true);
  notificationsOuvertes = signal(false);

  /** Groupe principal — navigation courante */
  readonly navItemsPrimary: NavItem[] = [
    { label: 'Tableau de bord',      route: ROUTES_APP.ETABLISSEMENT.TABLEAU_DE_BORD, icon: 'dashboard' },
    { label: 'Centre de Pilotage',   route: ROUTES_APP.ETABLISSEMENT.PILOTAGE,         icon: 'pilotage'  },
    { label: 'AlternIA Insights',    route: ROUTES_APP.ETABLISSEMENT.INSIGHTS,          icon: 'insights'  },
    { label: 'Élèves & Classes',     route: ROUTES_APP.ETABLISSEMENT.APPRENANTS,        icon: 'students'  },
    { label: 'Supervision Boîtiers', route: ROUTES_APP.ETABLISSEMENT.SUPERVISION_BOITIERS, icon: 'box'  },
    { label: 'Statistiques',         route: ROUTES_APP.ETABLISSEMENT.STATISTIQUES,     icon: 'stats'     },
    { label: 'Avatars IA',           route: ROUTES_APP.ETABLISSEMENT.AVATARS,           icon: 'avatar'    },
    { label: 'Studio vocal',         route: ROUTES_APP.ETABLISSEMENT.STUDIO_VOCAL,      icon: 'mic'       },
    { label: 'Rapports',             route: ROUTES_APP.ETABLISSEMENT.RAPPORTS,          icon: 'report'    },
  ];

  /** Groupe configuration — en bas de nav */
  readonly navItemsSecondary: NavItem[] = [
    { label: 'Paramètres', route: ROUTES_APP.ETABLISSEMENT.PARAMETRES, icon: 'settings' },
  ];

  basculerSidebar(): void {
    this.sidebarExpanded.update(v => !v);
  }

  basculerTheme(): void {
    this.themeService.basculerTheme();
  }

  seDeconnecter(): void {
    this.authService.deconnexion();
  }

  basculerNotifications(): void {
    this.notificationsOuvertes.update(v => !v);
    if (this.notificationsOuvertes()) {
      this.notifService.info('Notifications établissement', '3 boîtiers synchronisés avec le serveur de Bamako.');
    }
  }
}
