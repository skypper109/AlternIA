import { Component, OnInit, signal, inject, computed, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AvatarRepository } from '../../../data/repositories/avatar.repository';
import { AvatarPedagogique } from '../../../domain/entites/avatar-pedagogique.entite';
import { Matiere, MatiereLabels, MatiereCouleurs, CategorieMatiere } from '../../../core/enums';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-gestion-avatars',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './gestion-avatars.composant.html',
  styleUrl: './gestion-avatars.composant.scss',
})
export class GestionAvatarsComposant implements OnInit {
  private readonly repo = inject(AvatarRepository);
  private readonly notifService = inject(NotificationService);

  @ViewChild('fileInputPhoto') fileInputPhoto?: ElementRef<HTMLInputElement>;

  readonly MatiereLabels = MatiereLabels;
  readonly MatiereCouleurs = MatiereCouleurs;
  readonly matieresList = Object.values(Matiere);

  chargement = signal(true);
  avatars = signal<AvatarPedagogique[]>([]);

  // Avatar vedette pour la bannière Hero
  avatarVedette = computed(() => {
    const list = this.avatars();
    return list.find(a => a.actif) ?? list[0] ?? null;
  });

  // Audio Playback State
  avatarEnLecture = signal<string | null>(null);
  tempsLecture = signal(0);
  private audioTimer: any = null;

  // Modales State
  modalAvatarOuverte = signal(false);
  avatarEnEdition: AvatarPedagogique | null = null;
  avatarForm = {
    nom: '',
    description: '',
    matiere: Matiere.MATHEMATIQUES,
    personnalite: '',
  };
  formImageUrl = signal<string | null>(null);

  avatarEnTest = signal<AvatarPedagogique | null>(null);
  avatarASupprimer = signal<AvatarPedagogique | null>(null);

  ngOnInit(): void {
    this.repo.obtenirTousAvatars().subscribe(a => {
      this.avatars.set(a);
      this.chargement.set(false);
    });
  }

  getLibelleMatiere(matiere: Matiere): string {
    return MatiereLabels[matiere] ?? matiere;
  }

  getCouleurMatiere(matiere: Matiere): string {
    return MatiereCouleurs[matiere] ?? '#314999';
  }

  getInitiales(nom: string): string {
    if (!nom) return 'A';
    const parts = nom.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return nom.substring(0, 2).toUpperCase();
  }

  // Audio Playback simulation
  toggleEcouterAvatar(avatar: AvatarPedagogique, event?: MouseEvent): void {
    if (event) event.stopPropagation();

    if (this.avatarEnLecture() === avatar.id) {
      this.arreterLectureAudio();
    } else {
      this.lancerLectureAudio(avatar);
    }
  }

  private lancerLectureAudio(avatar: AvatarPedagogique): void {
    this.arreterLectureAudio();
    this.avatarEnLecture.set(avatar.id);
    this.tempsLecture.set(0);

    const step = 2;
    this.audioTimer = setInterval(() => {
      this.tempsLecture.update(t => {
        if (t >= 100) {
          this.arreterLectureAudio();
          return 0;
        }
        return t + step;
      });
    }, 120);

    this.notifService.info('Extrait sonore', `Écoute de l'extrait vocal de ${avatar.nom}`);
  }

  private arreterLectureAudio(): void {
    if (this.audioTimer) {
      clearInterval(this.audioTimer);
      this.audioTimer = null;
    }
    this.avatarEnLecture.set(null);
    this.tempsLecture.set(0);
  }

  // Statut Actif / Inactif
  basculerStatut(avatar: AvatarPedagogique, event?: MouseEvent): void {
    if (event) event.stopPropagation();
    const nouveauStatut = !avatar.actif;
    this.avatars.update(list => list.map(a => a.id === avatar.id ? { ...a, actif: nouveauStatut } : a));
    this.notifService.succes('Statut mis à jour', `Avatar "${avatar.nom}" est désormais ${nouveauStatut ? 'Actif' : 'Inactif'}.`);
  }

  // Modale Création / Édition
  ouvrirModalCreation(): void {
    this.avatarEnEdition = null;
    this.avatarForm = {
      nom: '',
      description: '',
      matiere: Matiere.MATHEMATIQUES,
      personnalite: 'Enthousiaste, pédagogique',
    };
    this.formImageUrl.set(null);
    this.modalAvatarOuverte.set(true);
  }

  ouvrirModalEdition(avatar: AvatarPedagogique): void {
    this.avatarEnEdition = avatar;
    this.avatarForm = {
      nom: avatar.nom,
      description: avatar.description,
      matiere: avatar.matiere,
      personnalite: avatar.personnalite,
    };
    this.formImageUrl.set(avatar.imageUrl ?? null);
    this.modalAvatarOuverte.set(true);
  }

  fermerModalAvatar(): void {
    this.modalAvatarOuverte.set(false);
  }

  declencherUploadPhoto(): void {
    this.fileInputPhoto?.nativeElement.click();
  }

  onPhotoFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      const reader = new FileReader();
      reader.onload = (e) => {
        this.formImageUrl.set(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  }

  supprimerPhotoForm(): void {
    this.formImageUrl.set(null);
  }

  sauvegarderAvatar(): void {
    if (!this.avatarForm.nom.trim() || !this.avatarForm.description.trim()) {
      this.notifService.erreur('Formulaire incomplet', 'Veuillez saisir un nom et une description.');
      return;
    }

    if (this.avatarEnEdition) {
      const updatedNom = this.avatarForm.nom;
      this.avatars.update(list => list.map(a => a.id === this.avatarEnEdition!.id ? {
        ...a,
        nom: updatedNom,
        description: this.avatarForm.description,
        matiere: this.avatarForm.matiere,
        personnalite: this.avatarForm.personnalite,
        imageUrl: this.formImageUrl() ?? undefined,
      } : a));
      this.notifService.succes('Avatar modifié', `L'avatar ${updatedNom} a été mis à jour.`);
    } else {
      const nouvel: AvatarPedagogique = {
        id: 'av-' + Date.now(),
        nom: this.avatarForm.nom,
        description: this.avatarForm.description,
        matiere: this.avatarForm.matiere,
        categorie: CategorieMatiere.SCIENTIFIQUE,
        personnalite: this.avatarForm.personnalite || 'Enthousiaste, pédagogique',
        imageUrl: this.formImageUrl() ?? undefined,
        actif: true,
        dateCreation: new Date(),
        utilisations: 0,
      };
      this.avatars.update(list => [nouvel, ...list]);
      this.notifService.succes('Avatar créé', `L'avatar ${nouvel.nom} a été créé avec succès.`);
    }

    this.fermerModalAvatar();
  }

  // Modale Aperçu / Test Live
  testerAvatar(avatar: AvatarPedagogique): void {
    this.avatarEnTest.set(avatar);
    this.notifService.info('Démonstration', `Démonstration vocale en direct de l'avatar ${avatar.nom}`);
  }

  fermerTest(): void {
    this.avatarEnTest.set(null);
  }

  // Suppression
  confirmerSuppression(avatar: AvatarPedagogique): void {
    this.avatarASupprimer.set(avatar);
  }

  annulerSuppression(): void {
    this.avatarASupprimer.set(null);
  }

  validerSuppression(): void {
    const toDelete = this.avatarASupprimer();
    if (!toDelete) return;

    this.avatars.update(list => list.filter(a => a.id !== toDelete.id));
    this.notifService.succes('Avatar supprimé', `L'avatar ${toDelete.nom} a été supprimé.`);
    this.annulerSuppression();
  }
}
