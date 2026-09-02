import re
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CurriculumTopic:
    """Description d'une notion curriculaire et de ses caractéristiques."""
    name: str
    subject: str
    target_class: str
    target_series: str
    patterns: list[str]
    prerequisites: list[str]
    intuitive_analogy: str
    suggested_questions: list[str]


@dataclass
class ScopeAnalysisResult:
    """Résultat de l'analyse d'adéquation curriculaire."""
    is_higher_level: bool = False
    current_class: str = "10eme"
    target_class: Optional[str] = None
    target_series: Optional[str] = None
    topic_name: Optional[str] = None
    subject: Optional[str] = None
    prerequisites: list[str] = field(default_factory=list)
    intuitive_analogy: Optional[str] = None
    suggested_questions: list[str] = field(default_factory=list)
    pedagogical_guidance: Optional[str] = None


class CurriculumScopeChecker:
    """
    Vérificateur de portée curriculaire pour AlternIA.

    Détecte lorsqu'un élève (ex: 10ème ou 11ème) pose une question
    sur une notion d'un niveau supérieur (ex: 12ème / Terminale),
    afin de :
    1. L'informer avec bienveillance que la notion dépasse son programme actuel.
    2. Lui donner une vulgarisation intuitive adaptée sans le perdre dans des calculs hors de portée.
    3. Lui rappeler les prérequis de sa classe actuelle à maîtriser d'abord.
    4. Lui suggérer des questions pertinentes de son niveau.
    """

    CLASS_RANKS = {
        "10eme": 10,
        "10ème": 10,
        "10": 10,
        "10e": 10,
        "10eme annee": 10,
        "10ème année": 10,
        "11eme": 11,
        "11ème": 11,
        "11": 11,
        "11e": 11,
        "11eme annee": 11,
        "11ème année": 11,
        "11s": 11,
        "11l": 11,
        "11seco": 11,
        "12eme": 12,
        "12ème": 12,
        "12": 12,
        "12e": 12,
        "12eme annee": 12,
        "12ème année": 12,
        "terminale": 12,
        "terminal": 12,
        "tse": 12,
        "tsexp": 12,
        "tss": 12,
        "tseco": 12,
        "tll": 12,
    }

    def __init__(self):
        self.topics_database: list[CurriculumTopic] = self._init_database()

    def _init_database(self) -> list[CurriculumTopic]:
        return [
            # =========================================================
            # NOTIONS DE 12ÈME (TERMINALE TSE / TSExp / TSEco / TSS)
            # =========================================================
            CurriculumTopic(
                name="L'Arithmétique, la Divisibilité et les Congruences",
                subject="mathematiques",
                target_class="12eme",
                target_series="TSE (Sciences Exactes)",
                patterns=[
                    r"\bcongruences?\b",
                    r"\bcongru\b",
                    r"\barithmetique\s+modulaire\b",
                    r"\bmodulo\b",
                    r"\btheoreme\s+de\s+bezout\b",
                    r"\btheoreme\s+de\s+gauss\b",
                    r"\bidentite\s+de\s+bezout\b",
                    r"\bdivisibilite\s+dans\s+z\b",
                    r"\bpgcd\s+dans\s+z\b",
                    r"\bnombres?\s+premiers?\s+entre\s+eux\b",
                    r"\bpetit\s+theoreme\s+de\s+fermat\b",
                    r"\bdivision\s+euclidienne\s+dans\s+z\b",
                    r"\bequations?\s+diophantiennes?\b",
                    r"≡",
                ],
                prerequisites=[
                    "Division euclidienne dans N et ensemble des entiers naturels",
                    "Multiples et diviseurs en 10ème",
                    "Nombres premiers et décomposition en facteurs premiers",
                ],
                intuitive_analogy=(
                    "La congruence fonctionne exactement comme une horloge : après 12h, il est 1h "
                    "(13h ≡ 1h modulo 12). On ne s'intéresse qu'au reste de la division !"
                ),
                suggested_questions=[
                    "Comment effectuer la division euclidienne avec quotient et reste en 10ème ?",
                    "Comment décomposer un entier en produit de facteurs premiers ?",
                ],
            ),
            CurriculumTopic(
                name="La Stéréochimie et l'Isomérie Spatiale",
                subject="chimie",
                target_class="12eme",
                target_series="TSExp (Sciences Expérimentales) / TSE",
                patterns=[
                    r"\bstereochimie\b",
                    r"\bstereoisomeres?\b",
                    r"\bchiralite\b",
                    r"\bmolecules?\s+chirales?\b",
                    r"\bcarbone\s+asymetrique\b",
                    r"\benantiomeres?\b",
                    r"\bdiastereoisomeres?\b",
                    r"\bisomerie\s+optique\b",
                    r"\bisomerie\s+spatiale\b",
                    r"\brepresentation\s+de\s+newman\b",
                    r"\bprojection\s+de\s+fischer\b",
                    r"\bprojection\s+de\s+cram\b",
                    r"\bconformation\s+chaise\b",
                    r"\bpouvoir\s+rotatoire\b",
                    r"\bmelange\s+racemique\b",
                ],
                prerequisites=[
                    "Structure de l'atome de carbone (tétravalence) en 10ème",
                    "Formules brutes et formules semi-développées des molécules simples",
                    "Notion de liaisons covalentes",
                ],
                intuitive_analogy=(
                    "La chiralité, c'est comme tes mains gauche et droite : elles ont les mêmes composants, "
                    "mais tu ne peux pas superposer ta main gauche sur ta main droite dans l'espace !"
                ),
                suggested_questions=[
                    "Qu'est-ce qu'une formule brute et une formule développée en chimie de 10ème ?",
                    "Qu'est-ce qu'une liaison covalente simple entre atomes ?",
                ],
            ),
            CurriculumTopic(
                name="Les Nombres Complexes",
                subject="mathematiques",
                target_class="12eme",
                target_series="TSE (Sciences Exactes) / TSExp",
                patterns=[
                    r"\bnombres?\s+complexes?\b",
                    r"\bpartie\s+imaginaire\b",
                    r"\bpartie\s+reelle\b",
                    r"\bmodule\s+et\s+argument\b",
                    r"\bforme\s+trigonometrique\b",
                    r"\bforme\s+algebrique\b",
                    r"\bnombre\s+i\b",
                    r"\bi\s*²\s*=\s*-1\b",
                    r"\bi\^2\s*=\s*-1\b",
                    r"\bplan\s+complexe\b",
                    r"\bformule\s+de\s+moivre\b",
                    r"\bformule\s+d'euler\b",
                ],
                prerequisites=[
                    "Résolution des équations du second degré (discriminant Delta)",
                    "Calcul littéral et factorisation",
                    "Trigonométrie dans le cercle et angles remarquables",
                ],
                intuitive_analogy=(
                    "Imagine un nombre magique noté 'i' qui permet de résoudre les équations "
                    "où le carré est négatif (comme x² = -1). C'est comme inventer une 2ème dimension pour les nombres !"
                ),
                suggested_questions=[
                    "Comment résoudre une équation du second degré ax² + bx + c = 0 quand Delta est positif ?",
                    "Que se passe-t-il quand le discriminant Delta est négatif dans l'ensemble des réels ?",
                ],
            ),
            CurriculumTopic(
                name="Le Calcul Intégral et les Primitives",
                subject="mathematiques",
                target_class="12eme",
                target_series="TSE / TSExp / TSEco",
                patterns=[
                    r"\bintegrales?\b",
                    r"\bcalcul\s+integral\b",
                    r"\bprimitives?\b",
                    r"\bintegration\s+par\s+parties\b",
                    r"\bcalcul\s+d'aires?\b",
                    r"\bintegrer\s+une\s+fonction\b",
                ],
                prerequisites=[
                    "Dérivation et sens de variation des fonctions",
                    "Calculs d'aires de figures usuelles (rectangles, triangles, trapèzes)",
                    "Fonctions usuelles et polynômes",
                ],
                intuitive_analogy=(
                    "L'intégrale, c'est comme découper une surface courbée sous une courbe en millions de "
                    "minuscules rectangles pour en calculer l'aire exacte avec une précision absolue."
                ),
                suggested_questions=[
                    "Comment calculer l'aire d'un polygone ou d'un trapèze ?",
                    "Comment étudier les variations d'une fonction affine ou polynôme ?",
                ],
            ),
            CurriculumTopic(
                name="Les Fonctions Exponentielles et Logarithmes",
                subject="mathematiques",
                target_class="12eme",
                target_series="TSE / TSExp / TSEco / TSS",
                patterns=[
                    r"\bexponentielles?\b",
                    r"\blogarithmes?\s+neperiens?\b",
                    r"\bln\s*\(",
                    r"\be\^x\b",
                    r"\bcroissance\s+comparee\b",
                ],
                prerequisites=[
                    "Puissances et racines carrées (propriétés de a^n)",
                    "Étude générale des fonctions numériques et sens de variation",
                ],
                intuitive_analogy=(
                    "L'exponentielle représente les phénomènes qui explosent très vite (comme la croissance d'une population de bactéries), "
                    "tandis que le logarithme est son miroir qui grandit très lentement."
                ),
                suggested_questions=[
                    "Quelles sont les propriétés des puissances en mathématiques ?",
                    "Comment tracer la courbe d'une fonction affine f(x) = ax + b ?",
                ],
            ),
            CurriculumTopic(
                name="Les Équations Différentielles",
                subject="mathematiques",
                target_class="12eme",
                target_series="TSE (Sciences Exactes)",
                patterns=[
                    r"\bequations?\s+differentielles?\b",
                    r"\by'\s*=\s*ay\b",
                    r"\by''\s*\+\s*",
                ],
                prerequisites=[
                    "Notion de dérivée d'une fonction",
                    "Résolution d'équations algébriques usuelles",
                ],
                intuitive_analogy=(
                    "Une équation différentielle ne cherche pas un nombre inconnu x, mais une fonction inconnue "
                    "qui décrit l'évolution dans le temps d'un phénomène physique (comme la vitesse ou la température)."
                ),
                suggested_questions=[
                    "Comment résoudre un système d'équations à deux inconnues ?",
                    "Qu'est-ce que le taux de variation d'une fonction ?",
                ],
            ),
            CurriculumTopic(
                name="Le Calcul Matriciel et Systèmes Linéaires",
                subject="mathematiques",
                target_class="12eme",
                target_series="TSE (Sciences Exactes)",
                patterns=[
                    r"\bmatrices?\b",
                    r"\bcalcul\s+matriciel\b",
                    r"\bpivot\s+de\s+gauss\b",
                    r"\bdeterminant\s+d'une\s+matrice\b",
                    r"\bmatrice\s+inverse\b",
                ],
                prerequisites=[
                    "Résolution de systèmes d'équations du premier degré à 2 inconnues",
                    "Calcul littéral et distributivité",
                ],
                intuitive_analogy=(
                    "Une matrice est comme un tableau de chiffres organisé qui permet de résoudre "
                    "dizaines d'équations en même temps en une seule opération."
                ),
                suggested_questions=[
                    "Comment résoudre un système de 2 équations à 2 inconnues par substitution ?",
                ],
            ),
            CurriculumTopic(
                name="La Géométrie dans l'Espace et le Produit Vectoriel",
                subject="mathematiques",
                target_class="12eme",
                target_series="TSE / TSExp",
                patterns=[
                    r"\bproduit\s+vectoriel\b",
                    r"\bequation\s+cartesienne\s+du\s+plan\b",
                    r"\bvecteur\s+normal\s+au\s+plan\b",
                    r"\bgeometrie\s+dans\s+l'espace\b",
                ],
                prerequisites=[
                    "Vecteurs du plan et relation de Chasles",
                    "Repère orthonormé et coordonnées d'un vecteur",
                ],
                intuitive_analogy=(
                    "Le produit vectoriel crée un vecteur qui pointe directement vers le haut, "
                    "perpendiculaire à la feuille de papier sur laquelle sont dessinés deux vecteurs."
                ),
                suggested_questions=[
                    "Comment calculer les coordonnées de la somme de deux vecteurs ?",
                ],
            ),
            CurriculumTopic(
                name="Les Probabilités Combinatoires et Variables Aléatoires",
                subject="mathematiques",
                target_class="12eme",
                target_series="TSE / TSExp / TSEco / TSS",
                patterns=[
                    r"\bprobabilites?\s+conditionnelles?\b",
                    r"\bvariable\s+aleatoire\b",
                    r"\bloi\s+binomiale\b",
                    r"\bcombinaisons?\s+et\s+arrangements\b",
                    r"\barbre\s+de\s+probabilite\b",
                ],
                prerequisites=[
                    "Statistiques descriptives simples (effectifs, fréquences, moyenne)",
                    "Notions de pourcentages et proportions",
                ],
                intuitive_analogy=(
                    "Les probabilités permettent de quantifier mathématiquement le hasard et la chance qu'un événement "
                    "se produise lors d'une expérience (tirage de billes, jeu de dés, sondages)."
                ),
                suggested_questions=[
                    "Comment calculer la moyenne et la fréquence d'une série statistique ?",
                    "Comment calculer un pourcentage d'augmentation ou de réduction ?",
                ],
            ),
            CurriculumTopic(
                name="La Chimie Organique Avancée (Esters, Saponification, Acides)",
                subject="chimie",
                target_class="12eme",
                target_series="TSExp / TSE",
                patterns=[
                    r"\besters?\b",
                    r"\besterification\b",
                    r"\bsaponification\b",
                    r"\bacides?\s+carboxyliques?\b",
                    r"\bamides?\b",
                    r"\bamines?\b",
                    r"\banhydride\s+d'acide\b",
                    r"\bchlorure\s+d'acyle\b",
                ],
                prerequisites=[
                    "Familles de composés chimiques élémentaires",
                    "Réactions chimiques de combustion et équilibrage d'équations-bilans",
                ],
                intuitive_analogy=(
                    "La saponification est la réaction magique qui fabrique le savon traditionnel à partir d'huile et de soude !"
                ),
                suggested_questions=[
                    "Comment équilibrer une équation de réaction chimique en 10ème ?",
                ],
            ),
            CurriculumTopic(
                name="La Cinétique Chimique et les Équilibres Acido-Basiques",
                subject="chimie",
                target_class="12eme",
                target_series="TSExp / TSE",
                patterns=[
                    r"\bcinetique\s+chimique\b",
                    r"\bvitesse\s+volumique\b",
                    r"\bconstante\s+d'acidite\b",
                    r"\bpka\b",
                    r"\bproduit\s+ionique\s+de\s+l'eau\b",
                    r"\bdosage\s+ph-?metrique\b",
                    r"\bsolutions?\s+tampons?\b",
                ],
                prerequisites=[
                    "Notion d'acidité et de basicité (pH, papier pH) en 10ème",
                    "Solutions aqueuses et concentration massique",
                ],
                intuitive_analogy=(
                    "La cinétique chimique mesure à quelle vitesse une réaction se produit (comme une allumette qui brûle en 1 seconde vs le fer qui rouille en 1 an)."
                ),
                suggested_questions=[
                    "Quelle est la définition d'une solution acide et d'une solution basique en 10ème ?",
                ],
            ),
            CurriculumTopic(
                name="Les Lois de Newton et la Mécanique Céleste",
                subject="physique",
                target_class="12eme",
                target_series="TSE / TSExp",
                patterns=[
                    r"\blois?\s+de\s+newton\b",
                    r"\btroisieme\s+loi\s+de\s+newton\b",
                    r"\bdeuxieme\s+loi\s+de\s+newton\b",
                    r"\bmouvement\s+de\s+projectiles?\b",
                    r"\bsatellites?\s+et\s+planetes\b",
                    r"\bchute\s+libre\s+parabolique\b",
                ],
                prerequisites=[
                    "Notions de force, poids (P = m.g) et masse en 10ème",
                    "Énergie mécanique, travail et puissance",
                    "Principe de l'équilibre d'un solide soumis à deux ou trois forces",
                ],
                intuitive_analogy=(
                    "Les lois de Newton expliquent pourquoi la Terre tourne autour du Soleil et comment "
                    "calculer exactement la trajectoire d'un ballon tiré en l'air sous l'effet de la pesanteur."
                ),
                suggested_questions=[
                    "Quelle est la différence entre le poids et la masse d'un corps en 10ème ?",
                    "Comment calculer le travail d'une force W = F x d ?",
                ],
            ),
            CurriculumTopic(
                name="Les Circuits Électriques RLC et Oscillations",
                subject="physique",
                target_class="12eme",
                target_series="TSE / TSExp",
                patterns=[
                    r"\bcircuits?\s+rlc\b",
                    r"\bauto-?induction\b",
                    r"\boscillations?\s+electriques\b",
                    r"\bimpédance\b",
                    r"\bcondensateur\s+et\s+bobine\b",
                ],
                prerequisites=[
                    "Loi d'Ohm (U = R.I) et circuits électriques simples en série/dérivation",
                    "Puissance et énergie électrique",
                ],
                intuitive_analogy=(
                    "Un circuit RLC est comme une balançoire électrique : l'énergie oscille continuellement "
                    "entre le condensateur (qui stocke la tension) et la bobine (qui stocke le courant)."
                ),
                suggested_questions=[
                    "Comment appliquer la loi d'Ohm U = R x I dans un circuit simple ?",
                    "Comment calculer la résistance équivalente de dipôles en série et en dérivation ?",
                ],
            ),
            CurriculumTopic(
                name="La Physique Nucléaire, Radioactivité et Énergie de Masse",
                subject="physique",
                target_class="12eme",
                target_series="TSE / TSExp",
                patterns=[
                    r"\bradioactivite\b",
                    r"\bdecroissance\s+radioactive\b",
                    r"\bfission\s+nucleaire\b",
                    r"\bfusion\s+nucleaire\b",
                    r"\bdefaut\s+de\s+masse\b",
                    r"\be\s*=\s*mc\^?2\b",
                    r"\bdemi-?vie\b",
                    r"\bradiations?\s+(alpha|beta|gamma)\b",
                ],
                prerequisites=[
                    "Structure de l'atome (noyau, protons, neutrons, électrons)",
                    "Conservation de la masse et réactions chimiques",
                ],
                intuitive_analogy=(
                    "La radioactivité est la transformation spontanée d'un noyau instable en un noyau plus stable avec libération d'une énergie colossale."
                ),
                suggested_questions=[
                    "De quoi est composé le noyau d'un atome (protons, neutrons) ?",
                ],
            ),
            CurriculumTopic(
                name="La Génétique Formelle et l'Hérédité Humaine",
                subject="biologie",
                target_class="12eme",
                target_series="TSExp (Sciences Expérimentales)",
                patterns=[
                    r"\bgenetique\s+mendelienne\b",
                    r"\bmonohybridisme\b",
                    r"\bdihybridisme\b",
                    r"\bcrossing-?over\b",
                    r"\btransmission\s+des\s+genes\b",
                    r"\bchromosomes?\s+homologues\b",
                    r"\bkaryotype\b",
                    r"\bmeiose\b",
                ],
                prerequisites=[
                    "La cellule et le noyau cellulaire en 10ème",
                    "La reproduction humaine et la fécondation",
                ],
                intuitive_analogy=(
                    "La génétique étudie la façon dont les caractéristiques des parents (comme la couleur des yeux ou du groupe sanguin) "
                    "sont transmises aux enfants via les gènes sur les chromosomes."
                ),
                suggested_questions=[
                    "Quels sont les principaux composants d'une cellule animale et végétale ?",
                    "Comment se déroule la fécondation humaine ?",
                ],
            ),
            CurriculumTopic(
                name="La Biologie Moléculaire (ADN, ARN et Synthèse des Protéines)",
                subject="biologie",
                target_class="12eme",
                target_series="TSExp",
                patterns=[
                    r"\btranscription\s+de\s+l'adn\b",
                    r"\btraduction\s+de\s+l'arn\b",
                    r"\barn\s+messager\b",
                    r"\bcode\s+genetique\b",
                    r"\bribosomes?\b",
                    r"\bmutations?\s+genetiques?\b",
                ],
                prerequisites=[
                    "La cellule et ses organites en 10ème",
                ],
                intuitive_analogy=(
                    "L'ADN est le grand livre de recettes de la vie, l'ARN en est une photocopie de travail, et le ribosome prépare le plat (la protéine) !"
                ),
                suggested_questions=[
                    "Où se trouve le matériel génétique dans la cellule vivante ?",
                ],
            ),
            CurriculumTopic(
                name="L'Immunologie et le Système de Défense de l'Organisme",
                subject="biologie",
                target_class="12eme",
                target_series="TSExp",
                patterns=[
                    r"\bimmunologie\b",
                    r"\bsysteme\s+immunitaire\b",
                    r"\banticorps\b",
                    r"\bantigenes?\b",
                    r"\blymphocytes?\b",
                    r"\bphagocytose\b",
                    r"\bserotherapie\b",
                    r"\bseropositivite\b",
                ],
                prerequisites=[
                    "Les microbes, bactéries et virus en 10ème",
                    "Hygiène et santé",
                ],
                intuitive_analogy=(
                    "Le système immunitaire est l'armée de défense du corps : les globules blancs patrouillent et les anticorps ciblent les intrus."
                ),
                suggested_questions=[
                    "Quelle est la différence entre une bactérie et un virus ?",
                ],
            ),
            # =========================================================
            # NOTIONS DE 11ÈME (SPÉCIALISATION SCIENCES / LETTRES)
            # =========================================================
            CurriculumTopic(
                name="Les Suites Numériques et le Raisonnement par Récurrence",
                subject="mathematiques",
                target_class="11eme",
                target_series="11ème Sciences / 12ème TSE",
                patterns=[
                    r"\braisonnement\s+par\s+recurrence\b",
                    r"\bsuites?\s+numeriques?\b",
                    r"\bsuites?\s+geometriques?\b",
                    r"\bsuites?\s+arithmetiques?\b",
                    r"\blimite\s+de\s+suite\b",
                ],
                prerequisites=[
                    "Fonctions affines et équations du premier degré",
                    "Calcul algébrique et puissances",
                ],
                intuitive_analogy=(
                    "Une suite est comme une chaîne de dominos : on vérifie que le 1er tombe, et que chaque domino fait tomber le suivant !"
                ),
                suggested_questions=[
                    "Qu'est-ce qu'une fonction affine en 10ème ?",
                ],
            ),
            CurriculumTopic(
                name="Les Barycentres et le Produit Scalaire",
                subject="mathematiques",
                target_class="11eme",
                target_series="11ème Sciences",
                patterns=[
                    r"\bbarycentres?\b",
                    r"\bpoints?\s+ponderes?\b",
                    r"\bproduit\s+scalaire\b",
                    r"\bangles?\s+orientes?\b",
                ],
                prerequisites=[
                    "Vecteurs du plan (somme, coordonnées, relation de Chasles)",
                    "Trigonométrie dans le triangle rectangle (sinus, cosinus)",
                ],
                intuitive_analogy=(
                    "Le barycentre est le point d'équilibre exact de plusieurs masses pondérées, "
                    "comme le centre de gravité d'une balance avec des poids différents."
                ),
                suggested_questions=[
                    "Comment utiliser la relation de Chasles avec des vecteurs ?",
                    "Comment calculer la distance entre deux points dans un repère ?",
                ],
            ),
            CurriculumTopic(
                name="L'Électrostatique et la Loi de Coulomb",
                subject="physique",
                target_class="11eme",
                target_series="11ème Sciences",
                patterns=[
                    r"\belectrostatique\b",
                    r"\bloi\s+de\s+coulomb\b",
                    r"\bchamp\s+electrique\b",
                    r"\bcharges?\s+electriques?\s+ponctuelles?\b",
                ],
                prerequisites=[
                    "Structure de l'atome (protons, neutrons, électrons)",
                    "Notion de force et de vecteur force en 10ème",
                ],
                intuitive_analogy=(
                    "La loi de Coulomb explique pourquoi les charges de même signe se repoussent et les charges opposées s'attirent, "
                    "comme des aimants invisibles à l'échelle atomique."
                ),
                suggested_questions=[
                    "Quelle est la composition d'un atome (noyau, électrons) ?",
                    "Qu'est-ce qu'une force et comment la représenter par un vecteur ?",
                ],
            ),
            CurriculumTopic(
                name="La Philosophie et la Dissertation Philosophique",
                subject="philosophie",
                target_class="11eme",
                target_series="11ème / 12ème (Toutes séries)",
                patterns=[
                    r"\bphilosophie\b",
                    r"\bdissertation\s+philosophique\b",
                    r"\binconscient\s+freudien\b",
                    r"\ble\s+cogito\b",
                    r"\bimperatif\s+categorique\b",
                    r"\betat\s+de\s+nature\b",
                ],
                prerequisites=[
                    "Expression écrite, argumentation et analyse de texte en Français (10ème)",
                ],
                intuitive_analogy=(
                    "La philosophie est l'art d'interroger le monde, nos certitudes et nos valeurs par le raisonnement critique."
                ),
                suggested_questions=[
                    "Comment construire une argumentation solide dans une rédaction de français en 10ème ?",
                ],
            ),
        ]

    @staticmethod
    def _normalize_text(text: str) -> str:
        import unicodedata
        nfkd = unicodedata.normalize("NFKD", text)
        no_accents = "".join([c for c in nfkd if not unicodedata.combining(c)])
        return no_accents.lower().strip()

    def check_scope(
        self,
        question: str,
        student_class: str,
        subject: Optional[str] = None,
    ) -> ScopeAnalysisResult:
        """
        Vérifie si la question de l'élève dépasse son niveau scolaire actuel.
        """
        t0 = time.perf_counter()
        current_rank = self.CLASS_RANKS.get(student_class.strip().lower(), 10)
        norm_q = self._normalize_text(question)

        for topic in self.topics_database:
            target_rank = self.CLASS_RANKS.get(topic.target_class.lower(), 12)

            # Vérifier si la notion appartient à une classe strictement supérieure
            if target_rank > current_rank:
                # Vérifier si la question matche un des patterns de la notion
                for pattern in topic.patterns:
                    norm_pat = self._normalize_text(pattern)
                    if re.search(norm_pat, norm_q):
                        guidance = self._build_guidance(
                            student_class=student_class,
                            topic=topic,
                        )
                        dt = time.perf_counter() - t0
                        print(f"\033[36m⏱️  [curriculum_scope.py]\033[0m Notion de niveau supérieur détectée : '{topic.name}' ({topic.target_class}) en \033[1;33m{dt:.4f}s\033[0m")
                        return ScopeAnalysisResult(
                            is_higher_level=True,
                            current_class=student_class,
                            target_class=topic.target_class,
                            target_series=topic.target_series,
                            topic_name=topic.name,
                            subject=topic.subject,
                            prerequisites=topic.prerequisites,
                            intuitive_analogy=topic.intuitive_analogy,
                            suggested_questions=topic.suggested_questions,
                            pedagogical_guidance=guidance,
                        )

        dt = time.perf_counter() - t0
        print(f"\033[36m⏱️  [curriculum_scope.py]\033[0m Cadrage curriculaire vérifié (conforme à la {student_class}) en \033[1;33m{dt:.4f}s\033[0m")
        return ScopeAnalysisResult(
            is_higher_level=False,
            current_class=student_class,
            subject=subject,
        )

    def _build_guidance(
        self,
        student_class: str,
        topic: CurriculumTopic,
    ) -> str:
        """Construit la consigne didactique spécifique injectée au LLM."""
        prereq_str = "\n".join([f"  - {p}" for p in topic.prerequisites])
        sugg_str = "\n".join([f"  - {q}" for q in topic.suggested_questions])

        return (
            f"CADRAGE CURRICULAIRE STRICT — NOTION DE NIVEAU SUPÉRIEUR ({topic.name}) :\n"
            f"L'élève connecté est actuellement en classe de {student_class}.\n"
            f"Cette notion ({topic.name}) appartient officiellement au programme de {topic.target_class} ({topic.target_series}).\n\n"
            f"CONSIGNES OBLIGATOIRES POUR ALTA :\n"
            f"1. Avertissement pédagogique bienveillant : Précise clairement dès ta réponse que cette notion "
            f"({topic.name}) est au programme de {topic.target_class} ({topic.target_series}) et ne fait pas partie du programme de {student_class}.\n"
            f"2. Vulgarisation intuitive et accessible : Donne une explication simple, imagée et intuitive "
            f"(sans formules ni calculs lourds de Terminale). Utilise l'analogie : '{topic.intuitive_analogy}'.\n"
            f"3. Rappel des prérequis de {student_class} à maîtriser d'abord :\n{prereq_str}\n"
            f"4. Questions suggérées adaptées au niveau {student_class} :\n{sugg_str}\n"
        )

