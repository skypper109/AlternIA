/**
 * Moteur d'Animation Faciale 2.5D & Synchronisation Labiale Dynamique (Lip-Sync)
 * Déforme et anime n'importe quelle photo de portrait avec :
 * - Déplacement dynamique de la mâchoire (Jaw drop 2.5D)
 * - Morphing labial fluide calé sur le signal audio FFT à 60 FPS
 * - Clignements naturels des paupières
 * - Respiration, hochements de tête et inclinaisons 3D
 * - Halo holographique et ondes réactives
 */

export class DeviceAvatarAnimator {
  constructor(canvas, options = {}) {
    this.canvas = typeof canvas === 'string' ? document.getElementById(canvas) : canvas;
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d', { alpha: true });
    this.themeColor = options.themeColor || '#0284C7';
    this.state = 'IDLE'; // 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING'

    this.image = null;
    this.isLoaded = false;
    this.animFrameId = null;
    this.time = 0;

    // Analyseur Audio Web Audio API
    this.audioAnalyser = null;
    this.dataArray = null;

    // Mimiques & Clignements
    this.blinkTimer = 0;
    this.nextBlink = 2800;
    this.blinkProgress = 0;
    this.isBlinking = false;

    // Head sway & tracking
    this.mouseX = 0;
    this.mouseY = 0;
    this.targetHeadX = 0;
    this.targetHeadY = 0;
    this.currentHeadX = 0;
    this.currentHeadY = 0;

    // Lip-sync smoothing
    this.mouthOpen = 0;
    this.mouthWidth = 1;
    this.jawDrop = 0;

    this.initMouseTracking();
    this.start();
  }

