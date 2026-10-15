/**
 * Service de reconnaissance vocale Speech-to-Text (STT) haute fidélité.
 * Hybride & 100% Réactif au clic unique (1 clic pour enregistrer, 1 clic pour couper et envoyer) :
 * 1. Web Speech API immédiat (transcription mot par mot en temps réel)
 * 2. MediaRecorder local automatique vers /api/stt (Faster-Whisper GPU si Web Speech vide)
 * 3. Feedback visuel réactif en direct.
 */

import { ApiService } from './api.js';

export class SpeechService {
  constructor({ onStart, onTranscript, onResult, onEnd, onError, onAudioLevel } = {}) {
    this.onStart = onStart;
    this.onTranscript = onTranscript || onResult;
    this.onResult = this.onTranscript;
    this.onEnd = onEnd;
    this.onError = onError;
    this.onAudioLevel = onAudioLevel;

    this.recognition = null;
    this.isRecording = false;
    this.currentTranscript = '';
    this.finalTranscriptAccumulated = '';

    this.mediaRecorder = null;
    this.audioChunks = [];
    this.stream = null;
    this.audioCtx = null;
    this.analyser = null;
    this.animFrameId = null;

    this.initWebSpeech();
  }

  initWebSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        this.recognition = new SpeechRecognition();
        this.recognition.lang = 'fr-FR';
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;

        this.recognition.onstart = () => {
          this.isRecording = true;
        };

        this.recognition.onresult = (event) => {
          let interimTranscript = '';
          let finalChunk = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
              finalChunk += transcript + ' ';
            } else {
              interimTranscript += transcript;
            }
          }
          if (finalChunk) {
            this.finalTranscriptAccumulated += finalChunk;
          }
          this.currentTranscript = (this.finalTranscriptAccumulated + interimTranscript).trim();
          if (this.onTranscript && this.currentTranscript) {
            this.onTranscript(this.currentTranscript);
          }
        };

        this.recognition.onerror = (event) => {
          console.warn('Statut Web Speech :', event.error);
        };

        this.recognition.onend = () => {
          if (this.isRecording && this.recognition) {
            try {
              this.recognition.start();
            } catch (e) {}
          }
        };
      } catch (e) {
        console.warn("Web Speech API non disponible :", e);
      }
    }
  }

  toggleListening() {
    return this.toggle();
  }

  isListening() {
    return this.isRecording;
  }

  async toggle() {
    if (this.isRecording) {
      await this.stop();
    } else {
      await this.start();
    }
  }

  async start() {
    if (this.isRecording) return;
    this.isRecording = true;
    this.currentTranscript = '';
    this.finalTranscriptAccumulated = '';
    this.audioChunks = [];

    // Notifier immédiatement l'UI pour mise à jour visuelle instantanée
    if (this.onStart) {
      this.onStart();
    }

    // 1. Démarrer Web Speech API IMMÉDIATEMENT (sans attendre getUserMedia)
    if (this.recognition) {
      try {
        this.recognition.start();
      } catch (err) {
        console.warn("Web Speech start :", err);
      }
    }

    // 2. Initialiser le micro physique en tâche de fond pour l'analyseur et le fallback Whisper
    this.startMediaRecorderBackground().catch((err) => {
      console.warn("MediaRecorder background error :", err);
    });
  }

  async startMediaRecorderBackground() {
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        this.stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,
            sampleRate: 16000,
            echoCancellation: true,
            noiseSuppression: true
          }
        });

        // Si l'utilisateur a déjà cliqué pour couper pendant l'autorisation, arrêter immédiatement
        if (!this.isRecording) {
          if (this.stream) {
            this.stream.getTracks().forEach(t => t.stop());
            this.stream = null;
          }
          return;
        }

        this.setupAudioAnalyser(this.stream);

        let mimeType = 'audio/webm';
        if (typeof MediaRecorder !== 'undefined') {
          if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
            mimeType = 'audio/webm;codecs=opus';
          } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
            mimeType = 'audio/mp4';
          }

          this.mediaRecorder = new MediaRecorder(this.stream, { mimeType });
          this.mediaRecorder.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) {
              this.audioChunks.push(e.data);
            }
          };
          this.mediaRecorder.start(100);
        }
      }
    } catch (err) {
      console.warn("Accès microphone partiel ou refusé :", err);
    }
  }

  setupAudioAnalyser(stream) {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.audioCtx = new AudioCtx();
        if (this.audioCtx.state === 'suspended') {
          this.audioCtx.resume();
        }
        const source = this.audioCtx.createMediaStreamSource(stream);
        this.analyser = this.audioCtx.createAnalyser();
        this.analyser.fftSize = 256;
        source.connect(this.analyser);

        const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        const checkLevel = () => {
          if (!this.isRecording) return;
          this.analyser.getByteFrequencyData(dataArray);
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
          const avg = sum / dataArray.length / 255;
          if (this.onAudioLevel) this.onAudioLevel(avg);
          this.animFrameId = requestAnimationFrame(checkLevel);
        };
        this.animFrameId = requestAnimationFrame(checkLevel);
      }
    } catch (e) {}
  }

  async stop() {
    if (!this.isRecording) return;
    this.isRecording = false;

    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }

    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }

    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      try {
        this.mediaRecorder.stop();
      } catch (e) {}
    }

    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }

    if (this.audioCtx) {
      try {
        this.audioCtx.close();
      } catch (e) {}
      this.audioCtx = null;
    }

    // Récupérer le texte transcrit immédiatement
    let text = (this.finalTranscriptAccumulated + ' ' + this.currentTranscript).trim();

    // Si Web Speech a déjà capturé du texte, on l'envoie SANS ATTENDRE pour réactivité instantanée
    if (text && text.length > 0) {
      if (this.onEnd) {
        this.onEnd(text);
      }
      return;
    }

    // Fallback : si Web Speech n'a rien capturé mais qu'on a des morceaux audio MediaRecorder
    if (this.audioChunks.length > 0) {
      try {
        console.log("🎙️ [SpeechService] Transcription de secours Faster-Whisper GPU...");
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        if (audioBlob.size > 200) {
          text = await ApiService.transcribeAudioBlob(audioBlob);
          console.log("📝 [SpeechService] Texte transcrit :", text);
        }
      } catch (e) {
        console.warn("Erreur transcription locale :", e);
      }
    }

    if (this.onEnd) {
      this.onEnd(text || '');
    }
  }
}
