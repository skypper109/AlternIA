import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ROUTES_APP } from '../../../core/constantes/routes.constantes';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-inscription-parent',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  template: `
<div class="auth-page">
  <!-- Left: Branding (Identique Connexion) -->
  <div class="auth-branding">
    <div class="auth-branding__inner">
      <!-- Logo -->
      <div class="auth-logo">
        <div class="auth-logo__icon">
          <img src="logo-icon.jpeg" alt="AlternIA" width="44" height="44" style="border-radius:10px;object-fit:cover;display:block;box-shadow:0 4px 16px rgba(0,0,0,0.3);">
        </div>
        <span class="auth-logo__name">Altern<span style="color:#40BBCC;">iA</span></span>
      </div>

      <!-- Hero Content -->
      <div class="auth-hero">
        <h1 class="auth-hero__title">Accompagnez vos enfants <em>au quotidien</em></h1>
        <p class="auth-hero__desc">
          Suivez la progression pédagogique, configurez le boîtier familial et recevez des alertes personnalisées.
        </p>

        <!-- Feature Pills -->
        <div class="auth-features">
          <div class="auth-feature-pill">
            <span class="pill-icon">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M2 12L5 8L7.5 10.5L10.5 5.5L13 8L15 6" stroke="#F1851F" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
            <span>Suivi temps réel</span>
          </div>

          <div class="auth-feature-pill">
            <span class="pill-icon">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <rect x="2" y="4" width="12" height="8" rx="1.5" stroke="#F1851F" stroke-width="1.3"/>
                <circle cx="5" cy="8" r="0.75" fill="#F1851F"/>
                <circle cx="8" cy="8" r="0.75" fill="#F1851F"/>
              </svg>
            </span>
            <span>Gestion du boîtier</span>
          </div>

          <div class="auth-feature-pill">
            <span class="pill-icon">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M8 2C5.239 2 3 4.239 3 7V12H13V7C13 4.239 10.761 2 8 2Z" stroke="#F1851F" stroke-width="1.3"/>
              </svg>
            </span>
            <span>Alertes & Notifs</span>
          </div>

          <div class="auth-feature-pill">
            <span class="pill-icon">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <circle cx="8" cy="8" r="6" stroke="#F1851F" stroke-width="1.3"/>
                <path d="M8 4V8L10.5 10.5" stroke="#F1851F" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
            </span>
            <span>Historique d'étude</span>
          </div>
        </div>
      </div>

      <!-- Stats Footer -->
      <div class="auth-stats">
        <div class="auth-stat">
          <div class="auth-stat__value">12k+</div>
          <div class="auth-stat__label">Familles Actives</div>
        </div>
        <div class="auth-stat">
          <div class="auth-stat__value">4.9/5</div>
          <div class="auth-stat__label">Satisfaction</div>
        </div>
        <div class="auth-stat">
          <div class="auth-stat__value">100%</div>
          <div class="auth-stat__label">Autonomie</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Right: Form Panel -->
  <div class="auth-form-panel">
    <div class="auth-form-container" style="max-width: 460px;">
      @if (!succes()) {
        <div class="auth-step animate-fade-in">
          
          <div class="auth-form-header">
            <div style="display: flex; justify-content: center; margin-bottom: 12px;">
              <span class="profile-badge profile-badge--parent">
                <svg width="13" height="13" viewBox="0 0 16 16" fill="none" style="margin-right: 4px;">
                  <circle cx="8" cy="5.5" r="3" stroke="currentColor" stroke-width="1.3"/>
                  <path d="M2.5 14C2.5 11 5 9 8 9C11 9 13.5 11 13.5 14" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                </svg>
                Espace Famille
              </span>
            </div>
            <h2 class="auth-form-title">Créer votre compte parent</h2>
            <p class="auth-form-subtitle">Associez votre boîtier Alternia pour commencer le suivi</p>
          </div>

          @if (messageErreur()) {
            <div class="auth-error-alert animate-fade-in">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style="flex-shrink:0;">
                <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.3"/>
                <path d="M8 5V8.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                <circle cx="8" cy="11" r="0.75" fill="currentColor"/>
              </svg>
              <span>{{ messageErreur() }}</span>
            </div>
          }

          <form [formGroup]="formulaire" (ngSubmit)="sInscrire()" class="auth-form-body">
            <!-- Nom et Prénom -->
            <div class="form-grid">
              <div class="form-group">
                <label class="form-label" for="nom-parent">Nom *</label>
                <div class="form-input-wrapper">
                  <span class="form-input-icon">
                    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
                      <circle cx="8" cy="5.5" r="3" stroke="currentColor" stroke-width="1.3"/>
                      <path d="M2.5 14C2.5 11 5 9 8 9C11 9 13.5 11 13.5 14" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                    </svg>
                  </span>
                  <input
                    id="nom-parent"
                    type="text"
                    class="form-input"
                    formControlName="nom"
                    placeholder="Coulibaly"
                  />
                </div>
              </div>

              <div class="form-group">
                <label class="form-label" for="prenom-parent">Prénom *</label>
                <div class="form-input-wrapper">
                  <span class="form-input-icon">
                    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
                      <circle cx="8" cy="5.5" r="3" stroke="currentColor" stroke-width="1.3"/>
                      <path d="M2.5 14C2.5 11 5 9 8 9C11 9 13.5 11 13.5 14" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                    </svg>
                  </span>
                  <input
                    id="prenom-parent"
                    type="text"
                    class="form-input"
                    formControlName="prenom"
                    placeholder="Aïssata"
                  />
                </div>
              </div>
            </div>

            <!-- Email -->
            <div class="form-group">
              <label class="form-label" for="email-parent">Adresse email personnelle *</label>
              <div class="form-input-wrapper">
                <span class="form-input-icon">
                  <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
                    <rect x="2" y="3" width="12" height="10" rx="2" stroke="currentColor" stroke-width="1.3" />
                    <path d="M2 5.5L8 9.5L14 5.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" />
                  </svg>
                </span>
                <input
                  id="email-parent"
                  type="email"
                  class="form-input"
                  formControlName="email"
                  placeholder="aissata.coulibaly@gmail.com"
                />
              </div>
            </div>

            <!-- Code Boîtier -->
            <div class="form-group">
              <label class="form-label" for="code-boitier">Code unique du boîtier *</label>
              <div class="form-input-wrapper">
                <span class="form-input-icon">
                  <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
                    <rect x="2" y="4" width="12" height="8" rx="1.5" stroke="currentColor" stroke-width="1.3"/>
                    <circle cx="5" cy="8" r="0.75" fill="currentColor"/>
                    <circle cx="8" cy="8" r="0.75" fill="currentColor"/>
                  </svg>
                </span>
                <input
                  id="code-boitier"
                  type="text"
                  class="form-input text-mono"
                  formControlName="codeBoitier"
                  placeholder="ALT-HOME-0042"
                />
              </div>
              <span class="text-xs text-tertiary" style="margin-top: 3px;">Le code se trouve sur l'étiquette sous votre boîtier Alternia</span>
            </div>

            <!-- Mot de passe & Confirmation -->
            <div class="form-grid">
              <div class="form-group">
                <label class="form-label" for="mdp-parent">Mot de passe *</label>
                <div class="form-input-wrapper">
                  <span class="form-input-icon">
                    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
                      <rect x="3" y="7" width="10" height="7" rx="2" stroke="currentColor" stroke-width="1.3" />
                      <path d="M5.5 7V4.5C5.5 3.119 6.619 2 8 2C9.381 2 10.5 3.119 10.5 4.5V7" stroke="currentColor" stroke-width="1.3" />
                    </svg>
                  </span>
                  <input
                    id="mdp-parent"
                    [type]="afficherMdp() ? 'text' : 'password'"
                    class="form-input"
                    formControlName="motDePasse"
                    placeholder="Min. 8 caractères"
                  />
                  <button
                    type="button"
                    class="form-input-toggle"
                    (click)="toggleAfficherMdp()"
                    tabindex="-1"
                  >
                    @if (afficherMdp()) {
                      <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
                        <path d="M2 2L14 14M6.5 6.5C6.187 6.813 6 7.24 6 7.7C6 8.97 7.03 10 8.3 10C8.76 10 9.187 9.813 9.5 9.5M3 8C4.2 5.5 6 4 8 4C9.1 4 10.1 4.5 11 5.3M13 8C12.3 9.4 11 10.8 9.5 11.4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    } @else {
                      <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
                        <path d="M1.5 8C2.7 4.8 5.1 3 8 3C10.9 3 13.3 4.8 14.5 8C13.3 11.2 10.9 13 8 13C5.1 13 2.7 11.2 1.5 8Z" stroke="currentColor" stroke-width="1.3"/>
                        <circle cx="8" cy="8" r="2" stroke="currentColor" stroke-width="1.3"/>
                      </svg>
                    }
                  </button>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label" for="conf-mdp-parent">Confirmation *</label>
                <div class="form-input-wrapper">
                  <span class="form-input-icon">
                    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
                      <rect x="3" y="7" width="10" height="7" rx="2" stroke="currentColor" stroke-width="1.3" />
                      <path d="M5.5 7V4.5C5.5 3.119 6.619 2 8 2C9.381 2 10.5 3.119 10.5 4.5V7" stroke="currentColor" stroke-width="1.3" />
                    </svg>
                  </span>
                  <input
                    id="conf-mdp-parent"
                    [type]="afficherConfMdp() ? 'text' : 'password'"
                    class="form-input"
                    formControlName="confirmationMotDePasse"
                    placeholder="Retapez le mot de passe"
                  />
                  <button
                    type="button"
                    class="form-input-toggle"
                    (click)="toggleAfficherConfMdp()"
                    tabindex="-1"
                  >
                    @if (afficherConfMdp()) {
                      <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
                        <path d="M2 2L14 14M6.5 6.5C6.187 6.813 6 7.24 6 7.7C6 8.97 7.03 10 8.3 10C8.76 10 9.187 9.813 9.5 9.5M3 8C4.2 5.5 6 4 8 4C9.1 4 10.1 4.5 11 5.3M13 8C12.3 9.4 11 10.8 9.5 11.4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    } @else {
                      <svg width="15" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M1.5 8C2.7 4.8 5.1 3 8 3C10.9 3 13.3 4.8 14.5 8C13.3 11.2 10.9 13 8 13C5.1 13 2.7 11.2 1.5 8Z" stroke="currentColor" stroke-width="1.3"/>
                        <circle cx="8" cy="8" r="2" stroke="currentColor" stroke-width="1.3"/>
                      </svg>
                    }
                  </button>
                </div>
              </div>
            </div>

            <!-- Submit Button -->
            <button
              id="btn-creer-compte-parent"
              type="submit"
              class="btn btn-secondary btn-lg btn-full"
              [disabled]="chargement()"
              style="margin-top: 6px;"
            >
              @if (chargement()) {
                <span class="animate-spin">⟳</span> Inscription en cours…
              } @else {
                Créer mon compte parent
              }
            </button>
          </form>

          <div style="text-align:center; margin-top: 18px;">
            <p class="text-secondary text-sm">
              Vous avez déjà un compte ?
              <a [routerLink]="routes.AUTH.CONNEXION" class="fw-semibold text-link" style="margin-left: 4px;">
                Se connecter
              </a>
            </p>
          </div>

        </div>
      } @else {
        <div class="auth-step auth-success animate-scale-in" style="text-align:center; padding: 32px 16px;">
          <div class="icon-box icon-box-lg icon-box-success" style="margin: 0 auto 18px auto; width: 56px; height: 56px;">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="16 9 10 15 7 12"/>
            </svg>
          </div>
          <h2 class="auth-form-title">Compte parent créé avec succès !</h2>
          <p class="auth-form-subtitle" style="margin-bottom: 24px; line-height: 1.6;">
            Votre boîtier Alternia est associé à votre compte. Vous pouvez maintenant suivre les activités d'apprentissage.
          </p>
          <a [routerLink]="routes.AUTH.CONNEXION" class="btn btn-secondary btn-lg btn-full" id="link-retour-connexion-parent">
            Accéder à la connexion →
          </a>
        </div>
      }
    </div>
  </div>
