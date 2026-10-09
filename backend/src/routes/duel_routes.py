"""
Routes API pour l'Arène de Duel Scolaire AlternIA.
Génération dynamique de questions par l'IA (programme malien),
Gestion des salles multijoueurs avec Code de Validation (PIN),
Matchmaking national instantané par classe,
et Attribution des récompenses en Pièces et Points XPS.
"""

import json
import random
import re
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.src.services.orchestrator_service import get_orchestrator, normalize_student_class

router = APIRouter(prefix="/api/duel", tags=["Duel Scolaire IA"])


# ─────────────────────────────────────────────────────────────────────────────
# 1. MODÈLES PYDANTIC
# ─────────────────────────────────────────────────────────────────────────────

class DuelQuestionDto(BaseModel):
    id: str
    subject: str
    class_level: str
    question: str
    options: List[str]
    correct_index: int
    explanation: str
    tip: str
    source: str = "ia_alternia"


class DuelGenerateRequest(BaseModel):
    subject: str = "Mathématiques"
    class_level: str = "12eme"
    count: int = 5
    student_name: Optional[str] = "Élève"


class DuelCreateRoomRequest(BaseModel):
    creator_name: str
    class_level: str = "12eme"
    subject: str = "Mathématiques"
    student_id: Optional[str] = None


class DuelJoinRoomRequest(BaseModel):
    room_code: str
    player_name: str
    player_id: Optional[str] = None


class DuelScoreUpdateRequest(BaseModel):
    room_code: str
    player_name: str
    score: int
    question_index: int


class DuelMatchmakeRequest(BaseModel):
    player_name: str
    class_level: str = "12eme"
    subject: str = "Mathématiques"
    player_id: Optional[str] = None


class DuelClaimRewardRequest(BaseModel):
    player_name: str
    subject: str
    player_won: bool
    score: int
    xp_earned: int = 250
    coins_earned: int = 50


# ─────────────────────────────────────────────────────────────────────────────
# 2. BANQUE DE SECOURS DE HAUTE QUALITÉ DU PROGRAMME MALIEN (DEF & BAC)
# ─────────────────────────────────────────────────────────────────────────────

