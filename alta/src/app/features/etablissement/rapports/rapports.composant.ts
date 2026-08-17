import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatistiquesRepository } from '../../../data/repositories/statistiques.repository';
import { RapportActivite } from '../../../domain/entites/statistiques-utilisation.entite';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-rapports',
  standalone: true,
  imports: [CommonModule],
  template: `
<div class="page-content stagger-children">
  <div class="page-header">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
      <div>
        <h1 class="page-header__title">Rapports</h1>
        <p class="page-header__subtitle">Générez et consultez vos rapports pédagogiques</p>
      </div>
      <div style="display:flex;gap:10px;">
        <button class="btn btn-outline btn-sm" (click)="exporterExcelRapide()" id="btn-rapport-excel">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <rect x="1" y="1" width="12" height="12" rx="2" stroke="#10B981" stroke-width="1.3"/>
            <path d="M4 5L7 8L10 5M4 9H10" stroke="#10B981" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          Export Excel
        </button>
        <button class="btn btn-primary btn-sm" (click)="exporterPdfRapide()" id="btn-rapport-pdf">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <rect x="1" y="1" width="12" height="12" rx="2" stroke="white" stroke-width="1.3"/>
            <path d="M4 7H10M7 4V10" stroke="white" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
          Générer PDF
        </button>
      </div>
    </div>
  </div>

  <!-- Génération rapide -->
  <div class="rapport-generator">
    <h2 class="fw-semibold text-base" style="margin-bottom:16px;">Générer un nouveau rapport</h2>
    <div class="rapport-generator__options">
      @for (type of typesRapport; track type.id) {
        <button class="rapport-type-btn" [class.rapport-type-btn--active]="typeSelectionne() === type.id" (click)="typeSelectionne.set(type.id)" [id]="'btn-type-' + type.id">
          <div class="rapport-type-btn__icon" [style.background]="type.couleur + '20'" [style.color]="type.couleur">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <rect x="3" y="2" width="14" height="16" rx="2.5" stroke="currentColor" stroke-width="1.5"/>
                <path d="M7 7H13M7 10H13M7 13H10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </div>
          <div>
            <div class="fw-semibold text-sm">{{ type.label }}</div>
            <div class="text-xs text-secondary">{{ type.desc }}</div>
          </div>
        </button>
      }
    </div>
    <button class="btn btn-primary" style="margin-top:16px;" (click)="genererNouveauRapport()" id="btn-generer-rapport-action" [disabled]="!typeSelectionne() || generationEnCours()">
      @if (generationEnCours()) {
        <span class="animate-spin">⟳</span> Génération…
      } @else {
        Générer le rapport
      }
    </button>
  </div>

  <!-- Historique -->
  @if (chargement()) {
    <div class="skeleton" style="height:300px;border-radius:16px;"></div>
  } @else {
    <div class="card">
      <div class="card__header">
        <h2 class="card__title">Historique des rapports</h2>
        <span class="badge badge-primary">{{ rapports().length }} rapports</span>
      </div>
      <div class="table-wrapper">
        <table class="table">
          <thead>
            <tr>
              <th>Rapport</th>
              <th>Période</th>
              <th>Date</th>
              <th>Format</th>
              <th>Taille</th>
              <th>Statut</th>
              <th style="text-align:right">Actions</th>
            </tr>
          </thead>
          <tbody>
            @for (rapport of rapports(); track rapport.id) {
              <tr>
                <td>
                  <div style="display:flex;align-items:center;gap:10px;">
                    <div class="icon-box icon-box-sm" [class.icon-box-danger]="rapport.type === 'pdf'" [class.icon-box-success]="rapport.type === 'excel'">
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <rect x="2" y="1" width="10" height="12" rx="1.5" stroke="currentColor" stroke-width="1.3"/>
                        <path d="M4 5H10M4 7.5H10M4 10H7" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                      </svg>
                    </div>
                    <span class="fw-medium text-sm">{{ rapport.titre }}</span>
                  </div>
                </td>
                <td class="text-secondary text-sm">{{ rapport.periode }}</td>
                <td class="text-secondary text-sm">{{ rapport.dateGeneration | date:'dd/MM/yyyy' }}</td>
                <td>
                  <span class="badge" [class.badge-danger]="rapport.type === 'pdf'" [class.badge-success]="rapport.type === 'excel'">
                    {{ rapport.type.toUpperCase() }}
                  </span>
                </td>
                <td class="text-secondary text-sm">{{ (rapport.tailleFichier || 0) | number:'1.0-0' }} Ko</td>
                <td>
                  <span class="badge badge-success">
                    <span class="dot"></span>
                    Disponible
                  </span>
                </td>
                <td>
                  <div style="display:flex;gap:6px;justify-content:flex-end;">
                    <button class="btn btn-ghost btn-sm" (click)="telechargerRapport(rapport)" [id]="'btn-dl-' + rapport.id">
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M7 2V9M7 9L4 6M7 9L10 6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                        <path d="M2 12H12" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                      </svg>
                      Télécharger
                    </button>
                  </div>
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
    .rapport-generator { background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 20px 24px; margin-bottom: 24px; box-shadow: var(--shadow-xs); }
    .rapport-generator__options { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
    .rapport-type-btn { display: flex; align-items: center; gap: 12px; padding: 14px; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-bg-surface-2); cursor: pointer; text-align: left; transition: all var(--transition-fast); }
    .rapport-type-btn:hover { border-color: var(--color-primaire); background: var(--color-bg-surface); }
    .rapport-type-btn--active { border-color: var(--color-primaire) !important; background: var(--color-primaire-light) !important; }
    .rapport-type-btn__icon { width: 38px; height: 38px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  `],
})
export class RapportsComposant implements OnInit {
  private readonly repo = inject(StatistiquesRepository);
  private readonly notifService = inject(NotificationService);

