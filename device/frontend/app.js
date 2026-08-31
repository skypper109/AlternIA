/**
 * AlternIA Device Interface - Contrôleur Kiosk Épuré (Voice-First & Avatar Photoréaliste / 2.5D).
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
    this.activeAvatar = null;

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
    this.btnShowAvatar = document.getElementById('btn-show-avatar');

    this.speechContentArea = document.getElementById('speech-content-area');
    this.studentQueryPreview = document.getElementById('student-query-preview');
    this.studentQueryText = document.getElementById('student-query-text');
    this.ragSourceBadge = document.getElementById('rag-source-badge');
    this.classSublabel = document.getElementById('alta-class-sublabel');
    this.classTabs = document.querySelectorAll('.class-tab-btn');
    this.vortexHub = document.getElementById('alta-vortex-hub');
    this.avatarNameText = document.getElementById('alta-avatar-name');
    this.avatarNameBox = document.getElementById('alta-avatar-name-box');
    this.avatarVideo = document.getElementById('alta-avatar-video');
    this.avatarCanvas = document.getElementById('main-animated-logo-canvas');
    this.teacherHeaderLabel = document.getElementById('teacher-header-label');

    // Modal Avatar Plein Écran
    this.avatarModal = document.getElementById('avatar-fullscreen-modal');
    this.modalAvatarTitle = document.getElementById('modal-avatar-title');
    this.modalAvatarSubtitle = document.getElementById('modal-avatar-subtitle');
    this.modalAvatarVideo = document.getElementById('modal-avatar-video');
    this.modalAvatarCanvas = document.getElementById('modal-avatar-canvas');
    this.modalStatusDot = document.getElementById('modal-status-dot');
    this.modalStatusText = document.getElementById('modal-status-text');
    this.avatarTranscription = document.getElementById('avatar-fullscreen-transcription');
    this.btnCloseAvatar = document.getElementById('btn-close-avatar');
    this.btnMicModal = document.getElementById('btn-mic-modal');
  }

  initModules() {
    // 1. UI Vortex avec le Logo / Avatar Photoréaliste (Halo chromatique & FFT audio)
    this.vortex = new VortexUI({
      canvasId: 'main-animated-logo-canvas',
      statusTextId: 'status-text',
      statusDotId: 'status-dot',
      defaultImageUrl: 'assets/logo-icon.jpeg',
      isLogoMode: true
    });

    // Modal Vortex si présent
    if (this.modalAvatarCanvas) {
      this.modalVortex = new VortexUI({
        canvasId: 'modal-avatar-canvas',
        statusTextId: 'modal-status-text',
        statusDotId: 'modal-status-dot',
        defaultImageUrl: 'assets/logo-icon.jpeg',
        isLogoMode: false
      });
    } else {
      this.modalVortex = null;
    }

    // 2. Moteur KaTeX
    this.katex = new KaTeXRenderer();

    // 3. Moteur Audio & Synthèse Vocale avec analyseur FFT
    this.audio = new AudioService({
      onSpeakingChange: (isSpeaking) => {
        if (isSpeaking) {
          this.vortex.setState('SPEAKING', 'Enseignant explique...');
          if (this.modalVortex) this.modalVortex.setState('SPEAKING', 'Enseignant explique...');
        } else if (this.vortex.currentState === 'SPEAKING') {
          this.vortex.setState('IDLE', 'Prêt à répondre');
          if (this.modalVortex) this.modalVortex.setState('IDLE', 'Prêt à répondre');
        }
      },
      onAnalyserReady: (analyser) => {
        this.vortex.setAudioAnalyser(analyser);
        if (this.modalVortex) this.modalVortex.setAudioAnalyser(analyser);
      }
    });

    // 4. Moteur Speech-To-Text (Microphone Push-To-Talk)
    this.speech = new SpeechService({
      onStart: () => {
        if (this.micBtn) this.micBtn.classList.add('is-recording');
        if (this.btnMicModal) this.btnMicModal.classList.add('animate-pulse', 'ring-4', 'ring-amber-300');
        this.vortex.setState('LISTENING', 'Écoute en cours...');
        if (this.modalVortex) this.modalVortex.setState('LISTENING', 'Écoute en cours...');
        this.audio.stop();
      },
      onTranscript: (transcript) => {
        if (this.questionInput) {
          this.questionInput.value = transcript;
        }
        if (this.avatarTranscription) {
          this.avatarTranscription.textContent = transcript;
        }
      },
      onEnd: (finalTranscript) => {
        if (this.micBtn) this.micBtn.classList.remove('is-recording');
        if (this.btnMicModal) this.btnMicModal.classList.remove('animate-pulse', 'ring-4', 'ring-amber-300');
        if (finalTranscript && finalTranscript.trim().length > 1) {
          this.submitQuestion(finalTranscript.trim());
        } else {
          this.vortex.setState('IDLE', 'Prêt à répondre');
          if (this.modalVortex) this.modalVortex.setState('IDLE', 'Prêt à répondre');
        }
      },
      onError: (err) => {
        if (this.micBtn) this.micBtn.classList.remove('is-recording');
        if (this.btnMicModal) this.btnMicModal.classList.remove('animate-pulse', 'ring-4', 'ring-amber-300');
        this.vortex.setState('IDLE', 'Prêt à répondre');
        if (this.modalVortex) this.modalVortex.setState('IDLE', 'Prêt à répondre');
        console.warn("Erreur reconnaissance vocale :", err);
      }
    });
  }

  async loadActiveAvatar() {
    try {
      let resp = await fetch('/api/avatars/actif');
      if (!resp.ok) {
        resp = await fetch('/api/avatars');
      }
      if (resp.ok) {
        const raw = await resp.json();
        const data = Array.isArray(raw) ? (raw.find(a => a.parDefaut || a.actif) || raw[0]) : raw;
        if (data) {
          this.activeAvatar = data;
          console.log("🎬 [Avatar Actif Chargé]:", data.nom, data.matiere, data.photoUrl);

          if (this.avatarNameText && data.nom) {
            this.avatarNameText.textContent = data.nom;
          }
          if (this.classSublabel && data.matiere) {
            const style = data.stylePedagogique ? ` • ${data.stylePedagogique}` : '';
            this.classSublabel.textContent = `${data.matiere}${style}`;
          }
          if (this.teacherHeaderLabel && data.nom) {
            this.teacherHeaderLabel.textContent = `Explication de ${data.nom}`;
          }

          // La photo de l'avatar n'est appliquée qu'au modal plein écran (comme demandé)
          // Le vortex principal garde l'icône AlternIA par défaut.

          // Mise à jour du modal plein écran
          if (this.modalAvatarTitle && data.nom) {
            this.modalAvatarTitle.textContent = data.nom;
          }
          if (this.modalAvatarSubtitle) {
            const subject = data.matiere || 'Tuteur Pédagogique';
            const style = data.stylePedagogique ? ` • Style ${data.stylePedagogique}` : '';
            this.modalAvatarSubtitle.textContent = `${subject}${style}`;
          }
          if (data.photoUrl && this.modalVortex) {
            this.modalVortex.setAvatarImage(data.photoUrl, data.nom, data.landmarks);
            if (data.visemePhotos && this.modalVortex.animator) {
              this.modalVortex.animator.setVisemePhotos(data.visemePhotos);
            }
          }

          // Si une vidéo MP4 existe
          if (data.videoUrl) {
            if (this.avatarVideo) {
              this.avatarVideo.src = data.videoUrl;
              this.avatarVideo.load();
            }
            if (this.modalAvatarVideo) {
              this.modalAvatarVideo.src = data.videoUrl;
              this.modalAvatarVideo.load();
            }
          }
        }
      }
    } catch (e) {
      console.warn("Note chargement avatar :", e);
    }
  }

  playAvatarPresentation() {
    if (this.audio && this.audio.audioCtx && this.audio.audioCtx.state === 'suspended') {
      this.audio.audioCtx.resume();
    }

    const nom = this.activeAvatar?.nom || "Assistant AlternIA";
    const matiere = this.activeAvatar?.matiere || "toutes les matières du lycée";
    const presentationText = this.activeAvatar?.phrase || `Bonjour ! Je suis ${nom}. Je suis à ta disposition pour t'expliquer toutes les notions de ${matiere}. Pose-moi toutes tes questions !`;

    if (this.speechContentArea) {
      this.speechContentArea.innerHTML = `
        <div class="speech-welcome-text">
          <h3 class="text-xl font-bold text-slate-800 mb-2">Présentation de ${nom}</h3>
          <p class="text-base text-slate-600 leading-relaxed">${presentationText}</p>
        </div>
      `;
    }

    if (this.avatarTranscription) {
      this.avatarTranscription.textContent = presentationText;
    }

    if (this.activeAvatar?.videoUrl && this.avatarVideo) {
      this.avatarVideo.classList.remove('hidden');
      if (this.avatarCanvas) this.avatarCanvas.classList.add('hidden');
      this.avatarVideo.currentTime = 0;
      this.avatarVideo.muted = false;
      this.vortex.setState('SPEAKING', 'Présentation en cours...');

      this.avatarVideo.play().catch(err => {
        console.warn("Autoplay vidéo :", err);
        this.audio.speakText(presentationText);
      });

      this.avatarVideo.onended = () => {
        this.avatarVideo.classList.add('hidden');
        if (this.avatarCanvas) this.avatarCanvas.classList.remove('hidden');
        this.vortex.setState('IDLE', 'Prêt à répondre');
      };
    } else {
      if (this.avatarCanvas) this.avatarCanvas.classList.remove('hidden');
      if (this.avatarVideo) this.avatarVideo.classList.add('hidden');
      this.audio.speakText(presentationText);
    }
  }

  openAvatarModal() {
    if (!this.avatarModal) return;
    this.avatarModal.classList.remove('hidden');
    this.playAvatarPresentation();
  }

  closeAvatarModal() {
    if (!this.avatarModal) return;
    this.avatarModal.classList.add('hidden');
    if (this.modalAvatarVideo) {
      this.modalAvatarVideo.pause();
    }
  }

  bindEvents() {
    // Sélection de classe
    this.classTabs.forEach(btn => {
      btn.onclick = () => {
        const c = btn.getAttribute('data-class');
        if (c) this.selectClass(c);
      };
    });

    // Envoi par bouton ou touche Entrée
    if (this.sendBtn) {
      this.sendBtn.onclick = () => this.submitQuestion();
    }
    if (this.questionInput) {
      this.questionInput.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          this.submitQuestion();
        }
      };
    }

    // Bouton Microphone Push-To-Talk principal
    if (this.micBtn) {
      this.micBtn.onclick = () => {
        if (this.audio && this.audio.audioCtx && this.audio.audioCtx.state === 'suspended') {
          this.audio.audioCtx.resume();
        }
        this.speech.toggleListening();
      };
    }

    // Bouton Microphone dans le Modal
    if (this.btnMicModal) {
      this.btnMicModal.onclick = () => {
        if (this.audio && this.audio.audioCtx && this.audio.audioCtx.state === 'suspended') {
          this.audio.audioCtx.resume();
        }
        this.speech.toggleListening();
      };
    }

    // Clic sur le Vortex / Avatar : jouer la présentation
    if (this.vortexHub) {
      this.vortexHub.onclick = () => this.playAvatarPresentation();
    }
    if (this.avatarNameBox) {
      this.avatarNameBox.onclick = () => this.playAvatarPresentation();
    }
    if (this.btnShowAvatar) {
      this.btnShowAvatar.onclick = () => this.openAvatarModal();
    }
    if (this.btnCloseAvatar) {
      this.btnCloseAvatar.onclick = () => this.closeAvatarModal();
    }

    // Reset Session
    if (this.btnReset) {
      this.btnReset.onclick = () => {
        this.audio.stop();
        this.sessionId = 'kiosk_session_' + Date.now();
        if (this.questionInput) this.questionInput.value = '';
        if (this.studentQueryPreview) this.studentQueryPreview.classList.add('hidden');
        if (this.speechContentArea) {
          this.speechContentArea.innerHTML = `
            <div class="speech-welcome-text">
              <h3 class="text-xl font-bold text-slate-800 mb-2">Nouvelle question prête !</h3>
              <p class="text-base text-slate-600 leading-relaxed">
                Session réinitialisée. Posez une nouvelle question au micro ou par écrit.
              </p>
            </div>
          `;
        }
        this.vortex.setState('IDLE', 'Prêt à répondre');
        if (this.modalVortex) this.modalVortex.setState('IDLE', 'Prêt à répondre');
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

  async submitQuestion(questionText) {
    const question = questionText || (this.questionInput ? this.questionInput.value.trim() : '');
    if (!question) return;

    if (this.questionInput) this.questionInput.value = '';
    this.audio.stop();
    
    if (this.audio.audioCtx && this.audio.audioCtx.state === 'suspended') {
      this.audio.audioCtx.resume();
    }

    if (this.studentQueryPreview) {
      this.studentQueryPreview.classList.remove('hidden');
      if (this.studentQueryText) this.studentQueryText.textContent = question;
    }

    this.vortex.setState('THINKING', 'Consultation du programme officiel...');
    if (this.modalVortex) this.modalVortex.setState('THINKING', 'Consultation du programme...');

    if (this.speechContentArea) {
      this.speechContentArea.innerHTML = `
        <div class="flex items-center gap-3 text-cyan-300 py-4">
          <div class="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
          <span class="text-sm font-medium">Recherche dans les manuels officiels et génération...</span>
        </div>
      `;
    }

    if (this.avatarTranscription) {
      this.avatarTranscription.textContent = "Recherche dans le programme officiel...";
    }

    let fullText = "";
    let sentenceBuffer = "";
    let firstSent = false;
    const clauseDelim = /([,;:\.!?…]\s+|\n+)/;
    const sentDelim = /([\.!?…]\s+|\n+)/;

    const streamSuccess = await ApiService.streamChat({
      question,
      studentClass: this.currentClass,
      subject: this.currentSubject,
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
        const isModalOpen = !this.avatarModal.classList.contains('hidden');
        
        // 🚨 CONFIGURATION : Mettre à `true` dans 2 semaines quand le compte Simli sera actif
        const ENABLE_SIMLI_WEBRTC = false;

        // Découpage et émission vocale TTS fluide (Seulement si modal fermé OU si Simli est activé)
        const match = sentDelim.exec(sentenceBuffer) || clauseDelim.exec(sentenceBuffer);
        if (match && sentenceBuffer.substring(0, match.index).trim().split(/\s+/).length >= 3) {
          const pos = match.index + match[0].length;
          const segment = sentenceBuffer.substring(0, pos).trim();
          sentenceBuffer = sentenceBuffer.substring(pos);
          if (segment.length > 2) {
            if (!isModalOpen || ENABLE_SIMLI_WEBRTC) {
                this.audio.enqueueSentence(segment);
            }
            firstSent = true;
          }
        }
      },
      onDone: async (data) => {
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

        const isModalOpen = !this.avatarModal.classList.contains('hidden');
        const ENABLE_SIMLI_WEBRTC = false; // Doit correspondre au flag ci-dessus

        // Si le buffer contient encore du texte restant
        if (sentenceBuffer.trim().length > 2) {
          if (!isModalOpen || ENABLE_SIMLI_WEBRTC) this.audio.enqueueSentence(sentenceBuffer.trim());
          firstSent = true;
        } else if (!firstSent && fullText.trim().length > 2) {
          if (!isModalOpen || ENABLE_SIMLI_WEBRTC) this.audio.enqueueSentence(fullText.trim());
          firstSent = true;
        }

        // Si Simli est DÉSACTIVÉ et que le modal est ouvert, on génère la vidéo LivePortrait 10s (Option Gratuit)
        if (!ENABLE_SIMLI_WEBRTC && isModalOpen && fullText.length > 2 && this.activeAvatar?.photoUrl) {
            if (this.modalStatusText) this.modalStatusText.textContent = "Génération de la vidéo en cours (Patientez ~10s)...";
            if (this.modalStatusDot) {
                this.modalStatusDot.className = "w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse";
            }
            
            const videoUrl = await ApiService.generateLivePortraitVideo({
                phrase: fullText,
                photoUrl: this.activeAvatar.photoUrl,
                voice: this.activeAvatar.voix_tts || this.activeAvatar.voix || 'vivienne',
                name: this.activeAvatar.nom,
                subject: this.currentSubject
            });

            if (videoUrl) {
                if (this.modalStatusText) this.modalStatusText.textContent = "Réponse prête !";
                if (this.modalStatusDot) this.modalStatusDot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400";

                if (this.modalAvatarCanvas) this.modalAvatarCanvas.classList.add('hidden');
                if (this.modalAvatarVideo) {
                    this.modalAvatarVideo.classList.remove('hidden');
                    // Gérer l'URL relative vers le backend
                    const backendUrl = window.location.origin; // or API_BASE_URL if imported
                    this.modalAvatarVideo.src = `${videoUrl}?t=${Date.now()}`;
                    this.modalAvatarVideo.muted = false;
                    this.modalAvatarVideo.play().catch(e => {
                        console.warn("Erreur lecture vidéo automatique :", e);
                        this.audio.enqueueSentence(fullText); // Fallback TTS
                    });
                }
            } else {
                if (this.modalStatusText) this.modalStatusText.textContent = "Erreur vidéo (Fallback Audio)";
                if (this.modalStatusDot) this.modalStatusDot.className = "w-2.5 h-2.5 rounded-full bg-red-500";
                this.audio.enqueueSentence(fullText); // Fallback audio
            }
        }
      }
    });

    if (!streamSuccess) {
      if (this.speechContentArea) {
        this.speechContentArea.innerHTML = `<p class="text-red-400">Désolé, une erreur de connexion est survenue.</p>`;
      }
    }

    setTimeout(() => {
      if (!this.audio.isPlayingQueue && this.vortex.currentState === 'THINKING') {
        this.vortex.setState('IDLE', 'Prêt à répondre');
        if (this.modalVortex) this.modalVortex.setState('IDLE', 'Prêt à répondre');
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