  initMouseTracking() {
    window.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      this.mouseX = Math.max(-1, Math.min(1, (e.clientX - centerX) / (window.innerWidth / 2)));
      this.mouseY = Math.max(-1, Math.min(1, (e.clientY - centerY) / (window.innerHeight / 2)));
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

  render(timestamp) {
    const { width, height } = this.canvas;
    this.ctx.clearRect(0, 0, width, height);

    const delta = timestamp - (this.time || timestamp);
    this.time = timestamp;

    // 1. Analyse audio & Lip-Sync forcé
    const audio = this.getAudioEnergy();
    let targetMouthOpen = 0;
    let targetMouthWidth = 1.0;

    if (this.state === 'SPEAKING' || audio.volume > 0.015) {
      const simulatedEnergy = (this.state === 'SPEAKING' && audio.volume <= 0.015)
        ? Math.abs(Math.sin(timestamp * 0.018)) * 0.85 + Math.sin(timestamp * 0.009) * 0.35
        : audio.volume * 3.2;

      targetMouthOpen = Math.min(1.0, Math.max(0.15, simulatedEnergy));
      targetMouthWidth = 1.0 + (audio.high || 0) * 0.5 - (audio.bass || 0) * 0.3;
    }

    this.mouthOpen += (targetMouthOpen - this.mouthOpen) * 0.4;
    this.mouthWidth += (targetMouthWidth - this.mouthWidth) * 0.25;
    this.jawDrop += (this.mouthOpen * 14 - this.jawDrop) * 0.35;

    // 2. Clignements naturels
    this.blinkTimer += delta;
    if (this.blinkTimer > this.nextBlink && !this.isBlinking) {
      this.isBlinking = true;
      this.blinkProgress = 0;
    }

    if (this.isBlinking) {
      this.blinkProgress += delta / 130;
      if (this.blinkProgress >= 1) {
        this.isBlinking = false;
        this.blinkProgress = 0;
        this.blinkTimer = 0;
        this.nextBlink = 2200 + Math.random() * 3800;
      }
    }

    const blinkValue = this.isBlinking
      ? Math.sin(this.blinkProgress * Math.PI)
      : 0;

    // 3. Posture, inclinaison 3D et respiration
    let breathY = Math.sin(timestamp * 0.002) * 3.0;
    let swayAngle = Math.sin(timestamp * 0.001) * 0.02;
    let nodY = 0;

    if (this.state === 'SPEAKING') {
      nodY = Math.sin(timestamp * 0.01) * 5.0 * this.mouthOpen;
      swayAngle += Math.sin(timestamp * 0.005) * 0.035;
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
    const size = Math.min(width, height) * 0.88;

    // 4. Halo holographique
    this.drawHolographicAura(cx, cy, size, audio.volume || (this.state === 'SPEAKING' ? 0.3 : 0), timestamp);

    // 5. Rendu du Portrait 2.5D Déformé
    this.ctx.save();
    this.ctx.translate(cx + this.currentHeadX * 14, cy + breathY + nodY + this.currentHeadY * 10);
    this.ctx.rotate(swayAngle);

    // Fond de sécurité sombre
    this.ctx.beginPath();
    this.ctx.arc(0, 0, size / 2, 0, Math.PI * 2);
    this.ctx.fillStyle = '#0F172A';
    this.ctx.fill();

    // Masque circulaire
    this.ctx.beginPath();
    this.ctx.arc(0, 0, size / 2, 0, Math.PI * 2);
    this.ctx.closePath();
    this.ctx.clip();

    if (this.isLoaded && this.image) {
      // Rendu de la moitié supérieure (Crâne / Yeux / Nez)
      this.ctx.save();
      this.ctx.drawImage(this.image, -size / 2, -size / 2, size, size);
      this.ctx.restore();

      // Déformation 2.5D de la Mâchoire (Jaw Drop) sur le bas de l'image
      if (this.jawDrop > 1.0) {
        this.ctx.save();
        // Découpe de la mâchoire (40% inférieur)
        this.ctx.beginPath();
        this.ctx.rect(-size / 2, size * 0.12, size, size * 0.38);
        this.ctx.clip();
        // Translation vers le bas
        this.ctx.translate(0, this.jawDrop * 0.6);
        this.ctx.drawImage(this.image, -size / 2, -size / 2, size, size);
        this.ctx.restore();
      }

      // Morphing Labial & Ouverture Buccale Lumineuse
      if (this.mouthOpen > 0.08) {
        this.renderLipSyncOnFace(size, this.mouthOpen, this.mouthWidth);
      }

      // Clignements naturels
      if (blinkValue > 0.05) {
        this.renderEyeBlinkOnFace(size, blinkValue);
      }
    } else {
      this.drawStylizedPlaceholder(size, this.mouthOpen, blinkValue);
    }

    this.ctx.restore();

    // 6. Contour lumineux réactif
    this.ctx.save();
    this.ctx.translate(cx + this.currentHeadX * 8, cy + breathY + nodY + this.currentHeadY * 5);
    this.ctx.beginPath();
    this.ctx.arc(0, 0, size / 2, 0, Math.PI * 2);
    this.ctx.lineWidth = 3;
    this.ctx.strokeStyle = this.themeColor;
    this.ctx.shadowColor = this.themeColor;
    this.ctx.shadowBlur = 12 + (audio.volume || (this.state === 'SPEAKING' ? 0.4 : 0)) * 22;
    this.ctx.stroke();
    this.ctx.restore();
  }

  drawHolographicAura(cx, cy, size, energy, timestamp) {
    const auraRadius = (size / 2) * (1.08 + energy * 0.18 + Math.sin(timestamp * 0.003) * 0.02);
    const grad = this.ctx.createRadialGradient(cx, cy, size * 0.38, cx, cy, auraRadius);
    grad.addColorStop(0, 'transparent');
    grad.addColorStop(0.7, `${this.themeColor}33`);
    grad.addColorStop(1, `${this.themeColor}00`);

    this.ctx.save();
    this.ctx.fillStyle = grad;
    this.ctx.beginPath();
    this.ctx.arc(cx, cy, auraRadius, 0, Math.PI * 2);
    this.ctx.fill();

    if (this.state === 'SPEAKING' || energy > 0.03) {
      const bars = 32;
      this.ctx.strokeStyle = this.themeColor;
      this.ctx.lineWidth = 2.2;
      this.ctx.lineCap = 'round';

      for (let i = 0; i < bars; i++) {
        const angle = (i / bars) * Math.PI * 2 + timestamp * 0.0015;
        const wave = Math.sin(i * 0.5 + timestamp * 0.015) * (energy * 22 + 5);
        const r1 = size / 2 + 5;
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

  renderLipSyncOnFace(size, openFactor, widthFactor) {
    const mouthY = size * 0.20;
    const mouthWidth = size * 0.22 * widthFactor;
    const mouthHeight = size * 0.16 * openFactor;

    this.ctx.save();

    // Cavité buccale réaliste avec dégradé de profondeur
    this.ctx.beginPath();
    this.ctx.ellipse(0, mouthY, mouthWidth / 2, mouthHeight / 2, 0, 0, Math.PI * 2);
    const mouthGrad = this.ctx.createRadialGradient(0, mouthY, 2, 0, mouthY, mouthHeight);
    mouthGrad.addColorStop(0, '#22050A');
    mouthGrad.addColorStop(0.65, '#5A1420');
    mouthGrad.addColorStop(1, '#1A0407');
    this.ctx.fillStyle = mouthGrad;
    this.ctx.fill();

    // Dents supérieures blanches nettes
    if (openFactor > 0.25) {
      this.ctx.beginPath();
      this.ctx.ellipse(0, mouthY - mouthHeight * 0.22, mouthWidth * 0.36, mouthHeight * 0.2, 0, 0, Math.PI);
      this.ctx.fillStyle = '#FFFFFF';
      this.ctx.fill();
    }

    // Langue douce
    if (openFactor > 0.4) {
      this.ctx.beginPath();
      this.ctx.ellipse(0, mouthY + mouthHeight * 0.25, mouthWidth * 0.25, mouthHeight * 0.18, 0, 0, Math.PI * 2);
      this.ctx.fillStyle = '#E11D48';
      this.ctx.fill();
    }

    // Lèvres souples & ombre de contour
    this.ctx.beginPath();
    this.ctx.ellipse(0, mouthY, mouthWidth * 0.54, mouthHeight * 0.55, 0, 0, Math.PI * 2);
    this.ctx.lineWidth = 2.5;
    this.ctx.strokeStyle = 'rgba(80, 20, 30, 0.45)';
    this.ctx.stroke();

    this.ctx.restore();
  }

  renderEyeBlinkOnFace(size, blinkAmount) {
    const eyeY = -size * 0.09;
    const eyeSpacing = size * 0.19;
    const eyeWidth = size * 0.16;
    const eyeHeight = size * 0.10 * blinkAmount;

    this.ctx.save();
    this.ctx.fillStyle = 'rgba(20, 20, 28, 0.85)';

    this.ctx.beginPath();
    this.ctx.ellipse(-eyeSpacing, eyeY, eyeWidth / 2, eyeHeight, 0, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.beginPath();
    this.ctx.ellipse(eyeSpacing, eyeY, eyeWidth / 2, eyeHeight, 0, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.restore();
  }

  drawStylizedPlaceholder(size, mouthOpen, blink) {
    this.ctx.fillStyle = '#0F172A';
    this.ctx.fillRect(-size / 2, -size / 2, size, size);

    const eyeY = -size * 0.08;
    const eyeSpacing = size * 0.18;
    const eyeRadius = size * 0.06 * (1 - blink * 0.85);

    this.ctx.fillStyle = '#38BDF8';
    this.ctx.beginPath();
    this.ctx.arc(-eyeSpacing, eyeY, eyeRadius, 0, Math.PI * 2);
    this.ctx.arc(eyeSpacing, eyeY, eyeRadius, 0, Math.PI * 2);
    this.ctx.fill();

    const mouthY = size * 0.20;
    const mouthH = size * 0.04 + mouthOpen * size * 0.10;
    this.ctx.fillStyle = '#F43F5E';
    this.ctx.beginPath();
    this.ctx.ellipse(0, mouthY, size * 0.14, mouthH, 0, 0, Math.PI * 2);
    this.ctx.fill();
  }
}
