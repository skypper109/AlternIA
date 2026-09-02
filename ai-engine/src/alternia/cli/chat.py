import os
import sys
import time
import re
from pathlib import Path
from types import SimpleNamespace

# Désactiver le warning de parallélisme HuggingFace lors des forks
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from alternia.config.settings import (
    PROJECT_ROOT,
    settings,
)
from alternia.core.models import StudentClass, Subject
from alternia.llm.local_client import LocalLLMClient
from alternia.orchestration.orchestrator import AlterniaOrchestrator
from alternia.pedagogical.engine import PedagogicalEngine
from alternia.rag.embeddings import EmbeddingService
from alternia.rag.semantic_retriever import SemanticRetriever
from alternia.rag.vector_store import LocalVectorStore
from alternia.rag.service import RAGService
from alternia.rag.contextualizer import QueryContextualizer
from alternia.tts.engine import TTSEngine, NEURAL_VOICES
from alternia.conversation.manager import ConversationManager
from alternia.learner.manager import LearnerManager
from alternia.pedagogical.curriculum_keywords import detect_malian_curriculum_subject


def create_orchestrator(enable_rag: bool = True):
    """Initialise et met en cache l'orchestrateur pédagogique avec RAG réel et LLM local."""
    # Sélection automatique du meilleur modèle (3B en priorité pour une qualité pédagogique maximale, ou 1.5B)
    model_3b = PROJECT_ROOT / "ai-engine" / "models" / "llm" / "qwen2.5-3b-instruct-q4_k_m.gguf"
    model_1_5b = PROJECT_ROOT / "ai-engine" / "models" / "llm" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    model_path = model_3b if model_3b.exists() else model_1_5b

    print(f"⏳ Chargement du modèle LLM local ({model_path.name})...")
    llm_client = LocalLLMClient(
        model_path=str(model_path),
        n_ctx=4096,   # Contexte élargi pour supporter le RAG sans crash
        n_batch=512,
    )

    rag_service = None
    vector_store = None
    if enable_rag:
        print("⏳ Chargement du moteur d'embedding et de la base de connaissances...")
        embedding_service = EmbeddingService()
        vector_store = LocalVectorStore()
        loaded = vector_store.load()
        if loaded:
            print(f"✅ Base RAG chargée : {vector_store.count} extraits pédagogiques prêts.")
        else:
            print("⚠️ Aucun index vectoriel trouvé. Mode sans RAG actif.")

        retriever = SemanticRetriever(
            embedding_service=embedding_service,
            vector_store=vector_store,
        )
        rag_service = RAGService(
            retriever=retriever,
            top_k=2,
        )

    pedagogical_engine = PedagogicalEngine()
    learner_manager = LearnerManager()
    conversation_manager = ConversationManager()

    orchestrator = AlterniaOrchestrator(
        pedagogical_engine=pedagogical_engine,
        llm_client=llm_client,
        rag_service=rag_service,
        learner_manager=learner_manager,
        conversation_manager=conversation_manager,
    )

    return orchestrator, vector_store


def print_header(student_class: str, series_label: str, subject: str, audio_enabled: bool, voice_name: str):
    print()
    print("=" * 68)
    print("  🇲🇱   ALTA — Assistant Pédagogique Intelligent (AlternIA)   🇲🇱")
    print("=" * 68)
    print(f"  • Niveau & Série : \033[1;36m{series_label} ({student_class})\033[0m")
    print(f"  • Matière active : \033[1;32m{subject}\033[0m")
    audio_status = f"\033[1;35mActivé (Voix : {voice_name})\033[0m" if audio_enabled else "\033[1;30mDésactivé\033[0m"
    print(f"  • Audio / Voix   : {audio_status}")
    print("-" * 68)
    print("  Commandes utiles :")
    print("    /classe 10eme | 11eme [11s|11l|11seco] | 12eme [tse|tsexp|tseco|tss|tll]")
    print("    /matiere <nom>             -> Changer de matière (maths, physique...)")
    print("    /audio on|off              -> Activer/Désactiver la voix")
    print("    /voix <nom>                -> Changer de voix (vivienne, remy, denise, system)")
    print("    /modele 1.5b | 3b          -> Changer de modèle (1.5B ~16 tok/s | 3B haute précision)")
    print("    /sources                   -> Voir les sources du dernier RAG")
    print("    /profil                    -> Voir le carnet de suivi d'apprentissage")
    print("    /aide                      -> Afficher l'aide")
    print("    quit / exit                -> Quitter")
    print("=" * 68)
    print()


