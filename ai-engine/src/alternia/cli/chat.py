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


def create_orchestrator(enable_rag: bool = True):
    """Initialise et met en cache l'orchestrateur pédagogique avec RAG réel et LLM local."""
    # Sélection automatique du meilleur modèle (1.5B ultra-rapide pour RPi/Edge, ou 3B)
    model_1_5b = PROJECT_ROOT / "ai-engine" / "models" / "llm" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    model_3b = PROJECT_ROOT / "ai-engine" / "models" / "llm" / "qwen2.5-3b-instruct-q4_k_m.gguf"
    model_path = model_1_5b if model_1_5b.exists() else model_3b

    print(f"⏳ Chargement du modèle LLM local ({model_path.name})...")
    llm_client = LocalLLMClient(
        model_path=str(model_path),
        n_ctx=4096,   # Contexte complet pour absorber RAG + historique sans jamais saturer
        n_batch=512,
        # max_tokens non limité : le modèle s'arrête seul à la fin d'une réponse complète
        # On laisse le prompt guider la longueur, pas une coupure artificielle
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

    # Message d'accueil vocal personnalisé selon la classe
    if audio_enabled:
        tts.speak_sentence_async(f"Bonjour ! Je suis ALTA. Tu es configuré en {series_label}. Pose-moi ta première question !")

    while True:
        try:
            prompt_label = f"[{current_class}|{current_series}|{current_subject}] Élève > "
            question = input(prompt_label).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nALTA > À bientôt et bon courage pour tes révisions !")
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
            print("\nALTA > À bientôt et bon courage pour tes révisions !")
            if audio_enabled:
                tts.speak("À bientôt et bon courage pour tes révisions !")
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

        if cmd == "/aide":
            print_header(current_class, series_label, current_subject, audio_enabled, tts.voice)
            continue

        # Traitement d'une question élève avec le RAG
        print("\n\033[1;33m🔍 Recherche dans le programme officiel & analyse pédagogique...\033[0m")
        start_time = time.perf_counter()

        try:
            # Matière résolue dynamiquement si en mode général
            effective_subject = None if current_subject in {"général", "general", "toutes", "tous"} else current_subject

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

            # ——— Streaming TTS : déclenchement immédiat dès le 1er token ———
            # Stratégie : buffer de 30 caractères minimum puis envoi immédiat
            # au premier signe de ponctuation ou à 12 mots pour démarrer la voix
            # sans aucune latence perceptible.
            full_response = ""
            sentence_buffer = ""
            first_audio_sent = False

            # Séparateurs naturels de groupes phonétiques pour TTS
            tts_split = re.compile(r"(?<=[.!?…])\s+|(?<=[,;:])\s+|\n+")

            for chunk in stream:
                print(chunk, end="", flush=True)
                full_response += chunk

                if not audio_enabled:
                    continue

                sentence_buffer += chunk

                if not first_audio_sent:
                    # Déclenchement dès que le buffer dépasse 30 chars ET atteint
                    # un espace (mot complet) — pas besoin de ponctuation
                    if len(sentence_buffer) >= 30 and sentence_buffer[-1] in ' \n\t':
                        segment = sentence_buffer.strip()
                        sentence_buffer = ""
                        if segment:
                            tts.speak_sentence_async(segment)
                            first_audio_sent = True
                else:
                    # Envoi au fil de l'eau dès qu'un séparateur est trouvé
                    while True:
                        m = tts_split.search(sentence_buffer)
                        if not m:
                            break
                        end_pos = m.end()
                        segment = sentence_buffer[:end_pos].strip()
                        sentence_buffer = sentence_buffer[end_pos:]
                        if len(segment) > 3:
                            tts.speak_sentence_async(segment)

            # Dernier segment (fin de réponse sans séparateur final)
            if audio_enabled and sentence_buffer.strip():
                tts.speak_sentence_async(sentence_buffer.strip())

            elapsed = time.perf_counter() - start_time
            print(f"\n\n\033[2m[Réponse générée en {elapsed:.2f}s]\033[0m\n")

            # Enregistrement en direct de l'interaction dans alta_db (alertes & analytics admin temps réel)
            try:
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
            except Exception as db_err:
                pass

        except Exception as exc:
            print(f"\n\n❌ Erreur : {exc}\n")


if __name__ == "__main__":
    main()

