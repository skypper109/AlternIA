/**
 * AlternIA Device Interface - Kiosk Engine
 * Interface tactile interactive avec AlternIA Core réactif (Vortex 60 FPS),
 * sélecteur de classe/matière (Lycée Malien), rendu KaTeX et synthèse vocale intelligente.
 */

// =============================================================================
// CONFIGURATION ET DONNÉES CURRICULAIRES
// =============================================================================

const API_BASE_URL = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
  ? 'http://localhost:8000'
  : window.location.origin;

const CURRICULUM_DATA = {
  classes: [
    {
      id: "10eme",
      name: "10ème Année",
      badge: "Tronc Commun",
      description: "Fondations scientifiques et littéraires",
      series: ["10ème Commune", "10ème Technique"],
      subjects: [
        { id: "mathematiques", name: "Mathématiques", icon: "📐" },
        { id: "physique", name: "Physique", icon: "⚡" },
        { id: "chimie", name: "Chimie", icon: "🧪" },
        { id: "francais", name: "Français", icon: "📚" },
        { id: "histoire_geo", name: "Histoire-Géo", icon: "🌍" },
        { id: "anglais", name: "Anglais", icon: "🇬🇧" }
      ],
      topics: {
        mathematiques: ["Équations du 1er degré", "Théorème de Thalès", "Trigonométrie de base", "Statistiques"],
        physique: ["Mouvement rectiligne", "Masse et Poids", "Forces et Équilibre", "Courant électrique"],
        chimie: ["Matière et Atomes", "Réactions chimiques", "L'eau et l'air", "Combustion"],
        francais: ["Grammaire & Syntaxe", "Analyse de texte", "Figures de style"]
      }
    },
    {
      id: "11eme",
      name: "11ème Année",
      badge: "Spécialisation",
      description: "Sciences, Lettres ou Économie",
      series: ["11ème Sciences (11è S)", "11ème Lettres (11è L)", "11ème Sciences Économiques (11è SECO)"],
      subjects: [
        { id: "mathematiques", name: "Mathématiques", icon: "📐" },
        { id: "physique", name: "Physique", icon: "⚡" },
        { id: "chimie", name: "Chimie", icon: "🧪" },
        { id: "biologie", name: "Biologie / SVT", icon: "🧬" },
        { id: "francais", name: "Français", icon: "📚" },
        { id: "histoire_geo", name: "Histoire-Géo", icon: "🌍" },
        { id: "anglais", name: "Anglais", icon: "🇬🇧" }
      ],
      topics: {
        mathematiques: ["Polynômes du 2nd degré", "Fonctions numériques", "Vecteurs et Barycentres", "Suites arithmétiques"],
        physique: ["Travail et Énergie", "Optique géométrique", "Loi d'Ohm & Circuits", "Calorimétrie"],
        chimie: ["Chimie organique (Alcanes)", "Oxydoréduction", "Concentration molaire", "Solutions aqueuses"],
        biologie: ["Génétique élémentaire", "Cellule vivante", "Écosystèmes du Sahel"]
      }
    },
    {
      id: "12eme",
      name: "12ème (Terminale)",
      badge: "Baccalauréat",
      description: "Programme officiel Baccalauréat Malien",
      series: [
        "12ème TSE (Sciences Exactes)",
        "12ème TSExp (Sciences Expérimentales)",
        "12ème TSECO (Sciences Économiques)",
        "12ème TSS (Sciences Sociales)",
        "12ème TLL (Langues & Littérature)"
      ],
      subjects: [
        { id: "mathematiques", name: "Mathématiques", icon: "📐" },
        { id: "physique", name: "Physique", icon: "⚡" },
        { id: "chimie", name: "Chimie", icon: "🧪" },
        { id: "philosophie", name: "Philosophie", icon: "🏛️" },
        { id: "biologie", name: "Biologie / SVT", icon: "🧬" },
        { id: "histoire_geo", name: "Histoire-Géo", icon: "🌍" },
        { id: "francais", name: "Littérature", icon: "📚" }
      ],
      topics: {
        mathematiques: [
          "Nombres Complexes (Formule d'Euler & Moivre)",
          "Équations Différentielles (y' + ay = 0)",
          "Fonctions Logarithme Népérien & Exponentielle",
          "Calcul Intégral & Primitives",
          "Probabilités conditionnelles"
        ],
        physique: [
          "Lois de Newton (F = m.a)",
          "Mouvement dans un champ gravitationnel",
          "Circuit RLC & Oscillations électriques",
          "Noyau atomique et Radioactivité",
          "Condensateur et Bobine inductive"
        ],
        chimie: [
          "Couples Acides-Bases & pH = -log[H3O+]",
          "Estérification et Saponification",
          "Alcools, Aldéhydes et Cétones",
          "Solutions Tampons et Dosages"
        ],
        philosophie: [
          "La Conscience et l'Inconscient",
          "La Liberté et le Déterminisme",
          "La Science et la Vérité",
          "La Société et l'État"
        ]
      }
    }
  ]
};

