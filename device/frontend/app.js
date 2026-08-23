/**
 * AlternIA Device Interface - Contrôleur Kiosk Épuré (Voice-First & Avatar 2.5D).
 */

import { ApiService } from './js/services/api.js';
import { AudioService } from './js/services/audio.js';
import { SpeechService } from './js/services/speech.js';
import { VortexUI } from './js/ui/vortex.js';
import { KaTeXRenderer } from './js/ui/katex-renderer.js';

export class AlternIAApp {
  constructor() {
    this.currentClass = '10eme';
    this.currentSubject = null; // Auto-détection de matière par le RAG
    this.sessionId = 'kiosk_session_' + Date.now();

    this.initDOM();
    this.initModules();
    this.bindEvents();
    this.loadActiveAvatar();
  }

  initDOM() {
    this.questionInput = document.getElementById('question-input');
    this.sendBtn = document.getElementById('btn-send');
    this.micBtn = document.getElementById('btn-mic-main');
    this.btnReset = document.getElementById('btn-reset-session');
    this.btnMute = document.getElementById('btn-toggle-mute');

    this.speechContentArea = document.getElementById('speech-content-area');
    this.studentQueryPreview = document.getElementById('student-query-preview');
    this.studentQueryText = document.getElementById('student-query-text');
    this.ragSourceBadge = document.getElementById('rag-source-badge');
    this.classSublabel = document.getElementById('alta-class-sublabel');

    this.classTabs = document.querySelectorAll('.class-tab-btn');
  }

  initModules() {
    // 1. UI Vortex & Avatar 2.5D
    this.vortex = new VortexUI({
      canvasId: 'alta-avatar-canvas',
      statusTextId: 'status-text',
      statusDotId: 'status-dot',
    });

    // 2. Moteur KaTeX
    this.katex = new KaTeXRenderer();

    // 3. Moteur Audio & Synthèse Vocale avec analyseur FFT pour Lip-Sync
    this.audio = new AudioService({
      onSpeakingChange: (isSpeaking) => {
        if (isSpeaking) {
          this.vortex.setState('SPEAKING', 'Enseignant explique...');
        } else if (this.vortex.currentState === 'SPEAKING') {
          this.vortex.setState('IDLE', 'Prêt à répondre');
        }
      },
      onAnalyserReady: (analyser) => {
        this.vortex.setAudioAnalyser(analyser);
      }
    });

    // 4. Moteur Speech-To-Text (Microphone) avec mode interactif clic-pour-parler / clic-pour-finir
    this.speech = new SpeechService({
      onStart: () => {
        if (this.micBtn) this.micBtn.classList.add('is-recording');
        this.vortex.setState('LISTENING', 'Écoute en cours... (Touchez pour envoyer)');
        this.audio.playBeep(440, 0.1);
        if (this.studentQueryPreview) {
          this.studentQueryPreview.classList.remove('hidden');
          if (this.studentQueryText) this.studentQueryText.textContent = "Je vous écoute... Parlez au micro";
        }
      },
      onResult: (transcript) => {
        if (this.studentQueryText) this.studentQueryText.textContent = transcript;
        if (this.questionInput) this.questionInput.value = transcript;
      },
      onEnd: (finalText) => {
        if (this.micBtn) this.micBtn.classList.remove('is-recording');
        const text = finalText || (this.questionInput ? this.questionInput.value.trim() : '');
        if (text) {
          if (this.studentQueryText) this.studentQueryText.textContent = text;
          this.submitQuestion(text);
        } else {
          this.vortex.setState('IDLE', 'Prêt à répondre');
        }
      },
      onError: () => {
        if (this.micBtn) this.micBtn.classList.remove('is-recording');
        this.vortex.setState('IDLE', 'Prêt à répondre');
      }
    });
  }

