import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators, FormsModule } from '@angular/forms';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-parametres-etablissement',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  template: `
<div class="page-content stagger-children">
  <div class="page-header">
    <h1 class="page-header__title">Paramètres</h1>
    <p class="page-header__subtitle">Configurez votre établissement et vos préférences</p>
  </div>

  <div class="settings-layout">
    <!-- Left Nav -->
    <div class="settings-nav">
      @for (section of sections; track section.id) {
        <button
          class="settings-nav-item"
          [class.settings-nav-item--active]="sectionActive() === section.id"
          (click)="sectionActive.set(section.id)"
          [id]="'nav-param-' + section.id"
        >
          <!-- no emoji icon -->
          {{ section.label }}
        </button>
      }
    </div>

    <!-- Content -->
    <div class="settings-content">

      @if (sectionActive() === 'etablissement') {
        <div class="settings-section animate-fade-in">
          <h2 class="settings-section__title">Informations de l'établissement</h2>
          <form [formGroup]="formEtablissement" (ngSubmit)="sauvegarderEtablissement()" class="settings-form">
            <div class="form-group">
              <label class="form-label">Nom de l'établissement</label>
              <input type="text" class="form-input" formControlName="nom" placeholder="Lycée Soundiata Keïta Bamako"/>
            </div>
            <div class="form-grid">
              <div class="form-group">
                <label class="form-label">Ville</label>
                <input type="text" class="form-input" formControlName="ville" placeholder="Bamako"/>
              </div>
              <div class="form-group">
                <label class="form-label">Pays</label>
                <input type="text" class="form-input" formControlName="pays" placeholder="Mali"/>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Email de contact</label>
              <input type="email" class="form-input" formControlName="email" placeholder="contact@soundiatakeita.edu.ml"/>
            </div>
            <div class="form-group">
              <label class="form-label">Téléphone</label>
              <input type="tel" class="form-input" formControlName="telephone" placeholder="+223 20 22 11 00"/>
            </div>
            <div class="form-group">
              <label class="form-label">Adresse</label>
              <textarea class="form-input" formControlName="adresse" rows="3" placeholder="Hamdallaye ACI 2000, Bamako"></textarea>
            </div>
            <button type="submit" class="btn btn-primary" id="btn-sauvegarder-etab">Sauvegarder les modifications</button>
          </form>
        </div>
      }

      @if (sectionActive() === 'administrateurs') {
        <div class="settings-section animate-fade-in">
          <h2 class="settings-section__title">Gestion des administrateurs</h2>
          <div class="admin-list">
            @for (admin of admins(); track admin.email) {
              <div class="admin-item">
                <div style="display:flex;align-items:center;gap:12px;">
                  <div class="avatar avatar-md avatar-primary">{{ admin.nom.charAt(0) }}</div>
                  <div>
                    <div class="fw-semibold">{{ admin.nom }}</div>
                    <div class="text-sm text-secondary">{{ admin.email }}</div>
                  </div>
                </div>
                <span class="badge badge-primary">{{ admin.role }}</span>
              </div>
            }
          </div>
          <button class="btn btn-outline btn-sm" style="margin-top:16px;" (click)="ouvrirModalInvite()" id="btn-inviter-admin">+ Inviter un administrateur</button>
        </div>
      }

      @if (sectionActive() === 'preferences') {
        <div class="settings-section animate-fade-in">
          <h2 class="settings-section__title">Préférences</h2>
          <div class="preferences-list">
            @for (pref of preferences(); track pref.id) {
              <div class="pref-item">
                <div>
                  <div class="fw-semibold text-sm">{{ pref.label }}</div>
                  <div class="text-xs text-secondary">{{ pref.desc }}</div>
                </div>
                <label class="toggle-switch">
                  <input type="checkbox" [checked]="pref.active" (change)="basculerPreference(pref.id)" [id]="'toggle-' + pref.id"/>
                  <span class="toggle-slider"></span>
                </label>
              </div>
            }
          </div>
        </div>
      }

      @if (sectionActive() === 'boitier') {
        <div class="settings-section animate-fade-in">
          <h2 class="settings-section__title">Configuration des boîtiers</h2>
          <div class="boitier-config">
            <div class="config-item">
              <label class="form-label">Durée de session maximale (minutes)</label>
              <input type="number" class="form-input" [(ngModel)]="dureeSession" id="input-duree-session" style="max-width:150px;"/>
            </div>
            <div class="config-item">
              <label class="form-label">Heure de début autorisée</label>
              <input type="time" class="form-input" [(ngModel)]="heureDebut" id="input-heure-debut" style="max-width:150px;"/>
            </div>
            <div class="config-item">
              <label class="form-label">Heure de fin autorisée</label>
              <input type="time" class="form-input" [(ngModel)]="heureFin" id="input-heure-fin" style="max-width:150px;"/>
            </div>
            <button class="btn btn-primary" (click)="sauvegarderBoitier()" id="btn-sauvegarder-boitier">Sauvegarder la configuration</button>
          </div>
        </div>
      }
    </div>
  </div>

  <!-- Modal invitation admin -->
  @if (modalInviteOuverte()) {
    <div class="modal-overlay" (click)="fermerModalInvite()">
      <div class="modal-card animate-scale-in" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <h3 class="fw-bold text-lg">Inviter un administrateur</h3>
          <button class="btn btn-ghost btn-sm btn-icon" (click)="fermerModalInvite()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        </div>
        <div class="modal-body" style="display:flex;flex-direction:column;gap:14px;padding:20px 0;">
          <div class="form-group">
            <label class="form-label">Nom complet</label>
            <input type="text" class="form-input" [(ngModel)]="nouvelAdminNom" placeholder="Mme. Keita Fatoumata"/>
          </div>
          <div class="form-group">
            <label class="form-label">Adresse email</label>
            <input type="email" class="form-input" [(ngModel)]="nouvelAdminEmail" placeholder="fatoumata@soundiatakeita.edu.ml"/>
          </div>
          <div class="form-group">
            <label class="form-label">Rôle</label>
            <select class="form-input" [(ngModel)]="nouvelAdminRole">
              <option value="Administrateur">Administrateur</option>
              <option value="Responsable pédagogique">Responsable pédagogique</option>
            </select>
          </div>
        </div>
        <div class="modal-footer" style="display:flex;justify-content:flex-end;gap:10px;">
          <button class="btn btn-ghost" (click)="fermerModalInvite()">Annuler</button>
          <button class="btn btn-primary" (click)="envoyerInvitationAdmin()">Envoyer l'invitation</button>
        </div>
      </div>
    </div>
  }
