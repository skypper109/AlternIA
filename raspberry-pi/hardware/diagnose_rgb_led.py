#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════
Diagnostic & Étalonnage de la LED Tricolore RGB (AlternIA Box - Pi 5)
══════════════════════════════════════════════════════════════════════════════

Ce script permet d'identifier immédiatement :
1. Si un conflit de service (comme l'ancien 'alta-led') bloque le canal Rouge (GPIO 17).
2. Si la LED est à Cathode Commune (GND) ou Anode Commune (+3.3V).
3. Si les canaux Rouge (17), Vert (27) et Bleu (22) sont bien reliés aux bonnes broches.
4. De sauvegarder automatiquement la bonne configuration dans votre fichier .env.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Chemins .env
ENV_PATHS = [
    Path("/home/ubuntu/Alternia/raspberry-pi/.env"),
    Path("/home/ubuntu/AlternIA/raspberry-pi/.env"),
    Path(__file__).resolve().parent.parent / ".env",
    Path(".env"),
]

def load_env():
    env_vars = {}
    for p in ENV_PATHS:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip().strip('"').strip("'")
            except Exception:
                pass
            return p, env_vars
    return ENV_PATHS[0], env_vars

def save_env_var(key: str, value: str):
    target_path, current_vars = load_env()
    current_vars[key] = value
    
    # Réécriture propre
    lines = []
    found = False
    if target_path.exists():
        for line in target_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{key}=") or stripped.startswith(f"{key} ="):
                lines.append(f"{key}={value}")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"{key}={value}")
    
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"💾 [Configuration enregistrée dans {target_path}] : {key}={value}")

def stop_conflicting_services():
    print("\n🔍 [1/5] Vérification et arrêt des services conflictuels...")
    for svc in ["alta-led", "alta-hardware"]:
        try:
            res = subprocess.run(["systemctl", "is-active", svc], capture_output=True, text=True)
            if res.stdout.strip() == "active":
                print(f"   🛑 Arrêt temporaire de '{svc}' pour libérer les broches GPIO...")
                subprocess.run(["sudo", "systemctl", "stop", svc], check=False)
        except Exception:
            pass

    # Désactiver l'ancien alta-led qui monopolisait le GPIO 17
    try:
        subprocess.run(["sudo", "systemctl", "disable", "alta-led"], capture_output=True, check=False)
        print("   ✅ Service 'alta-led' désactivé définitivement (le contrôle RGB est géré par alta-hardware).")
    except Exception:
        pass

def init_raw_pins(pin_r: int, pin_g: int, pin_b: int):
    """Initialise les broches avec gpiod ou gpiozero."""
    # Méthode 1 : libgpiod (le plus direct sur Pi 5)
    try:
        import gpiod
        chip = gpiod.Chip('gpiochip4')
        lines = {
            "r": chip.get_line(pin_r),
            "g": chip.get_line(pin_g),
            "b": chip.get_line(pin_b),
        }
        for name, line in lines.items():
            line.request(consumer="alta-diagnose", type=gpiod.LINE_REQ_DIR_OUT)
        return "gpiod", lines
    except Exception as e:
        pass

    # Méthode 2 : gpiozero LED
    try:
        from gpiozero import LED
        pins = {
            "r": LED(pin_r, active_high=True),
            "g": LED(pin_g, active_high=True),
            "b": LED(pin_b, active_high=True),
        }
        return "gpiozero", pins
    except Exception as e:
        print(f"❌ Impossible d'accéder aux broches physiques : {e}")
        return None, None

def set_pin_level(backend, handle, pin_key, high: bool):
    """Envoie un niveau HAUT (3.3V) ou BAS (0V) physique."""
    if backend == "gpiod":
        handle[pin_key].set_value(1 if high else 0)
    elif backend == "gpiozero":
        if high:
            handle[pin_key].on()
        else:
            handle[pin_key].off()

def release_pins(backend, handle):
    if backend == "gpiod" and handle:
        for line in handle.values():
            try:
                line.set_value(0)
                line.release()
            except Exception:
                pass
    elif backend == "gpiozero" and handle:
        for led in handle.values():
            try:
                led.off()
                led.close()
            except Exception:
                pass

def test_color_cycle(backend, handle, active_high: bool, duration: float = 1.8):
    """
    Allume successivement Rouge, Vert, Bleu selon la polarité choisie :
    - Si active_high=True (Cathode Commune / patte longue sur GND) : ON = HIGH (1), OFF = LOW (0)
    - Si active_high=False (Anode Commune / patte longue sur +3.3V) : ON = LOW (0), OFF = HIGH (1)
    """
    def set_rgb(r_on, g_on, b_on):
        lvl_r = r_on if active_high else (not r_on)
        lvl_g = g_on if active_high else (not g_on)
        lvl_b = b_on if active_high else (not b_on)
        set_pin_level(backend, handle, "r", lvl_r)
        set_pin_level(backend, handle, "g", lvl_g)
        set_pin_level(backend, handle, "b", lvl_b)

    # 1. Éteindre tout
    set_rgb(False, False, False)
    time.sleep(0.3)

    # 2. Test Rouge
    print("   🔴 [TEST] Allumage ROUGE seul (GPIO 17 / Broche 11)...")
    set_rgb(True, False, False)
    time.sleep(duration)

    # 3. Test Vert
    print("   🟢 [TEST] Allumage VERT seul (GPIO 27 / Broche 13)...")
    set_rgb(False, True, False)
    time.sleep(duration)

    # 4. Test Bleu
    print("   🔵 [TEST] Allumage BLEU seul (GPIO 22 / Broche 15)...")
    set_rgb(False, False, True)
    time.sleep(duration)

    # 5. Test Blanc (Tous allumés)
    print("   ⚪ [TEST] Allumage des 3 couleurs ensemble (Blanc)...")
    set_rgb(True, True, True)
    time.sleep(duration)

    # Éteindre
    set_rgb(False, False, False)

