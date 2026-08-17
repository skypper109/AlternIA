import { Component, OnInit, signal, inject, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AvatarRepository } from '../../../data/repositories/avatar.repository';
import { VoixPedagogique } from '../../../domain/entites/avatar-pedagogique.entite';
import { Matiere, MatiereLabels, MatiereCouleurs } from '../../../core/enums';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-studio-vocal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './studio-vocal.composant.html',
  styleUrl: './studio-vocal.composant.scss',
})
export class StudioVocalComposant implements OnInit {
  private readonly repo = inject(AvatarRepository);
  private readonly notifService = inject(NotificationService);

  @ViewChild('fileInputAudio') fileInputAudio?: ElementRef<HTMLInputElement>;

  readonly MatiereLabels = MatiereLabels;
  readonly MatiereCouleurs = MatiereCouleurs;
  readonly matieresList = Object.values(Matiere);

  chargement = signal(true);
  voixList = signal<VoixPedagogique[]>([]);

  // Audio Playback State
  voixEnLecture = signal<VoixPedagogique | null>(null);
  tempsLecture = signal(0);
  private audioTimer: any = null;

  // Modale Création / Clonage
  modalVoixOuverte = signal(false);
  estModeClonage = false;
  voixForm = {
    nom: '',
    description: '',
    genre: 'feminin' as 'feminin' | 'masculin' | 'neutre',
  };
  formAudioFileName = signal<string | null>(null);

  // Modale Association
  voixEnAssociation = signal<VoixPedagogique | null>(null);
  matiereAssociation: Matiere = Matiere.MATHEMATIQUES;

  // Modale Suppression
  voixASupprimer = signal<VoixPedagogique | null>(null);

  ngOnInit(): void {
    this.repo.obtenirToutesVoix().subscribe(v => {
      this.voixList.set(v);
      this.chargement.set(false);
    });
  }

  getLibelleMatiere(matiere: Matiere): string {
    return MatiereLabels[matiere] ?? matiere;
  }

  getCouleurMatiere(matiere: Matiere): string {
    return MatiereCouleurs[matiere] ?? '#314999';
  }

  // Live Audio Playback simulation
  toggleLectureVoix(voix: VoixPedagogique): void {
    if (this.voixEnLecture()?.id === voix.id) {
      this.arreterLecture();
    } else {
      this.lireVoix(voix);
    }
  }

  lireVoix(voix: VoixPedagogique): void {
    this.arreterLecture();
    this.voixEnLecture.set(voix);
    this.tempsLecture.set(0);

    const step = 2.5;
    this.audioTimer = setInterval(() => {
      this.tempsLecture.update(t => {
        if (t >= 100) {
          this.arreterLecture();
          return 0;
        }
        return t + step;
      });
    }, 120);

    this.notifService.info('Studio vocal', `Lecture de la voix de ${voix.nom} en cours…`);
  }

  arreterLecture(): void {
    if (this.audioTimer) {
      clearInterval(this.audioTimer);
      this.audioTimer = null;
    }
    this.voixEnLecture.set(null);
    this.tempsLecture.set(0);
  }

  // Modale Création / Clonage
  ouvrirModalClonage(): void {
    this.estModeClonage = true;
    this.voixForm = { nom: '', description: '', genre: 'feminin' };
    this.formAudioFileName.set(null);
    this.modalVoixOuverte.set(true);
  }

  ouvrirModalAjoutVoix(): void {
    this.estModeClonage = false;
    this.voixForm = { nom: '', description: '', genre: 'feminin' };
    this.formAudioFileName.set(null);
    this.modalVoixOuverte.set(true);
  }

  fermerModalVoix(): void {
    this.modalVoixOuverte.set(false);
  }

  declencherUploadAudio(): void {
    this.fileInputAudio?.nativeElement.click();
  }

  onAudioFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      this.formAudioFileName.set(input.files[0].name);
    }
  }

  supprimerAudioForm(): void {
    this.formAudioFileName.set(null);
  }

  sauvegarderVoix(): void {
    if (!this.voixForm.nom.trim()) {
      this.notifService.erreur('Champ obligatoire', 'Veuillez renseigner le nom de la voix.');
      return;
    }

    const nouvelleVoix: VoixPedagogique = {
      id: 'vx-' + Date.now(),
      nom: this.voixForm.nom,
      description: this.voixForm.description || 'Nouvelle voix générée par synthèse IA',
      langue: 'fr-FR',
      genre: this.voixForm.genre,
      accent: 'Africain francophone',
      actif: true,
      cloneeDepuis: this.estModeClonage ? (this.formAudioFileName() ?? 'Échantillon vocal modèle') : undefined,
      dateCreation: new Date(),
    };

    this.voixList.update(list => [nouvelleVoix, ...list]);
    this.fermerModalVoix();

    if (this.estModeClonage) {
      this.notifService.succes('Clonage vocal terminé', `La voix ${nouvelleVoix.nom} a été clonée et ajoutée au catalogue.`);
    } else {
      this.notifService.succes('Voix ajoutée', `La voix ${nouvelleVoix.nom} a été créée avec succès.`);
    }
  }

  // Modale Association Matière
  ouvrirModalAssociation(voix: VoixPedagogique): void {
    this.voixEnAssociation.set(voix);
    this.matiereAssociation = voix.matiereAssociee ?? Matiere.MATHEMATIQUES;
  }

  fermerModalAssociation(): void {
    this.voixEnAssociation.set(null);
  }

  enregistrerAssociation(): void {
    const v = this.voixEnAssociation();
    if (!v) return;

    this.voixList.update(list => list.map(item => item.id === v.id ? { ...item, matiereAssociee: this.matiereAssociation } : item));
    this.notifService.succes('Association réussie', `La voix ${v.nom} est désormais attribuée à la matière ${MatiereLabels[this.matiereAssociation]}.`);
    this.fermerModalAssociation();
  }

  // Suppression
  confirmerSuppression(voix: VoixPedagogique): void {
    this.voixASupprimer.set(voix);
  }

  annulerSuppression(): void {
    this.voixASupprimer.set(null);
  }

  validerSuppression(): void {
    const toDelete = this.voixASupprimer();
    if (!toDelete) return;

    this.voixList.update(list => list.filter(item => item.id !== toDelete.id));
    this.notifService.succes('Voix supprimée', `La voix ${toDelete.nom} a été supprimée.`);
    this.annulerSuppression();
  }
}
