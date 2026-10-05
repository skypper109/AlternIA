/**
 * AlternIA Device Interface - Contrôleur Kiosk Épuré (Voice-First & Avatar Photoréaliste / 2.5D).
 */

import { ApiService } from './js/services/api.js';
import { AudioService } from './js/services/audio.js';
import { SpeechService } from './js/services/speech.js';
import { VortexUI } from './js/ui/vortex.js';
import { KaTeXRenderer } from './js/ui/katex-renderer.js';
import { DidService } from './js/services/did.js';

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
    this.modalMicLabel = document.getElementById('modal-mic-label');
  }

  initModules() {
    // 1. UI Vortex avec le Logo / Avatar Photoréaliste (Halo chromatique & FFT audio)
    this.vortex = new VortexUI({
      canvasId: 'main-animated-logo-canvas',
      statusTextId: 'status-text',
      statusDotId: 'status-dot',
      defaultImageUrl: 'assets/Alternia.svg',
      isLogoMode: true
    });

    // Modal Vortex si présent (en mode carré immersif plein cadre)
    if (this.modalAvatarCanvas) {
      this.modalVortex = new VortexUI({
        canvasId: 'modal-avatar-canvas',
        statusTextId: 'modal-status-text',
        statusDotId: 'modal-status-dot',
        defaultImageUrl: 'assets/Alternia.svg',
        isLogoMode: false,
        isSquareMode: true
      });
    } else {
      this.modalVortex = null;
    }

    // 1.5 Moteur D-ID WebRTC Avatar Vidéo
    this.did = new DidService('modal-avatar-video', () => {
      if (this.modalAvatarCanvas) this.modalAvatarCanvas.classList.add('hidden');
      if (this.modalAvatarVideo) this.modalAvatarVideo.classList.remove('hidden');
    });

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
        // Synchronisation temps réel avec l'ESP32 : LED Blanche clignotante pendant le TTS
        fetch(`/api/esp32/tts-speaking?speaking=${isSpeaking ? 'true' : 'false'}`, { method: 'POST' }).catch(() => {});
      },
      onAnalyserReady: (analyser) => {
        this.vortex.setAudioAnalyser(analyser);
        if (this.modalVortex) this.modalVortex.setAudioAnalyser(analyser);
      }
    });

    // 4. Moteur Speech-To-Text (Microphone 1-clic enregistre, 1-clic coupe et envoie directement)
    this.speech = new SpeechService({
      onStart: () => {
        if (this.micBtn) this.micBtn.classList.add('is-recording');
        if (this.btnMicModal) {
          this.btnMicModal.classList.remove('from-[#314999]', 'via-[#0284C7]', 'to-[#314999]', 'ring-[#314999]/20');
          this.btnMicModal.classList.add('bg-rose-600', 'from-rose-600', 'to-red-600', 'animate-pulse', 'ring-4', 'ring-rose-400');
          this.btnMicModal.innerHTML = `
            <svg class="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="6" width="12" height="12" rx="2"></rect>
            </svg>
          `;
          this.btnMicModal.title = "Toucher pour couper et envoyer";
        }
        if (this.modalMicLabel) {
          this.modalMicLabel.textContent = "Écoute en direct... Touchez pour envoyer";
          this.modalMicLabel.classList.add('text-rose-600', 'font-semibold');
          this.modalMicLabel.classList.remove('text-slate-500');
        }
        this.vortex.setState('LISTENING', 'Écoute en cours...');
        if (this.modalVortex) this.modalVortex.setState('LISTENING', 'Écoute en cours...');
        this.audio.stop();

        // Afficher immédiatement l'indicateur d'enregistrement dans la boîte de transcription
        if (this.avatarTranscription) {
          this.avatarTranscription.innerHTML = `
            <div class="p-5 bg-rose-50/70 border-2 border-dashed border-rose-300 rounded-2xl flex flex-col gap-2 shadow-sm animate-fade-in">
              <div class="flex items-center gap-2 text-rose-600 text-xs font-bold uppercase tracking-wider">
                <span class="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping"></span>
                Microphone actif — Parlez maintenant
              </div>
              <div id="modal-live-transcript-text" class="text-slate-800 text-base sm:text-lg font-medium italic min-h-[36px]">
                « En écoute de votre question... »
              </div>
            </div>
          `;
        }
      },
      onTranscript: (transcript) => {
        if (this.questionInput) {
          this.questionInput.value = transcript;
        }
        const liveElem = document.getElementById('modal-live-transcript-text');
        if (liveElem) {
          liveElem.textContent = `« ${transcript} »`;
          liveElem.classList.remove('italic');
        } else if (this.avatarTranscription) {
          this.avatarTranscription.innerHTML = `
            <div class="p-5 bg-rose-50/70 border-2 border-dashed border-rose-300 rounded-2xl flex flex-col gap-2 shadow-sm">
              <div class="flex items-center gap-2 text-rose-600 text-xs font-bold uppercase tracking-wider">
                <span class="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping"></span>
                Microphone actif — En direct
              </div>
              <div id="modal-live-transcript-text" class="text-slate-800 text-base sm:text-lg font-medium">
                « ${transcript} »
              </div>
            </div>
          `;
        }
      },
      onEnd: (finalTranscript) => {
        if (this.micBtn) this.micBtn.classList.remove('is-recording');
        if (this.btnMicModal) {
          this.btnMicModal.classList.remove('bg-rose-600', 'from-rose-600', 'to-red-600', 'animate-pulse', 'ring-4', 'ring-rose-400');
          this.btnMicModal.classList.add('from-[#314999]', 'via-[#0284C7]', 'to-[#314999]', 'ring-[#314999]/20');
          this.btnMicModal.innerHTML = `
            <svg class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
              <line x1="12" y1="19" x2="12" y2="22"></line>
            </svg>
          `;
          this.btnMicModal.title = "Toucher pour parler";
        }
        if (this.modalMicLabel) {
          this.modalMicLabel.textContent = "Touchez pour parler";
          this.modalMicLabel.classList.remove('text-rose-600', 'font-semibold');
          this.modalMicLabel.classList.add('text-slate-500');
        }

        const query = (finalTranscript || (this.questionInput ? this.questionInput.value : '')).trim();
        if (query && query.length > 1) {
          this.submitQuestion(query);
        } else {
          this.vortex.setState('IDLE', 'Prêt à répondre');
          if (this.modalVortex) this.modalVortex.setState('IDLE', 'Prêt à répondre');
        }
      },
      onError: (err) => {
        if (this.micBtn) this.micBtn.classList.remove('is-recording');
        if (this.btnMicModal) {
          this.btnMicModal.classList.remove('bg-rose-600', 'from-rose-600', 'to-red-600', 'animate-pulse', 'ring-4', 'ring-rose-400');
          this.btnMicModal.classList.add('from-[#314999]', 'via-[#0284C7]', 'to-[#314999]', 'ring-[#314999]/20');
          this.btnMicModal.innerHTML = `
            <svg class="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
              <line x1="12" y1="19" x2="12" y2="22"></line>
            </svg>
          `;
          this.btnMicModal.title = "Toucher pour parler";
        }
        if (this.modalMicLabel) {
          this.modalMicLabel.textContent = "Touchez pour parler";
          this.modalMicLabel.classList.remove('text-rose-600', 'font-semibold');
          this.modalMicLabel.classList.add('text-slate-500');
        }
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
          // Configuration de la voix TTS de l'avatar actif (Simli ne sera initialisé QUE si on ouvre le modal avatar)
          if (this.audio) {
            const chosenVoice = data.voixTts || data.voix_tts || data.voixId || 'vivienne';
            this.audio.setVoice(chosenVoice);
            const faceId = data.face_id || data.faceId || null;
            console.log(`🎬 [AlternIA Kiosk] Avatar actif: "${data.nom}" | Voix TTS: "${chosenVoice}" | Face ID: "${faceId}"`);
          }
        }
      }
    } catch (e) {
      console.warn("Note chargement avatar :", e);
    }
  }

  playAvatarPresentation() {
    if (this.audio) {
      this.audio.ensureAudioContext();
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
      this.avatarTranscription.innerHTML = `
        <div class="p-4 bg-slate-50 border border-slate-200/80 rounded-2xl text-slate-800 leading-relaxed text-base sm:text-lg font-normal">
          ${presentationText}
        </div>
      `;
    }

    if (this.avatarCanvas) this.avatarCanvas.classList.remove('hidden');
    this.audio.speakText(presentationText);
  }

  openAvatarModal() {
    if (!this.avatarModal) return;
    this.avatarModal.classList.remove('hidden');

    // 1. Stopper immédiatement tout audio en cours pour éviter tout doublon
    if (this.audio) {
      this.audio.stop();
      this.audio.setSimliActive(true);
      const faceId = this.activeAvatar?.face_id || this.activeAvatar?.faceId || null;
      if (this.audio.simli) {
        this.audio.simli.init(faceId);
      }
    }

    // 2. Jouer la présentation d'accueil uniquement si aucune conversation n'est affichée
    const currentText = this.avatarTranscription ? this.avatarTranscription.textContent.trim() : '';
    if (!currentText || currentText.length < 5) {
      this.playAvatarPresentation();
    }
  }

  closeAvatarModal() {
    if (!this.avatarModal) return;
    this.avatarModal.classList.add('hidden');
    if (this.modalAvatarVideo) {
      try { this.modalAvatarVideo.pause(); } catch (_) {}
    }
    // Fermer et déconnecter immédiatement Simli et couper l'audio à la fermeture
    if (this.audio) {
      this.audio.stop();
      this.audio.setSimliActive(false);
    }
    if (this.speech && this.speech.isListening()) {
      this.speech.stop();
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
      this.micBtn.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (this.audio && this.audio.audioCtx && this.audio.audioCtx.state === 'suspended') {
          this.audio.audioCtx.resume();
        }
        this.speech.toggleListening();
      };
    }

    // Bouton Microphone dans le Modal
    if (this.btnMicModal) {
      this.btnMicModal.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (this.audio) {
          this.audio.ensureAudioContext();
        }
        this.speech.toggleListening();
      };
    }

    // Clic sur l'Avatar modal pour forcer la connexion Simli si nécessaire
    if (this.modalAvatarCanvas) {
      this.modalAvatarCanvas.onclick = () => {
        if (this.audio && this.audio.simli) {
          const faceId = this.activeAvatar?.face_id || this.activeAvatar?.faceId || null;
          this.audio.setSimliActive(true);
          this.audio.simli.init(faceId);
        }
      };
    }
    if (this.modalAvatarVideo) {
      this.modalAvatarVideo.onclick = () => {
        if (this.audio && this.audio.simli) {
          const faceId = this.activeAvatar?.face_id || this.activeAvatar?.faceId || null;
          this.audio.setSimliActive(true);
          this.audio.simli.init(faceId);
        }
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

    // Synchronisation immédiate sur le canal ESP32 : 10ème -> BLEU, 11ème -> ROUGE, 12ème -> JAUNE
    // Canal 1 : Via l'API Cloud (WebSocket /ws/esp32)
    fetch(`/api/esp32/select-class?classe=${encodeURIComponent(classId)}&mic_connected=true`, { method: 'POST' }).catch(() => {});
    // Canal 2 : Directement sur l'ESP32 en local (192.168.4.1) si connecté à son Wi-Fi SoftAP
    fetch(`http://192.168.4.1/api/select-class?classe=${encodeURIComponent(classId)}`, { mode: 'no-cors' }).catch(() => {});
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
      this.avatarTranscription.innerHTML = `
        <div class="p-4 bg-slate-100 border border-slate-200/80 rounded-2xl text-slate-900 font-medium mb-4 text-base sm:text-lg">
          ${question}
        </div>
        <div class="flex items-center gap-3 text-slate-500 py-3">
          <div class="w-4 h-4 border-2 border-[#314999] border-t-transparent rounded-full animate-spin"></div>
          <span class="text-sm font-medium">Recherche et formulation de la réponse...</span>
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
      subject: this.currentSubject,
      sessionId: this.sessionId,
      onChunk: (chunk) => {
        fullText += chunk;
        if (this.speechContentArea) {
          this.speechContentArea.innerHTML = `<div class="formatted-text">${this.formatMarkdownText(fullText)}</div>`;
          this.katex.renderFormulasInElement(this.speechContentArea);
        }
        if (this.avatarTranscription) {
          this.avatarTranscription.innerHTML = `
            <div class="p-4 bg-slate-100 border border-slate-200/80 rounded-2xl text-slate-900 font-medium mb-4 text-base sm:text-lg">
              ${question}
            </div>
            <div class="text-slate-800 text-base sm:text-lg leading-relaxed space-y-3 font-normal">
              ${this.formatMarkdownText(fullText)}
            </div>
          `;
          this.katex.renderFormulasInElement(this.avatarTranscription);
          if (this.avatarTranscription.parentElement) {
            this.avatarTranscription.parentElement.scrollTop = this.avatarTranscription.parentElement.scrollHeight;
          }
        }

        sentenceBuffer += chunk;
        const isModalOpen = !this.avatarModal.classList.contains('hidden');

        // Découpage et émission vocale TTS fluide vers Simli WebRTC / AudioService
        const match = sentDelim.exec(sentenceBuffer) || clauseDelim.exec(sentenceBuffer);
        if (match && sentenceBuffer.substring(0, match.index).trim().split(/\s+/).length >= 3) {
          const pos = match.index + match[0].length;
          const segment = sentenceBuffer.substring(0, pos).trim();
          sentenceBuffer = sentenceBuffer.substring(pos);
          if (segment.length > 2) {
            this.audio.enqueueSentence(segment);
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
          this.avatarTranscription.innerHTML = `
            <div class="p-4 bg-slate-100 border border-slate-200/80 rounded-2xl text-slate-900 font-medium mb-4 text-base sm:text-lg">
              ${question}
            </div>
            <div class="text-slate-800 text-base sm:text-lg leading-relaxed space-y-3 font-normal">
              ${this.formatMarkdownText(fullText)}
            </div>
          `;
          this.katex.renderFormulasInElement(this.avatarTranscription);
          if (this.avatarTranscription.parentElement) {
            this.avatarTranscription.parentElement.scrollTop = this.avatarTranscription.parentElement.scrollHeight;
          }
        }

        // Si le buffer contient encore du texte restant
        if (sentenceBuffer.trim().length > 2) {
          this.audio.enqueueSentence(sentenceBuffer.trim());
          firstSent = true;
        } else if (!firstSent && fullText.trim().length > 2) {
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

