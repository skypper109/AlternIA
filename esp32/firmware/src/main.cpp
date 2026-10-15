/**
 * ══════════════════════════════════════════════════════════════════════════════
 * ALTERNIA - PASSERELLE MATÉRIELLE ESP32 (IOT & AUDIO EDGE MALI)
 * Dispositif passerelle intermédiaire avant l'arrivée du RDK X5 (D-Robotics)
 * ══════════════════════════════════════════════════════════════════════════════
 * 
 * Fonctionnalités implémentées :
 * 1. Double Wi-Fi (AP + STA) :
 *    - SoftAP « AlterniA-Box-Mali » (192.168.4.1) avec portail captif DNS.
 *    - Permet l'accès exclusif à device.alterniamali.com aux élèves connectés au boîtier.
 * 2. Liaison WebSocket temps réel vers le serveur Runpod (/ws/esp32).
 * 3. Logique des LEDs d'état (Discrètes & NeoPixel WS2812B) :
 *    - Connecté au serveur Runpod : VERT allumé fixe.
 *    - Classe 10ème sélectionnée sur device : BLEU allumé fixe.
 *    - Classe 11ème sélectionnée sur device : ROUGE allumé fixe.
 *    - Classe 12ème sélectionnée sur device : JAUNE allumé fixe.
 *    - Synthèse vocale TTS en train de parler : BLANC clignotant.
 * 4. Préparation audio I2S complète :
 *    - Microphone I2S (INMP441) pour la transmission vocale.
 *    - Haut-parleur / DAC I2S (MAX98357A) pour la restitution audio TTS.
 *    - Bouton BOOT (GPIO 0) pour le Push-to-Talk physique.
 */

#include <Arduino.h>
#include "config.h"
#include "led_manager.h"
#include "audio_manager.h"
#include "captive_ap.h"
#include "websocket_client.h"

// Gestion du bouton physique Push-to-Talk (GPIO 0)
static bool lastButtonState = HIGH;
static unsigned long buttonPressStartTime = 0;
static uint8_t micBuffer[1024];

void setup() {
    Serial.begin(115200);
    delay(500);

    Serial.println(F("\n\n"));
    Serial.println(F("╔══════════════════════════════════════════════════════════════════════════════╗"));
    Serial.println(F("║              ALTERNIA - DISPOSITIF INTELLIGENT ESP32 (MALI)                  ║"));
    Serial.println(F("║       Passerelle Matérielle, Audio I2S & Point d'Accès Sécurisé Runpod       ║"));
    Serial.println(F("╚══════════════════════════════════════════════════════════════════════════════╝"));

    // 1. Initialiser le gestionnaire de LEDs
    ledManager.begin();

    // 2. Initialiser le pipeline Audio I2S (Microphone + Haut-parleur)
    audioManager.begin();

    // 3. Démarrer le Point d'Accès Wi-Fi (SoftAP) et le portail captif DNS
    captiveAp.begin();

    // 4. Initialiser la connexion WebSocket vers le serveur distant Runpod
    wsClient.begin();

    // 5. Configurer le bouton physique BOOT (GPIO 0)
    pinMode(PIN_BUTTON_BOOT, INPUT_PULLUP);

    Serial.println(F("\n🚀 [Système] Démarrage terminé. Le boîtier est prêt et écoute les événements !\n"));
}

void loop() {
    // 1. Traitement du portail captif et DNS
    captiveAp.update();

    // 2. Traitement de la liaison WebSocket vers Runpod
    wsClient.loop();

    // 3. Animation non-bloquante des LEDs (ex: clignotement blanc pendant TTS)
    ledManager.update();

    // 4. Gestion du bouton physique Push-to-Talk (Bouton BOOT GPIO 0)
    bool currentButtonState = digitalRead(PIN_BUTTON_BOOT);

    // Appui détecté (front descendant, pullup actif à l'état bas)
    if (lastButtonState == HIGH && currentButtonState == LOW) {
        buttonPressStartTime = millis();
        Serial.println(F("🎙️ [Bouton BOOT] Appui détecté : Début de prise de parole !"));
        
        // Notifier le serveur Runpod
        wsClient.sendButtonPress("boot_press");
        
        // Démarrer la capture micro I2S
        audioManager.startRecording();
    }
    // Relâchement du bouton (front montant)
    else if (lastButtonState == LOW && currentButtonState == HIGH) {
        unsigned long duration = millis() - buttonPressStartTime;
        Serial.printf("⏹️ [Bouton BOOT] Relâché après %lu ms : Fin de prise de parole.\n", duration);
        
        // Arrêter la capture audio
        audioManager.stopRecording();
        wsClient.sendButtonPress("boot_release");
    }
    lastButtonState = currentButtonState;

    // 5. Si le micro est en cours d'enregistrement, streamer les données audio vers Runpod
    if (audioManager.isRecording()) {
        size_t bytesRead = audioManager.recordPcmData(micBuffer, sizeof(micBuffer));
        if (bytesRead > 0 && wsClient.isConnected()) {
            wsClient.sendAudioChunk(micBuffer, bytesRead);
        }
    }

    // Petite pause pour céder le temps CPU au RTOS de l'ESP32
    vTaskDelay(1);
}
