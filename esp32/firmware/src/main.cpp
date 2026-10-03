#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include "config.h"

WebSocketsClient webSocket;

// État actuel du dispositif
String currentState = "DISCONNECTED";
String currentLed = "OFF";
String currentClass = "10eme";
bool isMicPlugged = AUTO_SIMULATE_MIC;
bool isServerConnected = false;

// Variables pour les timers non bloquants
unsigned long lastTelemetryTime = 0;
const unsigned long TELEMETRY_INTERVAL = 5000; // Télémétrie toutes les 5s

unsigned long lastBlinkTime = 0;
bool blinkState = false;

// Gestion du bouton BOOT (GPIO 0)
int lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long DEBOUNCE_DELAY = 50;

// ==============================================================================
// GESTION DES LEDS PHYSIQUES
// ==============================================================================
void setLeds(String color) {
  currentLed = color;

  // Éteindre d'abord toutes les LEDs
  digitalWrite(PIN_LED_GREEN, LOW);
  digitalWrite(PIN_LED_WHITE, LOW);
  digitalWrite(PIN_LED_RED, LOW);
  digitalWrite(PIN_LED_BLUE, LOW);

  if (color == "GREEN") {
    // Connecté avec succès au serveur -> LED Verte (PIN 27)
    digitalWrite(PIN_LED_GREEN, HIGH);
    Serial.println(
        "🟢 [LED] VERT ACTIF (PIN 27) - Connecté au serveur AlternIA !");
  } else if (color == "WHITE") {
    // Classe sélectionnée et micro prêt -> LED Blanche (PIN 26)
    digitalWrite(PIN_LED_WHITE, HIGH);
    // Si la LED blanche n'est pas branchée, on laisse aussi la verte active
    // pour retour visuel
    digitalWrite(PIN_LED_GREEN, HIGH);
    Serial.println("⚪ [LED] BLANC ACTIF (PIN 26 + 27) - Classe sélectionnée & "
                   "Micro prêt !");
  } else if (color == "BLUE" || color == "PULSE") {
    // Traitement IA / Réflexion
    digitalWrite(PIN_LED_BLUE, HIGH);
    Serial.println(
        "🔵 [LED] BLEU ACTIF (PIN 33) - IA en cours de réflexion...");
  } else if (color == "RED") {
    // Déconnecté
    digitalWrite(PIN_LED_RED, HIGH);
    Serial.println("🔴 [LED] ROUGE ACTIF (PIN 25) - Déconnecté.");
  }
}

// ==============================================================================
// ENVOI DE TÉLÉMÉTRIE AU SERVEUR
// ==============================================================================
void sendTelemetry() {
  if (!isServerConnected)
    return;

  JsonDocument doc;
  doc["type"] = "telemetry";
  doc["device_id"] = DEVICE_ID;
  doc["ip"] = WiFi.localIP().toString();
  doc["rssi"] = WiFi.RSSI();
  doc["free_heap"] = ESP.getFreeHeap();
  doc["battery"] = 95;
  doc["mic_plugged"] = isMicPlugged;
  doc["current_class"] = currentClass;
  doc["state"] = currentState;

  String output;
  serializeJson(doc, output);
  webSocket.sendTXT(output);
}

// ==============================================================================
// GESTION DES MESSAGES WEBSOCKET REÇUS DU SERVEUR
// ==============================================================================
void handleWebSocketMessage(uint8_t *payload) {
  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, payload);

  if (error) {
    Serial.printf("❌ Erreur JSON reçu : %s\n", error.c_str());
    return;
  }

  String msgType = doc["type"] | "";
  String command = doc["command"] | "";

  Serial.printf("📥 [Serveur -> ESP32] Type: %s | Commande: %s\n",
                msgType.c_str(), command.c_str());

  if (command == "set_state" || msgType == "command") {
    String newState = doc["state"] | currentState;
    String newLed = doc["led"] | currentLed;
    String newClass = doc["selected_class"] | currentClass;
    bool newMic = doc["mic_plugged"] | isMicPlugged;

    currentState = newState;
    currentClass = newClass;
    isMicPlugged = newMic;

    Serial.printf("👉 Nouvel état : %s | Classe: %s | Micro: %s | LED: %s\n",
                  currentState.c_str(), currentClass.c_str(),
                  isMicPlugged ? "OUI" : "NON", newLed.c_str());

    setLeds(newLed);
  }
}

