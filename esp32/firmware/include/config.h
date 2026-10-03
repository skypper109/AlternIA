/**
 * AlternIA ESP32 Configuration File
 * Définit le Wi-Fi, l'adresse du serveur distant AlternIA et l'assignation des broches (GPIO).
 */

#ifndef ALTERNIA_CONFIG_H
#define ALTERNIA_CONFIG_H

// ==============================================================================
// 1. CONFIGURATION WI-FI
// Remplacez par le nom de votre réseau Wi-Fi (ex: box internet ou partage de connexion 4G/5G)
// Note : L'ESP32 supporte les réseaux 2.4 GHz.
// ==============================================================================
#define WIFI_SSID       "VOTRE_WIFI_SSID"
#define WIFI_PASSWORD   "VOTRE_WIFI_PASSWORD"

// ==============================================================================
// 2. CONFIGURATION DU SERVEUR DISTANT ALTERNIA
// ==============================================================================
// OPTION A (Réseau Local Mac) : 192.168.100.223 (IP de votre machine sur le réseau local)
#define SERVER_HOST     "192.168.100.223"
#define SERVER_PORT     8000
#define SERVER_WS_PATH  "/ws/esp32"
#define USE_SSL         false

// OPTION B (Cloudflare Tunnel / Google Colab / AWS GPU) :
// Décommentez ci-dessous si vous vous connectez au serveur Colab distant via tunnel HTTPS/WSS :
// #define SERVER_HOST     "api.alterniamali.com"
// #define SERVER_PORT     443
// #define SERVER_WS_PATH  "/ws/esp32"
// #define USE_SSL         true

// Identifiant unique du boîtier pour la flotte
#define DEVICE_ID       "ESP32-ALT-01"

// ==============================================================================
// 3. ASSIGNATION DES BROCHES PHYSIQUES (PINOUT GPIO)
// ==============================================================================
// Broche 27 : LED Verte (Signal de connexion au serveur réussie)
#define PIN_LED_GREEN   27

// Broche 26 : LED Blanche (Classe sélectionnée + Micro prêt à l'écoute)
#define PIN_LED_WHITE   26

// Broche 25 : LED Rouge optionnelle (Déconnecté / Erreur)
#define PIN_LED_RED     25

// Broche 33 : LED Bleue optionnelle (Traitement IA / Réflexion RAG)
#define PIN_LED_BLUE    33

// Bouton physique BOOT intégré à l'ESP32 (GPIO 0)
// Permet de simuler la prise de parole sans aucun composant externe supplémentaire !
#define PIN_BOOT_BTN    0

// Broche de détection physique du microphone (ou bouton PTT externe)
#define PIN_MIC_DETECT  34

// Si true : Considère le micro branché automatiquement (idéal si vous n'avez pas encore soudé le jack)
#define AUTO_SIMULATE_MIC true

#endif // ALTERNIA_CONFIG_H
