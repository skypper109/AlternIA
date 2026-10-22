/**
 * Configuration & Données Curriculaires officielles (Mali).
 * Cycles supportés :
 * - Fondamental (Primaire / Collège) : 6ème, 7ème, 8ème, 9ème (DEF)
 * - Secondaire : 10ème (Tronc commun), 11ème (Séries)
 * - Terminale : 12ème (Baccalauréat)
 */

// Résolution dynamique de l'API (Support Local & Google Colab Pro / AWS Cloud)
const urlParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
const apiFromQuery = urlParams ? urlParams.get('api') : null;
if (apiFromQuery && typeof localStorage !== 'undefined') {
  localStorage.setItem('ALTERNIA_API_URL', apiFromQuery);
}
const savedApi = typeof localStorage !== 'undefined' ? localStorage.getItem('ALTERNIA_API_URL') : null;
export const API_BASE_URL = apiFromQuery || savedApi || (typeof window !== 'undefined' && window.location.origin.startsWith('http') ? window.location.origin : 'http://127.0.0.1:8000');

export const CYCLES = {
  fondamental: {
    id: "fondamental",
    label: "Fondamental",
    sublabel: "6ème · 7ème · 8ème · 9ème (Objectif DEF)",
    tag: "Objectif DEF",
    color: "#40BBCC",
    grades: [
      { id: "6eme", name: "6ème Année", short: "6ème", sub: "Cycle Fondamental" },
      { id: "7eme", name: "7ème Année", short: "7ème", sub: "Cycle Fondamental" },
      { id: "8eme", name: "8ème Année", short: "8ème", sub: "Cycle Fondamental" },
      { id: "9eme", name: "9ème Année (DEF)", short: "9ème", sub: "Diplôme d'Études Fondamentales" }
    ]
  },
  secondaire: {
    id: "secondaire",
    label: "Secondaire",
    sublabel: "10ème · 11ème (Lycée Malien)",
    tag: "Lycée",
    color: "#314999",
    grades: [
      { id: "10eme", name: "10ème Année", short: "10ème", sub: "Tronc Commun" },
      { id: "11eme", name: "11ème Année", short: "11ème", sub: "Sciences & Lettres" }
    ]
  },
  terminale: {
    id: "terminale",
    label: "Terminale",
    sublabel: "12ème Année · Baccalauréat Malien",
    tag: "Objectif BAC",
    color: "#F1851F",
    grades: [
      { id: "12eme", name: "Terminale (12ème)", short: "12ème", sub: "Toutes séries (TSE, TSExp, TSS, TLL, TSEco)" }
    ]
  }
};

