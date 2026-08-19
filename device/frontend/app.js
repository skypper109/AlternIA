/**
 * Alternia Device Interface - Contrôleur Principal (Architecture Modulaire ES6).
 *
 * Modules :
 * - js/config/curriculum.js   : Données officielles des classes & matières (Mali)
 * - js/services/api.js        : Client API FastAPI, STT & Streaming SSE
 * - js/services/audio.js      : Moteur audio, streaming TTS & bruitages SFX
 * - js/services/speech.js     : Reconnaissance vocale hybride (Web Speech + Faster-Whisper)
 * - js/ui/vortex.js           : Avatar Alta réactif (Halo chromatique & Waveform)
 * - js/ui/katex-renderer.js   : Rendu KaTeX des formules & zoom modal
 * - js/ui/chat-renderer.js    : Rendu des messages et bulles interactives
 * - js/ui/curriculum-ui.js    : Sélecteur de classes, matières et notions
 */

import { CURRICULUM_DATA, KNOWLEDGE_FALLBACK } from './js/config/curriculum.js';
import { ApiService } from './js/services/api.js';
import { AudioService } from './js/services/audio.js';
import { SpeechService } from './js/services/speech.js';
import { VortexUI } from './js/ui/vortex.js';
import { KaTeXRenderer } from './js/ui/katex-renderer.js';
import { ChatRenderer } from './js/ui/chat-renderer.js';
import { CurriculumUI } from './js/ui/curriculum-ui.js';

export class AlternIAApp {
  constructor() {
    this.currentClass = '10eme';
    this.currentSubject = 'mathematiques';
    this.sessionId = 'kiosk_session_' + Date.now();

    this.initDOM();
    this.initModules();
    this.bindEvents();
    this.checkHealth();
    this.welcome();
  }

  initDOM() {
    this.questionInput = document.getElementById('question-input');
    this.sendBtn = document.getElementById('btn-send');
    this.micBtn = document.getElementById('btn-mic-main');
    this.btnReset = document.getElementById('btn-reset-session');
    this.btnMute = document.getElementById('btn-toggle-mute');
    this.btnFullscreen = document.getElementById('btn-fullscreen');
    this.ragStatusBadge = document.getElementById('rag-status-badge');
    this.btnCloseModal = document.getElementById('btn-close-formula-modal');
  }

  initModules() {
    // 1. Contrôleur Avatar Alta & Waveform
    this.vortex = new VortexUI();

    // 2. Moteur KaTeX
    this.katex = new KaTeXRenderer();

    // 3. Moteur Audio & Synthèse Vocale
    this.audio = new AudioService({
      onSpeakingChange: (isSpeaking) => {
        if (isSpeaking) {
          this.vortex.setState('SPEAKING', 'ALTA explique...');
        } else if (this.vortex.currentState === 'SPEAKING') {
          this.vortex.setState('IDLE');
        }
      }
    });

    // 4. Moteur de Chat & Bulles
    this.chat = new ChatRenderer({
      katexRenderer: this.katex
    });

    // 5. Moteur Speech-To-Text (Microphone hybride Web Speech + Faster-Whisper)
    this.speech = new SpeechService({
      onStart: () => {
        if (this.micBtn) this.micBtn.classList.add('is-recording');
        this.vortex.setState('LISTENING', 'Écoute au micro... Parle maintenant !');
        this.audio.playBeep(440, 0.1);
      },
      onResult: (transcript) => {
        if (this.questionInput) this.questionInput.value = transcript;
      },
      onEnd: (finalTranscript) => {
        if (this.micBtn) this.micBtn.classList.remove('is-recording');
        const text = (finalTranscript || (this.questionInput ? this.questionInput.value : '')).trim();
        if (text) {
          if (this.questionInput) this.questionInput.value = text;
          this.submitQuestion();
        } else {
          this.vortex.setState('IDLE');
        }
      },
      onError: () => {
        if (this.micBtn) this.micBtn.classList.remove('is-recording');
        this.vortex.setState('IDLE');
      }
    });

    // 6. UI Curriculaire (Classes & Matières)
    this.curriculum = new CurriculumUI({
      onClassSelect: (classId) => this.selectClass(classId, true),
      onSubjectSelect: (subjectId) => this.selectSubject(subjectId),
      onTopicClick: (topic) => this.askQuestion(topic)
    });

    this.curriculum.render(this.currentClass, this.currentSubject);
  }