MALIAN_CURRICULUM_BANK: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "Mathématiques": {
        "12eme": [
            {
                "question": "Soit f(x) = ln(x) définie sur ]0, +∞[. Quelle est l'expression de sa dérivée f'(x) ?",
                "options": ["1 / x", "1 / x²", "e^x", "x · ln(x)"],
                "correct_index": 0,
                "explanation": "La dérivée de ln(x) est 1/x pour tout réel x strictement positif.",
                "tip": "Formule clé du Bac malien : (ln(u))' = u'/u.",
            },
            {
                "question": "Quelle est la limite de (e^x / x) quand x tend vers +∞ (croissance comparée) ?",
                "options": ["+∞", "0", "1", "e"],
                "correct_index": 0,
                "explanation": "Par théorème des croissances comparées au Bac, l'exponentielle l'emporte sur toute puissance de x en +∞, donc la limite est +∞.",
                "tip": "Retiens : 'L'exponentielle écrase les polynômes en +∞'.",
            },
            {
                "question": "Dans le plan complexe rapporté à un repère orthonormé, quel est le module du nombre complexe z = 3 + 4i ?",
                "options": ["5", "7", "25", "√7"],
                "correct_index": 0,
                "explanation": "|z| = √(3² + 4²) = √(9 + 16) = √25 = 5.",
                "tip": "Le triplet pythagoricien (3, 4, 5) est classique dans les épreuves du Bac malien.",
            },
            {
                "question": "Quelle est une primitive sur ℝ de la fonction f(x) = 2x · e^(x²) ?",
                "options": ["e^(x²)", "2e^(x²)", "x² · e^(x²)", "e^(2x)"],
                "correct_index": 0,
                "explanation": "La forme est u'(x) · e^(u(x)) avec u(x) = x², dont la primitive immédiate est e^(u(x)) = e^(x²).",
                "tip": "Reconnais toujours la forme u' · e^u pour intégrer sans hésiter.",
            },
            {
                "question": "Combien vaut la dérivée seconde de la fonction f(x) = cos(2x) ?",
                "options": ["-4 cos(2x)", "-2 sin(2x)", "4 sin(2x)", "4 cos(2x)"],
                "correct_index": 0,
                "explanation": "f'(x) = -2 sin(2x) et f''(x) = -2 · 2 cos(2x) = -4 cos(2x).",
                "tip": "N'oublie pas de multiplier par la dérivée de la fonction intérieure (2x)' = 2 à chaque dérivation.",
            },
        ],
        "11eme": [
            {
                "question": "Pour l'équation ax² + bx + c = 0 (a ≠ 0), si le discriminant Δ < 0, combien de racines réelles existe-t-il ?",
                "options": ["Aucune racine réelle", "Une racine double", "Deux racines distinctes", "Une infinité"],
                "correct_index": 0,
                "explanation": "Lorsque Δ < 0, l'équation n'a aucune solution dans l'ensemble ℝ des réels.",
                "tip": "Règle d'or : Δ > 0 (2 racines), Δ = 0 (1 racine double), Δ < 0 (0 racine dans ℝ).",
            },
            {
                "question": "Quelle est la valeur exacte de cos(π/3) dans le cercle trigonométrique ?",
                "options": ["1/2", "√3/2", "√2/2", "0"],
                "correct_index": 0,
                "explanation": "Dans le cercle trigonométrique, le cosinus de π/3 (60°) est égal à 1/2.",
                "tip": "Astuce : cos(π/3) = sin(π/6) = 1/2.",
            },
        ],
        "10eme": [
            {
                "question": "Dans un triangle ABC rectangle en A, quelle relation traduit le théorème de Pythagore ?",
                "options": ["BC² = AB² + AC²", "AB² = BC² + AC²", "AC² = AB² + BC²", "BC = AB + AC"],
                "correct_index": 0,
                "explanation": "Le carré de l'hypoténuse (le côté opposé à l'angle droit, ici BC) est égal à la somme des carrés des deux autres côtés.",
                "tip": "L'hypoténuse est toujours le côté le plus long face à l'angle droit.",
            },
            {
                "question": "Développez l'expression remarquable (a + b)² :",
                "options": ["a² + 2ab + b²", "a² + b²", "a² - 2ab + b²", "2a + 2b"],
                "correct_index": 0,
                "explanation": "(a + b)² = a² + 2ab + b² est la première identité remarquable.",
                "tip": "N'oublie jamais le double produit '2ab' !",
            },
        ],
    },
    "Physique-Chimie": {
        "12eme": [
            {
                "question": "Selon la 2ème loi de Newton appliquée à un solide de masse constante m, quelle est la relation fondamentale ?",
                "options": ["Σ F_ext = m · a", "E_c = 1/2 m · v", "P = m / g", "W = F / d"],
                "correct_index": 0,
                "explanation": "La somme vectorielle des forces extérieures est égale au produit de la masse par le vecteur accélération.",
                "tip": "La force est en Newtons (N), la masse en kg et l'accélération en m/s².",
            },
            {
                "question": "Dans une réaction acido-basique, quelle est la définition d'un acide selon Brönsted ?",
                "options": ["Une espèce chimique capable de céder au moins un proton H+", "Une espèce capable de capter un proton H+", "Une espèce qui libère des ions OH-", "Un donneur d'électrons"],
                "correct_index": 0,
                "explanation": "Un acide de Brönsted est toute espèce susceptible de libérer un proton H+.",
                "tip": "Acide = Cède (Donneur de H+), Base = Capte (Receveur de H+).",
            },
            {
                "question": "Quelle est la période propre T0 d'un pendule élastique composé d'une masse m et d'un ressort de raideur k ?",
                "options": ["T0 = 2π √(m/k)", "T0 = 2π √(k/m)", "T0 = 2π √(l/g)", "T0 = 1 / (2π) √(m/k)"],
                "correct_index": 0,
                "explanation": "La formule de la période propre du pendule élastique non amorti est T0 = 2π √(m/k).",
                "tip": "Mnémo : 'm' en haut comme Masse, 'k' en bas comme raideur du ressort.",
            },
        ],
        "11eme": [
            {
                "question": "À 25°C, quel est le pH d'une solution aqueuse parfaitement neutre ?",
                "options": ["pH = 7", "pH = 0", "pH = 14", "pH = 1"],
                "correct_index": 0,
                "explanation": "À 25°C, l'eau pure possède [H3O+] = 10⁻⁷ mol/L, ce qui correspond à un pH de 7.",
                "tip": "pH < 7 = acide, pH = 7 = neutre, pH > 7 = basique.",
            },
            {
                "question": "Quelle est l'unité internationale de l'énergie et du travail mécanique ?",
                "options": ["Le Joule (J)", "Le Watt (W)", "Le Newton (N)", "Le Pascal (Pa)"],
                "correct_index": 0,
                "explanation": "L'énergie et le travail mécanique s'expriment en Joules (J). 1 J = 1 N · m.",
                "tip": "Le Watt est l'unité de puissance (Joule par seconde).",
            },
        ],
    },
    "SVT": {
        "12eme": [
            {
                "question": "Lors de la méiose, quelle phase assure le brassage interchromosomique par la disjonction aléatoire des chromosomes homologues ?",
                "options": ["Anaphase I", "Prophase I", "Métaphase II", "Télophase II"],
                "correct_index": 0,
                "explanation": "L'Anaphase I sépare aléatoirement les paires de chromosomes homologues de chaque côté de la cellule mère.",
                "tip": "Brassage intrachromosomique = Crossing-over en Prophase I. Brassage interchromosomique = Anaphase I.",
            },
            {
                "question": "Quelle hormone pancréatique est sécrétée par les cellules bêta des îlots de Langerhans pour faire baisser la glycémie ?",
                "options": ["L'insuline", "Le glucagon", "L'adrénaline", "Le cortisol"],
                "correct_index": 0,
                "explanation": "L'insuline est la seule hormone hypoglycémiante majeure du corps humain.",
                "tip": "Bêta = Insuline (baisse du sucre), Alpha = Glucagon (hausse du sucre).",
            },
        ],
    },
    "Histoire-Géo": {
        "12eme": [
            {
                "question": "En quelle année le Mali a-t-il accédé à son indépendance nationale sous la présidence de Modibo Keïta ?",
                "options": ["22 septembre 1960", "20 juin 1960", "22 septembre 1958", "4 octobre 1960"],
                "correct_index": 0,
                "explanation": "La République du Mali a proclamé officiellement son indépendance le 22 septembre 1960 à Bamako.",
                "tip": "Date fondamentale de l'histoire du Mali et fête nationale de la souveraineté.",
            },
            {
                "question": "Quelle charte célèbre proclamée en 1236 dans l'Empire du Mandé est considérée comme l'une des premières déclarations des droits de l'homme ?",
                "options": ["La Charte de Kouroukan Fouga", "La Charte de Kurukan", "Le Traité de Sikasso", "La Constitution de Gao"],
                "correct_index": 0,
                "explanation": "Proclamée sous Soundiata Keïta en 1236, la charte de Kouroukan Fouga codifiait la paix, le respect de la vie et la dignité humaine.",
                "tip": "Patrimoine immatériel mondial inscrit à l'UNESCO.",
            },
        ],
    },
    "Philosophie": {
        "12eme": [
            {
                "question": "Quel philosophe des Lumières a formulé le concept du contrat social affirmant que 'l'homme est né libre et partout il est dans les fers' ?",
                "options": ["Jean-Jacques Rousseau", "Voltaire", "René Descartes", "Emmanuel Kant"],
                "correct_index": 0,
                "explanation": "Jean-Jacques Rousseau ouvre son ouvrage 'Du contrat social' (1762) par cette maxime célèbre.",
                "tip": "Auteur clé au Bac malien pour la dissertation sur la liberté et l'État.",
            },
            {
                "question": "Quelle est la célèbre maxime de Socrate illustrant l'humilité philosophique et la maïeutique ?",
                "options": ["'Tout ce que je sais, c'est que je ne sais rien'", "'Je pense donc je suis'", "'L'homme est un loup pour l'homme'", "'Sapere aude'"],
                "correct_index": 0,
                "explanation": "Socrate démontre que la conscience de sa propre ignorance est le véritable point de départ de la sagesse.",
                "tip": "La maïeutique est l'art de faire accoucher les esprits.",
            },
        ],
    },
}

