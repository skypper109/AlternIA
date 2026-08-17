import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators, FormsModule } from '@angular/forms';
import { NotificationService } from '../../../core/services/notification.service';

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
    <p class="page-header__subtitle">Gérez votre profil, vos boîtiers et vos préférences de notification</p>
  </div>

  <div class="settings-layout">
    <!-- Menu latéral des paramètres -->
    <div class="settings-nav">
      <button class="settings-nav-item" [class.active]="sectionActive() === 'profil'" (click)="sectionActive.set('profil')" id="btn-tab-profil">
        Mon profil
      </button>
      <button class="settings-nav-item" [class.active]="sectionActive() === 'boitier'" (click)="sectionActive.set('boitier')" id="btn-tab-boitier">
        Mes boîtiers associés
      </button>
      <button class="settings-nav-item" [class.active]="sectionActive() === 'notifications'" (click)="sectionActive.set('notifications')" id="btn-tab-notifications">
        Notifications
      </button>
      <button class="settings-nav-item" [class.active]="sectionActive() === 'securite'" (click)="sectionActive.set('securite')" id="btn-tab-securite">
        Sécurité & Mot de passe
      </button>
    </div>

    <!-- Contenu des paramètres -->
    <div class="settings-content">

      <!-- Section Profil -->
      @if (sectionActive() === 'profil') {
        <div class="settings-section animate-fade-in">
          <h2 class="settings-section__title">Informations du compte</h2>
          <form class="settings-form" [formGroup]="formProfil" (ngSubmit)="sauvegarderProfil()">
            <div class="form-grid">
              <div class="form-group">
                <label class="form-label">Prénom</label>
                <input type="text" class="form-input" formControlName="prenom"/>
              </div>
              <div class="form-group">
                <label class="form-label">Nom</label>
                <input type="text" class="form-input" formControlName="nom"/>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Email</label>
              <input type="email" class="form-input" formControlName="email"/>
            </div>
            <div class="form-group">
              <label class="form-label">Téléphone (Mali)</label>
              <input type="tel" class="form-input" formControlName="telephone" placeholder="+223 76 00 11 22"/>
            </div>
            <button type="submit" class="btn btn-secondary" id="btn-sauvegarder-profil-parent">Sauvegarder</button>
          </form>
        </div>
      }

      <!-- Section Boîtiers Associés -->
      @if (sectionActive() === 'boitier') {
        <div class="settings-section animate-fade-in">
          <h2 class="settings-section__title">Mes boîtiers associés</h2>
          <div class="boitier-cards">
            @for (b of boitiers(); track b.id) {
              <div class="boitier-manage-card">
                <div style="display:flex;align-items:center;gap:12px;">
                  <div class="icon-box icon-box-md icon-box-primary">
                    <svg width="16" height="16" viewBox="0 0 18 18" fill="none">
                      <path d="M2 5L9 1.5L16 5V13L9 16.5L2 13V5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
                      <path d="M2 5L9 8.5L16 5" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
                      <path d="M9 8.5V16.5" stroke="currentColor" stroke-width="1.5"/>
                    </svg>
                  </div>
                  <div>
                    <div class="fw-semibold">{{ b.nomBoitier }}</div>
                    <div class="text-sm text-secondary">Code : <span class="text-mono">{{ b.codeBoitier }}</span> · {{ b.emplacement }}</div>
                  </div>
                </div>
                <div style="display:flex;gap:8px;">
                  <span class="badge badge-success">Connecté</span>
                </div>
              </div>
            }
          </div>
          <button class="btn btn-outline btn-sm" style="margin-top:16px;" (click)="ouvrirModalAssociation()" id="btn-associer-nouveau-boitier">+ Associer un autre boîtier</button>
        </div>
      }

      <!-- Section Notifications -->
      @if (sectionActive() === 'notifications') {
        <div class="settings-section animate-fade-in">
          <h2 class="settings-section__title">Notifications</h2>
          <div class="preferences-list">
            @for (notif of notificationPrefs(); track notif.id) {
              <div class="pref-item">
                <div>
                  <div class="fw-semibold text-sm">{{ notif.label }}</div>
                  <div class="text-xs text-secondary">{{ notif.desc }}</div>
                </div>
                <label class="toggle-switch">
                  <input type="checkbox" [checked]="notif.active" (change)="basculerNotifPref(notif.id)" [id]="'toggle-notif-' + notif.id"/>
                  <span class="toggle-slider"></span>
                </label>
              </div>
            }
          </div>
        </div>
      }

      <!-- Section Sécurité -->
      @if (sectionActive() === 'securite') {
        <div class="settings-section animate-fade-in">
          <h2 class="settings-section__title">Sécurité</h2>
          <form class="settings-form" [formGroup]="formMotDePasse" (ngSubmit)="changerMotDePasse()">
            <div class="form-group">
              <label class="form-label">Mot de passe actuel</label>
              <input type="password" class="form-input" formControlName="actuel" placeholder="••••••••"/>
            </div>
            <div class="form-group">
              <label class="form-label">Nouveau mot de passe</label>
              <input type="password" class="form-input" formControlName="nouveau" placeholder="Min. 8 caractères"/>
            </div>
            <div class="form-group">
              <label class="form-label">Confirmation</label>
              <input type="password" class="form-input" formControlName="confirmation" placeholder="Retapez le nouveau mot de passe"/>
            </div>
            <button type="submit" class="btn btn-primary" id="btn-changer-mdp-parent">Changer le mot de passe</button>
          </form>
        </div>
      }
    </div>
  </div>

  <!-- Modal Association Boîtier -->
  @if (modalAssociationOuverte()) {
    <div class="modal-overlay" (click)="fermerModalAssociation()">
      <div class="modal-card animate-scale-in" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <h3 class="fw-bold text-lg">Associer un boîtier Alternia</h3>
          <button class="btn btn-ghost btn-sm btn-icon" (click)="fermerModalAssociation()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        </div>
        <div class="modal-body" style="display:flex;flex-direction:column;gap:14px;padding:20px 0;">
          <div class="form-group">
            <label class="form-label">Code unique du boîtier</label>
            <input type="text" class="form-input text-mono" [(ngModel)]="codeBoitierAssocier" placeholder="ALT-HOME-0043"/>
          </div>
          <div class="form-group">
            <label class="form-label">Nom personnalisé</label>
            <input type="text" class="form-input" [(ngModel)]="nomBoitierAssocier" placeholder="Boîtier Salon Bamako"/>
          </div>
        </div>
        <div class="modal-footer" style="display:flex;justify-content:flex-end;gap:10px;">
          <button class="btn btn-ghost" (click)="fermerModalAssociation()">Annuler</button>
          <button class="btn btn-primary" (click)="validerAssociationBoitier()">Associer</button>
        </div>
      </div>
    </div>
  }