export const CURRICULUM_DATA = {
  classes: [
    {
      id: "6eme",
      name: "6ème Année",
      cycle: "fondamental",
      badge: "Fondamental",
      description: "Entrée dans le second cycle fondamental malien",
      subjects: [
        { id: "mathematiques", name: "Mathématiques" },
        { id: "francais", name: "Français" },
        { id: "sciences", name: "Sciences d'Observation" },
        { id: "histoire_geo", name: "Histoire-Géo" }
      ],
      featuredChallenges: [
        { title: "Fractions & Décimaux", subject: "Mathématiques", query: "Explique-moi comment additionner deux fractions simples avec des exemples clairs." },
        { title: "Nature & Fonction des mots", subject: "Français", query: "Quelle est la différence entre la nature d'un mot et sa fonction dans une phrase ?" },
        { title: "Règne végétal & germination", subject: "Sciences", query: "Quelles sont les étapes de la germination d'une graine de haricot ?" }
      ]
    },
    {
      id: "7eme",
      name: "7ème Année",
      cycle: "fondamental",
      badge: "Fondamental",
      description: "Approfondissement des matières fondamentales",
      subjects: [
        { id: "mathematiques", name: "Mathématiques" },
        { id: "francais", name: "Français" },
        { id: "physique_chimie", name: "Physique-Chimie" },
        { id: "histoire_geo", name: "Histoire-Géo" }
      ],
      featuredChallenges: [
        { title: "Nombres relatifs", subject: "Mathématiques", query: "Comment faire la règle des signes pour la multiplication des nombres relatifs ?" },
        { title: "Accord du participe passé", subject: "Français", query: "Rappelle-moi la règle d'accord du participe passé avec l'auxiliaire avoir et être." },
        { title: "L'Empire du Mali", subject: "Histoire", query: "Raconte-moi l'histoire de Soundiata Keïta et la fondation de l'Empire du Mali." }
      ]
    },
    {
      id: "8eme",
      name: "8ème Année",
      cycle: "fondamental",
      badge: "Fondamental",
      description: "Consolidation pré-DEF",
      subjects: [
        { id: "mathematiques", name: "Mathématiques" },
        { id: "physique_chimie", name: "Physique-Chimie" },
        { id: "biologie", name: "Biologie / SVT" },
        { id: "francais", name: "Français" }
      ],
      featuredChallenges: [
        { title: "Équations à une inconnue", subject: "Mathématiques", query: "Explique comment résoudre une équation du premier degré du type ax + b = c." },
        { title: "Mélanges & Corps purs", subject: "Physique-Chimie", query: "Quelle est la différence entre un mélange homogène et un mélange hétérogène ?" },
        { title: "Appareil digestif humain", subject: "SVT", query: "Décris le trajet des aliments dans l'appareil digestif de l'homme." }
      ]
    },
    {
      id: "9eme",
      name: "9ème Année (DEF)",
      cycle: "fondamental",
      badge: "DEF",
      description: "Préparation intensive au Diplôme d'Études Fondamentales (DEF)",
      subjects: [
        { id: "mathematiques", name: "Mathématiques" },
        { id: "physique_chimie", name: "Physique-Chimie" },
        { id: "biologie", name: "Biologie" },
        { id: "francais", name: "Français" },
        { id: "histoire_geo", name: "Histoire-Géo" },
        { id: "anglais", name: "Anglais" }
      ],
      featuredChallenges: [
        { title: "Théorème de Pythagore (DEF)", subject: "Mathématiques", query: "Énonce le théorème de Pythagore et donne un exemple pour calculer l'hypoténuse." },
        { title: "Système de 2 équations", subject: "Mathématiques", query: "Comment résoudre un système de deux équations à deux inconnues par substitution ?" },
        { title: "Loi d'Ohm & Circuits", subject: "Physique", query: "Donne la formule de la loi d'Ohm U = R x I et montre comment trouver l'intensité." },
        { title: "La rédaction au DEF", subject: "Français", query: "Donne-moi la méthodologie complète pour réussir le sujet de rédaction au DEF malien." }
      ]
    },
    {
      id: "10eme",
      name: "10ème Année",
      cycle: "secondaire",
      badge: "Tronc Commun",
      description: "Fondations scientifiques et littéraires du Lycée Malien",
      subjects: [
        { id: "mathematiques", name: "Mathématiques" },
        { id: "physique", name: "Physique" },
        { id: "chimie", name: "Chimie" },
        { id: "francais", name: "Français" },
        { id: "histoire_geo", name: "Histoire-Géo" },
        { id: "anglais", name: "Anglais" }
      ],
      featuredChallenges: [
        { title: "Théorème de Thalès", subject: "Mathématiques", query: "Explique-moi le théorème de Thalès et donne un exercice d'application avec solution." },
        { title: "Loi d'Ohm & Circuits", subject: "Physique", query: "Énonce la loi d'Ohm U = R.I et explique comment calculer la résistance d'un dipôle." },
        { title: "Équilibrer une réaction", subject: "Chimie", query: "Comment équilibrer une équation chimique facilement ? Donne la méthode pas à pas." }
      ]
    },
    {
      id: "11eme",
      name: "11ème Année",
      cycle: "secondaire",
      badge: "Spécialisation",
      description: "Sciences (11S), Lettres (11L), Sciences Économiques (11SECO)",
      subjects: [
        { id: "mathematiques", name: "Mathématiques" },
        { id: "physique", name: "Physique" },
        { id: "chimie", name: "Chimie" },
        { id: "biologie", name: "Biologie / SVT" },
        { id: "francais", name: "Français" }
      ],
      featuredChallenges: [
        { title: "Discriminant Δ & Racines", subject: "Maths 11S", query: "Explique le calcul du discriminant delta et donne les trois cas de racines pour ax² + bx + c = 0." },
        { title: "Énergie Cinétique Ec = ½mv²", subject: "Physique", query: "Démontre le théorème de l'énergie cinétique et donne un exemple d'application." },
        { title: "Photosynthèse Globale", subject: "SVT", query: "C'est quoi la photosynthèse de façon simple ? Donne l'équation bilan et les deux phases." }
      ]
    },
    {
      id: "12eme",
      name: "12ème (Terminale)",
      cycle: "terminale",
      badge: "Baccalauréat",
      description: "Programme Officiel Baccalauréat Malien (TSE, TSExp, TSEco, TSS, TLL)",
      subjects: [
        { id: "mathematiques", name: "Mathématiques" },
        { id: "physique", name: "Physique" },
        { id: "chimie", name: "Chimie" },
        { id: "philosophie", name: "Philosophie" },
        { id: "biologie", name: "Biologie / SVT" }
      ],
      featuredChallenges: [
        { title: "Formule de Moivre (Complexes)", subject: "Maths TSE", query: "Donne la formule de De Moivre pour les nombres complexes et montre comment calculer cos(3x)." },
        { title: "Lois de Newton & Dynamique", subject: "Physique TSE", query: "Énonce la 2ème loi de Newton et explique l'équation du mouvement pour un solide en chute libre." },
        { title: "Acides-Bases & Calcul de pH", subject: "Chimie", query: "Donne la définition du pH en fonction de la concentration en H3O+ et la formule d'un dosage acido-basique." },
        { title: "Conscience & Liberté", subject: "Philosophie", query: "Propose un plan détaillé de dissertation sur le sujet : Sommes-nous maîtres de nos pensées ?" }
      ]
    }
  ]
};

