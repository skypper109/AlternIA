/**
 * Configuration & Données Curriculaires officielles (Lycée Malien).
 * Module enrichi avec Défis Express du Bac, Badges Gamifiés et Notions Clés tape-à-l'œil.
 */

export const API_BASE_URL = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
  ? 'http://localhost:8000'
  : window.location.origin;

export const CURRICULUM_DATA = {
  classes: [
    {
      id: "10eme",
      name: "10ème Année",
      badge: "Tronc Commun",
      accent: "emerald",
      description: "Fondations scientifiques et littéraires du Lycée Malien",
      series: ["10ème Commune", "10ème Technique"],
      subjects: [
        { id: "mathematiques", name: "Mathématiques", iconType: "math" },
        { id: "physique", name: "Physique", iconType: "physics" },
        { id: "chimie", name: "Chimie", iconType: "chemistry" },
        { id: "francais", name: "Français", iconType: "literature" },
        { id: "histoire_geo", name: "Histoire-Géo", iconType: "history" },
        { id: "anglais", name: "Anglais", iconType: "languages" }
      ],
      topics: {
        mathematiques: [
          { title: "Théorème de Thalès & Démonstration", tag: "Incontournable", type: "orange" },
          { title: "Équations & Inéquations du 1er degré", tag: "Méthode", type: "cyan" },
          { title: "Trigonométrie (Cos, Sin, Tan)", tag: "Formule Clé", type: "purple" },
          { title: "Statistiques & Moyennes pondérées", tag: "Exercice Type", type: "emerald" }
        ],
        physique: [
          { title: "Masse, Poids & Équilibre des forces", tag: "Loi Fondamentale", type: "orange" },
          { title: "Mouvement Rectiligne Uniforme (MRU)", tag: "Cinématique", type: "cyan" },
          { title: "Courant électrique continu & Loi d'Ohm", tag: "Circuits", type: "purple" }
        ],
        chimie: [
          { title: "Structure atomique & Tableau périodique", tag: "Atomes", type: "cyan" },
          { title: "Équilibrer une réaction chimique", tag: "Méthode Express", type: "orange" },
          { title: "Combustions du carbone et bilans", tag: "TP Révision", type: "emerald" }
        ],
        francais: [
          { title: "Figures de style & Procédés littéraires", tag: "Analyse", type: "purple" },
          { title: "Technique de l'Argumentation", tag: "Méthode Épreuve", type: "orange" }
        ]
      },
      featuredChallenges: [
        { title: "Théorème de Thalès", subject: "Mathématiques", badge: "Défi Géométrie", color: "from-blue-600/30 to-cyan-500/20", border: "border-cyan-500/40", query: "Explique-moi le théorème de Thalès et donne un exercice d'application avec solution." },
        { title: "Loi d'Ohm & Circuits", subject: "Physique", badge: "Formule Clé", color: "from-amber-600/30 to-orange-500/20", border: "border-orange-500/40", query: "Énonce la loi d'Ohm U = R.I et explique comment calculer la résistance d'un dipôle." },
        { title: "Équilibrer une réaction", subject: "Chimie", badge: "Quiz Minute", color: "from-emerald-600/30 to-teal-500/20", border: "border-emerald-500/40", query: "Comment équilibrer une équation chimique facilement ? Donne la méthode pas à pas." }
      ]
    },
    {
      id: "11eme",
      name: "11ème Année",
      badge: "Spécialisation",
      accent: "cyan",
      description: "Sciences (11S), Lettres (11L), Sciences Économiques (11SECO)",
      series: ["11ème Sciences (11S)", "11ème Lettres (11L)", "11ème Sciences Économiques (11SECO)"],
      subjects: [
        { id: "mathematiques", name: "Mathématiques", iconType: "math" },
        { id: "physique", name: "Physique", iconType: "physics" },
        { id: "chimie", name: "Chimie", iconType: "chemistry" },
        { id: "biologie", name: "Biologie / SVT", iconType: "biology" },
        { id: "francais", name: "Français", iconType: "literature" },
        { id: "histoire_geo", name: "Histoire-Géo", iconType: "history" },
        { id: "anglais", name: "Anglais", iconType: "languages" }
      ],
      topics: {
        mathematiques: [
          { title: "Polynômes du second degré & Discriminant Δ", tag: "Épreuve Type", type: "orange" },
          { title: "Étude & Dérivation de Fonctions", tag: "Analyse", type: "cyan" },
          { title: "Barycentres & Vecteurs du plan", tag: "Géométrie", type: "purple" },
          { title: "Suites Arithmétiques & Géométriques", tag: "Formule", type: "emerald" }
        ],
        physique: [
          { title: "Travail & Énergie Mécanique (W = F.d)", tag: "Formule Clé", type: "orange" },
          { title: "Optique : Lentilles & Réfraction", tag: "Optique", type: "cyan" },
          { title: "Calorimétrie & Transferts thermiques", tag: "Thermodynamique", type: "purple" }
        ],
        chimie: [
          { title: "Chimie Organique : Alcanes & Alcènes", tag: "Nomenclature", type: "cyan" },
          { title: "Oxydoréduction & Demi-équations", tag: "Méthode", type: "orange" },
          { title: "Concentrations & Solutions aqueuses", tag: "Calculs", type: "emerald" }
        ],
        biologie: [
          { title: "Photosynthèse : Phases claire & sombre", tag: "Bio Végétale", type: "emerald" },
          { title: "Mitose, Méiose & Génétique sahélienne", tag: "Génétique", type: "purple" }
        ]
      },
      featuredChallenges: [
        { title: "Discriminant Δ & Racines", subject: "Maths 11S", badge: "Incontournable", color: "from-cyan-600/30 to-blue-500/20", border: "border-cyan-500/40", query: "Explique le calcul du discriminant delta et donne les trois cas de racines pour un polynôme du second degré." },
        { title: "Énergie Cinétique Ec = ½mv²", subject: "Physique", badge: "Formule Star", color: "from-amber-600/30 to-orange-500/20", border: "border-orange-500/40", query: "Démontre le théorème de l'énergie cinétique et donne un exemple d'application." },
        { title: "Photosynthèse Globale", subject: "SVT", badge: "Défi Bio", color: "from-emerald-600/30 to-teal-500/20", border: "border-emerald-500/40", query: "C'est quoi la photosynthèse de façon simple ? Donne l'équation bilan et les deux phases." }
      ]
    },
    {
      id: "12eme",
      name: "12ème (Terminale)",
      badge: "Baccalauréat",
      accent: "orange",
      description: "Programme Officiel Baccalauréat Malien (TSE, TSExp, TSEco, TSS, TLL)",
      series: [
        "12ème TSE (Sciences Exactes)",
        "12ème TSExp (Sciences Expérimentales)",
        "12ème TSECO (Sciences Économiques)",
        "12ème TSS (Sciences Sociales)",
        "12ème TLL (Langues & Littérature)"
      ],
      subjects: [
        { id: "mathematiques", name: "Mathématiques", iconType: "math" },
        { id: "physique", name: "Physique", iconType: "physics" },
        { id: "chimie", name: "Chimie", iconType: "chemistry" },
        { id: "philosophie", name: "Philosophie", iconType: "philosophy" },
        { id: "biologie", name: "Biologie / SVT", iconType: "biology" },
        { id: "histoire_geo", name: "Histoire-Géo", iconType: "history" },
        { id: "francais", name: "Littérature", iconType: "literature" }
      ],
      topics: {
        mathematiques: [
          { title: "Nombres Complexes : Formule de Moivre", tag: "Bac TSE/TSExp", type: "orange" },
          { title: "Équations Différentielles (y' + ay = 0)", tag: "100% Bac", type: "cyan" },
          { title: "Logarithme népérien (ln) & Exponentielle", tag: "Analyse", type: "purple" },
          { title: "Intégrales, Primitives & Calcul d'aires", tag: "Calcul", type: "emerald" },
          { title: "Probabilités Conditionnelles & Arbres", tag: "Stats", type: "orange" }
        ],
        physique: [
          { title: "Lois de Newton (F = m.a) & Chute libre", tag: "Mécanique", type: "orange" },
          { title: "Circuits RLC, Oscillations & Résonance", tag: "Électricité", type: "cyan" },
          { title: "Radioactivité & Demi-vie nucléaire", tag: "Physique Nu", type: "purple" }
        ],
        chimie: [
          { title: "Couples Acides-Bases, pH & Solutions", tag: "Dosages", type: "cyan" },
          { title: "Estérification, Hydrolyse & Cinétique", tag: "Chimie Org", type: "orange" },
          { title: "Alcools, Aldéhydes & Cétones", tag: "Nomenclature", type: "emerald" }
        ],
        philosophie: [
          { title: "La Conscience, l'Inconscient & le Sujet", tag: "Dissertation", type: "purple" },
          { title: "L'État, la Justice & la Liberté", tag: "Sujet Bac", type: "orange" }
        ]
      },
      featuredChallenges: [
        { title: "Formule de Moivre (Complexes)", subject: "Maths TSE", badge: "Objectif Mention", color: "from-amber-600/35 to-orange-500/20", border: "border-orange-500/50", query: "Donne la formule de De Moivre pour les nombres complexes et montre comment calculer cos(3x)." },
        { title: "Lois de Newton & Dynamique", subject: "Physique TSE", badge: "Grand Classique", color: "from-blue-600/35 to-cyan-500/20", border: "border-cyan-500/50", query: "Énonce la 2ème loi de Newton et explique l'équation du mouvement pour un solide en chute libre." },
        { title: "Acides-Bases & Calcul de pH", subject: "Chimie", badge: "Épreuve Bac", color: "from-purple-600/35 to-indigo-500/20", border: "border-purple-500/50", query: "Donne la définition du pH en fonction de la concentration en H3O+ et la formule d'un dosage acido-basique." },
        { title: "Conscience & Liberté", subject: "Philosophie", badge: "Dissertation", color: "from-emerald-600/35 to-teal-500/20", border: "border-emerald-500/50", query: "Propose un plan détaillé de dissertation sur le sujet : Sommes-nous maîtres de nos pensées ?" }
      ]
    }
  ]
};

