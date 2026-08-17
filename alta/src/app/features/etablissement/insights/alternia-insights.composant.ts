import { Component, OnInit, signal, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { InsightsRepository } from '../../../data/repositories/insights.repository';
import {
  QuestionFrequente,
  TendanceMatiere,
  NotionRenforcer,
  IndiceEngagement,
} from '../../../domain/entites/insights.entite';
import { Matiere, MatiereLabels, MatiereCouleurs } from '../../../core/enums';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-alternia-insights',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
<div class="page-content stagger-children">
  <!-- Page Header -->
  <div class="page-header">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
      <div>
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
          <span class="badge badge-innovation" style="font-size:12px;padding:4px 10px;">
            <span class="dot animate-pulse"></span> AlternIA AI Engine v2.4
          </span>
          <span class="text-xs text-secondary">Mise à jour en temps réel</span>
        </div>
        <h1 class="page-header__title">AlternIA Insights</h1>
        <p class="page-header__subtitle">Intelligence pédagogique & analyse prédictive anonymisée au niveau établissement</p>
      </div>
      <div style="display:flex;gap:10px;">
        <button class="btn btn-outline btn-sm" (click)="rafraichirInsights()" id="btn-refresh-insights">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" [class.animate-spin]="chargement()">
            <path d="M2 7C2 4.239 4.239 2 7 2C9.209 2 11.14 3.14 12.25 4.875" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            <path d="M12 7C12 9.761 9.761 12 7 12C4.791 12 2.86 10.86 1.75 9.125" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            <path d="M12 2V5H9" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12V9H5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Actualiser
        </button>
        <button class="btn btn-primary btn-sm" (click)="exporterInsights()" id="btn-export-insights">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M7 2V9M7 9L4 6M7 9L10 6" stroke="white" stroke-width="1.3" stroke-linecap="round"/>
            <path d="M2 12H12" stroke="white" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          Exporter l'analyse
        </button>
      </div>
    </div>
  </div>

  @if (chargement()) {
    <div class="kpi-grid">
      @for (i of [1,2,3,4]; track i) {
        <div class="skeleton" style="height:140px;border-radius:16px;"></div>
      }
    </div>
    <div class="skeleton" style="height:320px;border-radius:16px;margin-top:24px;"></div>
  } @else {

    <!-- Section Top 10 Questions Frequentes -->
    <div class="card" style="margin-top:24px;">
      <div class="card__header" style="flex-wrap:wrap;gap:12px;">
        <div>
          <h2 class="card__title">Top 10 des Questions les Plus Fréquentes</h2>
          <p class="text-xs text-secondary" style="margin-top:2px;">Données anonymisées et agrégées issues des interactions des apprenants avec l'IA Alternia</p>
        </div>

        <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
          <!-- Recherche -->
          <div class="search-input-wrapper" style="width:240px;">
            <input type="text" class="form-input text-xs" placeholder="Rechercher une question..." [(ngModel)]="rechercheQuestion" (input)="filtrerQuestions()"/>
          </div>

          <!-- Filtre Matière -->
          <select class="form-input text-xs" style="width:160px;" [(ngModel)]="matiereFiltre" (change)="filtrerQuestions()">
            <option value="toutes">Toutes les matières</option>
            @for (m of matieresList; track m) {
              <option [value]="m">{{ MatiereLabels[m] }}</option>
            }
          </select>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Question récurrente posée à l'IA</th>
              <th>Matière & Chapitre</th>
              <th style="text-align:center;">Occurrences</th>
              <th style="text-align:center;">Évolution</th>
              <th style="text-align:right;">Priorité pédagogique</th>
            </tr>
          </thead>
          <tbody>
            @for (q of questionsFiltrees(); track q.id; let idx = $index) {
              <tr>
                <td class="fw-bold text-secondary text-sm" style="width:40px;">{{ idx + 1 }}</td>
                <td>
                  <div class="fw-semibold text-sm" style="color:var(--color-text-primary);">"{{ q.question }}"</div>
                </td>
                <td>
                  <div style="display:flex;align-items:center;gap:6px;">
                    <span class="matiere-dot-sm" [style.background]="MatiereCouleurs[q.matiere]"></span>
                    <span class="text-xs fw-medium">{{ MatiereLabels[q.matiere] }}</span>
                    <span class="text-xs text-tertiary">· {{ q.chapitre }}</span>
                  </div>
                </td>
                <td style="text-align:center;">
                  <div style="display:flex;flex-direction:column;align-items:center;gap:4px;">
                    <span class="fw-bold text-sm">{{ q.nombreOccurrences }}</span>
                    <div class="progress-bar" style="width:80px;height:4px;">
                      <div class="progress-bar__fill" [style.width.%]="(q.nombreOccurrences / maxOccurrences()) * 100" [style.background]="MatiereCouleurs[q.matiere]"></div>
                    </div>
                  </div>
                </td>
                <td style="text-align:center;">
                  <span class="badge" [class.badge-success]="q.evolutionPct > 0" [class.badge-danger]="q.evolutionPct < 0">
                    {{ q.evolutionPct > 0 ? '+' : '' }}{{ q.evolutionPct }}%
                  </span>
                </td>
                <td style="text-align:right;">
                  <span class="badge" [class.badge-danger]="q.niveauPriorite === 'haute'" [class.badge-warning]="q.niveauPriorite === 'moyenne'" [class.badge-primary]="q.niveauPriorite === 'basse'">
                    {{ q.niveauPriorite === 'haute' ? 'Haute' : q.niveauPriorite === 'moyenne' ? 'Moyenne' : 'Standard' }}
                  </span>
                </td>
              </tr>
            } @empty {
              <tr><td colspan="6" style="text-align:center;padding:40px;color:var(--color-text-tertiary);">Aucune question trouvée pour ce critère</td></tr>
            }
          </tbody>
        </table>
      </div>
    </div>

    <!-- Section Notions à renforcer -->
    <div class="card" style="margin-top:24px;">
      <div class="card__header">
        <div>
          <h2 class="card__title">Notions à Renforcer Recommandées</h2>
          <p class="text-xs text-secondary" style="margin-top:2px;">Détectées automatiquement par l'IA d'après les difficultés récurrentes</p>
        </div>
        <span class="badge badge-warning">Action pédagogique ciblée</span>
      </div>
      <div class="card__body">
        <div class="notions-grid">
          @for (notion of notions(); track notion.id) {
            <div class="notion-item-card">
              <div class="notion-item-header">
                <div style="display:flex;align-items:center;gap:10px;">
                  <span class="matiere-badge-pill" [style.background]="MatiereCouleurs[notion.matiere] + '20'" [style.color]="MatiereCouleurs[notion.matiere]">
                    {{ MatiereLabels[notion.matiere] }}
                  </span>
                  <span class="text-xs text-secondary">{{ notion.chapitre }}</span>
                </div>
                <span class="badge" [class.badge-danger]="notion.priorite === 'haute'" [class.badge-warning]="notion.priorite === 'moyenne'">
                  Priorité {{ notion.priorite }}
                </span>
              </div>
              <h3 class="notion-item-title">{{ notion.notion }}</h3>
              <p class="notion-item-action"><strong>Recommandation IA :</strong> {{ notion.actionRecommandee }}</p>
              <div class="notion-item-footer">
                <span class="text-xs text-secondary">{{ notion.nombreRequetes }} questions générées</span>
                <button class="btn btn-outline btn-sm" (click)="programmerSessionRenforcement(notion)" [id]="'btn-notion-' + notion.id">
                  Programmer session
                </button>
              </div>
            </div>
          }
        </div>
      </div>
    </div>

  }
</div>
  `,
  styles: [`
    .insights-hero-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 24px; @media(max-width:992px){ grid-template-columns: 1fr; } }
    .engagement-hero-card { background: var(--color-bg-surface); border: 1px solid var(--color-border); }
    .gauge-container { position: relative; width: 120px; height: 120px; flex-shrink: 0; }
    .gauge-svg { width: 100%; height: 100%; }
    .gauge-text { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: var(--font-display); }
    .gauge-val { font-size: 28px; font-weight: 800; color: var(--color-text-primary); line-height: 1; }
    .gauge-max { font-size: 11px; color: var(--color-text-tertiary); margin-top: 2px; }
    .composantes-grid { display: flex; flex-direction: column; gap: 8px; margin-top: 4px; }
    .comp-item { display: flex; align-items: center; gap: 10px; font-size: 12px; }
    .comp-label { width: 140px; color: var(--color-text-secondary); flex-shrink: 0; }
    .comp-item .progress-bar { flex: 1; height: 6px; }
    .comp-val { width: 36px; text-align: right; font-weight: 600; color: var(--color-text-primary); }
    .live-panel-card { background: var(--color-bg-surface); }
    .live-metric { display: flex; align-items: center; gap: 12px; padding: 10px 12px; background: var(--color-bg-surface-2); border-radius: var(--radius-md); border: 1px solid var(--color-border); }
    .tendances-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
    .tendance-card { background: var(--color-bg-surface-2); border: 1px solid var(--color-border); border-top: 4px solid; border-radius: var(--radius-md); padding: 14px; display: flex; flex-direction: column; gap: 10px; }
    .tendance-card__header { display: flex; justify-content: space-between; align-items: flex-start; }
    .sparkline-container { padding: 4px 0; }
    .tendance-card__footer { font-size: 11px; border-top: 1px dashed var(--color-border); padding-top: 8px; }
    .matiere-badge-pill { padding: 2px 8px; border-radius: var(--radius-full); font-size: 11px; font-weight: 600; }
    .notions-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
    .notion-item-card { background: var(--color-bg-surface-2); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 18px; display: flex; flex-direction: column; gap: 10px; }
    .notion-item-header { display: flex; justify-content: space-between; align-items: center; }
    .notion-item-title { font-size: 15px; font-weight: 700; color: var(--color-text-primary); margin: 2px 0; }
    .notion-item-action { font-size: 13px; color: var(--color-text-secondary); background: var(--color-bg-surface); padding: 10px; border-radius: var(--radius-md); border: 1px solid var(--color-border); line-height: 1.4; }
    .notion-item-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
  `],
})
export class AlternIAInsightsComposant implements OnInit {
  private readonly repo = inject(InsightsRepository);
  private readonly notifService = inject(NotificationService);

  readonly MatiereLabels = MatiereLabels;
  readonly MatiereCouleurs = MatiereCouleurs;
  readonly matieresList = Object.values(Matiere);

  chargement = signal(true);
  engagement = signal<IndiceEngagement | null>(null);
  tendances = signal<TendanceMatiere[]>([]);
  questions = signal<QuestionFrequente[]>([]);
  questionsFiltrees = signal<QuestionFrequente[]>([]);
  notions = signal<NotionRenforcer[]>([]);

  rechercheQuestion = '';
  matiereFiltre = 'toutes';

  readonly maxOccurrences = computed(() => {
    const list = this.questions();
    return list.length ? Math.max(...list.map(q => q.nombreOccurrences)) : 100;
  });

  ngOnInit(): void {
    this.chargerDonnees();
  }

  chargerDonnees(): void {
    this.chargement.set(true);
    Promise.all([
      new Promise<void>(resolve => this.repo.obtenirIndiceEngagement().subscribe(e => { this.engagement.set(e); resolve(); })),
      new Promise<void>(resolve => this.repo.obtenirTendancesMatieres().subscribe(t => { this.tendances.set(t); resolve(); })),
      new Promise<void>(resolve => this.repo.obtenirQuestionsFrequentes().subscribe(q => { this.questions.set(q); this.questionsFiltrees.set(q); resolve(); })),
      new Promise<void>(resolve => this.repo.obtenirNotionsRenforcer().subscribe(n => { this.notions.set(n); resolve(); })),
    ]).then(() => this.chargement.set(false));
  }

  filtrerQuestions(): void {
    let list = this.questions();
    if (this.matiereFiltre !== 'toutes') {
      list = list.filter(q => q.matiere === this.matiereFiltre);
    }
    if (this.rechercheQuestion) {
      const term = this.rechercheQuestion.toLowerCase();
      list = list.filter(q => q.question.toLowerCase().includes(term) || q.chapitre.toLowerCase().includes(term));
    }
    this.questionsFiltrees.set(list);
  }

  generateSparklinePath(points: number[]): string {
    if (!points || !points.length) return '';
    const max = Math.max(...points), min = Math.min(...points);
    const pts = points.map((v, i) => {
      const x = (i / (points.length - 1)) * 160;
      const y = 35 - (((v - min) / (max - min || 1)) * 28);
      return `${x},${y}`;
    });
    return 'M' + pts.join(' L');
  }

  rafraichirInsights(): void {
    this.chargerDonnees();
    this.notifService.succes('Insights actualisés', 'Les prédictions IA ont été recalculées en direct.');
  }

  exporterInsights(): void {
    this.notifService.succes('Exportation réussie', 'Le rapport complet AlternIA Insights a été exporté.');
  }

  programmerSessionRenforcement(notion: NotionRenforcer): void {
    this.notifService.succes('Session programmée', `Session de renforcement programmée pour "${notion.notion}".`);
  }
}
