import {
  Component,
  OnInit,
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
import { AvatarPedagogique } from '../../../domain/entites/avatar-pedagogique.entite';
import { Matiere, MatiereLabels, MatiereCouleurs } from '../../../core/enums';
import { NotificationService } from '../../../core/services/notification.service';
import { AvatarAnimatorService, CanvasAvatarInstance, AvatarState, VISEME_IDS, VisemeId } from '../../../core/services/avatar-animator.service';

@Component({
  selector: 'app-gestion-avatars',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './gestion-avatars.composant.html',
  styleUrl: './gestion-avatars.composant.scss',
})
export class GestionAvatarsComposant implements OnInit, OnDestroy {
  private readonly repo = inject(AvatarRepository);
  private readonly notifService = inject(NotificationService);
  private readonly animatorService = inject(AvatarAnimatorService);

  private heroCanvasEl?: HTMLCanvasElement;
  private previewCanvasEl?: HTMLCanvasElement;

  @ViewChild('fileInputViseme') fileInputViseme?: ElementRef<HTMLInputElement>;

  // Setter réactif pour le Canvas Hero (garantit l'initialisation dès le rendu DOM)
  @ViewChild('heroCanvas') set heroCanvas(canvasRef: ElementRef<HTMLCanvasElement> | undefined) {
    if (canvasRef && canvasRef.nativeElement !== this.heroCanvasEl) {
      this.heroCanvasEl = canvasRef.nativeElement;
      this.initHeroAnimator(canvasRef.nativeElement);
    }
  }

  // Setter réactif pour le Canvas Preview dans la modale
  @ViewChild('previewCanvas') set previewCanvas(canvasRef: ElementRef<HTMLCanvasElement> | undefined) {
    if (canvasRef && canvasRef.nativeElement !== this.previewCanvasEl) {
      this.previewCanvasEl = canvasRef.nativeElement;
      this.initPreviewAnimator(canvasRef.nativeElement);
    }
  }

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
  heroAnimator: CanvasAvatarInstance | null = null;
  previewAnimator: CanvasAvatarInstance | null = null;

  // Audio Playback & Lip-Sync
  audioEnCours: HTMLAudioElement | null = null;
  avatarEnLecture = signal<string | null>(null);
  etatAnimation = signal<AvatarState>('IDLE');

  // Modale Création / Édition
  modalAvatarOuverte = signal(false);
  isUploadingImage = signal(false);
  isUploadingPhoto = signal(false);
  @ViewChild('fileInputPhoto') fileInputPhoto?: ElementRef<HTMLInputElement>;
  diagnosticCompatibilite = signal<any>(null);
  landmarksDetectes = signal<any>(null);
  testPreviewAudioEnCours = signal(false);
  previewAudioEl: HTMLAudioElement | null = null;

  // Wizard Visème Sprite-Sheet
  readonly VISEME_IDS = VISEME_IDS;
  readonly visemeLabels: Record<string, { label: string; instruction: string; emoji: string }> = {
    REST: { label: 'Repos', instruction: 'Bouche naturelle, détendue, regard droit', emoji: '😐' },
    CLOSED: { label: 'Fermée', instruction: 'Lèvres fermées, comme pour dire "Mmm"', emoji: '😶' },
    OPEN_SMALL: { label: 'Petite ouverture', instruction: 'Bouche légèrement ouverte, comme pour dire "E"', emoji: '😊' },
    OPEN_WIDE: { label: 'Grande ouverture', instruction: 'Bouche bien ouverte, comme pour dire "Ahh"', emoji: '😮' },
    ROUND_O: { label: 'Arrondie O', instruction: 'Lèvres arrondies en O, comme pour dire "Oh"', emoji: '😯' },
    ROUND_U: { label: 'Arrondie U', instruction: 'Lèvres en cul-de-poule, comme pour dire "Ou"', emoji: '😗' },
    TEETH: { label: 'Dents visibles', instruction: 'Dents visibles, sourire léger, comme pour dire "Si"', emoji: '😬' },
    SMILE: { label: 'Sourire', instruction: 'Sourire naturel, bouche légèrement ouverte', emoji: '😄' },
  };
  visemePhotosMap = signal<Record<string, string>>({});
  visemeCurrentStep = signal(0);
  isUploadingViseme = signal(false);

  avatarForm = {
    nom: '',
    description: 'Bienveillant, rigoureux et interactif',
    matiere: Matiere.SVT,
    voixId: 'vivienne',
    parDefaut: true,
  };
  formImageUrl = signal<string | null>(null);
  formVideoUrl = signal<string | null>(null);
  isGeneratingVideo = signal(false);

  avatarASupprimer = signal<AvatarPedagogique | null>(null);

  declencherUploadPhoto(): void {
    this.fileInputPhoto?.nativeElement.click();
  }

  onPhotoAvatarSelectionnee(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    const file = input.files[0];
    this.isUploadingPhoto.set(true);

    this.repo.uploaderPhotoAvatar(file).subscribe({
      next: (res) => {
        this.isUploadingPhoto.set(false);
        this.formImageUrl.set(res.photoUrl);
        if (res.compatibility) {
          this.diagnosticCompatibilite.set(res.compatibility);
        }
        if (res.landmarks) {
          this.landmarksDetectes.set(res.landmarks);
        }
        if (res.visemePhotos && Object.keys(res.visemePhotos).length > 0) {
          this.visemePhotosMap.set(res.visemePhotos);
          if (this.previewAnimator) {
            this.previewAnimator.setVisemePhotos(res.visemePhotos);
          }
        } else if (this.previewAnimator) {
          this.previewAnimator.setImage(res.photoUrl);
        }
        this.notifService.succes('Photo Uploadée', "L'image et ses mimiques labiales ont été générées avec succès.");
        input.value = '';
      },
      error: () => {
        this.isUploadingPhoto.set(false);
        this.notifService.erreur('Erreur Upload', "Impossible d'uploader la photo.");
        input.value = '';
      },
    });
  }

  ngOnInit(): void {
    this.chargerAvatars();
  }

  ngOnDestroy(): void {
    this.arreterAudio();
    this.arreterTestPreviewModal();
    if (this.heroAnimator) this.heroAnimator.destroy();
    if (this.previewAnimator) this.previewAnimator.destroy();
  }

  chargerAvatars(): void {
    this.chargement.set(true);
    this.repo.obtenirTousAvatars().subscribe({
      next: (list) => {
        this.avatars.set(list);
        this.chargement.set(false);
        this.updateHeroAvatarImage();
      },
      error: () => this.chargement.set(false),
    });
  }

  private initHeroAnimator(canvas: HTMLCanvasElement): void {
    if (this.heroAnimator) {
      this.heroAnimator.destroy();
    }
    const vedette = this.avatarVedette();
    const color = vedette ? this.getCouleurMatiere(vedette.matiere) : '#40BBCC';

    this.heroAnimator = this.animatorService.createInstance(canvas, {
      themeColor: color,
      enableMouseTracking: true,
    });

    if (vedette) {
      this.heroAnimator.setImage(vedette.imageUrl || 'assets/avatars/vivienne.svg');
      // Charger les photos de visèmes si disponibles
      if (vedette.visemePhotos && Object.keys(vedette.visemePhotos).length > 0) {
        this.heroAnimator.setVisemePhotos(vedette.visemePhotos);
      }
    }
    this.heroAnimator.start();
  }

  private initPreviewAnimator(canvas: HTMLCanvasElement): void {
    if (this.previewAnimator) {
      this.previewAnimator.destroy();
    }
    this.previewAnimator = this.animatorService.createInstance(canvas, {
      themeColor: '#40BBCC',
      enableMouseTracking: false,
    });
    const visemes = this.visemePhotosMap();
    if (Object.keys(visemes).length > 0) {
      this.previewAnimator.setVisemePhotos(visemes);
    } else if (this.formImageUrl()) {
      this.previewAnimator.setImage(this.formImageUrl()!);
    }
    this.previewAnimator.start();
  }

  private updateHeroAvatarImage(): void {
    const vedette = this.avatarVedette();
    if (vedette && this.heroAnimator) {
      this.heroAnimator.themeColor = this.getCouleurMatiere(vedette.matiere);
      this.heroAnimator.setImage(vedette.imageUrl || 'assets/avatars/vivienne.svg');
      if (vedette.visemePhotos && Object.keys(vedette.visemePhotos).length > 0) {
        this.heroAnimator.setVisemePhotos(vedette.visemePhotos);
      }
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
      if (avatar.visemePhotos && Object.keys(avatar.visemePhotos).length > 0) {
        this.heroAnimator.setVisemePhotos(avatar.visemePhotos);
      }
      this.heroAnimator.themeColor = this.getCouleurMatiere(avatar.matiere);
      this.heroAnimator.setState('SPEAKING');
    }

    const phrase = `Bonjour ! Je suis ${avatar.nom}. Je t'accompagne dans tes révisions de ${this.getLibelleMatiere(avatar.matiere)} au programme du lycée malien.`;
    this.repo.testerAudio(phrase, avatar.voixId || 'vivienne').subscribe({
      next: (blob) => {
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);
        this.audioEnCours = audio;

        this.animatorService.connectAudioElement(audio);

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          this.arreterAudio();
        };
        audio.onerror = () => {
          URL.revokeObjectURL(audioUrl);
          this.arreterAudio();
        };
        audio.play().catch((err) => {
          console.warn("Autoplay audio blocked:", err);
          this.arreterAudio();
        });
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

  // --- Test de Prévisualisation dans la Modale ---
  toggleTestPreviewModal(): void {
    if (this.testPreviewAudioEnCours()) {
      this.arreterTestPreviewModal();
    } else {
      this.lancerTestPreviewModal();
    }
  }

  lancerTestPreviewModal(): void {
    this.arreterTestPreviewModal();
    if (!this.previewAnimator) return;

    this.testPreviewAudioEnCours.set(true);
    this.previewAnimator.setState('SPEAKING');

    const phrase = `Test de calibration faciale pour ${this.avatarForm.nom || 'mon avatar'}. La synchronisation labiale et la déformation 2.5D sont actives.`;
    this.repo.testerAudio(phrase, this.avatarForm.voixId || 'vivienne').subscribe({
      next: (blob) => {
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);
        this.previewAudioEl = audio;

        this.animatorService.connectAudioElement(audio);

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          this.arreterTestPreviewModal();
        };
        audio.onerror = () => {
          URL.revokeObjectURL(audioUrl);
          this.arreterTestPreviewModal();
        };
        audio.play().catch(() => this.arreterTestPreviewModal());
      },
      error: () => this.arreterTestPreviewModal(),
    });
  }

  arreterTestPreviewModal(): void {
    if (this.previewAudioEl) {
      this.previewAudioEl.pause();
      this.previewAudioEl = null;
    }
    this.testPreviewAudioEnCours.set(false);
    if (this.previewAnimator) {
      this.previewAnimator.setState('IDLE');
    }
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
    this.diagnosticCompatibilite.set(null);
    this.landmarksDetectes.set(null);
    this.visemePhotosMap.set({});
    this.visemeCurrentStep.set(0);
    this.modalAvatarOuverte.set(true);
  }

  fermerModal(): void {
    this.arreterTestPreviewModal();
    this.modalAvatarOuverte.set(false);
  }


  // --- Wizard Visème Sprite-Sheet ---
  get currentVisemeId(): string {
    return VISEME_IDS[this.visemeCurrentStep()] || 'REST';
  }

  get currentVisemeInfo() {
    return this.visemeLabels[this.currentVisemeId];
  }

  get visemeProgress(): number {
    return Object.keys(this.visemePhotosMap()).length;
  }

  declencherUploadViseme(): void {
    this.fileInputViseme?.nativeElement.click();
  }

  onVisemeFichierSelectionne(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    const file = input.files[0];
    const visemeId = this.currentVisemeId;
    this.isUploadingViseme.set(true);

    this.repo.uploaderVisemePhoto(file, visemeId).subscribe({
      next: (res) => {
        this.isUploadingViseme.set(false);
        const current = { ...this.visemePhotosMap() };
        current[visemeId] = res.photoUrl;
        this.visemePhotosMap.set(current);

        // Si c'est la première photo (REST), l'utiliser comme photo principale aussi
        if (visemeId === 'REST' && !this.formImageUrl()) {
          this.formImageUrl.set(res.photoUrl);
        }

        // Mettre à jour le preview animator avec les visèmes disponibles
        if (this.previewAnimator) {
          this.previewAnimator.setVisemePhotos(current);
        }

        // Passer au visème suivant
        const nextStep = this.visemeCurrentStep() + 1;
        if (nextStep < VISEME_IDS.length) {
          this.visemeCurrentStep.set(nextStep);
        }

        this.notifService.succes('Photo capturée', `Visème "${this.visemeLabels[visemeId].label}" enregistré (${Object.keys(current).length}/${VISEME_IDS.length}).`);

        // Reset l'input
        input.value = '';
      },
      error: () => {
        this.isUploadingViseme.set(false);
        this.notifService.erreur('Erreur Upload', "Impossible d'uploader la photo de visème.");
        input.value = '';
      },
    });
  }

  allerVisemeStep(index: number): void {
    if (index >= 0 && index < VISEME_IDS.length) {
      this.visemeCurrentStep.set(index);
    }
  }

  // --- Génération Vidéo LivePortrait IA ---
  genererVideoLivePortrait(): void {
    if (!this.formImageUrl()) {
      this.notifService.avertissement('Photo requise', 'Veuillez d\'abord uploader une photo du professeur.');
      return;
    }
    this.isGeneratingVideo.set(true);
    const phrase = `Bonjour ! Je suis ${this.avatarForm.nom || 'ton professeur'}. Je suis prêt à t'expliquer toutes les notions de ${this.getLibelleMatiere(this.avatarForm.matiere)}.`;
    this.repo.genererVideoAvatar({
      photoUrl: this.formImageUrl()!,
      phrase: phrase,
      voice: this.avatarForm.voixId || 'vivienne'
    }).subscribe({
      next: (res) => {
        this.isGeneratingVideo.set(false);
        if (res.video_url) {
          this.formVideoUrl.set(res.video_url);
          this.notifService.succes('Vidéo IA Générée', 'La vidéo LivePortrait a été générée avec succès !');
        }
      },
      error: () => {
        this.isGeneratingVideo.set(false);
        this.notifService.erreur('Génération Vidéo', 'Impossible de générer la vidéo LivePortrait.');
      }
    });
  }

  enregistrerNouvelAvatar(): void {
    if (!this.avatarForm.nom.trim()) {
      this.notifService.erreur('Champs requis', 'Veuillez saisir un nom pour votre enseignant virtuel.');
      return;
    }

    const visemes = this.visemePhotosMap();
    const hasVisemes = Object.keys(visemes).length > 0;

    this.repo.creerAvatar({
      nom: this.avatarForm.nom.trim(),
      matiere: this.avatarForm.matiere,
      stylePedagogique: this.avatarForm.description,
      voixTts: this.avatarForm.voixId,
      photoUrl: this.formImageUrl() || (hasVisemes ? visemes['REST'] : undefined),
      videoUrl: this.formVideoUrl() || undefined,
      parDefaut: this.avatarForm.parDefaut,
      landmarks: this.landmarksDetectes(),
      visemePhotos: hasVisemes ? visemes : undefined,
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
