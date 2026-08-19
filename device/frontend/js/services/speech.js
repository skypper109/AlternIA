/**
 * Service de reconnaissance vocale (Speech-to-Text).
 */

export class SpeechService {
  constructor({ onStart, onResult, onEnd, onError, onSimulationStart }) {
    this.onStart = onStart;
    this.onResult = onResult;
    this.onEnd = onEnd;
    this.onError = onError;
    this.onSimulationStart = onSimulationStart;

    this.recognition = null;
    this.isRecording = false;

    this.initRecognition();
  }

  initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.lang = 'fr-FR';
      this.recognition.continuous = false;
      this.recognition.interimResults = true;

      this.recognition.onstart = () => {
        this.isRecording = true;
        if (this.onStart) this.onStart();
      };

      this.recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
        }
        if (this.onResult) this.onResult(transcript);
      };

      this.recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        this.stop();
        if (this.onError) this.onError(event.error);
      };

      this.recognition.onend = () => {
        this.isRecording = false;
        if (this.onEnd) this.onEnd();
      };
    } else {
      console.warn("Reconnaissance vocale Web Speech API non supportée sur ce navigateur.");
    }
  }

  toggle() {
    if (!this.recognition) {
      this.simulateVoiceInput();
      return;
    }

    if (this.isRecording) {
      this.recognition.stop();
      this.stop();
    } else {
      try {
        this.recognition.start();
      } catch (err) {
        console.error(err);
        this.simulateVoiceInput();
      }
    }
  }

  stop() {
    this.isRecording = false;
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }
  }

  simulateVoiceInput() {
    if (this.onSimulationStart) this.onSimulationStart();
    this.isRecording = true;
    if (this.onStart) this.onStart();

    setTimeout(() => {
      const sampleQueries = [
        "Donne-moi la formule de Moivre pour les nombres complexes",
        "Quelle est la deuxième loi de Newton en physique ?",
        "Comment calcule-t-on le pH d'une solution d'acide chlorhydrique ?",
        "Explique-moi la formule de l'énergie cinétique",
        "C'est quoi la photosynthèse ?"
      ];
      const query = sampleQueries[Math.floor(Math.random() * sampleQueries.length)];
      if (this.onResult) this.onResult(query);
      this.isRecording = false;
      if (this.onEnd) this.onEnd(query);
    }, 1800);
  }
}
