import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators, FormsModule } from '@angular/forms';
import { NotificationService } from '../../../core/services/notification.service';
import { AuthService } from '../../../core/services/auth.service';

interface BoitierAssocieMock {
  id: string;
  nomBoitier: string;
  codeBoitier: string;
  emplacement: string;
  statut: string;
}

@Component({
  selector: 'app-parametres-parent',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  template: `
<div class="page-content stagger-children">
  <div class="page-header">
    <h1 class="page-header__title">Paramètres du compte Parent</h1>
    <p class="page-header__subtitle">Gérez votre profil personnel, vos boîtiers et vos préférences</p>
  </div>

  <div class="settings-layout">
    <!-- Menu latéral des paramètres -->
    <div class="settings-nav card">
      <button class="settings-nav-item" [class.settings-nav-item--active]="sectionActive() === 'profil'" (click)="sectionActive.set('profil')" id="btn-tab-profil">
        Mon Profil & Sécurité
      </button>
      <button class="settings-nav-item" [class.settings-nav-item--active]="sectionActive() === 'boitier'" (click)="sectionActive.set('boitier')" id="btn-tab-boitier">
        Mes Boîtiers Associés
      </button>
      <button class="settings-nav-item" [class.settings-nav-item--active]="sectionActive() === 'notifications'" (click)="sectionActive.set('notifications')" id="btn-tab-notifications">
        Notifications & Alertes
      </button>
    </div>

    <!-- Contenu des paramètres -->
    <div class="settings-content">

      <!-- Section Profil & Sécurité -->
      @if (sectionActive() === 'profil') {
        <div class="card settings-section animate-fade-in">
          <div class="card__header">
            <div>
              <h2 class="card__title">Informations Personnelles</h2>
              <p class="text-xs text-secondary">Identifiants de votre compte parent</p>
            </div>
            <span class="badge badge-secondaire">Espace Famille</span>
          </div>

          <div class="card__body">
            <form class="settings-form" [formGroup]="formProfil" (ngSubmit)="sauvegarderProfil()">
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">Nom complet *</label>
                  <input type="text" class="form-input" formControlName="nomComplet" placeholder="Aïssata Coulibaly"/>
                </div>
                <div class="form-group">
                  <label class="form-label">Email de connexion *</label>
                  <input type="email" class="form-input" formControlName="email" placeholder="aissata.coulibaly@gmail.com"/>
                </div>
              </div>

              <!-- Mot de passe -->
              <div style="border-top:1px solid var(--glass-border);padding-top:18px;margin-top:8px;">
                <h3 class="text-sm fw-semibold" style="margin-bottom:12px;color:var(--color-text-primary);">Modifier mon mot de passe</h3>
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

              <div style="display:flex;justify-content:flex-end;margin-top:8px;">
                <button type="submit" class="btn btn-secondary" [disabled]="formProfil.invalid || chargement()" id="btn-sauvegarder-profil-parent">
                  @if (chargement()) {
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

      <!-- Section Boîtiers Associés -->
      @if (sectionActive() === 'boitier') {
        <div class="card settings-section animate-fade-in">
          <div class="card__header">
            <div>
              <h2 class="card__title">Boîtiers AlternIA Associés</h2>
              <p class="text-xs text-secondary">Appareils physiques configurés pour vos enfants</p>
            </div>
            <button class="btn btn-outline btn-sm" (click)="ouvrirModalAssociation()" id="btn-associer-nouveau-boitier">+ Associer un boîtier</button>
          </div>

          <div class="card__body">
            <div style="display:flex;flex-direction:column;gap:12px;">
              @for (b of boitiers(); track b.id) {
                <div style="display:flex;align-items:center;justify-content:space-between;padding:14px;background:var(--glass-bg-subtle);border-radius:var(--radius-md);border:1px solid var(--glass-border);">
                  <div style="display:flex;align-items:center;gap:12px;">
                    <div class="icon-box icon-box-md icon-box-secondaire">
                      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                        <rect x="2" y="4" width="14" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
                        <circle cx="5.5" cy="9" r="1" fill="currentColor"/>
                        <circle cx="8.5" cy="9" r="1" fill="currentColor"/>
                        <path d="M12 9H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                      </svg>
                    </div>
                    <div>
                      <div class="fw-semibold text-sm">{{ b.nomBoitier }}</div>
                      <div class="text-xs text-secondary">Code : <span class="text-mono">{{ b.codeBoitier }}</span> · {{ b.emplacement }}</div>
                    </div>
                  </div>
                  <span class="badge badge-success">
                    <span class="dot"></span>
                    En ligne
                  </span>
                </div>
              }
            </div>
          </div>
        </div>
      }

      <!-- Section Notifications -->
      @if (sectionActive() === 'notifications') {
        <div class="card settings-section animate-fade-in">
          <div class="card__header">
            <div>
              <h2 class="card__title">Préférences d'Alertes</h2>
              <p class="text-xs text-secondary">Choisissez quand et comment recevoir les rapports d'étude</p>
            </div>
          </div>
          <div class="card__body" style="display:flex;flex-direction:column;gap:14px;">
            <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;background:var(--glass-bg-subtle);border-radius:var(--radius-md);border:1px solid var(--glass-border);">
              <div>
                <div class="fw-semibold text-sm">Bilan d'apprentissage hebdomadaire</div>
                <p class="text-xs text-secondary">Recevoir le récapitulatif des leçons et exercices le dimanche soir</p>
              </div>
              <span class="badge badge-success">Activé</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;background:var(--glass-bg-subtle);border-radius:var(--radius-md);border:1px solid var(--glass-border);">
              <div>
                <div class="fw-semibold text-sm">Alertes de baisse d'assiduité</div>
                <p class="text-xs text-secondary">Être notifié en cas d'inactivité de plus de 48h</p>
              </div>
              <span class="badge badge-success">Activé</span>
            </div>
          </div>
        </div>
      }

    </div>
  </div>
</div>
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
        color: var(--color-secondaire) !important;
        font-weight: var(--fw-semibold);
      }
    }

    .settings-form {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
  `]
})
export class ParametresParentComposant implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly notif = inject(NotificationService);
  private readonly authService = inject(AuthService);

  sectionActive = signal<'profil' | 'boitier' | 'notifications'>('profil');
  chargement = signal(false);

  boitiers = signal<BoitierAssocieMock[]>([
    { id: '1', nomBoitier: 'Boîtier Salon', codeBoitier: 'ALT-HOME-0042', emplacement: 'Maison', statut: 'Connecté' },
  ]);

  formProfil = this.fb.group({
    nomComplet: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.required, Validators.email]],
    motDePasseActuel: [''],
    nouveauMotDePasse: ['', [Validators.minLength(6)]],
  });

  ngOnInit(): void {
    const user = this.authService.utilisateurCourant();
    if (user) {
      this.formProfil.patchValue({
        nomComplet: user.nomComplet,
        email: user.email,
      });
    }
  }

  async sauvegarderProfil(): Promise<void> {
    if (this.formProfil.invalid) return;

    this.chargement.set(true);
    try {
      const val = this.formProfil.value;
      await this.authService.modifierMonProfil(
        val.nomComplet!,
        val.email!,
        val.motDePasseActuel || undefined,
        val.nouveauMotDePasse || undefined
      );
      this.notif.succes('Profil actualisé', 'Vos coordonnées parent ont été enregistrées.');
      this.formProfil.patchValue({ motDePasseActuel: '', nouveauMotDePasse: '' });
    } catch (e: any) {
      this.notif.erreur('Erreur', e.message || 'Impossible de mettre à jour le profil');
    } finally {
      this.chargement.set(false);
    }
  }

  ouvrirModalAssociation(): void {
    this.notif.info('Association de boîtier', 'Entrez le code d\'activation situé sous votre boîtier.');
  }
}
