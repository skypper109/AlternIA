import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BoitierRepository } from '../../../data/repositories/boitier.repository';
import { Boitier } from '../../../domain/entites/boitier.entite';
import { StatutBoitier } from '../../../core/enums';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-gestion-boitier',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
<div class="page-content stagger-children">
  <div class="page-header">
    <h1 class="page-header__title">Mon boîtier Alternia</h1>
    <p class="page-header__subtitle">Gérez et configurez votre boîtier d'apprentissage</p>
  </div>

  @if (chargement()) {
    <div class="skeleton" style="height:500px;border-radius:16px;"></div>
  } @else if (boitier()) {

    <!-- Boîtier Hero Card -->
    <div class="boitier-hero">
      <div class="boitier-hero__visual">
        <!-- Device illustration -->
        <div class="device-illustration">
          <div class="device-body">
            <div class="device-screen">
              <div class="device-screen__content">
                <div class="device-logo">A</div>
                <div class="device-status-light" [class.light-on]="boitier()!.statut === StatutBoitier.EN_LIGNE_CLOUD"></div>
              </div>
            </div>
            <div class="device-base"></div>
          </div>
        </div>
      </div>

      <div class="boitier-hero__info">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
          <h2 class="fw-bold text-xl">{{ boitier()!.nom }}</h2>
          <span class="badge" [class.badge-success]="boitier()!.statut === StatutBoitier.EN_LIGNE_CLOUD" [class.badge-warning]="boitier()!.statut === StatutBoitier.HORS_LIGNE_LOCAL" [class.badge-danger]="boitier()!.statut === StatutBoitier.DECONNECTE">
            <span class="dot"></span>
            {{ getStatutLabel(boitier()!.statut) }}
          </span>
        </div>

        <div class="boitier-info-grid">
          <div class="boitier-info-item">
            <span class="text-xs text-secondary">Modèle</span>
            <span class="fw-semibold text-sm">{{ boitier()!.modele }}</span>
          </div>
          <div class="boitier-info-item">
            <span class="text-xs text-secondary">Code unique</span>
            <span class="fw-semibold text-sm" style="font-family:var(--font-mono);">{{ boitier()!.codeUnique }}</span>
          </div>
          <div class="boitier-info-item">
            <span class="text-xs text-secondary">Firmware</span>
            <span class="fw-semibold text-sm">v{{ boitier()!.versionFirmware }}</span>
          </div>
          <div class="boitier-info-item">
            <span class="text-xs text-secondary">Dernière sync</span>
            <span class="fw-semibold text-sm">{{ boitier()!.derniereSync | date:'dd/MM HH:mm' }}</span>
          </div>
        </div>

        <!-- Indicators -->
        <div class="boitier-indicators">
          <!-- Battery -->
          <div class="indicator-card">
            <div class="indicator-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px;">
                <rect x="1" y="6" width="18" height="12" rx="2" ry="2"/><line x1="23" y1="11" x2="23" y2="13"/>
              </svg>
              Batterie
            </div>
            <div class="indicator-value" [class.indicator-value--danger]="boitier()!.niveauBatterie <= 20">{{ boitier()!.niveauBatterie }}%</div>
            <div class="progress-bar" style="margin-top:8px;">
              <div class="progress-bar__fill" [class.success]="boitier()!.niveauBatterie > 50" [class.warning]="boitier()!.niveauBatterie <= 50 && boitier()!.niveauBatterie > 20" [class.danger]="boitier()!.niveauBatterie <= 20" [style.width.%]="boitier()!.niveauBatterie"></div>
            </div>
          </div>

          <!-- Stockage -->
          <div class="indicator-card">
            <div class="indicator-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px;">
                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/>
              </svg>
              Stockage
            </div>
            <div class="indicator-value">{{ (boitier()!.espaceUtilise / 1000).toFixed(1) }} / {{ (boitier()!.espaceTotal / 1000).toFixed(0) }} Go</div>
            <div class="progress-bar" style="margin-top:8px;">
              <div class="progress-bar__fill innovation" [style.width.%]="(boitier()!.espaceUtilise / boitier()!.espaceTotal) * 100"></div>
            </div>
          </div>

          <!-- WiFi -->
          <div class="indicator-card">
            <div class="indicator-label">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px;">
                <path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/>
              </svg>
              Réseau Wi-Fi
            </div>
            <div class="indicator-value" [class.text-success]="boitier()!.wifiConnecte" [class.text-danger]="!boitier()!.wifiConnecte">
              {{ boitier()!.wifiConnecte ? boitier()!.ssid : 'Non connecté' }}
            </div>
            <button class="btn btn-outline btn-sm" style="margin-top:10px;" (click)="ouvrirModalWifi()" id="btn-config-wifi">Configurer Wi-Fi</button>
          </div>
        </div>

        <!-- Actions -->
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:20px;">
          <button class="btn btn-primary btn-sm" (click)="synchroniserBoitier()" id="btn-sync-boitier" [disabled]="synchroEnCours()">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" [class.animate-spin]="synchroEnCours()">
              <path d="M2 7C2 4.239 4.239 2 7 2C9.209 2 11.14 3.14 12.25 4.875" stroke="white" stroke-width="1.3" stroke-linecap="round"/>
              <path d="M12 7C12 9.761 9.761 12 7 12C4.791 12 2.86 10.86 1.75 9.125" stroke="white" stroke-width="1.3" stroke-linecap="round"/>
              <path d="M12 2V5H9" stroke="white" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 12V9H5" stroke="white" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            {{ synchroEnCours() ? 'Synchronisation…' : 'Synchroniser maintenant' }}
          </button>
          <button class="btn btn-outline btn-sm" (click)="basculerModeHorsLigne()" id="btn-mode-hors-ligne">
            {{ boitier()!.statut === StatutBoitier.HORS_LIGNE_LOCAL ? 'Mode en ligne' : 'Mode hors ligne' }}
          </button>
          <button class="btn btn-ghost btn-sm" (click)="ouvrirModalReinitialiser()" id="btn-reinitialiser">Réinitialiser</button>
        </div>
      </div>
    </div>

    <!-- Configuration -->
    <div class="card">
      <div class="card__header">
        <h2 class="card__title">Configuration</h2>
      </div>
      <div class="card__body">
        <div class="config-grid">
          <div class="config-item">
            <label class="form-label">Volume sonore</label>
            <div style="display:flex;align-items:center;gap:12px;">
              <input type="range" min="0" max="100" [(ngModel)]="volume" id="slider-volume" style="flex:1;accent-color:var(--color-secondaire);"/>
              <span class="fw-semibold text-sm">{{ volume }}%</span>
            </div>
          </div>
          <div class="config-item">
            <label class="form-label">Durée de session max.</label>
            <select class="form-input" [(ngModel)]="dureeMax" id="select-duree-session" style="max-width:200px;">
              <option value="60">60 minutes</option>
              <option value="90">90 minutes</option>
              <option value="120">120 minutes</option>
            </select>
          </div>
          <div class="config-item">
            <label class="form-label">Heure d'accès autorisée</label>
            <div style="display:flex;align-items:center;gap:8px;">
              <input type="time" class="form-input" [(ngModel)]="heureDebut" id="input-debut-parent" style="max-width:130px;"/>
              <span class="text-secondary">→</span>
              <input type="time" class="form-input" [(ngModel)]="heureFin" id="input-fin-parent" style="max-width:130px;"/>
            </div>
          </div>
        </div>
        <button class="btn btn-secondary" style="margin-top:20px;" (click)="sauvegarderConfig()" id="btn-sauvegarder-config-boitier">Sauvegarder la configuration</button>
      </div>
    </div>

  } @else {
    <div class="etat-vide-boitier">
      <div class="etat-vide-boitier__icon">
        <svg width="56" height="56" viewBox="0 0 18 18" fill="none" style="color:var(--color-text-tertiary);">
          <path d="M2 5L9 1.5L16 5V13L9 16.5L2 13V5Z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
          <path d="M2 5L9 8.5L16 5" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
          <path d="M9 8.5V16.5" stroke="currentColor" stroke-width="1.2"/>
        </svg>
      </div>
      <h2 class="fw-bold text-xl">Aucun boîtier associé</h2>
      <p class="text-secondary text-sm" style="margin-top:8px;">Associez votre boîtier Alternia à l'aide de son code unique</p>
      <button class="btn btn-primary" style="margin-top:20px;" (click)="ouvrirModalAssociation()" id="btn-associer-boitier">Associer un boîtier</button>
    </div>
  }

  <!-- Modal Wi-Fi -->
  @if (modalWifiOuverte()) {
    <div class="modal-overlay" (click)="fermerModalWifi()">
      <div class="modal-card animate-scale-in" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <h3 class="fw-bold text-lg">Configuration Wi-Fi</h3>
          <button class="btn btn-ghost btn-sm btn-icon" (click)="fermerModalWifi()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        </div>
        <div class="modal-body" style="display:flex;flex-direction:column;gap:14px;padding:20px 0;">
          <div class="form-group">
            <label class="form-label">Nom du réseau (SSID)</label>
            <input type="text" class="form-input" [(ngModel)]="nouveauSsid" placeholder="Maison_Coulibaly_Bamako"/>
          </div>
          <div class="form-group">
            <label class="form-label">Mot de passe Wi-Fi</label>
            <input type="password" class="form-input" [(ngModel)]="motDePasseWifi" placeholder="••••••••"/>
          </div>
        </div>
        <div class="modal-footer" style="display:flex;justify-content:flex-end;gap:10px;">
          <button class="btn btn-ghost" (click)="fermerModalWifi()">Annuler</button>
          <button class="btn btn-secondary" (click)="connecterWifi()">Se connecter</button>
        </div>
      </div>
    </div>
  }

  <!-- Modal Réinitialiser -->
  @if (modalResetOuverte()) {
    <div class="modal-overlay" (click)="fermerModalReinitialiser()">
      <div class="modal-card animate-scale-in" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <h3 class="fw-bold text-lg text-danger">Réinitialisation du boîtier</h3>
          <button class="btn btn-ghost btn-sm btn-icon" (click)="fermerModalReinitialiser()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        </div>
        <div class="modal-body" style="padding:20px 0;">
          <p class="text-sm text-secondary">Êtes-vous sûr de vouloir réinitialiser les paramètres d'usine du boîtier ? Le boîtier redémarrera et réappliquera la configuration par défaut.</p>
        </div>
        <div class="modal-footer" style="display:flex;justify-content:flex-end;gap:10px;">
          <button class="btn btn-ghost" (click)="fermerModalReinitialiser()">Annuler</button>
          <button class="btn btn-danger" (click)="confirmerReinitialisation()">Réinitialiser</button>
        </div>
      </div>
    </div>
  }

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
            <input type="text" class="form-input" [(ngModel)]="codeBoitierAssociation" placeholder="ALT-HOME-0042"/>
            <span class="text-xs text-secondary">Indiqué sous le boîtier Alternia.</span>
          </div>
        </div>
        <div class="modal-footer" style="display:flex;justify-content:flex-end;gap:10px;">
          <button class="btn btn-ghost" (click)="fermerModalAssociation()">Annuler</button>
          <button class="btn btn-primary" (click)="associerBoitierAction()">Valider l'association</button>
        </div>
      </div>
    </div>
  }