def main():
    tts = TTSEngine(voice=settings.tts_voice or "vivienne")
    audio_enabled = True

    print("\n" + "=" * 68)
    print("  🇲🇱   BIENVENUE SUR ALTA — Tuteur Pédagogique Intelligent (AlternIA)   🇲🇱")
    print("=" * 68)
    print("  Choisis ta classe pour adapter le programme à ton niveau :")
    print("    [1] 10ème Année (Tronc Commun)")
    print("    [2] 11ème Année (Sciences / Lettres / Économie)")
    print("    [3] 12ème Année (Terminale / Baccalauréat)")
    print("-" * 68)

    try:
        choice = input("👉 Entre ton choix [1, 2, ou 3] (Défaut: 3) : ").strip()
    except (KeyboardInterrupt, EOFError):
        return

    if choice == "1":
        current_class = "10eme"
        current_series = "generale"
        series_label = "10ème (Tronc Commun)"
    elif choice == "2":
        current_class = "11eme"
        print("\n  📚 Choisis ta filière de 11ème Année :")
        print("    [1] 11ème Sciences (11S — Mathématiques, Physique-Chimie, Biologie)")
        print("    [2] 11ème Lettres (11L — Français, Histoire-Géo, Langues)")
        print("    [3] 11ème Sciences Économiques / Tertiaire (11SEco / TE)")
        print("-" * 68)
        try:
            s_choice = input("👉 Entre ta filière [1, 2, ou 3] (Défaut: 1) : ").strip()
        except (KeyboardInterrupt, EOFError):
            return
        if s_choice == "2":
            current_series = "11l"
            series_label = "11ème Lettres (11L)"
        elif s_choice == "3":
            current_series = "11seco"
            series_label = "11ème Économie (11SEco)"
        else:
            current_series = "11s"
            series_label = "11ème Sciences (11S)"
    else:
        current_class = "12eme"
        print("\n  🎓 Choisis ta série de Terminale (12ème) :")
        print("    [1] TSE (Sciences Exactes — Maths & Physique approfondies)")
        print("    [2] TSExp (Sciences Expérimentales — Biologie/SVT, Physique, Chimie)")
        print("    [3] TSEco (Sciences Économiques — Économie, Comptabilité, Maths)")
        print("    [4] TSS (Sciences Sociales — Histoire-Géo, Sociologie, Philo)")
        print("    [5] TLL (Lettres et Littérature — Français, Philosophie, Langues)")
        print("-" * 68)
        try:
            s_choice = input("👉 Entre ta série [1, 2, 3, 4, ou 5] (Défaut: 1) : ").strip()
        except (KeyboardInterrupt, EOFError):
            return
        if s_choice == "2":
            current_series = "tsexp"
            series_label = "Terminale Sciences Expérimentales (TSExp)"
        elif s_choice == "3":
            current_series = "tseco"
            series_label = "Terminale Sciences Économiques (TSEco)"
        elif s_choice == "4":
            current_series = "tss"
            series_label = "Terminale Sciences Sociales (TSS)"
        elif s_choice == "5":
            current_series = "tll"
            series_label = "Terminale Lettres & Littérature (TLL)"
        else:
            current_series = "tse"
            series_label = "Terminale Sciences Exactes (TSE)"

    current_subject = "général"
    student_id = f"eleve_{current_class}_{current_series}"

    print(f"\n✅ Configuration active : \033[1;36m{series_label}\033[0m")
    print_header(current_class, series_label, current_subject, audio_enabled, tts.voice)

    orchestrator, vector_store = create_orchestrator(enable_rag=True)
    session_id = f"session_cli_{int(time.time())}"

    last_sources = []

    # Message d'accueil vocal personnalisé selon la classe (prononciation naturelle en français)
    if audio_enabled:
        speech_series = re.sub(r"\s*\([^)]*\)", "", series_label).strip()
        speech_series = speech_series.replace("&", "et")
        tts.speak_sentence_async(f"Bonjour ! Je suis ALTA. Tu es configuré en {speech_series}. Pose-moi ta première question !")

    while True:
        try:
            prompt_label = f"[{current_class}|{current_series}|{current_subject}] Élève > "
            question = input(prompt_label).strip()
        except (KeyboardInterrupt, EOFError):
            farewell = "À bientôt et bon courage pour tes révisions !"
            print(f"\n\nALTA > {farewell}")
            if audio_enabled:
                tts.speak_sync(farewell)
            tts.stop()
            break

        if not question:
            continue

        # Interrompre tout audio précédent dès la réception d'une nouvelle saisie
        if audio_enabled:
            tts.stop()

        # Gestion des commandes spéciales
        cmd = question.lower()
        if cmd in {"quit", "exit", "q"}:
            farewell = "À bientôt et bon courage pour tes révisions !"
            print(f"\nALTA > {farewell}")
            if audio_enabled:
                tts.speak_sync(farewell)
            tts.stop()
            break

        if cmd.startswith("/classe"):
            parts = question.split()
            if len(parts) >= 2:
                new_cls = parts[1].strip().lower()
                new_ser = parts[2].strip().lower() if len(parts) >= 3 else None
                if new_cls in {"10eme", "10", "10e"}:
                    current_class = "10eme"
                    current_series = "generale"
                    series_label = "10ème (Tronc Commun)"
                    print(f"✅ Classe basculée sur : \033[1;36m{series_label}\033[0m\n")
                elif new_cls in {"11eme", "11", "11e"}:
                    current_class = "11eme"
                    if new_ser in {"11l", "lettres", "l", "sh"}:
                        current_series = "11l"
                        series_label = "11ème Lettres (11L)"
                    elif new_ser in {"11seco", "economie", "eco", "te", "seco"}:
                        current_series = "11seco"
                        series_label = "11ème Économie (11SEco)"
                    else:
                        current_series = "11s"
                        series_label = "11ème Sciences (11S)"
                    print(f"✅ Classe basculée sur : \033[1;36m{series_label}\033[0m\n")
                elif new_cls in {"12eme", "12", "12e", "terminale", "t"}:
                    current_class = "12eme"
                    if new_ser in {"tsexp", "exp", "sciences_exp"}:
                        current_series = "tsexp"
                        series_label = "TSExp (Sciences Expérimentales)"
                    elif new_ser in {"tseco", "eco", "economie"}:
                        current_series = "tseco"
                        series_label = "TSEco (Sciences Économiques)"
                    elif new_ser in {"tss", "sociales", "sh"}:
                        current_series = "tss"
                        series_label = "TSS (Sciences Sociales)"
                    elif new_ser in {"tll", "lettres", "l"}:
                        current_series = "tll"
                        series_label = "TLL (Lettres & Littérature)"
                    else:
                        current_series = "tse"
                        series_label = "TSE (Sciences Exactes)"
                    print(f"✅ Classe basculée sur : \033[1;36m{series_label}\033[0m\n")
                else:
                    print("❌ Classe invalide. Choisis : 10eme, 11eme [11s|11l|11seco], ou 12eme [tse|tsexp|tseco|tss|tll]\n")
            else:
                print("❌ Utilisation : /classe 10eme | /classe 11eme [11s|11l|11seco] | /classe 12eme [tse|tsexp|tseco|tss|tll]\n")
            continue

        if cmd.startswith("/matiere "):
            new_subj = question.split(maxsplit=1)[1].strip().lower()
            current_subject = new_subj
            print(f"✅ Matière basculée sur : \033[1;32m{current_subject}\033[0m\n")
            continue

        if cmd.startswith("/audio "):
            sub = question.split(maxsplit=1)[1].strip().lower()
            if sub in {"on", "1", "true", "oui"}:
                audio_enabled = True
                print("✅ Synthèse vocale \033[1;32mACTIVÉE\033[0m\n")
            else:
                audio_enabled = False
                tts.stop()
                print("🔇 Synthèse vocale \033[1;31mDÉSACTIVÉE\033[0m\n")
            continue

        if cmd.startswith("/voix "):
            new_voice = question.split(maxsplit=1)[1].strip().lower()
            res = tts.set_voice(new_voice)
            print(f"🎙️ Voix changée pour : \033[1;35m{res}\033[0m\n")
            continue

        if cmd == "/sources":
            if not last_sources:
                print("Aucune source RAG enregistrée pour la dernière question.\n")
            else:
                print("\n📚 Sources officielles utilisées pour la dernière réponse :")
                for i, s in enumerate(last_sources, 1):
                    doc = getattr(s, "source_document", getattr(s, "source", "Manuel scolaire"))
                    chapter = getattr(s, "chapter", "Général")
                    lesson = getattr(s, "lesson", "")
                    score = getattr(s, "score", 0.0)
                    print(f"  [{i}] Doc: {Path(str(doc)).name} | Chapitre: {chapter} | Leçon: {lesson} | Score: {score:.3f}")
                print()
            continue

        if cmd == "/profil":
            profile = orchestrator.learner_manager.get_or_create(student_id)
            print(f"\n📊 Profil Apprenant [{student_id}] :")
            print(f"  • Niveau : {series_label} ({profile.student_class})")
            print(f"  • Notions maîtrisées : {profile.mastered_topics or 'En cours d\'évaluation'}")
            print(f"  • Notions à revoir   : {profile.topics_to_review or 'Aucune difficulté majeure'}")
            print(f"  • Interactions       : {len(profile.recent_interactions)}\n")
            continue

        if cmd.startswith("/modele"):
            parts = question.split()
            if len(parts) >= 2:
                target_m = parts[1].strip().lower()
                m_path = None
                if target_m in {"1.5b", "1.5", "fast", "rapide", "speed"}:
                    candidate = PROJECT_ROOT / "ai-engine" / "models" / "llm" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
                    if candidate.exists():
                        m_path = candidate
                elif target_m in {"3b", "3", "smart", "precision", "qualite"}:
                    candidate = PROJECT_ROOT / "ai-engine" / "models" / "llm" / "qwen2.5-3b-instruct-q4_k_m.gguf"
                    if candidate.exists():
                        m_path = candidate

                if m_path:
                    print(f"⏳ Basculement vers le modèle : \033[1;36m{m_path.name}\033[0m...")
                    new_client = LocalLLMClient(
                        model_path=str(m_path),
                        n_ctx=4096,
                        n_batch=512,
                    )
                    orchestrator.llm_client = new_client
                    print(f"✅ Modèle actif : \033[1;32m{m_path.name}\033[0m\n")
                else:
                    print("❌ Modèle indisponible. Choisis : /modele 1.5b (rapide ~16 tok/s) ou /modele 3b (précis ~8-10 tok/s)\n")
            else:
                print("❌ Utilisation : /modele 1.5b | /modele 3b\n")
            continue

        if cmd == "/aide":
            print_header(current_class, series_label, current_subject, audio_enabled, tts.voice)
            continue

        # Traitement d'une question élève avec le RAG
        req_start = time.perf_counter()
        print(f"\n\033[36m⏱️  [chat.py]\033[0m 1. Question élève reçue : \"{question}\" (Classe: {current_class}, Série: {current_series})")

        try:
            # Matière résolue dynamiquement si en mode général
            effective_subject = None if current_subject in {"général", "general", "toutes", "tous"} else current_subject

            # ----------------------------------------------------------------
            # DÉTECTION AUTOMATIQUE DE MATIÈRE DU PROGRAMME DU MALI
            # Identifie automatiquement la matière (biologie, chimie, physique, maths,
            # économie, comptabilité, histoire, géographie, philosophie, linguistique, etc.)
            # ----------------------------------------------------------------
            t0_sub = time.perf_counter()
            if effective_subject is None:
                effective_subject = detect_malian_curriculum_subject(question)
                dt_sub = time.perf_counter() - t0_sub
                print(f"\033[36m⏱️  [chat.py]\033[0m 2. Matière détectée automatiquement : \033[1;32m{effective_subject or 'Général'}\033[0m en \033[1;33m{dt_sub:.4f}s\033[0m")

            # Contextualisation intelligente de la recherche RAG pour les questions de suivi
            rag_query = question
            session = orchestrator.conversation_manager.get(session_id)
            if session and session.messages:
                student_past_msgs = [m.content for m in session.messages if m.role == "student"]
                rag_query = QueryContextualizer.contextualize(
                    current_question=question,
                    past_student_messages=student_past_msgs,
                    current_topic=getattr(session, "current_topic", None),
                )

            # Récupération du contexte RAG (filtrage strict par classe et série)
            rag_context = None
            if orchestrator.rag_service:
                rag_context = orchestrator.rag_service.retrieve(
                    question=rag_query,
                    student_class=current_class,
                    subject=effective_subject,
                    student_id=student_id,
                    series=current_series,
                )
                last_sources = rag_context.sources if rag_context else []

            # Vérification du cadrage curriculaire
            scope_check = orchestrator.curriculum_scope_checker.check_scope(
                question=question,
                student_class=current_class,
                subject=effective_subject,
            )
            if scope_check.is_higher_level:
                print(
                    f"ℹ️  \033[1;36m[Programme Scolaire] Notion de niveau {scope_check.target_class} "
                    f"({scope_check.target_series}). ALTA adapte l'explication pour la {current_class}.\033[0m"
                )

            # Affichage de la réponse en streaming
            print("\n\033[1;35mALTA > \033[0m", end="", flush=True)

            # Stream de la réponse
            stream = orchestrator.ask_stream(
                question=question,
                context=rag_context,
                student_class=current_class,
                subject=effective_subject,
                student_id=student_id,
                session_id=session_id,
                series=current_series,
            )

            # Arrêter tout audio précédent immédiatement
            if audio_enabled:
                tts.stop()

            # ——— Streaming TTS : découpage par phrases entières pour fluidité maximale ———
            full_response = ""
            sentence_buffer = ""
            first_audio_sent = False

            # Séparateurs de phrases complètes pour diction naturelle sans micro-pauses
            tts_split = re.compile(r"(?<=[.!?…])\s+|\n+")

            # Regex de nettoyage TTS : supprime les marqueurs anglais/balises
            tts_cleanup = re.compile(
                r"(\*{2,3}[^*]+\*{2,3}"  # **texte** ou ***texte***
                r"|\*{2,3}"              # *** seuls
                r"|\[Source\s*\d+[^\]]*\]"  # [Source 1 - ...]
                r"|CONTEXTE PÉDAGOGIQUE ALTERNIA"  # fuite de balise interne
                r"|FIN DU CONTEXTE"
                r")",
                re.IGNORECASE,
            )

            for chunk in stream:
                print(chunk, end="", flush=True)
                full_response += chunk

                if not audio_enabled:
                    continue

                sentence_buffer += chunk

                if not first_audio_sent:
                    # Première phrase : émise dès qu'on a au moins 45 caractères avec ponctuation ou 70 caractères
                    m = tts_split.search(sentence_buffer)
                    if (m and len(sentence_buffer[:m.end()].strip()) >= 20) or (len(sentence_buffer) >= 65 and sentence_buffer[-1] in ' \n\t'):
                        end_pos = m.end() if m else len(sentence_buffer)
                        segment = tts_cleanup.sub("", sentence_buffer[:end_pos]).strip()
                        sentence_buffer = sentence_buffer[end_pos:]
                        if segment:
                            tts.speak_sentence_async(segment)
                            first_audio_sent = True
                else:
                    # Phrases suivantes : envoyées phrase par phrase entière
                    while True:
                        m = tts_split.search(sentence_buffer)
                        if not m:
                            break
                        end_pos = m.end()
                        segment = tts_cleanup.sub("", sentence_buffer[:end_pos]).strip()
                        sentence_buffer = sentence_buffer[end_pos:]
                        if len(segment) > 3:
                            tts.speak_sentence_async(segment)

            # Dernier segment (fin de réponse)
            if audio_enabled and sentence_buffer.strip():
                tts.speak_sentence_async(tts_cleanup.sub("", sentence_buffer).strip())

            total_elapsed = time.perf_counter() - req_start
            print(f"\n\n\033[1;32m[✓ Réponse terminée en {total_elapsed:.2f}s | {len(full_response)} caractères]\033[0m\n")

            # Enregistrement en direct de l'interaction dans alta_db (alertes & analytics admin temps réel)
            try:
                t0_db = time.perf_counter()
                if str(PROJECT_ROOT) not in sys.path:
                    sys.path.insert(0, str(PROJECT_ROOT))
                from backend.src.services.learning_service import record_student_interaction
                record_student_interaction(
                    student_id=student_id,
                    student_class=current_class,
                    series=current_series,
                    subject=effective_subject,
                    question=question,
                    answer=full_response,
                    sources=last_sources,
                    session_id=session_id,
                )
                dt_db = time.perf_counter() - t0_db
                print(f"\033[36m⏱️  [chat.py]\033[0m Interaction enregistrée en DB (alta_db) en \033[1;33m{dt_db:.4f}s\033[0m\n")
            except Exception as db_err:
                pass

        except Exception as exc:
            print(f"\n\n❌ Erreur : {exc}\n")


if __name__ == "__main__":
    main()