// Base locale de secours autonome 100% hors-ligne
export const KNOWLEDGE_FALLBACK = {
  "formule de moivre": {
    text: "La formule de De Moivre permet d'élever un nombre complexe sous forme trigonométrique à une puissance entière n. Pour tout réel θ et tout entier relatif n :",
    formula: "(\\cos \\theta + i \\sin \\theta)^n = \\cos(n\\theta) + i \\sin(n\\theta)",
    formulaSpeech: "Voici la formule : cosinus de thêta plus i sinus de thêta, le tout à la puissance n, est égal à cosinus de n thêta plus i sinus de n thêta.",
    variables: [
      { name: "θ", desc: "Argument du nombre complexe (en radians)" },
      { name: "n", desc: "Entier relatif (exposant)" },
      { name: "i", desc: "Unité imaginaire pure (i² = -1)" }
    ],
    source: "Manuel Mathématiques 12ème TSE - Nombres Complexes",
    followup: "Veux-tu un exemple d'application pour calculer cos(3θ) ?"
  },
  "nombres complexes": {
    text: "En classe de 12ème TSE/TSExp, un nombre complexe s'écrit sous forme algébrique z = a + ib, ou sous forme trigonométrique et exponentielle :",
    formula: "z = a + i b = r (\\cos \\theta + i \\sin \\theta) = r e^{i\\theta}",
    formulaSpeech: "Voici la formule : z est égal à a plus i b, qui s'écrit aussi r facteur de cosinus thêta plus i sinus thêta, ou encore r exponentielle de i thêta.",
    variables: [
      { name: "a", desc: "Partie réelle Re(z)" },
      { name: "b", desc: "Partie imaginaire Im(z)" },
      { name: "r", desc: "Module |z| = √(a² + b²)" },
      { name: "θ", desc: "Argument de z" }
    ],
    source: "Manuel Mathématiques 12ème TSE/TSExp",
    followup: "Souhaites-tu passer de la forme algébrique à la forme exponentielle ?"
  },
  "loi de newton": {
    text: "La deuxième loi de Newton (principe fondamental de la dynamique) stipule que la somme vectorielle des forces extérieures appliquées à un solide est égale au produit de sa masse par l'accélération de son centre d'inertie :",
    formula: "\\sum \\vec{F}_{ext} = m \\cdot \\vec{a}_G = m \\cdot \\frac{d\\vec{v}}{dt}",
    formulaSpeech: "Voici la formule : la somme des forces extérieures est égale à la masse multipliée par l'accélération.",
    variables: [
      { name: "ΣF", desc: "Somme des forces en Newtons (N)" },
      { name: "m", desc: "Masse du solide en kilogrammes (kg)" },
      { name: "a_G", desc: "Accélération du centre d'inertie en m/s²" },
      { name: "v", desc: "Vitesse instantanée en m/s" }
    ],
    source: "Manuel Physique 12ème TSE - Dynamique",
    followup: "Veux-tu voir l'application sur un plan incliné ou en chute libre ?"
  },
  "acide base": {
    text: "En chimie de Terminale, le potentiel hydrogène (pH) d'une solution aqueuse diluée est défini en fonction de la concentration en ions oxonium [H₃O⁺] :",
    formula: "pH = -\\log_{10}[H_3O^+] \\iff [H_3O^+] = 10^{-pH}",
    formulaSpeech: "Voici la formule : le pH est égal à moins le logarithme décimal de la concentration en ions H3O+.",
    variables: [
      { name: "pH", desc: "Potentiel Hydrogène (sans unité, de 0 à 14)" },
      { name: "[H₃O⁺]", desc: "Concentration molaire en ions oxonium (mol/L)" }
    ],
    source: "Manuel Chimie 12ème TSE/TSExp - Solutions Aqueuses",
    followup: "Souhaites-tu calculer le pH d'un acide fort ou d'un acide faible ?"
  },
  "energie cinetique": {
    text: "L'énergie cinétique d'un solide en mouvement de translation est proportionnelle à sa masse et au carré de sa vitesse :",
    formula: "E_c = \\frac{1}{2} m v^2",
    formulaSpeech: "Voici la formule : l'énergie cinétique est égale à un demi de la masse multipliée par le carré de la vitesse.",
    variables: [
      { name: "Ec", desc: "Énergie cinétique en Joules (J)" },
      { name: "m", desc: "Masse en kilogrammes (kg)" },
      { name: "v", desc: "Vitesse en mètres par seconde (m/s)" }
    ],
    source: "Manuel Physique 11ème & 12ème",
    followup: "Veux-tu énoncer le théorème de l'énergie cinétique ?"
  },
  "photosynthese": {
    text: "La photosynthèse est le processus biologique par lequel les végétaux chlorophylliens synthétisent des matières organiques (glucides) à partir d'eau, de dioxyde de carbone et d'énergie lumineuse solaire :",
    formula: "6\\text{CO}_2 + 6\\text{H}_2\\text{O} \\xrightarrow{h\\nu} \\text{C}_6\\text{H}_{12}\\text{O}_6 + 6\\text{O}_2",
    formulaSpeech: "Voici l'équation globale : 6 molécules de CO2 plus 6 molécules d'eau donnent une molécule de glucose et 6 molécules de dioxygène grâce à l'énergie lumineuse.",
    variables: [
      { name: "CO₂", desc: "Dioxyde de carbone absorbé par les stomates" },
      { name: "H₂O", desc: "Eau puisée par les racines" },
      { name: "C₆H₁₂O₆", desc: "Glucose synthétisé (énergie chimique)" },
      { name: "O₂", desc: "Dioxygène rejeté dans l'atmosphère" }
    ],
    source: "Manuel Biologie / SVT 11ème & 12ème",
    followup: "Veux-tu distinguer la phase photochimique et la phase d'assimilation du carbone ?"
  }
};
