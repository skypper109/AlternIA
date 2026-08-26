/**
 * Composant de contrôle de l'Avatar Pédagogique Alta (Halo Chromatique & Moteur 2.5D).
 */

import { DeviceAvatarAnimator } from './avatar-animator.js';

export class VortexUI {
  constructor({
    coreWrapperId = 'alta-avatar-card',
    statusTextId = 'status-text',
    statusDotId = 'status-dot',
    canvasId = 'alta-avatar-canvas',
    defaultImageUrl = null
  } = {}) {
    this.coreWrapper = document.getElementById(coreWrapperId);
    this.statusText = document.getElementById(statusTextId);
    this.statusDot = document.getElementById(statusDotId);
    this.currentState = 'IDLE';

    // Initialisation du Moteur d'Animation Faciale 2.5D
    const canvas = document.getElementById(canvasId);
    if (canvas) {
      this.animator = new DeviceAvatarAnimator(canvas, {
        themeColor: '#0284C7',
        enableMouseTracking: false
      });
      if (defaultImageUrl) {
        this.animator.setImage(defaultImageUrl);
      }
    } else {
      this.animator = null;
    }
  }

  setAudioAnalyser(analyser) {
    if (this.animator) {
      this.animator.setAudioAnalyser(analyser);
    }
  }

  setAvatarImage(imageUrl, name = null, landmarks = null) {
    if (this.animator && imageUrl) {
      this.animator.setImage(imageUrl, landmarks);
    }
    const nameEl = document.getElementById('alta-avatar-name');
    if (nameEl && name) {
      nameEl.textContent = name;
    }
  }

  setThemeColor(color) {
    if (this.animator && color) {
      this.animator.setThemeColor(color);
    }
  }

  setState(newState, statusMessage = null) {
    this.currentState = newState;
    if (this.animator) {
      this.animator.setState(newState);
    }

    if (this.statusText) {
      switch (newState) {
        case 'IDLE':
          this.updateBadge(statusMessage || 'Prêt à répondre', 'w-2 h-2 rounded-full bg-emerald-400');
          break;
        case 'LISTENING':
          this.updateBadge(statusMessage || 'Je vous écoute...', 'w-2 h-2 rounded-full bg-cyan-400 animate-pulse');
          break;
        case 'THINKING':
          this.updateBadge(statusMessage || 'Consultation du programme...', 'w-2 h-2 rounded-full bg-amber-400 animate-spin');
          break;
        case 'SPEAKING':
          this.updateBadge(statusMessage || 'Enseignant explique...', 'w-2 h-2 rounded-full bg-purple-400');
          break;
      }
    }
  }

  updateBadge(text, dotClass) {
    if (this.statusText) this.statusText.textContent = text;
    if (this.statusDot) this.statusDot.className = dotClass;
  }
}
