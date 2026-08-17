import { Component, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ProgrammeRevisionService } from '../../../core/services/programme-revision.service';
import { SeanceRevision, StatutSeance, STATUT_SEANCE_CONFIG } from '../../../domain/entites/programme-revision.entite';
import { Matiere, MatiereLabels, MatiereCouleurs } from '../../../core/enums';

@Component({
  selector: 'app-programme-revision',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './programme-revision.composant.html',
  styleUrl: './programme-revision.composant.scss',
})
export class ProgrammeRevisionComposant {
  readonly service = inject(ProgrammeRevisionService);

  readonly MatiereLabels = MatiereLabels;
  readonly MatiereCouleurs = MatiereCouleurs;
  readonly STATUT_SEANCE_CONFIG = STATUT_SEANCE_CONFIG;

  // Signaux réactifs du service
  readonly seances = this.service.seancesTriees;
  readonly notifications = this.service.notifications;
  readonly tauxRespectPlanning = this.service.tauxRespectPlanning;
  readonly notificationsNonLuesCount = this.service.notificationsNonLuesCount;

  // Vue courante : 'semaine' | 'agenda' | 'notifications'
  vueCourante = signal<'semaine' | 'agenda' | 'notifications'>('semaine');

  // Filtres
  filtreMatiere = signal<string>('TOUTES');
  filtreStatut = signal<string>('TOUS');

  // Modal création / édition
  modalOuverte = signal<boolean>(false);
  seanceEnEditionId = signal<string | null>(null);

  // Modèle du formulaire
  formTitre = signal<string>('');
  formMatiere = signal<Matiere>(Matiere.MATHEMATIQUES);
  formJour = signal<string>(new Date().toISOString().split('T')[0]);
  formHeureDebut = signal<string>('17:00');
  formHeureFin = signal<string>('17:45');
  formRappelMinutes = signal<number>(30);
  formCommentaire = signal<string>('');

  // Modal report de séance
  modalReportOuverte = signal<boolean>(false);
  seanceAReporter = signal<SeanceRevision | null>(null);
  reportNouvelleDate = signal<string>('');
  reportNouvelleHeureDebut = signal<string>('17:00');
  reportNouvelleHeureFin = signal<string>('17:45');

  // Popover d'action sur séance
  seanceSelectionneePopover = signal<SeanceRevision | null>(null);

  // Liste des matières pour le dropdown
  readonly matieresOptions = Object.keys(MatiereLabels).map(key => ({
    key: key as Matiere,
    label: MatiereLabels[key as Matiere],
  }));