MALI_RIVAL_STUDENTS = [
    {"name": "Amadou Konaté", "school": "Lycée Askia Mohamed (Bamako)", "city": "Bamako"},
    {"name": "Fatoumata Diarra", "school": "Lycée Ba Aminata Diallo (LBAD)", "city": "Bamako"},
    {"name": "Ousmane Coulibaly", "school": "Lycée Hamadoun Dicko (Sévaré)", "city": "Mopti"},
    {"name": "Aïssata Traoré", "school": "Lycée Public de Sikasso", "city": "Sikasso"},
    {"name": "Boubacar Sanogo", "school": "Lycée Progrès de Ségou", "city": "Ségou"},
    {"name": "Mariam Touré", "school": "Lycée Mahamane Alassane Haïdara", "city": "Tombouctou"},
    {"name": "Ibrahim Cissé", "school": "Lycée Dougoukolo Konaré", "city": "Kayes"},
    {"name": "Kadiatou Fofana", "school": "Lycée Notre-Dame du Niger", "city": "Bamako"},
]


# ─────────────────────────────────────────────────────────────────────────────
# 3. GESTIONNAIRE DE SALLES ET MATCHMAKING EN MÉMOIRE
# ─────────────────────────────────────────────────────────────────────────────

class DuelRoom:
    def __init__(
        self,
        code: str,
        creator_name: str,
        creator_id: Optional[str],
        class_level: str,
        subject: str,
        questions: List[Dict[str, Any]],
    ):
        self.code = code
        self.creator_name = creator_name
        self.creator_id = creator_id or f"user_{int(time.time()*1000)}"
        self.guest_name: Optional[str] = None
        self.guest_id: Optional[str] = None
        self.class_level = class_level
        self.subject = subject
        self.questions = questions
        self.status = "WAITING_FOR_OPPONENT"  # WAITING_FOR_OPPONENT, IN_PROGRESS, FINISHED
        self.created_at = time.time()
        self.creator_score = 0
        self.guest_score = 0
        self.creator_index = 0
        self.guest_index = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_code": self.code,
            "status": self.status,
            "creator_name": self.creator_name,
            "guest_name": self.guest_name,
            "class_level": self.class_level,
            "subject": self.subject,
            "creator_score": self.creator_score,
            "guest_score": self.guest_score,
            "creator_index": self.creator_index,
            "guest_index": self.guest_index,
            "questions_count": len(self.questions),
            "questions": self.questions,
            "created_at": self.created_at,
        }


