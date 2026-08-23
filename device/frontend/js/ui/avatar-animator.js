/**
/**
 * Moteur d'Animation Faciale 2.5D & Synchronisation Labiale (Lip-Sync) ES6 pour le Kiosk Alternia.
 * Anime n'importe quelle photo / portrait uploadé avec clignements d'yeux, hochements, respiration
 * et morphing labial dynamique en temps réel calé sur le signal audio TTS de la voix.
 */

export class DeviceAvatarAnimator {
  constructor(canvas, options = {}) {
    this.canvas = typeof canvas === 'string' ? document.getElementById(canvas) : canvas;
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d', { alpha: true });
    this.themeColor = options.themeColor || '#40BBCC';
    this.state = 'IDLE'; // 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING'

    this.image = null;
    this.isLoaded = false;
    this.animFrameId = null;
    this.time = 0;

    // Analyseur Audio Web Audio API
    this.audioAnalyser = null;
    this.dataArray = null;

    // Mimiques
    this.blinkTimer = 0;
    this.nextBlink = 3000;
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
    this.isLoaded = false;
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.src = imageUrl;
    img.onload = () => {
      this.image = img;
      this.isLoaded = true;
    };
    img.onerror = () => {
      // Fallback portrait stylisé
      this.image = null;
      this.isLoaded = false;
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

    this.audioAnalyser.getByteFrequencyData(this.dataArray);
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

  render(timestamp) {
    const { width, height } = this.canvas;
    this.ctx.clearRect(0, 0, width, height);

    const delta = timestamp - (this.time || timestamp);
    this.time = timestamp;

    // 1. Analyse audio et calcul Lip-Sync
    const audio = this.getAudioEnergy();
    let targetMouthOpen = 0;
    let targetMouthWidth = 1.0;

    if (this.state === 'SPEAKING' || audio.volume > 0.02) {
      const simulatedEnergy = this.state === 'SPEAKING' && audio.volume <= 0.02
        ? Math.abs(Math.sin(timestamp * 0.015)) * 0.7 + Math.sin(timestamp * 0.008) * 0.3
        : audio.volume * 2.6;

      targetMouthOpen = Math.min(1.0, simulatedEnergy);
      targetMouthWidth = 1.0 + (audio.high || 0) * 0.4 - (audio.bass || 0) * 0.2;
    }

    this.mouthOpen += (targetMouthOpen - this.mouthOpen) * 0.35;
    this.mouthWidth += (targetMouthWidth - this.mouthWidth) * 0.2;

    // 2. Clignements naturels
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

    // 3. Posture, inclinaison et respiration
    let breathY = Math.sin(timestamp * 0.002) * 2.5;
    let swayAngle = Math.sin(timestamp * 0.001) * 0.015;
    let nodY = 0;

    if (this.state === 'SPEAKING') {
      nodY = Math.sin(timestamp * 0.008) * 3.5 * this.mouthOpen;
      swayAngle += Math.sin(timestamp * 0.004) * 0.025;
    } else if (this.state === 'THINKING') {
      this.targetHeadX = 0.2;
      this.targetHeadY = -0.25;
      swayAngle = 0.035;
    } else if (this.state === 'LISTENING') {
      this.targetHeadX = this.mouseX * 0.25;
      this.targetHeadY = 0.12;
      swayAngle = -0.025;
    } else {
      this.targetHeadX = this.mouseX * 0.15;
      this.targetHeadY = this.mouseY * 0.15;
    }

    this.currentHeadX += (this.targetHeadX - this.currentHeadX) * 0.08;
    this.currentHeadY += (this.targetHeadY - this.currentHeadY) * 0.08;

    const cx = width / 2;
    const cy = height / 2;
    const size = Math.min(width, height) * 0.88;

    // 4. Aura holographique
    this.drawHolographicAura(cx, cy, size, audio.volume, timestamp);

    // 5. Rendu 2.5D du portrait avec Lip-Sync & Mimiques
    this.ctx.save();
    this.ctx.translate(cx + this.currentHeadX * 12, cy + breathY + nodY + this.currentHeadY * 8);
    this.ctx.rotate(swayAngle);

    // Masque circulaire parfait
    this.ctx.beginPath();
    this.ctx.arc(0, 0, size / 2, 0, Math.PI * 2);
    this.ctx.closePath();
    this.ctx.clip();

    if (this.isLoaded && this.image) {
      this.ctx.drawImage(this.image, -size / 2, -size / 2, size, size);

      // Morphing Labial (Bouche animée sur l'image)
      if (this.mouthOpen > 0.05) {
        this.renderLipSyncOnFace(size, this.mouthOpen, this.mouthWidth);
      }

      // Clignements d'yeux
      if (blinkValue > 0.05) {
        this.renderEyeBlinkOnFace(size, blinkValue);
      }
    } else {
      this.drawStylizedPlaceholder(size, this.mouthOpen, blinkValue);
    }

    this.ctx.restore();

    // 6. Contour lumineux
    this.ctx.save();
    this.ctx.translate(cx + this.currentHeadX * 6, cy + breathY + nodY + this.currentHeadY * 4);
    this.ctx.beginPath();
    this.ctx.arc(0, 0, size / 2, 0, Math.PI * 2);
    this.ctx.lineWidth = 2.5;
    this.ctx.strokeStyle = this.themeColor;
    this.ctx.shadowColor = this.themeColor;
    this.ctx.shadowBlur = 10 + audio.volume * 18;
    this.ctx.stroke();
    this.ctx.restore();
  }

  drawHolographicAura(cx, cy, size, energy, timestamp) {
    const auraRadius = (size / 2) * (1.06 + energy * 0.12 + Math.sin(timestamp * 0.003) * 0.02);
    const grad = this.ctx.createRadialGradient(cx, cy, size * 0.4, cx, cy, auraRadius);
    grad.addColorStop(0, 'transparent');
    grad.addColorStop(0.75, `${this.themeColor}33`);
    grad.addColorStop(1, `${this.themeColor}00`);

    this.ctx.save();
    this.ctx.fillStyle = grad;
    this.ctx.beginPath();
    this.ctx.arc(cx, cy, auraRadius, 0, Math.PI * 2);
    this.ctx.fill();

    if (this.state === 'SPEAKING' || energy > 0.04) {
      const bars = 28;
      this.ctx.strokeStyle = this.themeColor;
      this.ctx.lineWidth = 2;
      this.ctx.lineCap = 'round';

      for (let i = 0; i < bars; i++) {
        const angle = (i / bars) * Math.PI * 2 + timestamp * 0.0012;
        const wave = Math.sin(i * 0.6 + timestamp * 0.012) * energy * 16 + 3;
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

  renderLipSyncOnFace(size, openFactor, widthFactor) {
    const mouthY = size * 0.22;
    const mouthWidth = size * 0.18 * widthFactor;
    const mouthHeight = size * 0.12 * openFactor;

    this.ctx.save();

    // Cavité buccale intérieure
    this.ctx.beginPath();
    this.ctx.ellipse(0, mouthY, mouthWidth / 2, mouthHeight / 2, 0, 0, Math.PI * 2);
    const mouthGrad = this.ctx.createRadialGradient(0, mouthY, 2, 0, mouthY, mouthHeight);
    mouthGrad.addColorStop(0, '#3A0D15');
    mouthGrad.addColorStop(0.7, '#671D28');
    mouthGrad.addColorStop(1, '#22080D');
    this.ctx.fillStyle = mouthGrad;
    this.ctx.fill();

    // Dents
    if (openFactor > 0.3) {
      this.ctx.beginPath();
      this.ctx.ellipse(0, mouthY - mouthHeight * 0.22, mouthWidth * 0.32, mouthHeight * 0.18, 0, 0, Math.PI);
      this.ctx.fillStyle = '#F8FAFC';
      this.ctx.fill();
    }

    // Ombre lèvre inférieure
    this.ctx.beginPath();
    this.ctx.ellipse(0, mouthY + mouthHeight * 0.4, mouthWidth * 0.45, mouthHeight * 0.15, 0, 0, Math.PI);
    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.18)';
    this.ctx.fill();

    this.ctx.restore();
  }

  renderEyeBlinkOnFace(size, blinkAmount) {
    const eyeY = -size * 0.08;
    const eyeSpacing = size * 0.18;
    const eyeWidth = size * 0.14;
    const eyeHeight = size * 0.08 * blinkAmount;

    this.ctx.save();
    this.ctx.fillStyle = 'rgba(25, 25, 32, 0.75)';

    this.ctx.beginPath();
    this.ctx.ellipse(-eyeSpacing, eyeY, eyeWidth / 2, eyeHeight, 0, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.beginPath();
    this.ctx.ellipse(eyeSpacing, eyeY, eyeWidth / 2, eyeHeight, 0, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.restore();
  }

  drawStylizedPlaceholder(size, mouthOpen, blink) {
    this.ctx.fillStyle = '#111A2E';
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