// Base de connaissances locale de secours pour fonctionnement immédiat 100% autonome
const KNOWLEDGE_FALLBACK = {
  "formule de moivre": {
    text: "La formule de De Moivre permet d'élever un nombre complexe sous forme trigonométrique à une puissance entière n. Pour tout réel θ et tout entier relatif n :",
    formula: "(\\cos \\theta + i \\sin \\theta)^n = \\cos(n\\theta) + i \\sin(n\\theta)",
    formulaSpeech: "Voici la formule en question : cosinus de thêta plus i sinus de thêta, le tout à la puissance n, est égal à cosinus de n thêta plus i sinus de n thêta.",
    variables: [
      { name: "θ", desc: "Argument du nombre complexe (en radians)" },
      { name: "n", desc: "Entier relatif (exposant de la puissance)" },
      { name: "i", desc: "Unité imaginaire pure telle que i² = -1" }
    ],
    source: "Manuel Mathématiques 12ème TSE - Chapitre 1 Nombres Complexes",
    followup: "Veux-tu un exemple d'application pour calculer cos(3θ) ou résoudre une équation ?"
  },
  "nombres complexes": {
    text: "En classe de 12ème TSE/TSExp, un nombre complexe s'écrit sous forme algébrique z = a + ib, ou sous forme trigonométrique et exponentielle :",
    formula: "z = a + i b = r (\\cos \\theta + i \\sin \\theta) = r e^{i\\theta}",
    formulaSpeech: "Voici la formule en question : z est égal à a plus i b, qui s'écrit aussi r facteur de cosinus thêta plus i sinus thêta, ou encore r exponentielle de i thêta.",
    variables: [
      { name: "a", desc: "Partie réelle Re(z)" },
      { name: "b", desc: "Partie imaginaire Im(z)" },
      { name: "r", desc: "Module |z| = √(a² + b²)" },
      { name: "θ", desc: "Argument de z" }
    ],
    source: "Manuel Mathématiques 12ème TSE/TSExp",
    followup: "Souhaites-tu passer de la forme algébrique à la forme exponentielle avec un exercice ?"
  },
  "loi de newton": {
    text: "La deuxième loi de Newton (principe fondamental de la dynamique) stipule que la somme vectorielle des forces extérieures appliquées à un solide est égale au produit de sa masse par l'accélération de son centre d'inertie :",
    formula: "\\sum \\vec{F}_{ext} = m \\cdot \\vec{a}_G = m \\cdot \\frac{d\\vec{v}}{dt}",
    formulaSpeech: "Voici la formule en question : la somme des forces extérieures est égale à la masse multipliée par l'accélération.",
    variables: [
      { name: "ΣF", desc: "Somme des forces en Newtons (N)" },
      { name: "m", desc: "Masse du solide en kilogrammes (kg)" },
      { name: "a_G", desc: "Accélération du centre d'inertie en m/s²" },
      { name: "v", desc: "Vitesse instantanée en m/s" }
    ],
    source: "Manuel Physique 12ème TSE - Chapitre Lois de Newton",
    followup: "Veux-tu voir l'application sur un plan incliné ou lors d'une chute libre ?"
  },
  "acide base": {
    text: "En chimie de Terminale, le potentiel hydrogène (pH) d'une solution aqueuse diluée est défini en fonction de la concentration en ions oxonium [H₃O⁺] :",
    formula: "pH = -\\log_{10}[H_3O^+] \\iff [H_3O^+] = 10^{-pH}",
    formulaSpeech: "Voici la formule en question : le pH est égal à moins le logarithme décimal de la concentration en ions H3O+.",
    variables: [
      { name: "pH", desc: "Potentiel Hydrogène (sans unité, entre 0 et 14)" },
      { name: "[H₃O⁺]", desc: "Concentration molaire en ions oxonium (en mol/L)" }
    ],
    source: "Manuel Chimie 12ème TSE/TSExp - Solutions Aqueuses",
    followup: "Souhaites-tu calculer le pH d'un acide fort comme HCl ou d'un acide faible ?"
  },
  "energie cinetique": {
    text: "L'énergie cinétique d'un solide en mouvement de translation est proportionnelle à sa masse et au carré de sa vitesse :",
    formula: "E_c = \\frac{1}{2} m v^2",
    formulaSpeech: "Voici la formule en question : l'énergie cinétique est égale à un demi de la masse multipliée par le carré de la vitesse.",
    variables: [
      { name: "Ec", desc: "Énergie cinétique en Joules (J)" },
      { name: "m", desc: "Masse en kilogrammes (kg)" },
      { name: "v", desc: "Vitesse en mètres par seconde (m/s)" }
    ],
    source: "Manuel Physique 11ème & 12ème",
    followup: "Veux-tu énoncer le théorème de l'énergie cinétique (ΔEc = ΣW) ?"
  }
};

// =============================================================================
// GESTIONNAIRE D'ÉTAT DE L'APPLICATION
// =============================================================================

class AlternIAApp {
  constructor() {
    this.state = 'IDLE'; // IDLE, LISTENING, THINKING, SPEAKING
    this.currentClass = '12eme';
    this.currentSubject = 'mathematiques';
    this.sessionId = 'kiosk_session_' + Date.now();
    this.speechSynthesis = window.speechSynthesis;
    this.recognition = null;
    this.isRecording = false;
    this.audioCtx = null;
    this.isAudioMuted = false;
    this.speechRate = 1.0;
    this.messages = [];

    // File d'attente audio pour streaming TTS en temps réel
    this.audioQueue = [];
    this.isPlayingAudioQueue = false;
    this.currentAudioPlayer = null;

    this.initElements();
    this.initCurriculumUI();
    this.initSpeechRecognition();
    this.initAudioContext();
    this.bindEvents();
    this.checkBackendHealth();
    this.renderInitialWelcome();
  }

  // Sélecteurs DOM
  initElements() {
    this.vortexContainer = document.getElementById('alternia-core');
    this.statusPill = document.getElementById('status-pill');
    this.statusDot = document.getElementById('status-dot');
    this.statusText = document.getElementById('status-text');
    this.audioWaveVisualizer = document.getElementById('audio-visualizer');
    this.classSelectorContainer = document.getElementById('class-selector-tabs');
    this.subjectSelectorContainer = document.getElementById('subject-selector-tabs');
    this.topicChipsContainer = document.getElementById('topic-chips-container');
    this.chatMessagesList = document.getElementById('chat-messages-list');
    this.questionInput = document.getElementById('question-input');
    this.sendBtn = document.getElementById('btn-send');
    this.micBtn = document.getElementById('btn-mic-main');
    this.activeClassLabel = document.getElementById('active-class-label');
    this.activeSubjectLabel = document.getElementById('active-subject-label');
    this.ragStatusBadge = document.getElementById('rag-status-badge');
    this.btnReset = document.getElementById('btn-reset-session');
    this.btnMute = document.getElementById('btn-toggle-mute');
    this.btnFullscreen = document.getElementById('btn-fullscreen');
    this.formulaModal = document.getElementById('formula-modal');
  }

