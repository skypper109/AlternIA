#ifndef ALTERNIA_CONFIG_H
#define ALTERNIA_CONFIG_H

#include <Arduino.h>

// ==============================================================================
// 1. CONFIGURATION WI-FI DU DISPOSITIF ALTERNIA
// ==============================================================================

// Mode Station (STA) : Connexion au réseau Internet (Hotspot téléphone ou Box
// Wi-Fi)
#define WIFI_STA_SSID "KALANSO_Telefilani"
#define WIFI_STA_PASSWORD "4HuCUrqhuNxUer"

// Mode Point d'Accès (SoftAP) : Le boîtier émet son propre Wi-Fi pour les
// élèves
#define WIFI_AP_SSID "AlterniA-Box-Mali"
#define WIFI_AP_PASSWORD                                                       \
  "MaliEduc2026" // Minimum 8 caractères (WPA2) ou laisser "" pour ouvert
#define WIFI_AP_CHANNEL 6
#define WIFI_AP_MAX_CONN 8
#define WIFI_AP_IP IPAddress(192, 168, 4, 1)
#define WIFI_AP_GATEWAY IPAddress(192, 168, 4, 1)
#define WIFI_AP_SUBNET IPAddress(255, 255, 255, 0)

// ==============================================================================
// 2. CONFIGURATION DU SERVEUR DISTANT (RUNPOD / CLOUD / LOCAL)
// ==============================================================================

// Remplacez par l'adresse IP de votre pod Runpod, votre tunnel ou votre Mac en
// local
#define SERVER_HOST "api.alterniamali.com" // ou IP Runpod ex: "159.223.x.x"
#define SERVER_PORT 443 // 443 pour HTTPS/WSS, 8000 pour HTTP/WS local
#define SERVER_USE_SSL                                                         \
  true // true si connexion sécurisée wss://, false si ws://
#define SERVER_WS_PATH "/ws/esp32"
#define DEVICE_ID "ESP32-ALT-BOX-01"

// Jeton secret partagé pour autoriser l'accès à device.alterniamali.com
#define DEVICE_AUTH_TOKEN "ALT-ESP32-TOKEN-MALI-8899"

// Domaine et URL de l'espace élève (Kiosk tactile & vocal)
#define DEVICE_HOST "device.alterniamali.com"
#define DEVICE_KIOSK_URL "https://device.alterniamali.com/?token=" DEVICE_AUTH_TOKEN

// ==============================================================================
// 3. AFFECTATION DES BROCHES (GPIO PINOUT) - SANS AUCUN CONFLIT
// ==============================================================================

// ── LEDS INDIVIDUELLES (MODE LEDS DISCRÈTES)
// ──────────────────────────────────
#define PIN_LED_GREEN 27  // Vert : ESP32 connecté au serveur Runpod
#define PIN_LED_BLUE 33   // Bleu : Classe 10ème sélectionnée
#define PIN_LED_RED 21    // Rouge : Classe 11ème sélectionnée
#define PIN_LED_YELLOW 19 // Jaune : Classe 12ème (Terminale) sélectionnée
#define PIN_LED_WHITE 4   // Blanc : TTS en train de parler (clignotant)

// ── LED RGB ADRESSABLE WS2812B / NEOPIXEL (OPTION RECOMMANDÉE) ───────────────
// Permet de piloter toutes les couleurs (Vert, Bleu, Rouge, Jaune, Blanc) avec
// 1 seule broche !
#define ENABLE_WS2812B true
#define PIN_NEOPIXEL 18
#define NUM_PIXELS 1 // 1 si LED unique, ou nombre de LEDs sur un anneau/ruban

// ── BOUTONS PHYSIQUES ────────────────────────────────────────────────────────
#define PIN_BUTTON_BOOT 0 // Bouton BOOT intégré à l'ESP32 (Push-to-Talk)

// ── MICROPHONE I2S (ex: INMP441 / SPH0645)
// ────────────────────────────────────
#define I2S_MIC_SCK 14 // Serial Clock (BCLK)
#define I2S_MIC_WS 15  // Word Select (LRCK / Left-Right Clock)
#define I2S_MIC_SD 32  // Serial Data (DATA OUT du micro)
#define I2S_MIC_PORT I2S_NUM_0
#define AUDIO_SAMPLE_RATE                                                      \
  16000 // 16 kHz idéal pour la reconnaissance vocale STT

// ── HAUT-PARLEUR / AMPLIFICATEUR I2S (ex: MAX98357A / DAC)
// ────────────────────
#define I2S_SPK_BCLK 26 // Bit Clock
#define I2S_SPK_LRC 25  // Left-Right Clock (WS)
#define I2S_SPK_DIN 22  // Data In (DIN)
#define I2S_SPK_PORT I2S_NUM_1

// ==============================================================================
// 4. TEMPORISATIONS & CADENCES TEMPS RÉEL
// ==============================================================================
#define PING_INTERVAL_MS 15000 // Heartbeat WebSocket toutes les 15 secondes
#define TELEMETRY_INTERVAL_MS 30000 // Télémétrie toutes les 30 secondes
#define TTS_BLINK_INTERVAL_MS                                                  \
  160 // Vitesse de clignotement blanc pendant la parole TTS

#endif // ALTERNIA_CONFIG_H
