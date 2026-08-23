import { Injectable, NgZone, inject } from '@angular/core';

export type AvatarState = 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING';

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

  private dataArray: Uint8Array | null = null;

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
        // Déjà connecté ou fallback direct
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
      if (i < len * 0.2) bass += v;
      else if (i < len * 0.6) mid += v;
      else high += v;
    }

    return {
      volume: sum / (len * 255),
      bass: bass / (len * 0.2 * 255),
      mid: mid / (len * 0.4 * 255),
      high: high / (len * 0.4 * 255),
    };
  }
}

export class CanvasAvatarInstance {
  private ctx: CanvasRenderingContext2D;
  private image: HTMLImageElement | null = null;
  private isLoaded = false;

  private animFrameId: number | null = null;
  private state: AvatarState = 'IDLE';
  private time = 0;

  // Mimiques
  private blinkTimer = 0;
  private nextBlink = 3000;
  private blinkProgress = 0;
  private isBlinking = false;

  // Head sway & tracking
  private mouseX = 0;
  private mouseY = 0;
  private targetHeadX = 0;
  private targetHeadY = 0;
  private currentHeadX = 0;
  private currentHeadY = 0;

  // Lip-sync smoothing
  private mouthOpen = 0;
  private mouthWidth = 1;

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
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      this.mouseX = Math.max(-1, Math.min(1, (e.clientX - centerX) / (window.innerWidth / 2)));
      this.mouseY = Math.max(-1, Math.min(1, (e.clientY - centerY) / (window.innerHeight / 2)));
    });
  }

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
      // Fallback direct sans crossOrigin si refusé
      const fallback = new Image();
      fallback.src = imageUrl;
      fallback.onload = () => {
        this.image = fallback;
        this.isLoaded = true;
      };
    };
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

  private render(timestamp: number) {
    const { width, height } = this.canvas;
    this.ctx.clearRect(0, 0, width, height);

    const delta = timestamp - (this.time || timestamp);
    this.time = timestamp;

    // 1. Audio Energy & Lip-Sync analysis
    const audio = this.service.getAudioEnergy();
    let targetMouthOpen = 0;
    let targetMouthWidth = 1.0;

    if (this.state === 'SPEAKING' || audio.volume > 0.02) {
      const simulatedEnergy = this.state === 'SPEAKING' && audio.volume <= 0.02
        ? Math.abs(Math.sin(timestamp * 0.015)) * 0.7 + Math.sin(timestamp * 0.008) * 0.3
        : audio.volume * 2.5;

      targetMouthOpen = Math.min(1.0, simulatedEnergy);
      targetMouthWidth = 1.0 + (audio.high || 0) * 0.4 - (audio.bass || 0) * 0.2;
    }

    this.mouthOpen += (targetMouthOpen - this.mouthOpen) * 0.35;
    this.mouthWidth += (targetMouthWidth - this.mouthWidth) * 0.2;

    // 2. Gestion des Clignements d'yeux naturels
    this.blinkTimer += delta;
    if (this.blinkTimer > this.nextBlink && !this.isBlinking) {
      this.isBlinking = true;
      this.blinkProgress = 0;
    }

    if (this.isBlinking) {
      this.blinkProgress += delta / 140;
      if (this.blinkProgress >= 1) {
        this.isBlinking = false;
        this.blinkProgress = 0;
        this.blinkTimer = 0;
        this.nextBlink = 2500 + Math.random() * 4000;
      }
    }

    const blinkValue = this.isBlinking
      ? Math.sin(this.blinkProgress * Math.PI)
      : 0;

    // 3. Calcul de la posture, respiration et inclinaison
    let breathY = Math.sin(timestamp * 0.002) * 3;
    let swayAngle = Math.sin(timestamp * 0.001) * 0.015;
    let nodY = 0;

    if (this.state === 'SPEAKING') {
      nodY = Math.sin(timestamp * 0.008) * 4 * this.mouthOpen;
      swayAngle += Math.sin(timestamp * 0.004) * 0.03;
    } else if (this.state === 'THINKING') {
      this.targetHeadX = 0.25;
      this.targetHeadY = -0.3;
      swayAngle = 0.04;
    } else if (this.state === 'LISTENING') {
      this.targetHeadX = this.mouseX * 0.3;
      this.targetHeadY = 0.15;
      swayAngle = -0.03;
    } else {
      this.targetHeadX = this.mouseX * 0.2;
      this.targetHeadY = this.mouseY * 0.2;
    }

    this.currentHeadX += (this.targetHeadX - this.currentHeadX) * 0.08;
    this.currentHeadY += (this.targetHeadY - this.currentHeadY) * 0.08;

    const cx = width / 2;
    const cy = height / 2;
    const size = Math.min(width, height) * 0.85;

    // 4. Rendu du Halo Holographique dynamique (Aura autour de l'avatar)
    this.drawHolographicAura(cx, cy, size, audio.volume, timestamp);

    // 5. Rendu du Portrait 2.5D avec Déformation Labiale & Mimiques
    this.ctx.save();
    this.ctx.translate(cx + this.currentHeadX * 15, cy + breathY + nodY + this.currentHeadY * 10);
    this.ctx.rotate(swayAngle);

    // Fond de base pour éviter tout écran noir
    this.ctx.beginPath();
    this.ctx.arc(0, 0, size / 2, 0, Math.PI * 2);
    this.ctx.fillStyle = '#0F172A';
    this.ctx.fill();

    // Masque circulaire élégant
    this.ctx.beginPath();
    this.ctx.arc(0, 0, size / 2, 0, Math.PI * 2);
    this.ctx.closePath();
    this.ctx.clip();

    if (this.isLoaded && this.image) {
      this.ctx.drawImage(this.image, -size / 2, -size / 2, size, size);

      // Morphing Labial sur l'image
      if (this.mouthOpen > 0.05) {
        this.renderLipSyncOnFace(size, this.mouthOpen, this.mouthWidth);
      }

      // Clignements naturels sur l'image
      if (blinkValue > 0.05) {
        this.renderEyeBlinkOnFace(size, blinkValue);
      }
    } else {
      this.drawStylizedFacePlaceholder(size, this.mouthOpen, blinkValue);
    }

    this.ctx.restore();

    // 6. Bordure lumineuse externe
    this.ctx.save();
    this.ctx.translate(cx + this.currentHeadX * 8, cy + breathY + nodY + this.currentHeadY * 5);
    this.ctx.beginPath();
    this.ctx.arc(0, 0, size / 2, 0, Math.PI * 2);
    this.ctx.lineWidth = 3;
    this.ctx.strokeStyle = this.themeColor;
    this.ctx.shadowColor = this.themeColor;
    this.ctx.shadowBlur = 12 + audio.volume * 20;
    this.ctx.stroke();
    this.ctx.restore();
  }

  private drawHolographicAura(cx: number, cy: number, size: number, energy: number, timestamp: number) {
    const auraRadius = (size / 2) * (1.08 + energy * 0.15 + Math.sin(timestamp * 0.003) * 0.02);

    const grad = this.ctx.createRadialGradient(cx, cy, size * 0.4, cx, cy, auraRadius);
    grad.addColorStop(0, 'transparent');
    grad.addColorStop(0.7, `${this.themeColor}33`);
    grad.addColorStop(1, `${this.themeColor}00`);

    this.ctx.save();
    this.ctx.fillStyle = grad;
    this.ctx.beginPath();
    this.ctx.arc(cx, cy, auraRadius, 0, Math.PI * 2);
    this.ctx.fill();

    if (this.state === 'SPEAKING' || energy > 0.05) {
      const bars = 32;
      this.ctx.strokeStyle = this.themeColor;
      this.ctx.lineWidth = 2;
      this.ctx.lineCap = 'round';

      for (let i = 0; i < bars; i++) {
        const angle = (i / bars) * Math.PI * 2 + timestamp * 0.001;
        const wave = Math.sin(i * 0.5 + timestamp * 0.01) * energy * 18 + 4;
        const r1 = size / 2 + 6;
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

  private renderLipSyncOnFace(size: number, openFactor: number, widthFactor: number) {
    const mouthY = size * 0.22;
    const mouthWidth = size * 0.18 * widthFactor;
    const mouthHeight = size * 0.12 * openFactor;

    this.ctx.save();

    this.ctx.beginPath();
    this.ctx.ellipse(0, mouthY, mouthWidth / 2, mouthHeight / 2, 0, 0, Math.PI * 2);
    const mouthGrad = this.ctx.createRadialGradient(0, mouthY, 2, 0, mouthY, mouthHeight);
    mouthGrad.addColorStop(0, '#3A0D15');
    mouthGrad.addColorStop(0.7, '#671D28');
    mouthGrad.addColorStop(1, '#22080D');
    this.ctx.fillStyle = mouthGrad;
    this.ctx.fill();

    if (openFactor > 0.3) {
      this.ctx.beginPath();
      this.ctx.ellipse(0, mouthY - mouthHeight * 0.22, mouthWidth * 0.32, mouthHeight * 0.18, 0, 0, Math.PI);
      this.ctx.fillStyle = '#F8FAFC';
      this.ctx.fill();
    }

    this.ctx.beginPath();
    this.ctx.ellipse(0, mouthY + mouthHeight * 0.4, mouthWidth * 0.45, mouthHeight * 0.15, 0, 0, Math.PI);
    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.18)';
    this.ctx.fill();

    this.ctx.restore();
  }

  private renderEyeBlinkOnFace(size: number, blinkAmount: number) {
    const eyeY = -size * 0.08;
    const eyeSpacing = size * 0.18;
    const eyeWidth = size * 0.14;
    const eyeHeight = size * 0.08 * blinkAmount;

    this.ctx.save();
    this.ctx.fillStyle = 'rgba(28, 28, 35, 0.75)';

    this.ctx.beginPath();
    this.ctx.ellipse(-eyeSpacing, eyeY, eyeWidth / 2, eyeHeight, 0, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.beginPath();
    this.ctx.ellipse(eyeSpacing, eyeY, eyeWidth / 2, eyeHeight, 0, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.restore();
  }

  private drawStylizedFacePlaceholder(size: number, mouthOpen: number, blink: number) {
    this.ctx.fillStyle = '#1E293B';
    this.ctx.fillRect(-size / 2, -size / 2, size, size);

    const eyeY = -size * 0.08;
    const eyeSpacing = size * 0.18;
    const eyeRadius = size * 0.05 * (1 - blink * 0.8);

    this.ctx.fillStyle = '#38BDF8';
    this.ctx.beginPath();
    this.ctx.arc(-eyeSpacing, eyeY, eyeRadius, 0, Math.PI * 2);
    this.ctx.arc(eyeSpacing, eyeY, eyeRadius, 0, Math.PI * 2);
    this.ctx.fill();

    const mouthY = size * 0.22;
    const mouthH = size * 0.04 + mouthOpen * size * 0.08;
    this.ctx.fillStyle = '#F43F5E';
    this.ctx.beginPath();
    this.ctx.ellipse(0, mouthY, size * 0.12, mouthH, 0, 0, Math.PI * 2);
    this.ctx.fill();
  }
}
