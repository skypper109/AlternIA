# Hardware

Contient la documentation et le code lié au matériel physique du dispositif AlternIA.

## Modules Matériels

- **[Raspberry Pi 3 (AlternIA Box)](../../raspberry-pi/)** : Code client Python complet, gestion GPIO (boutons Fondamental / Lycée, micro PTT, LEDs), audio ALSA, scripts d'installation automatique et service systemd.
- **[ESP32 IoT & Firmware](../../esp32/)** : Firmware MicroPython/C++ pour boîtier connecté, micro I2S et LED ring NeoPixel.

## Règle d'Architecture

Le hardware reste modulaire et communique avec le moteur pédagogique via l'API REST / WebSocket d'AlternIA. Il fournit les périphériques nécessaires (boutons, microphone, LEDs, écran).
