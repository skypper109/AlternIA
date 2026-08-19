/**
 * Alternia Device Interface - Contrôleur Principal (Architecture Modulaire ES6).
 *
 * Modules :
 * - js/config/curriculum.js   : Données officielles des classes & matières (Mali)
 * - js/services/api.js        : Client API FastAPI & Streaming SSE
 * - js/services/audio.js      : Moteur audio, streaming TTS & bruitages SFX
 * - js/services/speech.js     : Reconnaissance vocale (Speech-to-Text)
 * - js/ui/vortex.js           : Avatar Tri-Vortex réactif 60 FPS
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
    // 1. UI Vortex 60 FPS
    this.vortex = new VortexUI();

    // 2. Moteur KaTeX
    this.katex = new KaTeXRenderer();

    // 3. Moteur Audio & Synthèse Vocale
    this.audio = new AudioService({
      onSpeakingChange: (isSpeaking) => {
        if (isSpeaking) {
          this.vortex.setState('SPEAKING', 'ALTA répond vocalement...');
        } else if (this.vortex.currentState === 'SPEAKING') {
          this.vortex.setState('IDLE');
        }
      }
    });

    // 4. Moteur de Chat & Bulles
    this.chat = new ChatRenderer({
      katexRenderer: this.katex
    });

    // 5. Moteur Speech-To-Text (Microphone)
    this.speech = new SpeechService({
      onStart: () => {
        if (this.micBtn) this.micBtn.classList.add('is-recording');
        this.vortex.setState('LISTENING', 'Parle maintenant dans le micro...');
        this.audio.playBeep(440, 0.1);
      },
      onResult: (transcript) => {
        if (this.questionInput) this.questionInput.value = transcript;
      },
      onEnd: () => {
        if (this.micBtn) this.micBtn.classList.remove('is-recording');
        const text = this.questionInput ? this.questionInput.value.trim() : '';
        if (text) {
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
      onClassSelect: (classId) => this.selectClass(classId),
      onSubjectSelect: (subjectId) => this.selectSubject(subjectId),
      onTopicClick: (topic) => this.askQuestion(topic)
    });

    this.curriculum.render(this.currentClass, this.currentSubject);
  }

  bindEvents() {
    // Bouton d'envoi & Entrée
    if (this.sendBtn) this.sendBtn.onclick = () => this.submitQuestion();
    if (this.questionInput) {
      this.questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.submitQuestion();
        }
      });
    }

    // Bouton Microphone
    if (this.micBtn) this.micBtn.onclick = () => this.speech.toggle();

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
          ? '<svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"></path></svg>'
          : '<svg class="w-5 h-5 text-cyan-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"></path></svg>';
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

  selectClass(classId) {
    this.currentClass = classId;
    this.curriculum.render(this.currentClass, this.currentSubject);
    const clsObj = this.curriculum.getClassObj(classId);
    this.chat.addSystemNotification(`Classe changée en : ${clsObj.name}`);
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

        // Découpage et émission vocale TTS fluide
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
        this.ragStatusBadge.className = 'status-pill text-xs text-emerald-300 border-emerald-500/30';
      } else {
        this.ragStatusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-amber-400"></span> <span>Mode Embarqué Autonome</span>`;
        this.ragStatusBadge.className = 'status-pill text-xs text-amber-300 border-amber-500/30';
      }
    }
  }

  welcome() {
    this.chat.renderInitialWelcome((clsId) => {
      this.selectClass(clsId);
      const clsObj = this.curriculum.getClassObj(clsId);
      const subjObj = this.curriculum.getSubjectObj(clsId, this.currentSubject);
      this.chat.appendAIMessage({
        answer: `Parfait ! Tu es configuré en **${clsObj.name}** (${clsObj.badge}).\n\nChoisis ta matière et pose-moi ta première question par écrit ou au micro ! 🚀`,
        followup: `Quelles sont les formules clés en ${subjObj.name} ?`
      }, (f) => this.askQuestion(f));
    });
    this.audio.speakText("Bonjour ! Je suis ALTA, ton tuteur pédagogique. Choisis ta classe pour commencer !");
  }
}

// Initialisation au chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
  window.alternia = new AlternIAApp();
});
