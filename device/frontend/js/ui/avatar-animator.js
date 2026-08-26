/**
 * Moteur d'Animation de Portrait 2.5D Haute Fidélité & Tête Parlante Synchrone (Talking Head).
 * Variante pure JS du CanvasAvatarInstance (Angular) pour le boîtier.
 * Implémente le système Viseme Sprite-Sheet (Cross-Fade) pour un réalisme accru.
 */

const VISEME_IDS = ['REST', 'CLOSED', 'OPEN_SMALL', 'OPEN_WIDE', 'ROUND_O', 'ROUND_U', 'TEETH', 'SMILE'];

export class DeviceAvatarAnimator {
  constructor(canvas, options = {}) {
    this.canvas = typeof canvas === 'string' ? document.getElementById(canvas) : canvas;
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d', { alpha: true });
    this.themeColor = options.themeColor || '#0284C7';
    this.isLogoMode = options.isLogoMode || false;
    this.state = 'IDLE'; // 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING'

    // Image principale (fallback si pas de visèmes)
    this.image = null;
    this.isLoaded = false;

    // Sprite-Sheet Visème : 8 images pré-chargées
    this.visemeImages = new Map();
    this.visemeLoadedCount = 0;
    this.hasVisemes = false;

    // Visème courant et cible pour le cross-fade
    this.currentViseme = 'REST';
    this.targetViseme = 'REST';
    this.crossFadeProgress = 1.0;
    this.crossFadeSpeed = 0.18;

    this.animFrameId = null;
    this.time = 0;

    // Analyseur Audio FFT
    this.audioAnalyser = null;
    this.dataArray = null;

    // Dynamique de la Tête (3D Pose & Saccades)
    this.headPitch = 0;
    this.headYaw = 0;
    this.headRoll = 0;
    this.targetPitch = 0;
    this.targetYaw = 0;
    this.targetRoll = 0;

    // Suivi de la souris / de l'élève
    this.mouseX = 0;
    this.mouseY = 0;

    // Clignements naturels
    this.blinkTimer = 0;
    this.nextBlink = 3000;
    this.blinkProgress = 0;
    this.isBlinking = false;

    // Lip-Sync dynamique (uniquement pour le fallback statique maintenant)
    this.mouthOpenness = 0;

    // Respiration
    this.breathCycle = 0;

    if (options.enableMouseTracking !== false) {
      this.initMouseTracking();
    }
    this.start();
  }