def main():
    print("═" * 74)
    print("🌈 OUTIL DE DIAGNOSTIC ET ÉTALONNAGE DE LA LED TRICOLORE ALTA")
    print("═" * 74)
    print("Ce test va allumer Rouge, Vert et Bleu pour calibrer votre LED.")

    stop_conflicting_services()

    _, env = load_env()
    pin_r = int(env.get("PIN_LED_R", 17))
    pin_g = int(env.get("PIN_LED_G", 27))
    pin_b = int(env.get("PIN_LED_B", 22))

    print(f"\n📍 Broches testées : R=GPIO {pin_r} (Pin 11), G=GPIO {pin_g} (Pin 13), B=GPIO {pin_b} (Pin 15)")
    backend, handle = init_raw_pins(pin_r, pin_g, pin_b)

    if not backend:
        print("❌ Impossible de prendre le contrôle des GPIO. Assurez-vous d'exécuter ce script avec sudo.")
        sys.exit(1)

    print(f"✅ Pilote matériel activé via : {backend}")

    # Guide de câblage
    print("""
📋 RAPPEL DU CÂBLAGE DES 4 PATTES DE LA LED TRICOLORE :
   • Patte 1 (à gauche de la plus longue) : Canal ROUGE  ➔ GPIO 17 (Pin 11) avec résistance 220Ω
   • Patte 2 (LA PLUS LONGUE)             : COMMUNE      ➔ GND (Pin 9) OU +3.3V (Pin 1)
   • Patte 3                              : Canal VERT   ➔ GPIO 27 (Pin 13) avec résistance 220Ω
   • Patte 4                              : Canal BLEU   ➔ GPIO 22 (Pin 15) avec résistance 220Ω
""")

    print("──────────────────────────────────────────────────────────────────────────")
    print("🔬 TEST 1 : Mode CATHODE COMMUNE (La plus longue patte est reliée à GND)")
    print("──────────────────────────────────────────────────────────────────────────")
    print("Lancement du défilement Rouge ➔ Vert ➔ Bleu ➔ Blanc...")
    test_color_cycle(backend, handle, active_high=True)

    ans = input("\n👉 Avez-vous bien vu Rouge, puis Vert, puis Bleu nettement ? (o/n) [o] : ").strip().lower()

    if ans in ("", "o", "oui", "y", "yes"):
        print("🎉 Excellent ! Votre LED est à CATHODE COMMUNE (Standard).")
        save_env_var("LED_ACTIVE_HIGH", "1")
    else:
        print("\n──────────────────────────────────────────────────────────────────────────")
        print("🔬 TEST 2 : Mode ANODE COMMUNE (La plus longue patte est reliée au +3.3V)")
        print("──────────────────────────────────────────────────────────────────────────")
        print("Lancement du défilement avec logique inversée (Active Low)...")
        test_color_cycle(backend, handle, active_high=False)

        ans2 = input("\n👉 Est-ce que les couleurs Rouge, Vert, Bleu sont apparues correctement maintenant ? (o/n) : ").strip().lower()
        if ans2 in ("o", "oui", "y", "yes"):
            print("🎉 Parfait ! Votre LED est une ANODE COMMUNE.")
            print("   L'inversion de polarité a été prise en compte.")
            save_env_var("LED_ACTIVE_HIGH", "0")
        else:
            print("""
⚠️ DIAGNOSTIC DES BRANCHEMENTS PHYSIQUES :
   Si seule la couleur ROUGE apparaît toujours ou si rien ne s'allume :
   1. Vérifiez où est branchée la patte LA PLUS LONGUE :
      - Si elle est sur GND (Pin 9 ou 14) : c'est une Cathode commune.
      - Si elle est sur 3.3V (Pin 1 ou 17) : c'est une Anode commune.
   2. Vérifiez si les fils Vert (GPIO 27) et Bleu (GPIO 22) font bien contact.
   3. Si le vert et le bleu sont inversés, échangez les fils sur GPIO 27 et 22.
""")
            ans_force = input("Voulez-vous enregistrer le mode Cathode Commune (1) ou Anode Commune (0) ? [1] : ").strip()
            val = "0" if ans_force == "0" else "1"
            save_env_var("LED_ACTIVE_HIGH", val)

    release_pins(backend, handle)

    print("\n🚀 [Redémarrage] Réactivation du contrôleur principal alta-hardware...")
    subprocess.run(["sudo", "systemctl", "restart", "alta-hardware"], check=False)
    print("✅ Le contrôleur alta-hardware est maintenant relancé avec la bonne configuration !")
    print("👉 Appuyez sur les boutons 1, 2, 3 pour vérifier que la LED change de couleur selon la classe !")

if __name__ == "__main__":
    main()
