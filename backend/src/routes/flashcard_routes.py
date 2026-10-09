"""
Routes API pour la génération de Flashcards Leitner par l'IA AlternIA (Système Malien).
Connecté à l'orchestrateur LLM et au RAG officiel du DEF et Baccalauréat.
"""

from datetime import datetime
import json
import logging
import re
import time
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.src.services.orchestrator_service import get_orchestrator, normalize_student_class

logger = logging.getLogger("alternia.flashcards")

router = APIRouter(prefix="/api/education/flashcards", tags=["Flashcards Leitner IA"])


def _clean_str(text: Any) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    try:
        return text.encode("utf-16", "surrogatepass").decode("utf-16", "replace").strip()
    except Exception:
        return text.encode("utf-8", "replace").decode("utf-8").strip()


class FlashcardDto(BaseModel):
    id: str
    subject: str
    classLevel: str
    front: str
    back: str
    concept: str
    box: int = 1
    nextReviewDate: str
    repetitionCount: int = 0
    source: str = "ia_alternia"


class FlashcardGenerateRequest(BaseModel):
    subject: str = "Mathématiques"
    class_level: str = "12eme"
    topic: Optional[str] = None
    count: int = 5


@router.post("/generate")
async def api_generate_flashcards(req: FlashcardGenerateRequest) -> List[Dict[str, Any]]:
    """
    Génère dynamiquement un deck de cartes mémo par l'IA AlternIA
    conformément aux épreuves officielles et programmes scolaires maliens.
    """
    subject = req.subject.strip()
    class_level = normalize_student_class(req.class_level)
    topic = req.topic.strip() if req.topic else f"Programme officiel de {subject}"
    count = min(max(req.count, 3), 10)

    system_prompt = (
        "Tu es le Professeur IA d'AlternIA, expert pédagogique des programmes scolaires du Mali (DEF et Baccalauréat malien). "
        "Ta mission est de générer des flashcards (cartes mémo) de très haute qualité pour la méthode de révision espacée Leitner.\n"
        "RÈGLES STRICTES :\n"
        "1. Chaque carte doit avoir un RECTO ('front') concis (question directe, formule à compléter ou notion clé).\n"
        "2. Le VERSO ('back') doit être précis, clair, pédagogique avec la méthode de résolution ou le repère officiel malien.\n"
        "3. Le 'concept' doit résumer le chapitre en 2 ou 3 mots.\n"
        "4. Réponds UNIQUEMENT sous forme d'un tableau JSON contenant des objets avec les clés : 'front', 'back', 'concept'."
    )

    user_prompt = (
        f"Génère exactement {count} flashcards de révision pour le cours suivant :\n"
        f"Matière : {subject}\n"
        f"Niveau scolaire malien : {class_level}\n"
        f"Thème spécifique : {topic}\n\n"
        "Format de sortie attendu : [ {\"front\": \"...\", \"back\": \"...\", \"concept\": \"...\"} ]"
    )

    now_iso = datetime.utcnow().isoformat()
    generated_cards: List[Dict[str, Any]] = []

    # 1. Tentative de génération via l'orchestrateur IA d'AlternIA (LLM + RAG)
    try:
        orchestrator = get_orchestrator()
        if hasattr(orchestrator, "process_message"):
            ai_response = await orchestrator.process_message(
                user_message=user_prompt,
                conversation_id=f"flashcards_{int(time.time())}",
                metadata={"system_override": system_prompt, "target": "flashcards"},
            )
            content = ai_response.get("content", "") if isinstance(ai_response, dict) else str(ai_response)
        elif hasattr(orchestrator, "llm_client") and orchestrator.llm_client:
            import asyncio
            content = await asyncio.to_thread(
                orchestrator.llm_client.generate,
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.25,
                max_tokens=min(count * 90 + 70, 480),
            )
        else:
            content = ""

        def _sanitize_surrogates(text: Any) -> str:
            if text is None:
                return ""
            if not isinstance(text, str):
                text = str(text)
            try:
                return text.encode("utf-16", "surrogatepass").decode("utf-16", "replace").strip()
            except Exception:
                return text.encode("utf-8", "replace").decode("utf-8").strip()

        if content:
            content = _sanitize_surrogates(content)

        def _parse_llm_json(raw: str):
            cleaned = re.sub(r"```(?:json)?\s*", "", raw)
            cleaned = re.sub(r"```\s*", "", cleaned)
            cleaned = re.sub(r"//.*", "", cleaned)
            cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)
            m = re.search(r"\[[\s\S]*\]", cleaned)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
            m_obj = re.search(r"\{[\s\S]*\}", cleaned)
            if m_obj:
                try:
                    obj = json.loads(m_obj.group(0))
                    for k in ["flashcards", "cards", "data", "items"]:
                        if k in obj and isinstance(obj[k], list):
                            return obj[k]
                except Exception:
                    pass
            return None

        json_items = None
        try:
            json_items = _parse_llm_json(content)
        except Exception as parse_err:
            logger.debug(f"[Flashcards] 1er parsing JSON échoué : {parse_err}")

        if json_items and isinstance(json_items, list):
            for i, it in enumerate(json_items):
                if isinstance(it, dict) and "front" in it and "back" in it:
                    card_id = f"fc_ia_{int(time.time())}_{uuid.uuid4().hex[:4]}_{i}"
                    generated_cards.append({
                        "id": _sanitize_surrogates(card_id),
                        "subject": _sanitize_surrogates(subject),
                        "classLevel": _sanitize_surrogates(class_level),
                        "front": _sanitize_surrogates(it["front"]),
                        "back": _sanitize_surrogates(it["back"]),
                        "concept": _sanitize_surrogates(it.get("concept", topic)),
                        "box": 1,
                        "nextReviewDate": now_iso,
                        "repetitionCount": 0,
                        "source": "ia_alternia",
                    })
    except Exception as e:
        logger.warning(f"[Flashcards] Erreur de l'orchestrateur IA : {e}")

    # 2. Si l'IA a généré des cartes, on les retourne immédiatement
    if len(generated_cards) >= 3:
        logger.info(f"[Flashcards] {len(generated_cards)} cartes générées avec succès par l'IA pour {subject} ({class_level})")
        return generated_cards

    # 3. Fallback dynamique certifié conforme au programme malien si LLM non disponible
    logger.info(f"[Flashcards] Utilisation du moteur de secours certifié pour {subject}")
    fallback_deck = _get_curated_cards(subject, class_level, count, now_iso)
    return fallback_deck


