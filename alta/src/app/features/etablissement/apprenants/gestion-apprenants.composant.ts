import { Component, OnInit, signal, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApprenantRepository } from '../../../data/repositories/apprenant.repository';
import { BoitierRepository } from '../../../data/repositories/boitier.repository';
import { Apprenant } from '../../../domain/entites/etablissement.entite';
import { Boitier } from '../../../domain/entites/boitier.entite';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-gestion-apprenants',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
<div class="page-content stagger-children">
  <div class="page-header">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
      <div>
        <h1 class="page-header__title">Gestion des Apprenants</h1>
        <p class="page-header__subtitle">{{ apprenants().length }} élèves inscrits · {{ totalQuestions() }} questions posées au tuteur ALTA</p>
      </div>
      <div style="display: flex; gap: 10px;">
        <button class="btn btn-outline btn-sm" (click)="exporterCSV()" id="btn-exporter-apprenants">Exporter CSV</button>
        <button class="btn btn-primary btn-sm" (click)="ouvrirModalAjout()" id="btn-ajouter-apprenant">+ Inscrire un élève</button>
      </div>
    </div>
  </div>

  <!-- Statistiques rapides par classe -->
  <div class="kpi-grid" style="margin-bottom: 24px;">
    <div class="card" style="padding: 16px 20px; display: flex; align-items: center; gap: 14px;">
      <div class="icon-box icon-box-primary" style="font-weight: 700; font-size: 16px;">10e</div>
      <div>
        <div class="text-xs text-secondary">10ème Année (Tronc Commun)</div>
        <div class="fw-bold text-xl">{{ nbClasse('10eme') }} élèves</div>
      </div>
    </div>
    <div class="card" style="padding: 16px 20px; display: flex; align-items: center; gap: 14px;">
      <div class="icon-box icon-box-innovation" style="font-weight: 700; font-size: 16px;">11e</div>
      <div>
        <div class="text-xs text-secondary">11ème Année (11S / 11L / 11SEco)</div>
        <div class="fw-bold text-xl">{{ nbClasse('11eme') }} élèves</div>
      </div>
    </div>
    <div class="card" style="padding: 16px 20px; display: flex; align-items: center; gap: 14px;">
      <div class="icon-box icon-box-accent" style="font-weight: 700; font-size: 16px;">Tle</div>
      <div>
        <div class="text-xs text-secondary">Terminale (TSE / TSExp / TSEco)</div>
        <div class="fw-bold text-xl">{{ nbClasse('12eme') }} élèves</div>
      </div>
    </div>
    <div class="card" style="padding: 16px 20px; display: flex; align-items: center; gap: 14px;">
      <div class="icon-box icon-box-success" style="font-weight: 700; font-size: 16px;">★</div>
      <div>
        <div class="text-xs text-secondary">Moyenne de Maîtrise</div>
        <div class="fw-bold text-xl">{{ moyenneMaitrise() }}%</div>
      </div>
    </div>
  </div>

  <!-- Barre de Recherche et Filtres par niveau -->
  <div class="filters-bar">
    <div class="search-input-wrapper" style="max-width: 360px; flex: 1;">
      <svg class="search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.5"/>
        <path d="M11 11L14 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
      <input
        id="recherche-apprenant"
        type="text"
        class="form-input"
        placeholder="Rechercher par nom, prénom ou matricule..."
        [(ngModel)]="recherche"
        (input)="filtrer()"
      />
    </div>
    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
      <button class="btn btn-ghost btn-sm filtre-btn" [class.filtre-btn--active]="filtreClasse() === 'toutes'" (click)="setFiltreClasse('toutes')">Tous ({{ apprenants().length }})</button>
      <button class="btn btn-ghost btn-sm filtre-btn" [class.filtre-btn--active]="filtreClasse() === '10eme'" (click)="setFiltreClasse('10eme')">10ème</button>
      <button class="btn btn-ghost btn-sm filtre-btn" [class.filtre-btn--active]="filtreClasse() === '11eme'" (click)="setFiltreClasse('11eme')">11ème</button>
      <button class="btn btn-ghost btn-sm filtre-btn" [class.filtre-btn--active]="filtreClasse() === '12eme'" (click)="setFiltreClasse('12eme')">Terminale</button>
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
              <th>Apprenant</th>
              <th>Classe & Filière</th>
              <th>Boîtier AlternIA</th>
              <th>Taux de Maîtrise</th>
              <th>Dernière Session</th>
              <th>Statut</th>
              <th style="text-align: right;">Actions</th>
            </tr>
          </thead>
          <tbody>
            @for (a of apprenantsFiltres(); track a.id) {
              <tr>
                <td>
                  <div style="display: flex; align-items: center; gap: 12px;">
                    <div class="apprenant-avatar-circle" [style.background]="getCouleurClasse(a.classe)">
                      {{ getInitiales(a.nomComplet) }}
                    </div>
                    <div>
                      <div class="fw-semibold">{{ a.nomComplet }}</div>
                      <div class="text-xs text-secondary text-mono">ID: {{ a.id }}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <span class="badge" [class.badge-primary]="a.classe.includes('10')" [class.badge-innovation]="a.classe.includes('11')" [class.badge-accent]="a.classe.includes('12') || a.classe.includes('term')">
                    {{ formatClasseLabel(a.classe) }}
                  </span>
                </td>
                <td>
                  <span class="text-mono text-xs fw-semibold" style="color: #40BBCC;">{{ a.boitierId || 'Non assigné' }}</span>
                </td>
                <td>
                  <div style="display: flex; flex-direction: column; gap: 4px; min-width: 120px;">
                    <div style="display: flex; justify-content: space-between; font-size: 11px;">
                      <span class="fw-bold">{{ a.progression }}%</span>
                      <span class="text-secondary">{{ a.progression >= 70 ? 'Satisfaisant' : 'À renforcer' }}</span>
                    </div>
                    <div class="progress-bar" style="height: 5px;">
                      <div class="progress-bar__fill" [class.success]="a.progression >= 70" [class.warning]="a.progression < 70 && a.progression >= 50" [class.danger]="a.progression < 50" [style.width.%]="a.progression"></div>
                    </div>
                  </div>
                </td>
                <td class="text-secondary text-sm">{{ a.derniereActivite | date:'dd/MM/yyyy HH:mm' }}</td>
                <td>
                  <span class="badge badge-success">
                    <span class="dot"></span> Actif
                  </span>
                </td>
                <td style="text-align: right;">
                  <button class="btn btn-ghost btn-sm" (click)="supprimerApprenant(a)" [title]="'Supprimer ' + a.nomComplet" style="color: var(--color-danger);">
                    ✕
                  </button>
                </td>
              </tr>
            } @empty {
              <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: var(--color-text-secondary);">
                  Aucun élève trouvé pour cette recherche.
                </td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    </div>
  }

  <!-- Modale d'inscription d'un nouvel élève -->
  @if (modalAjoutOuverte()) {
    <div class="modal-backdrop animate-fade-in" (click)="fermerModalAjout()">
      <div class="modal-card animate-scale-up" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <h2 class="modal-title">Inscrire un nouvel élève</h2>
          <button class="modal-close" (click)="fermerModalAjout()">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group" style="margin-bottom: 14px;">
            <label class="form-label">Prénom de l'élève *</label>
            <input type="text" class="form-input" [(ngModel)]="nouveauPrenom" placeholder="ex: Fatoumata" />
          </div>
          <div class="form-group" style="margin-bottom: 14px;">
            <label class="form-label">Nom de famille *</label>
            <input type="text" class="form-input" [(ngModel)]="nouveauNom" placeholder="ex: Traoré" />
          </div>
          <div class="form-grid" style="margin-bottom: 14px;">
            <div class="form-group">
              <label class="form-label">Classe *</label>
              <select class="form-input" [(ngModel)]="nouvelleClasse">
                <option value="10eme">10ème Année (Tronc Commun)</option>
                <option value="11eme">11ème Année</option>
                <option value="12eme">Terminale (12ème)</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Série / Filière</label>
              <select class="form-input" [(ngModel)]="nouvelleSerie">
                <option value="generale">Générale / Tronc Commun</option>
                <option value="11s">11ème Sciences (11S)</option>
                <option value="11l">11ème Lettres (11L)</option>
                <option value="11seco">11ème Économie (11SEco)</option>
                <option value="tse">Terminale Sciences Exactes (TSE)</option>
                <option value="tsexp">Terminale Sciences Expérimentales (TSExp)</option>
                <option value="tseco">Terminale Sciences Économiques (TSEco)</option>
                <option value="tss">Terminale Sciences Sociales (TSS)</option>
                <option value="tll">Terminale Lettres & Littérature (TLL)</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Boîtier AlternIA assigné</label>
            <select class="form-input" [(ngModel)]="nouveauBoitierId">
              <option value="">-- Aucun boîtier pour l'instant --</option>
              @for (b of boitiers(); track b.id) {
                <option [value]="b.id">{{ b.nom }} ({{ b.codeUnique }})</option>
              }
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" (click)="fermerModalAjout()">Annuler</button>
          <button class="btn btn-primary" (click)="enregistrerApprenant()" id="btn-valider-ajout-apprenant">Enregistrer l'élève</button>
        </div>
      </div>
    </div>
  }