  // Jours de la semaine courante pour la vue calendrier
  readonly joursSemaine = computed(() => {
    const aujourdhui = new Date();
    const curr = new Date(aujourdhui);
    const first = curr.getDate() - curr.getDay() + (curr.getDay() === 0 ? -6 : 1); // Lundi

    const result = [];
    const nomsJours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];

    for (let i = 0; i < 7; i++) {
      const d = new Date(curr.setDate(first + i));
      const dateStr = d.toISOString().split('T')[0];
      const estAujourdhui = dateStr === aujourdhui.toISOString().split('T')[0];
      result.push({
        nom: nomsJours[i],
        dateNum: d.getDate(),
        dateStr,
        estAujourdhui,
      });
    }
    return result;
  });

  // Filtrage des séances
  readonly seancesFiltrees = computed(() => {
    const mat = this.filtreMatiere();
    const stat = this.filtreStatut();

    return this.seances().filter(s => {
      const matchMatiere = mat === 'TOUTES' || s.matiere === mat;
      const matchStatut = stat === 'TOUS' || s.statut === stat;
      return matchMatiere && matchStatut;
    });
  });

  // Obtenir les séances pour une date donnée
  getSeancesPourJour(dateStr: string): SeanceRevision[] {
    return this.seancesFiltrees().filter(s => s.jour === dateStr);
  }

  // Durée calculée du formulaire
  readonly formDureeCalculee = computed(() => {
    const [hDeb, mDeb] = this.formHeureDebut().split(':').map(Number);
    const [hFin, mFin] = this.formHeureFin().split(':').map(Number);
    if (isNaN(hDeb) || isNaN(mDeb) || isNaN(hFin) || isNaN(mFin)) return 45;
    const diff = (hFin * 60 + mFin) - (hDeb * 60 + mDeb);
    return diff > 0 ? diff : 30;
  });

  ouvrirModalCreation(dateOptionnelle?: string): void {
    this.seanceEnEditionId.set(null);
    this.formTitre.set('');
    this.formMatiere.set(Matiere.MATHEMATIQUES);
    this.formJour.set(dateOptionnelle ?? new Date().toISOString().split('T')[0]);
    this.formHeureDebut.set('17:00');
    this.formHeureFin.set('17:45');
    this.formRappelMinutes.set(30);
    this.formCommentaire.set('');
    this.modalOuverte.set(true);
  }

  ouvrirModalEdition(seance: SeanceRevision, event?: Event): void {
    if (event) event.stopPropagation();
    this.seanceEnEditionId.set(seance.id);
    this.formTitre.set(seance.titre);
    this.formMatiere.set(seance.matiere);
    this.formJour.set(seance.jour);
    this.formHeureDebut.set(seance.heureDebut);
    this.formHeureFin.set(seance.heureFin);
    this.formRappelMinutes.set(seance.rappelMinutesAvant ?? 30);
    this.formCommentaire.set(seance.commentaire ?? '');
    this.modalOuverte.set(true);
    this.fermerPopover();
  }

  fermerModal(): void {
    this.modalOuverte.set(false);
  }

  sauvegarderSeance(): void {
    if (!this.formTitre().trim()) return;

    const payload = {
      titre: this.formTitre().trim(),
      matiere: this.formMatiere(),
      jour: this.formJour(),
      heureDebut: this.formHeureDebut(),
      heureFin: this.formHeureFin(),
      dureeMinutes: this.formDureeCalculee(),
      commentaire: this.formCommentaire().trim() || undefined,
      statut: 'PROGRAMMÉE' as StatutSeance,
      rappelMinutesAvant: this.formRappelMinutes(),
    };

    if (this.seanceEnEditionId()) {
      this.service.modifierSeance(this.seanceEnEditionId()!, payload);
    } else {
      this.service.ajouterSeance(payload);
    }

    this.fermerModal();
  }

  supprimerSeance(id: string, event?: Event): void {
    if (event) event.stopPropagation();
    this.service.supprimerSeance(id);
    this.fermerPopover();
  }

  changerStatut(id: string, statut: StatutSeance, event?: Event): void {
    if (event) event.stopPropagation();
    this.service.changerStatutSeance(id, statut);
    this.fermerPopover();
  }

  ouvrirModalReport(seance: SeanceRevision, event?: Event): void {
    if (event) event.stopPropagation();
    this.seanceAReporter.set(seance);
    this.reportNouvelleDate.set(seance.jour);
    this.reportNouvelleHeureDebut.set(seance.heureDebut);
    this.reportNouvelleHeureFin.set(seance.heureFin);
    this.modalReportOuverte.set(true);
    this.fermerPopover();
  }

  fermerModalReport(): void {
    this.modalReportOuverte.set(false);
    this.seanceAReporter.set(null);
  }

  confirmerReport(): void {
    const seance = this.seanceAReporter();
    if (seance && this.reportNouvelleDate()) {
      this.service.reporterSeance(
        seance.id,
        this.reportNouvelleDate(),
        this.reportNouvelleHeureDebut(),
        this.reportNouvelleHeureFin()
      );
    }
    this.fermerModalReport();
  }

  togglePopoverSeance(seance: SeanceRevision, event: Event): void {
    event.stopPropagation();
    if (this.seanceSelectionneePopover()?.id === seance.id) {
      this.seanceSelectionneePopover.set(null);
    } else {
      this.seanceSelectionneePopover.set(seance);
    }
  }

  fermerPopover(): void {
    this.seanceSelectionneePopover.set(null);
  }

  marquerNotifLue(id: string): void {
    this.service.marquerNotificationLue(id);
  }

  toutMarquerNotifLue(): void {
    this.service.toutMarquerNotificationLue();
  }

  formatDateLisible(dateStr: string): string {
    const d = new Date(dateStr);
    return d.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' });
  }
}