def _resolve_subject_category(raw_subject: str) -> str:
    """Catégorise le nom de matière demandé pour correspondre aux référentiels maliens."""
    s = (raw_subject or "").strip().lower()
    if any(k in s for k in ["math", "arithm", "géom", "geom"]):
        return "Mathématiques"
    if any(k in s for k in ["phys", "chim", "pc", "science phys"]):
        return "Physique-Chimie"
    if any(k in s for k in ["svt", "bio", "naturell", "vie et de la terre", "géolog", "geolog"]):
        return "SVT"
    if any(k in s for k in ["hist", "géo", "geo", "h-g", "monde"]):
        return "Histoire-Géographie"
    if any(k in s for k in ["philo"]):
        return "Philosophie"
    if any(k in s for k in ["fran", "litt", "gramm", "lecture", "texte"]):
        return "Français"
    if any(k in s for k in ["ecm", "civ", "moral", "citoyen"]):
        return "ECM"
    if any(k in s for k in ["éco", "eco", "ses", "comptab", "gest"]):
        return "Économie"
    if any(k in s for k in ["socio", "social"]):
        return "Sociologie Générale"
    if any(k in s for k in ["droit", "institut", "jurid"]):
        return "Droit & Institutions"
    if any(k in s for k in ["polit"]):
        return "Science Politique"
    if any(k in s for k in ["angl", "engl"]):
        return "Anglais"
    if any(k in s for k in ["cult", "patrim", "tradit", "monument"]):
        return "Culture"
    return raw_subject.strip() or "Général"


