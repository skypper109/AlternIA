"""
Dictionnaire exhaustif des concepts, notions et termes du programme scolaire officiel
du Mali (10ème, 11ème, 12ème / Terminale) pour la détection précise de la matière.
"""

import re
import unicodedata
from typing import Optional


# ==============================================================================
# MOTS-CLÉS DU PROGRAMME OFFICIEL DU MALI PAR MATIÈRE
# ==============================================================================

MALIAN_CURRICULUM_KEYWORDS: dict[str, list[str]] = {
    # --------------------------------------------------------------------------
    # BIOLOGIE / SVT (Sciences de la Vie et de la Terre)
    # --------------------------------------------------------------------------
    "biologie": [
        # Botanique & Physiologie végétale
        "photosynthèse", "photosynthese", "chlorophylle", "chloroplaste", "stomate", "stomates",
        "transpiration végétale", "transpiration vegetale", "sève brute", "seve brute",
        "sève élaborée", "seve elaboree", "sociologie végétale", "sociologie vegetale",
        "groupement végétal", "groupement vegetal", "succession écologique", "succession ecologique",
        "phytosociologie", "stratification végétale", "autotrophe", "hétérotrophe", "heterotrophe",
        "végétal", "vegetal", "végétale", "vegetale", "plante", "chlorophyllienne",
        # Biologie cellulaire & Génétique
        "cellule", "membrane plasmique", "cytoplasme", "noyau cellulaire", "mitochondrie",
        "adn", "arn", "arn messager", "arnm", "arnt", "chromosome", "caryotype", "gène", "gene",
        "allèle", "allele", "mutation génétique", "mitose", "méiose", "meiose", "crossing-over",
        "brassage génétique", "brassage interchromosomique", "brassage intrachromosomique",
        "réplication de l'adn", "transcription", "traduction génétique", "ribosome", "code génétique",
        "synthèse des protéines", "synthese des proteines", "acides aminés", "acide aminé",
        "monohybridisme", "dihybridisme", "lois de mendel", "loi de mendel", "mendélisme",
        "dominance", "récessivité", "recessivite", "codominance", "test-cross", "back-cross",
        "hérédité liée au sexe", "gonosome", "autosome", "arbre généalogique", "génotype", "genotype",
        "phénotype", "phenotype", "homozygote", "hétérozygote", "heterozygote",
        # Physiologie animale & Reproduction
        "gamétogenèse", "gametogenese", "spermatogenèse", "spermatogenese", "ovogenèse", "ovogenese",
        "spermatozoïde", "spermatozoide", "ovocyte", "folliculogenèse", "cycle menstruel",
        "cycle ovarien", "cycle utérin", "ovulation", "fécondation", "fecondation", "nidation",
        "placenta", "testostérone", "testosterone", "œstrogène", "oestrogene", "progestérone",
        "progesterone", "fsh", "lh", "complexe hypothalamo-hypophysaire", "contraception", "gamète", "gamete",
        # Neurobiologie & Immunologie
        "neurone", "axone", "dendrite", "potentiel de repos", "potentiel d'action", "synapse",
        "neurotransmetteur", "réflexe myotatique", "reflexe myotatique", "arc réflexe", "arc reflexe",
        "fuseau neuromusculaire", "moelle épinière", "moelle epiniere", "système nerveux",
        "immunité innée", "immunité adaptative", "anticorps", "antigène", "antigene",
        "lymphocyte t", "lymphocyte b", "lymphocytes", "phagocytose", "macrophage", "vih", "sida",
        "séropositivité", "seropositivite", "vaccin", "sérum", "serum", "immunologie",
        # Écologie & Géologie (SVT)
        "écosystème", "ecosysteme", "biotope", "biocénose", "biocenose", "chaîne trophique",
        "chaine alimentaire", "réseau trophique", "biomasse", "productivité primaire",
        "cycle du carbone", "cycle de l'azote", "pédologie", "pedologie", "sol", "profil du sol",
        "tectonique des plaques", "lithosphère", "lithosphere", "asthénosphère", "asthenosphere",
        "dérive des continents", "dorsale océanique", "subduction", "séisme", "seisme", "volcanisme",
        "roches magmatiques", "roches sédimentaires", "roches métamorphiques", "svt", "biologie",
        "respiration cellulaire", "fermentation", "digestion", "vivant",
    ],

    # --------------------------------------------------------------------------
    # CHIMIE
    # --------------------------------------------------------------------------
    "chimie": [
        # Chimie organique
        "alcane", "alcanes", "alcène", "alcènes", "alcene", "alcenes", "alcyne", "alcynes",
        "alcool", "alcools", "aldéhyde", "aldéhydes", "aldehyde", "aldehydes", "cétone", "cétones", "cetone", "cetones",
        "acide carboxylique", "acides carboxyliques", "ester", "esters", "estérification", "esterification",
        "hydrolyse", "saponification", "savon", "savons", "amine", "amines", "amide", "amides",
        "polymère", "polymères", "polymere", "polymeres", "polymérisation", "polymerisation",
        "isomérie", "isomere", "chaîne carbonée", "chaine carbonee", "formule brute", "formule semi-développée",
        "nomenclature uicpa", "benzène", "benzene", "aromatique", "combustion des alcanes",
        # Chimie générale & Minérale
        "solution aqueuse", "solutions aqueuses", "solvant", "soluté", "solute",
        "concentration molaire", "concentration massique", "mole", "moles", "masse molaire",
        "volume molaire", "quantité de matière", "quantite de matiere", "avogadro",
        "réaction chimique", "reaction chimique", "équation-bilan", "equation-bilan",
        "stœchiométrie", "stoechiometrie", "réactif limitant", "reactif limitant", "tableau d'avancement",
        "ion", "ions", "cation", "cations", "anion", "anions", "liaison ionique", "liaison covalente",
        "électronégativité", "electronegativite", "atome", "atomes", "électron", "electron", "proton", "protons",
        "neutron", "neutrons", "tableau périodique", "tableau periodique", "mendeleïev", "mendeleiev",
        # Solutions acido-basiques
        "ph", "autoprotolyse de l'eau", "produit ionique de l'eau", "acide fort", "base forte",
        "acide faible", "base faible", "couple acide-base", "constante d'acidité", "constante d'acidite",
        "ka", "pka", "zone de virage", "indicateur coloré", "indicateur colore",
        "solution tampon", "solutions tampons", "dosage acido-basique", "titrage acido-basique",
        "équivalence acido-basique", "equivalence acido-basique", "acide chlorhydrique", "hydroxyde de sodium",
        # Oxydoréduction & Cinétique
        "oxydation", "réduction", "reduction", "oxydoréduction", "oxydoreduction", "oxydant", "réducteur", "reducteur",
        "couple redox", "demi-équation", "demi-equation", "pile électrochimique", "pile daniell",
        "anode", "cathode", "électrolyse", "electrolyse", "loi de faraday", "vitesse de réaction",
        "catalyseur", "temps de demi-réaction", "chimie",
    ],

    # --------------------------------------------------------------------------
    # PHYSIQUE
    # --------------------------------------------------------------------------
    "physique": [
        # Mécanique & Cinématique
        "vecteur position", "vecteur vitesse", "vecteur accélération", "vecteur acceleration",
        "mouvement rectiligne", "mru", "mruv", "mouvement circulaire", "mcu", "vitesse angulaire",
        "accélération tangentielle", "accélération normale", "trajectoire",
        # Dynamique & Lois de Newton
        "lois de newton", "loi de newton", "première loi de newton", "deuxième loi de newton",
        "troisième loi de newton", "principe d'inertie", "centre d'inertie", "quantité de mouvement",
        "quantite de mouvement", "force de frottement", "frottement", "poids", "masse", "gravitation",
        "poussée d'archimède", "poussee d'archimede", "tension du fil",
        # Travail & Énergie
        "travail d'une force", "énergie cinétique", "energie cinetique", "énergie potentielle",
        "energie potentielle", "énergie mécanique", "energie mecanique", "théorème de l'énergie cinétique",
        "theoreme de l'energie cinetique", "conservation de l'énergie", "puissance mécanique", "joule",
        # Champs & Gravitation
        "champ de gravitation", "gravitation universelle", "mouvement des satellites", "satellites",
        "lois de kepler", "loi de kepler", "champ électrostatique", "champ electrostatique",
        "force de coulomb", "champ électrique uniforme", "particule chargée", "déflexion électrique",
        "champ magnétique", "champ magnetique", "aimant", "solénoïde", "solenoide", "force de lorentz",
        "force de laplace", "règle de la main droite", "spectromètre de masse", "cyclotron",
        # Électricité & Électromagnétisme
        "circuit électrique", "courant électrique", "tension électrique", "intensité", "intensite",
        "résistance", "resistance", "loi d'ohm", "condensateur", "capacité", "capacite",
        "charge du condensateur", "décharge du condensateur", "constante de temps", "bobine inductive",
        "bobine", "inductance", "auto-induction", "force électromotrice", "loi de lenz",
        "circuit rc", "circuit rl", "circuit rlc", "oscillations électriques", "oscillations electriques",
        "résonance électrique", "resonance electrique", "impédance", "impedance",
        # Oscillations mécaniques & Ondes
        "pendule simple", "pendule élastique", "oscillateur harmonique", "pulsation propre",
        "période propre", "onde mécanique", "onde transversale", "onde longitudinale",
        "célérité de l'onde", "longueur d'onde", "fréquence", "frequence", "interférences", "diffraction",
        # Optique géométrique
        "réflexion", "reflexion", "réfraction", "refraction", "snell-descartes", "indice de réfraction",
        "réflexion totale", "lentille mince", "lentille convergente", "lentille divergente",
        "distance focale", "vergence", "formule de conjugaison", "grandissement", "optique",
        # Physique nucléaire
        "noyau atomique", "nucléons", "nucleons", "isotope", "défaut de masse", "énergie de liaison",
        "radioactivité", "radioactivite", "radioactivité alpha", "radioactivité bêta", "radioactivité gamma",
        "décroissance radioactive", "période radioactive", "demi-vie", "fission nucléaire", "fusion nucléaire", "physique",
    ],

    # --------------------------------------------------------------------------
    # MATHÉMATIQUES
    # --------------------------------------------------------------------------
    "mathematiques": [
        # Analyse & Fonctions
        "fonction numérique", "domaine de définition", "ensemble de définition", "limite", "continuité",
        "théorème des valeurs intermédiaires", "dérivée", "derivee", "dérivabilité",
        "tableau de variation", "asymptote", "asymptote oblique", "fonction réciproque",
        "logarithme", "logarithme népérien", "fonction exponentielle", "primitives", "primitive",
        "intégrale", "integrale", "intégration par parties", "calcul d'aire", "équation différentielle",
        "equation differentielle", "différentielle", "differentielle",
        # Suites numériques
        "suite numérique", "suite arithmétique", "suite geometrique", "suite géométrique",
        "raison de la suite", "somme des termes", "suite convergente", "récurrence", "recurrence",
        # Nombres complexes
        "nombre complexe", "nombres complexes", "partie réelle", "partie imaginaire", "module d'un complexe",
        "argument d'un complexe", "forme trigonométrique", "forme exponentielle", "formule d'euler",
        "formule de moivre", "racines n-ièmes",
        # Géométrie & Algèbre
        "vecteur", "vecteurs", "produit scalaire", "barycentre", "coniques", "ellipse", "parabole",
        "hyperbole", "transformation du plan", "homothétie", "similitude directe", "trigonométrie",
        "trigonometrie", "sinus", "cosinus", "tangente", "géométrie", "geometrie",
        # Probabilités & Statistiques
        "probabilité", "probabilite", "dénombrement", "combinaison", "arrangement", "factorielle",
        "variable aléatoire", "loi binomiale", "schéma de bernoulli", "probabilité conditionnelle",
        "espérance mathématique", "variance", "écart-type", "statistique", "régression linéaire",
        # Arithmétique & Algèbre générale
        "pgcd", "ppcm", "algorithme d'euclide", "nombres premiers", "division euclidienne",
        "congruence", "théorème de bézout", "théorème de gauss", "matrice", "déterminant",
        "polynôme", "polynome", "équation", "equation", "inéquation", "inequation", "théorème", "theoreme",
        "maths", "mathématiques", "mathematiques",
    ],

    # --------------------------------------------------------------------------
    # ÉCONOMIE & COMPTABILITÉ
    # --------------------------------------------------------------------------
    "economie": [
        # Économie générale & Macroéconomie
        "pib", "pnb", "revenu national", "croissance économique", "développement économique",
        "inflation", "déflation", "stagflation", "chômage", "chomage", "population active",
        "marché du travail", "offre et demande", "équilibre du marché", "élasticité-prix",
        "circuit économique", "agents économiques", "ménages", "menages", "entreprises individuelles",
        "consommation", "épargne", "investissement", "multiplicateur d'investissement",
        # Comptabilité nationale & Secteurs institutionnels (Programme Mali 11ème / 12ème)
        "comptabilité nationale", "comptabilite nationale", "agrégats économiques",
        "sociétés non financières", "societes non financieres", "société non financière",
        "snf", "sqnf", "sqsnf", "société et quasi société non financière",
        "sociétés financières", "societes financieres", "société financière", "sf",
        "secteurs institutionnels", "secteur institutionnel", "secteurs institutionnel", "si",
        "unités institutionnelles", "unite institutionnelle", "unités résidentes",
        "administrations publiques", "apul", "apuc", "institutions sans but lucratif", "isblsm",
        "reste du monde", "rdm", "système élargi de comptabilité nationale", "secn",
        "opérations sur biens et services", "opérations de répartition", "opérations financières",
        "tableau économique d'ensemble", "tee", "tableau entrées-sorties", "tes",
        # Monnaie & Finance
        "masse monétaire", "création monétaire", "banque centrale", "bceao", "uemoa",
        "franc cfa", "politique monétaire", "taux d'intérêt", "taux d'interet", "crédit bancaire",
        "bourse", "marché financier", "actions", "obligations",
        # Économie publique & Internationale
        "budget de l'état", "fiscalité", "fiscalite", "impôt", "impots", "déficit budgétaire",
        "dette publique", "politique budgétaire", "balance des paiements", "balance commerciale",
        "taux de change", "dévaluation", "libre-échange", "protectionnisme", "omc", "cedeao", "économie", "economie",
    ],

    "comptabilite": [
        # Comptabilité générale & SYSCOHADA
        "comptabilité", "comptabilite", "bilan comptable", "actif du bilan", "passif du bilan",
        "capitaux propres", "actif immobilisé", "actif circulant", "compte de résultat", "charges",
        "produits", "résultat net", "partie double", "débit", "debit", "crédit", "credit",
        "journal comptable", "grand livre", "balance des comptes", "plan comptable", "syscohada",
        "amortissement", "amortissement linéaire", "amortissement dégressif", "provision",
        "tva", "facture", "facturation", "trésorerie", "tresorerie",
    ],

    # --------------------------------------------------------------------------
    # FRANÇAIS & LITTÉRATURE
    # --------------------------------------------------------------------------
    "francais": [
        "conjugaison", "grammaire", "syntaxe", "subjonctif", "conditionnel", "concordance des temps",
        "participe passé", "voix passive", "discours direct", "discours indirect",
        "figure de style", "métaphore", "metaphore", "métonymie", "metonymie", "allégorie",
        "personnification", "hyperbole", "litote", "anaphore", "oxymore", "antithèse",
        "champ lexical", "registre littéraire", "registre tragique", "registre lyrique",
        "roman", "poésie", "poesie", "poème", "poeme", "versification", "alexandrin", "rime",
        "théâtre", "theatre", "tragédie", "comédie", "didascalie", "monologue", "quiproquo",
        "littérature", "litterature", "négritude", "negritude", "aimé césaire", "léopold sédar senghor",
        "classicisme", "siècle des lumières", "romantisme", "réalisme", "naturalisme",
        "littérature africaine", "amadou hampâté bâ", "camara laye", "commentaire composé",
        "dissertation littéraire", "résumé de texte", "français", "francais",
    ],

    # --------------------------------------------------------------------------
    # LINGUISTIQUE
    # --------------------------------------------------------------------------
    "linguistique": [
        "linguistique", "signe linguistique", "signifiant", "signifié", "arbitraire du signe",
        "phonétique", "phonetique", "phonologie", "phonème", "phoneme", "alphabet phonétique international",
        "morphologie", "morphème", "morpheme", "affixe", "préfixe", "suffixe",
        "syntagme nominal", "syntagme verbal", "sémantique", "semantique", "pragmatique",
        "énonciation", "enonciation", "déictique", "schéma de la communication", "jakobson",
        "fonction expressive", "fonction conative", "fonction référentielle", "fonction phatique",
        "fonction métalinguistique", "fonction poétique", "langues nationales du mali",
        "bamanankan", "bambara", "fulfulde", "peul", "soninké", "soninke", "songhaï", "tamasheq", "dogon",
    ],

    # --------------------------------------------------------------------------
    # HISTOIRE
    # --------------------------------------------------------------------------
    "histoire": [
        # Histoire du Mali & de l'Afrique
        "empire du ghana", "empire du mali", "soundiata keïta", "soundiata keita", "charte de kurukan fuga",
        "mansa moussa", "empire songhaï", "empire songhai", "sonni ali ber", "askia mohamed",
        "royaume bambara de ségou", "biton coulibaly", "ngolo diarra", "empire peul du macina",
        "sékou amadou", "empire toucouleur", "el hadj omar tall", "royaume du kénédougou",
        "tiéba traoré", "babemba traoré", "samory touré", "bataille de sikasso",
        "traite négrière", "traite transsaharienne", "commerce triangulaire", "code noir",
        # Colonisation & Indépendances
        "conférence de berlin", "partage de l'afrique", "soudan français", "tirailleurs sénégalais",
        "résistances anticoloniales", "décolonisation", "decolonisation", "indépendance du mali",
        "modibo keïta", "modibo keita", "fédération du mali", "organisation de l'unité africaine",
        "oua", "union africaine",
        # Histoire contemporaine mondiale
        "première guerre mondiale", "premiere guerre mondiale", "seconde guerre mondiale",
        "traité de versailles", "société des nations", "sdn", "guerre froide", "plan marshall",
        "crise de 1929", "nazisme", "fascisme", "holocauste", "chute du mur de berlin",
        "onu", "non-alignement", "histoire",
    ],

    # --------------------------------------------------------------------------
    # GÉOGRAPHIE
    # --------------------------------------------------------------------------
    "geographie": [
        # Géographie du Mali
        "géographie du mali", "relief du mali", "plateau mandingue", "falaise de bandiagara",
        "mont hombori", "adrar des ifoghas", "delta central du niger", "fleuve niger",
        "fleuve sénégal", "climat sahélien", "climat soudanien", "harmattan", "mousson",
        "désertification", "culture du coton au mali", "riziculture", "mines d'or du mali",
        "mines de loulo", "mines de morila", "démographie du mali", "urbanisation de bamako", "exode rural",
        # Géographie mondiale & Développement
        "continent", "continents", "latitude", "longitude", "relief", "climat", "biome",
        "mondialisation", "flux migratoires", "commerce mondial", "pays développés",
        "pays émergents", "pma", "développement durable", "changement climatique",
        "gaz à effet de serre", "transition démographique", "géographie", "geographie",
    ],

    # --------------------------------------------------------------------------
    # PHILOSOPHIE
    # --------------------------------------------------------------------------
    "philosophie": [
        "conscience", "inconscient", "mémoire", "perception", "désir", "desir", "passion",
        "liberté", "liberte", "déterminisme", "determinisme", "devoir", "morale", "éthique", "ethique",
        "justice", "droit naturel", "droit positif", "état", "etat", "pouvoir politique",
        "contrat social", "société", "societe", "autrui", "culture", "nature", "travail",
        "technique", "art", "esthétique", "religion", "vérité", "verite", "raison", "illusion",
        "démonstration", "science", "matière", "esprit", "temps", "existence", "mort", "bonheur",
        # Auteurs
        "socrate", "maïeutique", "platon", "allégorie de la caverne", "aristote", "descartes",
        "cogito", "spinoza", "rousseau", "kant", "impératif catégorique", "hegel", "dialectique",
        "marx", "matérialisme", "nietzsche", "freud", "sartre", "existentialisme",
        "philosophie africaine", "amadou hampâté bâ", "kwame nkrumah", "cheikh anta diop",
        "philosophie", "philo",
    ],

    # --------------------------------------------------------------------------
    # DROIT
    # --------------------------------------------------------------------------
    "droit": [
        "droit objectif", "droit subjectif", "règle de droit", "constitution", "loi", "décret",
        "jurisprudence", "coutume", "personnalité juridique", "personne physique", "personne morale",
        "capacité juridique", "contrat", "responsabilité civile", "responsabilité pénale",
        "infraction", "crime", "délit", "contravention", "organisation judiciaire", "cour suprême",
        "cour constitutionnelle", "tribunal", "droit",
    ],

    # --------------------------------------------------------------------------
    # ANGLAIS
    # --------------------------------------------------------------------------
    "anglais": [
        "simple present", "present continuous", "simple past", "past continuous",
        "present perfect", "past perfect", "passive voice", "reported speech", "conditional",
        "modals", "relative pronouns", "gerund", "infinitive", "phrasal verbs",
        "irregular verbs", "tag questions", "reading comprehension", "essay writing",
        "grammar", "vocabulary", "tense", "english", "anglais",
    ],
}