  bindEvents() {
    // Boutons de sélection de classe
    this.classTabs.forEach(btn => {
      btn.onclick = () => {
        const cls = btn.getAttribute('data-class');
        this.selectClass(cls);
      };
    });

    // Bouton Microphone : Touchez pour parler, retouchez pour envoyer la question
    if (this.micBtn) {
      this.micBtn.onclick = () => this.speech.toggle();
    }

    // Envoi par bouton ou Entrée
    if (this.sendBtn) {
      this.sendBtn.onclick = () => {
        const text = this.questionInput ? this.questionInput.value.trim() : '';
        if (text) this.submitQuestion(text);
      };
    }
    if (this.questionInput) {
      this.questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          const text = this.questionInput.value.trim();
          if (text) this.submitQuestion(text);
        }
      });
    }

    // Réinitialiser la session
    if (this.btnReset) {
      this.btnReset.onclick = async () => {
        this.sessionId = 'kiosk_session_' + Date.now();
        this.audio.stop();
        if (this.studentQueryPreview) this.studentQueryPreview.classList.add('hidden');
        if (this.speechContentArea) {
          this.speechContentArea.innerHTML = `
            <div class="speech-welcome-text">
              <p class="text-base text-slate-200 leading-relaxed">
                Session réinitialisée. Posez une nouvelle question au micro ou par écrit.
              </p>
            </div>
          `;
        }
        this.vortex.setState('IDLE', 'Prêt à répondre');
      };
    }

    // Mute / Unmute
    if (this.btnMute) {
      this.btnMute.onclick = () => {
        const isMuted = this.audio.toggleMute();
        this.btnMute.innerHTML = isMuted
          ? '<svg class="w-5 h-5 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="1" y1="1" x2="23" y2="23"></line><path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"></path><path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2a7 7 0 0 1-.11 1.23"></path></svg>'
          : '<svg class="w-5 h-5 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>';
      };
    }
  }

  selectClass(classId) {
    this.currentClass = classId;
    this.classTabs.forEach(btn => {
      if (btn.getAttribute('data-class') === classId) {
        btn.classList.add('class-tab--active');
      } else {
        btn.classList.remove('class-tab--active');
      }
    });

    const labels = {
      '10eme': '10ème Année (Tronc Commun)',
      '11eme': '11ème Année (Sciences & Lettres)',
      '12eme': 'Terminale (Baccalauréat Mali)'
    };
    if (this.classSublabel) {
      this.classSublabel.textContent = labels[classId] || 'Programme Lycée Mali';
    }
  }

  async loadActiveAvatar() {
    try {
      const res = await fetch('/api/avatars/actif');
      if (res.ok) {
        const data = await res.json();
        if (data && data.photoUrl) {
          this.vortex.setAvatarImage(data.photoUrl, data.nom);
        }
      }
    } catch (e) {
      console.warn("Avatar actif chargé :", e);
    }
  }

  async submitQuestion(questionText) {
    const question = questionText || (this.questionInput ? this.questionInput.value.trim() : '');
    if (!question) return;

    if (this.questionInput) this.questionInput.value = '';
    this.audio.stop();

    if (this.studentQueryPreview) {
      this.studentQueryPreview.classList.remove('hidden');
      if (this.studentQueryText) this.studentQueryText.textContent = question;
    }

    this.vortex.setState('THINKING', 'Consultation du RAG malien...');

    // Préparation de la zone d'explication
    if (this.speechContentArea) {
      this.speechContentArea.innerHTML = `
        <div class="flex items-center gap-3 text-cyan-300 py-4">
          <div class="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
          <span class="text-sm font-medium">Recherche dans les manuels officiels et génération...</span>
        </div>
      `;
    }

    let fullText = "";
    let sentenceBuffer = "";
    let firstSent = false;
    const clauseDelim = /([,;:\.!?…]\s+|\n+)/;
    const sentDelim = /([\.!?…]\s+|\n+)/;

    const streamSuccess = await ApiService.streamChat({
      question,
      studentClass: this.currentClass,
      subject: this.currentSubject, // null => auto-détection multi-matières (SVT, Maths, Physique, etc.)
      sessionId: this.sessionId,
      onChunk: (chunk) => {
        fullText += chunk;
        if (this.speechContentArea) {
          this.speechContentArea.innerHTML = `<div class="formatted-text">${this.formatMarkdownText(fullText)}</div>`;
          this.katex.renderFormulasInElement(this.speechContentArea);
        }

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
        if (data.sources && data.sources.length > 0 && this.ragSourceBadge) {
          this.ragSourceBadge.textContent = data.sources[0].document;
        }
        if (data.full_text) fullText = data.full_text;
        if (this.speechContentArea) {
          this.speechContentArea.innerHTML = `<div class="formatted-text">${this.formatMarkdownText(fullText)}</div>`;
          this.katex.renderFormulasInElement(this.speechContentArea);
        }
      }
    });

    if (streamSuccess) {
      if (sentenceBuffer.trim().length > 2) {
        this.audio.enqueueSentence(sentenceBuffer.trim());
      }
    } else {
      if (this.speechContentArea) {
        this.speechContentArea.innerHTML = `
          <p class="text-slate-200">
            Pour la classe de <strong>${this.currentClass}</strong> : voici les éléments clés concernant votre question.
          </p>
        `;
      }
    }
  }

  formatMarkdownText(text) {
    if (!text) return '';
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
  }
}

// Initialisation au chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
  window.alternia = new AlternIAApp();
});
