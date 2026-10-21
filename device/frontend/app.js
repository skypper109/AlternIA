/**
 * AlternIA Device Interface - Contrôleur Kiosk & Portail Tactile/Vocal.
 * Compatible TV HDMI (Chromium Kiosk), écrans tactiles et portail Wi-Fi Alta-Box.
 */

import { ApiService } from './js/services/api.js';
import { AudioService } from './js/services/audio.js';
import { SpeechService } from './js/services/speech.js';
import { VortexUI } from './js/ui/vortex.js';
import { KaTeXRenderer } from './js/ui/katex-renderer.js';
import { DidService } from './js/services/did.js';
import { CYCLES, CURRICULUM_DATA } from './js/config/curriculum.js';

export class AlternIAApp {
  constructor() {
    this.currentCycle = 'secondaire';
    this.currentClass = '10eme';
    this.currentSubject = null;
    this.sessionId = 'kiosk_session_' + Date.now();
    this.activeAvatar = null;
    this.currentScreen = 'welcome';
    this.thread = []; // Historique de conversation { role: 'user'|'assistant', text, source }

    this.initDOM();
    this.initClock();
    this.initNetworkStatus();
    this.initModules();
    this.bindEvents();
    this.loadActiveAvatar();
    this.renderSuggestions();
  }

  /* -------------------------------------------------------------------------
     1. ÉLÉMENTS DOM
     ------------------------------------------------------------------------- */
  initDOM() {
    // Écrans
    this.screenWelcome = document.getElementById('screen-welcome');
    this.screenWorkspace = document.getElementById('screen-workspace');
    this.welcomeGreeting = document.getElementById('welcome-greeting');
    this.welcomeClock = document.getElementById('welcome-clock');
    this.topbarClock = document.getElementById('topbar-clock');
    this.netStatus = document.getElementById('net-status');
    this.netStatusLabel = document.getElementById('net-status-label');
    this.btnWelcomeListen = document.getElementById('btn-welcome-listen');

    // Niveaux & Tiroirs
    this.levelCards = document.querySelectorAll('.level-card');
    this.gradeChips = document.querySelectorAll('.grade-chip');
    this.levelPillCycle = document.getElementById('level-pill-cycle');
    this.levelPillGrade = document.getElementById('level-pill-grade');
    this.gradeSegment = document.getElementById('grade-segment');
    this.btnChangeLevel = document.getElementById('btn-change-level');
    this.btnHome = document.getElementById('btn-home');

    // Panneau Tuteur
    this.vortexHub = document.getElementById('alta-vortex-hub');
    this.avatarNameText = document.getElementById('alta-avatar-name');
    this.avatarNameBox = document.getElementById('alta-avatar-name-box');
    this.avatarVideo = document.getElementById('alta-avatar-video');
    this.avatarCanvas = document.getElementById('main-animated-logo-canvas');
    this.classSublabel = document.getElementById('alta-class-sublabel');
    this.teacherHeaderLabel = document.getElementById('teacher-header-label');
    this.ragSourceBadge = document.getElementById('rag-source-badge');

    // Commandes Topbar
    this.btnShowAvatar = document.getElementById('btn-show-avatar');
    this.btnOpenAvatarPanel = document.getElementById('btn-open-avatar-panel');
    this.btnMute = document.getElementById('btn-toggle-mute');
    this.btnReset = document.getElementById('btn-reset-session');

    // Microphones & Écoute
    this.micBtn = document.getElementById('btn-mic-main');
    this.micInstructionLabel = document.getElementById('mic-instruction-label');
    this.listeningBanner = document.getElementById('listening-banner');
    this.listeningText = document.getElementById('listening-text');

    // Saisie & Conversation principale
    this.speechContentArea = document.getElementById('speech-content-area');
    this.conversationEmpty = document.getElementById('conversation-empty');
    this.conversationThread = document.getElementById('conversation-thread');
    this.suggestionsContainer = document.getElementById('suggestions');
    this.mainComposer = document.getElementById('main-composer');
    this.questionInput = document.getElementById('question-input');
    this.sendBtn = document.getElementById('btn-send');

    // Modale Professeur Virtuel (<dialog>)
    this.avatarModal = document.getElementById('avatar-fullscreen-modal');
    this.modalAvatarTitle = document.getElementById('modal-avatar-title');
    this.modalAvatarSubtitle = document.getElementById('modal-avatar-subtitle');
    this.modalAvatarVideo = document.getElementById('modal-avatar-video');
    this.modalAvatarCanvas = document.getElementById('modal-avatar-canvas');
    this.modalStatusDot = document.getElementById('modal-status-dot');
    this.modalStatusText = document.getElementById('modal-status-text');
    this.modalLevelBadge = document.getElementById('modal-level-badge');
    this.avatarTranscription = document.getElementById('avatar-fullscreen-transcription');
    this.modalTranscriptScroll = document.getElementById('modal-transcript-scroll');
    this.modalEmpty = document.getElementById('modal-empty');
    this.modalSuggestions = document.getElementById('modal-suggestions');
    this.modalListeningBanner = document.getElementById('modal-listening-banner');
    this.modalListeningText = document.getElementById('modal-listening-text');
    this.btnCloseAvatar = document.getElementById('btn-close-avatar');
    this.btnMicModal = document.getElementById('btn-mic-modal');
    this.modalMicLabel = document.getElementById('modal-mic-label');

    // Saisie DANS le modal avatar (nouveauté demandée)
    this.modalComposer = document.getElementById('modal-composer');
    this.modalQuestionInput = document.getElementById('modal-question-input');
    this.btnModalSend = document.getElementById('btn-modal-send');
  }

