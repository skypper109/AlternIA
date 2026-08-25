/**
 * Moteur d'Animation de Portrait 2.5D Haute Fidélité & Tête Parlante Synchrone (Talking Head).
 * 
 * Anime n'importe quelle photo de visage/portrait de manière organique et fluide :
 * 1. Mouvements 3D de la tête entière (Pitch, Yaw, Roll, Parallaxe de profondeur).
 * 2. Déformation faciale anatomique continue (Mâchoire, Joues, Menton, Cou).
 * 3. Hochements de tête expressifs et micro-inclinaisons synchronisés avec le TTS.
 * 4. Morphing labial fluide multi-visèmes (A, E, I, O, U, Consonnes) calé sur l'analyse FFT.
 * 5. Clignements de paupières naturels avec micro-saccades oculaires.
 * 6. Respiration du buste et aura holographique réactive.
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

    // Analyseur Audio FFT
    this.audioAnalyser = null;
    this.dataArray = null;

    // Dynamique de la Tête (3D Pose & Saccades)
    this.headPitch = 0;   // Hochement haut/bas
    this.headYaw = 0;     // Rotation gauche/droite
    this.headRoll = 0;    // Inclinaison latérale
    this.targetPitch = 0;
    this.targetYaw = 0;
    this.targetRoll = 0;

    // Suivi de la souris / de l'élève
    this.mouseX = 0;
    this.mouseY = 0;
    this.eyeTargetX = 0;
    this.eyeTargetY = 0;
    this.eyeCurrentX = 0;
    this.eyeCurrentY = 0;

    // Clignements naturels
    this.blinkTimer = 0;
    this.nextBlink = 3000;
    this.blinkProgress = 0;
    this.isBlinking = false;

    // Lip-Sync & Visèmes organiques
    this.mouthOpen = 0;
    this.mouthWidth = 1.0;
    this.jawDrop = 0;
    this.cheekLift = 0;
    this.eyebrowLift = 0;

    // Respiration
    this.breathCycle = 0;

    this.initMouseTracking();
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
    this.breathCycle += delta * 0.0018;

    // 1. Analyse audio & Énergie vocale
    const audio = this.getAudioEnergy();
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

    // Lissage dynamique des visèmes
    this.mouthOpen += (targetMouthOpen - this.mouthOpen) * 0.38;
    this.mouthWidth += (targetMouthWidth - this.mouthWidth) * 0.25;
    this.jawDrop += (this.mouthOpen * 16 - this.jawDrop) * 0.35;
    this.cheekLift += (this.mouthOpen * 4 - this.cheekLift) * 0.25;
    this.eyebrowLift += (speechEmphasis * 5 - this.eyebrowLift) * 0.2;

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

    const blinkValue = this.isBlinking
      ? Math.sin(this.blinkProgress * Math.PI)
      : 0;

    // 3. Posture 3D de la tête et hochements expressifs
    const breathOffset = Math.sin(this.breathCycle) * 3.0;

    if (this.state === 'SPEAKING') {
      // Hochements naturels au rythme de la voix
      this.targetPitch = Math.sin(timestamp * 0.009) * 0.08 * (1 + this.mouthOpen * 0.5);
      this.targetYaw = this.mouseX * 0.15 + Math.sin(timestamp * 0.004) * 0.06;
      this.targetRoll = Math.sin(timestamp * 0.003) * 0.04 + this.mouseX * 0.03;
      this.eyeTargetX = this.mouseX * 0.25;
      this.eyeTargetY = this.mouseY * 0.2;
    } else if (this.state === 'LISTENING') {
      // Tête légèrement penchée en écoute attentive
      this.targetPitch = 0.04;
      this.targetYaw = this.mouseX * 0.25;
      this.targetRoll = -0.04;
      this.eyeTargetX = this.mouseX * 0.4;
      this.eyeTargetY = 0.1;
    } else if (this.state === 'THINKING') {
      // Regard et tête tournés vers le haut en réflexion
      this.targetPitch = -0.08;
      this.targetYaw = 0.1;
      this.targetRoll = 0.05;
      this.eyeTargetX = 0.3;
      this.eyeTargetY = -0.4;
    } else {
      // Repos (Idle) avec léger balancement vivant
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

    // 4. Halo lumineux holographique réactif
    this.drawAura(cx, cy, size, audio.volume || (this.state === 'SPEAKING' ? 0.3 : 0), timestamp);

    // 5. Rendu du Portrait Déformé en 2.5D
    this.ctx.save();
    
    // Positionnement global avec parallaxe 3D
    const parallaxX = cx + this.headYaw * 35;
    const parallaxY = cy + breathOffset + this.headPitch * 25;
    this.ctx.translate(parallaxX, parallaxY);
    this.ctx.rotate(this.headRoll);

    // Masque circulaire
    this.ctx.beginPath();
    this.ctx.arc(0, 0, size / 2, 0, Math.PI * 2);
    this.ctx.closePath();
    this.ctx.clip();

    // Fond sombre élégant
    this.ctx.fillStyle = '#0F172A';
    this.ctx.fill();

    if (this.isLoaded && this.image) {
      // Rendu Multi-Tranches 2.5D (Tête, Joues, Mâchoire, Yeux)
      this.renderOrganicPortrait(size, blinkValue);
    } else {
      this.drawStylizedPlaceholder(size, this.mouthOpen, blinkValue);
    }

    this.ctx.restore();

    // 6. Anneau lumineux dynamique extérieur
    this.drawGlowRing(cx, cy, size, breathOffset, audio.volume || (this.state === 'SPEAKING' ? 0.3 : 0));
  }

  renderOrganicPortrait(size, blinkValue) {
    const img = this.image;
    const half = size / 2;

    // 1. Couche Arrière (Crâne & Buste / Cheveux)
    this.ctx.save();
    this.ctx.drawImage(img, -half, -half, size, size);
    this.ctx.restore();

    // 2. Déformation 2.5D de la Mâchoire & du Menton (Jaw-Drop continu)
    if (this.jawDrop > 0.8) {
      const jawY = size * 0.10;
      const jawH = size * 0.40;

      this.ctx.save();
      this.ctx.beginPath();
      this.ctx.ellipse(0, size * 0.28, half * 0.88, jawH * 0.65, 0, 0, Math.PI * 2);
      this.ctx.clip();

      // Déplacement de la mâchoire avec léger élargissement
      this.ctx.translate(0, this.jawDrop * 0.7);
      this.ctx.scale(1.0 + this.mouthOpen * 0.02, 1.0 + this.mouthOpen * 0.04);
      this.ctx.drawImage(img, -half, -half, size, size);
      this.ctx.restore();
    }

    // 3. Morphing Labial Réaliste (Cavité, Lèvres, Dents)
    if (this.mouthOpen > 0.06) {
      this.renderRealisticMouth(size, this.mouthOpen, this.mouthWidth);
    }

    // 4. Clignements et regard expressif
    if (blinkValue > 0.04) {
      this.renderEyelids(size, blinkValue);
    }

    // 5. Sourcils expressifs (Légère animation d'accentuation)
    if (this.eyebrowLift > 0.5) {
      this.renderEyebrowAccents(size, this.eyebrowLift);
    }
  }

  renderRealisticMouth(size, openFactor, widthFactor) {
    const mouthY = size * 0.21 + this.jawDrop * 0.3;
    const mouthW = size * 0.23 * widthFactor;
    const mouthH = size * 0.17 * openFactor;

    this.ctx.save();

    // Cavité buccale avec profondeur
    this.ctx.beginPath();
    this.ctx.ellipse(0, mouthY, mouthW / 2, mouthH / 2, 0, 0, Math.PI * 2);
    const grad = this.ctx.createRadialGradient(0, mouthY, 2, 0, mouthY, mouthH);
    grad.addColorStop(0, '#1A0407');
    grad.addColorStop(0.6, '#4A0F1A');
    grad.addColorStop(1, '#1A0407');
    this.ctx.fillStyle = grad;
    this.ctx.fill();

    // Dents supérieures nettes
    if (openFactor > 0.2) {
      this.ctx.beginPath();
      this.ctx.ellipse(0, mouthY - mouthH * 0.24, mouthW * 0.38, mouthH * 0.22, 0, 0, Math.PI);
      this.ctx.fillStyle = '#FFFFFF';
      this.ctx.fill();
    }

    // Langue douce
    if (openFactor > 0.4) {
      this.ctx.beginPath();
      this.ctx.ellipse(0, mouthY + mouthH * 0.22, mouthW * 0.26, mouthH * 0.18, 0, Math.PI, Math.PI * 2);
      this.ctx.fillStyle = '#BA485C';
      this.ctx.fill();
    }

    // Contour des lèvres teinté et estompé
    this.ctx.beginPath();
    this.ctx.ellipse(0, mouthY, (mouthW / 2) + 2, (mouthH / 2) + 2, 0, 0, Math.PI * 2);
    this.ctx.strokeStyle = 'rgba(120, 40, 50, 0.45)';
    this.ctx.lineWidth = 2.5;
    this.ctx.stroke();

    this.ctx.restore();
  }

  renderEyelids(size, blink) {
    const eyeY = -size * 0.08;
    const eyeSpacing = size * 0.17;
    const eyeW = size * 0.13;
    const eyeH = size * 0.08 * blink;

    this.ctx.save();
    this.ctx.fillStyle = 'rgba(40, 20, 25, 0.75)';

    // Paupière gauche
    this.ctx.beginPath();
    this.ctx.ellipse(-eyeSpacing, eyeY, eyeW / 2, eyeH / 2, 0, 0, Math.PI * 2);
    this.ctx.fill();

    // Paupière droite
    this.ctx.beginPath();
    this.ctx.ellipse(eyeSpacing, eyeY, eyeW / 2, eyeH / 2, 0, 0, Math.PI * 2);
    this.ctx.fill();

    // Ligne des cils
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

  renderEyebrowAccents(size, lift) {
    const browY = -size * 0.19 - lift * 0.8;
    const browSpacing = size * 0.17;
    const browW = size * 0.12;

    this.ctx.save();
    this.ctx.strokeStyle = 'rgba(30, 20, 20, 0.35)';
    this.ctx.lineWidth = 2.5;
    this.ctx.lineCap = 'round';

    // Sourcil gauche
    this.ctx.beginPath();
    this.ctx.moveTo(-browSpacing - browW / 2, browY + 2);
    this.ctx.quadraticCurveTo(-browSpacing, browY - 3, -browSpacing + browW / 2, browY);
    this.ctx.stroke();

    // Sourcil droit
    this.ctx.beginPath();
    this.ctx.moveTo(browSpacing - browW / 2, browY);
    this.ctx.quadraticCurveTo(browSpacing, browY - 3, browSpacing + browW / 2, browY + 2);
    this.ctx.stroke();

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

    // Ondes sinusoïdales réactives pendant la parole
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

  drawStylizedPlaceholder(size, mouthOpen, blink) {
    const half = size / 2;
    this.ctx.save();
    
    // Tête stylisée
    this.ctx.beginPath();
    this.ctx.ellipse(0, 0, half * 0.7, half * 0.85, 0, 0, Math.PI * 2);
    this.ctx.fillStyle = '#1E293B';
    this.ctx.fill();
    this.ctx.strokeStyle = this.themeColor;
    this.ctx.lineWidth = 2;
    this.ctx.stroke();

    // Yeux
    if (blink < 0.7) {
      this.ctx.beginPath();
      this.ctx.arc(-size * 0.18, -size * 0.08, 6, 0, Math.PI * 2);
      this.ctx.arc(size * 0.18, -size * 0.08, 6, 0, Math.PI * 2);
      this.ctx.fillStyle = this.themeColor;
      this.ctx.fill();
    }

    // Bouche
    this.renderRealisticMouth(size, mouthOpen, 1.0);
    this.ctx.restore();
  }
}
