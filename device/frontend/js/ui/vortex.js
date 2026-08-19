/**
 * Composant de contrôle de l'Avatar Pédagogique Alta (Halo Chromatique & Égaliseur Audio).
 */

export class VortexUI {
  constructor({
    coreWrapperId = 'alta-avatar-card',
    statusTextId = 'status-text',
    statusDotId = 'status-dot',
    visualizerId = 'audio-waveform-container'
  } = {}) {
    this.coreWrapper = document.getElementById(coreWrapperId);
    this.statusText = document.getElementById(statusTextId);
    this.statusDot = document.getElementById(statusDotId);
    this.visualizer = document.getElementById(visualizerId);
    this.currentState = 'IDLE';
  }

  setState(newState, statusMessage = null) {
    this.currentState = newState;
    if (!this.coreWrapper) return;

    this.coreWrapper.classList.remove('state-idle', 'state-listening', 'state-thinking', 'state-speaking');

    switch (newState) {
      case 'IDLE':
        this.coreWrapper.classList.add('state-idle');
        this.updateBadge('Prêt', 'w-2 h-2 rounded-full bg-emerald-400');
        this.setVisualizerActive(false);
        break;

      case 'LISTENING':
        this.coreWrapper.classList.add('state-listening');
        this.updateBadge(statusMessage || 'Écoute au micro...', 'w-2 h-2 rounded-full bg-cyan-400 animate-pulse');
        this.setVisualizerActive(true);
        break;

      case 'THINKING':
        this.coreWrapper.classList.add('state-thinking');
        this.updateBadge(statusMessage || 'Consultation du programme...', 'w-2 h-2 rounded-full bg-amber-400 animate-spin');
        this.setVisualizerActive(false);
        break;

      case 'SPEAKING':
        this.coreWrapper.classList.add('state-speaking');
        this.updateBadge(statusMessage || 'ALTA explique...', 'w-2 h-2 rounded-full bg-purple-400');
        this.setVisualizerActive(true);
        break;
    }
  }

  updateBadge(text, dotClass) {
    if (this.statusText) this.statusText.textContent = text;
    if (this.statusDot) this.statusDot.className = dotClass;
  }

  setVisualizerActive(active) {
    if (!this.visualizer) return;
    this.visualizer.style.opacity = active ? '1' : '0.2';
  }
}