// ==============================================================================
// CALLBACKS WEBSOCKET
// ==============================================================================
void webSocketEvent(WStype_t type, uint8_t *payload, size_t length) {
  switch (type) {
  case WStype_DISCONNECTED:
    isServerConnected = false;
    currentState = "DISCONNECTED";
    Serial.println("⚠️ [WebSocket] Déconnecté du serveur AlternIA.");
    setLeds("RED");
    break;

  case WStype_CONNECTED:
    isServerConnected = true;
    currentState = "CONNECTED";
    Serial.println("✅ [WebSocket] CONNECTÉ AU SERVEUR ALTERNIA !");

    // Allumage immédiat de la LED Verte dès la connexion réussie !
    setLeds("GREEN");

    // Envoi du message d'enregistrement initial
    {
      JsonDocument doc;
      doc["type"] = "register";
      doc["device_id"] = DEVICE_ID;
      doc["firmware"] = "v2.0-AlternIA-IoT";
      doc["ip"] = WiFi.localIP().toString();
      doc["mic_plugged"] = isMicPlugged;

      String output;
      serializeJson(doc, output);
      webSocket.sendTXT(output);
    }
    break;

  case WStype_TEXT:
    handleWebSocketMessage(payload);
    break;

  case WStype_BIN:
    // Réception audio binaire si applicable
    break;

  case WStype_PING:
  case WStype_PONG:
  case WStype_ERROR:
    break;
  }
}

// ==============================================================================
// CONNEXION AU RÉSEAU WI-FI
// ==============================================================================
void connectWiFi() {
  Serial.println("\n📡 Connexion au Wi-Fi : " + String(WIFI_SSID) + "...");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 15000) {
    // Clignotement vert rapide en cours de recherche Wi-Fi
    digitalWrite(PIN_LED_GREEN, !digitalRead(PIN_LED_GREEN));
    delay(300);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    digitalWrite(PIN_LED_GREEN, LOW);
    Serial.println("\n✅ Wi-Fi connecté !");
    Serial.print("🌐 Adresse IP Locale ESP32 : ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n⚠️ Échec connexion Wi-Fi. Vérifiez les identifiants dans "
                   "include/config.h");
    setLeds("RED");
  }
}

// ==============================================================================
// INITIALISATION SETUP
// ==============================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("==================================================");
  Serial.println("🌟 AlternIA ESP32 Hardware Bridge v2.0");
  Serial.println("   Broche 27 : LED Verte (Liaison Serveur)");
  Serial.println("   Broche 26 : LED Blanche (Classe & Micro)");
  Serial.println("   Broche 0  : Bouton BOOT (Simuler Voix/PTT)");
  Serial.println("==================================================");

  // Configuration des broches en sortie
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_WHITE, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_LED_BLUE, OUTPUT);

  // Bouton BOOT (GPIO 0 avec résistance de tirage vers le haut)
  pinMode(PIN_BOOT_BTN, INPUT_PULLUP);

  // Éteindre les LEDs au démarrage
  setLeds("OFF");

  // Connexion Wi-Fi
  connectWiFi();

  // Initialisation du client WebSocket
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("🔌 Connexion au serveur : ws%s://%s:%d%s\n",
                  USE_SSL ? "s" : "", SERVER_HOST, SERVER_PORT, SERVER_WS_PATH);

    if (USE_SSL) {
      webSocket.beginSSL(SERVER_HOST, SERVER_PORT, SERVER_WS_PATH);
    } else {
      webSocket.begin(SERVER_HOST, SERVER_PORT, SERVER_WS_PATH);
    }

    webSocket.onEvent(webSocketEvent);
    webSocket.setReconnectInterval(3000); // Reconnexion auto toutes les 3s
  }
}

// ==============================================================================
// BOUCLE PRINCIPALE LOOP
// ==============================================================================
void loop() {
  // Boucle WebSocket
  webSocket.loop();

  // 1. Gestion de la reconnexion Wi-Fi si perdue
  if (WiFi.status() != WL_CONNECTED) {
    // Clignotement lent rouge/vert
    if (millis() - lastBlinkTime > 1000) {
      lastBlinkTime = millis();
      blinkState = !blinkState;
      digitalWrite(PIN_LED_GREEN, blinkState ? HIGH : LOW);
    }
    return;
  }

  // 2. Gestion du bouton BOOT (GPIO 0)
  int reading = digitalRead(PIN_BOOT_BTN);
  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > DEBOUNCE_DELAY) {
    // Bouton pressé (LOW car pull-up)
    if (reading == LOW && lastButtonState == HIGH) {
      Serial.println("🔘 [BOUTON BOOT PRESSÉ] Demande de parole élève !");

      if (isServerConnected) {
        JsonDocument doc;
        doc["type"] = "button_press";
        doc["button"] = "boot";
        doc["device_id"] = DEVICE_ID;
        doc["class"] = currentClass;

        String output;
        serializeJson(doc, output);
        webSocket.sendTXT(output);
      }
    }
  }
  lastButtonState = reading;

  // 3. Envoi périodique de télémétrie
  if (millis() - lastTelemetryTime > TELEMETRY_INTERVAL) {
    lastTelemetryTime = millis();
    sendTelemetry();
  }
}