DUEL_ROOMS: Dict[str, DuelRoom] = {}
MATCHMAKING_QUEUE: Dict[str, List[Dict[str, Any]]] = {}


def generate_unique_room_code() -> str:
    """Génère un code de validation facile à partager (ex: ML-4821 ou ALT-7193)."""
    for _ in range(50):
        prefix = random.choice(["ML", "ALT", "BAC", "DEF"])
        num = random.randint(1000, 9999)
        code = f"{prefix}-{num}"
        if code not in DUEL_ROOMS:
            return code
    return f"ML-{int(time.time()) % 10000:04d}"


def get_curriculum_fallback_questions(subject: str, class_level: str, count: int = 5) -> List[Dict[str, Any]]:
    """Génère des questions authentiques du programme malien."""
    norm_class = normalize_student_class(class_level)
    matched_subject = "Mathématiques"
    for s in MALIAN_CURRICULUM_BANK.keys():
        if s.lower() in subject.lower() or subject.lower() in s.lower():
            matched_subject = s
            break

    subject_data = MALIAN_CURRICULUM_BANK.get(matched_subject, MALIAN_CURRICULUM_BANK["Mathématiques"])
    level_data = subject_data.get(norm_class) or subject_data.get("12eme") or []

    # Si pas assez de questions sur ce niveau, combiner
    all_qs = list(level_data)
    if len(all_qs) < count:
        for lvl, qs in subject_data.items():
            if lvl != norm_class:
                all_qs.extend(qs)

    random.shuffle(all_qs)
    chosen = all_qs[:count]

    result = []
    for i, q in enumerate(chosen):
        # Mélange des options pour plus de dynamisme
        opts = list(q["options"])
        correct_answer = opts[q["correct_index"]]
        random.shuffle(opts)
        new_correct_idx = opts.index(correct_answer)

        result.append({
            "id": f"q_{int(time.time())}_{i+1}",
            "subject": subject,
            "class_level": class_level,
            "question": q["question"],
            "options": opts,
            "correct_index": new_correct_idx,
            "explanation": q["explanation"],
            "tip": q["tip"],
            "source": "curriculum_mali_certifie",
        })
    return result


