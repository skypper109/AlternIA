import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AlerteRepository } from '../../../data/repositories/alerte.repository';
import { Alerte, TypeAlerte } from '../../../domain/entites/alerte.entite';

@Component({
  selector: 'app-alertes',
  standalone: true,
  imports: [CommonModule],
  template: `
<div class="page-content stagger-children">
  <div class="page-header">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
      <div>
        <h1 class="page-header__title">Alertes & Notifications</h1>
        <p class="page-header__subtitle">{{ alertesNonLues() }} notification(s) non lue(s)</p>
      </div>
      <button class="btn btn-ghost btn-sm" id="btn-tout-marquer-lu" (click)="toutMarquerLu()">Tout marquer comme lu</button>
    </div>
  </div>

  @if (chargement()) {
    <div class="skeleton" style="height:400px;border-radius:16px;"></div>
  } @else {

    <!-- Filtres -->
    <div class="alertes-filtres">
      @for (type of typesAlertes; track type.id) {
        <button class="alerte-filtre-btn" [class.alerte-filtre-btn--active]="filtreActif() === type.id" (click)="filtreActif.set(type.id)" [id]="'btn-filtre-' + type.id">
          {{ type.label }}
        </button>
      }
    </div>

    <!-- Liste alertes -->
    <div class="alertes-list">
      @for (alerte of alertesFiltrees(); track alerte.id) {
        <div class="alerte-card" [class.alerte-card--unread]="!alerte.lue" [class.alerte-card--haute]="alerte.priorite === 'haute'">
          <div class="alerte-card__icon" [ngClass]="getIconClass(alerte.type)">
            @switch (alerte.type) {
              @case ('OBJECTIF_ATTEINT') {
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path d="M3 9L7 13L15 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              }
              @case ('PROGRESSION_REMARQUABLE') {
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <polyline points="1.5,12 5,8 8,11.5 12,5 15,8 17,6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>
              }
              @case ('REVISION_RECOMMANDEE') {
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <rect x="3" y="2" width="10" height="14" rx="2" stroke="currentColor" stroke-width="1.3"/>
                  <path d="M6 6H10M6 9H10M6 12H8" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                </svg>
              }
              @case ('FAIBLE_ACTIVITE') {
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M9 5V9.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                  <circle cx="9" cy="12" r="1" fill="currentColor"/>
                </svg>
              }
              @default {
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path d="M9 2C6.239 2 4 4.239 4 7V12H14V7C14 4.239 11.761 2 9 2Z" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M4 12H14L15 14H3L4 12Z" fill="currentColor" fill-opacity="0.5"/>
                  <path d="M7.5 15C7.5 16.105 8.12 17 9 17C9.88 17 10.5 16.105 10.5 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
              }
            }
          </div>
          <div class="alerte-card__content">
            <div class="alerte-card__header">
              <span class="alerte-card__title">{{ alerte.titre }}</span>
              <div style="display:flex;align-items:center;gap:8px;">
                @if (alerte.priorite === 'haute') {
                  <span class="badge badge-danger">Urgent</span>
                }
                <span class="text-xs text-secondary">{{ alerte.dateCreation | date:'dd MMM, HH:mm' }}</span>
              </div>
            </div>
            <p class="alerte-card__message">{{ alerte.message }}</p>
            <div class="alerte-card__actions">
              @if (!alerte.lue) {
                <button class="btn btn-ghost btn-sm" (click)="marquerLue(alerte)" [id]="'btn-lu-' + alerte.id">
                  <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                    <path d="M2 7L5 10L11 3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
                  </svg>
                  Marquer comme lu
                </button>
              }
            </div>
          </div>
          @if (!alerte.lue) {
            <div class="alerte-unread-indicator"></div>
          }
        </div>
      } @empty {
        <div class="etat-vide">
          <div class="etat-vide__icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" style="color:var(--color-success);">
              <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="1.5"/>
              <path d="M7.5 12L10.5 15L16.5 9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="etat-vide__titre">Tout est à jour !</div>
          <div class="etat-vide__desc">Aucune alerte pour cette catégorie</div>
        </div>
      }
    </div>
  }
</div>
  `,
  styles: [`
    .alertes-filtres { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }
    .alerte-filtre-btn { display: flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: var(--radius-full); border: 1px solid var(--color-border); background: var(--color-bg-surface); cursor: pointer; font-size: var(--text-xs); font-weight: var(--fw-medium); color: var(--color-text-secondary); transition: all var(--transition-fast); }
    .alerte-filtre-btn:hover { border-color: var(--color-secondaire); color: var(--color-text-primary); }
    .alerte-filtre-btn--active { border-color: var(--color-secondaire) !important; background: var(--color-secondaire-light) !important; color: var(--color-secondaire) !important; font-weight: var(--fw-semibold); }
    .alertes-list { display: flex; flex-direction: column; gap: 12px; }
    .alerte-card { display: flex; gap: 14px; padding: 16px 18px; background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); box-shadow: var(--shadow-xs); position: relative; transition: all var(--transition-base); }
    .alerte-card:hover { box-shadow: var(--shadow-sm); }
    .alerte-card--unread { border-left: 3px solid var(--color-secondaire); }
    .alerte-card--haute { border-left-color: var(--color-danger) !important; }
    .alerte-card__icon { width: 40px; height: 40px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; background: var(--color-bg-surface-2); color: var(--color-text-secondary); }
    .alerte-card__content { flex: 1; min-width: 0; }
    .alerte-card__header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 6px; flex-wrap: wrap; }
    .alerte-card__title { font-weight: var(--fw-semibold); font-size: var(--text-sm); color: var(--color-text-primary); }
    .alerte-card__message { font-size: var(--text-sm); color: var(--color-text-secondary); line-height: var(--lh-relaxed); margin-bottom: 10px; }
    .alerte-card__actions { display: flex; gap: 8px; }
    .alerte-unread-indicator { position: absolute; top: 18px; right: 16px; width: 8px; height: 8px; border-radius: 50%; background: var(--color-secondaire); }
    .etat-vide { text-align: center; padding: 60px 24px; }
    .etat-vide__icon { margin-bottom: 12px; display: flex; justify-content: center; }
    .etat-vide__titre { font-family: var(--font-display); font-size: var(--text-xl); font-weight: var(--fw-bold); color: var(--color-text-primary); margin-bottom: 6px; }
    .etat-vide__desc { font-size: var(--text-sm); color: var(--color-text-secondary); }
  `],
})
export class AlertesComposant implements OnInit {
  private readonly repo = inject(AlerteRepository);