</div>
  `,
  styles: [`
    .settings-layout { display: grid; grid-template-columns: 220px 1fr; gap: 24px; @media(max-width:768px){ grid-template-columns: 1fr; } }
    .settings-nav { background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 8px; height: fit-content; }
    .settings-nav-item { display: flex; align-items: center; gap: 10px; width: 100%; padding: 10px 12px; border-radius: var(--radius-md); border: none; background: none; cursor: pointer; font-size: var(--text-sm); font-weight: var(--fw-medium); color: var(--color-text-secondary); transition: all var(--transition-fast); }
    .settings-nav-item:hover { background: var(--color-bg-surface-2); color: var(--color-text-primary); }
    .settings-nav-item--active { background: var(--color-primaire-light) !important; color: var(--color-primaire) !important; font-weight: var(--fw-semibold); }
    .settings-content { background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 24px; box-shadow: var(--shadow-xs); }
    .settings-section__title { font-family: var(--font-display); font-size: var(--text-lg); font-weight: var(--fw-bold); color: var(--color-text-primary); margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid var(--color-border); }
    .settings-form { display: flex; flex-direction: column; gap: 16px; }
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .admin-list { display: flex; flex-direction: column; }
    .admin-item { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid var(--color-border); }
    .admin-item:last-child { border-bottom: none; }
    .preferences-list { display: flex; flex-direction: column; }
    .pref-item { display: flex; align-items: center; justify-content: space-between; padding: 14px 0; border-bottom: 1px solid var(--color-border); }
    .pref-item:last-child { border-bottom: none; }
    .boitier-config { display: flex; flex-direction: column; gap: 16px; }
    .config-item { display: flex; flex-direction: column; gap: 6px; }
  `],
})
export class ParametresEtablissementComposant {
  private readonly fb = inject(FormBuilder);
  private readonly notifService = inject(NotificationService);

  sectionActive = signal('etablissement');

  readonly sections = [
    { id: 'etablissement', label: 'Établissement' },
    { id: 'administrateurs', label: 'Administrateurs' },
    { id: 'preferences', label: 'Préférences' },
    { id: 'boitier', label: 'Boîtiers' },
  ];

  admins = signal([
    { nom: 'Dr. Konaté Moussa', email: 'konate@soundiatakeita.edu.ml', role: 'Super Admin' },
    { nom: 'Mme. Diallo Aminata', email: 'diallo@soundiatakeita.edu.ml', role: 'Responsable pédagogique' },
    { nom: 'M. Traoré Seydou', email: 'traore@soundiatakeita.edu.ml', role: 'Administrateur' },
  ]);

  preferences = signal([
    { id: 'notifs-email', label: 'Notifications par email', desc: 'Recevoir les alertes et rapports par email', active: true },
    { id: 'sync-auto', label: 'Synchronisation automatique', desc: 'Synchroniser les boîtiers toutes les nuits', active: true },
    { id: 'mode-debug', label: 'Logs détaillés', desc: 'Activer les logs techniques pour le débogage', active: false },
    { id: 'backup', label: 'Sauvegarde automatique', desc: 'Sauvegarde quotidienne des données', active: true },
  ]);

  dureeSession = 90;
  heureDebut = '07:00';
  heureFin = '22:00';

  modalInviteOuverte = signal(false);
  nouvelAdminNom = '';
  nouvelAdminEmail = '';
  nouvelAdminRole = 'Administrateur';

  formEtablissement = this.fb.group({
    nom: ['Lycée Soundiata Keïta Bamako', Validators.required],
    ville: ['Bamako', Validators.required],
    pays: ['Mali'],
    email: ['contact@soundiatakeita.edu.ml', [Validators.required, Validators.email]],
    telephone: ['+223 20 22 11 00'],
    adresse: ['Hamdallaye ACI 2000, Bamako'],
  });

  sauvegarderEtablissement(): void {
    if (this.formEtablissement.valid) {
      this.notifService.succes('Modifications enregistrées', 'Les informations de l\'établissement ont été mises à jour.');
    } else {
      this.notifService.erreur('Formulaire invalide', 'Veuillez vérifier les champs renseignés.');
    }
  }

  ouvrirModalInvite(): void {
    this.nouvelAdminNom = '';
    this.nouvelAdminEmail = '';
    this.nouvelAdminRole = 'Administrateur';
    this.modalInviteOuverte.set(true);
  }

  fermerModalInvite(): void {
    this.modalInviteOuverte.set(false);
  }

  envoyerInvitationAdmin(): void {
    if (!this.nouvelAdminNom || !this.nouvelAdminEmail) {
      this.notifService.erreur('Champs requis', 'Veuillez saisir un nom et un email.');
      return;
    }
    this.admins.update(list => [
      ...list,
      { nom: this.nouvelAdminNom, email: this.nouvelAdminEmail, role: this.nouvelAdminRole }
    ]);
    this.notifService.succes('Invitation envoyée', `Un email a été envoyé à ${this.nouvelAdminEmail}.`);
    this.fermerModalInvite();
  }

  basculerPreference(id: string): void {
    this.preferences.update(list => list.map(p => p.id === id ? { ...p, active: !p.active } : p));
    const pref = this.preferences().find(p => p.id === id);
    if (pref) {
      this.notifService.info('Préférence mise à jour', `${pref.label} est désormais ${pref.active ? 'activé' : 'désactivé'}.`);
    }
  }

  sauvegarderBoitier(): void {
    this.notifService.succes('Configuration enregistrée', 'Les paramètres des boîtiers ont été sauvegardés.');
  }
}
