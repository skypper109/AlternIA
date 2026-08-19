/**
 * Configuration & Données Curriculaires officielles (Lycée Malien).
 * Module de configuration pour Alternia Box (Sans émojis, icônes vectorielles SVG).
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
      description: "Fondations scientifiques et littéraires",
      series: ["10ème Commune", "10ème Technique"],
      subjects: [
        { id: "mathematiques", name: "Mathématiques", iconType: "math" },
        { id: "physique", name: "Physique", iconType: "physics" },
        { id: "chimie", name: "Chimie", iconType: "chemistry" },
        { id: "francais", name: "Français", iconType: "literature" },
        { id: "histoire_geo", name: "Histoire-Géographie", iconType: "history" },
        { id: "anglais", name: "Anglais", iconType: "languages" }
      ],
      topics: {
        mathematiques: ["Équations du 1er degré", "Théorème de Thalès", "Trigonométrie fondamentale", "Statistiques descriptives"],
        physique: ["Mouvement rectiligne", "Masse et Poids", "Forces et Équilibre", "Courant électrique continu"],
        chimie: ["Structure de la matière", "Réactions chimiques", "L'eau et l'air", "Combustions et bilans"],
        francais: ["Grammaire et Syntaxe", "Analyse de texte", "Figures de style", "Argumentation"]
      }
    },
    {
      id: "11eme",
      name: "11ème Année",
      badge: "Spécialisation",
      description: "Sciences, Lettres ou Économie",
      series: ["11ème Sciences (11S)", "11ème Lettres (11L)", "11ème Sciences Économiques (11SECO)"],
      subjects: [
        { id: "mathematiques", name: "Mathématiques", iconType: "math" },
        { id: "physique", name: "Physique", iconType: "physics" },
        { id: "chimie", name: "Chimie", iconType: "chemistry" },
        { id: "biologie", name: "Biologie / SVT", iconType: "biology" },
        { id: "francais", name: "Français", iconType: "literature" },
        { id: "histoire_geo", name: "Histoire-Géographie", iconType: "history" },
        { id: "anglais", name: "Anglais", iconType: "languages" }
      ],
      topics: {
        mathematiques: ["Polynômes du second degré", "Fonctions numériques", "Vecteurs et Barycentres", "Suites arithmétiques"],
        physique: ["Travail et Énergie mécanique", "Optique géométrique", "Lois des circuits électriques", "Calorimétrie"],
        chimie: ["Chimie organique (Alcanes)", "Oxydoréduction", "Concentration molaire", "Solutions aqueuses"],
        biologie: ["Organisation cellulaire", "Génétique fondamentale", "Écosystèmes sahéliens"]
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
        { id: "mathematiques", name: "Mathématiques", iconType: "math" },
        { id: "physique", name: "Physique", iconType: "physics" },
        { id: "chimie", name: "Chimie", iconType: "chemistry" },
        { id: "philosophie", name: "Philosophie", iconType: "philosophy" },
        { id: "biologie", name: "Biologie / SVT", iconType: "biology" },
        { id: "histoire_geo", name: "Histoire-Géographie", iconType: "history" },
        { id: "francais", name: "Littérature", iconType: "literature" }
      ],
      topics: {
        mathematiques: [
          "Nombres Complexes (Formule de Moivre & Euler)",
          "Équations Différentielles (y' + ay = 0)",
          "Fonctions Logarithme et Exponentielle",
          "Calcul Intégral et Primitives",
          "Probabilités conditionnelles"
        ],
        physique: [
          "Lois de Newton (F = m.a)",
          "Mouvement dans un champ de pesanteur",
          "Circuits RLC et Oscillations libres",
          "Noyau atomique et Radioactivité",
          "Dipôles RC et RL"
        ],
        chimie: [
          "Couples Acides-Bases et pH",
          "Estérification et Hydrolyse",
          "Fonctions oxygénées (Alcools, Aldéhydes, Cétones)",
          "Dosages acido-basiques"
        ],
        philosophie: [
          "La Conscience et l'Inconscient",
          "La Liberté et la Nécessité",
          "La Science et la Vérité",
          "L'État et la Justice"
        ]
      }
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
