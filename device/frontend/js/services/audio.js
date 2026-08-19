/**
 * Service de gestion audio, synthèse vocale et effets sonores (SFX).
 */

import { ApiService } from './api.js';

export class AudioService {
  constructor({ onSpeakingChange } = {}) {
    this.onSpeakingChange = onSpeakingChange;
    this.speechSynthesis = window.speechSynthesis;
    this.audioCtx = null;
    this.isMuted = false;
    this.audioQueue = [];
    this.isPlayingQueue = false;
    this.currentPlayer = null;

    this.initAudioContext();
  }

  initAudioContext() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.audioCtx = new AudioCtx();
    } catch (e) {
      console.warn("AudioContext non disponible :", e);
    }
  }

  playBeep(freq = 520, duration = 0.15) {
    if (!this.audioCtx || this.isMuted) return;
    try {
      if (this.audioCtx.state === 'suspended') this.audioCtx.resume();
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, this.audioCtx.currentTime);
      gain.gain.setValueAtTime(0.08, this.audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + duration);
      osc.connect(gain);
      gain.connect(this.audioCtx.destination);
      osc.start();
      osc.stop(this.audioCtx.currentTime + duration);
    } catch (e) {}
  }

  toggleMute() {
    this.isMuted = !this.isMuted;
    if (this.isMuted) {
      this.stop();
    }
    return this.isMuted;
  }

  stop() {
    if (this.currentPlayer) {
      this.currentPlayer.pause();
      this.currentPlayer = null;
    }
    if (this.speechSynthesis) {
      this.speechSynthesis.cancel();
    }
    this.audioQueue = [];
    this.isPlayingQueue = false;
    if (this.onSpeakingChange) {
      this.onSpeakingChange(false);
    }
  }

  cleanTextForTTS(text) {
    return text
      .replace(/\\\[[\s\S]*?\\\]/g, "la formule affichée")
      .replace(/\\\(.*?\\\)/g, "la formule")
      .replace(/\$\$.*?\$\$/g, "la formule :")
      .replace(/\$.*?\$/g, "")
      .replace(/[#*`_]/g, '')
      .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, "$1 sur $2")
      .replace(/\\sqrt\{([^}]+)\}/g, "racine carrée de $1")
      .replace(/\s+/g, ' ')
      .trim();
  }

  enqueueSentence(sentence) {
    if (this.isMuted || !sentence) return;
    const cleanText = this.cleanTextForTTS(sentence);
    if (cleanText.length < 2) return;

    // Pré-chargement immédiat du blob en arrière-plan
    const audioPromise = ApiService.fetchTTSBlob(cleanText);
    this.audioQueue.push({ text: cleanText, audioPromise });
    this.processQueue();
  }

  async processQueue() {
    if (this.isPlayingQueue || this.audioQueue.length === 0 || this.isMuted) {
      return;
    }

    this.isPlayingQueue = true;
    if (this.onSpeakingChange) this.onSpeakingChange(true);

    while (this.audioQueue.length > 0 && !this.isMuted) {
      const item = this.audioQueue.shift();
      try {
        const audioBlob = await item.audioPromise;
        if (audioBlob) {
          const audioUrl = URL.createObjectURL(audioBlob);
          const player = new Audio(audioUrl);
          this.currentPlayer = player;

          await new Promise((resolve) => {
            player.onended = () => {
              URL.revokeObjectURL(audioUrl);
              this.currentPlayer = null;
              resolve();
            };
            player.onerror = () => {
              URL.revokeObjectURL(audioUrl);
              this.currentPlayer = null;
              resolve();
            };
            player.play().catch(() => resolve());
          });
        } else if (this.speechSynthesis) {
          await this.speakWithWebSpeech(item.text);
        }
      } catch (err) {
        console.warn("Erreur lecture audio :", err);
      }
    }

    this.isPlayingQueue = false;
    if (this.onSpeakingChange) this.onSpeakingChange(false);
  }

  speakWithWebSpeech(text) {
    if (!this.speechSynthesis || this.isMuted || !text) return Promise.resolve();
    return new Promise((resolve) => {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'fr-FR';
      utterance.rate = 1.0;
      const voices = this.speechSynthesis.getVoices();
      const frVoice = voices.find(v => v.lang.startsWith('fr') && (v.name.includes('Denise') || v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Thomas')));
      if (frVoice) utterance.voice = frVoice;

      utterance.onend = resolve;
      utterance.onerror = resolve;
      this.speechSynthesis.speak(utterance);
    });
  }

  speakText(fullText, formulaSpeech = null) {
    this.stop();
    this.enqueueSentence(formulaSpeech || fullText);
  }
}