  chargement = signal(true);
  rapports = signal<RapportActivite[]>([]);
  typeSelectionne = signal<string | null>('hebdo');
  generationEnCours = signal(false);

  readonly typesRapport = [
    { id: 'hebdo', label: 'Hebdomadaire', desc: 'Activité des 7 derniers jours', couleur: '#314999' },
    { id: 'mensuel', label: 'Mensuel', desc: 'Synthèse du mois en cours', couleur: '#40BBCC' },
    { id: 'trimestriel', label: 'Trimestriel', desc: 'Bilan pédagogique trimestriel', couleur: '#F1851F' },
    { id: 'classe', label: 'Par classe', desc: 'Bilan par classe et niveau', couleur: '#10B981' },
  ];

  ngOnInit(): void {
    this.repo.obtenirRapports('etab-1').subscribe(r => {
      this.rapports.set(r);
      this.chargement.set(false);
    });
  }

  exporterExcelRapide(): void {
    this.notifService.succes('Export Excel généré', 'Le rapport Excel a été téléchargé avec succès.');
    this.simulerTelechargement('rapport-general.xlsx');
  }

  exporterPdfRapide(): void {
    this.notifService.succes('Export PDF généré', 'Le rapport PDF global a été généré.');
    this.simulerTelechargement('rapport-general.pdf');
  }

  genererNouveauRapport(): void {
    const selected = this.typeSelectionne();
    if (!selected) return;

    const tInfo = this.typesRapport.find(t => t.id === selected);
    this.generationEnCours.set(true);

    setTimeout(() => {
      const nouveauRapport: RapportActivite = {
        id: 'rpt-' + Date.now(),
        etablissementId: 'etab-1',
        titre: `Rapport ${tInfo?.label ?? 'Pédagogique'} – Août 2026`,
        periode: 'Août 2026',
        dateDebut: new Date(),
        dateFin: new Date(),
        dateGeneration: new Date(),
        type: 'pdf',
        statut: 'genere',
        urlTelechargement: '#',
        tailleFichier: Math.floor(Math.random() * 3000) + 1200,
      };

      this.rapports.update(list => [nouveauRapport, ...list]);
      this.generationEnCours.set(false);
      this.notifService.succes('Rapport généré', `Le rapport ${tInfo?.label} est prêt.`);
    }, 1200);
  }

  telechargerRapport(rapport: RapportActivite): void {
    this.notifService.info('Téléchargement', `Téléchargement de "${rapport.titre}" en cours…`);
    this.simulerTelechargement(`${rapport.titre.toLowerCase().replace(/[^a-z0-9]/g, '-')}.${rapport.type}`);
  }

  private simulerTelechargement(nomFichier: string): void {
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent('Alternia - Rapport Pédagogique (Mali)'));
    element.setAttribute('download', nomFichier);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  }
}