</div>
  `,
  styleUrl: '../inscription-etablissement/inscription-etablissement.composant.scss',
})
export class InscriptionParentComposant {
  private readonly fb = inject(FormBuilder);
  private readonly notifService = inject(NotificationService);
  readonly routes = ROUTES_APP;

  chargement = signal(false);
  succes = signal(false);
  messageErreur = signal<string | null>(null);
  afficherMdp = signal(false);
  afficherConfMdp = signal(false);

  formulaire = this.fb.group({
    nom: ['', [Validators.required]],
    prenom: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    codeBoitier: ['', [Validators.required, Validators.pattern(/^ALT-[A-Z]+-\d{4}$/)]],
    motDePasse: ['', [Validators.required, Validators.minLength(8)]],
    confirmationMotDePasse: ['', [Validators.required]],
  }, { validators: this.passwordsMatch });

  private passwordsMatch(group: any) {
    const mdp = group.get('motDePasse')?.value;
    const conf = group.get('confirmationMotDePasse')?.value;
    return mdp === conf ? null : { passwordMismatch: true };
  }

  toggleAfficherMdp(): void {
    this.afficherMdp.update(v => !v);
  }

  toggleAfficherConfMdp(): void {
    this.afficherConfMdp.update(v => !v);
  }

  async sInscrire(): Promise<void> {
    this.messageErreur.set(null);

    if (this.formulaire.invalid) {
      this.formulaire.markAllAsTouched();
      if (this.formulaire.hasError('passwordMismatch')) {
        this.messageErreur.set('Les mots de passe ne correspondent pas.');
      } else if (this.formulaire.get('codeBoitier')?.invalid) {
        this.messageErreur.set('Le format du code boîtier est invalide (Ex: ALT-HOME-0042).');
      } else {
        this.messageErreur.set('Veuillez remplir correctement tous les champs obligatoires.');
      }
      return;
    }

    this.chargement.set(true);
    await new Promise(r => setTimeout(r, 1200));
    this.chargement.set(false);
    this.succes.set(true);
    this.notifService.succes('Compte créé', 'Votre compte parent a été créé avec succès.');
  }
}
