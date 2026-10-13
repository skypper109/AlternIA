"""
Application autonome pour le boîtier physique AlternIA Box (4 Boutons & Reconnaissance Vocale).

Exécution :
    PYTHONPATH=ai-engine/src python3 -m alternia.cli.device_app

Permet de piloter ALTA avec les 4 boutons du boîtier physique ou le clavier :
- [1] BOUTON 1 : Basculer sur la classe de 10ème (Programme officiel 10ème)
- [2] BOUTON 2 : Basculer sur la classe de 11ème (Programme officiel 11ème)
- [3] BOUTON 3 : Basculer sur la classe de 12ème (Programme officiel 12ème Terminale)
- [4 / ESPACE] : BOUTON 4 (MICRO) : Parler dans le micro pour poser une question vocale
                 Pour continuer ou poser une suite, réappuyer sur le bouton 4.
"""

import os
import sys
import time

from alternia.cli.chat import create_orchestrator
from alternia.config.settings import settings
from alternia.hardware.device_controller import DeviceController
from alternia.stt.engine import STTEngine
from alternia.tts.engine import TTSEngine


def render_dashboard(state: str, current_class: str, school: str = "", detail: str = ""):
    """Affiche le tableau de bord interactif du dispositif."""
    os.system("clear" if os.name == "posix" else "cls")
    
    def badge(c_id: str, label: str) -> str:
        if current_class == c_id:
            return f"\033[1;42;37m {label} (ACTIF) \033[0m"
        return f"\033[1;30;47m {label} \033[0m"

    state_symbols = {
        "ready": "🟢 \033[1;32mPRÊT (En attente d'une question sur le Bouton 4)\033[0m",
        "listening": "🔴 \033[1;31m🎙️ ENREGISTREMENT MICRO EN COURS... (Parlez maintenant)\033[0m",
        "thinking": "🟡 \033[1;33m🧠 ANALYSE STT & RECHERCHE RAG OFFICIELLE...\033[0m",
        "speaking": "🟣 \033[1;35m🔊 ALTA RÉPOND VOCALEMENT...\033[0m",
        "error": "❌ \033[1;31mERREUR SYSTÈME\033[0m",
    }

    school_display = school or "\033[0;33mNon configurée (Appuyez sur [e] pour choisir)\033[0m"

    print("=" * 76)
    print("  🇲🇱   ALTERNIA BOX — DISPOSITIF ÉDUCATIF PHYSIQUE VOCAL DU MALI   🇲🇱")
    print("=" * 76)
    print(f"  🏫 Établissement : \033[1;37m{school_display}\033[0m")
    print(f"  📚 Fondamental   : {badge('6eme', '[6] 6ème')}  {badge('7eme', '[7] 7ème')}  {badge('8eme', '[8] 8ème')}  {badge('9eme', '[9] 9ème (DEF)')}")
    print(f"  🎓 Lycée         : {badge('10eme', '[1] 10ème')}  {badge('11eme', '[2] 11ème')}  {badge('12eme', '[3] 12ème (Terminale)')}")
    print(f"  ⚡ État Matériel : {state_symbols.get(state, state)}")
    if detail:
        print(f"  ℹ️  Information   : \033[1;37m{detail}\033[0m")
    print("-" * 76)
    print("  🎛️  COMMANDES DU DISPOSITIF :")
    print("    [6, 7, 8, 9] -> Fondamental (6ème, 7ème, 8ème, 9ème / Examen DEF)")
    print("    [1, 2, 3]    -> Lycée (10ème Tronc Commun, 11ème, 12ème Terminale BAC)")
    print("    [e]          -> Configurer son École / Établissement Scolaire")
    print("    [4] ou [ESPACE] -> BOUTON MICRO :")
    print("           • 1er Clic  : Démarrer l'enregistrement vocal")
    print("           • 2ème Clic : Arrêter et lancer la réponse d'ALTA")
    print("    [q] -> Éteindre le boîtier")
    print("=" * 76)
    print("\n👉 Appuyez sur [6, 7, 8, 9, 1, 2, 3, e, 4/ESPACE, ou q] : ", end="", flush=True)


def main():
    print("\n⏳ Initialisation de la Box AlternIA...")
    
    # 1. Chargement de l'Orchestrateur et du RAG
    orchestrator, vector_store = create_orchestrator(enable_rag=True)

    # 2. Moteur de synthèse vocale TTS
    tts = TTSEngine(voice=settings.tts_voice or "vivienne")

    # 3. Moteur de reconnaissance vocale STT (Faster-Whisper local)
    stt = STTEngine(model_size="base", language="fr")

    # 4. Contrôleur du Dispositif
    current_state = {"state": "ready", "class": "6eme", "school": "", "detail": "Boîtier prêt à l'emploi"}

    def on_state_update(st, cls, dt):
        current_state["state"] = st
        current_state["class"] = cls
        current_state["detail"] = dt
        render_dashboard(st, cls, current_state["school"], dt)

    controller = DeviceController(
        orchestrator=orchestrator,
        tts=tts,
        stt=stt,
        initial_class="6eme",
        on_state_change=on_state_update,
    )

    # Message de bienvenue
    tts.speak_sentence_async("Boîtier AlternIA prêt. Choisis ta classe fondamentale ou lycée, puis pose ta question avec le micro.")
    render_dashboard("ready", "6eme", "", "Boîtier prêt. Choisis ta classe ou clique sur le Bouton 4 !")

    # Boucle de capture clavier pour le mode simulation sur Mac / PC
    try:
        import tty, termios  # pyrefly: ignore
        fd = sys.stdin.fileno()
        def getch():
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch
    except Exception:
        def getch():
            return input().strip()[:1]

    try:
        while True:
            char = getch()
            if not char:
                continue

            if char in {"q", "Q", "\x03"}:  # 'q' ou Ctrl+C
                print("\n\n👋 Extinction du boîtier AlternIA. À bientôt !")
                tts.speak_sync("Au revoir et bon travail !")
                break

            elif char == "6":
                controller.select_class_6()

            elif char == "7":
                controller.select_class_7()

            elif char == "8":
                controller.select_class_8()

            elif char == "9":
                controller.select_class_9()

            elif char == "1":
                controller.select_class_10()

            elif char == "2":
                controller.select_class_11()

            elif char == "3":
                controller.select_class_12()

            elif char in {"e", "E"}:
                print("\n\n🏫 Nom de votre école / établissement : ", end="", flush=True)
                school_name = sys.stdin.readline().strip()
                if school_name:
                    current_state["school"] = school_name
                    controller.set_school(school_name)
                else:
                    render_dashboard(current_state["state"], current_state["class"], current_state["school"])

            elif char in {"4", " ", "\r", "\n"}:  # Bouton 4 ou Espace
                if not controller.is_listening:
                    controller.start_mic_interaction()
                else:
                    controller.stop_mic_interaction()

    except KeyboardInterrupt:
        pass
    finally:
        controller.close()


if __name__ == "__main__":
    main()
