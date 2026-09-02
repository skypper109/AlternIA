import { Injectable, NgZone, inject } from '@angular/core';

export type AvatarState = 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING';

/**
 * Les 8 visèmes standard pour l'animation Sprite-Sheet.
 * Chaque visème correspond à une position de bouche photographiée.
 */
export const VISEME_IDS = ['REST', 'CLOSED', 'OPEN_SMALL', 'OPEN_WIDE', 'ROUND_O', 'ROUND_U', 'TEETH', 'SMILE'] as const;
export type VisemeId = typeof VISEME_IDS[number];

export interface AvatarAnimOptions {
  themeColor?: string;
  glowIntensity?: number;
  enableMouseTracking?: boolean;
}

@Injectable({ providedIn: 'root' })
export class AvatarAnimatorService {
  private readonly ngZone = inject(NgZone);

  private audioCtx: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private audioSource: MediaElementAudioSourceNode | null = null;
  private currentAudioElement: HTMLAudioElement | null = null;
  private dataArray: Uint8Array<ArrayBuffer> | null = null;

  createInstance(canvas: HTMLCanvasElement, options: AvatarAnimOptions = {}) {
    return new CanvasAvatarInstance(canvas, this, options, this.ngZone);
  }

  getAudioContext(): AudioContext {
    if (!this.audioCtx) {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      this.audioCtx = new AudioContextClass();
    }
    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
    return this.audioCtx;
  }

  connectAudioElement(audio: HTMLAudioElement): AnalyserNode {
    const ctx = this.getAudioContext();
    if (!this.analyser) {
      this.analyser = ctx.createAnalyser();
      this.analyser.fftSize = 256;
      this.analyser.smoothingTimeConstant = 0.8;
      this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
    }

    if (this.currentAudioElement !== audio) {
      try {
        if (ctx.state === 'suspended') {
          ctx.resume();
        }
        this.audioSource = ctx.createMediaElementSource(audio);
        this.audioSource.connect(this.analyser);
        this.analyser.connect(ctx.destination);
        this.currentAudioElement = audio;
      } catch (e) {
        // Déjà connecté
      }
    }
    return this.analyser;
  }

  getAudioEnergy(): { volume: number; bass: number; mid: number; high: number } {
    if (!this.analyser || !this.dataArray) {
      return { volume: 0, bass: 0, mid: 0, high: 0 };
    }

    try {
      this.analyser.getByteFrequencyData(this.dataArray);
    } catch {
      return { volume: 0, bass: 0, mid: 0, high: 0 };
    }

    let sum = 0;
    let bass = 0;
    let mid = 0;
    let high = 0;

    const len = this.dataArray.length;
    for (let i = 0; i < len; i++) {
      const v = this.dataArray[i];
      sum += v;
      if (i < len * 0.25) bass += v;
      else if (i < len * 0.65) mid += v;
      else high += v;
    }

    return {
      volume: sum / (len * 255),
      bass: bass / (len * 0.25 * 255),
      mid: mid / (len * 0.4 * 255),
      high: high / (len * 0.35 * 255),
    };
  }
}

/**
 * Moteur de rendu Canvas 2.5D avec Cross-Fade Visème Sprite-Sheet.
 *
 * Au lieu de dessiner des formes vectorielles par-dessus la photo,
 * ce moteur charge 8 photos correspondant à 8 positions de bouche différentes
 * et effectue un cross-fade fluide entre elles au rythme de l'audio TTS.
 *
 * Les animations de qualité sont conservées :
 * - Respiration naturelle
 * - Parallax 2.5D (suivi souris)
 * - Clignements des yeux naturels
 * - Halo audio-réactif circulaire
 * - Anneau lumineux
 */
export class CanvasAvatarInstance {
  private ctx: CanvasRenderingContext2D;

  // Image principale (fallback si pas de visèmes)
  private image: HTMLImageElement | null = null;
  private isLoaded = false;

  // Sprite-Sheet Visème : 8 images pré-chargées
  private visemeImages: Map<VisemeId, HTMLImageElement> = new Map();
  private visemeLoadedCount = 0;
  private hasVisemes = false;

