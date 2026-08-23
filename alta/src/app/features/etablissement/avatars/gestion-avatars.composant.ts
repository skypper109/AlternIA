import {
  Component,
  OnInit,
  AfterViewInit,
  OnDestroy,
  signal,
  inject,
  computed,
  ElementRef,
  ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AvatarRepository, VOIX_DISPONIBLES } from '../../../data/repositories/avatar.repository';
import { AvatarPedagogique, VoixPedagogique } from '../../../domain/entites/avatar-pedagogique.entite';
import { Matiere, MatiereLabels, MatiereCouleurs } from '../../../core/enums';
import { NotificationService } from '../../../core/services/notification.service';
import { AvatarAnimatorService, CanvasAvatarInstance, AvatarState } from '../../../core/services/avatar-animator.service';

@Component({
  selector: 'app-gestion-avatars',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './gestion-avatars.composant.html',
  styleUrl: './gestion-avatars.composant.scss',
})
export class GestionAvatarsComposant implements OnInit, AfterViewInit, OnDestroy {
  private readonly repo = inject(AvatarRepository);
  private readonly notifService = inject(NotificationService);
  private readonly animatorService = inject(AvatarAnimatorService);

  @ViewChild('heroCanvas') heroCanvasRef?: ElementRef<HTMLCanvasElement>;
  @ViewChild('previewCanvas') previewCanvasRef?: ElementRef<HTMLCanvasElement>;
  @ViewChild('fileInputPhoto') fileInputPhoto?: ElementRef<HTMLInputElement>;

  readonly MatiereLabels = MatiereLabels;
  readonly MatiereCouleurs = MatiereCouleurs;
  readonly matieresList = Object.values(Matiere);
  readonly voixDisponibles = VOIX_DISPONIBLES;

  chargement = signal(true);
  avatars = signal<AvatarPedagogique[]>([]);

  // Avatar vedette (actif)
  avatarVedette = computed(() => {
    const list = this.avatars();
    return list.find(a => a.actif) ?? list[0] ?? null;
  });

  // Instances d'animation Canvas 2.5D
  private heroAnimator: CanvasAvatarInstance | null = null;
  private previewAnimator: CanvasAvatarInstance | null = null;

  // Audio Playback & Lip-Sync
  audioEnCours: HTMLAudioElement | null = null;
  avatarEnLecture = signal<string | null>(null);
  etatAnimation = signal<AvatarState>('IDLE');

  // Modale Création / Édition
  modalAvatarOuverte = signal(false);
  isUploadingImage = signal(false);

  avatarForm = {
    nom: '',
    description: 'Bienveillant, rigoureux et interactif',
    matiere: Matiere.SVT,
    voixId: 'vivienne',
    parDefaut: true,
  };
  formImageUrl = signal<string | null>(null);

  avatarASupprimer = signal<AvatarPedagogique | null>(null);

  ngOnInit(): void {
    this.chargerAvatars();
  }

  ngAfterViewInit(): void {
    this.initHeroAnimator();
  }

  ngOnDestroy(): void {
    this.arreterAudio();
    if (this.heroAnimator) this.heroAnimator.destroy();
    if (this.previewAnimator) this.previewAnimator.destroy();
  }

  chargerAvatars(): void {
    this.chargement.set(true);
    this.repo.obtenirTousAvatars().subscribe({
      next: (list) => {
        this.avatars.set(list);
        this.chargement.set(false);
        setTimeout(() => this.updateHeroAvatarImage(), 100);
      },
      error: () => this.chargement.set(false),
    });
  }

  private initHeroAnimator(): void {
    if (!this.heroCanvasRef) return;
    const canvas = this.heroCanvasRef.nativeElement;
    const vedette = this.avatarVedette();
    const color = vedette ? this.getCouleurMatiere(vedette.matiere) : '#40BBCC';

    this.heroAnimator = this.animatorService.createInstance(canvas, {
      themeColor: color,
      enableMouseTracking: true,
    });
    this.updateHeroAvatarImage();
    this.heroAnimator.start();
  }

  private updateHeroAvatarImage(): void {
    const vedette = this.avatarVedette();
    if (vedette && this.heroAnimator) {
      this.heroAnimator.themeColor = this.getCouleurMatiere(vedette.matiere);
      this.heroAnimator.setImage(vedette.imageUrl || 'assets/avatars/vivienne.svg');
    }
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
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return nom.substring(0, 2).toUpperCase();
  }

  setEtatManuel(nouvelEtat: AvatarState): void {
    this.etatAnimation.set(nouvelEtat);
    if (this.heroAnimator) {
      this.heroAnimator.setState(nouvelEtat);
    }
  }

  // --- Lecture Audio & Lip-Sync Test ---
  toggleEcouterAvatar(avatar: AvatarPedagogique, event?: MouseEvent): void {
    if (event) event.stopPropagation();

    if (this.avatarEnLecture() === avatar.id) {
      this.arreterAudio();
    } else {
      this.lancerTestAudio(avatar);
    }
  }