</div>
  `,
  styles: [`
    .boitier-hero { display: grid; grid-template-columns: auto 1fr; gap: 32px; background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: var(--radius-xl); padding: 32px; margin-bottom: 24px; box-shadow: var(--shadow-md); @media(max-width:768px){ grid-template-columns: 1fr; } }
    .boitier-hero__visual { display: flex; align-items: center; justify-content: center; }
    .device-illustration { display: flex; justify-content: center; }
    .device-body { width: 140px; display: flex; flex-direction: column; align-items: center; gap: 0; }
    .device-screen { width: 140px; height: 100px; background: #0F172A; border-radius: 12px 12px 4px 4px; border: 2px solid #334155; display: flex; align-items: center; justify-content: center; }
    .device-screen__content { display: flex; flex-direction: column; align-items: center; gap: 8px; }
    .device-logo { font-family: var(--font-display); font-size: 28px; font-weight: var(--fw-bold); color: var(--color-secondaire); }
    .device-status-light { width: 8px; height: 8px; border-radius: 50%; background: #334155; transition: background var(--transition-base); }
    .device-status-light.light-on { background: var(--color-success); box-shadow: 0 0 8px var(--color-success); animation: pulse-soft 2s infinite; }
    .device-base { width: 100px; height: 12px; background: #334155; border-radius: 0 0 8px 8px; }
    .boitier-info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 20px; }
    .boitier-info-item { display: flex; flex-direction: column; gap: 3px; padding: 10px 14px; background: var(--color-bg-surface-2); border-radius: var(--radius-md); border: 1px solid var(--color-border); }
    .boitier-indicators { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; }
    .indicator-card { padding: 14px; background: var(--color-bg-surface-2); border-radius: var(--radius-md); border: 1px solid var(--color-border); }
    .indicator-label { font-size: var(--text-xs); color: var(--color-text-secondary); margin-bottom: 4px; }
    .indicator-value { font-size: var(--text-base); font-weight: var(--fw-bold); color: var(--color-text-primary); }
    .indicator-value--danger { color: var(--color-danger); }
    .config-grid { display: flex; flex-direction: column; gap: 20px; }
    .config-item { display: flex; flex-direction: column; gap: 8px; }
    .etat-vide-boitier { text-align: center; padding: 80px 24px; }
    .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 999; display: flex; align-items: center; justify-content: center; padding: 20px; }
    .modal-card { background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: var(--radius-xl); padding: 24px; max-width: 480px; width: 100%; box-shadow: var(--shadow-xl); }
    .modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--color-border); padding-bottom: 12px; }
  `],
})
export class GestionBoitierComposant implements OnInit {
  private readonly repo = inject(BoitierRepository);
  private readonly notifService = inject(NotificationService);

  readonly StatutBoitier = StatutBoitier;

  chargement = signal(true);
  boitier = signal<Boitier | null>(null);
  synchroEnCours = signal(false);

  volume = 75;
  dureeMax = '90';
  heureDebut = '07:00';
  heureFin = '21:00';

  modalWifiOuverte = signal(false);
  nouveauSsid = '';
  motDePasseWifi = '';

  modalResetOuverte = signal(false);
  modalAssociationOuverte = signal(false);
  codeBoitierAssociation = '';

  ngOnInit(): void {
    this.repo.obtenirBoitierParEnfant('enfant-1').subscribe(b => {
      this.boitier.set(b ?? null);
      if (b) {
        this.nouveauSsid = b.ssid ?? 'Maison_Coulibaly_Bamako';
      }
      this.chargement.set(false);
    });
  }

  getStatutLabel(statut: StatutBoitier): string {
    return { [StatutBoitier.EN_LIGNE_CLOUD]: 'En ligne', [StatutBoitier.HORS_LIGNE_LOCAL]: 'Hors ligne', [StatutBoitier.DECONNECTE]: 'Déconnecté' }[statut] ?? '';
  }

  synchroniserBoitier(): void {
    const b = this.boitier();
    if (!b) return;
    this.synchroEnCours.set(true);
    this.repo.synchroniser(b.id).subscribe({
      next: (res) => {
        this.boitier.update(item => item ? { ...item, derniereSync: new Date(res.timestamp || new Date()), statut: StatutBoitier.EN_LIGNE_CLOUD } : null);
        this.synchroEnCours.set(false);
        this.notifService.succes('Synchronisation réussie', `Le boîtier a synchronisé ${res.elementsSynchronises ?? 14} éléments avec la base de données.`);
      },
      error: () => {
        this.synchroEnCours.set(false);
        this.notifService.erreur('Échec de synchronisation', 'Impossible de joindre le serveur.');
      }
    });
  }

  basculerModeHorsLigne(): void {
    const b = this.boitier();
    if (!b) return;

    const nouveauStatut = b.statut === StatutBoitier.HORS_LIGNE_LOCAL ? StatutBoitier.EN_LIGNE_CLOUD : StatutBoitier.HORS_LIGNE_LOCAL;
    this.boitier.update(item => item ? { ...item, statut: nouveauStatut } : null);
    this.notifService.info('Mode réseau', `Le boîtier est maintenant en mode ${nouveauStatut === StatutBoitier.EN_LIGNE_CLOUD ? 'En ligne' : 'Hors ligne'}.`);
  }

  ouvrirModalWifi(): void {
    this.modalWifiOuverte.set(true);
  }

  fermerModalWifi(): void {
    this.modalWifiOuverte.set(false);
  }

  connecterWifi(): void {
    const b = this.boitier();
    if (!b) return;
    if (!this.nouveauSsid) {
      this.notifService.erreur('Erreur Wi-Fi', 'Saisissez le nom du réseau.');
      return;
    }
    this.repo.configurerWifi(b.id, this.nouveauSsid, this.motDePasseWifi).subscribe({
      next: () => {
        this.boitier.update(item => item ? { ...item, wifiConnecte: true, ssid: this.nouveauSsid, statut: StatutBoitier.EN_LIGNE_CLOUD } : null);
        this.notifService.succes('Wi-Fi connecté', `Le boîtier est connecté au réseau "${this.nouveauSsid}".`);
        this.fermerModalWifi();
      },
      error: () => {
        this.notifService.erreur('Erreur Wi-Fi', 'Échec de la configuration Wi-Fi.');
      }
    });
  }

  sauvegarderConfig(): void {
    this.notifService.succes('Configuration sauvegardée', 'Les paramètres audio et horaires du boîtier ont été enregistrés.');
  }

  ouvrirModalReinitialiser(): void {
    this.modalResetOuverte.set(true);
  }

  fermerModalReinitialiser(): void {
    this.modalResetOuverte.set(false);
  }

  confirmerReinitialisation(): void {
    this.boitier.update(b => b ? { ...b, niveauBatterie: 100, derniereSync: new Date() } : null);
    this.notifService.avertissement('Réinitialisation', 'Le boîtier a été réinitialisé avec succès.');
    this.fermerModalReinitialiser();
  }

  ouvrirModalAssociation(): void {
    this.codeBoitierAssociation = '';
    this.modalAssociationOuverte.set(true);
  }

  fermerModalAssociation(): void {
    this.modalAssociationOuverte.set(false);
  }

  associerBoitierAction(): void {
    if (!this.codeBoitierAssociation) {
      this.notifService.erreur('Erreur', 'Entrez le code de votre boîtier.');
      return;
    }

    this.boitier.set({
      id: 'boitier-home-1',
      codeUnique: this.codeBoitierAssociation,
      nom: 'Boîtier Maison',
      modele: 'Alternia Box v2',
      statut: StatutBoitier.EN_LIGNE_CLOUD,
      niveauBatterie: 90,
      versionFirmware: '2.4.1',
      derniereSync: new Date(),
      espaceUtilise: 3200,
      espaceTotal: 16000,
      wifiConnecte: true,
      ssid: 'Maison_Coulibaly_Bamako',
      enfantId: 'enfant-1',
      dateActivation: new Date(),
    });

    this.notifService.succes('Boîtier associé', `Le boîtier ${this.codeBoitierAssociation} a été associé avec succès.`);
    this.fermerModalAssociation();
  }
}