  // Visème courant et cible pour le cross-fade
  private currentViseme: VisemeId = 'REST';
  private targetViseme: VisemeId = 'REST';
  private crossFadeProgress = 1.0; // 1.0 = transition terminée
  private crossFadeSpeed = 0.18;   // Vitesse du cross-fade (plus haut = plus rapide)

  private animFrameId: number | null = null;
  private state: AvatarState = 'IDLE';
  private time = 0;

  // Dynamique de la Tête (3D Pose & Saccades)
  private headPitch = 0;
  private headYaw = 0;
  private headRoll = 0;
  private targetPitch = 0;
  private targetYaw = 0;
  private targetRoll = 0;

  // Suivi de la souris
  private mouseX = 0;
  private mouseY = 0;

  // Clignements
  private blinkTimer = 0;
  private nextBlink = 3000;
  private blinkProgress = 0;
  private isBlinking = false;

  // Lip-Sync dynamique
  private mouthOpenness = 0; // 0-1, piloté par l'énergie audio

  // Respiration
  private breathCycle = 0;

  themeColor = '#314999';

  constructor(
    private canvas: HTMLCanvasElement,
    private service: AvatarAnimatorService,
    private options: AvatarAnimOptions,
    private ngZone: NgZone
  ) {
    this.ctx = canvas.getContext('2d', { alpha: true })!;
    if (options.themeColor) this.themeColor = options.themeColor;

    if (options.enableMouseTracking !== false) {
      this.initMouseTracking();
    }
  }