CURATED_CURRICULUM_FLASHCARDS: Dict[str, Dict[str, List[Dict[str, str]]]] = {
    # ── 1. DIPLÔME D'ÉTUDES FONDAMENTALES (DEF / 9ÈME ANNÉE) ─────────────────
    "def": {
        "Mathématiques": [
            {
                "front": "Énoncer le Théorème de Pythagore dans un triangle ABC rectangle en A.",
                "back": "BC² = AB² + AC². Le carré de l'hypoténuse est égal à la somme des carrés des côtés de l'angle droit.",
                "concept": "Théorème de Pythagore",
            },
            {
                "front": "Quelle est la propriété de Thalès pour deux droites sécantes coupées par deux parallèles (BC) // (MN) ?",
                "back": "AM / AB = AN / AC = MN / BC.",
                "concept": "Théorème de Thalès",
            },
            {
                "front": "Comment résoudre dans ℝ l'équation du 1er degré : ax + b = 0 (avec a ≠ 0) ?",
                "back": "ax = -b, d'où x = -b / a. L'ensemble des solutions est S = {-b / a}.",
                "concept": "Équations 1er Degré",
            },
            {
                "front": "Simplifier le produit de racines carrées √(a) × √(b) pour a ≥ 0 et b ≥ 0.",
                "back": "√(a) × √(b) = √(a × b). Exemple : √2 × √8 = √16 = 4.",
                "concept": "Racines Carrées",
            },
            {
                "front": "Que signifie le PGCD de deux entiers et comment le déterminer ?",
                "back": "Le Plus Grand Commun Diviseur. On le calcule avec l'algorithme d'Euclide (divisions successives) ou la décomposition en facteurs premiers.",
                "concept": "Arithmétique & PGCD",
            },
        ],
        "Physique-Chimie": [
            {
                "front": "Donner la formule reliant le poids P et la masse m d'un corps sur Terre.",
                "back": "P = m × g (P en Newtons [N], m en kilogrammes [kg], intensité de la pesanteur g ≈ 9,8 N/kg ou 10 N/kg).",
                "concept": "Poids et Masse",
            },
            {
                "front": "Énoncer la Loi d'Ohm aux bornes d'un résistor de résistance R.",
                "back": "U = R × I (U en Volts [V], R en Ohms [Ω], intensité I en Ampères [A]).",
                "concept": "Loi d'Ohm",
            },
            {
                "front": "Écrire l'équation-bilan de la combustion complète du carbone dans le dioxygène.",
                "back": "C + O₂ → CO₂ (dégagement de dioxyde de carbone qui trouble l'eau de chaux).",
                "concept": "Combustions",
            },
            {
                "front": "À 25°C, quelle est la plage de pH d'une solution acide, neutre et basique ?",
                "back": "pH < 7 : acide ; pH = 7 : neutre (eau pure) ; pH > 7 : basique.",
                "concept": "Acides & Bases",
            },
        ],
        "SVT": [
            {
                "front": "Quel est le rôle vital des globules rouges (hématies) dans le sang humain ?",
                "back": "Transporter le dioxygène (O₂) des poumons vers l'ensemble des organes grâce à l'hémoglobine.",
                "concept": "Circulation Sanguine",
            },
            {
                "front": "Définir la photosynthèse chez les plantes vertes chlorophylliennes.",
                "back": "Production de matière organique (glucose/amidon) à partir d'eau, de sels minéraux et de CO₂ grâce à l'énergie lumineuse, avec rejet d'O₂.",
                "concept": "Photosynthèse",
            },
            {
                "front": "Citer les 3 organes clés où se déroule la digestion des aliments chez l'Homme.",
                "back": "La bouche (mastication et salive), l'estomac (suc gastrique), et l'intestin grêle (suc intestinal et absorption).",
                "concept": "Appareil Digestif",
            },
        ],
        "Histoire-Géographie": [
            {
                "front": "Qui a fondé l'Empire du Mali au XIIIe siècle et après quelle grande bataille ?",
                "back": "Soundiata Keïta, après sa victoire historique à la bataille de Kirina en 1235 contre Soumaoro Kanté du Sosso.",
                "concept": "Empire du Mali & Kirina",
            },
            {
                "front": "Citer les deux grands fleuves qui arrosent la République du Mali.",
                "back": "Le fleuve Niger (le Djoliba, 4 200 km) et le fleuve Sénégal (formé à Bafoulabé).",
                "concept": "Fleuves du Mali",
            },
            {
                "front": "Quels sont les 7 pays frontaliers limitrophes du Mali ?",
                "back": "L'Algérie, la Mauritanie, le Sénégal, la Guinée, la Côte d'Ivoire, le Burkina Faso et le Niger.",
                "concept": "Frontières du Mali",
            },
        ],
        "Français": [
            {
                "front": "Règle d'accord du participe passé employé avec l'auxiliaire 'avoir'.",
                "back": "Il s'accorde en genre et en nombre avec le Complément d'Objet Direct (COD) UNIQUEMENT si celui-ci est placé AVANT le verbe.",
                "concept": "Accord du Participe Passé",
            },
            {
                "front": "Quelle est la différence fondamentale entre une comparaison et une métaphore ?",
                "back": "La comparaison emploie un outil comparatif (comme, pareil à, tel que), tandis que la métaphore associe directement sans outil.",
                "concept": "Figures de Style",
            },
            {
                "front": "Qu'est-ce qu'une proposition subordonnée relative ?",
                "back": "Une proposition introduite par un pronom relatif (qui, que, dont, où, lequel) complétant son nom antécédent.",
                "concept": "Syntaxe & Grammaire",
            },
        ],
        "ECM": [
            {
                "front": "Quelle est la devise nationale officielle de la République du Mali ?",
                "back": "Un Peuple - Un But - Une Foi.",
                "concept": "Devise Nationale",
            },
            {
                "front": "Quelles sont les 3 couleurs du drapeau du Mali et leur signification patriotique ?",
                "back": "Vert (espérance et nature), Or/Jaune (richesses minières et pureté), Rouge (sang versé pour la patrie).",
                "concept": "Drapeau & Symboles",
            },
        ],
    },

    # ── 2. SECONDE / 10ÈME ANNÉE (TRONC COMMUN LYCÉE) ────────────────────────
    "10eme": {
        "Mathématiques": [
            {
                "front": "Donner la formule du discriminant Δ pour l'équation ax² + bx + c = 0.",
                "back": "Δ = b² - 4ac. Si Δ > 0 : 2 racines distinctes (-b ± √Δ)/(2a) ; si Δ = 0 : racine double -b/(2a) ; si Δ < 0 : pas de solution dans ℝ.",
                "concept": "Discriminant Second Degré",
            },
            {
                "front": "Énoncer la relation de Chasles pour le calcul vectoriel.",
                "back": "Pour tous points A, B, C du plan : vecteur AB + vecteur BC = vecteur AC.",
                "concept": "Relation de Chasles",
            },
            {
                "front": "Sens de variation d'une fonction affine f(x) = ax + b sur ℝ.",
                "back": "Si a > 0 : f est strictement croissante. Si a < 0 : f est strictement décroissante. Si a = 0 : f est constante.",
                "concept": "Fonctions Affines",
            },
        ],
        "Physique-Chimie": [
            {
                "front": "Énoncer le Principe d'Inertie (1ère Loi de Newton).",
                "back": "Dans un référentiel galiléen, si la somme des forces extérieures est nulle (Σ F = 0), le centre d'inertie est soit au repos, soit en mouvement rectiligne uniforme.",
                "concept": "Principe d'Inertie",
            },
            {
                "front": "Donner la relation liant quantité de matière n, masse m et masse molaire M.",
                "back": "n = m / M (n en moles [mol], m en grammes [g], M en g/mol).",
                "concept": "Mole & Masse Molaire",
            },
            {
                "front": "Comment calcule-t-on la concentration molaire C d'une solution aqueuse ?",
                "back": "C = n / V (C en mol/L, n en moles [mol], volume V en Litres [L]).",
                "concept": "Concentration Molaire",
            },
        ],
        "SVT": [
            {
                "front": "Quelles sont les 4 phases successives de la mitose cellulaire ?",
                "back": "1. Prophase (condensation de l'ADN), 2. Métaphase (plaque équatoriale), 3. Anaphase (séparation des chromatides), 4. Télophase (cytodiérèse).",
                "concept": "Mitose Cellulaire",
            },
            {
                "front": "Quelles sont les 4 bases azotées de l'ADN et leurs liaisons complémentaires ?",
                "back": "Adénine (A) liée à Thymine (T) par 2 liaisons H ; Guanine (G) liée à Cytosine (C) par 3 liaisons H.",
                "concept": "Structure de l'ADN",
            },
        ],
        "Histoire-Géographie": [
            {
                "front": "Qui a mené la résistance de Sikasso face à la pénétration coloniale française en 1898 ?",
                "back": "Le roi Babemba Traoré du royaume du Kénédougou ('Sayi ni Maloya' : Plutôt la mort que la honte).",
                "concept": "Résistance de Sikasso",
            },
            {
                "front": "Quelle fut la portée historique de la Conférence de Berlin (1884-1885) ?",
                "back": "Elle organisa les règles du partage colonial arbitraire de l'Afrique entre puissances européennes sans les Africains.",
                "concept": "Conférence de Berlin",
            },
        ],
        "Français": [
            {
                "front": "Citer les 4 registres littéraires majeurs.",
                "back": "Tragique (fatalité inexorable), Comique (rire et satire), Lyrique (émotions intimes), Épique (héroïsme collectif).",
                "concept": "Registres Littéraires",
            },
            {
                "front": "Quel est le thème central du roman classique malien 'Sous l'orage' de Seydou Badian ?",
                "back": "Le conflit de générations et le dialogue nécessaire entre traditions africaines et aspirations de la jeunesse instruite.",
                "concept": "Seydou Badian - Sous l'orage",
            },
        ],
    },

    # ── 3. PREMIÈRE / 11ÈME ANNÉE (SCIENCES, LETTRES & ÉCONOMIE) ─────────────
    "11eme": {
        "Mathématiques": [
            {
                "front": "Définition du nombre dérivé f'(a) d'une fonction f en un point a.",
                "back": "f'(a) = lim (h→0) [f(a+h) - f(a)] / h. Il donne la pente de la tangente à la courbe représentative au point d'abscisse a.",
                "concept": "Nombre Dérivé & Tangente",
            },
            {
                "front": "Formule de dérivation du produit de deux fonctions (u × v)'.",
                "back": "(u × v)' = u'·v + u·v'.",
                "concept": "Dérivée de Produit",
            },
            {
                "front": "Relation trigonométrique fondamentale pour tout angle réel x.",
                "back": "cos²(x) + sin²(x) = 1, et tan(x) = sin(x) / cos(x) (pour cos(x) ≠ 0).",
                "concept": "Trigonométrie",
            },
        ],
        "Physique-Chimie": [
            {
                "front": "Expression du travail W d'une force constante F sur un déplacement rectiligne AB.",
                "back": "W_AB(F) = F · AB · cos(α) (W en Joules [J], F en Newtons [N], AB en mètres [m]).",
                "concept": "Travail d'une Force",
            },
            {
                "front": "Définir une réaction d'oxydoréduction.",
                "back": "Réaction avec transfert d'électrons entre un réducteur (donneur d'électrons) et un oxydant (accepteur d'électrons).",
                "concept": "Oxydoréduction",
            },
        ],
        "SVT": [
            {
                "front": "Comment le pancréas régule-t-il la glycémie lors d'une hyperglycémie ?",
                "back": "Sécrétion d'insuline par les cellules β des îlots de Langerhans, stimulant le stockage du glucose en glycogène (foie/muscles).",
                "concept": "Régulation Glycémique",
            },
            {
                "front": "Qu'est-ce que le potentiel d'action d'une fibre nerveuse ?",
                "back": "Une inversion brutale et transitoire de la polarité membranaire (entrée de Na+ puis sortie de K+) se propageant sans atténuation.",
                "concept": "Message Nerveux",
            },
        ],
        "Histoire-Géographie": [
            {
                "front": "Qu'est-ce que le mouvement intellectuel et poétique de la Négritude ?",
                "back": "Créé dans les années 1930 par Aimé Césaire, Léopold Sédar Senghor et Léon-Gontran Damas pour affirmer l'identité, la dignité et la culture noire.",
                "concept": "Mouvement de la Négritude",
            },
            {
                "front": "Quel rôle économique stratégique joue l'Office du Niger au Mali ?",
                "back": "Aménagement hydro-agricole majeur assurant la souveraineté alimentaire en riz et cultures maraîchères le long du fleuve Niger.",
                "concept": "Office du Niger",
            },
        ],
        "Français": [
            {
                "front": "Qu'est-ce que le roman de désillusion post-coloniale en Afrique ?",
                "back": "Courant illustré par 'Les Soleils des Indépendances' d'Ahmadou Kourouma, dénonçant les dérives politiques et la corruption après 1960.",
                "concept": "Ahmadou Kourouma",
            },
            {
                "front": "Les trois composantes d'un texte argumentatif rigoureux.",
                "back": "La thèse (position défendue), les arguments (justifications rationnelles) et les exemples (illustrations concrètes).",
                "concept": "Texte Argumentatif",
            },
        ],
    },

    # ── 4. TERMINALE / 12ÈME ANNÉE (BACCALAURÉAT MALIEN : TSE, TSExp, TLL, TSS, TSEco)
    "12eme": {
        "Mathématiques": [
            {
                "front": "Quelle est la dérivée de f(x) = ln(x) sur ]0, +∞[ ?",
                "back": "f'(x) = 1 / x. Formule générale composée : (ln(u))' = u' / u.",
                "concept": "Dérivées & Logarithmes",
            },
            {
                "front": "Donner la formule de la dérivée d'un quotient f(x) = u(x) / v(x).",
                "back": "f'(x) = (u'·v - u·v') / v².",
                "concept": "Règles de Dérivation",
            },
            {
                "front": "Pour une suite arithmétique de 1er terme u0 et de raison r, exprimer un en fonction de n.",
                "back": "un = u0 + n·r. (Si le 1er terme est u1 : un = u1 + (n-1)·r).",
                "concept": "Suites Arithmétiques",
            },
            {
                "front": "Que vaut la limite en +∞ de (ln x) / x (croissance comparée) ?",
                "back": "lim (x→+∞) (ln x) / x = 0. L'exponentielle l'emporte sur les puissances qui l'emportent sur le logarithme.",
                "concept": "Limites & Croissance Comparée",
            },
            {
                "front": "Dans ℝ, quelle est la primitive de e^(ax) avec a ≠ 0 ?",
                "back": "F(x) = (1/a) · e^(ax) + C.",
                "concept": "Primitives & Intégrales",
            },
            {
                "front": "Forme trigonométrique et exponentielle d'un nombre complexe z = a + ib.",
                "back": "z = r(cos θ + i sin θ) = r e^(iθ), où le module r = √(a² + b²) et θ = arg(z).",
                "concept": "Nombres Complexes",
            },
        ],
        "Physique-Chimie": [
            {
                "front": "Énoncer la relation fondamentale de la dynamique (2ème Loi de Newton).",
                "back": "Σ F_ext = m · a. La somme vectorielle des forces est égale à la masse multipliée par le vecteur accélération.",
                "concept": "2ème Loi de Newton",
            },
            {
                "front": "Quelle est la définition rigoureuse du pH d'une solution aqueuse diluée ?",
                "back": "pH = -log([H3O+]). D'où [H3O+] = 10^(-pH) mol/L.",
                "concept": "Acides & Bases",
            },
            {
                "front": "Donner l'expression de l'énergie cinétique Ec d'un solide de masse m en translation de vitesse v.",
                "back": "Ec = 1/2 · m · v² (en Joules [J]).",
                "concept": "Énergie Mécanique",
            },
            {
                "front": "Quelle est la période propre T0 d'un oscillateur élastique horizontal (masse m - ressort k) ?",
                "back": "T0 = 2π · √(m / k).",
                "concept": "Oscillateurs Mécaniques",
            },
            {
                "front": "Donner la loi de décroissance radioactive d'un échantillon radioactif.",
                "back": "N(t) = N₀ · e^(-λ·t). La demi-vie ou période radioactive est T = ln(2) / λ.",
                "concept": "Radioactivité Nucléaire",
            },
        ],
        "SVT": [
            {
                "front": "Différence fondamentale entre mitose et méiose.",
                "back": "La mitose produit 2 cellules diploïdes (2n) identiques. La méiose produit 4 gamètes haploïdes (n) diversifiés par brassages inter et intrachromosomiques.",
                "concept": "Méiose & Brassages",
            },
            {
                "front": "Qu'est-ce que le crossing-over (brassage intrachromosomique) ?",
                "back": "Échange réciproque de segments de chromatides entre chromosomes homologues appariés en prophase I de méiose.",
                "concept": "Crossing-over Génétique",
            },
        ],
        "Philosophie": [
            {
                "front": "Comment Sigmund Freud conçoit-il la structure de l'appareil psychique ?",
                "back": "En 3 instances : le Ça (pulsions inconscientes), le Moi (médiateur réaliste) et le Surmoi (intériorisation des interdits moraux). 'Le Moi n'est pas maître dans sa propre maison'.",
                "concept": "Conscience & Inconscient",
            },
            {
                "front": "Que signifie la célèbre thèse de Jean-Paul Sartre : 'L'existence précède l'essence' ?",
                "back": "L'homme existe d'abord, se projette dans le monde, et se définit ensuite librement par ses actes. 'L'homme est condamné à être libre'.",
                "concept": "Existentialisme Sartrien",
            },
            {
                "front": "Selon Rousseau dans 'Du Contrat Social', qu'est-ce que la volonté générale ?",
                "back": "L'expression souveraine de l'intérêt commun de tous les citoyens, distincte de la somme des volontés particulières.",
                "concept": "Contrat Social & Politique",
            },
        ],
        "Histoire-Géographie": [
            {
                "front": "À quelle date historique la République du Mali a-t-elle proclamé son indépendance ?",
                "back": "Le 22 septembre 1960 à Bamako, sous la présidence de Modibo Keïta, après la dissolution de la Fédération du Mali.",
                "concept": "Indépendance du Mali (1960)",
            },
            {
                "front": "Quelles sont les bornes chronologiques et la nature de la Guerre Froide ?",
                "back": "1947 à 1991 : rivalité bipolaire (USA vs URSS) sans affrontement militaire direct mondial, marquée par la dissuasion nucléaire et les guerres par procuration.",
                "concept": "Guerre Froide Bipolaire",
            },
            {
                "front": "Qu'est-ce que l'Alliance des États du Sahel (AES) créée par le Mali, le Burkina et le Niger ?",
                "back": "Une confédération souveraine et militaire créée en 2023 pour mutualiser la sécurité, la défense collective et l'intégration économique face aux défis sahéliens.",
                "concept": "Alliance des États du Sahel (AES)",
            },
        ],
        "Économie": [
            {
                "front": "Définition du Produit Intérieur Brut (PIB).",
                "back": "Valeur monétaire totale de tous les biens et services finaux produits sur le territoire économique d'un pays au cours d'une année.",
                "concept": "Produit Intérieur Brut (PIB)",
            },
            {
                "front": "Quel est l'objectif premier de la politique monétaire de la BCEAO au sein de l'UEMOA ?",
                "back": "Garantir la stabilité des prix (maîtrise de l'inflation) et soutenir une croissance économique durable dans les 8 pays membres.",
                "concept": "Politique Monétaire UEMOA",
            },
        ],
    },

    # ── 5. TERMINALE SCIENCE SOCIALE (TSS — PROGRAMME OFFICIEL DU MALI) ──────
    "tss": {
        "Sociologie Générale": [
            {
                "front": "Quelle est la règle méthodologique fondamentale d'Émile Durkheim en sociologie ?",
                "back": "« Traiter les faits sociaux comme des choses ». Les faits sociaux sont extérieurs à l'individu et exercent sur lui une contrainte sociale.",
                "concept": "Méthode Durkheimienne",
            },
            {
                "front": "Différence fondamentale entre sociologie explicative (Durkheim) et sociologie compréhensive (Max Weber).",
                "back": "Durkheim cherche les causes extérieures des faits sociaux (déterminisme social), tandis que Weber interprète le sens subjectif que les individus donnent à leur action sociale (idéal-type).",
                "concept": "Weber vs Durkheim",
            },
            {
                "front": "Définir la socialisation primaire et la socialisation secondaire.",
                "back": "La socialisation primaire se fait pendant l'enfance au sein de la famille et de l'école fondamentale. La socialisation secondaire intervient à l'âge adulte (milieu professionnel, université, pairs).",
                "concept": "Processus de Socialisation",
            },
            {
                "front": "Comment s'organise traditionnellement la stratification sociale en milieu mandingue et sahélien ?",
                "back": "En trois grands ordres : les hommes libres (Horonw), les gens de caste ou artisans dépositaires des savoirs (Nyamakala : forgerons, griots, cordonniers) et historiquement les captifs (Jonw).",
                "concept": "Stratification & Castes au Mali",
            },
        ],
        "Droit & Institutions": [
            {
                "front": "Qu'est-ce que la Constitution au sein de la hiérarchie des normes juridiques ?",
                "back": "La loi fondamentale et suprême d'un État. Elle organise les pouvoirs publics, fixe le fonctionnement des institutions et garantit les droits et libertés des citoyens.",
                "concept": "Constitution de l'État",
            },
            {
                "front": "Énoncer le principe de la séparation des pouvoirs théorisé par Montesquieu.",
                "back": "Séparation stricte entre le pouvoir exécutif (appliquer les lois), le pouvoir législatif (voter les lois) et le pouvoir judiciaire (sanctionner le non-respect des lois) pour éviter toute tyrannie.",
                "concept": "Séparation des Pouvoirs",
            },
            {
                "front": "Qu'est-ce que la pyramide des normes de Hans Kelsen ?",
                "back": "Théorie hiérarchique où chaque norme juridique tire sa validité de la norme supérieure : Constitution > Traités internationaux > Lois votées > Règlements & Décrets > Actes administratifs.",
                "concept": "Pyramide de Kelsen",
            },
            {
                "front": "Quelle est la mission constitutionnelle de la Cour Suprême et de la Cour Constitutionnelle au Mali ?",
                "back": "La Cour Constitutionnelle veille à la conformité des lois avec la Constitution et régule le fonctionnement des institutions. La Cour Suprême est la plus haute juridiction judiciaire et administrative.",
                "concept": "Institutions Judiciaires du Mali",
            },
        ],
        "Science Politique": [
            {
                "front": "Quelle est la définition de l'État donnée par le sociologue Max Weber ?",
                "back": "Une entreprise politique à caractère institutionnel dont la direction revendique avec succès le « monopole de la violence physique légitime » sur un territoire délimité.",
                "concept": "Monopole de la Violence Légitime",
            },
            {
                "front": "Quelles sont les fonctions essentielles d'un parti politique dans une démocratie ?",
                "back": "1. Sélectionner et présenter des candidats aux élections ; 2. Encadrer et éduquer politiquement les citoyens ; 3. Formuler des programmes politiques ; 4. Servir de relais entre peuple et pouvoir.",
                "concept": "Rôle des Partis Politiques",
            },
            {
                "front": "Qu'est-ce que l'Alliance des États du Sahel (AES) regroupant le Mali, le Burkina et le Niger ?",
                "back": "Une confédération géopolitique et de sécurité collective créée en 2023 pour mutualiser la souveraineté, la défense commune contre le terrorisme et l'intégration économique régionale.",
                "concept": "Alliance des États du Sahel (AES)",
            },
        ],
        "Histoire-Géographie": [
            {
                "front": "À quelle date historique la République du Mali a-t-elle proclamé son indépendance ?",
                "back": "Le 22 septembre 1960 à Bamako, sous la direction du président Modibo Keïta, proclamant la souveraineté totale du Mali.",
                "concept": "Indépendance du Mali (1960)",
            },
            {
                "front": "Quelle fut la portée historique de la Charte de Kurukan Fuga proclamée en 1236 au Mali ?",
                "back": "Considérée comme la première constitution des droits humains au monde par Soundiata Keïta : inviolabilité de la vie humaine, paix sociale, protection des femmes et cohésion clanique.",
                "concept": "Charte de Kurukan Fuga",
            },
        ],
        "Philosophie": [
            {
                "front": "Comment Jean-Jacques Rousseau fonde-t-il la légitimité politique dans 'Du Contrat Social' ?",
                "back": "Sur la souveraineté populaire et la « Volonté Générale ». Chaque citoyen renonce à sa liberté naturelle pour acquérir la liberté civile sous l'empire de la loi commune.",
                "concept": "Contrat Social & Volonté Générale",
            },
            {
                "front": "Quelle est la célèbre thèse de Sigmund Freud sur l'inconscient psychique ?",
                "back": "« Le Moi n'est pas maître dans sa propre maison ». La conscience est déterminée en profondeur par le Ça (pulsions refoulées) et le Surmoi (interdits moraux intériorisés).",
                "concept": "Inconscient & Psychanalyse",
            },
        ],
        "Économie": [
            {
                "front": "Quelle est la différence entre croissance économique et développement économique ?",
                "back": "La croissance est quantitative (hausse durable du PIB réel). Le développement est qualitatif (amélioration des conditions de vie, santé, éducation mesurée par l'IDH).",
                "concept": "Croissance vs Développement",
            },
            {
                "front": "Quel est le rôle prépondérant du secteur informel dans l'économie du Mali ?",
                "back": "Il emploie plus de 80 % de la population active, assure la distribution des biens de première nécessité et amortit les chocs sociaux, malgré l'absence de protection sociale formelle.",
                "concept": "Secteur Informel au Mali",
            },
        ],
        "Français": [
            {
                "front": "Quelles sont les trois parties indispensables du plan dialectique en dissertation ?",
                "back": "1. Thèse (défense de l'affirmation) ; 2. Antithèse (nuance ou réfutation argumentée) ; 3. Synthèse (dépassement vers un point de vue enrichi et équilibré).",
                "concept": "Plan Dialectique en Dissertation",
            },
            {
                "front": "Quelle est l'œuvre maîtresse de Seydou Badian et son enseignement central ?",
                "back": "« Sous l'orage » (1957). Elle illustre le dialogue entre la tradition africaine ancestrale et l'émancipation de la jeunesse instruite moderne au Mali.",
                "concept": "Seydou Badian - Sous l'orage",
            },
        ],
        "Anglais": [
            {
                "front": "Translate and explain in English: 'Rule of law and citizenship'.",
                "back": "'État de droit et citoyenneté'. The rule of law means that all citizens and public authorities are accountable to laws that are publicly promulgated and equally enforced.",
                "concept": "Rule of Law & Civic Terms",
            },
        ],
    },

    # ── 6. CULTURE & PATRIMOINE DU MALI (TOUTES CLASSES / TRANCHES D'ÂGE) ────
    "culture": {
        "Culture": [
            {
                "front": "À quelle date la République du Mali a-t-elle proclamé son indépendance ?",
                "back": "Le 22 septembre 1960 à Bamako, sous la présidence du président Modibo Keïta.",
                "concept": "Indépendance du Mali",
            },
            {
                "front": "Quelle bataille décisive de 1235 a vu la victoire fondatrice de Soundiata Keïta ?",
                "back": "La bataille de Kirina contre le roi Soumaoro Kanté du Sosso, posant les fondations de l'Empire du Mali.",
                "concept": "Manding & Kirina",
            },
            {
                "front": "Qu'est-ce que la Charte de Kurukan Fuga proclamée en 1236 au Mali ?",
                "back": "L'un des premiers textes constitutionnels et déclarations des droits humains au monde, instituant la paix civile, le respect de la vie et la justice clanique.",
                "concept": "Charte de Kurukan Fuga",
            },
            {
                "front": "Pourquoi la Grande Mosquée de Djenné est-elle renommée à travers le monde ?",
                "back": "C'est le plus grand monument en terre crue (banco) au monde, chef-d'œuvre de l'architecture soudano-sahélienne classé par l'UNESCO.",
                "concept": "Grande Mosquée de Djenné",
            },
            {
                "front": "Quelle est l'importance des manuscrits anciens conservés à Tombouctou ?",
                "back": "Ils témoignent du rayonnement savant médiéval de l'université Sankoré dans les disciplines comme l'astronomie, les mathématiques, la médecine et le droit.",
                "concept": "Manuscrits de Tombouctou",
            },
        ],
    },
}


