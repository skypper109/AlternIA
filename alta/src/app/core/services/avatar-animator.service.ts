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

export class CanvasAvatarInstance {
  private ctx: CanvasRenderingContext2D;
  private image: HTMLImageElement | null = null;
  private isLoaded = false;

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
  private eyeTargetX = 0;
  private eyeTargetY = 0;
  private eyeCurrentX = 0;
  private eyeCurrentY = 0;

  // Clignements
  private blinkTimer = 0;
  private nextBlink = 3000;
  private blinkProgress = 0;
  private isBlinking = false;

  // Lip-Sync & Visèmes
  private mouthOpen = 0;
  private mouthWidth = 1.0;
  private jawDrop = 0;
  private eyebrowLift = 0;

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
    this.breathCycle += delta * 0.0018;

    // 1. Analyse audio & Énergie vocale
    const audio = this.service.getAudioEnergy();
    let targetMouthOpen = 0;
    let targetMouthWidth = 1.0;
    let speechEmphasis = 0;

    if (this.state === 'SPEAKING' || audio.volume > 0.012) {
      const rawEnergy = (this.state === 'SPEAKING' && audio.volume <= 0.012)
        ? Math.abs(Math.sin(timestamp * 0.015)) * 0.85 + Math.sin(timestamp * 0.008) * 0.3
        : audio.volume * 3.5;

      targetMouthOpen = Math.min(1.0, Math.max(0.12, rawEnergy));
      targetMouthWidth = 1.0 + (audio.mid || 0) * 0.4 - (audio.bass || 0) * 0.25;
      speechEmphasis = targetMouthOpen;
    }

    this.mouthOpen += (targetMouthOpen - this.mouthOpen) * 0.38;
    this.mouthWidth += (targetMouthWidth - this.mouthWidth) * 0.25;
    this.jawDrop += (this.mouthOpen * 16 - this.jawDrop) * 0.35;
    this.eyebrowLift += (speechEmphasis * 5 - this.eyebrowLift) * 0.2;

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

    // 3. Posture 3D de la tête et hochements expressifs
    const breathOffset = Math.sin(this.breathCycle) * 3.0;

    if (this.state === 'SPEAKING') {
      this.targetPitch = Math.sin(timestamp * 0.009) * 0.08 * (1 + this.mouthOpen * 0.5);
      this.targetYaw = this.mouseX * 0.15 + Math.sin(timestamp * 0.004) * 0.06;
      this.targetRoll = Math.sin(timestamp * 0.003) * 0.04 + this.mouseX * 0.03;
      this.eyeTargetX = this.mouseX * 0.25;
      this.eyeTargetY = this.mouseY * 0.2;
    } else if (this.state === 'LISTENING') {
      this.targetPitch = 0.04;
      this.targetYaw = this.mouseX * 0.25;
      this.targetRoll = -0.04;
      this.eyeTargetX = this.mouseX * 0.4;
      this.eyeTargetY = 0.1;
    } else if (this.state === 'THINKING') {
      this.targetPitch = -0.08;
      this.targetYaw = 0.1;
      this.targetRoll = 0.05;
      this.eyeTargetX = 0.3;
      this.eyeTargetY = -0.4;
    } else {
      this.targetPitch = Math.sin(this.breathCycle * 0.5) * 0.02;
      this.targetYaw = this.mouseX * 0.18 + Math.sin(timestamp * 0.001) * 0.03;
      this.targetRoll = Math.sin(timestamp * 0.0015) * 0.02;
      this.eyeTargetX = this.mouseX * 0.3;
      this.eyeTargetY = this.mouseY * 0.25;
    }

    this.headPitch += (this.targetPitch - this.headPitch) * 0.08;
    this.headYaw += (this.targetYaw - this.headYaw) * 0.08;
    this.headRoll += (this.targetRoll - this.headRoll) * 0.08;
    this.eyeCurrentX += (this.eyeTargetX - this.eyeCurrentX) * 0.1;
    this.eyeCurrentY += (this.eyeTargetY - this.eyeCurrentY) * 0.1;

    const cx = width / 2;
    const cy = height / 2;
    const size = Math.min(width, height) * 0.88;

    // 4. Halo lumineux
    this.drawHolographicAura(cx, cy, size, audio.volume || (this.state === 'SPEAKING' ? 0.3 : 0), timestamp);

    // 5. Rendu du Portrait 2.5D
    this.ctx.save();
    const parallaxX = cx + this.headYaw * 35;
    const parallaxY = cy + breathOffset + this.headPitch * 25;
    this.ctx.translate(parallaxX, parallaxY);
    this.ctx.rotate(this.headRoll);

    this.ctx.beginPath();
    this.ctx.arc(0, 0, size / 2, 0, Math.PI * 2);
    this.ctx.closePath();
    this.ctx.clip();

    this.ctx.fillStyle = '#0F172A';
    this.ctx.fill();

    if (this.isLoaded && this.image) {
      this.renderOrganicPortrait(size, blinkValue);
    } else {
      this.drawStylizedFacePlaceholder(size, this.mouthOpen, blinkValue);
    }

    this.ctx.restore();