  private initMouseTracking() {
    window.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      this.mouseX = Math.max(-1, Math.min(1, (e.clientX - cx) / (window.innerWidth / 2)));
      this.mouseY = Math.max(-1, Math.min(1, (e.clientY - cy) / (window.innerHeight / 2)));
    });
  }

  /**
   * Charge une image principale (utilisée si pas de visèmes disponibles).
   */
  setImage(imageUrl: string) {
    if (!imageUrl) return;
    this.isLoaded = false;
    const img = new Image();
    if (imageUrl.startsWith('http')) {
      img.crossOrigin = 'anonymous';
    }
    img.src = imageUrl;
    img.onload = () => {
      this.image = img;
      this.isLoaded = true;
    };
    img.onerror = () => {
      const fallback = new Image();
      fallback.src = imageUrl;
      fallback.onload = () => {
        this.image = fallback;
        this.isLoaded = true;
      };
    };
  }

  /**
   * Charge les photos de visèmes pour l'animation Sprite-Sheet.
   * @param visemePhotos Record<string, string> — { "REST": "/api/avatars/images/xxx.jpg", ... }
   */
  setVisemePhotos(visemePhotos: Record<string, string>) {
    if (!visemePhotos || Object.keys(visemePhotos).length === 0) {
      this.hasVisemes = false;
      return;
    }

    this.visemeImages.clear();
    this.visemeLoadedCount = 0;
    const totalToLoad = Object.keys(visemePhotos).length;

    for (const [visemeId, url] of Object.entries(visemePhotos)) {
      const img = new Image();
      if (url.startsWith('http')) {
        img.crossOrigin = 'anonymous';
      }
      img.src = url;
      img.onload = () => {
        this.visemeImages.set(visemeId as VisemeId, img);
        this.visemeLoadedCount++;
        if (this.visemeLoadedCount >= totalToLoad) {
          this.hasVisemes = true;
          // Utiliser REST comme image principale de fallback
          const restImg = this.visemeImages.get('REST');
          if (restImg) {
            this.image = restImg;
            this.isLoaded = true;
          }
        }
      };
    }
  }


  setState(newState: AvatarState) {
    this.state = newState;
  }

  start() {
    if (this.animFrameId) return;
    this.ngZone.runOutsideAngular(() => {
      const loop = (timestamp: number) => {
        this.render(timestamp);
        this.animFrameId = requestAnimationFrame(loop);
      };
      this.animFrameId = requestAnimationFrame(loop);
    });
  }

  stop() {
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
  }

  destroy() {
    this.stop();
  }

  /**
   * Détermine le visème cible basé sur l'énergie audio en temps réel.
   * Mapping : énergie vocale + fréquences → position de bouche la plus probable.
   */
  private determineVisemeFromAudio(audio: { volume: number; bass: number; mid: number; high: number }): VisemeId {
    const { volume, bass, mid, high } = audio;

    if (volume < 0.015) return 'REST';

    // Forte ouverture (voyelles ouvertes A, AH)
    if (volume > 0.35 && bass > 0.3) return 'OPEN_WIDE';

    // Bouche arrondie (O, AU) — basses dominantes
    if (bass > 0.35 && mid < 0.25) return 'ROUND_O';

    // Bouche en U (OU, U) — basses très dominantes, peu de hauts
    if (bass > 0.4 && high < 0.15) return 'ROUND_U';

    // Consonnes sifflantes (S, Z, CH) — hautes fréquences dominantes
    if (high > 0.3 && volume > 0.1) return 'TEETH';

    // Ouverture moyenne (E, È, I)
    if (volume > 0.15 && mid > 0.2) return 'OPEN_SMALL';

    // Lèvres fermées (B, P, M) — volume très bas mais présent
    if (volume > 0.05 && volume < 0.15) return 'CLOSED';

    // Sourire / transition
    if (mid > 0.25 && high > 0.2) return 'SMILE';

    return 'OPEN_SMALL';
  }

  private render(timestamp: number) {
    const { width, height } = this.canvas;
    this.ctx.clearRect(0, 0, width, height);

    const delta = timestamp - (this.time || timestamp);
    this.time = timestamp;
    this.breathCycle += delta * 0.0018;

    // 1. Analyse audio & Énergie vocale
    const audio = this.service.getAudioEnergy();
    let speechEnergy = 0;

    if (this.state === 'SPEAKING' || audio.volume > 0.012) {
      speechEnergy = (this.state === 'SPEAKING' && audio.volume <= 0.012)
        ? Math.abs(Math.sin(timestamp * 0.015)) * 0.6
        : audio.volume * 3.0;

      // Déterminer le visème cible
      if (this.hasVisemes) {
        const newViseme = this.determineVisemeFromAudio(audio);
        if (newViseme !== this.targetViseme) {
          this.currentViseme = this.targetViseme;
          this.targetViseme = newViseme;
          this.crossFadeProgress = 0;
        }
      }
    } else {
      // Pas de parole → retour au repos
      if (this.targetViseme !== 'REST') {
        this.currentViseme = this.targetViseme;
        this.targetViseme = 'REST';
        this.crossFadeProgress = 0;
      }
    }

    // Avancer le cross-fade
    if (this.crossFadeProgress < 1.0) {
      this.crossFadeProgress = Math.min(1.0, this.crossFadeProgress + this.crossFadeSpeed);
    }

    this.mouthOpenness += (speechEnergy - this.mouthOpenness) * 0.3;

    // 2. Clignements naturels
    this.blinkTimer += delta;
    if (this.blinkTimer > this.nextBlink && !this.isBlinking) {
      this.isBlinking = true;
      this.blinkProgress = 0;
    }

    if (this.isBlinking) {
      this.blinkProgress += delta / 120;
      if (this.blinkProgress >= 1) {
        this.isBlinking = false;
        this.blinkProgress = 0;
        this.blinkTimer = 0;
        this.nextBlink = 2000 + Math.random() * 3500;
      }
    }

    const blinkValue = this.isBlinking
      ? Math.sin(this.blinkProgress * Math.PI)
      : 0;

    // 3. Posture 3D de la tête
    const breathOffset = Math.sin(this.breathCycle) * 3.0;

    if (this.state === 'SPEAKING') {
      this.targetPitch = Math.sin(timestamp * 0.009) * 0.08 * (1 + this.mouthOpenness * 0.3);
      this.targetYaw = this.mouseX * 0.15 + Math.sin(timestamp * 0.004) * 0.06;
      this.targetRoll = Math.sin(timestamp * 0.003) * 0.04 + this.mouseX * 0.03;
    } else if (this.state === 'LISTENING') {
      this.targetPitch = 0.04;
      this.targetYaw = this.mouseX * 0.25;
      this.targetRoll = -0.04;
    } else if (this.state === 'THINKING') {
      this.targetPitch = -0.08;
      this.targetYaw = 0.1;
      this.targetRoll = 0.05;
    } else {
      this.targetPitch = Math.sin(this.breathCycle * 0.5) * 0.02;
      this.targetYaw = this.mouseX * 0.18 + Math.sin(timestamp * 0.001) * 0.03;
      this.targetRoll = Math.sin(timestamp * 0.0015) * 0.02;
    }

    this.headPitch += (this.targetPitch - this.headPitch) * 0.08;
    this.headYaw += (this.targetYaw - this.headYaw) * 0.08;
    const cx = width / 2;
    const cy = height / 2;
    const size = Math.min(width, height) * 0.88;

    // 4. Halo lumineux audio-réactif
    this.drawHolographicAura(cx, cy, size, audio.volume || (this.state === 'SPEAKING' ? 0.3 : 0), timestamp);

    // 5. Rendu du portrait avec morphing visème naturel (Fixe, sans rotation)
    this.ctx.save();
    this.ctx.translate(cx, cy);

    this.ctx.beginPath();
    this.ctx.arc(0, 0, size / 2, 0, Math.PI * 2);
    this.ctx.closePath();
    this.ctx.clip();

    this.ctx.fillStyle = '#0F172A';
    this.ctx.fill();

    if (this.hasVisemes) {
      this.renderVisemeCrossFade(size);
    } else if (this.isLoaded && this.image) {
      this.renderStaticPortrait(size);
    } else {
      this.drawPlaceholder(size);
    }

    // Clignement naturel par overlay semi-transparent (pas de dessins vectoriels)
    if (blinkValue > 0.04) {
      this.renderNaturalBlink(size, blinkValue);
    }

    this.ctx.restore();

    // 6. Anneau lumineux
    this.drawGlowRing(cx, cy, size, breathOffset, audio.volume || (this.state === 'SPEAKING' ? 0.3 : 0));
  }

  /**
   * Cross-Fade entre deux photos de visèmes.
   * Dessine d'abord le visème source, puis le visème cible par-dessus avec opacité progressive.
   */
  private renderVisemeCrossFade(size: number) {
    const half = size / 2;

    // Dessiner le visème source (en dessous)
    const currentImg = this.visemeImages.get(this.currentViseme) || this.image;
    if (currentImg) {
      this.ctx.save();
      this.ctx.globalAlpha = 1.0;
      this.ctx.drawImage(currentImg, -half, -half, size, size);
      this.ctx.restore();
    }

    // Dessiner le visème cible par-dessus avec opacité = crossFadeProgress
    if (this.crossFadeProgress < 1.0) {
      const targetImg = this.visemeImages.get(this.targetViseme) || this.image;
      if (targetImg && targetImg !== currentImg) {
        this.ctx.save();
        this.ctx.globalAlpha = this.crossFadeProgress;
        this.ctx.drawImage(targetImg, -half, -half, size, size);
        this.ctx.restore();
      }
    } else {
      // Transition terminée : dessiner directement le visème cible
      const targetImg = this.visemeImages.get(this.targetViseme) || this.image;
      if (targetImg) {
        this.ctx.save();
        this.ctx.globalAlpha = 1.0;
        this.ctx.drawImage(targetImg, -half, -half, size, size);
        this.ctx.restore();
      }
    }
  }

  /**
   * Rendu d'un portrait statique (fallback sans visèmes).
   * Aucun dessin vectoriel — juste la photo avec un léger scale subtil lié à l'audio.
   */
  private renderStaticPortrait(size: number) {
    const img = this.image!;
    const half = size / 2;

    // Micro-scale lié à la parole pour donner un peu de vie
    const breathScale = 1.0 + Math.sin(this.breathCycle) * 0.005;
    const speechScale = 1.0 + this.mouthOpenness * 0.008;
    const totalScale = breathScale * speechScale;

    this.ctx.save();
    this.ctx.scale(totalScale, totalScale);
    this.ctx.drawImage(img, -half, -half, size, size);
    this.ctx.restore();
  }

  /**
   * Clignement naturel : overlay sombre semi-transparent sur la zone des yeux.
   * Pas de dessin de paupières vectorielles.
   */
  private renderNaturalBlink(size: number, blinkValue: number) {
    const eyeY = -size * 0.08;
    const eyeW = size * 0.38;
    const eyeH = size * 0.06 * blinkValue;

    this.ctx.save();
    this.ctx.globalCompositeOperation = 'multiply';
    this.ctx.fillStyle = `rgba(20, 15, 15, ${blinkValue * 0.85})`;

    // Zone paupière gauche
    this.ctx.beginPath();
    this.ctx.ellipse(-size * 0.15, eyeY, eyeW / 2, eyeH, 0, 0, Math.PI * 2);
    this.ctx.fill();

    // Zone paupière droite
    this.ctx.beginPath();
    this.ctx.ellipse(size * 0.15, eyeY, eyeW / 2, eyeH, 0, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.restore();
  }

  private drawHolographicAura(cx: number, cy: number, size: number, energy: number, timestamp: number) {
    const auraRadius = (size / 2) * (1.1 + energy * 0.15 + Math.sin(timestamp * 0.003) * 0.02);
    const grad = this.ctx.createRadialGradient(cx, cy, size * 0.35, cx, cy, auraRadius);
    grad.addColorStop(0, 'transparent');
    grad.addColorStop(0.7, `${this.themeColor}33`);
    grad.addColorStop(1, `${this.themeColor}00`);

    this.ctx.save();
    this.ctx.fillStyle = grad;
    this.ctx.beginPath();
    this.ctx.arc(cx, cy, auraRadius, 0, Math.PI * 2);
    this.ctx.fill();

    if (this.state === 'SPEAKING' || energy > 0.03) {
      const bars = 28;
      this.ctx.strokeStyle = this.themeColor;
      this.ctx.lineWidth = 2.2;
      this.ctx.lineCap = 'round';

      for (let i = 0; i < bars; i++) {
        const angle = (i / bars) * Math.PI * 2 + timestamp * 0.0012;
        const wave = Math.sin(i * 0.5 + timestamp * 0.016) * (energy * 20 + 4);
        const r1 = size / 2 + 4;
        const r2 = r1 + wave;

        const x1 = cx + Math.cos(angle) * r1;
        const y1 = cy + Math.sin(angle) * r1;
        const x2 = cx + Math.cos(angle) * r2;
        const y2 = cy + Math.sin(angle) * r2;

        this.ctx.beginPath();
        this.ctx.moveTo(x1, y1);
        this.ctx.lineTo(x2, y2);
        this.ctx.stroke();
      }
    }
    this.ctx.restore();
  }

  private drawGlowRing(cx: number, cy: number, size: number, breathY: number, energy: number) {
    this.ctx.save();
    this.ctx.translate(cx + this.headYaw * 15, cy + breathY + this.headPitch * 10);
    this.ctx.beginPath();
    this.ctx.arc(0, 0, size / 2, 0, Math.PI * 2);
    this.ctx.lineWidth = 3.2;
    this.ctx.strokeStyle = this.themeColor;
    this.ctx.shadowColor = this.themeColor;
    this.ctx.shadowBlur = 14 + energy * 26;
    this.ctx.stroke();
    this.ctx.restore();
  }

  private drawPlaceholder(size: number) {
    const half = size / 2;
    this.ctx.save();
    this.ctx.beginPath();
    this.ctx.ellipse(0, 0, half * 0.7, half * 0.85, 0, 0, Math.PI * 2);
    this.ctx.fillStyle = '#1E293B';
    this.ctx.fill();
    this.ctx.strokeStyle = this.themeColor;
    this.ctx.lineWidth = 2;
    this.ctx.stroke();

    // Points simples pour les yeux
    this.ctx.beginPath();
    this.ctx.arc(-size * 0.18, -size * 0.08, 6, 0, Math.PI * 2);
    this.ctx.arc(size * 0.18, -size * 0.08, 6, 0, Math.PI * 2);
    this.ctx.fillStyle = this.themeColor;
    this.ctx.fill();

    this.ctx.restore();
  }
}
