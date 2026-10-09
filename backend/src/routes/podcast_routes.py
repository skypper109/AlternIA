"""
Routes API pour la Génération de Podcasts de Révision Pédagogiques AlternIA.
Génération de cours audio structurés (script narratif, chapitres, notions clés)
basés sur le programme officiel malien (DEF et Baccalauréat),
prêts pour la synthèse vocale ultra-réaliste (TTS Vivienne).
"""

import json
import random
import re
import time
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.src.services.orchestrator_service import get_orchestrator, normalize_student_class

router = APIRouter(prefix="/api/education/podcast", tags=["Podcasts de Révision IA"])


# ─────────────────────────────────────────────────────────────────────────────
# 1. MODÈLES PYDANTIC
# ─────────────────────────────────────────────────────────────────────────────

class PodcastChapterDto(BaseModel):
    title: str
    timestamp_seconds: int


class PodcastDto(BaseModel):
    id: str
    title: str
    subject: str
    class_level: str
    duration_minutes: int
    summary: str
    narrator: str = "Professeur IA (AlternIA)"
    chapters: List[PodcastChapterDto]
    key_takeaways: List[str]
    full_script: str
    icon_name: str = "headphones"
    source: str = "ia_alternia"


class PodcastGenerateRequest(BaseModel):
    subject: str = "Mathématiques"
    topic: str = "Les Dérivées et Étude de Fonctions"
    class_level: str = "12eme"
    duration_minutes: int = 6
    student_name: Optional[str] = "Élève"