  /* -------------------------------------------------------------------------
     2. HORLOGE & ÉTAT RÉSEAU
     ------------------------------------------------------------------------- */
  initClock() {
    const updateTime = () => {
      const now = new Date();
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      const timeStr = `${hours}:${minutes}`;
      if (this.welcomeClock) this.welcomeClock.textContent = timeStr;
      if (this.topbarClock) this.topbarClock.textContent = timeStr;

      // Salutation dynamique
      if (this.welcomeGreeting) {
        const h = now.getHours();
        const salutation = (h >= 17 || h < 5) ? 'Bonsoir !' : 'Bonjour !';
        this.welcomeGreeting.textContent = salutation;
      }
    };
    updateTime();
    setInterval(updateTime, 10000);
  }

  async initNetworkStatus() {
    const check = async () => {
      const isOnline = navigator.onLine;
      let backendHealthy = false;
      try {
        const res = await fetch('/health', { method: 'GET', cache: 'no-store' });
        backendHealthy = res.ok;
      } catch (_) {
        // En local le backend peut répondre via l'API cloud ou localhost
        backendHealthy = isOnline;
      }

      if (this.netStatus && this.netStatusLabel) {
        if (backendHealthy) {
          this.netStatus.dataset.online = 'true';
          this.netStatusLabel.textContent = 'Boîtier connecté · Prêt';
        } else {
          this.netStatus.dataset.online = 'false';
          this.netStatusLabel.textContent = isOnline ? 'Boîtier en ligne' : 'Mode hors-ligne local';
        }
      }
    };

    check();
    window.addEventListener('online', check);
    window.addEventListener('offline', check);
    setInterval(check, 30000);
  }

  /* -------------------------------------------------------------------------
     3. MODULES AUDIO, AVATAR, KATEX, VORTEX
     ------------------------------------------------------------------------- */
  initModules() {
    // 1. Vortex animé
    this.vortex = new VortexUI({
      canvasId: 'main-animated-logo-canvas',
      statusTextId: 'status-text',
      statusDotId: 'status-dot',
      defaultImageUrl: 'assets/Alternia.svg',
      isLogoMode: true
    });

    if (this.modalAvatarCanvas) {
      this.modalVortex = new VortexUI({
        canvasId: 'modal-avatar-canvas',
        statusTextId: 'modal-status-text',
        statusDotId: 'modal-status-dot',
        defaultImageUrl: 'assets/Alternia.svg',
        isLogoMode: false,
        isSquareMode: true
      });
    }

    // 2. D-ID WebRTC
    this.did = new DidService('modal-avatar-video', () => {
      if (this.modalAvatarCanvas) this.modalAvatarCanvas.classList.add('hidden');
      if (this.modalAvatarVideo) this.modalAvatarVideo.classList.remove('opacity-0');
    });

    // 3. KaTeX
    this.katex = new KaTeXRenderer();

    // 4. Synthèse vocale & FFT
    this.audio = new AudioService({
      onSpeakingChange: (isSpeaking) => {
        document.body.dataset.state = isSpeaking ? 'speaking' : 'idle';
        if (isSpeaking) {
          this.vortex.setState('SPEAKING', 'Enseignant explique...');
          if (this.modalVortex) this.modalVortex.setState('SPEAKING', 'Enseignant explique...');
        } else if (this.vortex.currentState === 'SPEAKING') {
          this.vortex.setState('IDLE', 'Prêt à répondre');
          if (this.modalVortex) this.modalVortex.setState('IDLE', 'Prêt à répondre');
        }
        // LED Blanche clignotante ESP32 pendant le TTS
        fetch(`/api/esp32/tts-speaking?speaking=${isSpeaking ? 'true' : 'false'}`, { method: 'POST' }).catch(() => {});
      },
      onAnalyserReady: (analyser) => {
        this.vortex.setAudioAnalyser(analyser);
        if (this.modalVortex) this.modalVortex.setAudioAnalyser(analyser);
      }
    });

    // 5. Speech-to-Text
    this.speech = new SpeechService({
      onStart: () => {
        document.body.dataset.state = 'listening';
        this.setMicRecordingState(true);
        this.vortex.setState('LISTENING', 'Écoute en cours...');
        if (this.modalVortex) this.modalVortex.setState('LISTENING', 'Écoute en cours...');
        this.audio.stop();

        this.showListeningBanner("Je t'écoute… parle maintenant");
      },
      onTranscript: (transcript) => {
        if (this.questionInput) this.questionInput.value = transcript;
        if (this.modalQuestionInput) this.modalQuestionInput.value = transcript;
        this.showListeningBanner(`« ${transcript} »`);
      },
      onEnd: (finalTranscript) => {
        document.body.dataset.state = 'idle';
        this.setMicRecordingState(false);
        this.hideListeningBanner();

        const query = (finalTranscript || (this.questionInput ? this.questionInput.value : '') || (this.modalQuestionInput ? this.modalQuestionInput.value : '')).trim();
        if (query && query.length > 1) {
          this.submitQuestion(query);
        } else {
          this.vortex.setState('IDLE', 'Prêt à répondre');
          if (this.modalVortex) this.modalVortex.setState('IDLE', 'Prêt à répondre');
        }
      },
      onError: (err) => {
        document.body.dataset.state = 'idle';
        this.setMicRecordingState(false);
        this.hideListeningBanner();
        this.vortex.setState('IDLE', 'Prêt à répondre');
        if (this.modalVortex) this.modalVortex.setState('IDLE', 'Prêt à répondre');
        console.warn('Erreur reconnaissance vocale :', err);
      }
    });
  }

