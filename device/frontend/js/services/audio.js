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
    
    this.initAudioContext();

    // Initialisation du client Simli
    this.simli = new SimliService('modal-avatar-video', 'simli-audio');
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

    // Assurez-vous que Simli est initialisé dès la première intention de parler
    if (!this.simli.isInitialized) {
      this.simli.init();
    }

    // Pré-chargement immédiat du blob en arrière-plan
    const audioPromise = ApiService.fetchTTSBlob(cleanText);
    this.audioQueue.push({ text: cleanText, audioPromise });
    this.processQueue();
  }

  // Convertisseur vers PCM16 à 16000Hz (Format requis par Simli)
  audioBufferToPCM16(audioBuffer) {
    const channelData = audioBuffer.getChannelData(0);
    const pcm16 = new Int16Array(channelData.length);
    for (let i = 0; i < channelData.length; i++) {
        let s = Math.max(-1, Math.min(1, channelData[i]));
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return new Uint8Array(pcm16.buffer);
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
          
          let playedSuccessfully = false;

          // Streaming via Simli (prioritaire si initialisé et modal ouvert)
          if (this.simli.isInitialized) {
             try {
                const arrayBuffer = await audioBlob.arrayBuffer();
                
                // Utiliser un OfflineAudioContext pour forcer le rééchantillonnage à 16000 Hz
                const offlineCtx = new (window.OfflineAudioContext || window.webkitOfflineAudioContext)(1, 48000 * 10, 16000);
                const decodedBuffer = await offlineCtx.decodeAudioData(arrayBuffer);
                
                // Extraire exactement la durée nécessaire
                const actualCtx = new (window.OfflineAudioContext || window.webkitOfflineAudioContext)(1, decodedBuffer.length, 16000);
                const source = actualCtx.createBufferSource();
                source.buffer = decodedBuffer;
                source.connect(actualCtx.destination);
                source.start(0);
                
                const resampledBuffer = await actualCtx.startRendering();
                const pcm16Data = this.audioBufferToPCM16(resampledBuffer);
                
                console.log("🚀 [Simli] Envoi de l'audio PCM16 au WebRTC...");
                await this.simli.sendAudioBuffer(pcm16Data);
                
                // Simuler le délai de lecture pour ne pas consommer toute la queue
                await new Promise(resolve => setTimeout(resolve, resampledBuffer.duration * 1000));
                
                playedSuccessfully = true;
             } catch (e) {
                console.warn("⚠️ [SimliService] Échec du streaming Simli :", e);
             }
          }

          // Fallback : Web Audio API directe
          if (!playedSuccessfully && this.audioCtx) {
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
            } catch (webAudioErr) {}
          }

          if (!playedSuccessfully) {
             await this.playWithAudioElement(audioBlob);
             playedSuccessfully = true;
          }

        } else if (this.speechSynthesis) {
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
      player.play().catch((e) => { URL.revokeObjectURL(audioUrl); this.currentPlayer = null; resolve(); });
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