  bindEvents() {
    // Bouton d'envoi & Touche Entrée
    if (this.sendBtn) this.sendBtn.onclick = () => this.submitQuestion();
    if (this.questionInput) {
      this.questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.submitQuestion();
        }
      });
    }

    // Bouton Microphone Principal sous l'avatar (Bouton 4)
    if (this.micBtn) {
      this.micBtn.onclick = () => this.speech.toggle();
    }

    // Raccourcis clavier physiques (Touches 1, 2, 3 pour les classes et 4/Espace pour le micro)
    window.addEventListener('keydown', (e) => {
      // Si l'utilisateur n'est pas en train de taper dans l'input
      if (document.activeElement !== this.questionInput) {
        if (e.key === '1') {
          this.selectClass('10eme', true);
        } else if (e.key === '2') {
          this.selectClass('11eme', true);
        } else if (e.key === '3') {
          this.selectClass('12eme', true);
        } else if (e.key === '4' || e.key === ' ') {
          e.preventDefault();
          this.speech.toggle();
        }
      }
    });

    // Réinitialiser la session
    if (this.btnReset) {
      this.btnReset.onclick = async () => {
        const oldId = this.sessionId;
        this.sessionId = 'kiosk_session_' + Date.now();
        this.chat.clear();
        this.audio.stop();
        await ApiService.resetSession(oldId);
        this.vortex.setState('IDLE');
        this.welcome();
        this.chat.addSystemNotification("Session réinitialisée. Nouvelle conversation active.");
      };
    }

    // Mute / Unmute
    if (this.btnMute) {
      this.btnMute.onclick = () => {
        const isMuted = this.audio.toggleMute();
        this.btnMute.innerHTML = isMuted
          ? '<svg class="w-4 h-4 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="1" y1="1" x2="23" y2="23"></line><path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"></path><path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>'
          : '<svg class="w-4 h-4 text-cyan-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>';
      };
    }

    // Plein écran
    if (this.btnFullscreen) {
      this.btnFullscreen.onclick = () => {
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(() => {});
        } else {
          document.exitFullscreen().catch(() => {});
        }
      };
    }

    // Fermeture Modal KaTeX
    if (this.btnCloseModal) {
      this.btnCloseModal.onclick = () => this.katex.closeFormulaModal();
    }
  }

  selectClass(classId, announceVoice = false) {
    this.currentClass = classId;
    this.curriculum.render(this.currentClass, this.currentSubject);
    const clsObj = this.curriculum.getClassObj(classId);
    this.chat.addSystemNotification(`Programme configuré sur : ${clsObj.name} (${clsObj.badge})`);

    if (announceVoice) {
      const voicePrompts = {
        "10eme": "Mode 10ème Année Tronc Commun activé. Tu peux poser ta question au micro ou par écrit.",
        "11eme": "Mode 11ème Année activé. Pose ta question au micro ou par écrit.",
        "12eme": "Mode Terminale 12ème activé. Pose ta question au micro ou par écrit."
      };
      const promptText = voicePrompts[classId] || `Mode ${clsObj.name} activé.`;
      this.audio.speakText(promptText);
    }
  }

  selectSubject(subjectId) {
    this.currentSubject = subjectId;
    this.curriculum.render(this.currentClass, this.currentSubject);
  }

  askQuestion(text) {
    if (!text || !text.trim()) return;
    if (this.questionInput) this.questionInput.value = text;
    this.submitQuestion();
  }

  async submitQuestion() {
    const question = this.questionInput ? this.questionInput.value.trim() : '';
    if (!question) return;

    this.questionInput.value = '';
    this.audio.stop();
    const classObj = this.curriculum.getClassObj(this.currentClass);
    this.chat.appendUserMessage(question, classObj.name);
    this.vortex.setState('THINKING', 'Consultation du programme officiel malien...');

    const streamingMessage = this.chat.createStreamingAIMessage((followup) => this.askQuestion(followup));

    let fullText = "";
    let sentenceBuffer = "";
    let firstSent = false;
    const clauseDelim = /([,;:\.!?…]\s+|\n+)/;
    const sentDelim = /([\.!?…]\s+|\n+)/;
    let streamSuccess = false;
    let sources = [];

    streamSuccess = await ApiService.streamChat({
      question,
      studentClass: this.currentClass,
      subject: this.currentSubject,
      sessionId: this.sessionId,
      onChunk: (chunk) => {
        fullText += chunk;
        streamingMessage.updateText(fullText);
        sentenceBuffer += chunk;

        // Découpage et émission vocale TTS fluide au fil de l'eau
        if (!firstSent) {
          const match = clauseDelim.exec(sentenceBuffer);
          if (match || sentenceBuffer.trim().split(/\s+/).length >= 6) {
            const pos = match ? match.index + match[0].length : sentenceBuffer.length;
            const segment = sentenceBuffer.substring(0, pos).trim();
            sentenceBuffer = sentenceBuffer.substring(pos);
            if (segment.length > 2) {
              this.audio.enqueueSentence(segment);
              firstSent = true;
            }
          }
        } else {
          while (true) {
            let match = sentDelim.exec(sentenceBuffer);
            if (!match && sentenceBuffer.trim().split(/\s+/).length >= 10) {
              match = clauseDelim.exec(sentenceBuffer);
            }
            if (!match) break;
            const pos = match.index + match[0].length;
            const segment = sentenceBuffer.substring(0, pos).trim();
            sentenceBuffer = sentenceBuffer.substring(pos);
            if (segment.length > 2) {
              this.audio.enqueueSentence(segment);
            }
          }
        }
      },
      onDone: (data) => {
        sources = data.sources || [];
        if (data.full_text) fullText = data.full_text;
      }
    });

    if (streamSuccess) {
      if (sentenceBuffer.trim().length > 2) {
        this.audio.enqueueSentence(sentenceBuffer.trim());
      }
      streamingMessage.finalize({
        answer: fullText,
        sources,
        source: sources.length > 0 ? sources[0].document : null,
        followup: "Veux-tu un exemple d'application ou un exercice type Bac ?"
      });
    } else {
      if (streamingMessage && streamingMessage.element) {
        streamingMessage.element.remove();
      }
      this.handleFallback(question);
    }
  }

  handleFallback(question) {
    const qLower = question.toLowerCase();
    const matchKey = Object.keys(KNOWLEDGE_FALLBACK).find(k => qLower.includes(k));

    if (matchKey) {
      const item = KNOWLEDGE_FALLBACK[matchKey];
      this.chat.appendAIMessage({
        answer: item.text,
        formula: item.formula,
        formulaSpeech: item.formulaSpeech,
        variables: item.variables,
        source: item.source,
        followup: item.followup
      }, (f) => this.askQuestion(f));
      this.audio.speakText(item.text, item.formulaSpeech);
    } else {
      const clsObj = this.curriculum.getClassObj(this.currentClass);
      const subjObj = this.curriculum.getSubjectObj(this.currentClass, this.currentSubject);
      const answer = `Pour la classe de **${clsObj.name}** en **${subjObj.name}** :\n\nVoici les notions clés concernant : *"${question}"*.\n\nAssure-toi d'appliquer les formules et démarches officielles du lycée malien.`;
      this.chat.appendAIMessage({
        answer,
        source: `Manuel ${subjObj.name} ${clsObj.name}`,
        followup: "Veux-tu que nous résolvions un exemple concret étape par étape ?"
      }, (f) => this.askQuestion(f));
      this.audio.speakText(answer);
    }
  }

  async checkHealth() {
    const health = await ApiService.checkHealth();
    if (this.ragStatusBadge) {
      if (health) {
        this.ragStatusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> <span>RAG Local Connecté (${health.rag_chunks_count || 'OK'})</span>`;
        this.ragStatusBadge.className = 'glass-status-badge text-xs text-emerald-300 border-emerald-500/30 font-mono';
      } else {
        this.ragStatusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-amber-400"></span> <span>Mode Embarqué Autonome</span>`;
        this.ragStatusBadge.className = 'glass-status-badge text-xs text-amber-300 border-amber-500/30 font-mono';
      }
    }
  }

  welcome() {
    this.chat.renderInitialWelcome((clsId) => {
      this.selectClass(clsId, true);
      const clsObj = this.curriculum.getClassObj(clsId);
      const subjObj = this.curriculum.getSubjectObj(clsId, this.currentSubject);
      this.chat.appendAIMessage({
        answer: `Parfait ! Tu es configuré en **${clsObj.name}** (${clsObj.badge}).\n\nChoisis ta matière et pose-moi ta première question au micro ou par écrit !`,
        followup: `Quelles sont les notions clés en ${subjObj.name} ?`
      }, (f) => this.askQuestion(f));
    });
    this.audio.speakText("Bonjour ! Je suis ALTA, ton tuteur pédagogique. Choisis ta classe pour commencer !");
  }
}

// Initialisation au chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
  window.alternia = new AlternIAApp();
});