# ─────────────────────────────────────────────────────────────────────────────
# 2. BANQUE DE COURS PÉDAGOGIQUES DE SECOURS (PROGRAMME MALIEN)
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_SCRIPTS_BANK: Dict[str, Dict[str, Any]] = {
    "Mathématiques": {
        "title": "Maîtriser les Dérivées et les Variations de Fonctions",
        "summary": "Comprends le rôle clé de la dérivée comme coefficient directeur de la tangente et son application directe pour dresser le tableau de variations au Bac malien.",
        "chapters": [
            {"title": "Introduction & Sens intuitif de la dérivée", "timestamp_seconds": 0},
            {"title": "Les formules reines du Bac malien", "timestamp_seconds": 90},
            {"title": "Dressage du tableau de variations sans faute", "timestamp_seconds": 210},
            {"title": "Conseils du correcteur pour le jour J", "timestamp_seconds": 310},
        ],
        "key_takeaways": [
            "La dérivée f'(x) indique la pente de la droite tangente en chaque point.",
            "Si f'(x) > 0 sur un intervalle, f est strictement croissante.",
            "Pour f(x) = ln(u), la formule est f'(x) = u'/u ; pour e^u, c'est u'·e^u.",
            "L'extremum local se trouve toujours là où f' s'annule en changeant de signe.",
        ],
        "full_script": (
            "Bienvenue dans ce podcast de révision AlternIA. Mets tes écouteurs, détends-toi, "
            "et plongeons ensemble dans les mathématiques du Bac malien. Aujourd'hui, nous allons "
            "dompter la notion fondamentale de la dérivée.\n\n"
            "Imagine une moto roulant entre Bamako et Kati. Sa vitesse n'est pas constante : elle accélère dans "
            "les montées et ralentit aux carrefours. La vitesse instantanée affichée sur le compteur à une seconde "
            "précise est exactement ce que représente la dérivée : le taux de variation instantané d'une grandeur.\n\n"
            "Au Bac, le réflexe numéro un est systématique : d'abord préciser l'ensemble de définition et de dérivabilité, "
            "ensuite appliquer rigoureusement les formules de dérivation comme la dérivée d'un produit u fois v, ou d'un quotient u sur v. "
            "Ensuite, étudie toujours le signe de la dérivée avant de dresser le tableau de variations.\n\n"
            "Rappelle-toi : la rigueur mathématique paie toujours. Garde confiance et bon courage pour tes révisions !"
        ),
    },
    "Histoire-Géo": {
        "title": "La Décolonisation et la Naissance de la République du Mali",
        "summary": "Révise les étapes décisives de l'indépendance de 1960, l'éclatement de la Fédération du Mali et la vision panafricaniste du Président Modibo Keïta.",
        "chapters": [
            {"title": "Le contexte de l'après-guerre et la Loi-cadre", "timestamp_seconds": 0},
            {"title": "La Fédération du Mali et son éclatement", "timestamp_seconds": 100},
            {"title": "Le 22 Septembre 1960 et le choix de la souveraineté", "timestamp_seconds": 220},
            {"title": "Bilan historique pour l'épreuve du Bac", "timestamp_seconds": 320},
        ],
        "key_takeaways": [
            "La Loi-cadre Defferre de 1956 amorce l'autonomie interne des colonies de l'AOF.",
            "La Fédération du Mali (Sénégal et Soudan français) éclate en août 1960.",
            "Le 22 septembre 1960, Modibo Keïta proclame l'indépendance totale de la République du Mali.",
            "Le Mali opte pour le non-alignement, le socialisme et l'intégration africaine.",
        ],
        "full_script": (
            "Salutations et bienvenue sur les ondes d'AlternIA. Aujourd'hui en Histoire, nous voyageons "
            "au cœur du vingtième siècle pour revivre un tournant historique majeur du Mali contemporain : "
            "la proclamation de notre souveraineté nationale.\n\n"
            "Après la Seconde Guerre mondiale, le vent de l'émancipation souffle sur toute l'Afrique. Sous l'impulsion "
            "de figures syndicales et politiques comme Modibo Keïta au sein de l'US-RDA, la lutte anticoloniale s'organise. "
            "En 1959, le Soudan français et le Sénégal s'unissent pour former la Fédération du Mali, symbole de l'idéal unitaire africain.\n\n"
            "Cependant, des divergences politiques profondes mènent à l'éclatement de la Fédération dans la nuit du 19 au 20 août 1960. "
            "Face à ce défi historique, le 22 septembre 1960, réuni en congrès extraordinaire, le peuple soudanais proclame la République "
            "du Mali libre, souveraine et indépendante.\n\n"
            "Pour ton épreuve du Bac ou du DEF, structure toujours ta dissertation avec les causes internes et externes, les acteurs clés "
            "et les conséquences géopolitiques durables. Excellente révision avec AlternIA !"
        ),
    },
    "Physique-Chimie": {
        "title": "Les Lois de Newton et le Mouvement des Satellites",
        "summary": "Toutes les clés de la mécanique newtonienne, du principe fondamental de la dynamique jusqu'aux trajectoires orbitales circulaires des satellites.",
        "chapters": [
            {"title": "Les trois lois de Newton revisitées", "timestamp_seconds": 0},
            {"title": "Application du PFD dans le repère de Frenet", "timestamp_seconds": 95},
            {"title": "Vitesse orbitale et période d'un satellite", "timestamp_seconds": 210},
            {"title": "Récapitulatif des pièges classiques au Bac", "timestamp_seconds": 315},
        ],
        "key_takeaways": [
            "Le principe fondamental de la dynamique énonce que la somme des forces extérieures est égale à m · a.",
            "Dans le repère de Frenet, l'accélération normale vaut a_n = v² / R et l'accélération tangentielle a_t = dv/dt.",
            "Pour une trajectoire circulaire uniforme, a_t = 0 et a_n = G · M / R².",
            "La vitesse orbitale est donnée par v = √(G · M / R) et est indépendante de la masse du satellite.",
        ],
        "full_script": (
            "Bienvenue dans ce cours audio AlternIA consacré à la physique céleste et à la mécanique de Newton. "
            "Aujourd'hui, nous décollons vers l'espace pour comprendre comment les satellites gravitent autour de la Terre sans jamais s'écraser.\n\n"
            "Isaac Newton a compris une vérité révolutionnaire : la même force d'attraction gravitationnelle qui fait tomber une mangue d'un arbre "
            "à Sikasso est celle qui maintient la Lune en orbite autour de la Terre.\n\n"
            "Quand un satellite tourne à altitude constante, son mouvement est circulaire et uniforme. En appliquant la deuxième loi de Newton "
            "dans le repère de Frenet, la force de gravitation universelle fournit l'accélération centripète nécessaire pour courber sa trajectoire. "
            "On démontre ainsi la formule clé : vitesse v égale racine carrée de G grand M sur le rayon total de l'orbite.\n\n"
            "Attention au piège classique du Bac : n'oublie jamais d'ajouter le rayon de la Terre R_T à l'altitude h du satellite avant de calculer. "
            "Retiens bien ces formules et bonne réussite dans ton examen !"
        ),
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. ROUTE DE GÉNÉRATION DE PODCAST PAR L'IA
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=PodcastDto)
async def generate_revision_podcast(req: PodcastGenerateRequest):
    """
    Génère un cours audio pédagogique complet (script, chapitres, résumé, notions clés)
    en s'appuyant sur l'orchestrateur d'IA et le programme officiel du Mali.
    """
    subject = req.subject.strip()
    topic = req.topic.strip()
    class_level = req.class_level.strip()
    duration = max(3, min(10, req.duration_minutes))

    system_prompt = (
        "Tu es le Professeur IA d'AlternIA, le système d'excellence éducative au Mali. "
        "Ta mission est de concevoir un podcast de révision audio captivant, didactique et rigoureux "
        "destiné aux lycéens et collégiens du Mali préparant le DEF et le Baccalauréat malien.\n\n"
        "Directives pédagogiques impératives :\n"
        "1. Le ton doit être direct, bienveillant, clair et dynamique comme un vrai animateur radio / tuteur.\n"
        "2. Utilise des analogies parlantes adaptées à la culture et au quotidien malien (fleuve Niger, transports, histoire locale, etc.).\n"
        "3. Fournis des explications précises sur les définitions, formules et méthodes exigées par les correcteurs maliens.\n"
        "4. Réponds STRICTEMENT au format JSON avec les clés suivantes :\n"
        "   - 'title': titre fort et engageant du cours (ex: 'Dompter les Dérivées au Bac malien')\n"
        "   - 'summary': résumé synthétique de 2 phrases\n"
        "   - 'chapters': liste de 3 à 4 chapitres avec 'title' et 'timestamp_seconds' (0, 90, 180, 270)\n"
        "   - 'key_takeaways': liste de 4 phrases résumant les notions incontournables\n"
        "   - 'full_script': script narratif complet d'au moins 350 mots, rédigé en français oralisé fluide sans puces ni astérisques, parfait pour être lu par un moteur de synthèse vocale (TTS)."
    )

    user_prompt = (
        f"Matière : {subject}\n"
        f"Sujet / Chapitre : {topic}\n"
        f"Niveau scolaire malien : {class_level}\n"
        f"Durée cible : {duration} minutes\n"
        f"Nom de l'élève : {req.student_name}\n\n"
        "Génère maintenant le cours de révision en format JSON pur."
    )

    podcast_id = f"gen_pod_{int(time.time())}_{uuid.uuid4().hex[:6]}"

    # 1. Tentative de génération via l'orchestrateur IA d'AlternIA
    try:
        orchestrator = get_orchestrator()
        ai_response = await orchestrator.process_message(
            user_message=user_prompt,
            conversation_id=f"podcast_{podcast_id}",
            metadata={"system_override": system_prompt, "target": "education_podcast"},
        )
        content = ai_response.get("content", "")

        # Extraction JSON
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            data = json.loads(json_match.group(0))
            title = data.get("title", f"Révision : {topic}")
            summary = data.get("summary", f"Synthèse audio sur {topic} pour la classe de {class_level}.")
            raw_chapters = data.get("chapters", [])
            chapters: List[PodcastChapterDto] = []
            if isinstance(raw_chapters, list) and len(raw_chapters) > 0:
                for c in raw_chapters:
                    if isinstance(c, dict):
                        chapters.append(
                            PodcastChapterDto(
                                title=str(c.get("title", "Chapitre")),
                                timestamp_seconds=int(c.get("timestamp_seconds", 0)),
                            )
                        )
            if not chapters:
                chapters = [
                    PodcastChapterDto(title=f"Introduction à {topic}", timestamp_seconds=0),
                    PodcastChapterDto(title="Concepts Clés & Formules", timestamp_seconds=120),
                    PodcastChapterDto(title="Méthode & Réflexe d'Examen", timestamp_seconds=240),
                ]

            key_takeaways = [str(k) for k in data.get("key_takeaways", []) if isinstance(k, str)]
            if not key_takeaways:
                key_takeaways = [
                    f"Comprendre la définition fondamentale de {topic}.",
                    "Maîtriser les formules clés et théorèmes du programme malien.",
                    "Soigner la rédaction méthodique le jour de l'épreuve.",
                ]

            full_script = str(data.get("full_script", "")).strip()
            if len(full_script) > 100:
                return PodcastDto(
                    id=podcast_id,
                    title=title,
                    subject=subject,
                    class_level=class_level,
                    duration_minutes=duration,
                    summary=summary,
                    narrator="Professeur IA (AlternIA)",
                    chapters=chapters,
                    key_takeaways=key_takeaways,
                    full_script=full_script,
                    icon_name=_subject_to_icon(subject),
                    source="ia_alternia",
                )
    except Exception as e:
        # En cas d'erreur de réseau ou d'indisponibilité du LLM, passage au fallback
        pass

    # 2. Générateur de secours intelligent du programme malien
    fallback_data = DEFAULT_SCRIPTS_BANK.get(subject)
    if not fallback_data:
        fallback_data = {
            "title": f"Révision Express : {topic}",
            "summary": f"Le cours audio de référence sur {topic} ({subject}) spécialement vulgarisé pour réussir les examens nationaux maliens.",
            "chapters": [
                {"title": f"Introduction : Pourquoi {topic} est crucial", "timestamp_seconds": 0},
                {"title": "Développement des notions fondamentales", "timestamp_seconds": 90},
                {"title": "Applications pratiques et pièges classiques", "timestamp_seconds": 200},
                {"title": "Conclusion et synthèse pour le Bac", "timestamp_seconds": 300},
            ],
            "key_takeaways": [
                f"Définition précise et rigoureuse de {topic}.",
                f"Formules et théorèmes essentiels en {subject}.",
                "Analyse des sujets des sessions précédentes au Mali.",
                "Structure méthodologique attendue par les professeurs examinateurs.",
            ],
            "full_script": (
                f"Bienvenue dans cette session de révision AlternIA dédiée à {topic} en {subject}. "
                f"Mets tes écouteurs et prépare-toi à assimiler l'essentiel de cette notion pour ton examen.\n\n"
                f"Dans le programme officiel malien de {class_level}, {topic} est un chapitre incontournable qui tombe très fréquemment "
                f"dans les épreuves. Les correcteurs recherchent avant tout la maîtrise des définitions de base, la précision du vocabulaire "
                f"technique et la clarté du raisonnement.\n\n"
                f"Prends le temps de mémoriser les formules directrices. Ne te précipite pas : identifie les hypothèses données dans l'énoncé, "
                f"applique la propriété idoine étape par étape, et encadre ton résultat final avec ses unités de mesure appropriées.\n\n"
                f"Garde ton calme, persévère dans tes exercices réguliers, et fais la différence lors de la session officielle. Bonne révision avec AlternIA !"
            ),
        }

    chapters = [
        PodcastChapterDto(title=c["title"], timestamp_seconds=c["timestamp_seconds"])
        for c in fallback_data["chapters"]
    ]

    return PodcastDto(
        id=podcast_id,
        title=f"{topic} : {fallback_data['title']}" if topic.lower() not in fallback_data['title'].lower() else fallback_data['title'],
        subject=subject,
        class_level=class_level,
        duration_minutes=duration,
        summary=fallback_data["summary"],
        narrator="Professeur IA (AlternIA)",
        chapters=chapters,
        key_takeaways=fallback_data["key_takeaways"],
        full_script=fallback_data["full_script"],
        icon_name=_subject_to_icon(subject),
        source="ia_alternia_offline",
    )


def _subject_to_icon(subject: str) -> str:
    sub = subject.lower()
    if "math" in sub:
        return "calculate"
    if "phys" in sub or "chim" in sub:
        return "science"
    if "hist" in sub or "géo" in sub:
        return "public"
    if "philo" in sub:
        return "psychology"
    if "svt" in sub or "biol" in sub:
        return "biotech"
    if "fran" in sub or "litt" in sub:
        return "menu_book"
    return "headphones"
