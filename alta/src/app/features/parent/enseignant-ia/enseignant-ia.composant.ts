import { Component, inject, signal, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EnseignantIaParentService } from '../../../core/services/enseignant-ia-parent.service';
import { ProfilPedagogique } from '../../../domain/entites/enseignant-ia.entite';
import { AvatarRepository } from '../../../data/repositories/avatar.repository';

@Component({
  selector: 'app-enseignant-ia',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './enseignant-ia.composant.html',
  styleUrl: './enseignant-ia.composant.scss',
})
export class EnseignantIaComposant {
  readonly service = inject(EnseignantIaParentService);

  readonly profils = this.service.profils;
  readonly profilActif = this.service.profilActif;

  // Liste des matières suggérées
  readonly matieresSuggerees: string[] = [
    'Mathématiques',
    'Physique-Chimie',
    'Français',
    'SVT',
    'Histoire-Géographie',
    'Anglais',
    'Philosophie',
    'Économie',
  ];

  // Lecteur audio en cours
  profilEnLecture = signal<string | null>(null);
  tempsLecture = signal<number>(0);
  intervalLecture: ReturnType<typeof setInterval> | null = null;
  private audioElement: HTMLAudioElement | null = null;

  // Modale d'ajout / édition
  modalOuverte = signal<boolean>(false);
  modeEdition = signal<boolean>(false);
  profilEditionId = signal<string | null>(null);

  // Formulaire state
  formNom = signal<string>('');
  formMatiere = signal<string>('');
  formPhotoUrl = signal<string>('');
  formAudioUrl = signal<string>('');
  formAudioFileName = signal<string>('');

  // Modale de confirmation de suppression
  profilASupprimer = signal<ProfilPedagogique | null>(null);

  @ViewChild('fileInputPhoto') fileInputPhoto!: ElementRef<HTMLInputElement>;
  @ViewChild('fileInputAudio') fileInputAudio!: ElementRef<HTMLInputElement>;

  // ── Actions CRUD ──────────────────────────────────────────
  choisirProfil(id: string): void {
    this.service.choisirProfil(id);
  }

  ouvrirModalAjout(): void {
    this.modeEdition.set(false);
    this.profilEditionId.set(null);
    this.formNom.set('');
    this.formMatiere.set(this.matieresSuggerees[0] ?? 'Mathématiques');
    this.formPhotoUrl.set('');
    this.formAudioUrl.set('');
    this.formAudioFileName.set('');
    this.modalOuverte.set(true);
  }

  ouvrirModalEdition(profil: ProfilPedagogique, event?: Event): void {
    if (event) event.stopPropagation();
    this.modeEdition.set(true);
    this.profilEditionId.set(profil.id);
    this.formNom.set(profil.nom);
    this.formMatiere.set(profil.matiere);
    this.formPhotoUrl.set(profil.photoUrl ?? '');
    this.formAudioUrl.set(profil.audioUrl ?? '');
    this.formAudioFileName.set(profil.audioFileName ?? '');
    this.modalOuverte.set(true);
  }

  fermerModal(): void {
    this.modalOuverte.set(false);
  }

  enregistrerFormulaire(): void {
    const nom = this.formNom().trim();
    const matiere = this.formMatiere().trim();

    if (!nom || !matiere) return;

    if (this.modeEdition() && this.profilEditionId()) {
      this.service.modifierProfil(this.profilEditionId()!, {
        nom,
        matiere,
        photoUrl: this.formPhotoUrl(),
        audioUrl: this.formAudioUrl(),
        audioFileName: this.formAudioFileName(),
      });
    } else {
      this.service.ajouterProfil({
        nom,
        matiere,
        photoUrl: this.formPhotoUrl(),
        audioUrl: this.formAudioUrl(),
        audioFileName: this.formAudioFileName(),
      });
    }

    this.fermerModal();
  }

  confirmerSuppression(profil: ProfilPedagogique, event?: Event): void {
    if (event) event.stopPropagation();
    this.profilASupprimer.set(profil);
  }

  annulerSuppression(): void {
    this.profilASupprimer.set(null);
  }

  validerSuppression(): void {
    const p = this.profilASupprimer();
    if (p) {
      if (this.profilEnLecture() === p.id) {
        this.arreterAudio();
      }
      this.service.supprimerProfil(p.id);
      this.profilASupprimer.set(null);
    }
  }