  setMicRecordingState(isRec) {
    [this.micBtn, this.btnMicModal].forEach(btn => {
      if (!btn) return;
      btn.classList.toggle('is-recording', isRec);
      btn.setAttribute('aria-pressed', isRec ? 'true' : 'false');
      btn.title = isRec ? 'Toucher pour arrêter et envoyer' : 'Toucher pour parler';
    });

    if (this.micInstructionLabel) {
      this.micInstructionLabel.textContent = isRec ? 'Enregistrement actif… retouche pour envoyer' : 'Touche pour parler, retouche pour envoyer';
      this.micInstructionLabel.classList.toggle('is-live', isRec);
    }
    if (this.modalMicLabel) {
      this.modalMicLabel.textContent = isRec ? 'En direct… retouche pour envoyer' : 'Touche pour parler';
      this.modalMicLabel.classList.toggle('is-live', isRec);
    }
  }

  showListeningBanner(text) {
    if (this.listeningBanner) {
      this.listeningBanner.hidden = false;
      if (this.listeningText) this.listeningText.textContent = text;
    }
    if (this.modalListeningBanner) {
      this.modalListeningBanner.hidden = false;
      if (this.modalListeningText) this.modalListeningText.textContent = text;
    }
  }

  hideListeningBanner() {
    if (this.listeningBanner) this.listeningBanner.hidden = true;
    if (this.modalListeningBanner) this.modalListeningBanner.hidden = true;
  }

  /* -------------------------------------------------------------------------
     4. GESTION DES ÉCRANS & NAVIGATION
     ------------------------------------------------------------------------- */
  showScreen(screenName) {
    if (this.currentScreen === screenName) return;

    const apply = () => {
      this.currentScreen = screenName;
      document.body.dataset.screen = screenName;
      if (screenName === 'welcome') {
        if (this.screenWelcome) this.screenWelcome.hidden = false;
        if (this.screenWorkspace) this.screenWorkspace.hidden = true;
        const target = document.getElementById('welcome-title');
        if (target) target.focus();
      } else {
        if (this.screenWelcome) this.screenWelcome.hidden = true;
        if (this.screenWorkspace) this.screenWorkspace.hidden = false;
        const target = document.getElementById('workspace-title');
        if (target) target.focus();
      }
    };

    if (document.startViewTransition) {
      document.startViewTransition(apply);
    } else {
      apply();
    }
  }

