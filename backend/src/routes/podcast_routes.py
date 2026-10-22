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
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.src.services.document_extractor_service import extraire_texte_document
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


def sanitize_french_educational_text(text: str) -> str:
    """
    Nettoie et sécurise un texte pédagogique pour garantir une pureté totale
    de la langue française (zéro caractère chinois/CJK, zéro hallucination linguistique).
    """
    if not text:
        return ""
    # 1. Remplacement de l'hallucination chinoise sur le symbole 'O' (oxygène)
    text = re.sub(
        r"[-\s]*O\s*代表的是汉字[^\n\.]*[\.\n]?",
        "\n- O représente l'atome d'oxygène (et O2 la molécule de dioxygène).\n",
        text,
    )
    text = re.sub(
        r"^[-\s]*O\s*代表.*$",
        "- O représente l'atome d'oxygène (et O2 la molécule de dioxygène).",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(r"让我们继续翻译[^\n\.]*[\.\n]?", "", text)

    # 2. Élimination complète de tous les caractères CJK (Chinois, Japonais, Coréen)
    text = re.sub(
        r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff\u3040-\u30ff\u3000-\u303f\uff00-\uffef]+",
        "",
        text,
    )

    # 3. Suppression des méta-phrases en anglais (hors cours d'anglais)
    text = re.sub(
        r"(?i)\b(here is the (script|podcast)|sure, here is|let's continue to translate)\b[^\n]*",
        "",
        text,
    )

    # 4. Correction des coquilles fréquentes de traduction
    text = re.sub(r"\bmol[ée]cule d'oxygen\b", "molécule d'oxygène", text, flags=re.IGNORECASE)
    text = re.sub(r"\bdeux mol[ée]cull?es\b", "deux molécules", text, flags=re.IGNORECASE)

    # 5. Nettoyage des lignes orphelines (ex: tirets orphelins après suppression de texte)
    text = re.sub(r"^\s*[-*•]\s*$", "", text, flags=re.MULTILINE)

    # 6. Normalisation des sauts de ligne multiples et espaces
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


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
        "Directives linguistiques et pédagogiques impératives :\n"
        "1. RÈGLE LINGUISTIQUE STRICTE : Rédige STRICTEMENT et EXCLUSIVEMENT en FRANÇAIS. "
        "AUCUN caractère chinois (Hanzi / CJK), AUCUN mot en anglais sauf pour le cours d'anglais. "
        "Ne traduis JAMAIS les symboles chimiques ou mathématiques en idéogrammes ou en anglais. "
        "Pour 'O' (oxygène), 'H' (hydrogène), formule '2H2 + O2 -> 2H2O', décris tout en français limpide.\n"
        "2. Aucun méta-commentaire de modèle (ne dis jamais 'continuons de traduire ce script', 'voici le script', etc.).\n"
        "3. Le ton doit être direct, apaisant, bienveillant, clair et dynamique comme un vrai animateur radio / tuteur.\n"
        "4. Utilise des analogies parlantes adaptées à la culture et au quotidien malien (fleuve Niger, transports, histoire locale, etc.).\n"
        "5. Fournis des explications précises sur les définitions, formules et méthodes exigées par les correcteurs maliens.\n"
        "6. Réponds STRICTEMENT au format JSON avec les clés suivantes :\n"
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
        if hasattr(orchestrator, "process_message"):
            ai_response = await orchestrator.process_message(
                user_message=user_prompt,
                conversation_id=f"podcast_{podcast_id}",
                metadata={"system_override": system_prompt, "target": "education_podcast", "max_tokens": 4096},
            )
            content = ai_response.get("content", "") if isinstance(ai_response, dict) else str(ai_response)
        elif hasattr(orchestrator, "llm_client") and orchestrator.llm_client:
            import asyncio
            content = await asyncio.to_thread(
                orchestrator.llm_client.generate,
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
            )
        else:
            content = ""

        # Extraction JSON robuste
        full_script = ""
        title = f"Révision : {topic}"
        summary = f"Synthèse audio sur {topic} pour la classe de {class_level}."
        chapters: List[PodcastChapterDto] = []
        key_takeaways: List[str] = []

        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            try:
                raw_json = json_match.group(0)
                cleaned_json = re.sub(r"//.*", "", raw_json)
                # Nettoyage des virgules traînantes
                cleaned_json = re.sub(r",\s*([\}\]])", r"\1", cleaned_json)
                data = json.loads(cleaned_json, strict=False)
                title = data.get("title", title)
                summary = data.get("summary", summary)
                raw_chapters = data.get("chapters", [])
                if isinstance(raw_chapters, list) and len(raw_chapters) > 0:
                    for c in raw_chapters:
                        if isinstance(c, dict):
                            chapters.append(
                                PodcastChapterDto(
                                    title=str(c.get("title", "Chapitre")),
                                    timestamp_seconds=int(c.get("timestamp_seconds", 0)),
                                )
                            )
                key_takeaways = [str(k) for k in data.get("key_takeaways", []) if isinstance(k, str)]
                full_script = str(data.get("full_script", "")).strip()
            except Exception:
                pass

        # Secours regex ultra-robuste si le JSON est incomplet ou tronqué
        if not full_script:
            script_match = re.search(r'"full_script"\s*:\s*"([\s\S]*?)(?:"\s*,\s*"\w+"|"\}|$)', content)
            if script_match:
                extracted = script_match.group(1).replace(r'\"', '"').replace(r'\n', '\n').strip()
                if len(extracted) > 60:
                    full_script = extracted

        if title == f"Révision : {topic}":
            title_match = re.search(r'"title"\s*:\s*"([^"\n]+)"', content)
            if title_match:
                title = title_match.group(1).strip()

        if summary == f"Synthèse audio sur {topic} pour la classe de {class_level}.":
            sum_match = re.search(r'"summary"\s*:\s*"([^"\n]+)"', content)
            if sum_match:
                summary = sum_match.group(1).strip()

        if not chapters:
            chap_matches = re.findall(r'\{\s*"title"\s*:\s*"([^"]+)"\s*,\s*"timestamp_seconds"\s*:\s*(\d+)\s*\}', content)
            for ct, cts in chap_matches:
                chapters.append(PodcastChapterDto(title=ct, timestamp_seconds=int(cts)))

        if not key_takeaways:
            kt_match = re.search(r'"key_takeaways"\s*:\s*\[([\s\S]*?)\]', content)
            if kt_match:
                raw_items = re.findall(r'"([^"\n]+)"', kt_match.group(1))
                key_takeaways = [it.strip() for it in raw_items if len(it.strip()) > 5]

        # Si le full_script n'était pas explicite dans le JSON, on formate la narration IA
        if not full_script and summary and len(summary) > 20:
            chapter_points = "\n".join([f"• {c.title}" for c in chapters]) if chapters else f"• Les bases indispensables de {topic}"
            full_script = (
                f"Bonjour et bienvenue dans ton podcast de révision AlternIA !\n"
                f"Aujourd'hui, nous explorons ensemble un chapitre clé de {subject} pour ta classe de {class_level} : {topic}.\n\n"
                f"{summary}\n\n"
                f"Dans cette leçon, nous développons les points majeurs du programme malien :\n{chapter_points}\n\n"
                f"Rappelle-toi : la régularité et la rigueur dans tes révisions font la différence pour réussir les examens nationaux au Mali. "
                f"Garde confiance en toi et révise régulièrement avec ton assistant AlternIA !"
            )

        # Si le LLM a généré du texte direct hors JSON
        if not full_script and len(content.strip()) > 80:
            cleaned_text = re.sub(r"```[a-zA-Z]*", "", content)
            cleaned_text = cleaned_text.replace("```", "").strip()
            full_script = cleaned_text.strip()

        if len(full_script) > 80:
            if not chapters:
                chapters = [
                    PodcastChapterDto(title=f"Introduction à {topic}", timestamp_seconds=0),
                    PodcastChapterDto(title="Développement & Notions Clés", timestamp_seconds=120),
                    PodcastChapterDto(title="Méthodologie pour le Bac malien", timestamp_seconds=240),
                ]
            if not key_takeaways:
                key_takeaways = [
                    f"Comprendre la définition fondamentale de {topic} en {subject}.",
                    "Maîtriser les règles et notions exigées par les inspecteurs du Mali.",
                    "Soigner la structure méthodologique le jour de l'épreuve.",
                    "S'entraîner régulièrement avec les podcasts et quiz AlternIA.",
                ]
            return PodcastDto(
                id=podcast_id,
                title=sanitize_french_educational_text(title),
                subject=subject,
                class_level=class_level,
                duration_minutes=duration,
                summary=sanitize_french_educational_text(summary),
                narrator="Professeur IA (AlternIA)",
                chapters=[
                    PodcastChapterDto(
                        title=sanitize_french_educational_text(c.title),
                        timestamp_seconds=c.timestamp_seconds,
                    )
                    for c in chapters
                ],
                key_takeaways=[sanitize_french_educational_text(k) for k in key_takeaways],
                full_script=sanitize_french_educational_text(full_script),
                icon_name=_subject_to_icon(subject),
                source="ia_alternia",
            )
    except Exception as e:
        print(f"⚠️ [PodcastRoutes] Erreur génération IA : {e}. Utilisation du cours certifié.")

    # 2. Générateur de secours intelligent du programme malien (strictement adapté à la matière)
    sub_lower = subject.lower()
    if any(k in sub_lower for k in ["litt", "fran"]):
        script_text = (
            f"Bienvenue dans ce podcast de révision AlternIA consacré à {topic} en {subject}.\n\n"
            f"En classe de {class_level}, la littérature et l'expression française exigent une analyse méthodique rigoureuse. "
            f"Quand tu abordes une dissertation littéraire ou un commentaire de texte au Mali, ne te contente jamais de raconter l'histoire. "
            f"Dégage la problématique centrale de l'auteur, repère les figures de style, le registre de langue et les procédés rhétoriques "
            f"qui soutiennent la pensée de l'écrivain.\n\n"
            f"Pour l'épreuve d'examen : structure toujours ton devoir avec une introduction claire (amorce, présentation du texte, problématique "
            f"et annonce du plan), des transitions soignées entre tes parties, et une conclusion qui ouvre sur un élargissement pertinent.\n\n"
            f"Soigne particulièrement la syntaxe, l'orthographe et la richesse du vocabulaire pour maximiser tes points. Bonnes révisions avec AlternIA !"
        )
        chaps = [
            {"title": f"Introduction & Problématique de {topic}", "timestamp_seconds": 0},
            {"title": "Analyse Textuelle & Figures de Style", "timestamp_seconds": 90},
            {"title": "Méthode du Commentaire & Dissertation", "timestamp_seconds": 180},
            {"title": "Conseils de Rédaction pour l'Examen", "timestamp_seconds": 270},
        ]
        takeaways = [
            f"Identifier les thèmes majeurs et la vision de l'auteur dans {topic}.",
            "Analyser la forme : syntaxe, figures de style et tonalité du texte.",
            "Construire une argumentation structurée avec des citations précises.",
            "Soigner impérativement l'expression écrite pour décrocher la mention.",
        ]
    elif any(k in sub_lower for k in ["hist", "géo"]):
        script_text = (
            f"Bienvenue dans cette session de révision audio sur {topic} en {subject}.\n\n"
            f"Pour les épreuves de {class_level} au Mali, la réussite en histoire-géographie repose sur la précision des repères "
            f"chronologiques et spatiaux. Ne récite pas des faits isolés : mets en évidence les relations de cause à effet, les dynamiques "
            f"économiques, politiques et sociales qui expliquent les évolutions étudiées.\n\n"
            f"Le jour de l'examen, définis clairement les termes du sujet dans l'introduction, organise ton plan de manière équilibrée "
            f"et illustre chacune de tes sous-parties par des exemples précis et des faits historiques ou données géographiques avérées.\n\n"
            f"Révise régulièrement les cartes et les synthèses de cours AlternIA pour faire la différence le jour J !"
        )
        chaps = [
            {"title": f"Contexte Historique & Enjeux de {topic}", "timestamp_seconds": 0},
            {"title": "Causes et Dynamiques Majeures", "timestamp_seconds": 90},
            {"title": "Conséquences & Bilan pour le Mali", "timestamp_seconds": 180},
            {"title": "Méthode d'Examen en Histoire-Géo", "timestamp_seconds": 270},
        ]
        takeaways = [
            f"Maîtriser les dates clés et les repères spatiaux de {topic}.",
            "Expliquer les causalités historiques et géographiques sous-jacentes.",
            "Illustrer l'argumentation par des faits précis du programme malien.",
            "Rédiger une conclusion synthétique ouvrant sur les perspectives actuelles.",
        ]
    elif any(k in sub_lower for k in ["socio", "social"]):
        script_text = (
            f"Bienvenue dans ce cours audio AlternIA consacré à {topic} en {subject} pour la classe de {class_level}.\n\n"
            f"En sociologie au Baccalauréat malien, la clé consiste à distinguer le sens commun de la démarche scientifique rigoureuse. "
            f"Comme l'enseignait Émile Durkheim, nous devons traiter les faits sociaux comme des choses, en analysant les contraintes collectives "
            f"qui s'exercent sur les individus, tout en comprenant avec Max Weber le sens que les acteurs donnent à leurs actions.\n\n"
            f"Pour ton épreuve d'examen : relie toujours les théories de la socialisation et de la stratification sociale aux réalités concrètes "
            f"du Mali, notamment l'évolution de la cellule familiale, les dynamiques communautaires et les transformations urbaines.\n\n"
            f"Définis soigneusement tes concepts clés dès l'introduction et illustre chaque thèse par des enquêtes sociologiques probantes."
        )
        chaps = [
            {"title": f"Introduction & Définition Sociologique de {topic}", "timestamp_seconds": 0},
            {"title": "Courants Théoriques & Auteurs Fondateurs", "timestamp_seconds": 90},
            {"title": "Analyse Empirique & Réalités du Mali", "timestamp_seconds": 180},
            {"title": "Méthode d'Examen & Conseils pour la Dissertation", "timestamp_seconds": 270},
        ]
        takeaways = [
            f"Maîtriser la définition scientifique et les enjeux de {topic}.",
            "Confronter la sociologie explicative (Durkheim) et compréhensive (Weber).",
            "Illustrer l'analyse par des exemples précis de la société malienne.",
            "Rédiger une argumentation sociologique rigoureuse et exempte de jugements de valeur.",
        ]
    elif any(k in sub_lower for k in ["droit", "institut", "jurid"]):
        script_text = (
            f"Bienvenue dans cette session audio AlternIA sur {topic} en {subject} pour ta classe de {class_level}.\n\n"
            f"L'étude du droit et des institutions repose sur la précision du vocabulaire juridique et la maîtrise de la hiérarchie des normes. "
            f"Au sommet de l'édifice juridique se trouve la Constitution, qui garantit la séparation des pouvoirs théorisée par Montesquieu "
            f"et protège les libertés fondamentales de chaque citoyen malien.\n\n"
            f"Le jour de l'épreuve : commence par définir le cadre juridique applicable, cite les textes de référence et déroule un raisonnement "
            f"structuré en qualifiant juridiquement chaque fait sans approximation.\n\n"
            f"Soigne particulièrement la logique de ton argumentation pour convaincre les correcteurs du Baccalauréat."
        )
        chaps = [
            {"title": f"Fondements Juridiques & Notions de {topic}", "timestamp_seconds": 0},
            {"title": "Hiérarchie des Normes & Textes de Référence", "timestamp_seconds": 90},
            {"title": "Fonctionnement des Institutions Maliennes", "timestamp_seconds": 180},
            {"title": "Méthodologie du Cas Pratique & Dissertation Juridique", "timestamp_seconds": 270},
        ]
        takeaways = [
            f"Identifier les sources du droit et les règles régissant {topic}.",
            "Comprendre le rôle de la Constitution et la séparation des pouvoirs.",
            "Utiliser la terminologie juridique exacte exigée par les correcteurs.",
            "Structurer la réponse selon la rigueur du syllogisme juridique.",
        ]
    elif any(k in sub_lower for k in ["polit"]):
        script_text = (
            f"Bienvenue dans ton cours de science politique AlternIA dédié à {topic} en {subject} ({class_level}).\n\n"
            f"La science politique étudie la conquête, l'exercice et la légitimation du pouvoir au sein de la société. "
            f"Elle analyse les institutions de l'État, le rôle moteur des partis politiques et les grands défis géopolitiques contemporains, "
            f"tels que la souveraineté nationale et l'intégration régionale sahélienne à travers l'Alliance des États du Sahel (AES).\n\n"
            f"Pour l'examen du Bac : fonde ton argumentation sur les concepts de légitimité, de citoyenneté et de souveraineté populaire, "
            f"en montrant comment les institutions démocratiques répondent aux aspirations de la société civile.\n\n"
            f"Adopte une analyse neutre, objective et documentée pour obtenir une excellente note."
        )
        chaps = [
            {"title": f"Concept Clé & Problématique Politique de {topic}", "timestamp_seconds": 0},
            {"title": "Institutions de l'État & Régimes Politiques", "timestamp_seconds": 90},
            {"title": "Enjeux Contemporains & Souveraineté Sahélienne (AES)", "timestamp_seconds": 180},
            {"title": "Conseils du Correcteur pour le Baccalauréat", "timestamp_seconds": 270},
        ]
        takeaways = [
            f"Analyser les mécanismes du pouvoir et de la gouvernance dans {topic}.",
            "Comprendre le rôle des partis politiques et de la participation citoyenne.",
            "Relier les concepts théoriques aux dynamiques politiques actuelles du Sahel.",
            "Rédiger un plan équilibré articulant théorie et exemples institutionnels concrets.",
        ]
    elif any(k in sub_lower for k in ["philo"]):
        script_text = (
            f"Bienvenue dans ce cours de révision philosophique AlternIA sur {topic} pour ta classe de {class_level}.\n\n"
            f"En philosophie au Baccalauréat malien, philosopher ne consiste pas à réciter des citations au hasard, mais à problématiser "
            f"une question universelle. Face à un sujet d'examen, identifie le paradoxe ou la tension sous-jacente : par exemple entre "
            f"la liberté et le déterminisme, la conscience et l'inconscient, ou la justice et la loi.\n\n"
            f"Convoque les grands penseurs classiques et modernes (Descartes, Rousseau, Kant, Sartre) non comme des vérités absolues, "
            f"mais comme des interlocuteurs pour éclairer ta propre réflexion critique.\n\n"
            f"Soigne le plan dialectique (thèse, antithèse, synthèse) et rédige une conclusion qui tranche fermement la problématique posée."
        )
        chaps = [
            {"title": f"Problématique Centrale & Définition de {topic}", "timestamp_seconds": 0},
            {"title": "Thèse Philosophique & Réflexion Critique", "timestamp_seconds": 90},
            {"title": "Antithèse & Dialogue entre Auteurs", "timestamp_seconds": 180},
            {"title": "Synthèse Dialectique & Conseils de Dissertation", "timestamp_seconds": 270},
        ]
        takeaways = [
            f"Dégager la tension philosophique essentielle de {topic}.",
            "Articuler les concepts de conscience, de liberté et de justice.",
            "Mobiliser des citations d'auteurs intégrées naturellement à l'argumentation.",
            "Construire un plan dialectique progressif et rigoureux.",
        ]
    elif any(k in sub_lower for k in ["éco", "eco", "ses"]):
        script_text = (
            f"Bienvenue dans cette synthèse audio AlternIA d'économie consacrée à {topic} ({class_level}).\n\n"
            f"La science économique analyse l'allocation optimale des ressources rares face aux besoins illimités des agents économiques. "
            f"Pour les épreuves d'examen au Mali, maîtrise parfaitement les agrégats macroéconomiques comme le PIB, les mécanismes "
            f"de formation des prix par l'offre et la demande, ainsi que la politique monétaire menée par la BCEAO au sein de l'UEMOA.\n\n"
            f"Mets en perspective ces principes avec les réalités de l'économie malienne, en abordant la diversification agricole, "
            f"l'industrialisation locale et l'importance cruciale du secteur informel.\n\n"
            f"Définis rigoureusement les termes économiques et illustre chaque point par des données chiffrées précises."
        )
        chaps = [
            {"title": f"Définitions & Notions Économiques de {topic}", "timestamp_seconds": 0},
            {"title": "Mécanismes de Marché & Agrégats Clés", "timestamp_seconds": 90},
            {"title": "Politiques Économiques & Conjoncture au Mali (UEMOA)", "timestamp_seconds": 180},
            {"title": "Méthode d'Analyse de Documents & Dissertation SES", "timestamp_seconds": 270},
        ]
        takeaways = [
            f"Définir avec exactitude les concepts économiques de {topic}.",
            "Comprendre les leviers de la croissance, du PIB et de l'inflation.",
            "Analyser l'impact des politiques monétaires et budgétaires au Mali.",
            "Interpréter avec rigueur les graphiques et tableaux statistiques d'examen.",
        ]
    elif any(k in sub_lower for k in ["svt", "biol"]):
        script_text = (
            f"Bienvenue dans ton cours de sciences naturelles AlternIA dédié à {topic} en {subject}.\n\n"
            f"En {class_level}, les SVT évaluent ta capacité à raisonner scientifiquement. Chaque question d'examen fait appel à la démarche : "
            f"« Je vois que », « Or je sais que », « Donc j'en déduis que ». Ne confonds jamais une observation avec une interprétation.\n\n"
            f"Pour les schémas de biologie ou de géologie : respecte scrupuleusement les proportions, utilise des flèches nettes pour les légendes, "
            f"et n'oublie jamais de donner un titre complet souligné à ton schéma fonctionnel.\n\n"
            f"Assimile le vocabulaire biologique avec rigueur pour convaincre les correcteurs. Bon courage pour tes révisions !"
        )
        chaps = [
            {"title": f"Observation & Mécanismes de {topic}", "timestamp_seconds": 0},
            {"title": "Analyse Scientifique & Schémas", "timestamp_seconds": 90},
            {"title": "Démarche Déductive d'Examen", "timestamp_seconds": 180},
            {"title": "Points de Vigilance pour le Bac", "timestamp_seconds": 270},
        ]
        takeaways = [
            f"Comprendre le fonctionnement biologique ou géologique de {topic}.",
            "Adopter la démarche scientifique rigoureuse : constat, savoir, déduction.",
            "Réaliser des schémas légendés soignés avec un titre complet.",
            "Utiliser le lexique biologique exact exigé au programme malien.",
        ]
    else:
        script_text = (
            f"Bienvenue dans ce podcast AlternIA sur {topic} en {subject} pour la classe de {class_level}.\n\n"
            f"Pour réussir cette épreuve aux examens nationaux maliens, la clé réside dans la maîtrise des définitions de base, "
            f"la compréhension des théorèmes fondamentaux et la rigueur de la démarche logique.\n\n"
            f"Lors des exercices : lis attentivement l'énoncé, identifie les données initiales, pose les hypothèses de travail, "
            f"puis applique pas à pas les formules sans sauter d'étape intermédiaire. Encadre tes résultats avec soin.\n\n"
            f"Persévère avec régularité : c'est l'entraînement méthodique qui garantit d'excellentes notes au Bac !"
        )
        chaps = [
            {"title": f"Introduction & Définition de {topic}", "timestamp_seconds": 0},
            {"title": "Formules et Principes Fondamentaux", "timestamp_seconds": 90},
            {"title": "Applications et Résolution d'Exercices", "timestamp_seconds": 180},
            {"title": "Conseils du Correcteur pour le Bac", "timestamp_seconds": 270},
        ]
        takeaways = [
            f"Définir avec exactitude les concepts fondamentaux de {topic}.",
            "Appliquer rigoureusement les formules et propriétés associées.",
            "Justifier chaque étape de résolution sur sa copie.",
            "S'entraîner régulièrement sur les annales officielles du Mali.",
        ]

    chapters = [
        PodcastChapterDto(
            title=str(c["title"]),
            timestamp_seconds=int(c["timestamp_seconds"]),
        )
        for c in chaps
    ]

    return PodcastDto(
        id=podcast_id,
        title=f"Cours Clé : {topic}",
        subject=subject,
        class_level=class_level,
        duration_minutes=duration,
        summary=f"Synthèse audio pédagogique complète sur {topic} ({subject}) pour la classe de {class_level} au Mali.",
        narrator="Professeur IA (AlternIA)",
        chapters=chapters,
        key_takeaways=takeaways,
        full_script=script_text,
        icon_name=_subject_to_icon(subject),
        source="ia_alternia_certifiee",
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
    if "socio" in sub or "social" in sub:
        return "groups"
    if "droit" in sub or "institut" in sub or "jurid" in sub:
        return "gavel"
    if "polit" in sub:
        return "account_balance"
    if "éco" in sub or "eco" in sub or "ses" in sub:
        return "trending_up"
    if "angl" in sub or "engl" in sub:
        return "language"
    if "fran" in sub or "litt" in sub:
        return "menu_book"
    return "headphones"


# ─────────────────────────────────────────────────────────────────────────────
# 4. GÉNÉRATION DE PODCAST DEPUIS UN DOCUMENT IMPORTÉ (PDF, WORD, POWERPOINT)
# ─────────────────────────────────────────────────────────────────────────────

class PodcastFromTextRequest(BaseModel):
    course_text: str
    subject: str = "Sciences"
    class_level: str = "12eme"
    student_name: str = "Élève"
    duration_minutes: int = 6


async def _synthetiser_cours_en_podcast(
    raw_text: str,
    source_title: str,
    subject: str,
    class_level: str,
    student_name: str,
    duration_minutes: int,
) -> PodcastDto:
    """Transforme un texte brut de cours en podcast audio structuré conforme au programme malien."""
    duration = max(3, min(10, duration_minutes))
    podcast_id = f"import_pod_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    clean_sample = raw_text[:4000].strip()

    system_prompt = (
        "Tu es le Professeur IA d'AlternIA au Mali. Tu dois transformer le document de cours importé "
        f"en un podcast de révision audio oralisé pour un élève de {class_level} du Mali.\n"
        "Réponds STRICTEMENT au format JSON avec :\n"
        "- 'title': titre clair du cours\n"
        "- 'summary': résumé synthétique de 2 phrases\n"
        "- 'chapters': liste de 3 ou 4 chapitres avec 'title' et 'timestamp_seconds'\n"
        "- 'key_takeaways': 4 points essentiels à retenir pour le Bac/DEF\n"
        "- 'full_script': script narratif complet d'au moins 300 mots, clair, captivant, sans puces ni astérisques, optimisé pour la voix TTS."
    )

    user_prompt = (
        f"Matière : {subject}\n"
        f"Niveau scolaire malien : {class_level}\n"
        f"Document source : {source_title}\n"
        f"Contenu du cours :\n{clean_sample}\n\n"
        "Génère maintenant le podcast au format JSON."
    )

    try:
        orchestrator = get_orchestrator()
        content = ""
        if hasattr(orchestrator, "process_message"):
            ai_res = await orchestrator.process_message(
                user_message=user_prompt,
                conversation_id=f"doc_podcast_{podcast_id}",
                metadata={"system_override": system_prompt},
            )
            content = ai_res.get("content", "") if isinstance(ai_res, dict) else str(ai_res)
        elif hasattr(orchestrator, "llm_client") and orchestrator.llm_client:
            import asyncio
            content = await asyncio.to_thread(
                orchestrator.llm_client.generate,
                prompt=user_prompt,
                system_prompt=system_prompt,
            )

        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            data = json.loads(re.sub(r",\s*([\}\]])", r"\1", json_match.group(0)), strict=False)
            chapters = [
                PodcastChapterDto(
                    title=str(c.get("title", f"Partie {idx+1}")),
                    timestamp_seconds=int(c.get("timestamp_seconds", idx * 90)),
                )
                for idx, c in enumerate(data.get("chapters", []))
                if isinstance(c, dict)
            ]
            if not chapters:
                chapters = [
                    PodcastChapterDto(title="Introduction du cours importé", timestamp_seconds=0),
                    PodcastChapterDto(title="Notions essentielles & Formules", timestamp_seconds=120),
                    PodcastChapterDto(title="Synthèse & Méthodologie Bac", timestamp_seconds=240),
                ]

            return PodcastDto(
                id=podcast_id,
                title=sanitize_french_educational_text(data.get("title", f"Cours : {source_title}")),
                subject=subject,
                class_level=class_level,
                duration_minutes=duration,
                summary=sanitize_french_educational_text(data.get("summary", f"Podcast de révision extrait de {source_title}.")),
                narrator="Professeur IA (AlternIA)",
                chapters=[
                    PodcastChapterDto(
                        title=sanitize_french_educational_text(c.title),
                        timestamp_seconds=c.timestamp_seconds,
                    )
                    for c in chapters
                ],
                key_takeaways=[sanitize_french_educational_text(str(k)) for k in data.get("key_takeaways", []) if isinstance(k, str)],
                full_script=sanitize_french_educational_text(str(data.get("full_script", "")).strip()),
                icon_name=_subject_to_icon(subject),
                source="import_document_ia",
            )
    except Exception as e:
        print(f"⚠️ [PodcastImport] Fallback heuristique : {e}")

    # Fallback robuste basé sur le texte extrait
    lignes = [l.strip() for l in raw_text.splitlines() if len(l.strip()) > 30][:6]
    extrait_resume = " ".join(lignes[:2]) if lignes else f"Ce cours aborde les notions de base de {subject}."
    
    script_fallback = (
        f"Bonjour {student_name} ! Bienvenue dans ton podcast de révision AlternIA généré à partir de ton document : {source_title}.\n\n"
        f"Pour ta classe de {class_level}, voici l'explication structurée des points essentiels de cette leçon :\n\n"
        f"{extrait_resume}\n\n"
        f"Au Mali, la réussite des épreuves de {subject} repose sur trois piliers : la compréhension rigoureuse des définitions, "
        f"la maîtrise des formules et théorèmes associés, et une argumentation méthodique lors de la rédaction.\n\n"
        f"Prends le temps de réécouter ce passage, note les concepts fondamentaux dans ton cahier de révision, et entraîne-toi avec AlternIA !"
    )

    return PodcastDto(
        id=podcast_id,
        title=f"Cours Importé : {source_title}",
        subject=subject,
        class_level=class_level,
        duration_minutes=duration,
        summary=f"Synthèse de révision extraite du document '{source_title}' pour la classe de {class_level}.",
        narrator="Professeur IA (AlternIA)",
        chapters=[
            PodcastChapterDto(title=f"Introduction à {source_title}", timestamp_seconds=0),
            PodcastChapterDto(title="Notions Clés du Document", timestamp_seconds=100),
            PodcastChapterDto(title="Conseils Méthodologiques Mali", timestamp_seconds=200),
        ],
        key_takeaways=[
            f"Identifier les thèmes centraux développés dans {source_title}.",
            f"Relier les concepts aux exigences officielles du programme malien en {class_level}.",
            "Retenir les définitions et termes techniques spécifiques.",
            "Consolider par des exercices pratiques dans AlternIA.",
        ],
        full_script=script_fallback,
        icon_name=_subject_to_icon(subject),
        source="import_document_certifie",
    )


@router.post("/generate-from-text", response_model=PodcastDto)
async def generate_podcast_from_text_endpoint(req: PodcastFromTextRequest):
    """Génère un cours audio à partir d'un texte ou d'un cours déjà présent dans AlterniA."""
    if len(req.course_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Le texte du cours doit comporter au moins 50 caractères.")
    return await _synthetiser_cours_en_podcast(
        raw_text=req.course_text,
        source_title="Cours AlterniA",
        subject=req.subject,
        class_level=req.class_level,
        student_name=req.student_name,
        duration_minutes=req.duration_minutes,
    )


@router.post("/import-and-generate", response_model=PodcastDto)
async def generate_podcast_from_file_endpoint(
    file: UploadFile = File(...),
    subject: str = Form("Sciences"),
    class_level: str = Form("12eme"),
    student_name: str = Form("Élève"),
    duration_minutes: int = Form(6),
):
    """
    Importe un document de cours (PDF, Word .docx, PowerPoint .pptx ou texte),
    extrait son contenu et génère un podcast structuré conforme au programme officiel du Mali.
    """
    try:
        contenu_bytes = await file.read()
        texte_extrait = extraire_texte_document(file.filename or "cours.txt", contenu_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse du fichier : {e}")

    return await _synthetiser_cours_en_podcast(
        raw_text=texte_extrait,
        source_title=file.filename or "Document de cours",
        subject=subject,
        class_level=class_level,
        student_name=student_name,
        duration_minutes=duration_minutes,
    )

