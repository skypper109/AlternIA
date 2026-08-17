import { Component, OnInit, signal, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BoitierRepository } from '../../../data/repositories/boitier.repository';
import { AlerteRepository } from '../../../data/repositories/alerte.repository';
import { Boitier } from '../../../domain/entites/boitier.entite';
import { Alerte } from '../../../domain/entites/alerte.entite';
import { StatutBoitier, Matiere, MatiereLabels, MatiereCouleurs } from '../../../core/enums';
import { ROUTES_APP } from '../../../core/constantes/routes.constantes';
import { ProgrammeRevisionService } from '../../../core/services/programme-revision.service';
import { EnseignantIaParentService } from '../../../core/services/enseignant-ia-parent.service';
import { STATUT_SEANCE_CONFIG } from '../../../domain/entites/programme-revision.entite';

interface DispositifMock {
  codeBoitier: string;
  nomBoitier: string;
  tempsUtilisationGlobal: number; // minutes
  matiereDominante: Matiere;
  derniereUtilisation: Date;
  matieresConsultees: { matiere: Matiere; tempsMinutes: number; questionsPosees: number }[];
}

@Component({
  selector: 'app-tableau-de-bord-parent',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './tableau-de-bord-parent.composant.html',
  styleUrl: './tableau-de-bord-parent.composant.scss',
})
export class TableauDeBordParentComposant implements OnInit {
  private readonly boitierRepo = inject(BoitierRepository);
  private readonly alerteRepo = inject(AlerteRepository);
  readonly revisionService = inject(ProgrammeRevisionService);
  readonly enseignantService = inject(EnseignantIaParentService);

  readonly routes = ROUTES_APP;
  readonly MatiereLabels = MatiereLabels;
  readonly MatiereCouleurs = MatiereCouleurs;
  readonly StatutBoitier = StatutBoitier;
  readonly STATUT_SEANCE_CONFIG = STATUT_SEANCE_CONFIG;

  readonly aujourdhui = new Date();

  boitier = signal<Boitier | null>(null);
  alertes = signal<Alerte[]>([]);

  readonly alertesNonLues = computed(() => this.alertes().filter(a => !a.lue).length);

  readonly prochainesSeances = this.revisionService.prochainesSeances;
  readonly seancesTermineesCount = computed(() => this.revisionService.seancesTerminees().length);
  readonly seancesManqueesCount = computed(() => this.revisionService.seancesManquees().length);
  readonly tauxRespectPlanning = this.revisionService.tauxRespectPlanning;
  readonly profilActif = this.enseignantService.profilActif;
  readonly avatarActif = this.profilActif;

  readonly dispositif: DispositifMock = {
    codeBoitier: 'ALT-HOME-0042',
    nomBoitier: 'Boîtier Alternia Maison',
    tempsUtilisationGlobal: 125,
    matiereDominante: Matiere.MATHEMATIQUES,
    derniereUtilisation: new Date('2026-08-09T18:30:00'),
    matieresConsultees: [
      { matiere: Matiere.MATHEMATIQUES, tempsMinutes: 50, questionsPosees: 18 },
      { matiere: Matiere.PHYSIQUE, tempsMinutes: 35, questionsPosees: 12 },
      { matiere: Matiere.CHIMIE, tempsMinutes: 20, questionsPosees: 7 },
      { matiere: Matiere.SVT, tempsMinutes: 12, questionsPosees: 5 },
      { matiere: Matiere.FRANCAIS, tempsMinutes: 8, questionsPosees: 3 },
    ],
  };

  ngOnInit(): void {
    this.boitierRepo.obtenirBoitierParEnfant('enfant-1').subscribe(b => {
      this.boitier.set(b ?? null);
    });
    this.alerteRepo.obtenirAlertesParent('parent-1').subscribe(a => {
      this.alertes.set(a);
    });
  }

  getStatutClass(statut: StatutBoitier): string {
    return { [StatutBoitier.EN_LIGNE_CLOUD]: 'online', [StatutBoitier.HORS_LIGNE_LOCAL]: 'warning', [StatutBoitier.DECONNECTE]: 'danger' }[statut] ?? '';
  }

  getStatutLabel(statut: StatutBoitier): string {
    return { [StatutBoitier.EN_LIGNE_CLOUD]: 'En ligne', [StatutBoitier.HORS_LIGNE_LOCAL]: 'Hors ligne', [StatutBoitier.DECONNECTE]: 'Déconnecté' }[statut] ?? '';
  }

  formatTemps(minutes: number): string {
    return minutes >= 60 ? `${Math.floor(minutes/60)}h${minutes%60 > 0 ? minutes%60 + 'min' : ''}` : `${minutes}min`;
  }

  getMatiereCouleur(matiere: Matiere): string {
    return MatiereCouleurs[matiere] ?? '#314999';
  }

  getMatiereLabel(matiere: Matiere): string {
    return MatiereLabels[matiere] ?? matiere;
  }

  getStatutSeanceConfig(statut: any) {
    return STATUT_SEANCE_CONFIG[statut as keyof typeof STATUT_SEANCE_CONFIG] ?? STATUT_SEANCE_CONFIG['PROGRAMMÉE'];
  }
}
