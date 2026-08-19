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


def render_dashboard(state: str, current_class: str, detail: str = ""):
    """Affiche le tableau de bord interactif du dispositif."""
    os.system("clear" if os.name == "posix" else "cls")
    
    class_badges = {
        "10eme": "\033[1;42;37m  [1] 10ème (ACTIF)  \033[0m  [2] 11ème    [3] 12ème",
        "11eme": "  [1] 10ème  \033[1;44;37m  [2] 11ème (ACTIF)  \033[0m  [3] 12ème",
        "12eme": "  [1] 10ème    [2] 11ème  \033[1;45;37m  [3] 12ème (ACTIF)  \033[0m",
    }

    state_symbols = {
        "ready": "🟢 \033[1;32mPRÊT (En attente d'une question sur le Bouton 4)\033[0m",
        "listening": "🔴 \033[1;31m🎙️ ENREGISTREMENT MICRO EN COURS... (Parlez maintenant)\033[0m",
        "thinking": "🟡 \033[1;33m🧠 ANALYSE STT & RECHERCHE RAG OFFICIELLE...\033[0m",
        "speaking": "🟣 \033[1;35m🔊 ALTA RÉPOND VOCALEMENT...\033[0m",
        "error": "❌ \033[1;31mERREUR SYSTÈME\033[0m",
    }

    print("=" * 72)
    print("  🇲🇱  ALTERNIA BOX — DISPOSITIF ÉDUCATIF PHYSIQUE (4 BOUTONS)  🇲🇱")
    print("=" * 72)
    print(f"  Programme Actif : {class_badges.get(current_class, current_class)}")
    print(f"  État Matériel   : {state_symbols.get(state, state)}")
    if detail:
        print(f"  Information     : \033[1;37m{detail}\033[0m")
    print("-" * 72)
    print("  🎛️  COMMANDES PHYSIQUES DU DISPOSITIF :")
    print("    [1] -> BOUTON 1 : Basculer sur 10ème Année (Tronc Commun)")
    print("    [2] -> BOUTON 2 : Basculer sur 11ème Année (Générale)")
    print("    [3] -> BOUTON 3 : Basculer sur 12ème Année (Terminale)")
    print("    [4] ou [ESPACE] -> BOUTON 4 (MICRO) :")
    print("           • 1er Clic  : Démarrer l'enregistrement vocal")
    print("           • 2ème Clic : Arrêter et lancer la réponse d'ALTA")
    print("           • Re-clic   : Continuer et poser la question suivante")
    print("    [q] -> Éteindre le boîtier")
    print("=" * 72)
    print("\n👉 Appuyez sur une touche [1, 2, 3, 4, ESPACE, ou q] : ", end="", flush=True)


def main():
    print("\n⏳ Initialisation de la Box AlternIA...")
    
    # 1. Chargement de l'Orchestrateur et du RAG
    orchestrator, vector_store = create_orchestrator(enable_rag=True)

    # 2. Moteur de synthèse vocale TTS
    tts = TTSEngine(voice=settings.tts_voice or "vivienne")

    # 3. Moteur de reconnaissance vocale STT (Faster-Whisper local)
    stt = STTEngine(model_size="base", language="fr")

    # 4. Contrôleur du Dispositif 4 Boutons
    current_state = {"state": "ready", "class": "10eme", "detail": "Boîtier prêt à l'emploi"}

    def on_state_update(st, cls, dt):
        current_state["state"] = st
        current_state["class"] = cls
        current_state["detail"] = dt
        render_dashboard(st, cls, dt)

    controller = DeviceController(
        orchestrator=orchestrator,
        tts=tts,
        stt=stt,
        initial_class="10eme",
        on_state_change=on_state_update,
    )

    # Message de bienvenue
    tts.speak_sentence_async("Boîtier AlternIA prêt. Choisis ta classe avec les boutons 1, 2 ou 3, puis pose ta question avec le bouton 4.")
    render_dashboard("ready", "10eme", "Boîtier prêt. Clique sur le Bouton 4 pour parler !")

    # Boucle de capture clavier pour le mode simulation sur Mac / PC
    # Sur Raspberry Pi, les vrais boutons GPIO fonctionnent en parallèle automatiquement via HardwareManager
    try:
        import tty, termios  # pyrefly: ignore
        def getch():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
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

            elif char == "1":
                controller.select_class_10()

            elif char == "2":
                controller.select_class_11()

            elif char == "3":
                controller.select_class_12()

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