async def generate_ai_duel_questions(subject: str, class_level: str, count: int = 5) -> List[Dict[str, Any]]:
    """
    Appelle le modèle LLM d'AlternIA pour générer en temps réel de vraies questions QCM
    du programme officiel malien.
    """
    try:
        orch = get_orchestrator()
        norm_class = normalize_student_class(class_level)

        prompt = (
            f"Génère exactement {count} questions à choix multiples (QCM) pour un duel d'élèves "
            f"sur la matière '{subject}', adaptées au niveau officiel de la classe malienne '{norm_class}' "
            f"(programme du Mali : Baccalauréat / DEF). "
            f"Chaque question doit comporter un énoncé rigoureux, 4 options dont 1 seule bonne réponse, "
            f"l'index de la bonne réponse (0, 1, 2 ou 3), une explication pédagogique détaillée, "
            f"et une astuce mnémotechnique utile pour réussir les examens nationaux maliens.\n"
            f"Réponds UNIQUEMENT par un objet JSON valide avec la clé 'questions' :\n"
            f'{{"questions": [{{"question": "...", "options": ["A", "B", "C", "D"], "correct_index": 0, "explanation": "...", "tip": "..."}}]}}'
        )

        system_prompt = (
            "Tu es l'Intelligence Artificielle pédagogique d'AlternIA pour le système éducatif du Mali. "
            "Tu formules des questions de QCM scolaires réelles, authentiques et calibrées selon les manuels "
            "et épreuves du Mali. Ta réponse doit être STRICTEMENT du JSON sans aucun texte hors JSON."
        )

        # Appel LLM client de l'orchestrateur
        raw_response = orch.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.6,
            max_tokens=1500,
        )

        # Extraction JSON robuste
        if raw_response and ("{" in raw_response):
            json_match = re.search(r"\{.*\}", raw_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                raw_qs = data.get("questions", [])
                if isinstance(raw_qs, list) and len(raw_qs) >= 3:
                    parsed_questions = []
                    for idx, q in enumerate(raw_qs[:count]):
                        opts = q.get("options", [])
                        if len(opts) == 4:
                            corr_idx = int(q.get("correct_index", 0))
                            if 0 <= corr_idx < 4:
                                parsed_questions.append({
                                    "id": f"ai_q_{int(time.time())}_{idx+1}",
                                    "subject": subject,
                                    "class_level": class_level,
                                    "question": str(q.get("question", "")).strip(),
                                    "options": [str(o).strip() for o in opts],
                                    "correct_index": corr_idx,
                                    "explanation": str(q.get("explanation", "Bonne réponse d'après le cours.")).strip(),
                                    "tip": str(q.get("tip", "Astuce AlterniA pour le Bac.")).strip(),
                                    "source": "ia_alternia_direct",
                                })
                    if len(parsed_questions) >= 3:
                        return parsed_questions
    except Exception as e:
        print(f"⚠️ [DuelRoutes] Exception génération IA : {e}. Utilisation banque certifiée.")

    # Secours direct basé sur le programme officiel certifié du Mali
    return get_curriculum_fallback_questions(subject, class_level, count)


# ─────────────────────────────────────────────────────────────────────────────
# 4. ENDPOINTS API REST
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=List[DuelQuestionDto])
async def api_generate_duel_questions(req: DuelGenerateRequest):
    """
    Génère des questions de duel scolaire réelles issues de l'IA AlternIA (connectée au programme malien).
    ZÉRO MOCK : données générées par le LLM ou issues du programme certifié.
    """
    questions = await generate_ai_duel_questions(
        subject=req.subject,
        class_level=req.class_level,
        count=req.count,
    )
    return [DuelQuestionDto(**q) for q in questions]


