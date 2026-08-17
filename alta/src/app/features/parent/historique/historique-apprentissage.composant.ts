import { Component, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Matiere, MatiereLabels, MatiereCouleurs } from '../../../core/enums';

@Component({
  selector: 'app-historique-apprentissage',
  standalone: true,
  imports: [CommonModule],
  template: `
<div class="page-content stagger-children">
  <div class="page-header">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
      <div>
        <h1 class="page-header__title">Historique d'activité du boîtier</h1>
        <p class="page-header__subtitle">Sessions enregistrées sur le boîtier Maison (ALT-HOME-0042) · {{ sessionsFiltrees().length }} session(s) affichée(s)</p>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;">
        <button class="btn btn-ghost btn-sm filtre-btn" [class.filtre-btn--active]="filtreActif() === 'tout'" (click)="filtreActif.set('tout')" id="btn-hist-tout">Toutes les sessions</button>
        <button class="btn btn-ghost btn-sm filtre-btn" [class.filtre-btn--active]="filtreActif() === 'Vocal'" (click)="filtreActif.set('Vocal')" id="btn-hist-vocale">Interactions vocales</button>
        <button class="btn btn-ghost btn-sm filtre-btn" [class.filtre-btn--active]="filtreActif() === 'Interactif'" (click)="filtreActif.set('Interactif')" id="btn-hist-interactif">Mode interactif</button>
      </div>
    </div>
  </div>

  <div class="historique-timeline">
    @for (session of sessionsFiltrees(); track session.id) {
      <div class="timeline-item">
        <div class="timeline-dot" [style.border-color]="MatiereCouleurs[session.matiere]" [style.background]="MatiereCouleurs[session.matiere] + '20'"></div>
        <div class="timeline-card">
          <div class="timeline-card__header">
            <div style="display:flex;align-items:center;gap:10px;">
              <span class="matiere-tag" [style.background]="MatiereCouleurs[session.matiere] + '20'" [style.color]="MatiereCouleurs[session.matiere]">
                {{ MatiereLabels[session.matiere] }}
              </span>
              <span class="text-sm fw-semibold">{{ session.date | date:'EEEE d MMMM':'':'fr' }}</span>
            </div>
            <span class="text-xs text-secondary">{{ session.date | date:'HH:mm' }}</span>
          </div>
          <div class="timeline-card__stats">
            <div class="session-stat">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <circle cx="7" cy="7" r="6" stroke="currentColor" stroke-width="1.2"/>
                <path d="M7 4V7L9 9" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
              </svg>
              {{ session.duree }} min d'utilisation
            </div>
            <div class="session-stat">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 1L4 5H10L7 1Z" fill="currentColor" fill-opacity="0.6"/>
                <rect x="3" y="7" width="8" height="6" rx="1" stroke="currentColor" stroke-width="1.2"/>
              </svg>
              {{ session.questions }} questions posées
            </div>
            <div class="session-stat text-success fw-medium">
              Mode {{ session.mode }}
            </div>
          </div>
          <div class="timeline-card__notions">
            @for (notion of session.notions; track notion) {
              <span class="notion-tag">{{ notion }}</span>
            }
          </div>
        </div>
      </div>
    } @empty {
      <div class="text-sm text-secondary" style="padding:24px 0;">Aucune session trouvée pour ce filtre.</div>
    }
  </div>
</div>
  `,
  styles: [`
    .historique-timeline { display: flex; flex-direction: column; gap: 0; }
    .timeline-item { display: flex; gap: 16px; position: relative; padding-bottom: 20px; }
    .timeline-item::before { content: ''; position: absolute; left: 11px; top: 24px; bottom: 0; width: 1px; background: var(--color-border); }
    .timeline-item:last-child::before { display: none; }
    .timeline-dot { width: 24px; height: 24px; border-radius: 50%; border: 2px solid; flex-shrink: 0; margin-top: 12px; }
    .timeline-card { flex: 1; background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 14px 16px; box-shadow: var(--shadow-xs); }
    .timeline-card__header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
    .matiere-tag { padding: 3px 10px; border-radius: var(--radius-full); font-size: var(--text-xs); font-weight: var(--fw-semibold); }
    .timeline-card__stats { display: flex; gap: 16px; margin-bottom: 10px; flex-wrap: wrap; }
    .session-stat { display: flex; align-items: center; gap: 5px; font-size: var(--text-sm); color: var(--color-text-secondary); font-weight: var(--fw-medium); }
    .timeline-card__notions { display: flex; flex-wrap: wrap; gap: 6px; }
    .notion-tag { padding: 2px 8px; background: var(--color-bg-surface-2); border-radius: var(--radius-full); font-size: var(--text-xs); color: var(--color-text-secondary); border: 1px solid var(--color-border); }
    .filtre-btn--active { background: var(--color-secondaire-light) !important; color: var(--color-secondaire) !important; border-color: var(--color-secondaire) !important; font-weight: var(--fw-semibold); }
  `],
})
export class HistoriqueApprentissageComposant {
  readonly MatiereLabels = MatiereLabels;
  readonly MatiereCouleurs = MatiereCouleurs;
  filtreActif = signal<'tout' | 'Vocal' | 'Interactif'>('tout');

  readonly sessions = [
    { id: '1', date: new Date('2026-08-09T18:30:00'), matiere: Matiere.MATHEMATIQUES, duree: 45, questions: 32, mode: 'Vocal', notions: ['Intégrales par parties', 'Fonctions exponentielles'] },
    { id: '2', date: new Date('2026-08-09T10:15:00'), matiere: Matiere.PHYSIQUE, duree: 30, questions: 22, mode: 'Interactif', notions: ['Mécanique céleste', '2ème loi de Newton'] },
    { id: '3', date: new Date('2026-08-08T17:00:00'), matiere: Matiere.SVT, duree: 50, questions: 28, mode: 'Vocal', notions: ['Mitose & Méiose', 'Génétique'] },
    { id: '4', date: new Date('2026-08-07T14:30:00'), matiere: Matiere.FRANCAIS, duree: 40, questions: 20, mode: 'Interactif', notions: ['Dissertation littéraire', 'Structure d\'introduction'] },
    { id: '5', date: new Date('2026-08-06T09:00:00'), matiere: Matiere.CHIMIE, duree: 35, questions: 18, mode: 'Vocal', notions: ['Oxydoréduction', 'Titrage pH-métrique'] },
    { id: '6', date: new Date('2026-08-05T16:00:00'), matiere: Matiere.MATHEMATIQUES, duree: 60, questions: 40, mode: 'Vocal', notions: ['Probabilités conditionnelles'] },
  ];

  readonly sessionsFiltrees = computed(() => {
    const f = this.filtreActif();
    if (f === 'tout') return this.sessions;
    return this.sessions.filter(s => s.mode === f);
  });
}
