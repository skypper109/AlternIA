import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators, FormsModule } from '@angular/forms';
import { NotificationService } from '../../../core/services/notification.service';
import { AuthService } from '../../../core/services/auth.service';
import { Utilisateur } from '../../../core/modeles/utilisateur.modele';
import { RoleUtilisateur } from '../../../core/enums';

type SectionParametre = 'profil' | 'utilisateurs' | 'etablissement' | 'securite';

@Component({
  selector: 'app-parametres-etablissement',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  template: `
<div class="page-content stagger-children">
  
  <!-- En-tête -->
  <div class="page-header">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
      <div>
        <h1 class="page-header__title">Profil & Gestion des Utilisateurs</h1>
        <p class="page-header__subtitle">Gérez vos identifiants d'authentification et les comptes du réseau</p>
      </div>
      @if (sectionActive() === 'utilisateurs') {
        <button class="btn btn-primary btn-sm" (click)="ouvrirModalCreerUtilisateur()" id="btn-creer-utilisateur">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M7 2V12M2 7H12" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          + Nouveau Compte
        </button>
      }
    </div>
  </div>

  <div class="settings-layout">
    <!-- Navigation Latérale -->
    <div class="settings-nav card">
      @for (section of sections; track section.id) {
        <button
          class="settings-nav-item"
          [class.settings-nav-item--active]="sectionActive() === section.id"
          (click)="sectionActive.set(section.id)"
          [id]="'nav-param-' + section.id"
        >
          <span class="settings-nav-icon">
            @switch (section.id) {
              @case ('profil') {
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="5.5" r="3" stroke="currentColor" stroke-width="1.3"/>
                  <path d="M2.5 14C2.5 11 5 9 8 9C11 9 13.5 11 13.5 14" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                </svg>
              }
              @case ('utilisateurs') {
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="6" cy="5" r="2.5" stroke="currentColor" stroke-width="1.3"/>
                  <path d="M2 13C2 10.5 4 9 6 9C8 9 10 10.5 10 13" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                  <circle cx="11.5" cy="5" r="2" stroke="currentColor" stroke-width="1.3"/>
                  <path d="M11 9C12.5 9 14 10 14 12" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                </svg>
              }
              @case ('etablissement') {
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M2 14V5L8 2L14 5V14H10V9H6V14H2Z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
                </svg>
              }
              @case ('securite') {
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <rect x="3" y="7" width="10" height="7" rx="2" stroke="currentColor" stroke-width="1.3"/>
                  <path d="M5.5 7V4.5C5.5 3.119 6.619 2 8 2C9.381 2 10.5 3.119 10.5 4.5V7" stroke="currentColor" stroke-width="1.3"/>
                </svg>
              }
            }
          </span>
          <span>{{ section.label }}</span>
        </button>
      }
    </div>

    <!-- Contenu Principal -->
    <div class="settings-content">

      <!-- 1. MON PROFIL & IDENTIFIANTS -->
      @if (sectionActive() === 'profil') {
        <div class="card settings-section animate-fade-in">
          <div class="card__header">
            <div>
              <h2 class="card__title">Mon Profil & Identifiants</h2>
              <p class="text-xs text-secondary">Modifiez vos informations personnelles et votre mot de passe</p>
            </div>
            <span class="badge badge-primary">Compte Connecté</span>
          </div>

          <div class="card__body">
            <form [formGroup]="formProfil" (ngSubmit)="sauvegarderProfil()" class="settings-form">
              
              <!-- Identité -->
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">Nom complet *</label>
                  <input type="text" class="form-input" formControlName="nomComplet" placeholder="Dr. Konaté Moussa"/>
                </div>

                <div class="form-group">
                  <label class="form-label">Adresse email de connexion *</label>
                  <input type="email" class="form-input" formControlName="email" placeholder="directeur@soundiatakeita.edu.ml"/>
                </div>
              </div>

              <!-- Séparateur Sécurité Mot de Passe -->
              <div style="border-top:1px solid var(--glass-border);padding-top:18px;margin-top:8px;">
                <h3 class="text-sm fw-semibold" style="margin-bottom:12px;color:var(--color-text-primary);">Changer mon mot de passe</h3>
                
                <div class="form-grid">
                  <div class="form-group">
                    <label class="form-label">Mot de passe actuel</label>
                    <input type="password" class="form-input" formControlName="motDePasseActuel" placeholder="••••••••"/>
                  </div>

                  <div class="form-group">
                    <label class="form-label">Nouveau mot de passe</label>
                    <input type="password" class="form-input" formControlName="nouveauMotDePasse" placeholder="Min. 8 caractères"/>
                  </div>
                </div>
              </div>

              <div style="display:flex;justify-content:flex-end;margin-top:12px;">
                <button type="submit" class="btn btn-primary" [disabled]="formProfil.invalid || chargementProfil()" id="btn-sauvegarder-profil">
                  @if (chargementProfil()) {
                    <span class="animate-spin">⟳</span> Enregistrement…
                  } @else {
                    Enregistrer les modifications
                  }
                </button>
              </div>

            </form>
          </div>
        </div>
      }

      <!-- 2. GESTION DES COMPTES & ANNUAIRE -->
      @if (sectionActive() === 'utilisateurs') {
        <div class="card settings-section animate-fade-in">
          <div class="card__header">
            <div>
              <h2 class="card__title">Annuaire des Comptes du Réseau</h2>
              <p class="text-xs text-secondary">Visualisez, activez et créez les accès pour votre équipe</p>
            </div>
            <span class="badge badge-innovation">{{ utilisateurs().length }} comptes actifs</span>
          </div>

          <div class="table-wrapper" style="border:none;border-radius:0;">
            <table class="table">
              <thead>
                <tr>
                  <th>Utilisateur</th>
                  <th>Email</th>
                  <th>Rôle attribué</th>
                  <th>Dernier accès</th>
                  <th>Statut</th>
                  <th style="text-align:right;">Actions</th>
                </tr>
              </thead>
              <tbody>
                @for (u of utilisateurs(); track u.id) {
                  <tr>
                    <td>
                      <div style="display:flex;align-items:center;gap:10px;">
                        <div class="avatar avatar-sm avatar-primary">
                          {{ u.nomComplet.charAt(0) || 'U' }}
                        </div>
                        <span class="fw-semibold text-sm">{{ u.nomComplet }}</span>
                      </div>
                    </td>
                    <td class="text-sm text-secondary">{{ u.email }}</td>
                    <td>
                      <span class="badge" [class.badge-primary]="u.role === RoleUtilisateur.ADMIN_ECOLE" [class.badge-secondaire]="u.role === RoleUtilisateur.PARENT" [class.badge-innovation]="u.role === RoleUtilisateur.ENSEIGNANT">
                        {{ getRoleLabel(u.role) }}
                      </span>
                    </td>
                    <td class="text-xs text-secondary">
                      {{ (u.dernierAcces | date:'dd/MM/yyyy HH:mm') || 'Jamais' }}
                    </td>
                    <td>
                      <span class="badge" [class.badge-success]="u.actif" [class.badge-warning]="!u.actif">
                        <span class="dot"></span>
                        {{ u.actif ? 'Actif' : 'Suspendu' }}
                      </span>
                    </td>
                    <td style="text-align:right;">
                      <button
                        class="btn btn-ghost btn-sm"
                        (click)="basculerStatutUtilisateur(u)"
                        [id]="'btn-toggle-user-' + u.id"
                        [style.color]="u.actif ? 'var(--color-danger)' : 'var(--color-success)'"
                      >
                        {{ u.actif ? 'Désactiver' : 'Activer' }}
                      </button>
                    </td>
                  </tr>
                } @empty {
                  <tr>
                    <td colspan="6" style="text-align:center;padding:32px;color:var(--color-text-tertiary);">
                      Aucun utilisateur trouvé.
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </div>
      }

      <!-- 3. INFORMATIONS ETABLISSEMENT -->
      @if (sectionActive() === 'etablissement') {
        <div class="card settings-section animate-fade-in">
          <div class="card__header">
            <div>
              <h2 class="card__title">Informations de l'Établissement</h2>
              <p class="text-xs text-secondary">Coordonnées officielles et fiche technique</p>
            </div>
            <span class="badge badge-primary">ID: ETAB-LBAD-01</span>
          </div>

          <div class="card__body">
            <form [formGroup]="formEtablissement" (ngSubmit)="sauvegarderEtablissement()" class="settings-form">
              <div class="form-group">
                <label class="form-label">Nom officiel de l'école / lycée *</label>
                <input type="text" class="form-input" formControlName="nom" placeholder="Lycée Soundiata Keïta"/>
              </div>

              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">Ville *</label>
                  <input type="text" class="form-input" formControlName="ville" placeholder="Bamako"/>
                </div>
                <div class="form-group">
                  <label class="form-label">Pays</label>
                  <input type="text" class="form-input" formControlName="pays" placeholder="Mali"/>
                </div>
              </div>

              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">Email officiel de contact</label>
                  <input type="email" class="form-input" formControlName="email" placeholder="contact@soundiatakeita.edu.ml"/>
                </div>
                <div class="form-group">
                  <label class="form-label">Téléphone</label>
                  <input type="tel" class="form-input" formControlName="telephone" placeholder="+223 20 22 11 00"/>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">Adresse postale</label>
                <textarea class="form-input" formControlName="adresse" rows="2" placeholder="Hamdallaye ACI 2000, Bamako"></textarea>
              </div>

              <div style="display:flex;justify-content:flex-end;">
                <button type="submit" class="btn btn-primary" id="btn-sauvegarder-etab">Sauvegarder l'établissement</button>
              </div>
            </form>
          </div>
        </div>
      }

      <!-- 4. SECURITE -->
      @if (sectionActive() === 'securite') {
        <div class="card settings-section animate-fade-in">
          <div class="card__header">
            <div>
              <h2 class="card__title">Sécurité & Politiques d'Accès</h2>
              <p class="text-xs text-secondary">Règles de session et contrôle d'accès</p>
            </div>
            <span class="badge badge-success">Verrouillé</span>
          </div>

          <div class="card__body" style="display:flex;flex-direction:column;gap:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;background:var(--glass-bg-subtle);border-radius:var(--radius-md);border:1px solid var(--glass-border);">
              <div>
                <div class="fw-semibold text-sm">Expiration automatique des sessions</div>
                <p class="text-xs text-secondary">Déconnecte les sessions inactives après 7 jours</p>
              </div>
              <span class="badge badge-success">Actif (7 jours)</span>
            </div>

            <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;background:var(--glass-bg-subtle);border-radius:var(--radius-md);border:1px solid var(--glass-border);">
              <div>
                <div class="fw-semibold text-sm">Création de compte restreinte</div>
                <p class="text-xs text-secondary">Seuls les administrateurs connectés peuvent créer de nouveaux comptes</p>
              </div>
              <span class="badge badge-primary">Politique Stricte</span>
            </div>
          </div>
        </div>
      }

    </div>
  </div>
</div>

<!-- Modale de Création d'un Nouveau Compte Utilisateur -->
@if (modalCreerUtilisateurOuverte()) {
  <div class="modal-overlay" (click)="fermerModalCreerUtilisateur()">
    <div class="modal-card animate-scale-in" (click)="$event.stopPropagation()" style="max-width: 500px;">
      <div class="modal-header">
        <h3 class="fw-bold text-lg">Créer un nouveau compte</h3>
        <button class="btn btn-ghost btn-sm btn-icon" (click)="fermerModalCreerUtilisateur()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
      </div>

      <div class="modal-body" style="display:flex;flex-direction:column;gap:14px;padding:20px 0;">
        <div class="form-group">
          <label class="form-label">Nom et prénom *</label>
          <input type="text" class="form-input" [(ngModel)]="nouvelUtilisateurForm.nomComplet" placeholder="Ex: Prof. Amadou Traoré"/>
        </div>

        <div class="form-group">
          <label class="form-label">Adresse email *</label>
          <input type="email" class="form-input" [(ngModel)]="nouvelUtilisateurForm.email" placeholder="amadou.traore@soundiatakeita.edu.ml"/>
        </div>

        <div class="form-group">
          <label class="form-label">Rôle attribué *</label>
          <select class="form-input" [(ngModel)]="nouvelUtilisateurForm.role">
            <option value="enseignant">Enseignant / Tuteur Pédagogique</option>
            <option value="admin_ecole">Administrateur Établissement</option>
            <option value="parent">Parent d'élève</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Mot de passe temporaire initial</label>
          <input type="text" class="form-input text-mono" [(ngModel)]="nouvelUtilisateurForm.motDePasse" placeholder="alternia2026"/>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-ghost" (click)="fermerModalCreerUtilisateur()">Annuler</button>
        <button
          class="btn btn-primary"
          (click)="validerCreationUtilisateur()"
          [disabled]="!nouvelUtilisateurForm.nomComplet.trim() || !nouvelUtilisateurForm.email.trim() || chargementCreation()"
          id="btn-valider-creation-user"
        >
          @if (chargementCreation()) {
            <span class="animate-spin">⟳</span> Création…
          } @else {
            Créer le compte
          }
        </button>
      </div>
    </div>
  </div>
}
  `,
  styles: [`
    .settings-layout {
      display: grid;
      grid-template-columns: 240px 1fr;
      gap: 20px;
      align-items: start;

      @media (max-width: 860px) {
        grid-template-columns: 1fr;
      }
    }

    .settings-nav {
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding: 10px;
    }

    .settings-nav-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 14px;
      border-radius: var(--radius-md);
      font-size: var(--text-sm);
      font-weight: var(--fw-medium);
      color: var(--color-text-secondary);
      text-align: left;
      transition: all var(--transition-fast);

      &:hover {
        background: var(--glass-bg-subtle);
        color: var(--color-text-primary);
      }

      &--active {
        background: var(--glass-bg-subtle) !important;
        color: var(--color-primaire) !important;
        font-weight: var(--fw-semibold);
      }
    }

    .settings-nav-icon {
      display: flex;
      align-items: center;
      color: currentColor;
    }

    .settings-form {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
  `]
})
export class ParametresEtablissementComposant implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly notif = inject(NotificationService);
  private readonly authService = inject(AuthService);

  readonly RoleUtilisateur = RoleUtilisateur;

  readonly sections = [
    { id: 'profil' as SectionParametre, label: 'Mon Profil & Identifiants' },
    { id: 'utilisateurs' as SectionParametre, label: 'Gestion des Comptes' },
    { id: 'etablissement' as SectionParametre, label: 'Fiche Établissement' },
    { id: 'securite' as SectionParametre, label: 'Sécurité & Politiques' },
  ];

  sectionActive = signal<SectionParametre>('profil');
  utilisateurs = signal<Utilisateur[]>([]);
  chargementProfil = signal(false);
  chargementCreation = signal(false);
  modalCreerUtilisateurOuverte = signal(false);

  nouvelUtilisateurForm = {
    nomComplet: '',
    email: '',
    role: 'enseignant',
    motDePasse: 'alternia2026',
  };

  formProfil = this.fb.group({
    nomComplet: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.required, Validators.email]],
    motDePasseActuel: [''],
    nouveauMotDePasse: ['', [Validators.minLength(6)]],
  });

  formEtablissement = this.fb.group({
    nom: ['Lycée Soundiata Keïta', [Validators.required]],
    ville: ['Bamako', [Validators.required]],
    pays: ['Mali'],
    email: ['direction@soundiatakeita.edu.ml'],
    telephone: ['+223 20 22 11 00'],
    adresse: ['Hamdallaye ACI 2000, Bamako'],
  });

  ngOnInit(): void {
    const user = this.authService.utilisateurCourant();
    if (user) {
      this.formProfil.patchValue({
        nomComplet: user.nomComplet,
        email: user.email,
      });
    }
    this.chargerUtilisateurs();
  }

  async chargerUtilisateurs(): Promise<void> {
    try {
      const list = await this.authService.listerUtilisateurs();
      this.utilisateurs.set(list);
    } catch {
      // Ignorer ou charger liste par défaut
    }
  }

  getRoleLabel(role: any): string {
    if (role === RoleUtilisateur.ADMIN_ECOLE || role === 'admin_ecole') return 'Admin École';
    if (role === RoleUtilisateur.PARENT || role === 'parent') return 'Parent';
    return 'Enseignant IA';
  }

  async sauvegarderProfil(): Promise<void> {
    if (this.formProfil.invalid) return;

    this.chargementProfil.set(true);
    try {
      const val = this.formProfil.value;
      await this.authService.modifierMonProfil(
        val.nomComplet!,
        val.email!,
        val.motDePasseActuel || undefined,
        val.nouveauMotDePasse || undefined
      );
      this.notif.succes('Profil actualisé', 'Vos identifiants ont été mis à jour avec succès.');
      this.formProfil.patchValue({ motDePasseActuel: '', nouveauMotDePasse: '' });
    } catch (e: any) {
      this.notif.erreur('Erreur', e.message || 'Impossible de mettre à jour le profil');
    } finally {
      this.chargementProfil.set(false);
    }
  }

  sauvegarderEtablissement(): void {
    this.notif.succes('Établissement', 'Les informations de l\'établissement ont été enregistrées.');
  }

  ouvrirModalCreerUtilisateur(): void {
    this.nouvelUtilisateurForm = {
      nomComplet: '',
      email: '',
      role: 'enseignant',
      motDePasse: 'alternia2026',
    };
    this.modalCreerUtilisateurOuverte.set(true);
  }

  fermerModalCreerUtilisateur(): void {
    this.modalCreerUtilisateurOuverte.set(false);
  }

  async validerCreationUtilisateur(): Promise<void> {
    this.chargementCreation.set(true);
    try {
      await this.authService.creerUtilisateur(
        this.nouvelUtilisateurForm.nomComplet,
        this.nouvelUtilisateurForm.email,
        this.nouvelUtilisateurForm.role,
        this.nouvelUtilisateurForm.motDePasse
      );
      this.notif.succes('Compte créé', `Le compte de ${this.nouvelUtilisateurForm.nomComplet} a été initialisé.`);
      this.fermerModalCreerUtilisateur();
      await this.chargerUtilisateurs();
    } catch (e: any) {
      this.notif.erreur('Erreur de création', e.message || 'Impossible de créer le compte');
    } finally {
      this.chargementCreation.set(false);
    }
  }

  async basculerStatutUtilisateur(u: Utilisateur): Promise<void> {
    try {
      await this.authService.toggleStatutUtilisateur(u.id);
      this.notif.info('Statut modifié', `Le compte de ${u.nomComplet} a été mis à jour.`);
      await this.chargerUtilisateurs();
    } catch {
      this.notif.erreur('Erreur', 'Impossible de modifier le statut');
    }
  }
}
