/**
 * Service de reconnaissance vocale Speech-to-Text (STT) haute fidélité.
 * Hybride & 100% Résilient :
 * 1. Web Speech API (transcription temps réel continue)
 * 2. MediaRecorder local automatique vers /api/stt (Faster-Whisper GPU)
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
    this.isStarting = false;
    this.isStopping = false;
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
          if (this.isRecording && this.recognition && !this.isStopping) {
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
    if (this.isStarting || this.isStopping) return;

    if (this.isRecording) {
      await this.stop();
    } else {
      await this.start();
    }
  }

  async start() {
    if (this.isRecording || this.isStarting) return;
    this.isStarting = true;
    this.currentTranscript = '';
    this.finalTranscriptAccumulated = '';
    this.audioChunks = [];

    if (this.onStart) this.onStart();

    // 1. Démarrer l'enregistrement micro physique MediaRecorder
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

        this.setupAudioAnalyser(this.stream);

        let mimeType = 'audio/webm';
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
    } catch (err) {
      console.warn("Accès microphone refusé :", err);
      if (this.onError) this.onError("Accès microphone requis.");
      this.isStarting = false;
      this.isRecording = false;
      return;
    }

    // 2. Démarrer Web Speech en parallèle
    if (this.recognition) {
      try {
        this.recognition.start();
      } catch (err) {}
    }

    this.isRecording = true;
    this.isStarting = false;
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
    if (!this.isRecording || this.isStopping) return;
    this.isStopping = true;
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

    // Délai pour s'assurer que tous les chunks sont dans audioChunks
    await new Promise(r => setTimeout(r, 150));

    await this.finalizeRecording();
    this.isStopping = false;
  }

  async finalizeRecording() {
    let text = (this.finalTranscriptAccumulated + ' ' + this.currentTranscript).trim();

    // Si Web Speech n'a pas capté de texte mais qu'on a un enregistrement audio
    if (!text && this.audioChunks.length > 0) {
      try {
        console.log("🎙️ [SpeechService] Transcription via Faster-Whisper GPU...");
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
      this.onEnd(text);
    }
  }
}