  // Initialisation UI Curriculum
  initCurriculumUI() {
    // Classes
    this.classSelectorContainer.innerHTML = '';
    CURRICULUM_DATA.classes.forEach(c => {
      const btn = document.createElement('button');
      btn.className = `pill-tab touch-btn ${c.id === this.currentClass ? 'active' : ''}`;
      btn.textContent = `${c.name} (${c.badge})`;
      btn.onclick = () => this.selectClass(c.id);
      this.classSelectorContainer.appendChild(btn);
    });

    this.renderSubjects();
    this.renderTopicChips();
    this.updateBadges();
  }

  selectClass(classId) {
    this.currentClass = classId;
    this.initCurriculumUI();
    this.addSystemNotification(`Classe changée en : ${this.getSelectedClassObj().name}`);
  }

  renderSubjects() {
    const classObj = this.getSelectedClassObj();
    this.subjectSelectorContainer.innerHTML = '';

    classObj.subjects.forEach(s => {
      const btn = document.createElement('button');
      btn.className = `pill-tab touch-btn ${s.id === this.currentSubject ? 'active' : ''}`;
      btn.innerHTML = `<span>${s.icon}</span> <span>${s.name}</span>`;
      btn.onclick = () => this.selectSubject(s.id);
      this.subjectSelectorContainer.appendChild(btn);
    });
  }

  selectSubject(subjectId) {
    this.currentSubject = subjectId;
    this.renderSubjects();
    this.renderTopicChips();
    this.updateBadges();
  }

  renderTopicChips() {
    const classObj = this.getSelectedClassObj();
    const topics = (classObj.topics && classObj.topics[this.currentSubject]) || [
      "Explique-moi ce chapitre",
      "Donne-moi la formule clé",
      "Propose-moi un exercice type Bac",
      "Comment résoudre ce problème ?"
    ];

    this.topicChipsContainer.innerHTML = '';
    topics.forEach(topic => {
      const chip = document.createElement('button');
      chip.className = 'touch-btn text-xs bg-slate-800/80 hover:bg-cyan-950/60 border border-slate-700/60 text-slate-200 px-3 py-1.5 rounded-full transition-all';
      chip.textContent = topic;
      chip.onclick = () => this.askQuestion(topic);
      this.topicChipsContainer.appendChild(chip);
    });
  }

  getSelectedClassObj() {
    return CURRICULUM_DATA.classes.find(c => c.id === this.currentClass) || CURRICULUM_DATA.classes[2];
  }

  getSelectedSubjectObj() {
    const classObj = this.getSelectedClassObj();
    return classObj.subjects.find(s => s.id === this.currentSubject) || { name: this.currentSubject, icon: "📖" };
  }

  updateBadges() {
    const classObj = this.getSelectedClassObj();
    const subjectObj = this.getSelectedSubjectObj();

    if (this.activeClassLabel) {
      this.activeClassLabel.textContent = `${classObj.name}`;
    }
    if (this.activeSubjectLabel) {
      this.activeSubjectLabel.textContent = `${subjectObj.icon} ${subjectObj.name}`;
    }
  }

  // ===========================================================================
  // MACHINE D'ÉTATS D'ALTERNIA CORE (VORTEX 60 FPS)
  // ===========================================================================

  setState(newState, statusMessage = null) {
    this.state = newState;
    const core = document.getElementById('alternia-core-wrapper');
    if (!core) return;

    // Supprime les anciennes classes d'état
    core.classList.remove('state-idle', 'state-listening', 'state-thinking', 'state-speaking');

    // Applique le nouvel état
    switch (newState) {
      case 'IDLE':
        core.classList.add('state-idle');
        this.updateStatusBadge('Prêt', 'status-dot', 'bg-emerald-500');
        this.setVisualizerActive(false);
        break;

      case 'LISTENING':
        core.classList.add('state-listening');
        this.updateStatusBadge(statusMessage || 'Écoute de l’élève...', 'status-dot listening', 'bg-cyan-400 animate-pulse');
        this.setVisualizerActive(true);
        this.playBeep(440, 0.1);
        break;

      case 'THINKING':
        core.classList.add('state-thinking');
        this.updateStatusBadge(statusMessage || 'Réflexion & RAG local...', 'status-dot thinking', 'bg-amber-500 animate-spin');
        this.setVisualizerActive(false);
        break;

      case 'SPEAKING':
        core.classList.add('state-speaking');
        this.updateStatusBadge(statusMessage || 'ALTA répond...', 'status-dot speaking', 'bg-purple-400');
        this.setVisualizerActive(true);
        break;
    }
  }

  updateStatusBadge(text, dotClass, tailwindBg) {
    if (this.statusText) this.statusText.textContent = text;
    if (this.statusDot) {
      this.statusDot.className = dotClass;
    }
  }

  setVisualizerActive(active) {
    if (!this.audioWaveVisualizer) return;
    this.audioWaveVisualizer.style.opacity = active ? '1' : '0.2';
  }

  // ===========================================================================
  // RECONNAISSANCE VOCALE (Speech-To-Text)
  // ===========================================================================

  initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.lang = 'fr-FR';
      this.recognition.continuous = false;
      this.recognition.interimResults = true;

      this.recognition.onstart = () => {
        this.isRecording = true;
        this.micBtn.classList.add('is-recording');
        this.setState('LISTENING');
      };

