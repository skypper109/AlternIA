import { Injectable, signal, computed, inject } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { Utilisateur, SessionUtilisateur } from '../modeles/utilisateur.modele';
import { RoleUtilisateur } from '../enums';
import { ROUTES_APP } from '../constantes/routes.constantes';
import { environment } from '../../../environments/environment';

const SESSION_KEY = 'alternia_session';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly router = inject(Router);
  private readonly http = inject(HttpClient);

  private _session = signal<SessionUtilisateur | null>(this.chargerSession());

  readonly utilisateurCourant = computed(() => this._session()?.utilisateur ?? null);
  readonly estConnecte = computed(() => this._session() !== null);
  readonly roleUtilisateur = computed(() => this._session()?.utilisateur?.role ?? null);

  async connexion(email: string, motDePasse: string): Promise<boolean> {
    const resp = await firstValueFrom(
      this.http.post<{ succes: boolean; token: string; expiresAt: string; utilisateur: any }>(
        `${environment.apiUrl}/auth/connexion`,
        { email: email.trim(), mot_de_passe: motDePasse }
      )
    );

    if (resp && resp.succes && resp.utilisateur) {
      const role = resp.utilisateur.role === 'admin_ecole' ? RoleUtilisateur.ADMIN_ECOLE : RoleUtilisateur.PARENT;
      const utilisateur: Utilisateur = {
        id: resp.utilisateur.id,
        email: resp.utilisateur.email,
        role,
        nomComplet: resp.utilisateur.nomComplet,
        avatar: resp.utilisateur.avatar,
        dateCreation: resp.utilisateur.dateCreation ? new Date(resp.utilisateur.dateCreation) : new Date(),
        dernierAcces: new Date(),
        actif: resp.utilisateur.actif ?? true,
      };

      const session: SessionUtilisateur = {
        utilisateur,
        token: resp.token,
        expiresAt: new Date(resp.expiresAt),
      };

      this.sauvegarderSession(session);
      this._session.set(session);
      return true;
    }

    throw new Error('Identifiants invalides');
  }

  deconnexion(): void {
    localStorage.removeItem(SESSION_KEY);
    this._session.set(null);
    this.router.navigate([ROUTES_APP.AUTH.CONNEXION]);
  }

  redirectionSelonRole(): void {
    const role = this.roleUtilisateur();
    if (role === RoleUtilisateur.ADMIN_ECOLE) {
      this.router.navigate([ROUTES_APP.ETABLISSEMENT.TABLEAU_DE_BORD]);
    } else if (role === RoleUtilisateur.PARENT) {
      this.router.navigate([ROUTES_APP.PARENT.TABLEAU_DE_BORD]);
    }
  }

  private chargerSession(): SessionUtilisateur | null {
    try {
      const raw = localStorage.getItem(SESSION_KEY);
      if (!raw) return null;
      const session: SessionUtilisateur = JSON.parse(raw);
      if (new Date(session.expiresAt) < new Date()) {
        localStorage.removeItem(SESSION_KEY);
        return null;
      }
      return session;
    } catch {
      return null;
    }
  }

  private sauvegarderSession(session: SessionUtilisateur): void {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  }
}
