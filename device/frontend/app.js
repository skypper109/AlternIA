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

    this.btnShowAvatar = document.getElementById('btn-show-avatar');
    this.btnCloseAvatar = document.getElementById('btn-close-avatar');
    this.avatarModal = document.getElementById('avatar-fullscreen-modal');
    this.avatarTranscription = document.getElementById('avatar-fullscreen-transcription');
    this.btnMicModal = document.getElementById('btn-mic-modal');
    this.modalAvatarTitle = document.getElementById('modal-avatar-title');
    this.modalAvatarSubtitle = document.getElementById('modal-avatar-subtitle');
    this.modalStatusText = document.getElementById('modal-status-text');
    this.modalStatusDot = document.getElementById('modal-status-dot');
  }

  initModules() {
    // 1. UI Vortex & Avatar 2.5D (Modal plein écran pour l'avatar actif du backoffice)
    this.vortex = new VortexUI({
      canvasId: 'alta-avatar-canvas',
      statusTextId: 'modal-status-text',
      statusDotId: 'modal-status-dot',
      isLogoMode: false
    });

    // 1b. UI Vortex & Avatar 2.5D (Logo Principal en page d'accueil)
    this.logoVortex = new VortexUI({
      canvasId: 'main-animated-logo-canvas',
      statusTextId: 'status-text',
      statusDotId: 'status-dot',
      defaultImageUrl: 'assets/logo-icon.jpeg',
      isLogoMode: true
    });

    // 2. Moteur KaTeX
    this.katex = new KaTeXRenderer();

    // 3. Moteur Audio & Synthèse Vocale avec analyseur FFT pour Lip-Sync
    this.audio = new AudioService({
      onSpeakingChange: (isSpeaking) => {
        if (isSpeaking) {
          this.vortex.setState('SPEAKING', 'Enseignant explique...');
          this.logoVortex.setState('SPEAKING', 'Enseignant explique...');
        } else if (this.vortex.currentState === 'SPEAKING') {
          this.vortex.setState('IDLE', 'Prêt à répondre');
          this.logoVortex.setState('IDLE', 'Prêt à répondre');
        }
      },
      onAnalyserReady: (analyser) => {
        this.vortex.setAudioAnalyser(analyser);
        this.logoVortex.setAudioAnalyser(analyser);
      }
    });

    // 4. Moteur Speech-To-Text (Microphone) avec mode interactif push-to-talk (Accueil + Modal Avatar)
    this.speech = new SpeechService({
      onStart: () => {
        if (this.micBtn) this.micBtn.classList.add('is-recording');
        if (this.btnMicModal) this.btnMicModal.classList.add('animate-ping', 'ring-4', 'ring-amber-300');
        this.vortex.setState('LISTENING', 'Écoute en cours...');
        this.logoVortex.setState('LISTENING', 'Écoute en cours...');
        this.audio.playBeep(440, 0.1);
        if (this.studentQueryPreview) {
          this.studentQueryPreview.classList.remove('hidden');
          if (this.studentQueryText) this.studentQueryText.textContent = "Je vous écoute... Parlez au micro";
        }
        if (this.avatarTranscription) {
          this.avatarTranscription.textContent = "Je vous écoute... Posez votre question au professeur.";
        }
      },
      onResult: (transcript) => {
        if (this.studentQueryText) this.studentQueryText.textContent = transcript;
        if (this.questionInput) this.questionInput.value = transcript;
        if (this.avatarTranscription) this.avatarTranscription.textContent = `"${transcript}"`;
      },
      onEnd: (finalText) => {
        if (this.micBtn) this.micBtn.classList.remove('is-recording');
        if (this.btnMicModal) this.btnMicModal.classList.remove('animate-ping', 'ring-4', 'ring-amber-300');
        const text = finalText || (this.questionInput ? this.questionInput.value.trim() : '');
        if (text) {
          if (this.studentQueryText) this.studentQueryText.textContent = text;
          this.submitQuestion(text);
        } else {
          this.vortex.setState('IDLE', 'Prêt à répondre');
          this.logoVortex.setState('IDLE', 'Prêt à répondre');
        }
      },
      onError: () => {
        if (this.micBtn) this.micBtn.classList.remove('is-recording');
        if (this.btnMicModal) this.btnMicModal.classList.remove('animate-ping', 'ring-4', 'ring-amber-300');
        this.vortex.setState('IDLE', 'Prêt à répondre');
        this.logoVortex.setState('IDLE', 'Prêt à répondre');
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

    // Boutons Microphone : Accueil + Modal Avatar (Push-To-Talk)
    if (this.micBtn) {
      this.micBtn.onclick = () => this.speech.toggle();
    }
    if (this.btnMicModal) {
      this.btnMicModal.onclick = () => this.speech.toggle();
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
              <p class="text-base text-slate-600 leading-relaxed">
                Session réinitialisée. Posez une nouvelle question au micro ou par écrit.
              </p>
            </div>
          `;
        }
        if (this.avatarTranscription) {
          this.avatarTranscription.textContent = "Session réinitialisée. Touchez le micro pour me parler !";
        }
        this.vortex.setState('IDLE', 'Prêt à répondre');
        this.logoVortex.setState('IDLE', 'Prêt à répondre');
      };
    }

    // Modal Avatar Plein Écran
    if (this.btnShowAvatar) {
      this.btnShowAvatar.onclick = () => {
        if (this.avatarModal) {
          this.avatarModal.classList.remove('hidden');
          if (this.audio && this.audio.audioCtx && this.audio.audioCtx.state === 'suspended') {
            this.audio.audioCtx.resume();
          }
        }
      };
    }
    if (this.btnCloseAvatar) {
      this.btnCloseAvatar.onclick = () => {
        if (this.avatarModal) this.avatarModal.classList.add('hidden');
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

    // Débloquer l'AudioContext lors du clic
    if (this.audio && this.audio.audioCtx && this.audio.audioCtx.state === 'suspended') {
      this.audio.audioCtx.resume();
    }

    const labels = {
      '10eme': '10ème Année (Tronc Commun)',
      '11eme': '11ème Année (Sciences & Lettres)',
      '12eme': 'Terminale (Baccalauréat Mali)'
    };
    if (this.classSublabel) {
      this.classSublabel.textContent = labels[classId] || 'Programme Lycée Mali';
    }

    const vocalLabels = {
      '10eme': 'dixième année',
      '11eme': 'onzième année',
      '12eme': 'classe de terminale'
    };
    if (vocalLabels[classId]) {
      this.audio.speakText(`Tu as sélectionné la ${vocalLabels[classId]}.`);
    }
  }

  async loadActiveAvatar() {
    try {
      const res = await fetch('/api/avatars/actif');
      if (res.ok) {
        const data = await res.json();
        if (data) {
          // Mise à jour des informations de l'avatar UNIQUEMENT dans le Modal Pédagogique
          if (this.modalAvatarTitle && data.nom) {
            this.modalAvatarTitle.textContent = data.nom;
          }
          if (this.modalAvatarSubtitle) {
            const subject = data.matiere || 'Tuteur Pédagogique';
            const style = data.stylePedagogique ? ` • Style ${data.stylePedagogique}` : '';
            this.modalAvatarSubtitle.textContent = `${subject}${style}`;
          }

          // L'image de l'avatar est chargée UNIQUEMENT dans le modal (this.vortex)
          // La page principale garde TOUJOURS le logo officiel AlternIA (this.logoVortex)
          if (data.photoUrl) {
            this.vortex.setAvatarImage(data.photoUrl, data.nom, data.landmarks);
          }
          if (data.visemePhotos && this.vortex.animator) {
            this.vortex.animator.setVisemePhotos(data.visemePhotos);
          }
        }
      }
    } catch (e) {
      console.warn("Avatar actif chargé :", e);
    }
    
    // Message de bienvenue
    setTimeout(() => {
      this.audio.speakText("Bonjour ! Je suis AlternIA, ton assistant pédagogique. Choisis ta classe et pose-moi tes questions.");
    }, 1000);
  }

  async submitQuestion(questionText) {
    const question = questionText || (this.questionInput ? this.questionInput.value.trim() : '');
    if (!question) return;

    if (this.questionInput) this.questionInput.value = '';
    this.audio.stop();
    
    // Débloquer l'AudioContext immédiatement sur l'interaction utilisateur pour éviter le blocage Autoplay (TTS)
    if (this.audio.audioCtx && this.audio.audioCtx.state === 'suspended') {
      this.audio.audioCtx.resume();
    }

    if (this.studentQueryPreview) {
      this.studentQueryPreview.classList.remove('hidden');
      if (this.studentQueryText) this.studentQueryText.textContent = question;
    }

    this.vortex.setState('THINKING', 'Consultation du RAG malien...');
    this.logoVortex.setState('THINKING', 'Consultation du RAG malien...');

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
        if (this.avatarTranscription) {
          this.avatarTranscription.innerHTML = this.formatMarkdownText(fullText);
          this.katex.renderFormulasInElement(this.avatarTranscription);
        }

        sentenceBuffer += chunk;

        // Découpage et émission vocale TTS fluide
        const match = sentDelim.exec(sentenceBuffer) || clauseDelim.exec(sentenceBuffer);
        if (match && sentenceBuffer.substring(0, match.index).trim().split(/\s+/).length >= 3) {
          const pos = match.index + match[0].length;
          const segment = sentenceBuffer.substring(0, pos).trim();
          sentenceBuffer = sentenceBuffer.substring(pos);
          if (segment.length > 2) {
            console.log("🔊 [TTS Stream Chunk]:", segment);
            this.audio.enqueueSentence(segment);
            firstSent = true;
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
        if (this.avatarTranscription) {
          this.avatarTranscription.innerHTML = this.formatMarkdownText(fullText);
          this.katex.renderFormulasInElement(this.avatarTranscription);
        }

        // Si le buffer contient encore du texte restant non émis
        if (sentenceBuffer.trim().length > 2) {
          console.log("🔊 [TTS Stream Restant]:", sentenceBuffer.trim());
          this.audio.enqueueSentence(sentenceBuffer.trim());
          firstSent = true;
        } else if (!firstSent && fullText.trim().length > 2) {
          console.log("🔊 [TTS Stream Full Fallback]:", fullText.trim());
          this.audio.enqueueSentence(fullText.trim());
          firstSent = true;
        }
      }
    });

    if (!streamSuccess) {
      if (this.speechContentArea) {
        this.speechContentArea.innerHTML = `<p class="text-red-400">Désolé, une erreur de connexion est survenue.</p>`;
      }
    }

    // Sécurité : si la file audio est vide (ou TTS désactivé/échoué), on force le retour à l'état IDLE
    setTimeout(() => {
      if (!this.audio.isPlayingQueue && this.vortex.currentState === 'THINKING') {
        this.vortex.setState('IDLE', 'Prêt à répondre');
        this.logoVortex.setState('IDLE', 'Prêt à répondre');
      }
    }, 500);
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
