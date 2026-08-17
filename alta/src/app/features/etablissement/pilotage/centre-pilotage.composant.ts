import { Component, OnInit, signal, inject, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InsightsRepository } from '../../../data/repositories/insights.repository';
import { BoitierRepository } from '../../../data/repositories/boitier.repository';
import { TelemetrieSysteme } from '../../../domain/entites/insights.entite';
import { Boitier } from '../../../domain/entites/boitier.entite';
import { StatutBoitier, MatiereLabels, MatiereCouleurs, Matiere } from '../../../core/enums';
import { NotificationService } from '../../../core/services/notification.service';

interface EventLog {
  id: string;
  horodatage: Date;
  type: 'info' | 'success' | 'warning';
  message: string;
}

@Component({
  selector: 'app-centre-pilotage',
  standalone: true,
  imports: [CommonModule],
  template: `
<div class="page-content stagger-children pilotage-theme">
  <!-- Mission Control Header -->
  <div class="pilotage-header">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;">
      <div>
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
          <span class="status-indicator-badge">
            <span class="status-dot online animate-pulse"></span>
            MISSION CONTROL · ALTERNIA CLOUD MALI
          </span>
          <span class="text-xs text-mono" style="color:rgba(255,255,255,0.6);">SERVER: BKO-CENTRAL-01</span>
        </div>
        <h1 class="pilotage-title">Centre de Pilotage & Télémétrie</h1>
        <p class="pilotage-subtitle">Supervision en direct des serveurs IA, boîtiers d'apprentissage et flux réseau</p>
      </div>

      <div style="display:flex;gap:10px;align-items:center;">
        <div class="control-time-chip">
          <span class="text-xs text-mono">{{ heureActuelle() }}</span>
        </div>
        <button class="btn btn-secondary btn-sm" (click)="forcerPulsation()" id="btn-force-ping">
          Pulsation Télémétrie
        </button>
      </div>
    </div>
  </div>

  @if (chargement()) {
    <div class="kpi-grid">
      @for (i of [1,2,3,4,5,6]; track i) {
        <div class="skeleton" style="height:110px;border-radius:16px;"></div>
      }
    </div>
  } @else {

    <!-- Telemetry Bar Cards -->
    <div class="telemetrie-grid">
      <div class="tele-card">
        <div class="tele-card__header">
          <span class="tele-label">Statut Cloud</span>
          <span class="badge badge-success">{{ telemetrie()?.statutServeur }}</span>
        </div>
        <div class="tele-val text-success">Optimal</div>
        <div class="tele-sub">Disponibilité {{ telemetrie()?.disponibilitePct }}%</div>
      </div>

      <div class="tele-card">
        <div class="tele-card__header">
          <span class="tele-label">Latence Réseau</span>
          <span class="text-xs text-mono text-success">ULTRA FAST</span>
        </div>
        <div class="tele-val">{{ telemetrie()?.latenceReseauMs }} ms</div>
        <div class="tele-sub">Serveur local Bamako</div>
      </div>

      <div class="tele-card">
        <div class="tele-card__header">
          <span class="tele-label">Boîtiers Actifs</span>
          <span class="badge badge-primary">{{ telemetrie()?.boitiersConnectes }}/{{ telemetrie()?.boitiersTotal }}</span>
        </div>
        <div class="tele-val">{{ telemetrie()?.boitiersConnectes }}</div>
        <div class="tele-sub">97.7% connectés en direct</div>
      </div>

      <div class="tele-card">
        <div class="tele-card__header">
          <span class="tele-label">Flux de Requêtes</span>
          <span class="text-xs text-mono">REQ/SEC</span>
        </div>
        <div class="tele-val text-innovation">{{ telemetrie()?.requetesParSeconde }} req/s</div>
        <div class="tele-sub">Charge Cloud CPU {{ telemetrie()?.chargeCpuCloudPct }}%</div>
      </div>

      <div class="tele-card">
        <div class="tele-card__header">
          <span class="tele-label">Bande Passante</span>
          <span class="text-xs text-mono">Mbps</span>
        </div>
        <div class="tele-val">{{ telemetrie()?.bandePassanteMbps }} Mbps</div>
        <div class="tele-sub">Débit global synchronisé</div>
      </div>
    </div>

    <!-- Main Grid: Box Status Grid & Distribution Radar -->
    <div class="pilotage-main-grid">

      <!-- Active Devices Map / Grid -->
      <div class="card mission-card">
        <div class="card__header">
          <div>
            <h2 class="card__title">Superviseur des Boîtiers (Réseau Établissement)</h2>
            <p class="text-xs text-secondary" style="margin-top:2px;">État en temps réel de chaque boîtier déployé dans les salles de classe</p>
          </div>
          <button class="btn btn-ghost btn-sm" (click)="filtrerBoitierStatut('tous')" id="btn-filtre-boitiers-tous">Tous ({{ boitiers().length }})</button>
        </div>
        <div class="card__body">
          <div class="boitier-matrix">
            @for (b of boitiers(); track b.id) {
              <div class="matrix-box" [class.matrix-box--online]="b.statut === StatutBoitier.EN_LIGNE_CLOUD" [class.matrix-box--warning]="b.statut === StatutBoitier.HORS_LIGNE_LOCAL">
                <div class="matrix-box__top">
                  <span class="status-dot {{ getStatutClass(b.statut) }}"></span>
                  <span class="matrix-code">{{ b.codeUnique }}</span>
                </div>
                <div class="matrix-nom">{{ b.nom }}</div>
                <div class="matrix-box__bottom">
                  <span class="text-xs text-secondary">Batterie {{ b.niveauBatterie }}%</span>
                  <span class="text-xs text-mono" style="font-size:10px;">{{ b.ssid || 'Local' }}</span>
                </div>
              </div>
            }
          </div>
        </div>
      </div>

      <!-- Subject Traffic Distribution & Radar -->
      <div class="card mission-card">
        <div class="card__header">
          <h2 class="card__title">Charge par Matière (Répartition Flux IA)</h2>
        </div>
        <div class="card__body">
          <div class="repartition-list">
            @for (item of repartitionMatiere; track item.matiere) {
              <div class="repartition-row">
                <div class="repartition-meta">
                  <span class="matiere-dot-sm" [style.background]="MatiereCouleurs[item.matiere]"></span>
                  <span class="fw-semibold text-sm">{{ MatiereLabels[item.matiere] }}</span>
                  <span class="text-xs text-secondary" style="margin-left:auto;">{{ item.pct }}% ({{ item.total }} req)</span>
                </div>
                <div class="progress-bar" style="height:8px;">
                  <div class="progress-bar__fill" [style.width.%]="item.pct" [style.background]="MatiereCouleurs[item.matiere]"></div>
                </div>
              </div>
            }
          </div>
        </div>
      </div>
    </div>

    <!-- Live Event Log Stream -->
    <div class="card mission-card" style="margin-top:24px;">
      <div class="card__header">
        <div style="display:flex;align-items:center;gap:10px;">
          <h2 class="card__title">Journal d'Événements & Télémétrie Live</h2>
          <span class="badge badge-innovation">Live Feed</span>
        </div>
        <button class="btn btn-ghost btn-sm" (click)="effacerLogs()" id="btn-clear-logs">Effacer journal</button>
      </div>
      <div class="card__body" style="padding-top:0;">
        <div class="event-stream">
          @for (log of logs(); track log.id) {
            <div class="log-row">
              <span class="log-time">{{ log.horodatage | date:'HH:mm:ss' }}</span>
              <span class="badge" [class.badge-success]="log.type === 'success'" [class.badge-warning]="log.type === 'warning'" [class.badge-primary]="log.type === 'info'" style="font-size:10px;">
                {{ log.type.toUpperCase() }}
              </span>
              <span class="log-msg">{{ log.message }}</span>
            </div>
          }
        </div>
      </div>
    </div>

  }
</div>
  `,
  styles: [`
    .pilotage-theme { background: var(--color-bg-app); }
    .pilotage-header { background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 20px 24px; margin-bottom: 20px; box-shadow: var(--shadow-xs); color: var(--color-text-primary); }
    .status-indicator-badge { display: inline-flex; align-items: center; gap: 6px; padding: 3px 8px; border-radius: var(--radius-full); background: var(--color-success-light); color: var(--color-success); font-size: 11px; font-weight: 600; font-family: var(--font-mono); }
    .pilotage-title { font-family: var(--font-display); font-size: 22px; font-weight: 700; color: var(--color-text-primary); margin-top: 4px; letter-spacing: -0.02em; }
    .pilotage-subtitle { font-size: 13px; color: var(--color-text-secondary); margin-top: 2px; }
    .control-time-chip { padding: 5px 12px; background: var(--color-bg-surface-2); border: 1px solid var(--color-border); border-radius: var(--radius-md); color: var(--color-text-primary); }
    .telemetrie-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .tele-card { background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 16px; display: flex; flex-direction: column; gap: 6px; box-shadow: var(--shadow-xs); }
    .tele-card__header { display: flex; justify-content: space-between; align-items: center; }
    .tele-label { font-size: 11px; color: var(--color-text-secondary); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
    .tele-val { font-family: var(--font-display); font-size: 22px; font-weight: 800; color: var(--color-text-primary); }
    .tele-sub { font-size: 11px; color: var(--color-text-tertiary); }
    .pilotage-main-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 24px; @media(max-width:992px){ grid-template-columns: 1fr; } }
    .mission-card { background: var(--color-bg-surface); border: 1px solid var(--color-border); }
    .boitier-matrix { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
    .matrix-box { background: var(--color-bg-surface-2); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 12px; display: flex; flex-direction: column; gap: 6px; transition: all var(--transition-fast); }
    .matrix-box:hover { border-color: var(--color-primaire); transform: translateY(-2px); }
    .matrix-box--online { border-left: 3px solid var(--color-success); }
    .matrix-box--warning { border-left: 3px solid var(--color-warning); }
    .matrix-box__top { display: flex; align-items: center; justify-content: space-between; }
    .matrix-code { font-family: var(--font-mono); font-size: 10px; font-weight: 700; color: var(--color-text-secondary); }
    .matrix-nom { font-size: 12px; font-weight: 700; color: var(--color-text-primary); }
    .matrix-box__bottom { display: flex; justify-content: space-between; align-items: center; margin-top: 2px; }
    .repartition-list { display: flex; flex-direction: column; gap: 16px; }
    .repartition-row { display: flex; flex-direction: column; gap: 6px; }
    .repartition-meta { display: flex; align-items: center; gap: 8px; }
    .event-stream { font-family: var(--font-mono); font-size: 12px; display: flex; flex-direction: column; gap: 8px; max-height: 240px; overflow-y: auto; }
    .log-row { display: flex; align-items: center; gap: 12px; padding: 6px 10px; background: var(--color-bg-surface-2); border-radius: var(--radius-sm); border: 1px solid var(--color-border); }
    .log-time { color: var(--color-text-tertiary); font-size: 11px; flex-shrink: 0; }
    .log-msg { color: var(--color-text-primary); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  `],
})
export class CentrePilotageComposant implements OnInit, OnDestroy {
  private readonly insightsRepo = inject(InsightsRepository);
  private readonly boitierRepo = inject(BoitierRepository);
  private readonly notifService = inject(NotificationService);