  chargement = signal(true);
  alertes = signal<Alerte[]>([]);
  filtreActif = signal<string>('toutes');

  readonly alertesNonLues = () => this.alertes().filter(a => !a.lue).length;
  readonly alertesFiltrees = () => {
    const f = this.filtreActif();
    if (f === 'toutes') return this.alertes();
    if (f === 'non-lues') return this.alertes().filter(a => !a.lue);
    return this.alertes().filter(a => a.type === f);
  };

  readonly typesAlertes = [
    { id: 'toutes', label: 'Toutes' },
    { id: 'non-lues', label: 'Non lues' },
    { id: TypeAlerte.OBJECTIF_ATTEINT, label: 'Objectifs' },
    { id: TypeAlerte.PROGRESSION_REMARQUABLE, label: 'Progression' },
    { id: TypeAlerte.REVISION_RECOMMANDEE, label: 'Révisions' },
    { id: TypeAlerte.FAIBLE_ACTIVITE, label: 'Inactivité' },
  ];

  ngOnInit(): void {
    this.repo.obtenirAlertesParent('parent-1').subscribe(a => {
      this.alertes.set(a);
      this.chargement.set(false);
    });
  }

  marquerLue(alerte: Alerte): void {
    this.repo.marquerCommeLue(alerte.id).subscribe(() => {
      this.alertes.update(list => list.map(a => a.id === alerte.id ? { ...a, lue: true } : a));
    });
  }

  toutMarquerLu(): void {
    this.alertes.update(list => list.map(a => ({ ...a, lue: true })));
  }

  getIconClass(type: TypeAlerte): string {
    if (type === TypeAlerte.OBJECTIF_ATTEINT || type === TypeAlerte.PROGRESSION_REMARQUABLE) return 'alerte-icon--success';
    if (type === TypeAlerte.FAIBLE_ACTIVITE || type === TypeAlerte.BOITIER_DECONNECTE) return 'alerte-icon--danger';
    return '';
  }
}