  private readonly avatarRepo = inject(AvatarRepository);

  // ── Gestion Photo ─────────────────────────────────────────
  declencherUploadPhoto(): void {
    this.fileInputPhoto?.nativeElement?.click();
  }

  onPhotoFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      this.avatarRepo.uploaderPhotoAvatar(file).subscribe({
        next: (res) => {
          this.formPhotoUrl.set(res.photoUrl);
        },
        error: () => {
          const reader = new FileReader();
          reader.onload = (e) => {
            const result = e.target?.result as string;
            this.formPhotoUrl.set(result);
          };
          reader.readAsDataURL(file);
        }
      });
    }
  }

  supprimerPhotoForm(): void {
    this.formPhotoUrl.set('');
  }

  // ── Gestion Audio ─────────────────────────────────────────
  declencherUploadAudio(): void {
    this.fileInputAudio?.nativeElement?.click();
  }

  onAudioFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      this.formAudioFileName.set(file.name);
      const reader = new FileReader();
      reader.onload = (e) => {
        const result = e.target?.result as string;
        this.formAudioUrl.set(result);
      };
      reader.readAsDataURL(file);
    }
  }

  supprimerAudioForm(): void {
    this.formAudioUrl.set('');
    this.formAudioFileName.set('');
  }

  // ── Lecteur Audio ─────────────────────────────────────────
  toggleEcouterProfil(profil: ProfilPedagogique, event?: Event): void {
    if (event) event.stopPropagation();

    if (this.profilEnLecture() === profil.id) {
      this.arreterAudio();
    } else {
      this.demarrerAudio(profil);
    }
  }

  private demarrerAudio(profil: ProfilPedagogique): void {
    this.arreterAudio();
    this.profilEnLecture.set(profil.id);
    this.tempsLecture.set(0);

    if (profil.audioUrl) {
      try {
        this.audioElement = new Audio(profil.audioUrl);
        this.audioElement.play();
        this.audioElement.onended = () => this.arreterAudio();
        this.audioElement.ontimeupdate = () => {
          if (this.audioElement && this.audioElement.duration) {
            const percent = (this.audioElement.currentTime / this.audioElement.duration) * 100;
            this.tempsLecture.set(Math.min(100, Math.round(percent)));
          }
        };
        return;
      } catch (e) {
        console.warn('Fallback lecture audio simulée');
      }
    }

    // Simulation de lecture si pas d’élément audio physique
    this.intervalLecture = setInterval(() => {
      this.tempsLecture.update(t => {
        if (t >= 100) {
          this.arreterAudio();
          return 0;
        }
        return t + 4;
      });
    }, 200);
  }

  private arreterAudio(): void {
    if (this.audioElement) {
      this.audioElement.pause();
      this.audioElement = null;
    }
    if (this.intervalLecture) {
      clearInterval(this.intervalLecture);
      this.intervalLecture = null;
    }
    this.profilEnLecture.set(null);
    this.tempsLecture.set(0);
  }

  // ── Utilitaires ───────────────────────────────────────────
  getInitiales(nom: string): string {
    if (!nom) return 'P';
    const parts = nom.replace(/Professeur|Professeure|Prof\./gi, '').trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return nom.substring(0, 2).toUpperCase();
  }

  getCouleurMatiere(matiere: string): string {
    const colors: Record<string, string> = {
      'Mathématiques': '#314999',
      'Physique-Chimie': '#40BBCC',
      'Français': '#F1851F',
      'SVT': '#10B981',
      'Histoire-Géographie': '#8B5CF6',
      'Anglais': '#EC4899',
      'Philosophie': '#6366F1',
      'Économie': '#F59E0B',
    };
    return colors[matiere] ?? '#314999';
  }

  getIconMatiere(matiere: string): string {
    const icons: Record<string, string> = {
      'Mathématiques': 'calculator',
      'Physique-Chimie': 'flask',
      'Français': 'book',
      'SVT': 'leaf',
      'Histoire-Géographie': 'globe',
      'Anglais': 'mic',
      'Philosophie': 'lightbulb',
      'Économie': 'trending-up',
    };
    return icons[matiere] ?? 'book';
  }
}
