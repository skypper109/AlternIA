/**
 * Composant de contrôle du Tri-Vortex Alternia Core (Avatar Réactif 60 FPS).
 */

export class VortexUI {
  constructor({ coreWrapperId = 'alternia-core-wrapper', statusTextId = 'status-text', statusDotId = 'status-dot', visualizerId = 'audio-visualizer' } = {}) {
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
        this.updateBadge('Prêt', 'status-dot');
        this.setVisualizerActive(false);
        break;

      case 'LISTENING':
        this.coreWrapper.classList.add('state-listening');
        this.updateBadge(statusMessage || 'Écoute de l’élève...', 'status-dot listening');
        this.setVisualizerActive(true);
        break;

      case 'THINKING':
        this.coreWrapper.classList.add('state-thinking');
        this.updateBadge(statusMessage || 'Réflexion & RAG local...', 'status-dot thinking');
        this.setVisualizerActive(false);
        break;

      case 'SPEAKING':
        this.coreWrapper.classList.add('state-speaking');
        this.updateBadge(statusMessage || 'ALTA répond...', 'status-dot speaking');
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