  /* -------------------------------------------------------------------------
     5. GESTION DES CYCLES & SÉLECTION DE CLASSE
     ------------------------------------------------------------------------- */
  toggleCycleAccordion(cycleId) {
    const card = document.querySelector(`.level-card[data-cycle="${cycleId}"]`);
    if (!card) return;
    const btn = card.querySelector('.level-card__main');

    // Terminale n'a pas de sous-classe : sélection directe
    if (cycleId === 'terminale') {
      this.selectClass('12eme');
      return;
    }

    const wasOpen = card.classList.contains('is-open');
    // Fermer les autres tiroirs
    this.levelCards.forEach(c => {
      c.classList.remove('is-open');
      const b = c.querySelector('.level-card__main');
      if (b) b.setAttribute('aria-expanded', 'false');
    });

    if (!wasOpen) {
      card.classList.add('is-open');
      if (btn) btn.setAttribute('aria-expanded', 'true');
      const firstChip = card.querySelector('.grade-chip');
      if (firstChip) firstChip.focus();
    }
  }

  selectClass(classId, shouldTransition = true) {
    this.currentClass = classId;

    // Détermination du cycle
    let foundCycle = 'secondaire';
    for (const [cKey, cData] of Object.entries(CYCLES)) {
      if (cData.grades.some(g => g.id === classId)) {
        foundCycle = cKey;
        break;
      }
    }
    this.currentCycle = foundCycle;
    document.body.dataset.cycle = foundCycle;

    // Mise à jour de l'UI
    this.updateClassLabels(classId, foundCycle);
    this.renderGradeSegment(foundCycle, classId);
    this.renderSuggestions();

    // Audio context
    if (this.audio && this.audio.audioCtx && this.audio.audioCtx.state === 'suspended') {
      this.audio.audioCtx.resume();
    }

    // Message vocal de confirmation
    const vocalLabels = {
      '6eme': 'sixième année',
      '7eme': 'septième année',
      '8eme': 'huitième année',
      '9eme': 'neuvième année, préparation au D E F',
      '10eme': 'dixième année tronc commun',
      '11eme': 'onzième année du lycée',
      '12eme': 'classe de terminale, objectif baccalauréat'
    };
    const voiceMsg = vocalLabels[classId] ? `Tu as choisi la ${vocalLabels[classId]}. Pose-moi ta question !` : 'Classe sélectionnée.';
    if (this.audio) {
      this.audio.speakText(voiceMsg);
    }

    // Synchronisation ESP32 :
    // 10ème -> BLEU, 11ème -> ROUGE, 12ème -> JAUNE, fondamental -> GREEN
    fetch(`/api/esp32/select-class?classe=${encodeURIComponent(classId)}&mic_connected=true`, { method: 'POST' }).catch(() => {});
    fetch(`http://192.168.4.1/api/select-class?classe=${encodeURIComponent(classId)}`, { mode: 'no-cors' }).catch(() => {});

    // Transition vers l'espace de travail
    if (shouldTransition) {
      this.showScreen('workspace');
    }
  }

  updateClassLabels(classId, cycleId) {
    const cycle = CYCLES[cycleId];
    const gradeObj = cycle?.grades.find(g => g.id === classId) || { name: classId, short: classId, sub: '' };

    if (this.levelPillCycle) this.levelPillCycle.textContent = cycle?.label || 'Niveau';
    if (this.levelPillGrade) this.levelPillGrade.textContent = gradeObj.short || classId;
    if (this.modalLevelBadge) this.modalLevelBadge.textContent = `${cycle?.label} · ${gradeObj.short}`;

    if (this.classSublabel) {
      this.classSublabel.textContent = `${gradeObj.name} • Programme Officiel du Mali`;
    }

    // Indication visuelle des chips
    this.gradeChips.forEach(chip => {
      chip.classList.toggle('is-active', chip.dataset.grade === classId);
    });

    this.levelCards.forEach(c => {
      c.classList.toggle('is-current', c.dataset.cycle === cycleId);
    });

    const emptyTitle = document.getElementById('empty-title');
    if (emptyTitle) {
      emptyTitle.textContent = `Prêt pour la ${gradeObj.name}.`;
    }
  }

  renderGradeSegment(cycleId, currentGradeId) {
    if (!this.gradeSegment) return;
    const cycle = CYCLES[cycleId];
    if (!cycle || cycle.grades.length <= 1) {
      this.gradeSegment.innerHTML = '';
      return;
    }

    this.gradeSegment.innerHTML = cycle.grades.map(g => `
      <button type="button" data-grade-btn="${g.id}" aria-pressed="${g.id === currentGradeId ? 'true' : 'false'}">
        ${g.short}
      </button>
    `).join('');

    this.gradeSegment.querySelectorAll('button').forEach(btn => {
      btn.onclick = () => {
        const gid = btn.getAttribute('data-grade-btn');
        if (gid) this.selectClass(gid, false);
      };
    });

    const activeBtn = this.gradeSegment.querySelector('button[aria-pressed="true"]');
    if (activeBtn && typeof activeBtn.scrollIntoView === 'function') {
      try {
        activeBtn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      } catch (_) {}
    }
  }