</div>
  `,
  styles: [`
    .apprenant-avatar-circle {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 13px;
      flex-shrink: 0;
      box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }
  `],
})
export class GestionApprenantsComposant implements OnInit {
  private readonly apprenantRepo = inject(ApprenantRepository);
  private readonly boitierRepo = inject(BoitierRepository);
  private readonly notifService = inject(NotificationService);

  chargement = signal(true);
  apprenants = signal<Apprenant[]>([]);
  boitiers = signal<Boitier[]>([]);
  apprenantsFiltres = signal<Apprenant[]>([]);

  recherche = '';
  filtreClasse = signal<string>('toutes');

  // Formulaire d'ajout
  modalAjoutOuverte = signal(false);
  nouveauPrenom = '';
  nouveauNom = '';
  nouvelleClasse = '10eme';
  nouvelleSerie = 'generale';
  nouveauBoitierId = '';

  readonly totalQuestions = computed(() => {
    return this.apprenants().length * 15;
  });

  readonly moyenneMaitrise = computed(() => {
    const list = this.apprenants();
    if (!list.length) return 80;
    const sum = list.reduce((acc, a) => acc + (a.progression || 75), 0);
    return Math.round(sum / list.length);
  });

  ngOnInit(): void {
    this.chargerDonnees();
  }

  chargerDonnees(): void {
    this.chargement.set(true);
    this.apprenantRepo.obtenirTous('').subscribe({
      next: (list) => {
        this.apprenants.set(list);
        this.filtrer();
        this.chargement.set(false);
      },
      error: () => {
        this.chargement.set(false);
      }
    });

    this.boitierRepo.obtenirTous().subscribe({
      next: (bList) => this.boitiers.set(bList),
    });
  }

  nbClasse(classe: string): number {
    return this.apprenants().filter(a => (a.classe || '').toLowerCase().includes(classe)).length;
  }

  setFiltreClasse(classe: string): void {
    this.filtreClasse.set(classe);
    this.filtrer();
  }

  filtrer(): void {
    const q = this.recherche.toLowerCase().trim();
    const c = this.filtreClasse();

    let res = this.apprenants();
    if (c !== 'toutes') {
      res = res.filter(a => (a.classe || '').toLowerCase().includes(c));
    }
    if (q) {
      res = res.filter(a =>
        a.nomComplet.toLowerCase().includes(q) ||
        a.id.toLowerCase().includes(q) ||
        (a.classe || '').toLowerCase().includes(q)
      );
    }
    this.apprenantsFiltres.set(res);
  }

  getInitiales(nomComplet: string): string {
    if (!nomComplet) return 'E';
    const parts = nomComplet.trim().split(' ');
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return nomComplet.substring(0, 2).toUpperCase();
  }

  getCouleurClasse(classe: string): string {
    const c = (classe || '').toLowerCase();
    if (c.includes('10')) return '#314999';
    if (c.includes('11')) return '#40BBCC';
    if (c.includes('12') || c.includes('term')) return '#F1851F';
    return '#10B981';
  }

  formatClasseLabel(classe: string): string {
    const c = (classe || '').toLowerCase();
    if (c.includes('10')) return '10ème Tronc Commun';
    if (c.includes('11')) return '11ème Année';
    if (c.includes('12') || c.includes('term')) return 'Terminale (12ème)';
    return classe.toUpperCase();
  }

  ouvrirModalAjout(): void {
    this.nouveauPrenom = '';
    this.nouveauNom = '';
    this.nouvelleClasse = '10eme';
    this.nouvelleSerie = 'generale';
    this.nouveauBoitierId = '';
    this.modalAjoutOuverte.set(true);
  }

  fermerModalAjout(): void {
    this.modalAjoutOuverte.set(false);
  }

  enregistrerApprenant(): void {
    if (!this.nouveauPrenom || !this.nouveauNom) {
      this.notifService.erreur('Champs requis', 'Veuillez renseigner le nom et le prénom.');
      return;
    }

    this.apprenantRepo.creerApprenant({
      prenom: this.nouveauPrenom.trim(),
      nom: this.nouveauNom.trim(),
      classe: this.nouvelleClasse,
      serie: this.nouvelleSerie,
      boitierId: this.nouveauBoitierId || undefined,
    }).subscribe({
      next: (nouvelApprenant) => {
        this.apprenants.update(list => [nouvelApprenant, ...list]);
        this.filtrer();
        this.notifService.succes('Élève inscrit', `${nouvelApprenant.nomComplet} a été inscrit avec succès.`);
        this.fermerModalAjout();
      },
      error: () => {
        this.notifService.erreur('Erreur', "Impossible d'inscrire l'élève.");
      }
    });
  }

  supprimerApprenant(a: Apprenant): void {
    if (confirm(`Voulez-vous vraiment supprimer l'élève ${a.nomComplet} ?`)) {
      this.apprenantRepo.supprimerApprenant(a.id).subscribe({
        next: () => {
          this.apprenants.update(list => list.filter(item => item.id !== a.id));
          this.filtrer();
          this.notifService.succes('Élève supprimé', `${a.nomComplet} a été retiré.`);
        }
      });
    }
  }

  exporterCSV(): void {
    const header = "ID,Nom Complet,Classe,Boitier,Maitrise,Derniere Activite\n";
    const rows = this.apprenants().map(a =>
      `"${a.id}","${a.nomComplet}","${a.classe}","${a.boitierId || ''}",${a.progression}%,"${a.derniereActivite.toISOString()}"`
    ).join("\n");

    const blob = new Blob([header + rows], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `apprenants_alternia_${Date.now()}.csv`;
    link.click();
    this.notifService.succes('Export CSV réussi', 'La liste des élèves a été téléchargée.');
  }
}