  lancerTestAudio(avatar: AvatarPedagogique): void {
    this.arreterAudio();
    this.avatarEnLecture.set(avatar.id);
    this.setEtatManuel('SPEAKING');

    if (this.heroAnimator) {
      this.heroAnimator.setImage(avatar.imageUrl || 'assets/avatars/vivienne.svg');
      this.heroAnimator.themeColor = this.getCouleurMatiere(avatar.matiere);
    }

    const phrase = `Bonjour ! Je suis ${avatar.nom}. Je t'accompagne dans tes révisions de ${this.getLibelleMatiere(avatar.matiere)} au programme du Mali.`;
    this.repo.testerAudio(phrase, avatar.voixId || 'vivienne').subscribe({
      next: (blob) => {
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);
        this.audioEnCours = audio;

        // Connexion au moteur d'animation
        this.animatorService.connectAudioElement(audio);

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          this.arreterAudio();
        };
        audio.onerror = () => {
          URL.revokeObjectURL(audioUrl);
          this.arreterAudio();
        };
        audio.play().catch(() => this.arreterAudio());
      },
      error: () => {
        this.notifService.erreur('Erreur Audio', 'Impossible de générer la synthèse vocale.');
        this.arreterAudio();
      },
    });
  }

  arreterAudio(): void {
    if (this.audioEnCours) {
      this.audioEnCours.pause();
      this.audioEnCours = null;
    }
    this.avatarEnLecture.set(null);
    this.setEtatManuel('IDLE');
  }

  // --- Activation d'Avatar par Défaut ---
  activerAvatar(avatar: AvatarPedagogique, event?: MouseEvent): void {
    if (event) event.stopPropagation();
    this.repo.activerAvatar(avatar.id).subscribe({
      next: () => {
        this.notifService.succes('Avatar Activé', `${avatar.nom} est désormais l'avatar actif sur les boîtiers.`);
        this.chargerAvatars();
      },
      error: () => this.notifService.erreur('Erreur', "Impossible d'activer l'avatar."),
    });
  }

  // --- Modal Création & Upload ---
  ouvrirModalCreation(): void {
    this.avatarForm = {
      nom: '',
      description: 'Bienveillant, rigoureux et interactif',
      matiere: Matiere.SVT,
      voixId: 'vivienne',
      parDefaut: true,
    };
    this.formImageUrl.set(null);
    this.modalAvatarOuverte.set(true);

    setTimeout(() => {
      if (this.previewCanvasRef && !this.previewAnimator) {
        this.previewAnimator = this.animatorService.createInstance(this.previewCanvasRef.nativeElement, {
          themeColor: '#40BBCC',
        });
        this.previewAnimator.start();
      }
    }, 150);
  }

  fermerModal(): void {
    this.modalAvatarOuverte.set(false);
  }

  declencherUpload(): void {
    this.fileInputPhoto?.nativeElement.click();
  }

  onFichierSelectionne(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    const file = input.files[0];
    this.isUploadingImage.set(true);

    this.repo.uploaderPhotoAvatar(file).subscribe({
      next: (res) => {
        this.isUploadingImage.set(false);
        this.formImageUrl.set(res.photoUrl);
        if (this.previewAnimator) {
          this.previewAnimator.setImage(res.photoUrl);
        }
        this.notifService.succes('Image importée', 'Votre image a été chargée et est prête à être animée.');
      },
      error: () => {
        this.isUploadingImage.set(false);
        this.notifService.erreur('Erreur Upload', "Impossible d'uploader l'image (formats acceptés: PNG, JPG, WEBP, SVG).");
      },
    });
  }

  enregistrerNouvelAvatar(): void {
    if (!this.avatarForm.nom.trim()) {
      this.notifService.erreur('Champs requis', 'Veuillez saisir un nom pour votre enseignant virtuel.');
      return;
    }

    this.repo.creerAvatar({
      nom: this.avatarForm.nom.trim(),
      matiere: this.avatarForm.matiere,
      stylePedagogique: this.avatarForm.description,
      voixTts: this.avatarForm.voixId,
      photoUrl: this.formImageUrl() || undefined,
      parDefaut: this.avatarForm.parDefaut,
    }).subscribe({
      next: (nouveau) => {
        this.notifService.succes('Avatar créé', `${nouveau.nom} a été configuré avec succès.`);
        this.fermerModal();
        this.chargerAvatars();
      },
      error: () => this.notifService.erreur('Erreur', "Impossible de créer l'avatar."),
    });
  }

  // --- Suppression ---
  demanderSuppression(avatar: AvatarPedagogique, event?: MouseEvent): void {
    if (event) event.stopPropagation();
    this.avatarASupprimer.set(avatar);
  }

  confirmerSuppression(): void {
    const target = this.avatarASupprimer();
    if (!target) return;

    this.repo.supprimerAvatar(target.id).subscribe({
      next: () => {
        this.notifService.succes('Avatar supprimé', `${target.nom} a été retiré du catalogue.`);
        this.avatarASupprimer.set(null);
        this.chargerAvatars();
      },
      error: () => this.notifService.erreur('Erreur', "Impossible de supprimer l'avatar."),
    });
  }
}