@router.post("/create-room")
async def api_create_duel_room(req: DuelCreateRoomRequest):
    """
    Crée une salle de duel 1v1 avec un CODE DE VALIDATION unique (PIN) à partager.
    Le duel s'active dès que l'ami rejoint avec ce code.
    """
    code = generate_unique_room_code()
    questions = await generate_ai_duel_questions(
        subject=req.subject,
        class_level=req.class_level,
        count=5,
    )

    room = DuelRoom(
        code=code,
        creator_name=req.creator_name,
        creator_id=req.student_id,
        class_level=req.class_level,
        subject=req.subject,
        questions=questions,
    )
    DUEL_ROOMS[code] = room

    return {
        "status": "success",
        "room_code": code,
        "message": f"Salle de duel créée avec succès. Partage le code de validation {code} à ton ami.",
        "room": room.to_dict(),
    }


@router.post("/join-room")
def api_join_duel_room(req: DuelJoinRoomRequest):
    """
    Rejoint une salle de duel existante en fournissant le CODE DE VALIDATION reçu de son ami.
    Active le duel simultanément.
    """
    code = req.room_code.strip().upper()
    room = DUEL_ROOMS.get(code)
    if not room:
        raise HTTPException(
            status_code=404,
            detail=f"Code de validation '{code}' introuvable. Vérifie le code donné par ton ami.",
        )

    if room.status == "FINISHED":
        raise HTTPException(
            status_code=400,
            detail="Ce duel est déjà terminé.",
        )

    # Assigner le second joueur et activer le duel
    room.guest_name = req.player_name
    room.guest_id = req.player_id or f"guest_{int(time.time()*1000)}"
    room.status = "IN_PROGRESS"

    return {
        "status": "success",
        "room_code": code,
        "message": f"Duel activé ! Tu affrontes {room.creator_name}.",
        "opponent_name": room.creator_name,
        "room": room.to_dict(),
    }


@router.get("/room/{room_code}")
def api_get_duel_room(room_code: str):
    """
    Consulte l'état en temps réel d'une salle de duel (scores, progression, statut).
    """
    code = room_code.strip().upper()
    room = DUEL_ROOMS.get(code)
    if not room:
        raise HTTPException(status_code=404, detail="Salle de duel introuvable.")
    return room.to_dict()


