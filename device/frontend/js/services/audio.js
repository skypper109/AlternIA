/**
/**
 * Service de gestion audio, synthèse vocale et analyseur de fréquences pour le Lip-Sync.
 */

import { ApiService } from './api.js';

export class AudioService {
  constructor({ onSpeakingChange, onAnalyserReady } = {}) {
    this.onSpeakingChange = onSpeakingChange;
    this.onAnalyserReady = onAnalyserReady;
    this.speechSynthesis = window.speechSynthesis;
    this.audioCtx = null;
    this.analyser = null;
    this.isMuted = false;
    this.audioQueue = [];
    this.isPlayingQueue = false;
    this.currentPlayer = null;

    this.initAudioContext();
  }

  initAudioContext() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.audioCtx = new AudioCtx();
        this.analyser = this.audioCtx.createAnalyser();
        this.analyser.fftSize = 256;
        this.analyser.smoothingTimeConstant = 0.8;
        if (this.onAnalyserReady) {
          this.onAnalyserReady(this.analyser);
        }
      }
    } catch (e) {
      console.warn("AudioContext non disponible :", e);
    }
  }

  getAnalyser() {
    return this.analyser;
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
    this.audioQueue = [];
    if (this.currentPlayer) {
      this.currentPlayer.pause();
      this.currentPlayer.removeAttribute('src');
      this.currentPlayer.load();
      this.currentPlayer = null;
    }
    if (this.currentSource) {
      try { this.currentSource.stop(); } catch(e){}
      this.currentSource = null;
    }
    if (this.speechSynthesis) {
      this.speechSynthesis.cancel();
    }
    this.isPlayingQueue = false;
    if (this.onSpeakingChange) this.onSpeakingChange(false);
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
        console.log("🔊 [AudioService] Préparation lecture :", item.text);
        const audioBlob = await item.audioPromise;
        if (audioBlob && audioBlob.size > 100) {
          console.log("🔊 [AudioService] Blob TTS reçu :", audioBlob.size, "octets");
          
          let playedSuccessfully = false;

          // Tentative 1 : Web Audio API directe (BufferSource)
          if (this.audioCtx) {
            try {
              if (this.audioCtx.state === 'suspended') {
                await this.audioCtx.resume();
              }
              const arrayBuffer = await audioBlob.arrayBuffer();
              const bufferCopy = arrayBuffer.slice(0);
              
              const audioBuffer = await new Promise((res, rej) => {
                this.audioCtx.decodeAudioData(bufferCopy, res, rej);
              });

              const source = this.audioCtx.createBufferSource();
              source.buffer = audioBuffer;
              this.currentSource = source;

              if (this.analyser) {
                source.connect(this.analyser);
                this.analyser.connect(this.audioCtx.destination);
              } else {
                source.connect(this.audioCtx.destination);
              }

              await new Promise((resolve) => {
                source.onended = () => {
                  this.currentSource = null;
                  resolve();
                };
                source.start(0);
              });
              playedSuccessfully = true;
              console.log("🔊 [AudioService] Phrase jouée avec succès via Web Audio");
            } catch (webAudioErr) {
              console.warn("⚠️ [AudioService] Web Audio BufferSource a échoué :", webAudioErr);
            }
          }

          // Tentative 2 : HTMLAudioElement si BufferSource a échoué
          if (!playedSuccessfully) {
            try {
              await this.playWithAudioElement(audioBlob);
              playedSuccessfully = true;
              console.log("🔊 [AudioService] Phrase jouée via HTMLAudioElement");
            } catch (elErr) {
              console.warn("⚠️ [AudioService] HTMLAudioElement a échoué :", elErr);
            }
          }

          // Tentative 3 : Synthèse vocale navigateur WebSpeech de secours
          if (!playedSuccessfully && this.speechSynthesis) {
            console.log("🔊 [AudioService] Fallback vers WebSpeech pour :", item.text);
            await this.speakWithWebSpeech(item.text);
          }

        } else if (this.speechSynthesis) {
          console.log("🔊 [AudioService] Aucun blob TTS reçu, lecture via WebSpeech");
          await this.speakWithWebSpeech(item.text);
        }
      } catch (err) {
        console.warn("❌ [AudioService] Erreur globale lecture audio :", err);
      }
    }

    this.isPlayingQueue = false;
    if (this.onSpeakingChange) this.onSpeakingChange(false);
  }

  playWithAudioElement(audioBlob) {
    return new Promise((resolve) => {
      const audioUrl = URL.createObjectURL(audioBlob);
      const player = new Audio(audioUrl);
      this.currentPlayer = player;
      
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
      player.play().catch((e) => {
        console.warn("AudioElement play failed (Autoplay policy?):", e);
        URL.revokeObjectURL(audioUrl);
        this.currentPlayer = null;
        resolve();
      });
    });
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