def normalize_curriculum_text(text: str) -> str:
    """Normalise une chaîne pour la détection de mots-clés."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return no_accents.lower().strip()


def detect_malian_curriculum_subject(question: str) -> Optional[str]:
    """
    Identifie automatiquement la matière scolaire malienne à partir
    de la question de l'élève ou d'une notion brute.

    Priorité :
    1. Expressions à mots multiples exactes (ex: "sociologie végétale", "lois de newton")
    2. Mots-clés uniques avec frontières de mots entiers (\\b)
    """
    if not question:
        return None

    q_norm = normalize_curriculum_text(question)

    # 1. Recherche prioritaire des expressions composées (>= 2 mots)
    for subj, keywords in MALIAN_CURRICULUM_KEYWORDS.items():
        for kw in keywords:
            if " " in kw or "-" in kw:
                kw_norm = normalize_curriculum_text(kw)
                pattern = r"\b" + re.escape(kw_norm) + r"\b"
                if re.search(pattern, q_norm):
                    return subj

    # 2. Recherche des mots-clés simples avec frontières strictes (\b)
    for subj, keywords in MALIAN_CURRICULUM_KEYWORDS.items():
        for kw in keywords:
            if " " not in kw and "-" not in kw:
                kw_norm = normalize_curriculum_text(kw)
                if len(kw_norm) < 3:
                    continue
                pattern = r"\b" + re.escape(kw_norm) + r"\b"
                if re.search(pattern, q_norm):
                    return subj

    return None