  renderSuggestions() {
    const classData = CURRICULUM_DATA.classes.find(c => c.id === this.currentClass)
      || CURRICULUM_DATA.classes.find(c => c.id === '10eme');

    const challenges = classData?.featuredChallenges || [];

    const buildHTML = (items) => items.map(ch => `
      <button type="button" class="suggestion" data-query="${this.escapeAttr(ch.query)}">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
        <span>${this.escapeHTML(ch.title)}</span>
      </button>
    `).join('');

    if (this.suggestionsContainer) {
      this.suggestionsContainer.innerHTML = buildHTML(challenges);
      this.suggestionsContainer.querySelectorAll('.suggestion').forEach(btn => {
        btn.onclick = () => {
          const q = btn.getAttribute('data-query');
          if (q) this.submitQuestion(q);
        };
      });
    }

    if (this.modalSuggestions) {
      this.modalSuggestions.innerHTML = buildHTML(challenges);
      this.modalSuggestions.querySelectorAll('.suggestion').forEach(btn => {
        btn.onclick = () => {
          const q = btn.getAttribute('data-query');
          if (q) this.submitQuestion(q);
        };
      });
    }
  }

  /* -------------------------------------------------------------------------
     6. AVATAR ACTIF & PRÉSENTATION
     ------------------------------------------------------------------------- */
  async loadActiveAvatar() {
    try {
      let resp = await fetch('/api/avatars/actif');
      if (!resp.ok) resp = await fetch('/api/avatars');
      if (resp.ok) {
        const raw = await resp.json();
        const data = Array.isArray(raw) ? (raw.find(a => a.parDefaut || a.actif) || raw[0]) : raw;
        if (data) {
          this.activeAvatar = data;
          if (this.avatarNameText && data.nom) this.avatarNameText.textContent = data.nom;
          if (this.modalAvatarTitle && data.nom) this.modalAvatarTitle.textContent = data.nom;
          if (this.teacherHeaderLabel && data.nom) this.teacherHeaderLabel.textContent = `Explications de ${data.nom}`;

          if (this.modalAvatarSubtitle) {
            const subject = data.matiere || 'Tuteur Pédagogique';
            const style = data.stylePedagogique ? ` • Style ${data.stylePedagogique}` : '';
            this.modalAvatarSubtitle.textContent = `${subject}${style}`;
          }

          if (this.audio) {
            const chosenVoice = data.voixTts || data.voix_tts || data.voixId || 'henri';
            this.audio.setVoice(chosenVoice);
          }
        }
      }
    } catch (e) {
      console.warn('Note chargement avatar :', e);
    }
  }

  playAvatarPresentation() {
    if (this.audio) this.audio.ensureAudioContext();

    const nom = this.activeAvatar?.nom || 'AlternIA';
    const matiere = this.activeAvatar?.matiere || 'toutes les matières du fondamental et du lycée';
    const presentationText = this.activeAvatar?.phrase ||
      `Bonjour ! Je suis ${nom}, ton tuteur pédagogique intelligent. Je suis à ta disposition pour t'expliquer tes leçons, résoudre des exercices et préparer tes examens du DEF ou du Baccalauréat selon les programmes officiels du Mali. Pose-moi toutes tes questions !`;

    this.appendMessage({
      role: 'assistant',
      text: presentationText,
      source: 'Présentation officielle'
    });

    if (this.avatarCanvas) this.avatarCanvas.classList.remove('hidden');
    this.audio.speakText(presentationText);
  }

  /* -------------------------------------------------------------------------
     7. MODALE AVATAR PLEIN ÉCRAN
     ------------------------------------------------------------------------- */
  openAvatarModal() {
    if (!this.avatarModal) return;

    if (typeof this.avatarModal.showModal === 'function') {
      try {
        if (!this.avatarModal.open) this.avatarModal.showModal();
      } catch (_) {
        this.avatarModal.classList.remove('hidden');
      }
    } else {
      this.avatarModal.classList.remove('hidden');
    }

    if (this.audio) {
      this.audio.stop();
      this.audio.setSimliActive(true);
      const faceId = this.activeAvatar?.face_id || this.activeAvatar?.faceId || null;
      if (this.audio.simli) {
        this.audio.simli.init(faceId);
      }
    }

    if (this.modalEmpty && this.thread.length > 0) {
      this.modalEmpty.hidden = true;
    }

    // Focus automatique sur le champ de saisie du modal
    setTimeout(() => {
      if (this.modalQuestionInput) this.modalQuestionInput.focus();
    }, 150);
  }

