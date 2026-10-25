/**
 * AlternIA Device Sync Service — Synchronisation Temps Réel HDMI Kiosk (TV) & Matériel Pi 5.
 * 
 * Assure la communication bidirectionnelle instantanée entre :
 * 1. Les 4 boutons physiques du boîtier (Niveaux 1-2-3 et Micro N4)
 * 2. L'interface Kiosk affichée sur la TV via le port HDMI
 * 3. La souris et le clavier USB branchés sur le Raspberry Pi 5
 */

export class DeviceSyncService {
  constructor(app) {
    this.app = app;
    this.ws = null;
    this.reconnectTimer = null;
    this.isRecordingRemotely = false;

    this.connect();
    this.initKeyboardShortcuts();
  }

  /**
   * Connexion WebSocket vers le hub de synchronisation (/ws/device/sync)
   */
  connect() {
    if (typeof window === 'undefined') return;

    const loc = window.location;
    const protocol = loc.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${loc.host}/ws/device/sync`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log("📺 [DeviceSync] Connecté au bus matériel Kiosk TV (Pi 5 + Boutons) !");
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          this.handleEvent(msg.event, msg.data || {});
        } catch (e) {
          console.warn("⚠️ [DeviceSync] Message invalide :", e);
        }
      };

      this.ws.onerror = () => {
        this.scheduleReconnect();
      };

      this.ws.onclose = () => {
        this.scheduleReconnect();
      };
    } catch (e) {
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    if (!this.reconnectTimer) {
      this.reconnectTimer = setTimeout(() => {
        this.reconnectTimer = null;
        this.connect();
      }, 2500);
    }
  }

  /**
   * Réception et traitement des événements matériels émis par les boutons du boîtier
   */
  handleEvent(event, data) {
    console.log(`📡 [DeviceSync] Événement matériel reçu : ${event}`, data);

    switch (event) {
      case 'initial_state':
        if (data.selected_class && data.selected_class !== this.app.currentClass) {
          this.app.selectClass(data.selected_class, false);
        }
        if (data.state === 'listening') {
          this.handleRecordingStart();
        } else if (data.state === 'thinking') {
          this.handleThinking();
        }
        break;

      case 'class_selected':
        if (data.class) {
          this.app.selectClass(data.class, true);
        }
        break;

      case 'recording_started':
      case 'listening':
        this.handleRecordingStart();
        break;

      case 'recording_stopped':
      case 'thinking':
        this.handleThinking();
        break;

      case 'user_transcript':
        this.handleUserTranscript(data.text);
        break;

      case 'ai_response':
      case 'answer':
        this.handleAiResponse(data.text, data.sources);
        break;

      case 'speaking':
        if (data.speaking) {
          document.body.dataset.state = 'speaking';
          if (this.app.vortex) this.app.vortex.setState('SPEAKING', 'Enseignant explique...');
          if (this.app.modalVortex) this.app.modalVortex.setState('SPEAKING', 'Enseignant explique...');
        } else {
          document.body.dataset.state = 'idle';
          if (this.app.vortex) this.app.vortex.setState('IDLE', 'Prêt à répondre');
          if (this.app.modalVortex) this.app.modalVortex.setState('IDLE', 'Prêt à répondre');
        }
        break;

      case 'idle':
        this.handleIdle();
        break;
    }
  }

  handleRecordingStart() {
    this.isRecordingRemotely = true;
    // Interruption immédiate de toute parole précédente (Barge-in instantané)
    if (this.app.audio) {
      this.app.audio.stop();
    }
    document.body.dataset.state = 'listening';
    if (this.app.vortex) this.app.vortex.setState('LISTENING', 'Écoute en cours...');
    if (this.app.modalVortex) this.app.modalVortex.setState('LISTENING', 'Écoute en cours...');
    this.app.setMicRecordingState(true);
    this.app.showListeningBanner("Je t'écoute… parle maintenant");
  }

  handleThinking() {
    this.isRecordingRemotely = false;
    document.body.dataset.state = 'thinking';
    if (this.app.vortex) this.app.vortex.setState('THINKING', 'Consultation du programme officiel...');
    if (this.app.modalVortex) this.app.modalVortex.setState('THINKING', 'Consultation du programme...');
    this.app.setMicRecordingState(false);
    this.app.showListeningBanner("Consultation d'ALTA en cours...");
  }

  handleUserTranscript(text) {
    if (!text) return;
    this.app.hideListeningBanner();
    if (this.app.questionInput) this.app.questionInput.value = text;
    if (this.app.modalQuestionInput) this.app.modalQuestionInput.value = text;
    // Afficher directement la question de l'élève sur l'écran TV
    this.app.appendMessage({ role: 'user', text });
  }

  handleAiResponse(text, sources) {
    if (!text) return;
    document.body.dataset.state = 'speaking';
    if (this.app.vortex) this.app.vortex.setState('SPEAKING', 'Enseignant explique...');
    if (this.app.modalVortex) this.app.modalVortex.setState('SPEAKING', 'Enseignant explique...');

    const sourceDoc = (sources && sources[0] && sources[0].document) ? sources[0].document : 'Programme Officiel du Mali';
    if (this.app.ragSourceBadge) this.app.ragSourceBadge.textContent = sourceDoc;

    // Afficher l'explication complète détaillée avec KaTeX et mise en page sur la TV
    this.app.appendMessage({ role: 'assistant', text, source: sourceDoc });
  }

  handleIdle() {
    document.body.dataset.state = 'idle';
    if (this.app.vortex) this.app.vortex.setState('IDLE', 'Prêt à répondre');
    if (this.app.modalVortex) this.app.modalVortex.setState('IDLE', 'Prêt à répondre');
    this.app.setMicRecordingState(false);
    this.app.hideListeningBanner();
  }

  /**
   * Raccourcis Clavier & Souris pour TV : Permet aux élèves d'utiliser clavier/souris sans manette
   */
  initKeyboardShortcuts() {
    window.addEventListener('keydown', (e) => {
      const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
      if (activeTag === 'input' || activeTag === 'textarea') {
        return;
      }

      // Touches numériques 1, 2, 3 pour changer de cycle
      if (e.key === '1') {
        this.app.selectClass('6eme');
      } else if (e.key === '2') {
        this.app.selectClass('10eme');
      } else if (e.key === '3') {
        this.app.selectClass('12eme');
      } else if (e.key === ' ' || e.key === 'm' || e.key === 'M') {
        // Espace ou M : Toggle Micro
        e.preventDefault();
        if (this.app.micBtn) this.app.micBtn.click();
      } else if (e.key === 'Escape') {
        // Échap : Revenir à l'accueil
        this.app.showScreen('welcome');
      } else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
        // N'importe quelle lettre tapée au clavier active le champ de recherche/question
        if (this.app.currentScreen === 'welcome') {
          this.app.showScreen('workspace');
        }
        setTimeout(() => {
          if (this.app.questionInput) {
            this.app.questionInput.focus();
          }
        }, 50);
      }
    });
  }

  /**
   * Transmet un événement depuis l'interface vers le contrôleur matériel
   */
  notifyEvent(event, data = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify({ event, data }));
      } catch (e) {}
    }
    fetch('/api/device/event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event, data })
    }).catch(() => {});
  }
}