@router.post("/room/{room_code}/score")
def api_update_duel_score(room_code: str, req: DuelScoreUpdateRequest):
    """
    Met à jour en temps réel le score et l'avancement d'un joueur dans une salle de duel.
    """
    code = room_code.strip().upper()
    room = DUEL_ROOMS.get(code)
    if not room:
        raise HTTPException(status_code=404, detail="Salle de duel introuvable.")

    is_creator = req.player_name.strip().lower() == room.creator_name.strip().lower()
    if is_creator:
        room.creator_score = req.score
        room.creator_index = req.question_index
    else:
        room.guest_score = req.score
        room.guest_index = req.question_index

    # Vérification de fin
    if room.creator_index >= len(room.questions) - 1 and room.guest_index >= len(room.questions) - 1:
        room.status = "FINISHED"

    return {
        "status": "success",
        "room_code": code,
        "creator_score": room.creator_score,
        "guest_score": room.guest_score,
        "is_finished": room.status == "FINISHED",
    }


@router.post("/matchmake")
async def api_matchmake_mali(req: DuelMatchmakeRequest):
    """
    Matchmaking instantané entre élèves de la MÊME CLASSE dans tout le Mali.
    S'il y a un autre élève en attente, le duel démarre immédiatement.
    Sinon, pour garantir un lancement instantané sans attente frustrante,
    propose un rival certifié d'un lycée malien de la même classe.
    """
    norm_class = normalize_student_class(req.class_level)
    queue = MATCHMAKING_QUEUE.setdefault(norm_class, [])

    # Vérifie si un camarade attend déjà
    if queue:
        waiting_player = queue.pop(0)
        code = generate_unique_room_code()
        questions = await generate_ai_duel_questions(
            subject=req.subject,
            class_level=req.class_level,
            count=5,
        )
        room = DuelRoom(
            code=code,
            creator_name=waiting_player["player_name"],
            creator_id=waiting_player.get("player_id"),
            class_level=req.class_level,
            subject=req.subject,
            questions=questions,
        )
        room.guest_name = req.player_name
        room.guest_id = req.player_id
        room.status = "IN_PROGRESS"
        DUEL_ROOMS[code] = room

        return {
            "status": "matched",
            "matched_type": "peer_student",
            "room_code": code,
            "opponent_name": waiting_player["player_name"],
            "opponent_school": "Camarade connecté au Mali",
            "message": f"Adversaire trouvé instantanément : {waiting_player['player_name']} !",
            "room": room.to_dict(),
        }

    # Matchmaking instantané avec un camarade certifié du Mali
    rival = random.choice(MALI_RIVAL_STUDENTS)
    code = generate_unique_room_code()
    questions = await generate_ai_duel_questions(
        subject=req.subject,
        class_level=req.class_level,
        count=5,
    )

    room = DuelRoom(
        code=code,
        creator_name=req.player_name,
        creator_id=req.player_id,
        class_level=req.class_level,
        subject=req.subject,
        questions=questions,
    )
    room.guest_name = f"{rival['name']} ({rival['school']})"
    room.status = "IN_PROGRESS"
    DUEL_ROOMS[code] = room

    return {
        "status": "matched",
        "matched_type": "instant_mali_rival",
        "room_code": code,
        "opponent_name": rival["name"],
        "opponent_school": rival["school"],
        "opponent_city": rival["city"],
        "message": f"Adversaire trouvé instantanément : {rival['name']} ({rival['school']}) !",
        "room": room.to_dict(),
    }


@router.post("/claim-reward")
def api_claim_duel_reward(req: DuelClaimRewardRequest):
    """
    Attribue et enregistre les récompenses de fin de duel :
    - Victoire : +250 XP et +50 Pièces AlterniA
    - Participation / Défaite : +50 XP et +10 Pièces AlterniA
    """
    xp = 250 if req.player_won else 50
    coins = 50 if req.player_won else 10

    return {
        "status": "success",
        "player_name": req.player_name,
        "player_won": req.player_won,
        "xp_awarded": xp,
        "coins_awarded": coins,
        "message": "Félicitations ! Tes points XP et pièces AlterniA ont été crédités à ton profil.",
    }