export const KNOWLEDGE_FALLBACK = {
  "formule de moivre": {
    text: "La formule de De Moivre permet d'élever un nombre complexe sous forme trigonométrique à une puissance entière n. Pour tout réel θ et tout entier relatif n :",
    formula: "(\\cos \\theta + i \\sin \\theta)^n = \\cos(n\\theta) + i \\sin(n\\theta)",
    formulaSpeech: "Voici la formule : cosinus de thêta plus i sinus de thêta, le tout à la puissance n, est égal à cosinus de n thêta plus i sinus de n thêta.",
    source: "Manuel Mathématiques 12ème TSE - Nombres Complexes"
  },
  "loi de newton": {
    text: "La deuxième loi de Newton stipule que la somme vectorielle des forces extérieures est égale au produit de sa masse par l'accélération :",
    formula: "\\sum \\vec{F}_{ext} = m \\cdot \\vec{a}_G",
    formulaSpeech: "Voici la formule : la somme des forces extérieures est égale à la masse multipliée par l'accélération.",
    source: "Manuel Physique 12ème TSE - Dynamique"
  },
  "theoreme de pythagore": {
    text: "Dans un triangle rectangle, le carré de la longueur de l'hypoténuse est égal à la somme des carrés des longueurs des deux autres côtés :",
    formula: "BC^2 = AB^2 + AC^2",
    formulaSpeech: "Dans un triangle rectangle en A, le carré de l'hypoténuse BC au carré est égal à AB au carré plus AC au carré.",
    source: "Programme Officiel de Mathématiques du Fondamental (9ème DEF)"
  }
};