</div>
  `,
  styles: [`
    .settings-layout { display: grid; grid-template-columns: 240px 1fr; gap: 24px; @media(max-width:768px){ grid-template-columns: 1fr; } }
    .settings-nav { display: flex; flex-direction: column; gap: 4px; background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 10px; height: fit-content; }
    .settings-nav-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: var(--radius-md); border: none; background: transparent; color: var(--color-text-secondary); font-size: var(--text-sm); font-weight: var(--fw-medium); cursor: pointer; text-align: left; transition: all var(--transition-fast); }
    .settings-nav-item:hover { background: var(--color-bg-surface-2); color: var(--color-text-primary); }
    .settings-nav-item.active { background: var(--color-secondaire-light); color: var(--color-secondaire); font-weight: var(--fw-semibold); }
    .settings-section { background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 24px; box-shadow: var(--shadow-xs); }
    .settings-section__title { font-family: var(--font-display); font-size: var(--text-lg); font-weight: var(--fw-bold); color: var(--color-text-primary); margin-bottom: 20px; border-bottom: 1px solid var(--color-border); padding-bottom: 12px; }
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .settings-form { display: flex; flex-direction: column; gap: 16px; max-width: 540px; }
    .boitier-cards { display: flex; flex-direction: column; gap: 12px; }
    .boitier-manage-card { display: flex; align-items: center; justify-content: space-between; padding: 14px; background: var(--color-bg-surface-2); border-radius: var(--radius-md); border: 1px solid var(--color-border); }
    .preferences-list { display: flex; flex-direction: column; gap: 12px; }
    .pref-item { display: flex; align-items: center; justify-content: space-between; padding: 14px; background: var(--color-bg-surface-2); border-radius: var(--radius-md); border: 1px solid var(--color-border); }
  `],
})
export class ParametresParentComposant {
  private readonly fb = inject(FormBuilder);
  private readonly notifService = inject(NotificationService);

  sectionActive = signal<'profil' | 'boitier' | 'notifications' | 'securite'>('profil');

  formProfil = this.fb.group({
    prenom: ['Aïssata'],
    nom: ['Coulibaly'],
    email: ['parent@famille.ml'],
    telephone: ['+223 76 00 11 22'],
  });

  formMotDePasse = this.fb.group({
    actuel: ['', Validators.required],
    nouveau: ['', [Validators.required, Validators.minLength(8)]],
    confirmation: ['', Validators.required],
  });

  boitiers = signal<BoitierAssocieMock[]>([
    { id: 'b-1', nomBoitier: 'Boîtier Alternia Maison', codeBoitier: 'ALT-HOME-0042', emplacement: 'Salon Bamako', statut: 'Connecté' },
  ]);

  notificationPrefs = signal([
    { id: 'objectifs', label: 'Alertes d\'activité du boîtier', desc: 'Recevoir une alerte quand le boîtier atteint son volume d\'utilisation prévu', active: true },
    { id: 'rapports', label: 'Synthèse hebdomadaire par email', desc: 'Recevoir le récapitulatif des matières les plus consultées chaque semaine', active: true },
    { id: 'maj', label: 'Mises à jour système et firmware', desc: 'Alertes lors des mises à jour des contenus pédagogiques sur le boîtier', active: true },
  ]);

  modalAssociationOuverte = signal(false);
  codeBoitierAssocier = '';
  nomBoitierAssocier = '';

  modalSuppressionOuverte = signal(false);

  sauvegarderProfil(): void {
    this.notifService.succes('Profil mis à jour', 'Vos informations personnelles ont été enregistrées.');
  }

  basculerNotifPref(id: string): void {
    this.notificationPrefs.update(list => list.map(item => item.id === id ? { ...item, active: !item.active } : item));
    this.notifService.info('Préférences modifiées', 'Préférence de notification mise à jour.');
  }

  changerMotDePasse(): void {
    if (this.formMotDePasse.invalid) {
      this.notifService.erreur('Formulaire invalide', 'Vérifiez les champs du mot de passe.');
      return;
    }
    this.notifService.succes('Mot de passe mis à jour', 'Votre mot de passe a été modifié avec succès.');
    this.formMotDePasse.reset();
  }

  ouvrirModalAssociation(): void {
    this.codeBoitierAssocier = '';
    this.nomBoitierAssocier = '';
    this.modalAssociationOuverte.set(true);
  }

  fermerModalAssociation(): void {
    this.modalAssociationOuverte.set(false);
  }

  validerAssociationBoitier(): void {
    if (!this.codeBoitierAssocier) {
      this.notifService.erreur('Erreur', 'Veuillez saisir le code du boîtier.');
      return;
    }
    const n: BoitierAssocieMock = {
      id: 'b-' + Date.now(),
      nomBoitier: this.nomBoitierAssocier || 'Nouveau Boîtier Alternia',
      codeBoitier: this.codeBoitierAssocier,
      emplacement: 'Bamako',
      statut: 'Connecté',
    };
    this.boitiers.update(l => [...l, n]);
    this.notifService.succes('Boîtier associé', `Le boîtier ${this.codeBoitierAssocier} a été associé à votre compte.`);
    this.fermerModalAssociation();
  }
}