def _get_curated_cards(subject: str, class_level: str, count: int, now_iso: str) -> List[Dict[str, Any]]:
    """Générateur de secours haute fidélité certifié pour TOUTES les classes et matières du Mali."""
    norm_class = normalize_student_class(class_level)
    cat = _resolve_subject_category(subject)

    # 1. Recherche par classe et matière
    class_deck = CURATED_CURRICULUM_FLASHCARDS.get(norm_class) or CURATED_CURRICULUM_FLASHCARDS["12eme"]
    chosen_cards: List[Dict[str, str]] = []

    if cat in class_deck:
        chosen_cards = class_deck[cat]
    else:
        # 2. Recherche transversale de la même matière dans les autres classes
        for other_class, other_deck in CURATED_CURRICULUM_FLASHCARDS.items():
            if cat in other_deck:
                chosen_cards = other_deck[cat]
                break

    # 3. Repli si la matière est totalement exotique : première matière de la classe
    if not chosen_cards:
        first_key = next(iter(class_deck.keys()))
        chosen_cards = class_deck[first_key]

    cards: List[Dict[str, Any]] = []
    for i, c in enumerate(chosen_cards[:count]):
        cards.append({
            "id": _clean_str(f"fc_cert_{norm_class}_{i}_{int(time.time())}"),
            "subject": _clean_str(subject),
            "classLevel": _clean_str(norm_class),
            "front": _clean_str(c["front"]),
            "back": _clean_str(c["back"]),
            "concept": _clean_str(c["concept"]),
            "box": 1,
            "nextReviewDate": now_iso,
            "repetitionCount": 0,
            "source": "curriculum_mali_certifie",
        })
    return cards