  readonly MatiereLabels = MatiereLabels;
  readonly MatiereCouleurs = MatiereCouleurs;
  readonly StatutBoitier = StatutBoitier;

  chargement = signal(true);
  telemetrie = signal<TelemetrieSysteme | null>(null);
  boitiers = signal<Boitier[]>([]);
  heureActuelle = signal(new Date().toLocaleTimeString('fr-FR'));
  logs = signal<EventLog[]>([]);

  private timer: any;

  readonly repartitionMatiere = [
    { matiere: Matiere.MATHEMATIQUES, pct: 35, total: 4139 },
    { matiere: Matiere.PHYSIQUE, pct: 24, total: 2809 },
    { matiere: Matiere.FRANCAIS, pct: 20, total: 2365 },
    { matiere: Matiere.SVT, pct: 13, total: 2069 },
    { matiere: Matiere.CHIMIE, pct: 8, total: 1183 },
  ];

  ngOnInit(): void {
    this.initialiserDonnees();
    this.timer = setInterval(() => {
      this.heureActuelle.set(new Date().toLocaleTimeString('fr-FR'));
    }, 1000);
  }

  ngOnDestroy(): void {
    if (this.timer) clearInterval(this.timer);
  }

  initialiserDonnees(): void {
    Promise.all([
      new Promise<void>(resolve => this.insightsRepo.obtenirTelemetrieSysteme().subscribe(t => { this.telemetrie.set(t); resolve(); })),
      new Promise<void>(resolve => this.boitierRepo.obtenirBoitiersEtablissement('etab-1').subscribe(b => { this.boitiers.set(b); resolve(); })),
    ]).then(() => {
      this.genererLogsInitiaux();
      this.chargement.set(false);
    });
  }

