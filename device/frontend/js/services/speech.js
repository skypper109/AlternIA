/**
 * Service de reconnaissance vocale (Speech-to-Text) hybride :
 * 1. Web Speech API (interim streaming en direct)
 * 2. MediaRecorder + Faster-Whisper local (/api/stt) pour une précision 100% hors-ligne.
 */

import { ApiService } from './api.js';

export class SpeechService {
  constructor({ onStart, onResult, onEnd, onError, onSimulationStart } = {}) {
    this.onStart = onStart;
    this.onResult = onResult;
    this.onEnd = onEnd;
    this.onError = onError;
    this.onSimulationStart = onSimulationStart;

    this.recognition = null;
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.stream = null;
    this.isRecording = false;
    this.currentTranscript = '';

    this.initWebSpeech();
  }

  initWebSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.lang = 'fr-FR';
      this.recognition.continuous = false;
      this.recognition.interimResults = true;

      this.recognition.onstart = () => {
        this.isRecording = true;
        this.currentTranscript = '';
        if (this.onStart) this.onStart();
      };

      this.recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
        }
        this.currentTranscript = transcript.trim();
        if (this.onResult) this.onResult(this.currentTranscript);
      };

      this.recognition.onerror = (event) => {
        console.warn('Erreur Web Speech :', event.error);
        if (event.error !== 'no-speech') {
          if (this.onError) this.onError(event.error);
        }
      };

      this.recognition.onend = async () => {
        if (!this.isRecording) return;
        this.isRecording = false;
        await this.finalizeRecording();
      };
    }
  }

  async toggle() {
    if (this.isRecording) {
      await this.stop();
    } else {
      await this.start();
    }
  }

  async start() {
    this.isRecording = true;
    this.currentTranscript = '';
    this.audioChunks = [];

    if (this.onStart) this.onStart();

    // 1. Démarrer l'enregistrement audio matériel via MediaRecorder
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.mediaRecorder = new MediaRecorder(this.stream);
        this.mediaRecorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) {
            this.audioChunks.push(e.data);
          }
        };
        this.mediaRecorder.start(250); // morceaux de 250ms
      }
    } catch (err) {
      console.warn("Microphone MediaRecorder non disponible ou accès refusé :", err);
    }

    // 2. Démarrer Web Speech pour le retour visuel en temps réel
    if (this.recognition) {
      try {
        this.recognition.start();
      } catch (err) {
        // En cas d'erreur de recognition, on se repose sur MediaRecorder
      }
    } else if (!this.mediaRecorder) {
      // Si ni Web Speech ni MediaRecorder ne sont dispo, mode simulation
      this.simulateVoiceInput();
    }
  }

  async stop() {
    if (!this.isRecording) return;
    this.isRecording = false;

    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }

    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }

    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }

    await this.finalizeRecording();
  }

  async finalizeRecording() {
    let finalTranscription = this.currentTranscript;

    // Si Web Speech n'a rien capté ou n'est pas dispo, envoyer l'audio au STT Faster-Whisper local
    if (!finalTranscription && this.audioChunks.length > 0) {
      const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
      if (audioBlob.size > 1000) {
        finalTranscription = await ApiService.transcribeAudioBlob(audioBlob);
      }
    }

    if (this.onEnd) {
      this.onEnd(finalTranscription);
    }
  }

  simulateVoiceInput() {
    if (this.onSimulationStart) this.onSimulationStart();
    this.isRecording = true;
    if (this.onStart) this.onStart();

    setTimeout(() => {
      const sampleQueries = [
        "C'est quoi la photosynthèse de façon simple ?",
        "Donne-moi la formule de Moivre pour les nombres complexes",
        "Quelle est la deuxième loi de Newton en physique ?",
        "Comment calcule-t-on le pH d'une solution aqueuse ?",
        "Explique-moi la formule de l'énergie cinétique"
      ];
      const query = sampleQueries[Math.floor(Math.random() * sampleQueries.length)];
      this.isRecording = false;
      if (this.onResult) this.onResult(query);
      if (this.onEnd) this.onEnd(query);
    }, 2000);
  }
}
