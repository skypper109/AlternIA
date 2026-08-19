/**
 * Configuration & Données Curriculaires officielles (Lycée Malien).
 * Module de configuration pour Alternia Box.
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

// Base locale de secours autonome 100% hors-ligne
export const KNOWLEDGE_FALLBACK = {
  "formule de moivre": {
    text: "La formule de De Moivre permet d'élever un nombre complexe sous forme trigonométrique à une puissance entière n. Pour tout réel θ et tout entier relatif n :",
    formula: "(\\cos \\theta + i \\sin \\theta)^n = \\cos(n\\theta) + i \\sin(n\\theta)",
    formulaSpeech: "Voici la formule en question : cosinus de thêta plus i sinus de thêta, le tout à la puissance n, est égal à cosinus de n thêta plus i sinus de n thêta.",
    variables: [
      { name: "θ", desc: "Argument du nombre complexe (en radians)" },
      { name: "n", desc: "Entier relatif (exposant de la puissance)" },
      { name: "i", desc: "Unité imaginaire pure telle que i² = -1" }
    ],
    source: "Manuel Mathématiques 12ème TSE - Chapitre Nombres Complexes",
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