  closeAvatarModal() {
    if (!this.avatarModal) return;

    if (typeof this.avatarModal.close === 'function') {
      try {
        if (this.avatarModal.open) this.avatarModal.close();
      } catch (_) {
        this.avatarModal.classList.add('hidden');
      }
    } else {
      this.avatarModal.classList.add('hidden');
    }

    if (this.modalAvatarVideo) {
      try { this.modalAvatarVideo.pause(); } catch (_) {}
    }
    if (this.audio) {
      this.audio.stop();
      this.audio.setSimliActive(false);
    }
    if (this.speech && this.speech.isListening()) {
      this.speech.stop();
    }
  }

  /* -------------------------------------------------------------------------
     8. ÉVÉNEMENTS & INTERACTIONS
     ------------------------------------------------------------------------- */
  bindEvents() {
    // Bouton écoute présentation accueil
    if (this.btnWelcomeListen) {
      this.btnWelcomeListen.onclick = () => {
        this.playAvatarPresentation();
      };
    }

    // Accordéons des niveaux (Accueil)
    document.querySelectorAll('[data-cycle-btn]').forEach(btn => {
      btn.onclick = () => {
        const cycle = btn.getAttribute('data-cycle-btn');
        if (cycle) this.toggleCycleAccordion(cycle);
      };
    });

    // Boutons de sous-classes (Accueil)
    this.gradeChips.forEach(chip => {
      chip.onclick = (e) => {
        e.stopPropagation();
        const grade = chip.getAttribute('data-grade');
        if (grade) this.selectClass(grade, true);
      };
    });

    // Changer de niveau depuis le topbar
    if (this.btnChangeLevel) {
      this.btnChangeLevel.onclick = () => this.showScreen('welcome');
    }
    if (this.btnHome) {
      this.btnHome.onclick = () => this.showScreen('welcome');
    }

    // Formulaire de saisie principal
    if (this.mainComposer) {
      this.mainComposer.onsubmit = (e) => {
        e.preventDefault();
        this.submitQuestion();
      };
    }
    if (this.sendBtn && !this.mainComposer) {
      this.sendBtn.onclick = () => this.submitQuestion();
    }

    // Formulaire de saisie du modal avatar (nouveauté)
    if (this.modalComposer) {
      this.modalComposer.onsubmit = (e) => {
        e.preventDefault();
        const text = this.modalQuestionInput ? this.modalQuestionInput.value.trim() : '';
        if (text) {
          this.submitQuestion(text);
          if (this.modalQuestionInput) this.modalQuestionInput.value = '';
        }
      };
    }
    if (this.btnModalSend && !this.modalComposer) {
      this.btnModalSend.onclick = () => {
        const text = this.modalQuestionInput ? this.modalQuestionInput.value.trim() : '';
        if (text) {
          this.submitQuestion(text);
          if (this.modalQuestionInput) this.modalQuestionInput.value = '';
        }
      };
    }

    // Micro principal
    if (this.micBtn) {
      this.micBtn.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (this.audio) this.audio.ensureAudioContext();
        this.speech.toggleListening();
      };
    }

