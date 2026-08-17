import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Matiere, MatiereLabels, MatiereCouleurs } from '../../../core/enums';
import { ROUTES_APP } from '../../../core/constantes/routes.constantes';

interface TendanceBoitierMatiere {
  matiere: Matiere;
  partTempsPct: number;
  variation: number;
  courbe: number[];
  notionsMaitrisees: string[];
  notionsRecurrentes: string[];
  tempsMinutesTotal: number;
}

@Component({
  selector: 'app-progression-enfant',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
<div class="page-content stagger-children">
  <div class="page-header" style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
    <div>
      <h1 class="page-header__title">Matières Consultées</h1>
      <p class="page-header__subtitle">Analyse détaillée du volume d'apprentissage et des questions par matière sur le boîtier</p>
    </div>
    <a [routerLink]="routes.PARENT.HISTORIQUE" class="btn btn-secondaire btn-sm" id="btn-ouvrir-historique-parent">
      Voir l'historique des sessions →
    </a>
  </div>

  <!-- Score global d'utilisation -->
  <div class="global-score-card">
    <div class="global-score-left">
      <div class="global-score-ring">
        <svg viewBox="0 0 120 120" class="score-svg">
          <circle cx="60" cy="60" r="52" fill="none" stroke="var(--color-bg-surface-2)" stroke-width="8"/>
          <circle cx="60" cy="60" r="52" fill="none" stroke="var(--color-secondaire)" stroke-width="8"
            [style.stroke-dasharray]="(74 / 100) * 327 + ' 327'"
            stroke-linecap="round"
            transform="rotate(-90 60 60)"
            style="transition: stroke-dasharray 1s ease;"/>
        </svg>
        <div class="global-score-value">74%</div>
      </div>
      <div>
        <div class="fw-bold text-xl" style="color:var(--color-text-primary);">Taux d'activité du dispositif</div>
        <div class="text-sm text-secondary" style="margin-top:4px;">Calculé d'après les sessions enregistrées ce mois</div>
        <div class="text-xs" style="margin-top:8px;color:var(--color-success);font-weight:600;">↑ +6% d'activité vs mois dernier</div>
      </div>
    </div>
    <div class="global-score-right">
      <div class="global-stat"><span class="global-stat__val">5</span><span class="global-stat__lab">Matières</span></div>
      <div class="global-stat"><span class="global-stat__val">1 495 min</span><span class="global-stat__lab">Temps cumulé</span></div>
      <div class="global-stat"><span class="global-stat__val">45</span><span class="global-stat__lab">Questions IA</span></div>
    </div>
  </div>

  <!-- Matières -->
  <div class="progressions-grid stagger-children">
    @for (prog of matieresUtilisation; track prog.matiere) {
      <div class="progression-card">
        <div class="progression-card__header" [style.border-left-color]="MatiereCouleurs[prog.matiere]">
          <div style="display:flex;align-items:center;gap:10px;">
            <div class="matiere-indicator" [style.background]="MatiereCouleurs[prog.matiere] + '20'" [style.color]="MatiereCouleurs[prog.matiere]">
              {{ MatiereLabels[prog.matiere].charAt(0) }}
            </div>
            <div>
              <div class="fw-bold">{{ MatiereLabels[prog.matiere] }}</div>
              <div class="text-xs text-secondary">{{ prog.tempsMinutesTotal }} min enregistrées</div>
            </div>
          </div>
          <div style="text-align:right;">
            <div class="fw-bold text-xl" [style.color]="MatiereCouleurs[prog.matiere]">{{ prog.partTempsPct }}%</div>
            <div class="text-xs" [class.text-success]="prog.variation > 0" [class.text-danger]="prog.variation < 0">
              {{ prog.variation > 0 ? '+' : '' }}{{ prog.variation }}% ce mois
            </div>
          </div>
        </div>

        <!-- Mini sparkline SVG -->
        <div class="progression-sparkline">
          <svg viewBox="0 0 200 50" preserveAspectRatio="none" style="width:100%;height:50px;">
            <defs>
              <linearGradient [id]="'grad-' + prog.matiere" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" [attr.stop-color]="MatiereCouleurs[prog.matiere]" stop-opacity="0.3"/>
                <stop offset="100%" [attr.stop-color]="MatiereCouleurs[prog.matiere]" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <path [attr.d]="makeArea(prog.courbe)" [attr.fill]="'url(#grad-' + prog.matiere + ')'"/>
            <path [attr.d]="makeLine(prog.courbe)" fill="none" [attr.stroke]="MatiereCouleurs[prog.matiere]" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>

        <!-- Compétences / Notions -->
        <div class="competences-section">
          <div class="competences-group">
            <div class="competences-label competences-label--success">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="display:inline-block;vertical-align:middle;margin-right:4px;">
                <path d="M3 8.5L6.5 12L13 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Sujets fréquents
            </div>
            @for (c of prog.notionsMaitrisees; track c) {
              <span class="competence-chip competence-chip--success">{{ c }}</span>
            }
          </div>
          <div class="competences-group">
            <div class="competences-label competences-label--warning">
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style="display:inline-block;vertical-align:middle;margin-right:4px;">
                <path d="M2.5 8C2.5 4.962 4.962 2.5 8 2.5C10.5 2.5 12.6 4.15 13.25 6.4M13.5 8C13.5 11.038 11.038 13.5 8 13.5C5.5 13.5 3.4 11.85 2.75 9.6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                <polyline points="10,6.5 13.5,6.5 13.5,3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Questions récurrentes
            </div>
            @for (c of prog.notionsRecurrentes; track c) {
              <span class="competence-chip competence-chip--warning">{{ c }}</span>
            }
          </div>
        </div>
      </div>
    }
  </div>
</div>
  `,
  styles: [`
    .global-score-card { background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: var(--radius-xl); padding: 28px 32px; margin-bottom: 28px; display: flex; align-items: center; justify-content: space-between; gap: 32px; box-shadow: var(--shadow-md); flex-wrap: wrap; }
    .global-score-left { display: flex; align-items: center; gap: 24px; }
    .global-score-ring { position: relative; width: 120px; height: 120px; flex-shrink: 0; }
    .score-svg { width: 100%; height: 100%; }
    .global-score-value { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-family: var(--font-display); font-size: var(--text-2xl); font-weight: var(--fw-bold); color: var(--color-text-primary); }
    .global-score-right { display: flex; gap: 32px; @media(max-width:500px){ gap: 16px; } }
    .global-stat { display: flex; flex-direction: column; align-items: center; gap: 4px; }
    .global-stat__val { font-family: var(--font-display); font-size: var(--text-xl); font-weight: var(--fw-bold); color: var(--color-text-primary); }
    .global-stat__lab { font-size: var(--text-xs); color: var(--color-text-secondary); }
    .progressions-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
    .progression-card { background: var(--color-bg-surface); border: 1px solid var(--color-border); border-left: 4px solid; border-radius: var(--radius-lg); overflow: hidden; box-shadow: var(--shadow-sm); transition: all var(--transition-base); }
    .progression-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
    .progression-card__header { display: flex; align-items: flex-start; justify-content: space-between; padding: 16px 18px 12px; }
    .matiere-indicator { width: 40px; height: 40px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; font-weight: var(--fw-bold); font-size: var(--text-base); flex-shrink: 0; }
    .progression-sparkline { padding: 0 18px 8px; }
    .competences-section { padding: 12px 18px 16px; display: flex; flex-direction: column; gap: 10px; border-top: 1px solid var(--color-border); background: var(--color-bg-surface-2); }
    .competences-group { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
    .competences-label { font-size: var(--text-xs); font-weight: var(--fw-semibold); margin-right: 2px; }
    .competences-label--success { color: var(--color-success); }
    .competences-label--warning { color: var(--color-warning); }
    .competence-chip { padding: 2px 8px; border-radius: var(--radius-full); font-size: var(--text-xs); font-weight: var(--fw-medium); }
    .competence-chip--success { background: var(--color-success-light); color: var(--color-success); }
    .competence-chip--warning { background: var(--color-warning-light); color: var(--color-warning); }
  `],
})
export class ProgressionEnfantComposant {
  readonly routes = ROUTES_APP;
  readonly MatiereLabels = MatiereLabels;
  readonly MatiereCouleurs = MatiereCouleurs;

  readonly matieresUtilisation: TendanceBoitierMatiere[] = [
    { matiere: Matiere.MATHEMATIQUES, partTempsPct: 40, variation: 5, courbe: [60,65,62,70,68,75,78,82], tempsMinutesTotal: 420, notionsMaitrisees: ['Fonctions', 'Dérivées'], notionsRecurrentes: ['Intégrales par parties'] },
    { matiere: Matiere.PHYSIQUE, partTempsPct: 28, variation: 15, courbe: [45,48,55,58,62,65,68,71], tempsMinutesTotal: 280, notionsMaitrisees: ['Mécanique céleste'], notionsRecurrentes: ['2ème loi de Newton'] },
    { matiere: Matiere.CHIMIE, partTempsPct: 15, variation: -3, courbe: [65,62,60,58,62,55,58,58], tempsMinutesTotal: 190, notionsMaitrisees: ['Nomenclature'], notionsRecurrentes: ['Oxydoréduction'] },
    { matiere: Matiere.SVT, partTempsPct: 10, variation: 8, courbe: [55,60,65,68,70,72,76,79], tempsMinutesTotal: 350, notionsMaitrisees: ['Immunologie'], notionsRecurrentes: ['Méiose vs Mitose'] },
    { matiere: Matiere.FRANCAIS, partTempsPct: 7, variation: 2, courbe: [58,60,62,60,63,64,64,65], tempsMinutesTotal: 255, notionsMaitrisees: ['Commentaire'], notionsRecurrentes: ['Plan de dissertation'] },
  ];

  makeLine(data: number[]): string {
    const max = Math.max(...data), min = Math.min(...data);
    return 'M' + data.map((v, i) => `${(i/(data.length-1))*200},${50-(((v-min)/(max-min||1))*40)}`).join(' L');
  }

  makeArea(data: number[]): string {
    const max = Math.max(...data), min = Math.min(...data);
    const pts = data.map((v, i) => `${(i/(data.length-1))*200},${50-(((v-min)/(max-min||1))*40)}`);
    return `M0,50 L${pts.join(' L')} L200,50 Z`;
  }
}
