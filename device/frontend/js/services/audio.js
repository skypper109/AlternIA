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
    this.currentVoice = 'henri'; // Voix TTS masculine par défaut (Henri)
    
    this.enableSimli = false; // Désactivé par défaut ! Activé UNIQUEMENT quand l'avatar modal est ouvert
    this.simli = new SimliService('modal-avatar-video', 'simli-audio');

    // Déblocage automatique de l'AudioContext dès le premier clic/toucher utilisateur
    this.setupUserGestureUnlock();
  }

  setSimliActive(active) {
    this.enableSimli = !!active;
    if (!active && this.simli) {
      this.simli.close();
    }
  }

  setVoice(voice) {
    if (voice && typeof voice === 'string') {
      this.currentVoice = voice.trim().toLowerCase();
      console.log(`🎙️ [AudioService] Voix configurée : ${this.currentVoice}`);
    }
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

  enqueueSentence(sentence, voiceOverride = null) {
    if (this.isMuted || !sentence) return;
    const cleanText = this.cleanTextForTTS(sentence);
    if (cleanText.length < 2) return;

    this.ensureAudioContext();

    const voiceToUse = voiceOverride || this.currentVoice || 'henri';
    console.log(`🎙️ [AudioService] Synthèse vocale (${voiceToUse}) : "${cleanText.substring(0, 45)}..."`);

    // Pré-chargement immédiat du blob en arrière-plan
    const audioPromise = ApiService.fetchTTSBlob(cleanText, voiceToUse);
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
        console.log("🔊 [AudioService] Traitement de la phrase :", item.text);
        const audioBlob = await item.audioPromise;

        if (audioBlob && audioBlob.size > 100) {
          const isSimliActive = this.enableSimli && this.simli;
          let simliReady = false;

          // 1. Envoi vers Simli WebRTC UNIQUEMENT si l'avatar modal est actif
          if (isSimliActive) {
            // Si la connexion Simli est en cours, attendre qu'elle s'établisse pour ne pas perdre la voix
            if (!this.simli.isConnected && this.simli.isConnecting) {
              await this.simli.waitForConnection(3500);
            }
            if (this.simli.isConnected) {
              try {
                const { pcm16Data, duration } = await this.resampleToPCM16(audioBlob);
                console.log(`🚀 [Simli] Envoi audio PCM16 (${duration.toFixed(1)}s) pour Lip-Sync avatar...`);
                this.simli.sendAudioBuffer(pcm16Data);
                simliReady = true;
              } catch (resampleErr) {
                console.warn("⚠️ [AudioService] Erreur rééchantillonnage Simli :", resampleErr);
              }
            }
          }

          // 2. Lecture audio avec analyseur FFT
          // RÈGLE ANTI-DOUBLON STRICTE :
          // Si Simli est actif et connecté, le son sort EXCLUSIVEMENT par le flux WebRTC de Simli.
          // Le gain local audioCtx est forcé à 0 (silence absolu sur les haut-parleurs locaux).
          // Il reste connecté uniquement à l'analyser FFT pour animer les ondes visuelles.
          // Si Simli a échoué ou n'est pas actif, le gain passe à 1 pour jouer le son en local.
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

              const gainNode = this.audioCtx.createGain();
              // Silence complet en local si Simli est actif et diffuse le son
              gainNode.gain.value = (isSimliActive && simliReady) ? 0.0 : 1.0;

              source.connect(gainNode);
              gainNode.connect(this.audioCtx.destination);

              if (this.analyser) {
                this.analyser.disconnect();
                // Toujours connecter à l'analyseur pour garder les ondes visuelles en direct
                source.connect(this.analyser);
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

          // 3. Fallback HTML5 Audio player UNIQUEMENT si Simli n'est pas actif
          if (!played && (!isSimliActive || !simliReady)) {
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

  speakText(fullText, formulaSpeech = null, voiceOverride = null) {
    this.stop();
    this.enqueueSentence(formulaSpeech || fullText, voiceOverride);
  }
}
