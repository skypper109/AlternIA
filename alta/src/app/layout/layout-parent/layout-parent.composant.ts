import { Component, signal, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ThemeService } from '../../core/services/theme.service';
import { ROUTES_APP } from '../../core/constantes/routes.constantes';

interface ParentNavItem {
  label: string;
  route: string;
  icon: string;
  badge?: number;
}

@Component({
  selector: 'app-layout-parent',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './layout-parent.composant.html',
  styleUrl: './layout-parent.composant.scss',
})
export class LayoutParentComposant {
  private readonly authService = inject(AuthService);
  private readonly themeService = inject(ThemeService);

  readonly routes = ROUTES_APP;
  readonly utilisateur = this.authService.utilisateurCourant;
  readonly estModeNuit = computed(() => this.themeService.theme() === 'dark');

  sidebarExpanded = signal(true);

  readonly navItems: ParentNavItem[] = [
    { label: 'Accueil',               route: ROUTES_APP.PARENT.TABLEAU_DE_BORD,     icon: 'home'     },
    { label: 'Profils pédagogiques',  route: ROUTES_APP.PARENT.ENSEIGNANT_IA,       icon: 'bot'      },
    { label: 'Programme de Révision', route: ROUTES_APP.PARENT.PROGRAMME_REVISION, icon: 'calendar' },
    { label: 'Matières Consultées',   route: ROUTES_APP.PARENT.PROGRESSION,         icon: 'book'     },
    { label: 'Historique d\'Activité', route: ROUTES_APP.PARENT.HISTORIQUE,         icon: 'activity' },
    { label: 'Alertes',               route: ROUTES_APP.PARENT.ALERTES,             icon: 'bell',  badge: 2 },
    { label: 'Mon Boîtier',           route: ROUTES_APP.PARENT.BOITIER,             icon: 'cpu'      },
    { label: 'Paramètres',            route: ROUTES_APP.PARENT.PARAMETRES,          icon: 'settings' },
  ];

  basculerSidebar(): void {
    this.sidebarExpanded.update(v => !v);
  }

  basculerTheme(): void { this.themeService.basculerTheme(); }
  seDeconnecter(): void { this.authService.deconnexion(); }
}
