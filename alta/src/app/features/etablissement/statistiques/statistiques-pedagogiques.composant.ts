import { Component, OnInit, signal, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { StatistiquesRepository } from '../../../data/repositories/statistiques.repository';
import { NotionDifficile, StatistiquesUtilisation } from '../../../domain/entites/statistiques-utilisation.entite';
import { MatiereLabels, MatiereCouleurs, Matiere } from '../../../core/enums';
import { NotificationService } from '../../../core/services/notification.service';

type PeriodeFiltre = 'jour' | 'semaine' | 'mois' | 'trimestre';

@Component({
  selector: 'app-statistiques-pedagogiques',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
<div class="page-content stagger-children">
  
  <!-- En-tête de page standardisé -->
  <div class="page-header">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
      <div>
        <h1 class="page-header__title">Statistiques Pédagogiques</h1>
        <p class="page-header__subtitle">Analytique d'apprentissage en temps réel · 342 boîtiers connectés</p>
      </div>
      <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
        <!-- Sélecteur de période -->
        <div class="periode-switcher">
          <button class="periode-btn" [class.periode-btn--active]="periodeActive() === 'jour'" (click)="changerPeriode('jour')">Aujourd'hui</button>
          <button class="periode-btn" [class.periode-btn--active]="periodeActive() === 'semaine'" (click)="changerPeriode('semaine')">7 Jours</button>
          <button class="periode-btn" [class.periode-btn--active]="periodeActive() === 'mois'" (click)="changerPeriode('mois')">Mois</button>
          <button class="periode-btn" [class.periode-btn--active]="periodeActive() === 'trimestre'" (click)="changerPeriode('trimestre')">Trimestre</button>
        </div>

        <button class="btn btn-outline btn-sm" (click)="rafraichirDonnees()" id="btn-refresh-stats">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" [class.animate-spin]="chargement()">
            <path d="M2 7C2 4.239 4.239 2 7 2C9.209 2 11.14 3.14 12.25 4.875" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            <path d="M12 7C12 9.761 9.761 12 7 12C4.791 12 2.86 10.86 1.75 9.125" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            <path d="M12 2V5H9" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12V9H5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Actualiser
        </button>

        <button class="btn btn-primary btn-sm" (click)="exporterRapport()" id="btn-export-stats">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M7 2V9M7 9L4 6M7 9L10 6" stroke="white" stroke-width="1.3" stroke-linecap="round"/>
            <path d="M2 12H12" stroke="white" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          Exporter le bilan
        </button>
      </div>
    </div>
  </div>

  @if (chargement()) {
    <div class="kpi-grid">
      @for (i of [1,2,3,4]; track i) {
        <div class="skeleton" style="height:120px;border-radius:14px;"></div>
      }
    </div>
    <div class="skeleton" style="height:320px;border-radius:14px;margin-top:20px;"></div>
  } @else {

    <!-- KPI Deck -->
    <div class="kpi-grid">
      <div class="card stat-card">
        <div class="stat-card__header">
          <span class="stat-card__label">Questions Posées à l'IA</span>
          <div class="icon-box icon-box-sm icon-box-primary">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
        </div>
        <div class="stat-card__val">{{ (stats()?.totalQuestionsIA || 14782).toLocaleString('fr-FR') }}</div>
        <div class="stat-card__footer">
          <span class="badge badge-success">+18.4%</span>
          <span class="text-xs text-secondary">vs période précédente</span>
        </div>
      </div>

      <div class="card stat-card">
        <div class="stat-card__header">
          <span class="stat-card__label">Temps d'Étude Cumulé</span>
          <div class="icon-box icon-box-sm icon-box-secondaire">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
        </div>
        <div class="stat-card__val">{{ heuresApprentissage() }}h {{ minutesRestantes() }}m</div>
        <div class="stat-card__footer">
          <span class="badge badge-success">+12.6%</span>
          <span class="text-xs text-secondary">Moy. ~4h20 / apprenant</span>
        </div>
      </div>

      <div class="card stat-card">
        <div class="stat-card__header">
          <span class="stat-card__label">Apprenants Actifs</span>
          <div class="icon-box icon-box-sm icon-box-innovation">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            </svg>
          </div>
        </div>
        <div class="stat-card__val">{{ stats()?.apprenantActifs || 342 }} <span class="text-sm text-secondary">/ 350</span></div>
        <div class="stat-card__footer">
          <span class="badge badge-primary">97.7%</span>
          <span class="text-xs text-secondary">Taux d'assiduité élevé</span>
        </div>
      </div>

      <div class="card stat-card">
        <div class="stat-card__header">
          <span class="stat-card__label">Taux d'Engagement</span>
          <div class="icon-box icon-box-sm icon-box-success">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          </div>
        </div>
        <div class="stat-card__val">{{ stats()?.tauxEngagement || 78 }}%</div>
        <div class="stat-card__footer">
          <span class="badge badge-success">Optimal</span>
          <span class="text-xs text-secondary">Qualité des sessions</span>
        </div>
      </div>
    </div>

    <!-- Grille des graphiques -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px;" class="charts-grid-resp">
      
      <!-- Pics d'utilisation journaliers -->
      <div class="card">
        <div class="card__header">
          <div>
            <h2 class="card__title">Pics d'Utilisation Journaliers</h2>
            <p class="text-xs text-secondary" style="margin-top:2px;">Volume de sessions par heure (07h à 21h)</p>
          </div>
          <span class="badge badge-secondaire">Pic : 16h (520 sessions)</span>
        </div>
        <div class="card__body">
          <div class="histogram-wrapper">
            <div class="histogram-bars">
              @for (pic of stats()?.pictUtilisation; track pic.heure) {
                <div class="histo-bar-item" (mouseenter)="barSurvolee.set(pic)" (mouseleave)="barSurvolee.set(null)">
                  <div class="histo-bar-track">
                    <div class="histo-bar-fill" [class.is-peak]="pic.nombreSessions === maxPic()" [style.height.%]="(pic.nombreSessions / maxPic()) * 100">
                      @if (pic.nombreSessions === maxPic() || barSurvolee()?.heure === pic.heure) {
                        <div class="histo-popover">{{ pic.nombreSessions }}</div>
                      }
                    </div>
                  </div>
                  <span class="histo-label" [class.is-peak-label]="pic.nombreSessions === maxPic()">{{ pic.heure }}h</span>
                </div>
              }
            </div>
          </div>
        </div>
      </div>

      <!-- Répartition par matière -->
      <div class="card">
        <div class="card__header">
          <div>
            <h2 class="card__title">Répartition par Matière</h2>
            <p class="text-xs text-secondary" style="margin-top:2px;">Volume de questions et temps passé</p>
          </div>
          <span class="badge badge-primary">7 matières</span>
        </div>
        <div class="card__body">
          <div class="matieres-list">
            @for (m of stats()?.matieresPlusUtilisees; track m.matiere; let idx = $index) {
              <div class="matiere-item">
                <div class="matiere-item__header">
                  <div style="display:flex;align-items:center;gap:8px;">
                    <span class="matiere-dot" [style.background]="getCouleurMatiere(m.matiere)"></span>
                    <span class="fw-medium text-sm">{{ getLibelleMatiere(m.matiere) }}</span>
                  </div>
                  <div class="text-xs text-secondary">
                    <span class="fw-semibold text-primary">{{ m.pourcentage }}%</span> ({{ m.totalQuestions }} q.)
                  </div>
                </div>
                <div class="progress-bar" style="height:6px;margin-top:6px;">
                  <div class="progress-bar__fill" [style.width.%]="m.pourcentage" [style.background]="getCouleurMatiere(m.matiere)"></div>
                </div>
              </div>
            }
          </div>
        </div>
      </div>

    </div>

    <!-- Tableau : Notions nécessitant un renforcement -->
    <div class="card">
      <div class="card__header">
        <div>
          <h2 class="card__title">Notions Complexes Détectées par l'IA</h2>
          <p class="text-xs text-secondary" style="margin-top:2px;">Notions générant le plus d'incompréhensions ou d'hésitations</p>
        </div>
        <span class="badge badge-warning">{{ notionsDifficiles().length }} notions à renforcer</span>
      </div>
      <div class="table-wrapper">
        <table class="table">
          <thead>
            <tr>
              <th>Notion & Matière</th>
              <th>Matière</th>
              <th>Volume de questions</th>
              <th>Élèves concernés</th>
              <th>Taux d'échec</th>
              <th>Statut Remédiation</th>
              <th style="text-align:right;">Actions</th>
            </tr>
          </thead>
          <tbody>
            @for (n of notionsDifficiles(); track n.notion) {
              <tr>
                <td>
                  <div class="fw-semibold text-sm">{{ n.notion }}</div>
                </td>
                <td>
                  <span class="badge" [style.background]="getCouleurMatiere(n.matiere) + '18'" [style.color]="getCouleurMatiere(n.matiere)">
                    {{ getLibelleMatiere(n.matiere) }}
                  </span>
                </td>
                <td class="text-sm fw-medium">{{ n.nombreTentatives.toLocaleString('fr-FR') }}</td>
                <td class="text-sm text-secondary">{{ n.apprenantsConcernes }} apprenants</td>
                <td>
                  <div style="display:flex;align-items:center;gap:6px;">
                    <div class="progress-bar" style="width:50px;height:5px;">
                      <div class="progress-bar__fill danger" [style.width.%]="n.tauxEchec"></div>
                    </div>
                    <span class="text-xs fw-semibold text-danger">{{ n.tauxEchec }}%</span>
                  </div>
                </td>
                <td>
                  <span class="badge" [class.badge-warning]="!n.remediationProposee" [class.badge-success]="n.remediationProposee">
                    <span class="dot"></span>
                    {{ n.remediationProposee ? 'Fiche IA Active' : 'À planifier' }}
                  </span>
                </td>
                <td style="text-align:right;">
                  <button class="btn btn-ghost btn-sm" (click)="programmerRemediation(n)" [id]="'btn-remedier-' + n.notion">
                    Planifier fiche IA →
                  </button>
                </td>
              </tr>
            } @empty {
              <tr>
                <td colspan="7" style="text-align:center;padding:32px;color:var(--color-text-tertiary);">
                  Aucune notion critique identifiée pour cette période.
                </td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    </div>

  }
</div>
  `,
  styles: [`
    .periode-switcher { display: flex; background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 2px; }
    .periode-btn { padding: 5px 12px; font-size: var(--text-xs); font-weight: var(--fw-medium); color: var(--color-text-secondary); border-radius: var(--radius-sm); transition: all var(--transition-fast); }
    .periode-btn:hover { color: var(--color-text-primary); }
    .periode-btn--active { background: var(--color-primaire); color: #fff !important; font-weight: var(--fw-semibold); }
    
    .stat-card { padding: 18px 20px; }
    .stat-card__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .stat-card__label { font-size: var(--text-xs); font-weight: var(--fw-medium); color: var(--color-text-secondary); text-transform: uppercase; letter-spacing: 0.04em; }
    .stat-card__val { font-family: var(--font-display); font-size: var(--text-2xl); font-weight: var(--fw-bold); color: var(--color-text-primary); margin-bottom: 8px; }
    .stat-card__footer { display: flex; align-items: center; gap: 8px; }

    .histogram-wrapper { height: 180px; display: flex; align-items: flex-end; padding-top: 24px; }
    .histogram-bars { display: flex; width: 100%; height: 100%; gap: 6px; align-items: flex-end; }
    .histo-bar-item { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; }
    .histo-bar-track { width: 100%; height: calc(100% - 22px); display: flex; align-items: flex-end; justify-content: center; }
    .histo-bar-fill { width: 100%; max-width: 28px; background: var(--color-primaire); border-radius: 4px 4px 0 0; position: relative; transition: height 0.4s ease, background 0.2s ease; cursor: pointer; }
    .histo-bar-fill:hover { background: var(--color-primaire-hover); }
    .histo-bar-fill.is-peak { background: var(--color-secondaire); }
    .histo-popover { position: absolute; top: -24px; left: 50%; transform: translateX(-50%); background: var(--color-text-primary); color: var(--color-text-inverse); font-size: 10px; font-weight: var(--fw-bold); padding: 2px 6px; border-radius: 4px; white-space: nowrap; }
    .histo-label { font-size: 10px; color: var(--color-text-tertiary); margin-top: 6px; }
    .is-peak-label { color: var(--color-secondaire); font-weight: var(--fw-bold); }

    .matieres-list { display: flex; flex-direction: column; gap: 14px; }
    .matiere-item__header { display: flex; justify-content: space-between; align-items: center; }
    .matiere-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

    @media (max-width: 900px) {
      .charts-grid-resp { grid-template-columns: 1fr !important; }
    }
  `],
})
export class StatistiquesPedagogiquesComposant implements OnInit {
  private readonly repo = inject(StatistiquesRepository);
  private readonly notifService = inject(NotificationService);

  readonly MatiereLabels = MatiereLabels;
  readonly MatiereCouleurs = MatiereCouleurs;

  chargement = signal(true);
  stats = signal<StatistiquesUtilisation | null>(null);
  notionsDifficiles = signal<NotionDifficile[]>([]);
  periodeActive = signal<PeriodeFiltre>('semaine');
  barSurvolee = signal<any>(null);

  readonly maxPic = computed(() => {
    const list = this.stats()?.pictUtilisation || [];
    if (!list.length) return 520;
    return Math.max(...list.map(p => p.nombreSessions), 1);
  });

  readonly heuresApprentissage = computed(() => {
    const totalMin = this.stats()?.tempsTotal || 900;
    return Math.floor(totalMin / 60);
  });

  readonly minutesRestantes = computed(() => {
    const totalMin = this.stats()?.tempsTotal || 900;
    return totalMin % 60;
  });

  ngOnInit(): void {
    this.chargerDonnees();
  }

  getLibelleMatiere(matiere: Matiere): string {
    return MatiereLabels[matiere] ?? matiere;
  }

  getCouleurMatiere(matiere: Matiere): string {
    return MatiereCouleurs[matiere] ?? '#314999';
  }

  chargerDonnees(): void {
    this.chargement.set(true);
    forkJoin({
      stats: this.repo.obtenirStatistiques('etab-1'),
      notions: this.repo.obtenirNotionsDifficiles('etab-1'),
    }).subscribe({
      next: ({ stats, notions }) => {
        this.stats.set(stats);
        this.notionsDifficiles.set(notions);
        this.chargement.set(false);
      },
      error: () => {
        this.chargement.set(false);
      }
    });
  }

  changerPeriode(p: PeriodeFiltre): void {
    this.periodeActive.set(p);
    this.chargerDonnees();
  }

  rafraichirDonnees(): void {
    this.chargerDonnees();
    this.notifService.info('Données actualisées', 'Les statistiques pédagogiques ont été synchronisées.');
  }

  exporterRapport(): void {
    this.notifService.succes('Exportation', 'Le bilan des statistiques a été généré avec succès.');
  }

  programmerRemediation(notion: NotionDifficile): void {
    this.notifService.succes('Fiche de remédiation', `Fiche IA planifiée pour : ${notion.notion}`);
  }
}
