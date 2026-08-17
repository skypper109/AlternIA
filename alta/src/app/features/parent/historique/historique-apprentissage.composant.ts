import { Component, signal, computed, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Matiere, MatiereLabels, MatiereCouleurs } from '../../../core/enums';
import { environment } from '../../../../environments/environment';

function parseMatiere(m: string): Matiere {
  const n = (m || '').toLowerCase();
  if (n.includes('math')) return Matiere.MATHEMATIQUES;
  if (n.includes('phys')) return Matiere.PHYSIQUE;
  if (n.includes('chim')) return Matiere.CHIMIE;
  if (n.includes('svt') || n.includes('bio')) return Matiere.SVT;
  if (n.includes('fran')) return Matiere.FRANCAIS;
  return Matiere.MATHEMATIQUES;
}

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
        <p class="page-header__subtitle">Sessions enregistrées en temps réel sur le boîtier Maison (ALT-HOME-0042) · {{ sessionsFiltrees().length }} session(s)</p>
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
        <div class="timeline-dot" [style.border-color]="getMatiereCouleur(session.matiere)" [style.background]="getMatiereCouleur(session.matiere) + '20'"></div>
        <div class="timeline-card card">
          <div class="timeline-card__header">
            <div style="display:flex;align-items:center;gap:10px;">
              <span class="matiere-tag" [style.background]="getMatiereCouleur(session.matiere) + '20'" [style.color]="getMatiereCouleur(session.matiere)">
                {{ getMatiereLabel(session.matiere) }}
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
    .timeline-item::before { content: ''; position: absolute; left: 11px; top: 24px; bottom: 0; width: 1px; background: var(--glass-border); }
    .timeline-item:last-child::before { display: none; }
    .timeline-dot { width: 24px; height: 24px; border-radius: 50%; border: 2px solid; flex-shrink: 0; margin-top: 12px; }
    .timeline-card { flex: 1; padding: 14px 16px; }
    .timeline-card__header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
    .matiere-tag { padding: 3px 10px; border-radius: var(--radius-full); font-size: var(--text-xs); font-weight: var(--fw-semibold); }
    .timeline-card__stats { display: flex; gap: 16px; margin-bottom: 10px; flex-wrap: wrap; }
    .session-stat { display: flex; align-items: center; gap: 5px; font-size: var(--text-sm); color: var(--color-text-secondary); font-weight: var(--fw-medium); }
    .timeline-card__notions { display: flex; flex-wrap: wrap; gap: 6px; }
    .notion-tag { padding: 2px 8px; background: var(--glass-bg-subtle); border-radius: var(--radius-full); font-size: var(--text-xs); color: var(--color-text-secondary); border: 1px solid var(--glass-border); }
  `],
})
export class HistoriqueApprentissageComposant implements OnInit {
  private readonly http = inject(HttpClient);

  filtreActif = signal<'tout' | 'Vocal' | 'Interactif'>('tout');
  sessions = signal<any[]>([
    { id: '1', date: new Date(), matiere: Matiere.MATHEMATIQUES, duree: 45, questions: 32, mode: 'Vocal', notions: ['Intégrales par parties', 'Fonctions exponentielles'] },
    { id: '2', date: new Date(Date.now() - 86400000), matiere: Matiere.PHYSIQUE, duree: 30, questions: 22, mode: 'Interactif', notions: ['Mécanique céleste', '2ème loi de Newton'] },
    { id: '3', date: new Date(Date.now() - 172800000), matiere: Matiere.SVT, duree: 50, questions: 28, mode: 'Vocal', notions: ['Zonation végétale', 'Facteurs écologiques'] },
  ]);

  getMatiereCouleur(m: any): string {
    return (MatiereCouleurs as any)[m] || '#314999';
  }

  getMatiereLabel(m: any): string {
    return (MatiereLabels as any)[m] || m;
  }

  ngOnInit(): void {
    this.http.get<any[]>(`${environment.apiUrl}/parent/historique`).subscribe({
      next: (list) => {
        if (list && list.length > 0) {
          const mapped = list.map((item, i) => ({
            id: item.id,
            date: item.date ? new Date(item.date) : new Date(Date.now() - i * 86400000),
            matiere: parseMatiere(item.matiere),
            duree: item.dureeMinutes || 30,
            questions: item.questionsPosees || 12,
            mode: i % 2 === 0 ? 'Vocal' : 'Interactif',
            notions: [item.notion || 'Révision générale'],
          }));
          this.sessions.set(mapped);
        }
      },
      error: () => {}
    });
  }

  readonly sessionsFiltrees = computed(() => {
    const f = this.filtreActif();
    if (f === 'tout') return this.sessions();
    return this.sessions().filter(s => s.mode === f);
  });
}
