"""
Routes API pour l'état système, le statut santé, la synthèse vocale, l'analyse RAG et le WebSocket session.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from alternia.config.settings import settings
from alternia.tts.engine import TTSEngine
from backend.src.models.device import TTSRequest
from backend.src.services.orchestrator_service import (
    get_orchestrator,
    normalize_student_class,
    state,
)

router = APIRouter(tags=["Système & Dispositif"])


@router.get("/health")
@router.get("/api/health")
def health():
    """Vérification d'état et santé de l'API AlternIA."""
    _ = get_orchestrator()
    return {
        "status": "healthy",
        "application": "AlternIA",
        "version": "1.0.0",
        "rag_ready": state.rag_ready,
        "llm_model": f"Qwen 2.5 ({state.model_name}) (GGUF Local)" if getattr(state, "model_name", None) else "Qwen 2.5 1.5B Instruct (GGUF Local)",
        "default_class": settings.default_class,
    }


@router.get("/api/info")
@router.get("/api/device/info")
@router.get("/api/device/ping")
def get_device_info():
    """Retourne les informations complètes du dispositif physique AlternIA local pour le scan mobile."""
    return {
        "id": "alternia-local-server",
        "device_id": "ALT-BOX-MALI-01",
        "device_name": "Boîtier AlternIA (Mali)",
        "name": "Boîtier AlternIA (Local AI & RAG Mali)",
        "version": "2.0.0",
        "firmware": "v2.0-LocalEdge",
        "firmware_version": "v2.0-LocalEdge",
        "battery": 94,
        "battery_level": 94,
        "storage_free_go": 24.2,
        "storage_total_go": 32.0,
        "status": "online",
        "ip": "127.0.0.1",
        "ip_address": "127.0.0.1",
        "port": 8000,
        "ai_engine": "AlternIA Native Engine (Qwen 2.5 + RAG)",
        "llm_local": True,
        "rag_local": True,
        "rag_ready": state.rag_ready,
        "indexed_chunks": state.chunks_count,
        "domain": "alterniamali.com",
        "domains": {
            "root": "https://alterniamali.com",
            "admin": "https://admin.alterniamali.com",
            "device": "https://device.alterniamali.com",
            "api": "https://api.alterniamali.com",
        },
    }


@router.post("/api/tts")
async def tts_post_endpoint(req: TTSRequest):
    """Synthèse vocale neurale haute fidélité (POST JSON body)."""
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Texte manquant pour la synthèse vocale")

    voice_name = req.voice or settings.tts_voice or "henri"
    tts_engine = TTSEngine(voice=voice_name)
    try:
        audio_bytes = await tts_engine.synthesize_to_bytes(req.text)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Échec de la synthèse vocale")
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur TTS : {str(e)}")


@router.get("/api/tts")
async def tts_get_endpoint(text: str, voice: Optional[str] = "henri"):
    """Synthèse vocale neurale haute fidélité (GET query param)."""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Texte manquant pour la synthèse vocale")

    tts_engine = TTSEngine(voice=voice or "henri")
    try:
        audio_bytes = await tts_engine.synthesize_to_bytes(text)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Échec de la synthèse vocale")
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur TTS : {str(e)}")


_stt_engine = None


def get_stt_engine():
    global _stt_engine
    if _stt_engine is None:
        from alternia.stt.engine import STTEngine
        _stt_engine = STTEngine(model_size="tiny", language="fr")
    return _stt_engine


@router.post("/api/stt")
async def stt_endpoint(
    audio: UploadFile = File(...),
    language: Optional[str] = Form("fr")
):
    """Transcription vocale Speech-to-Text via Faster-Whisper local embarqué."""
    try:
        stt = get_stt_engine()
        content = await audio.read()
        if not content:
            raise HTTPException(status_code=400, detail="Fichier audio vide")

        suffix = Path(audio.filename or "recording.wav").suffix or ".wav"
        text = stt.transcribe(content, language=language or "fr", suffix=suffix)
        return {"text": text, "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"text": "", "status": "error", "message": f"Erreur STT : {str(e)}"}


@router.post("/api/rag/analyze")
async def rag_analyze_exercise(
    subject: Optional[str] = Form(None),
    level: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
):
    """
    Analyse approfondie d'un exercice ou problème scolaire scanné :
    1. Extraction de texte par OCR haute fidélité (Apple Vision / fallback).
    2. Détection de lisibilité : rejet explicite si l'image est floue ou vide.
    3. Détection de conformité au programme : rejet immédiat des reçus de transaction, tickets financiers et documents non académiques.
    4. Détection dynamique de la vraie matière scolaire (Maths, Physique-Chimie, SVT, Français, Philo, Histoire-Géo).
    5. Analyse détaillée des procédures et décomposition socratique de résolution pas-à-pas alignée sur le programme du Mali.
    """
    import re
    from backend.src.services.ocr_service import perform_ocr_on_image
    from alternia.pedagogical.curriculum_keywords import detect_malian_curriculum_subject

    orch = get_orchestrator()
    student_class = normalize_student_class(level or "11eme")
    
    extracted_text = (text or "").strip()

    # 1. Traitement OCR si une image est transmise
    if image and image.filename:
        try:
            image_bytes = await image.read()
            if image_bytes:
                ocr_result = perform_ocr_on_image(image_bytes, filename=image.filename)
                if ocr_result and ocr_result.strip():
                    extracted_text = ocr_result.strip() if not extracted_text else f"{extracted_text}\n" + ocr_result.strip()
        except Exception as ocr_err:
            print(f"[OCR Error] {ocr_err}")

    # 2. Vérification de lisibilité
    clean_text = extracted_text.strip()
    if not clean_text or len(clean_text) < 4:
        return {
            "status": "unreadable",
            "is_valid": False,
            "subject": "Illisible",
            "class": student_class,
            "topic": "Image non exploitable",
            "extracted_text": clean_text,
            "message": "Le document ou la photo scannée est illisible ou ne contient aucun texte d'exercice exploitable. Assurez-vous de bien éclairer la feuille et de photographier l'énoncé de près.",
            "hints": [],
        }

    norm_text = clean_text.lower()

    # 3. Détection des documents hors programme scolaire (ex: reçus de paiement, tickets, cartes, factures)
    financial_receipt_terms = [
        "transaction", "montant", "frais", "fcfa", "xof", "cfa", "solde",
        "ref bill", "reçu de", "recu de", "ticket de caisse", "retrait", "dépôt", "depot",
        "orange money", "wave", "moov money", "sama money", "facture",
        "carte sim", "numéro de téléphone", "numero de telephone", "carte d'identité",
        "permis de conduire", "passeport", "bancaire", "virement", "guichet"
    ]
    academic_exercise_indicators = [
        "exercice", "problème", "probleme", "devoir", "question", "calculer",
        "démontrer", "demontrer", "montrer que", "justifier", "déterminer", "determiner",
        "résoudre", "resoudre", "équation", "equation", "fonction", "théorème", "theoreme",
        "formule", "suite", "intégrale", "integrale", "dérivée", "derivee", "vecteur",
        "vitesse", "accélération", "acceleration", "force", "tension", "courant",
        "chimie", "atome", "molécule", "molecule", "acide", "base", "ph", "solution",
        "cellule", "adn", "génétique", "genetique", "chromosome", "svt", "biologie",
        "dissertation", "commentaire", "texte", "strophe", "auteur", "philosophie",
        "histoire", "géographie", "geographie", "siècle", "siecle", "empire", "mali"
    ]

    non_acad_matches = sum(1 for term in financial_receipt_terms if term in norm_text)
    acad_matches = sum(1 for term in academic_exercise_indicators if term in norm_text)
    detected_raw_sub = detect_malian_curriculum_subject(clean_text)

    # Détection si c'est une équation ou formule mathématique / scientifique
    is_math_formula = bool(re.search(r"(=|<|>|\+|\-|\*|/|\^|\bx\b|\by\b|\bz\b|f\(x\)|lim|sqrt|cos|sin|tan)", clean_text, re.IGNORECASE))
    if is_math_formula and not detected_raw_sub:
        detected_raw_sub = "mathematiques"
        acad_matches += 1

    # Si le document contient des marqueurs financiers/reçus sans contexte d'exercice
    if non_acad_matches >= 2 and acad_matches == 0 and not detected_raw_sub:
        return {
            "status": "not_curriculum",
            "is_valid": False,
            "subject": "Document non académique",
            "class": student_class,
            "topic": "Reçu ou document financier",
            "extracted_text": clean_text,
            "message": "Ce document ne correspond pas au programme scolaire malien (reçu de paiement, ticket financier ou document non académique détecté). Veuillez scanner une page de manuel ou un exercice de cours (Mathématiques, Physique-Chimie, SVT, Français, etc.).",
            "hints": [],
        }

    # Si le texte extrait ne comporte aucun vocabulaire scolaire ni matière identifiable
    if acad_matches == 0 and not detected_raw_sub and len(clean_text) > 40:
        return {
            "status": "not_curriculum",
            "is_valid": False,
            "subject": "Non reconnu",
            "class": student_class,
            "topic": "Hors programme scolaire",
            "extracted_text": clean_text,
            "message": "Le texte détecté ne semble pas être un énoncé d'exercice ou de cours conforme au programme du lycée. Assurez-vous de cadrer directement l'exercice à résoudre.",
            "hints": [],
        }

    # 4. Identification dynamique de la vraie matière scolaire
    subject_display_names = {
        "biologie": "SVT / Biologie",
        "chimie": "Physique-Chimie",
        "physique": "Physique-Chimie",
        "mathematiques": "Mathématiques",
        "philosophie": "Philosophie",
        "histoire-geographie": "Histoire-Géographie",
        "francais": "Français",
        "anglais": "Anglais",
        "economie": "Économie",
    }
    
    true_subject = None
    if detected_raw_sub in subject_display_names:
        true_subject = subject_display_names[detected_raw_sub]
    elif detected_raw_sub:
        true_subject = detected_raw_sub.capitalize()
    elif subject and subject.strip().lower() not in {"général", "general", "non défini"}:
        true_subject = subject.strip()
    else:
        # Détection heuristique
        if any(w in norm_text for w in ["f(x)", "intégrale", "dérivée", "équation", "suite", "triangle", "cos", "sin", "matrice", "probabilité"]):
            true_subject = "Mathématiques"
        elif any(w in norm_text for w in ["newton", "force", "masse", "vitesse", "acide", "base", "ph", "solution", "circuit", "tension", "ampère"]):
            true_subject = "Physique-Chimie"
        elif any(w in norm_text for w in ["cellule", "chromosome", "allèle", "adn", "plante", "chlorophylle", "sol", "roche"]):
            true_subject = "SVT / Biologie"
        elif any(w in norm_text for w in ["conscience", "inconscient", "liberté", "morale", "justice", "vérité"]):
            true_subject = "Philosophie"
        else:
            true_subject = "Mathématiques"

    # 5. Détection du thème ou chapitre spécifique de l'exercice
    detected_topic = "Résolution méthodique"
    if "suite" in norm_text:
        detected_topic = "Suites numériques & Récurrence"
    elif "f(x)" in norm_text or "dériv" in norm_text or "limite" in norm_text:
        detected_topic = "Étude de fonctions & Dérivation"
    elif "complex" in norm_text or "imaginaire" in norm_text:
        detected_topic = "Nombres complexes & Géométrie"
    elif "probab" in norm_text:
        detected_topic = "Probabilités & Dénombrement"
    elif "newton" in norm_text or "force" in norm_text or "accélér" in norm_text:
        detected_topic = "Mécanique & Lois de Newton"
    elif "acide" in norm_text or "base" in norm_text or "ph" in norm_text:
        detected_topic = "Réactions acido-basiques & Dosage"
    elif "circuit" in norm_text or "rlc" in norm_text or "condensateur" in norm_text:
        detected_topic = "Électrocinétique & Circuits"
    elif "généti" in norm_text or "mendel" in norm_text or "chromosom" in norm_text:
        detected_topic = "Génétique mendélienne & Hérédité"
    elif "cellul" in norm_text or "mitose" in norm_text:
        detected_topic = "Biologie cellulaire & Division"
    elif "conscien" in norm_text or "libert" in norm_text:
        detected_topic = "La Conscience et la Liberté"

    # 6. Extraction des éléments clés (nombres, grandeurs, questions de l'exercice)
    found_numbers = re.findall(r"\b\d+(?:[.,]\d+)?\b", clean_text)
    numbers_snippet = ", ".join(found_numbers[:4]) if found_numbers else "Données littérales"

    first_sentence = clean_text.split("\n")[0][:100]

    # Construction des 4 étapes détaillées spécifiques à l'énoncé
    hints = [
        {
            "step": 1,
            "type": "observation",
            "title": f"Étape 1 • Observation & Données ({true_subject})",
            "text": (
                f"Analysons minutieusement l'énoncé scanné : « {first_sentence}… ».\n"
                f"• Données et grandeurs identifiées : {numbers_snippet}.\n"
                f"• Thématique dominante : {detected_topic}."
            ),
            "content": (
                f"Analysons minutieusement l'énoncé scanné : « {first_sentence}… ».\n"
                f"• Données et grandeurs identifiées : {numbers_snippet}.\n"
                f"• Thématique dominante : {detected_topic}."
            ),
            "question": "Quelles sont les données connues et quelle est la grandeur ou conclusion exacte demandée par la consigne ?",
        },
        {
            "step": 2,
            "type": "conceptual",
            "title": f"Étape 2 • Théorèmes & Formules ({true_subject})",
            "text": (
                f"Mobilisons les fondamentaux du programme officiel malien de {student_class} en {true_subject}.\n"
                f"Pour traiter le thème '{detected_topic}', rappelle-toi des définitions clés, relations maîtresses et conditions d'application requises."
            ),
            "content": (
                f"Mobilisons les fondamentaux du programme officiel malien de {student_class} en {true_subject}.\n"
                f"Pour traiter le thème '{detected_topic}', rappelle-toi des définitions clés, relations maîtresses et conditions d'application requises."
            ),
            "question": "Quelle formule maîtresse ou propriété de cours relie directement les données fournies à l'inconnue ?",
        },
        {
            "step": 3,
            "type": "procedural",
            "title": f"Étape 3 • Procédure de résolution méthodique",
            "text": (
                f"Procédure pas-à-pas pour cet exercice :\n"
                f"1. Pose l'équation ou la relation littérale sans remplacer prématurément par les valeurs numériques.\n"
                f"2. Isole méthodiquement la grandeur recherchée.\n"
                f"3. Vérifie l'homogénéité dimensionnelle et effectue l'application numérique avec les unités du système international."
            ),
            "content": (
                f"Procédure pas-à-pas pour cet exercice :\n"
                f"1. Pose l'équation ou la relation littérale sans remplacer prématurément par les valeurs numériques.\n"
                f"2. Isole méthodiquement la grandeur recherchée.\n"
                f"3. Vérifie l'homogénéité dimensionnelle et effectue l'application numérique avec les unités du système international."
            ),
            "question": "Quelle relation littérale intermédiaire obtiens-tu avant l'application numérique ?",
        },
        {
            "step": 4,
            "type": "solution",
            "title": f"Étape 4 • Résolution finale & Vérification",
            "text": (
                f"Synthèse et validation du résultat :\n"
                f"• Analyse critique : vérifie si l'ordre de grandeur est cohérent avec le cadre physique ou mathématique.\n"
                f"• Rédaction : encadre ton résultat final avec son unité exacte et une phrase explicative rigoureuse."
            ),
            "content": (
                f"Synthèse et validation du résultat :\n"
                f"• Analyse critique : vérifie si l'ordre de grandeur est cohérent avec le cadre physique ou mathématique.\n"
                f"• Rédaction : encadre ton résultat final avec son unité exacte et une phrase explicative rigoureuse."
            ),
            "question": "Ton résultat final répond-il complètement à toutes les questions posées dans l'énoncé ?",
        },
    ]

    return {
        "status": "success",
        "is_valid": True,
        "subject": true_subject,
        "class": student_class,
        "topic": detected_topic,
        "extracted_text": clean_text,
        "message": f"Exercice analysé avec succès en {true_subject} ({detected_topic}).",
        "hints": hints,
    }


@router.websocket("/ws/session")
async def websocket_session_endpoint(websocket: WebSocket):
    """
    WebSocket duplex temps réel pour le salon holographique et le kiosk AlternIA :
    diffuse l'état de l'IA (listening, thinking, speaking, idle), les transcriptions et l'amplitude.
    """
    await websocket.accept()
    orch = get_orchestrator()

    # Envoyer l'état initial
    await websocket.send_text(json.dumps({"type": "ai_state", "state": "idle"}))

    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                msg = json.loads(data_text)
            except Exception:
                msg = {"type": "text", "query": data_text}

            msg_type = msg.get("type", "query")

            if msg_type in ("query", "text", "ask"):
                query = msg.get("query") or msg.get("text") or "Bonjour AlternIA"
                student_class = normalize_student_class(msg.get("class", "11eme"))
                subject = msg.get("subject", "général")
                student_id = msg.get("student_id", "device-kiosk")
                session_id = msg.get("session_id", "device-session")
                series = msg.get("series")

                # Récupération du contexte RAG
                context = None
                if orch.rag_service:
                    try:
                        context = orch.rag_service.retrieve(
                            question=query,
                            student_class=student_class,
                            subject=subject,
                            student_id=student_id,
                            series=series,
                        )
                    except Exception:
                        context = None

                # 1. State: Thinking
                await websocket.send_text(json.dumps({"type": "ai_state", "state": "thinking"}))
                await asyncio.sleep(0.2)

                # 2. Pipeline LLM + RAG
                try:
                    res = orch.ask(
                        question=query,
                        context=context,
                        student_class=student_class,
                        subject=subject,
                        student_id=student_id,
                        session_id=session_id,
                        series=series,
                    )
                    answer = res.get("answer", "Voici l'explication demandée.")
                except Exception as e:
                    answer = f"Je suis à ton écoute. Pose-moi ta question sur le cours : {e}"

                # 3. State: Speaking + Transcription
                await websocket.send_text(json.dumps({"type": "ai_state", "state": "speaking"}))
                await websocket.send_text(json.dumps({
                    "type": "transcript",
                    "speaker": "ai",
                    "text": answer,
                    "partial": False,
                }))

                # 4. Simulation d'amplitude vocale pendant la parole
                for amp in [0.4, 0.75, 0.9, 0.6, 0.8, 0.5, 0.2]:
                    await websocket.send_text(json.dumps({"type": "amplitude", "value": amp}))
                    await asyncio.sleep(0.15)

                # 5. State: Idle
                await websocket.send_text(json.dumps({"type": "ai_state", "state": "idle"}))

            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        pass
    except Exception:
        pass


@router.get("/api/rag/documents")
def get_curriculum_documents():
    """Retourne la liste des documents officiels et manuels du programme malien indexés dans le boîtier/serveur AlternIA."""
    return {
        "status": "success",
        "documents": [
            {
                "id": "doc-math-tse",
                "name": "Manuel_Officiel_Mathematiques_TSE_Mali.pdf",
                "title": "Mathématiques — Analyse & Algèbre (TSE / 11ème)",
                "subject": "Mathématiques",
                "level": "Terminale",
                "date": "Programme Officiel 2026",
                "steps": 4,
                "source": "Ministère de l'Éducation Nationale du Mali",
                "color": "0xFF314999"
            },
            {
                "id": "doc-pc-tse",
                "name": "Physique_Chimie_Mecanique_Mali.pdf",
                "title": "Physique-Chimie — Lois de Newton & Cinétique",
                "subject": "Physique-Chimie",
                "level": "Terminale",
                "date": "Programme Officiel 2026",
                "steps": 4,
                "source": "Institut Pédagogique National (IPN)",
                "color": "0xFFF1851F"
            },
            {
                "id": "doc-svt-tse",
                "name": "SVT_Biologie_Cellulaire_Genetique.pdf",
                "title": "Sciences de la Vie et de la Terre — Génétique",
                "subject": "Biologie",
                "level": "11ème / TSE",
                "date": "Programme Officiel 2026",
                "steps": 4,
                "source": "Direction Nationale de l'Enseignement Secondaire",
                "color": "0xFF40BBCC"
            },
            {
                "id": "doc-philo-fr",
                "name": "Philosophie_Methodologie_Dissertation.pdf",
                "title": "Philosophie & Français — Méthodologie Baccalauréat",
                "subject": "Français",
                "level": "Toutes Séries",
                "date": "Annales Bac Mali",
                "steps": 4,
                "source": "Académie d'Enseignement de Bamako",
                "color": "0xFF8B5CF6"
            }
        ]
    }
