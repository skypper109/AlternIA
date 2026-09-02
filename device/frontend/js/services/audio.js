/**
/**
 * Service de gestion audio, synthèse vocale et analyseur de fréquences pour le Lip-Sync.
 */

import { ApiService } from './api.js';
import { SimliService } from './simli.js';

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
    this.currentSource = null;
    
    this.ENABLE_SIMLI = true; // Streaming Simli en parallèle si connecté
    this.simli = new SimliService('modal-avatar-video', 'simli-audio');

    // Déblocage automatique de l'AudioContext dès le premier clic/toucher utilisateur
    this.setupUserGestureUnlock();
  }

  setupUserGestureUnlock() {
    const unlock = () => {
      this.ensureAudioContext();
      document.removeEventListener('click', unlock);
      document.removeEventListener('touchstart', unlock);
      document.removeEventListener('keydown', unlock);
    };
    document.addEventListener('click', unlock, { once: true, passive: true });
    document.addEventListener('touchstart', unlock, { once: true, passive: true });
    document.addEventListener('keydown', unlock, { once: true, passive: true });
  }

  initAudioContext() {
    try {
      if (!this.audioCtx) {
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
      }
    } catch (e) {
      console.warn("AudioContext non disponible :", e);
    }
  }

  ensureAudioContext() {
    this.initAudioContext();
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume().catch(() => {});
    }
  }

  getAnalyser() {
    return this.analyser;
  }

  playBeep(freq = 520, duration = 0.15) {
    if (this.isMuted) return;
    this.ensureAudioContext();
    if (!this.audioCtx) return;
    try {
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

    this.ensureAudioContext();

    // Pré-chargement immédiat du blob en arrière-plan
    const audioPromise = ApiService.fetchTTSBlob(cleanText);
    this.audioQueue.push({ text: cleanText, audioPromise });
    this.processQueue();
  }

  async resampleToPCM16(audioBlob) {
    const arrayBuffer = await audioBlob.arrayBuffer();
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    const tempCtx = new AudioCtx();
    const audioBuffer = await tempCtx.decodeAudioData(arrayBuffer);
    try { await tempCtx.close(); } catch (e) {}

    const targetSampleRate = 16000;
    const targetLength = Math.max(1, Math.ceil(audioBuffer.duration * targetSampleRate));
    const offlineCtx = new (window.OfflineAudioContext || window.webkitOfflineAudioContext)(1, targetLength, targetSampleRate);

    const source = offlineCtx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(offlineCtx.destination);
    source.start(0);

    const renderedBuffer = await offlineCtx.startRendering();
    const channelData = renderedBuffer.getChannelData(0);

    const pcm16 = new Int16Array(channelData.length);
    for (let i = 0; i < channelData.length; i++) {
      const s = Math.max(-1, Math.min(1, channelData[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return { pcm16Data: pcm16.buffer, duration: audioBuffer.duration };
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
        console.log("🔊 [AudioService] Lecture de la phrase :", item.text);
        const audioBlob = await item.audioPromise;

        if (audioBlob && audioBlob.size > 100) {
          // 1. Envoi parallèle vers Simli WebRTC (si connecté pour l'avatar vidéo)
          if (this.ENABLE_SIMLI && this.simli && this.simli.isConnected) {
            this.resampleToPCM16(audioBlob).then(({ pcm16Data, duration }) => {
              console.log(`🚀 [Simli] Envoi audio PCM16 (${(duration).toFixed(1)}s) vers WebRTC...`);
              this.simli.sendAudioBuffer(pcm16Data);
            }).catch(() => {});
          }

          // 2. Lecture audio locale directe avec analyseur FFT pour le Vortex
          let played = false;
          this.ensureAudioContext();

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
              played = true;
            } catch (webAudioErr) {
              console.warn("⚠️ [AudioService] Échec Web Audio API, bascule sur Audio HTML5 :", webAudioErr);
            }
          }

          // 3. Fallback : HTML5 Audio player
          if (!played) {
            await this.playWithAudioElement(audioBlob);
          }

        } else if (this.speechSynthesis) {
          // 4. Fallback ultime : Web Speech API si le backend n'a pas produit de blob
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
      player.onended = () => { URL.revokeObjectURL(audioUrl); this.currentPlayer = null; resolve(); };
      player.onerror = () => { URL.revokeObjectURL(audioUrl); this.currentPlayer = null; resolve(); };
      player.play().catch(() => { URL.revokeObjectURL(audioUrl); this.currentPlayer = null; resolve(); });
    });
  }

  speakWithWebSpeech(text) {
    if (!this.speechSynthesis || this.isMuted || !text) return Promise.resolve();
    return new Promise((resolve) => {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'fr-FR';
      const voices = this.speechSynthesis.getVoices();
      const frVoice = voices.find(v => v.lang.startsWith('fr'));
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