  initMouseTracking() {
    window.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      this.mouseX = Math.max(-1, Math.min(1, (e.clientX - cx) / (window.innerWidth / 2)));
      this.mouseY = Math.max(-1, Math.min(1, (e.clientY - cy) / (window.innerHeight / 2)));
    });
  }

  setImage(imageUrl) {
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

  setVisemePhotos(visemePhotos) {
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
        this.visemeImages.set(visemeId, img);
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

  setAudioAnalyser(analyser) {
    this.audioAnalyser = analyser;
    if (analyser) {
      this.dataArray = new Uint8Array(analyser.frequencyBinCount);
    }
  }

  setState(newState) {
    this.state = newState;
  }

  setThemeColor(color) {
    this.themeColor = color;
  }

  start() {
    if (this.animFrameId) return;
    const loop = (timestamp) => {
      this.render(timestamp);
      this.animFrameId = requestAnimationFrame(loop);
    };
    this.animFrameId = requestAnimationFrame(loop);
  }

  stop() {
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
  }

  getAudioEnergy() {
    if (!this.audioAnalyser || !this.dataArray) {
      return { volume: 0, bass: 0, mid: 0, high: 0 };
    }

    try {
      this.audioAnalyser.getByteFrequencyData(this.dataArray);
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

  determineVisemeFromAudio(audio) {
    const { volume, bass, mid, high } = audio;

    if (volume < 0.015) return 'REST';

    if (volume > 0.35 && bass > 0.3) return 'OPEN_WIDE';
    if (bass > 0.35 && mid < 0.25) return 'ROUND_O';
    if (bass > 0.4 && high < 0.15) return 'ROUND_U';
    if (high > 0.3 && volume > 0.1) return 'TEETH';
    if (volume > 0.15 && mid > 0.2) return 'OPEN_SMALL';
    if (volume > 0.05 && volume < 0.15) return 'CLOSED';
    if (mid > 0.25 && high > 0.2) return 'SMILE';

    return 'OPEN_SMALL';
  }

  render(timestamp) {
    const { width, height } = this.canvas;
    this.ctx.clearRect(0, 0, width, height);

    const delta = timestamp - (this.time || timestamp);
    this.time = timestamp;
    this.breathCycle += delta * 0.0018;

    // 1. Analyse audio & Énergie vocale
    const audio = this.getAudioEnergy();
    let speechEnergy = 0;

    if (this.state === 'SPEAKING' || audio.volume > 0.012) {
      speechEnergy = (this.state === 'SPEAKING' && audio.volume <= 0.012)
        ? Math.abs(Math.sin(timestamp * 0.015)) * 0.6
        : audio.volume * 3.0;

      if (this.hasVisemes) {
        const newViseme = this.determineVisemeFromAudio(audio);
        if (newViseme !== this.targetViseme) {
          this.currentViseme = this.targetViseme;
          this.targetViseme = newViseme;
          this.crossFadeProgress = 0;
        }
      }
    } else {
      if (this.targetViseme !== 'REST') {
        this.currentViseme = this.targetViseme;
        this.targetViseme = 'REST';
        this.crossFadeProgress = 0;
      }
    }

    if (this.crossFadeProgress < 1.0) {
      this.crossFadeProgress = Math.min(1.0, this.crossFadeProgress + this.crossFadeSpeed);
    }

    this.mouthOpenness += (speechEnergy - this.mouthOpenness) * 0.3;

    // 2. Clignements naturels avec variation stochastique
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

    const blinkValue = this.isBlinking ? Math.sin(this.blinkProgress * Math.PI) : 0;

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
    this.headRoll += (this.targetRoll - this.headRoll) * 0.08;

    const cx = width / 2;
    const cy = height / 2;
    const size = Math.min(width, height) * 0.88;

    // 4. Halo lumineux
    this.drawAura(cx, cy, size, audio.volume || (this.state === 'SPEAKING' ? 0.3 : 0), timestamp);

    // 5. Rendu du Portrait en 2.5D
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

    if (this.hasVisemes) {
      this.renderVisemeCrossFade(size);
    } else if (this.isLoaded && this.image) {
      this.renderStaticPortrait(size);
    } else {
      this.drawPlaceholder(size);
    }

    if (!this.isLogoMode && blinkValue > 0.04) {
      this.renderNaturalBlink(size, blinkValue);
    }

    this.ctx.restore();

    // 6. Anneau lumineux
    this.drawGlowRing(cx, cy, size, breathOffset, audio.volume || (this.state === 'SPEAKING' ? 0.3 : 0));
  }

  renderVisemeCrossFade(size) {
    const half = size / 2;

    const currentImg = this.visemeImages.get(this.currentViseme) || this.image;
    if (currentImg) {
      this.ctx.save();
      this.ctx.globalAlpha = 1.0;
      this.ctx.drawImage(currentImg, -half, -half, size, size);
      this.ctx.restore();
    }

    if (this.crossFadeProgress < 1.0) {
      const targetImg = this.visemeImages.get(this.targetViseme) || this.image;
      if (targetImg && targetImg !== currentImg) {
        this.ctx.save();
        this.ctx.globalAlpha = this.crossFadeProgress;
        this.ctx.drawImage(targetImg, -half, -half, size, size);
        this.ctx.restore();
      }
    } else {
      const targetImg = this.visemeImages.get(this.targetViseme) || this.image;
      if (targetImg) {
        this.ctx.save();
        this.ctx.globalAlpha = 1.0;
        this.ctx.drawImage(targetImg, -half, -half, size, size);
        this.ctx.restore();
      }
    }
  }

  renderStaticPortrait(size) {
    const img = this.image;
    const half = size / 2;
    const breathScale = 1.0 + Math.sin(this.breathCycle) * 0.005;
    const speechScale = this.isLogoMode ? 1.0 : (1.0 + this.mouthOpenness * 0.008);
    const totalScale = breathScale * speechScale;

    this.ctx.save();
    this.ctx.scale(totalScale, totalScale);
    this.ctx.drawImage(img, -half, -half, size, size);
    this.ctx.restore();
  }

  renderNaturalBlink(size, blinkValue) {
    const eyeY = -size * 0.08;
    const eyeW = size * 0.38;
    const eyeH = size * 0.06 * blinkValue;

    this.ctx.save();
    this.ctx.globalCompositeOperation = 'multiply';
    this.ctx.fillStyle = `rgba(20, 15, 15, ${blinkValue * 0.85})`;

    this.ctx.beginPath();
    this.ctx.ellipse(-size * 0.15, eyeY, eyeW / 2, eyeH, 0, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.beginPath();
    this.ctx.ellipse(size * 0.15, eyeY, eyeW / 2, eyeH, 0, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.restore();
  }

  drawAura(cx, cy, size, energy, timestamp) {
    const r = (size / 2) * (1.1 + energy * 0.15 + Math.sin(timestamp * 0.003) * 0.02);
    const grad = this.ctx.createRadialGradient(cx, cy, size * 0.35, cx, cy, r);
    grad.addColorStop(0, 'transparent');
    grad.addColorStop(0.7, `${this.themeColor}33`);
    grad.addColorStop(1, `${this.themeColor}00`);

    this.ctx.save();
    this.ctx.fillStyle = grad;
    this.ctx.beginPath();
    this.ctx.arc(cx, cy, r, 0, Math.PI * 2);
    this.ctx.fill();

    if (!this.isLogoMode && (this.state === 'SPEAKING' || energy > 0.03)) {
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

  drawGlowRing(cx, cy, size, breathY, energy) {
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

  drawPlaceholder(size) {
    const half = size / 2;
    this.ctx.save();
    
    this.ctx.beginPath();
    this.ctx.ellipse(0, 0, half * 0.7, half * 0.85, 0, 0, Math.PI * 2);
    this.ctx.fillStyle = '#1E293B';
    this.ctx.fill();
    this.ctx.strokeStyle = this.themeColor;
    this.ctx.lineWidth = 2;
    this.ctx.stroke();

    this.ctx.beginPath();
    this.ctx.arc(-size * 0.18, -size * 0.08, 6, 0, Math.PI * 2);
    this.ctx.arc(size * 0.18, -size * 0.08, 6, 0, Math.PI * 2);
    this.ctx.fillStyle = this.themeColor;
    this.ctx.fill();

    this.ctx.restore();
  }
}
