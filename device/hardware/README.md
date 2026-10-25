# ⚙️ AlternIA Device — Couche d'Abstraction Matérielle (HAL)

Ce répertoire définit la couche d'abstraction matérielle (**Hardware Abstraction Layer**) du dispositif physique AlternIA.

---

## 🎯 Rôle & Principes de Conception

1. **Découplage strict Matériel / Pédagogie** :
   - Le code matériel ne contient **aucune logique métier ni intelligence pédagogique**.
   - Son rôle unique est d'interagir avec les capteurs (boutons, microphone), les actionneurs (haut-parleur, LEDs, écran), et d'émettre/recevoir des événements standardisés en JSON.

2. **Indépendance des Plateformes** :
   - L'implémentation physique principale pour le boîtier de classe est hébergée sur **Raspberry Pi 5** dans [`raspberry-pi/hardware`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/raspberry-pi/hardware).
   - Une alternative microcontrôleur basse consommation est disponible dans [`esp32/`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/esp32) pour les terminaux ultra-portables.

---

## 📡 Contrat d'Événements Matériels (JSON Protocol)

Le sous-système matériel communique avec l'interface et le serveur via des messages JSON émis sur WebSocket ou sockets locaux :

### Événements sortants (Du Matériel vers le Système) :
- `BUTTON_PRESS` :
  ```json
  { "type": "button_press", "button_id": 1, "target": "cycle_fondamental", "timestamp": 1729831200 }
  ```
- `MIC_TRIGGER` :
  ```json
  { "type": "mic_trigger", "action": "start_listen", "mode": "push_to_talk" }
  ```
- `BARGE_IN` :
  ```json
  { "type": "barge_in", "reason": "user_button_interrupt" }
  ```

### Événements entrants (Du Système vers le Matériel) :
- `SET_LED_STATE` :
  ```json
  { "type": "set_led", "color": "cyan", "mode": "pulsing", "duration_ms": 3500 }
  ```
- `PLAY_AUDIO_STREAM` :
  ```json
  { "type": "play_audio", "url": "https://api.alterniamali.com/audio/chunk_1.mp3", "barge_in_allowed": true }
  ```

---

## 🔗 Liens vers les Implémentations Réelles

- Pour le contrôleur Raspberry Pi 5 (Python, `gpiozero`, PipeWire/ALSA, I2S) : voir [`raspberry-pi/hardware/README.md`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/raspberry-pi/README.md).
- Pour le plan de câblage complet et les instructions de soudure : voir [`raspberry-pi/hardware/GUIDE_CABLAGE_ET_SOUDURE_PINS.md`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/raspberry-pi/hardware/GUIDE_CABLAGE_ET_SOUDURE_PINS.md).