    // 6. Anneau lumineux
    this.drawGlowRing(cx, cy, size, breathOffset, audio.volume || (this.state === 'SPEAKING' ? 0.3 : 0));
  }

  private renderOrganicPortrait(size: number, blinkValue: number) {
    const img = this.image!;
    const half = size / 2;

    this.ctx.save();
    this.ctx.drawImage(img, -half, -half, size, size);
    this.ctx.restore();

    // Mâchoire 2.5D Jaw-Drop
    if (this.jawDrop > 0.8) {
      const jawH = size * 0.40;
      this.ctx.save();
      this.ctx.beginPath();
      this.ctx.ellipse(0, size * 0.28, half * 0.88, jawH * 0.65, 0, 0, Math.PI * 2);
      this.ctx.clip();
      this.ctx.translate(0, this.jawDrop * 0.7);
      this.ctx.scale(1.0 + this.mouthOpen * 0.02, 1.0 + this.mouthOpen * 0.04);
      this.ctx.drawImage(img, -half, -half, size, size);
      this.ctx.restore();
    }

    // Bouche
    if (this.mouthOpen > 0.06) {
      this.renderRealisticMouth(size, this.mouthOpen, this.mouthWidth);
    }

    // Clignements
    if (blinkValue > 0.04) {
      this.renderEyelids(size, blinkValue);
    }

    // Sourcils
    if (this.eyebrowLift > 0.5) {
      this.renderEyebrowAccents(size, this.eyebrowLift);
    }
  }

  private renderRealisticMouth(size: number, openFactor: number, widthFactor: number) {
    const mouthY = size * 0.21 + this.jawDrop * 0.3;
    const mouthW = size * 0.23 * widthFactor;
    const mouthH = size * 0.17 * openFactor;

    this.ctx.save();

    this.ctx.beginPath();
    this.ctx.ellipse(0, mouthY, mouthW / 2, mouthH / 2, 0, 0, Math.PI * 2);
    const grad = this.ctx.createRadialGradient(0, mouthY, 2, 0, mouthY, mouthH);
    grad.addColorStop(0, '#1A0407');
    grad.addColorStop(0.6, '#4A0F1A');
    grad.addColorStop(1, '#1A0407');
    this.ctx.fillStyle = grad;
    this.ctx.fill();

    if (openFactor > 0.2) {
      this.ctx.beginPath();
      this.ctx.ellipse(0, mouthY - mouthH * 0.24, mouthW * 0.38, mouthH * 0.22, 0, 0, Math.PI);
      this.ctx.fillStyle = '#FFFFFF';
      this.ctx.fill();
    }

    if (openFactor > 0.4) {
      this.ctx.beginPath();
      this.ctx.ellipse(0, mouthY + mouthH * 0.22, mouthW * 0.26, mouthH * 0.18, 0, Math.PI, Math.PI * 2);
      this.ctx.fillStyle = '#BA485C';
      this.ctx.fill();
    }

    this.ctx.beginPath();
    this.ctx.ellipse(0, mouthY, (mouthW / 2) + 2, (mouthH / 2) + 2, 0, 0, Math.PI * 2);
    this.ctx.strokeStyle = 'rgba(120, 40, 50, 0.45)';
    this.ctx.lineWidth = 2.5;
    this.ctx.stroke();

    this.ctx.restore();
  }

  private renderEyelids(size: number, blink: number) {
    const eyeY = -size * 0.08;
    const eyeSpacing = size * 0.17;
    const eyeW = size * 0.13;
    const eyeH = size * 0.08 * blink;

    this.ctx.save();
    this.ctx.fillStyle = 'rgba(40, 20, 25, 0.75)';

    this.ctx.beginPath();
    this.ctx.ellipse(-eyeSpacing, eyeY, eyeW / 2, eyeH / 2, 0, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.beginPath();
    this.ctx.ellipse(eyeSpacing, eyeY, eyeW / 2, eyeH / 2, 0, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.strokeStyle = 'rgba(20, 10, 15, 0.9)';
    this.ctx.lineWidth = 1.8;
    this.ctx.beginPath();
    this.ctx.moveTo(-eyeSpacing - eyeW / 2, eyeY);
    this.ctx.lineTo(-eyeSpacing + eyeW / 2, eyeY);
    this.ctx.moveTo(eyeSpacing - eyeW / 2, eyeY);
    this.ctx.lineTo(eyeSpacing + eyeW / 2, eyeY);
    this.ctx.stroke();

    this.ctx.restore();
  }

  private renderEyebrowAccents(size: number, lift: number) {
    const browY = -size * 0.19 - lift * 0.8;
    const browSpacing = size * 0.17;
    const browW = size * 0.12;

    this.ctx.save();
    this.ctx.strokeStyle = 'rgba(30, 20, 20, 0.35)';
    this.ctx.lineWidth = 2.5;
    this.ctx.lineCap = 'round';

    this.ctx.beginPath();
    this.ctx.moveTo(-browSpacing - browW / 2, browY + 2);
    this.ctx.quadraticCurveTo(-browSpacing, browY - 3, -browSpacing + browW / 2, browY);
    this.ctx.stroke();

    this.ctx.beginPath();
    this.ctx.moveTo(browSpacing - browW / 2, browY);
    this.ctx.quadraticCurveTo(browSpacing, browY - 3, browSpacing + browW / 2, browY + 2);
    this.ctx.stroke();

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

  private drawStylizedFacePlaceholder(size: number, mouthOpen: number, blink: number) {
    const half = size / 2;
    this.ctx.save();
    this.ctx.beginPath();
    this.ctx.ellipse(0, 0, half * 0.7, half * 0.85, 0, 0, Math.PI * 2);
    this.ctx.fillStyle = '#1E293B';
    this.ctx.fill();
    this.ctx.strokeStyle = this.themeColor;
    this.ctx.lineWidth = 2;
    this.ctx.stroke();

    if (blink < 0.7) {
      this.ctx.beginPath();
      this.ctx.arc(-size * 0.18, -size * 0.08, 6, 0, Math.PI * 2);
      this.ctx.arc(size * 0.18, -size * 0.08, 6, 0, Math.PI * 2);
      this.ctx.fillStyle = this.themeColor;
      this.ctx.fill();
    }

    this.renderRealisticMouth(size, mouthOpen, 1.0);
    this.ctx.restore();
  }
}