      this.recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
        }
        if (this.questionInput) {
          this.questionInput.value = transcript;
        }
      };

      this.recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        this.stopRecording();
      };

      this.recognition.onend = () => {
        this.stopRecording();
        if (this.questionInput && this.questionInput.value.trim().length > 0) {
          this.submitQuestion();
        } else {
          this.setState('IDLE');
        }
      };
    } else {
      console.warn("Reconnaissance vocale Web Speech API non supportée sur ce navigateur.");
    }
  }

  toggleRecording() {
    if (!this.recognition) {
      // Simulation pour environnement sans microphone matériel
      this.simulateVoiceInput();
      return;
    }

    if (this.isRecording) {
      this.recognition.stop();
      this.stopRecording();
    } else {
      try {
        this.questionInput.value = '';
        this.recognition.start();
      } catch (err) {
        console.error(err);
        this.simulateVoiceInput();
      }
    }
  }

  stopRecording() {
    this.isRecording = false;
    if (this.micBtn) this.micBtn.classList.remove('is-recording');
  }

  simulateVoiceInput() {
    this.setState('LISTENING', 'Parlez maintenant (Simulation)...');
    if (this.micBtn) this.micBtn.classList.add('is-recording');

    setTimeout(() => {
      const sampleQueries = [
        "Donne-moi la formule de Moivre pour les nombres complexes",
        "Quelle est la deuxième loi de Newton en physique ?",
        "Comment calcule-t-on le pH d'une solution d'acide chlorhydrique ?",
        "Explique-moi la formule de l'énergie cinétique"
      ];
      const query = sampleQueries[Math.floor(Math.random() * sampleQueries.length)];
      if (this.questionInput) this.questionInput.value = query;
      this.stopRecording();
      this.submitQuestion();
    }, 1800);
  }

  // ===========================================================================
  // SYNTHÈSE VOCALE STREAMÉE AVEC PRÉ-CHARGEMENT (Zero latency gap)
  // ===========================================================================

  stopAudio() {
    if (this.currentAudioPlayer) {
      this.currentAudioPlayer.pause();
      this.currentAudioPlayer = null;
    }
    if (this.speechSynthesis) {
      this.speechSynthesis.cancel();
    }
    this.audioQueue = [];
    this.isPlayingAudioQueue = false;
    if (this.state === 'SPEAKING') {
      this.setState('IDLE');
    }
  }

  cleanTextForTTS(text) {
    return text
      .replace(/\\\[[\s\S]*?\\\]/g, "la formule affichée")
      .replace(/\\\(.*?\\\)/g, "la formule")
      .replace(/\$\$.*?\$\$/g, "la formule :")
      .replace(/\$.*?\$/g, "")
      .replace(/[#*`_]/g, '')
      .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, "$1 sur $2")
      .replace(/\\sqrt\{([^}]+)\}/g, "racine carrée de $1")
      .replace(/\s+/g, ' ')
      .trim();
  }

  async fetchTTSBlob(text) {
    try {
      const res = await fetch(`${API_BASE_URL}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text, voice: 'vivienne' })
      });
      if (res.ok) {
        return await res.blob();
      }
    } catch (e) {
      console.warn("TTS Backend indisponible, bascule fallback local.");
    }
    return null;
  }

  enqueueSpeechSentence(sentence) {
    if (this.isAudioMuted || !sentence) return;
    const cleanText = this.cleanTextForTTS(sentence);
    if (cleanText.length < 2) return;

    // Pré-téléchargement immédiat en tâche de fond pour enchaînement sans aucune coupure
    const audioPromise = this.fetchTTSBlob(cleanText);
    this.audioQueue.push({ text: cleanText, audioPromise });
    this.processAudioQueue();
  }

  async processAudioQueue() {
    if (this.isPlayingAudioQueue || this.audioQueue.length === 0 || this.isAudioMuted) {
      return;
    }

    this.isPlayingAudioQueue = true;
    this.setState('SPEAKING');

    while (this.audioQueue.length > 0 && !this.isAudioMuted) {
      const item = this.audioQueue.shift();
      try {
        const audioBlob = await item.audioPromise;
        if (audioBlob) {
          const audioUrl = URL.createObjectURL(audioBlob);
          const player = new Audio(audioUrl);
          this.currentAudioPlayer = player;

          await new Promise((resolve) => {
            player.onended = () => {
              URL.revokeObjectURL(audioUrl);
              this.currentAudioPlayer = null;
              resolve();
            };
            player.onerror = () => {
              URL.revokeObjectURL(audioUrl);
              this.currentAudioPlayer = null;
              resolve();
            };
            player.play().catch(() => resolve());
          });
        } else if (this.speechSynthesis) {
          // Fallback Web Speech API
          await this.speakWithWebSpeech(item.text);
        }
      } catch (err) {
        console.warn("Erreur de lecture audio :", err);
      }
    }

    this.isPlayingAudioQueue = false;
    if (this.state === 'SPEAKING') {
      this.setState('IDLE');
    }
  }

  async speakWithWebSpeech(text) {
    if (!this.speechSynthesis || this.isAudioMuted || !text) return;
    return new Promise((resolve) => {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'fr-FR';
      utterance.rate = 1.0;
      const voices = this.speechSynthesis.getVoices();
      const frVoice = voices.find(v => v.lang.startsWith('fr') && (v.name.includes('Denise') || v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Thomas')));
      if (frVoice) utterance.voice = frVoice;

      utterance.onend = resolve;
      utterance.onerror = resolve;
      this.speechSynthesis.speak(utterance);
    });
  }

  speakText(fullText, formulaSpeech = null) {
    this.stopAudio();
    this.enqueueSpeechSentence(formulaSpeech || fullText);
  }

  // ===========================================================================
  // EXTRACTION ET RENDU KATEX DES FORMULES
  // ===========================================================================

  extractAndFormatFormula(text) {
    // Détection de motifs LaTeX standards
    const displayMathRegex = /\$\$([\s\S]*?)\$\$|\\\[([\s\S]*?)\\\]/;
    const inlineMathRegex = /\$([^\$]+)\$|\\\((.*?)\\\)/;

    let mathMatch = text.match(displayMathRegex);
    let formulaLaTeX = null;

    if (mathMatch) {
      formulaLaTeX = mathMatch[1] || mathMatch[2];
    } else {
      const inlineMatch = text.match(inlineMathRegex);
      if (inlineMatch && (inlineMatch[1] || inlineMatch[2]).length > 4) {
        formulaLaTeX = inlineMatch[1] || inlineMatch[2];
      }
    }

    return formulaLaTeX ? formulaLaTeX.trim() : null;
  }

  renderKaTeXFormulaCard(formulaLaTeX, variables = [], sourceDoc = null) {
    const card = document.createElement('div');
    card.className = 'formula-spotlight-card animate-fade-in';

    let varsHtml = '';
    if (variables && variables.length > 0) {
      varsHtml = `
        <div class="formula-variables-grid">
          ${variables.map(v => `<div class="variable-chip"><strong>${v.name}</strong>: <span>${v.desc}</span></div>`).join('')}
        </div>
      `;
    }

    card.innerHTML = `
      <div class="flex items-center justify-between mb-2">
        <div class="formula-badge">
          <span>⚡ Formule Pédagogique Clé</span>
        </div>
        <button class="touch-btn text-xs bg-cyan-900/40 hover:bg-cyan-800/60 text-cyan-300 px-2.5 py-1 rounded-lg border border-cyan-500/30 flex items-center gap-1 btn-zoom-formula">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>
          <span>Plein Écran</span>
        </button>
      </div>

      <div class="formula-math-display" id="math-target-${Date.now()}"></div>
      ${varsHtml}
      ${sourceDoc ? `<div class="text-[11px] text-slate-400 mt-2 flex items-center gap-1"><span>📖 Source :</span> <span class="text-cyan-400 font-medium">${sourceDoc}</span></div>` : ''}
    `;

    const mathTarget = card.querySelector('.formula-math-display');
    try {
      if (window.katex) {
        window.katex.render(formulaLaTeX, mathTarget, {
          displayMode: true,
          throwOnError: false
        });
      } else {
        mathTarget.textContent = formulaLaTeX;
      }
    } catch (e) {
      mathTarget.textContent = formulaLaTeX;
    }

    // Gestion zoom plein écran
    const zoomBtn = card.querySelector('.btn-zoom-formula');
    if (zoomBtn) {
      zoomBtn.onclick = () => this.openFormulaModal(formulaLaTeX, variables, sourceDoc);
    }

    return card;
  }

  openFormulaModal(formulaLaTeX, variables, sourceDoc) {
    if (!this.formulaModal) return;
    const modalContent = document.getElementById('formula-modal-math');
    const modalVars = document.getElementById('formula-modal-vars');
    const modalSource = document.getElementById('formula-modal-source');

    if (window.katex) {
      window.katex.render(formulaLaTeX, modalContent, { displayMode: true, throwOnError: false });
    } else {
      modalContent.textContent = formulaLaTeX;
    }

    if (modalVars) {
      modalVars.innerHTML = variables && variables.length > 0
        ? variables.map(v => `<div class="variable-chip text-sm p-2"><strong>${v.name}</strong> : ${v.desc}</div>`).join('')
        : '';
    }

    if (modalSource && sourceDoc) {
      modalSource.textContent = `Document officiel : ${sourceDoc}`;
    }

    this.formulaModal.classList.remove('hidden');
  }

  closeFormulaModal() {
    if (this.formulaModal) {
      this.formulaModal.classList.add('hidden');
    }
  }

  // ===========================================================================
  // LOGIQUE DE QUESTION & RÉPONSE (API RAG + FALLBACK LOCAL)
  // ===========================================================================

  askQuestion(questionText) {
    if (!questionText || questionText.trim().length === 0) return;
    if (this.questionInput) this.questionInput.value = questionText;
    this.submitQuestion();
  }

  async submitQuestion() {
    const question = this.questionInput ? this.questionInput.value.trim() : '';
    if (!question) return;

    this.questionInput.value = '';
    this.stopAudio();
    this.appendUserMessage(question);
    this.setState('THINKING', 'Consultation du programme malien...');

    // Créer immédiatement le conteneur de message assistant avec animation de streaming
    const streamingMessage = this.createStreamingAIMessage();

    let currentFullText = "";
    let sentenceBuffer = "";
    let firstChunkSent = false;
    const clauseDelimiter = /([,;:\.!?…]\s+|\n+)/;
    const sentenceDelimiter = /([\.!?…]\s+|\n+)/;
    let streamSucceeded = false;
    let sources = [];

    try {
      // Appel SSE streaming vers le backend FastAPI local
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question,
          student_class: this.currentClass,
          subject: this.currentSubject,
          session_id: this.sessionId,
          enable_rag: true
        })
      });

      if (response.ok && response.body) {
        streamSucceeded = true;
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        let isFirstChunk = true;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith('data:')) continue;
            const dataStr = trimmed.replace(/^data:\s*/, '');
            if (!dataStr) continue;

            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.chunk) {
                if (isFirstChunk) {
                  isFirstChunk = false;
                  this.setState('SPEAKING', 'ALTA explique en direct...');
                }
                currentFullText += parsed.chunk;
                streamingMessage.updateText(currentFullText);

                // Découpage et synthèse vocale immédiate (< 1s au premier segment)
                sentenceBuffer += parsed.chunk;

                if (!firstChunkSent) {
                  const words = sentenceBuffer.trim().split(/\s+/);
                  const match = clauseDelimiter.exec(sentenceBuffer);
                  if (match || words.length >= 6) {
                    const splitPos = match ? match.index + match[0].length : sentenceBuffer.length;
                    const firstSentence = sentenceBuffer.substring(0, splitPos).trim();
                    sentenceBuffer = sentenceBuffer.substring(splitPos);
                    if (firstSentence.length > 2) {
                      this.enqueueSpeechSentence(firstSentence);
                      firstChunkSent = true;
                    }
                  }
                } else {
                  while (true) {
                    let match = sentenceDelimiter.exec(sentenceBuffer);
                    if (!match && sentenceBuffer.trim().split(/\s+/).length >= 10) {
                      match = clauseDelimiter.exec(sentenceBuffer);
                    }
                    if (!match) break;
                    const endPos = match.index + match[0].length;
                    const sentence = sentenceBuffer.substring(0, endPos).trim();
                    sentenceBuffer = sentenceBuffer.substring(endPos);
                    if (sentence.length > 2) {
                      this.enqueueSpeechSentence(sentence);
                    }
                  }
                }
              }

              if (parsed.done) {
                sources = parsed.sources || [];
                if (parsed.full_text) {
                  currentFullText = parsed.full_text;
                }
              }
            } catch (jsonErr) {
              console.warn("Erreur parsing SSE chunk:", jsonErr);
            }
          }
        }

        // Émettre la dernière phrase résiduelle pour l'audio
        if (sentenceBuffer.trim().length > 2) {
          this.enqueueSpeechSentence(sentenceBuffer.trim());
        }

        // Finaliser le message avec KaTeX et sources
        streamingMessage.finalize({
          answer: currentFullText,
          sources: sources,
          source: sources.length > 0 ? sources[0].document : null,
          followup: "Veux-tu un exemple d'application ou un exercice type Bac ?"
        });
        return;
      }
    } catch (err) {
      console.warn("Streaming backend non joignable, bascule vers mode hors-ligne :", err);
    }

    if (!streamSucceeded) {
      // Supprimer le conteneur de stream incomplet et basculer vers fallback autonome
      if (streamingMessage && streamingMessage.element) {
        streamingMessage.element.remove();
      }
      this.handleFallbackResponse(question);
    }
  }

  handleFallbackResponse(question) {
    const normalizedQ = question.toLowerCase();
    let localMatchKey = Object.keys(KNOWLEDGE_FALLBACK).find(k => normalizedQ.includes(k));

    if (localMatchKey) {
      const item = KNOWLEDGE_FALLBACK[localMatchKey];
      this.appendAIMessage({
        answer: item.text,
        formula: item.formula,
        formulaSpeech: item.formulaSpeech,
        variables: item.variables,
        source: item.source,
        followup: item.followup
      });
    } else {
      this.appendAIMessage({
        answer: `Pour la classe de **${this.getSelectedClassObj().name}** en **${this.getSelectedSubjectObj().name}** :\n\nVoici les éléments clés pour répondre à ta question sur : *"${question}"*.\n\nAssure-toi de bien identifier les données initiales du problème et d'appliquer la démarche pas à pas conforme au programme du lycée.`,
        source: `Manuel de référence ${this.getSelectedSubjectObj().name} ${this.getSelectedClassObj().name}`,
        followup: "Veux-tu que nous résolvions un exemple concret étape par étape ?"
      });
    }
  }

  createStreamingAIMessage() {
    const div = document.createElement('div');
    div.className = 'flex items-start gap-3 mb-6 animate-fade-in';
    div.innerHTML = `
      <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-700 to-cyan-500 border border-cyan-300 flex items-center justify-center text-white shrink-0 shadow-lg shadow-cyan-900/40">
        <svg class="w-6 h-6" viewBox="0 0 100 100" fill="none">
          <circle cx="50" cy="50" r="45" fill="#0C142B" />
          <path d="M50 15 C75 25 85 50 85 70 C70 60 55 55 45 65 Z" fill="#F26522"/>
          <path d="M85 70 C75 90 50 90 35 75 C45 60 60 60 65 45 Z" fill="#26B7CD"/>
          <path d="M15 60 C15 35 35 20 50 15 C45 30 50 50 65 55 Z" fill="#214392"/>
        </svg>
      </div>
      <div class="chat-bubble-ai max-w-[90%] p-4 text-white flex-1 border border-slate-700/60">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-bold text-cyan-400 tracking-wide uppercase flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            ALTA — Tuteur Intelligent (AlternIA)
          </span>
          <span class="text-[11px] bg-cyan-950/80 text-cyan-300 px-2 py-0.5 rounded border border-cyan-700/50 stream-badge">⚡ En direct</span>
        </div>
        <div class="ai-body-content">
          <div class="text-sm md:text-base text-slate-100 leading-relaxed selectable-text mb-2">
            <span class="streaming-text"></span><span class="typing-cursor"></span>
          </div>
        </div>
        <div class="followup-container"></div>
      </div>
    `;

    this.chatMessagesList.appendChild(div);
    this.scrollToBottom();

    const textSpan = div.querySelector('.streaming-text');
    const cursor = div.querySelector('.typing-cursor');
    const streamBadge = div.querySelector('.stream-badge');
    const bodyContent = div.querySelector('.ai-body-content');
    const followupContainer = div.querySelector('.followup-container');

    return {
      element: div,
      updateText: (fullText) => {
        if (textSpan) textSpan.innerHTML = this.formatMarkdownText(fullText);
        this.scrollToBottom();
      },
      finalize: (payload) => {
        if (cursor) cursor.remove();
        if (payload.source && streamBadge) {
          streamBadge.textContent = `📖 ${payload.source}`;
          streamBadge.className = "text-[11px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700";
        } else if (streamBadge) {
          streamBadge.remove();
        }

        // Extraction et rendu KaTeX si formule présente
        const formulaLaTeX = this.extractAndFormatFormula(payload.answer);
        if (formulaLaTeX) {
          const formulaCard = this.renderKaTeXFormulaCard(formulaLaTeX, [], payload.source);
          bodyContent.appendChild(formulaCard);
        }

        // Relance suggérée
        if (payload.followup) {
          followupContainer.innerHTML = `
            <div class="mt-3 pt-3 border-t border-slate-800">
              <button class="touch-btn text-xs bg-gradient-to-r from-orange-600/20 to-cyan-600/20 hover:from-orange-600/40 hover:to-cyan-600/40 border border-orange-500/40 text-orange-200 px-3 py-1.5 rounded-full flex items-center gap-1.5 btn-followup">
                <span>💡 Question suggérée :</span>
                <span class="font-medium underline">${payload.followup}</span>
              </button>
            </div>
          `;
          const followupBtn = followupContainer.querySelector('.btn-followup');
          if (followupBtn) {
            followupBtn.onclick = () => this.askQuestion(payload.followup);
          }
        }
        this.scrollToBottom();
      }
    };
  }

  // ===========================================================================
  // GESTION DU CHAT & AFFICHAGE
  // ===========================================================================

  appendUserMessage(text) {
    const div = document.createElement('div');
    div.className = 'flex items-start justify-end gap-3 mb-4 animate-fade-in';
    div.innerHTML = `
      <div class="chat-bubble-user max-w-[85%] p-4 text-white">
        <div class="text-xs text-cyan-200 font-semibold mb-1 flex items-center gap-1">
          <span>Élève (${this.getSelectedClassObj().name})</span>
        </div>
        <p class="text-sm md:text-base leading-relaxed selectable-text">${this.escapeHtml(text)}</p>
      </div>
      <div class="w-9 h-9 rounded-full bg-cyan-600/30 border border-cyan-400 flex items-center justify-center text-cyan-300 font-bold text-sm shrink-0">
        É
      </div>
    `;
    this.chatMessagesList.appendChild(div);
    this.scrollToBottom();
  }

  appendAIMessage(payload) {
    const div = document.createElement('div');
    div.className = 'flex items-start gap-3 mb-6 animate-fade-in';

    let contentHtml = `<p class="text-sm md:text-base text-slate-100 leading-relaxed selectable-text mb-2">${this.formatMarkdownText(payload.answer)}</p>`;

    div.innerHTML = `
      <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-700 to-cyan-500 border border-cyan-300 flex items-center justify-center text-white shrink-0 shadow-lg shadow-cyan-900/40">
        <svg class="w-6 h-6" viewBox="0 0 100 100" fill="none">
          <circle cx="50" cy="50" r="45" fill="#0C142B" />
          <path d="M50 15 C75 25 85 50 85 70 C70 60 55 55 45 65 Z" fill="#F26522"/>
          <path d="M85 70 C75 90 50 90 35 75 C45 60 60 60 65 45 Z" fill="#26B7CD"/>
          <path d="M15 60 C15 35 35 20 50 15 C45 30 50 50 65 55 Z" fill="#214392"/>
        </svg>
      </div>
      <div class="chat-bubble-ai max-w-[90%] p-4 text-white flex-1 border border-slate-700/60">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-bold text-cyan-400 tracking-wide uppercase flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-cyan-400"></span>
            ALTA — Tuteur Intelligent (AlternIA)
          </span>
          ${payload.source ? `<span class="text-[11px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700">📖 ${payload.source}</span>` : ''}
        </div>
        <div class="ai-body-content">${contentHtml}</div>
        ${payload.followup ? `
          <div class="mt-3 pt-3 border-t border-slate-800">
            <button class="touch-btn text-xs bg-gradient-to-r from-orange-600/20 to-cyan-600/20 hover:from-orange-600/40 hover:to-cyan-600/40 border border-orange-500/40 text-orange-200 px-3 py-1.5 rounded-full flex items-center gap-1.5 btn-followup">
              <span>💡 Question suggérée :</span>
              <span class="font-medium underline">${payload.followup}</span>
            </button>
          </div>
        ` : ''}
      </div>
    `;

    // Si une formule mathématique est présente, on insère la carte KaTeX dédiée
    if (payload.formula) {
      const bodyContainer = div.querySelector('.ai-body-content');
      const formulaCard = this.renderKaTeXFormulaCard(payload.formula, payload.variables, payload.source);
      bodyContainer.appendChild(formulaCard);
    }

    // Gestion du clic sur le bouton de relance pédagogique
    const followupBtn = div.querySelector('.btn-followup');
    if (followupBtn && payload.followup) {
      followupBtn.onclick = () => this.askQuestion(payload.followup);
    }

    this.chatMessagesList.appendChild(div);
    this.scrollToBottom();

    // Synthèse vocale de la réponse
    this.speakText(payload.answer, payload.formulaSpeech);
  }

  addSystemNotification(text) {
    const div = document.createElement('div');
    div.className = 'text-center my-3 animate-fade-in';
    div.innerHTML = `
      <span class="text-xs bg-slate-800/90 text-cyan-300 border border-cyan-500/30 px-3 py-1 rounded-full shadow">
        ℹ️ ${this.escapeHtml(text)}
      </span>
    `;
    this.chatMessagesList.appendChild(div);
    this.scrollToBottom();
  }

  renderInitialWelcome() {
    const div = document.createElement('div');
    div.className = 'flex items-start gap-3 mb-6 animate-fade-in';
    div.innerHTML = `
      <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-700 to-cyan-500 border border-cyan-300 flex items-center justify-center text-white shrink-0 shadow-lg shadow-cyan-900/40">
        <svg class="w-6 h-6" viewBox="0 0 100 100" fill="none">
          <circle cx="50" cy="50" r="45" fill="#0C142B" />
          <path d="M50 15 C75 25 85 50 85 70 C70 60 55 55 45 65 Z" fill="#F26522"/>
          <path d="M85 70 C75 90 50 90 35 75 C45 60 60 60 65 45 Z" fill="#26B7CD"/>
          <path d="M15 60 C15 35 35 20 50 15 C45 30 50 50 65 55 Z" fill="#214392"/>
        </svg>
      </div>
      <div class="chat-bubble-ai max-w-[92%] p-5 text-white flex-1 border border-slate-700/60 shadow-xl rounded-2xl bg-slate-900/90">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-bold text-cyan-400 tracking-wide uppercase flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
            ALTA — Tuteur Pédagogique Intelligent (AlternIA)
          </span>
          <span class="text-[11px] bg-slate-800 text-cyan-300 px-2.5 py-0.5 rounded-full border border-cyan-500/30">🇲🇱 Programme Officiel Malien</span>
        </div>
        <div class="ai-body-content">
          <p class="text-sm md:text-base text-slate-100 leading-relaxed selectable-text mb-3">
            Bonjour ! Je suis <strong>ALTA</strong>, ton assistant pédagogique personnel. 👋<br>
            Pour que j'adapte mes explications, résolutions et formules scientifiques à ton niveau exact, <strong>choisis ta classe pour commencer</strong> :
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 my-3">
            <button class="btn-select-class-welcome touch-btn p-3.5 rounded-xl border border-cyan-500/40 bg-cyan-950/40 hover:bg-cyan-900/60 text-left transition-all flex flex-col gap-1.5 shadow-md hover:border-cyan-300 hover:scale-[1.02]" data-class="10eme">
              <span class="text-sm font-bold text-cyan-300 flex items-center gap-1.5">📐 10ème Année</span>
              <span class="text-[11px] text-slate-300">Tronc Commun Scientifique & Littéraire</span>
            </button>
            <button class="btn-select-class-welcome touch-btn p-3.5 rounded-xl border border-cyan-500/40 bg-cyan-950/40 hover:bg-cyan-900/60 text-left transition-all flex flex-col gap-1.5 shadow-md hover:border-cyan-300 hover:scale-[1.02]" data-class="11eme">
              <span class="text-sm font-bold text-cyan-300 flex items-center gap-1.5">⚡ 11ème Année</span>
              <span class="text-[11px] text-slate-300">Sciences (S), Lettres (L) ou Économie (SECO)</span>
            </button>
            <button class="btn-select-class-welcome touch-btn p-3.5 rounded-xl border border-orange-500/50 bg-orange-950/40 hover:bg-orange-900/60 text-left transition-all flex flex-col gap-1.5 shadow-md hover:border-orange-400 hover:scale-[1.02]" data-class="12eme">
              <span class="text-sm font-bold text-orange-300 flex items-center gap-1.5">🎓 12ème (Terminale)</span>
              <span class="text-[11px] text-slate-300">Baccalauréat (TSE, TSExp, TSS, TSEco, TLL)</span>
            </button>
          </div>
          <p class="text-xs text-slate-400 italic mt-2">💡 Tu pourras aussi changer de classe et de matière à tout moment en haut de l'écran.</p>
        </div>
      </div>
    `;

    div.querySelectorAll('.btn-select-class-welcome').forEach(btn => {
      btn.onclick = () => {
        const clsId = btn.getAttribute('data-class');
        this.selectClass(clsId);
        const clsObj = this.getSelectedClassObj();
        this.appendAIMessage({
          answer: `Parfait ! Tu es configuré en **${clsObj.name}** (${clsObj.badge}).\n\nChoisis ta matière et pose-moi ta première question par écrit ou au micro ! 🚀`,
          followup: `Quelles sont les formules clés en ${this.getSelectedSubjectObj().name} ?`
        });
      };
    });

    this.chatMessagesList.appendChild(div);
    this.scrollToBottom();

    // Accueil vocal invitant à choisir la classe
    this.speakText("Bonjour ! Je suis ALTA, ton tuteur pédagogique. Choisis ta classe pour commencer !");
  }

  // ===========================================================================
  // BINDINGS & CONTRÔLES TACTILES
  // ===========================================================================

  bindEvents() {
    // Bouton d'envoi textuel
    if (this.sendBtn) {
      this.sendBtn.onclick = () => this.submitQuestion();
    }

    // Touche Entrée
    if (this.questionInput) {
      this.questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.submitQuestion();
        }
      });
    }

    // Bouton Microphone Principal
    if (this.micBtn) {
      this.micBtn.onclick = () => this.toggleRecording();
    }

    // Réinitialiser la session
    if (this.btnReset) {
      this.btnReset.onclick = async () => {
        const oldSessionId = this.sessionId;
        this.chatMessagesList.innerHTML = '';
        this.sessionId = 'kiosk_session_' + Date.now();
        this.stopAudio();
        try {
          await fetch(`${API_BASE_URL}/api/session/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: oldSessionId })
          });
        } catch (e) {
          // ignore
        }
        this.setState('IDLE');
        this.renderInitialWelcome();
        this.addSystemNotification("Session réinitialisée. Nouvelle conversation active.");
      };
    }

    // Mute / Unmute
    if (this.btnMute) {
      this.btnMute.onclick = () => {
        this.isAudioMuted = !this.isAudioMuted;
        if (this.isAudioMuted && this.speechSynthesis) {
          this.speechSynthesis.cancel();
        }
        this.btnMute.innerHTML = this.isAudioMuted
          ? '<svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"></path></svg>'
          : '<svg class="w-5 h-5 text-cyan-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"></path></svg>';
      };
    }

    // Plein écran tactile
    if (this.btnFullscreen) {
      this.btnFullscreen.onclick = () => {
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen().catch(() => {});
        } else {
          document.exitFullscreen().catch(() => {});
        }
      };
    }

    // Modal de formule
    const btnCloseModal = document.getElementById('btn-close-formula-modal');
    if (btnCloseModal) {
      btnCloseModal.onclick = () => this.closeFormulaModal();
    }
  }

  // Audio Context pour SFX
  initAudioContext() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.audioCtx = new AudioCtx();
    } catch (e) {
      console.warn("AudioContext non disponible");
    }
  }

  playBeep(freq = 520, duration = 0.15) {
    if (!this.audioCtx || this.isAudioMuted) return;
    try {
      if (this.audioCtx.state === 'suspended') this.audioCtx.resume();
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, this.audioCtx.currentTime);
      gain.gain.setValueAtTime(0.08, this.audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + duration);
      osc.connect(gain);
      gain.connect(this.audioCtx.destination);
      osc.start();
      osc.stop(this.audioCtx.currentTime + duration);
    } catch (e) {}
  }

  // Vérification de santé du Backend
  async checkBackendHealth() {
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      if (res.ok) {
        const data = await res.json();
        if (this.ragStatusBadge) {
          this.ragStatusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> <span>RAG Local Connecté (${data.rag_chunks_count || 'OK'})</span>`;
          this.ragStatusBadge.className = 'status-pill text-xs text-emerald-300 border-emerald-500/30';
        }
      }
    } catch (e) {
      if (this.ragStatusBadge) {
        this.ragStatusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-amber-400"></span> <span>Mode Embarqué Autonome</span>`;
        this.ragStatusBadge.className = 'status-pill text-xs text-amber-300 border-amber-500/30';
      }
    }
  }

  scrollToBottom() {
    const scrollContainer = document.getElementById('chat-scroll-area');
    if (scrollContainer) {
      scrollContainer.scrollTop = scrollContainer.scrollHeight;
    }
  }

  escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  formatMarkdownText(text) {
    if (!text) return "";
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-slate-800 text-cyan-300 px-1 py-0.5 rounded text-xs">$1</code>')
      .replace(/\n\n/g, '<br/><br/>')
      .replace(/\n/g, '<br/>');
  }
}

// Initialisation au chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
  window.alternia = new AlternIAApp();
});
