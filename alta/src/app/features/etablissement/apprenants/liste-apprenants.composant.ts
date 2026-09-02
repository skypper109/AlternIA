import { Component, OnInit, signal, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BoitierRepository } from '../../../data/repositories/boitier.repository';
import { Boitier } from '../../../domain/entites/boitier.entite';
import { StatutBoitier } from '../../../core/enums';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-liste-apprenants',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
<div class="page-content stagger-children">
  <div class="page-header">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
      <div>
        <h1 class="page-header__title">Supervision des Boîtiers</h1>
        <p class="page-header__subtitle">{{ boitiers().length }} boîtiers gérés · {{ nbEnLigne() }} en ligne · {{ nbHorsLigne() }} en mode local</p>
      </div>
      <div style="display: flex; gap: 10px;">
        <button class="btn btn-outline btn-sm" (click)="exporterCSV()" id="btn-exporter-boitiers">Exporter CSV</button>
        <button class="btn btn-primary btn-sm" (click)="ouvrirModalAjout()" id="btn-ajouter-boitier">+ Enregistrer un boîtier</button>
      </div>
    </div>
  </div>

  <!-- Filtres & Recherche -->
  <div class="filters-bar">
    <div class="search-input-wrapper" style="max-width: 360px; flex: 1;">
      <svg class="search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.5"/>
        <path d="M11 11L14 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
      <input
        id="recherche-boitier"
        type="text"
        class="form-input"
        placeholder="Rechercher un boîtier par nom ou code..."
        [(ngModel)]="recherche"
        (input)="filtrer()"
      />
    </div>
    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
      <button class="btn btn-ghost btn-sm filtre-btn" [class.filtre-btn--active]="filtre() === 'tous'" (click)="setFiltre('tous')" id="btn-filtre-tous">Tous ({{ boitiers().length }})</button>
      <button class="btn btn-ghost btn-sm filtre-btn" [class.filtre-btn--active]="filtre() === 'en_ligne'" (click)="setFiltre('en_ligne')" id="btn-filtre-en-ligne">En ligne ({{ nbEnLigne() }})</button>
      <button class="btn btn-ghost btn-sm filtre-btn" [class.filtre-btn--active]="filtre() === 'hors_ligne'" (click)="setFiltre('hors_ligne')" id="btn-filtre-hors-ligne">Mode local ({{ nbHorsLigne() }})</button>
    </div>
  </div>

  @if (chargement()) {
    <div class="skeleton" style="height: 400px; border-radius: 16px;"></div>
  } @else {
    <div class="card">
      <div class="table-wrapper">
        <table class="table">
          <thead>
            <tr>
              <th>Boîtier</th>
              <th>Code Unique</th>
              <th>Version Firmware</th>
              <th>Stockage Utilisé</th>
              <th>Batterie</th>
              <th>Réseau Wi-Fi</th>
              <th>Dernière Sync</th>
              <th>Statut</th>
              <th style="text-align: right;">Actions</th>
            </tr>
          </thead>
          <tbody>
            @for (b of boitiersFiltres(); track b.id) {
              <tr>
                <td>
                  <div style="display: flex; align-items: center; gap: 10px;">
                    <div class="icon-box icon-box-sm icon-box-primary">
                        <svg width="14" height="14" viewBox="0 0 18 18" fill="none">
                          <path d="M2 5L9 1.5L16 5V13L9 16.5L2 13V5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
                          <path d="M2 5L9 8.5L16 5" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
                          <path d="M9 8.5V16.5" stroke="currentColor" stroke-width="1.5"/>
                        </svg>
                      </div>
                    <div>
                      <div class="fw-semibold">{{ b.nom }}</div>
                      <div class="text-xs text-secondary">{{ b.modele }}</div>
                    </div>
                  </div>
                </td>
                <td><span class="text-mono text-xs fw-bold">{{ b.codeUnique }}</span></td>
                <td class="text-secondary text-sm">v{{ b.versionFirmware }}</td>
                <td>
                  <div style="display: flex; flex-direction: column; gap: 3px; min-width: 110px;">
                    <span class="text-xs text-secondary">{{ (b.espaceUtilise / 1000).toFixed(1) }} / {{ (b.espaceTotal / 1000).toFixed(0) }} Go</span>
                    <div class="progress-bar" style="height: 4px;">
                      <div class="progress-bar__fill innovation" [style.width.%]="(b.espaceUtilise / b.espaceTotal) * 100"></div>
                    </div>
                  </div>
                </td>
                <td>
                  <div style="display: flex; align-items: center; gap: 6px;">
                    <div class="progress-bar" style="width: 50px; height: 6px;">
                      <div class="progress-bar__fill" [class.success]="b.niveauBatterie > 50" [class.warning]="b.niveauBatterie <= 50 && b.niveauBatterie > 20" [class.danger]="b.niveauBatterie <= 20" [style.width.%]="b.niveauBatterie"></div>
                    </div>
                    <span class="text-xs fw-semibold">{{ b.niveauBatterie }}%</span>
                  </div>
                </td>
                <td class="text-xs">
                  @if (b.wifiConnecte) {
                    <span class="text-success fw-medium">{{ b.ssid }}</span>
                  } @else {
                    <span class="text-tertiary">Déconnecté</span>
                  }
                </td>
                <td class="text-secondary text-sm">{{ b.derniereSync | date:'dd MMM yyyy, HH:mm' }}</td>
                <td>
                  <span class="badge" [class.badge-success]="b.statut === StatutBoitier.EN_LIGNE_CLOUD" [class.badge-warning]="b.statut === StatutBoitier.HORS_LIGNE_LOCAL" [class.badge-danger]="b.statut === StatutBoitier.DECONNECTE">
                    <span class="dot"></span>
                    {{ getStatutLabel(b.statut) }}
                  </span>
                </td>
                <td style="text-align: right;">
                  <button class="btn btn-ghost btn-sm btn-icon" (click)="voirBoitier(b)" [id]="'btn-voir-boitier-' + b.id" title="Inspecter">
                     <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                        <ellipse cx="8" cy="8" rx="6" ry="4" stroke="currentColor" stroke-width="1.3"/>
                        <circle cx="8" cy="8" r="1.5" fill="currentColor"/>
                      </svg>
                  </button>
                </td>
              </tr>
            } @empty {
              <tr>
                <td colspan="9" style="text-align: center; padding: 40px; color: var(--color-text-tertiary);">
                  Aucun boîtier ne correspond aux critères de recherche.
                </td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    </div>
  }

  <!-- Modale Détail Boîtier -->
  @if (modalBoitierOuverte() && boitierSelectionne()) {
    <div class="modal-overlay" (click)="fermerModal()">
      <div class="modal-card animate-scale-in" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <h3 class="fw-bold text-lg">Supervision du Boîtier</h3>
          <button class="btn btn-ghost btn-sm btn-icon" (click)="fermerModal()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        </div>
        <div class="modal-body" style="padding: 20px 0; display: flex; flex-direction: column; gap: 16px;">
          <div style="display: flex; align-items: center; gap: 14px;">
            <div class="icon-box icon-box-lg icon-box-primary">
              <svg width="22" height="22" viewBox="0 0 18 18" fill="none">
                <path d="M2 5L9 1.5L16 5V13L9 16.5L2 13V5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
                <path d="M2 5L9 8.5L16 5" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
                <path d="M9 8.5V16.5" stroke="currentColor" stroke-width="1.5"/>
              </svg>
            </div>
            <div>
              <div class="fw-bold text-lg">{{ boitierSelectionne()!.nom }}</div>
              <div class="text-xs text-mono text-secondary">{{ boitierSelectionne()!.codeUnique }} · {{ boitierSelectionne()!.modele }}</div>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div style="padding: 10px; background: var(--color-bg-surface-2); border-radius: var(--radius-md);">
              <div class="text-xs text-secondary">Statut Réseau</div>
              <div class="fw-bold text-sm" style="margin-top: 2px;">{{ getStatutLabel(boitierSelectionne()!.statut) }}</div>
            </div>
            <div style="padding: 10px; background: var(--color-bg-surface-2); border-radius: var(--radius-md);">
              <div class="text-xs text-secondary">Niveau Batterie</div>
              <div class="fw-bold text-sm" style="margin-top: 2px;">{{ boitierSelectionne()!.niveauBatterie }}%</div>
            </div>
            <div style="padding: 10px; background: var(--color-bg-surface-2); border-radius: var(--radius-md);">
              <div class="text-xs text-secondary">Firmware</div>
              <div class="fw-bold text-sm" style="margin-top: 2px;">v{{ boitierSelectionne()!.versionFirmware }}</div>
            </div>
            <div style="padding: 10px; background: var(--color-bg-surface-2); border-radius: var(--radius-md);">
              <div class="text-xs text-secondary">Réseau Wi-Fi</div>
              <div class="fw-bold text-sm" style="margin-top: 2px;">{{ boitierSelectionne()!.ssid || 'Mode local' }}</div>
            </div>
          </div>
        </div>
        <div class="modal-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <button class="btn btn-ghost" (click)="fermerModal()">Fermer</button>
          <button class="btn btn-primary" (click)="forcerSynchronisation(boitierSelectionne()!)">Synchroniser maintenant</button>
        </div>
      </div>
    </div>
  }

  <!-- Modale Ajout Boîtier -->
  @if (modalAjoutOuverte()) {
    <div class="modal-overlay" (click)="fermerModalAjout()">
      <div class="modal-card animate-scale-in" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <h3 class="fw-bold text-lg">Enregistrer un nouveau boîtier</h3>
          <button class="btn btn-ghost btn-sm btn-icon" (click)="fermerModalAjout()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        </div>
        <div class="modal-body" style="display: flex; flex-direction: column; gap: 14px; padding: 20px 0;">
          <div class="form-group">
            <label class="form-label">Nom du boîtier</label>
            <input type="text" class="form-input" [(ngModel)]="nouveauBoitierNom" placeholder="Boîtier Salle Informatique 1"/>
          </div>
          <div class="form-group">
            <label class="form-label">Code unique boîtier</label>
            <input type="text" class="form-input text-mono" [(ngModel)]="nouveauBoitierCode" placeholder="ALT-BKO-2026-X"/>
          </div>
        </div>
        <div class="modal-footer" style="display: flex; justify-content: flex-end; gap: 10px;">
          <button class="btn btn-ghost" (click)="fermerModalAjout()">Annuler</button>
          <button class="btn btn-primary" (click)="enregistrerBoitier()">Enregistrer</button>
        </div>
      </div>
    </div>
  }
</div>
  `,
  styles: [`
    .filters-bar { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
    .filtre-btn { font-size: var(--text-xs); color: var(--color-text-secondary); border-radius: var(--radius-full); padding: 4px 12px; }
    .filtre-btn--active { background: var(--color-primaire-light); color: var(--color-primaire); font-weight: var(--fw-semibold); }
    .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 999; display: flex; align-items: center; justify-content: center; padding: 20px; }
    .modal-card { background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: var(--radius-xl); padding: 24px; max-width: 520px; width: 100%; box-shadow: var(--shadow-xl); }
    .modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--color-border); padding-bottom: 12px; }
  `],
})
export class ListeApprenantsComposant implements OnInit {
  private readonly boitierRepo = inject(BoitierRepository);
  private readonly notifService = inject(NotificationService);

  readonly StatutBoitier = StatutBoitier;

  chargement = signal(true);
  boitiers = signal<Boitier[]>([]);
  recherche = '';
  filtre = signal<'tous' | 'en_ligne' | 'hors_ligne'>('tous');

  boitiersFiltres = signal<Boitier[]>([]);
  boitierSelectionne = signal<Boitier | null>(null);
  modalBoitierOuverte = signal(false);

  modalAjoutOuverte = signal(false);
  nouveauBoitierNom = '';
  nouveauBoitierCode = '';

  readonly nbEnLigne = computed(() => this.boitiers().filter(b => b.statut === StatutBoitier.EN_LIGNE_CLOUD).length);
  readonly nbHorsLigne = computed(() => this.boitiers().filter(b => b.statut === StatutBoitier.HORS_LIGNE_LOCAL).length);

  ngOnInit(): void {
    this.boitierRepo.obtenirBoitiersEtablissement('etab-1').subscribe(list => {
      this.boitiers.set(list);
      this.boitiersFiltres.set(list);
      this.chargement.set(false);
    });
  }

  getStatutLabel(statut: StatutBoitier): string {
    return { [StatutBoitier.EN_LIGNE_CLOUD]: 'En ligne', [StatutBoitier.HORS_LIGNE_LOCAL]: 'Mode local', [StatutBoitier.DECONNECTE]: 'Déconnecté' }[statut] ?? '';
  }

  setFiltre(f: 'tous' | 'en_ligne' | 'hors_ligne'): void {
    this.filtre.set(f);
    this.filtrer();
  }

  filtrer(): void {
    let res = this.boitiers();

    if (this.filtre() === 'en_ligne') {
      res = res.filter(b => b.statut === StatutBoitier.EN_LIGNE_CLOUD);
    } else if (this.filtre() === 'hors_ligne') {
      res = res.filter(b => b.statut === StatutBoitier.HORS_LIGNE_LOCAL);
    }

    if (this.recherche.trim()) {
      const q = this.recherche.toLowerCase();
      res = res.filter(b => b.nom.toLowerCase().includes(q) || b.codeUnique.toLowerCase().includes(q));
    }

    this.boitiersFiltres.set(res);
  }

  voirBoitier(b: Boitier): void {
    this.boitierSelectionne.set(b);
    this.modalBoitierOuverte.set(true);
  }

  fermerModal(): void {
    this.modalBoitierOuverte.set(false);
  }

  forcerSynchronisation(b: Boitier): void {
    this.notifService.succes('Synchronisation', `Le boîtier ${b.codeUnique} a été synchronisé.`);
    this.fermerModal();
  }

  exporterCSV(): void {
    const csvContent = "Nom,CodeUnique,Firmware,Batterie,Statut\n" +
      this.boitiers().map(b => `"${b.nom}","${b.codeUnique}","v${b.versionFirmware}",${b.niveauBatterie}%,"${this.getStatutLabel(b.statut)}"`).join("\n");

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `supervision_boitiers_alternia_${Date.now()}.csv`;
    link.click();

    this.notifService.succes('Export réussi', 'La liste des boîtiers a été exportée au format CSV.');
  }

  ouvrirModalAjout(): void {
    this.nouveauBoitierNom = '';
    this.nouveauBoitierCode = '';
    this.modalAjoutOuverte.set(true);
  }

  fermerModalAjout(): void {
    this.modalAjoutOuverte.set(false);
  }

  enregistrerBoitier(): void {
    if (!this.nouveauBoitierNom || !this.nouveauBoitierCode) {
      this.notifService.erreur('Erreur', 'Veuillez saisir le nom et le code du boîtier.');
      return;
    }

    this.boitierRepo.ajouterBoitier({
      nom: this.nouveauBoitierNom.trim(),
      codeUnique: this.nouveauBoitierCode.trim(),
      modele: 'Alternia Box v2.0-LocalEdge',
    }).subscribe({
      next: (nouveau) => {
        this.boitiers.update(list => [nouveau, ...list]);
        this.filtrer();
        this.notifService.succes('Boîtier enregistré', `Le boîtier ${this.nouveauBoitierNom} a été ajouté à la flotte.`);
        this.fermerModalAjout();
      },
      error: () => {
        this.notifService.erreur('Erreur', "Impossible d'enregistrer le boîtier sur le serveur.");
      }
    });
  }
}