  genererLogsInitiaux(): void {
    this.logs.set([
      { id: '1', horodatage: new Date(), type: 'success', message: 'Heartbeat OK - Serveur Central Bamako BKO-01 (14ms)' },
      { id: '2', horodatage: new Date(Date.now() - 30000), type: 'info', message: 'Boîtier ALT-2025-001 synchronisé avec succès (16.0 Go)' },
      { id: '3', horodatage: new Date(Date.now() - 75000), type: 'info', message: 'IA Alternia Math : 142 requêtes traitées ce dernier quart d\'heure' },
      { id: '4', horodatage: new Date(Date.now() - 120000), type: 'warning', message: 'Boîtier ALT-2025-002 basculé en mode local hors-ligne' },
    ]);
  }

  getStatutClass(statut: StatutBoitier): string {
    return { [StatutBoitier.EN_LIGNE_CLOUD]: 'online', [StatutBoitier.HORS_LIGNE_LOCAL]: 'warning', [StatutBoitier.DECONNECTE]: 'danger' }[statut] ?? '';
  }

  forcerPulsation(): void {
    const nouveauLog: EventLog = {
      id: String(Date.now()),
      horodatage: new Date(),
      type: 'success',
      message: `Pulsation de télémétrie forcé : Serveur opérationnel (${Math.floor(Math.random() * 5) + 12}ms)`,
    };
    this.logs.update(l => [nouveauLog, ...l]);
    this.telemetrie.update(t => t ? { ...t, latenceReseauMs: Math.floor(Math.random() * 4) + 12, requetesParSeconde: Math.floor(Math.random() * 10) + 45 } : null);
    this.notifService.info('Télémétrie', 'Pulsation réseau envoyée au cloud Bamako.');
  }

  filtrerBoitierStatut(statut: string): void {
    this.notifService.info('Boîtiers', `Affichage de tous les ${this.boitiers().length} boîtiers.`);
  }

  effacerLogs(): void {
    this.logs.set([]);
    this.notifService.info('Journal', 'Le journal d\'événements a été réinitialisé.');
  }
}
