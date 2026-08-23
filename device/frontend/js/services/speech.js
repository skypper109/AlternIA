/**
 * Service de reconnaissance vocale Speech-to-Text (STT) haute fidélité.
 * Mode continu interactif : Touchez pour parler, touchez pour terminer et poser la question.
 */

import { ApiService } from './api.js';

export class SpeechService {
  constructor({ onStart, onResult, onEnd, onError } = {}) {
    this.onStart = onStart;
    this.onResult = onResult;
    this.onEnd = onEnd;
    this.onError = onError;

    this.recognition = null;
    this.isRecording = false;
    this.currentTranscript = '';
    this.finalTranscriptAccumulated = '';
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.stream = null;

    this.initWebSpeech();
  }

  initWebSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        this.recognition = new SpeechRecognition();
        this.recognition.lang = 'fr-FR';
        this.recognition.continuous = true; // Permet de parler en continu
        this.recognition.interimResults = true; // Transcription en temps réel

        this.recognition.onstart = () => {
          this.isRecording = true;
          this.currentTranscript = '';
          this.finalTranscriptAccumulated = '';
          if (this.onStart) this.onStart();
        };

        this.recognition.onresult = (event) => {
          let interimTranscript = '';
          let finalChunk = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalChunk += event.results[i][0].transcript + ' ';
            } else {
              interimTranscript += event.results[i][0].transcript;
            }
          }
          if (finalChunk) {
            this.finalTranscriptAccumulated += finalChunk;
          }
          this.currentTranscript = (this.finalTranscriptAccumulated + interimTranscript).trim();
          if (this.onResult) this.onResult(this.currentTranscript);
        };

        this.recognition.onerror = (event) => {
          console.warn('Web Speech status:', event.error);
          if (event.error !== 'no-speech') {
            if (this.onError) this.onError(event.error);
          }
        };

        this.recognition.onend = async () => {
          if (this.isRecording) {
            this.isRecording = false;
            await this.finalizeRecording();
          }
        };
      } catch (e) {
        console.warn("SpeechRecognition init error:", e);
      }
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
    this.finalTranscriptAccumulated = '';
    this.audioChunks = [];

    if (this.onStart) this.onStart();

    // 1. Démarre Web Speech API
    if (this.recognition) {
      try {
        this.recognition.start();
        return;
      } catch (err) {
        // Déjà démarré
      }
    }

    // 2. Fallback MediaRecorder si Web Speech absent
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.mediaRecorder = new MediaRecorder(this.stream);
        this.mediaRecorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) this.audioChunks.push(e.data);
        };
        this.mediaRecorder.start();
      }
    } catch (err) {
      console.warn("Microphone access:", err);
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
    let text = (this.finalTranscriptAccumulated + ' ' + this.currentTranscript).trim();

    // Si Web Speech n'a rien renvoyé mais qu'on a des chunks MediaRecorder
    if (!text && this.audioChunks.length > 0) {
      try {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        if (audioBlob.size > 2000) {
          text = await ApiService.transcribeAudioBlob(audioBlob);
        }
      } catch (e) {
        console.warn("STT backend fallback error:", e);
      }
    }

    if (this.onEnd) {
      this.onEnd(text);
    }
  }
}