    // Micro dans le modal avatar
    if (this.btnMicModal) {
      this.btnMicModal.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (this.audio) this.audio.ensureAudioContext();
        this.speech.toggleListening();
      };
    }

    // Ouverture / Fermeture modal avatar
    if (this.btnShowAvatar) {
      this.btnShowAvatar.onclick = () => this.openAvatarModal();
    }
    if (this.btnOpenAvatarPanel) {
      this.btnOpenAvatarPanel.onclick = () => this.openAvatarModal();
    }
    if (this.btnCloseAvatar) {
      this.btnCloseAvatar.onclick = () => this.closeAvatarModal();
    }
    if (this.avatarModal) {
      this.avatarModal.addEventListener('cancel', (e) => {
        e.preventDefault();
        this.closeAvatarModal();
      });
    }

    // Clic vortex
    if (this.vortexHub) {
      this.vortexHub.onclick = () => this.playAvatarPresentation();
      this.vortexHub.onkeydown = (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.playAvatarPresentation();
        }
      };
    }
    if (this.avatarNameBox) {
      this.avatarNameBox.onclick = () => this.playAvatarPresentation();
    }

    // Réinitialiser la session
    if (this.btnReset) {
      this.btnReset.onclick = () => this.resetSession();
    }

    // Mute / Unmute
    if (this.btnMute) {
      this.btnMute.onclick = () => {
        const isMuted = this.audio.toggleMute();
        this.btnMute.setAttribute('aria-pressed', isMuted ? 'true' : 'false');
      };
    }

    // Fermeture modal formule
    const btnCloseFormula = document.getElementById('btn-close-formula-modal');
    if (btnCloseFormula) {
      btnCloseFormula.onclick = () => this.katex.closeFormulaModal();
    }
  }

  resetSession() {
    this.audio.stop();
    this.sessionId = 'kiosk_session_' + Date.now();
    this.thread = [];
    if (this.questionInput) this.questionInput.value = '';
    if (this.modalQuestionInput) this.modalQuestionInput.value = '';

    if (this.conversationThread) this.conversationThread.innerHTML = '';
    if (this.conversationEmpty) this.conversationEmpty.hidden = false;
    if (this.avatarTranscription) this.avatarTranscription.innerHTML = '';
    if (this.modalEmpty) this.modalEmpty.hidden = false;

    this.vortex.setState('IDLE', 'Prêt à répondre');
    if (this.modalVortex) this.modalVortex.setState('IDLE', 'Prêt à répondre');
    document.body.dataset.state = 'idle';

    if (this.audio) {
      this.audio.speakText("Session réinitialisée. Je suis prêt pour une nouvelle question !");
    }
  }

  /* -------------------------------------------------------------------------
     9. ENVOI & AFFICHAGE DES QUESTIONS / RÉPONSES
     ------------------------------------------------------------------------- */
  async submitQuestion(questionText) {
    const question = (questionText || (this.questionInput ? this.questionInput.value.trim() : '') || (this.modalQuestionInput ? this.modalQuestionInput.value.trim() : '')).trim();
    if (!question) return;

    if (this.questionInput) this.questionInput.value = '';
    if (this.modalQuestionInput) this.modalQuestionInput.value = '';
    this.audio.stop();
    if (this.audio) this.audio.ensureAudioContext();

    // Ajout question élève au fil
    this.appendMessage({ role: 'user', text: question });

    // État réflexion
    document.body.dataset.state = 'thinking';
    this.vortex.setState('THINKING', 'Consultation du programme officiel...');
    if (this.modalVortex) this.modalVortex.setState('THINKING', 'Consultation du programme...');

    // Création de l'élément de réponse en streaming
    const messageNode = this.createAssistantMessagePlaceholder();

    let fullText = '';
    let sentenceBuffer = '';
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
        this.updateAssistantMessage(messageNode, fullText);

        sentenceBuffer += chunk;
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
        if (data.sources && data.sources.length > 0) {
          const sourceDoc = data.sources[0].document || 'Programme Officiel du Mali';
          if (this.ragSourceBadge) this.ragSourceBadge.textContent = sourceDoc;
          this.setAssistantSource(messageNode, sourceDoc);
        }
        if (data.full_text) fullText = data.full_text;
        this.updateAssistantMessage(messageNode, fullText, true);

        if (sentenceBuffer.trim().length > 2) {
          this.audio.enqueueSentence(sentenceBuffer.trim());
          firstSent = true;
        } else if (!firstSent && fullText.trim().length > 2) {
          this.audio.enqueueSentence(fullText.trim());
          firstSent = true;
        }

        setTimeout(() => {
          if (!this.audio.isPlayingQueue && this.vortex.currentState === 'THINKING') {
            this.vortex.setState('IDLE', 'Prêt à répondre');
            if (this.modalVortex) this.modalVortex.setState('IDLE', 'Prêt à répondre');
            document.body.dataset.state = 'idle';
          }
        }, 500);
      },
      onError: (err) => {
        this.updateAssistantMessage(messageNode, "Désolé, une erreur de connexion est survenue. Vérifie la connexion du boîtier ou réessaie dans un instant.", true, true);
        this.vortex.setState('IDLE', 'Prêt à répondre');
        if (this.modalVortex) this.modalVortex.setState('IDLE', 'Prêt à répondre');
        document.body.dataset.state = 'idle';
      }
    });

    if (!streamSuccess) {
      this.updateAssistantMessage(messageNode, "Désolé, impossible de contacter le moteur pédagogique. Le boîtier réessaie...", true, true);
    }
  }

  appendMessage({ role, text, source }) {
    if (this.conversationEmpty) this.conversationEmpty.hidden = true;
    if (this.modalEmpty) this.modalEmpty.hidden = true;

    this.thread.push({ role, text, source });

    if (role === 'user') {
      const li = document.createElement('li');
      li.className = 'msg msg--student';
      li.innerHTML = `
        <span class="msg__label">Ta question</span>
        <div>${this.escapeHTML(text)}</div>
      `;
      if (this.conversationThread) this.conversationThread.appendChild(li);

      // Duplication dans la boîte de dialogue avatar modal
      const modalLi = li.cloneNode(true);
      if (this.avatarTranscription) this.avatarTranscription.appendChild(modalLi);
    }

    this.scrollToBottom();
  }

  createAssistantMessagePlaceholder() {
    if (this.conversationEmpty) this.conversationEmpty.hidden = true;
    if (this.modalEmpty) this.modalEmpty.hidden = true;

    const li = document.createElement('li');
    li.className = 'msg msg--tutor';
    li.innerHTML = `
      <div class="msg__avatar" aria-hidden="true">
        <img src="assets/Alternia.svg" alt="">
      </div>
      <div class="msg__card">
        <span class="msg__label">${this.escapeHTML(this.activeAvatar?.nom || 'AlternIA')}</span>
        <div class="prose msg__body">
          <span class="typing">
            <span class="typing__dots"><i></i><i></i><i></i></span>
            <span>Recherche dans les manuels officiels…</span>
          </span>
        </div>
        <div class="msg__source-wrap" hidden></div>
      </div>
    `;

    if (this.conversationThread) this.conversationThread.appendChild(li);

    const modalLi = li.cloneNode(true);
    if (this.avatarTranscription) this.avatarTranscription.appendChild(modalLi);

    this.scrollToBottom();

    return {
      main: li,
      modal: modalLi,
      mainBody: li.querySelector('.msg__body'),
      modalBody: modalLi.querySelector('.msg__body'),
      mainSource: li.querySelector('.msg__source-wrap'),
      modalSource: modalLi.querySelector('.msg__source-wrap')
    };
  }

  updateAssistantMessage(messageNode, markdownText, isFinal = false, isError = false) {
    if (!messageNode) return;
    const formatted = this.formatMarkdownText(markdownText);

    if (messageNode.mainBody) {
      messageNode.mainBody.innerHTML = formatted;
      this.katex.renderFormulasInElement(messageNode.mainBody);
    }
    if (messageNode.modalBody) {
      messageNode.modalBody.innerHTML = formatted;
      this.katex.renderFormulasInElement(messageNode.modalBody);
    }

    if (isError) {
      messageNode.main?.classList.add('msg--error');
      messageNode.modal?.classList.add('msg--error');
    }

    this.scrollToBottom();
  }

  setAssistantSource(messageNode, sourceDoc) {
    if (!messageNode || !sourceDoc) return;
    const badgeHTML = `
      <span class="msg__source">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 4h6a4 4 0 0 1 4 4v12a3 3 0 0 0-3-3H2z"/><path d="M22 4h-6a4 4 0 0 0-4 4v12a3 3 0 0 1 3-3h7z"/></svg>
        <span>${this.escapeHTML(sourceDoc)}</span>
      </span>
    `;
    if (messageNode.mainSource) {
      messageNode.mainSource.hidden = false;
      messageNode.mainSource.innerHTML = badgeHTML;
    }
    if (messageNode.modalSource) {
      messageNode.modalSource.hidden = false;
      messageNode.modalSource.innerHTML = badgeHTML;
    }
  }

  scrollToBottom() {
    if (this.speechContentArea) {
      this.speechContentArea.scrollTop = this.speechContentArea.scrollHeight;
    }
    if (this.modalTranscriptScroll) {
      this.modalTranscriptScroll.scrollTop = this.modalTranscriptScroll.scrollHeight;
    }
  }

  /* -------------------------------------------------------------------------
     10. FORMATAGE & UTILITAIRES
     ------------------------------------------------------------------------- */
  formatMarkdownText(text) {
    if (!text) return '';
    return text
      // Gras & italique
      .replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Titres simples
      .replace(/^### (.*$)/gim, '<h4>$1</h4>')
      .replace(/^## (.*$)/gim, '<h4>$1</h4>')
      // Puces simples
      .replace(/^\s*[-•]\s+(.*$)/gim, '<li>$1</li>')
      .replace(/(<li>[\s\S]*?<\/li>)/gim, '<ul>$1</ul>')
      // Sauts de ligne
      .replace(/\n\n+/g, '</p><p>')
      .replace(/\n/g, '<br>')
      .replace(/^/, '<p>')
      .replace(/$/, '</p>')
      .replace(/<p><\/p>/g, '')
      .replace(/<p><h4/g, '<h4')
      .replace(/<\/h4><\/p>/g, '</h4>')
      .replace(/<p><ul/g, '<ul')
      .replace(/<\/ul><\/p>/g, '</ul>');
  }

  escapeHTML(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  escapeAttr(str) {
    if (!str) return '';
    return str.replace(/"/g, '&quot;');
  }
}

// Initialisation globale
document.addEventListener('DOMContentLoaded', () => {
  window.alternia = new AlternIAApp();
});
