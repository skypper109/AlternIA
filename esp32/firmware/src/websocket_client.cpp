#include "websocket_client.h"
#include "led_manager.h"
#include "audio_manager.h"
#include "captive_ap.h"

Esp32WebSocketClient wsClient;

Esp32WebSocketClient::Esp32WebSocketClient()
    : _isConnected(false),
      _lastPingTime(0),
      _lastTelemetryTime(0) {}

void Esp32WebSocketClient::_webSocketEventWrapper(WStype_t type, uint8_t* payload, size_t length) {
    wsClient._onWebSocketEvent(type, payload, length);
}

void Esp32WebSocketClient::begin() {
    Serial.println(F("\n🌐 [WebSocket Client] Configuration de la liaison vers Runpod..."));
    Serial.printf("   • Hôte : %s:%d\n", SERVER_HOST, SERVER_PORT);
    Serial.printf("   • Chemin : %s\n", SERVER_WS_PATH);

#if SERVER_USE_SSL
    _webSocket.beginSSL(SERVER_HOST, SERVER_PORT, SERVER_WS_PATH);
#else
    _webSocket.begin(SERVER_HOST, SERVER_PORT, SERVER_WS_PATH);
#endif

    _webSocket.onEvent(_webSocketEventWrapper);
    _webSocket.setReconnectInterval(3000);
    _webSocket.enableHeartbeat(15000, 3000, 2);
}

void Esp32WebSocketClient::_onWebSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
    switch (type) {
        case WStype_CONNECTED:
            _isConnected = true;
            Serial.println(F("\n════════════════════════════════════════════════════════════════════════════════"));
            Serial.println(F("🟢 [WebSocket] CONNEXION ÉTABLIE AVEC LE SERVEUR RUNPOD !"));
            Serial.println(F("   • Ordre matériel : LED VERTE ALLUMÉE FIXE"));
            Serial.println(F("════════════════════════════════════════════════════════════════════════════════\n"));

            // 1. ALLUMER LA LED VERTE EN FIXE DÈS LA CONNEXION AU SERVEUR
            ledManager.setServerConnected(true);

            // 2. Envoyer la poignée de main d'authentification avec le jeton du boîtier
            {
                StaticJsonDocument<256> doc;
                doc["type"] = "handshake";
                doc["device_id"] = DEVICE_ID;
                doc["token"] = DEVICE_AUTH_TOKEN;
                doc["ap_ssid"] = WIFI_AP_SSID;
                doc["ap_clients"] = captiveAp.getConnectedStationsCount();
                doc["firmware"] = "2.0-Edge-ESP32";

                String jsonOut;
                serializeJson(doc, jsonOut);
                _webSocket.sendTXT(jsonOut);
            }
            break;

        case WStype_DISCONNECTED:
            _isConnected = false;
            Serial.println(F("🔴 [WebSocket] Déconnecté du serveur Runpod. Tentative de reconnexion..."));
            ledManager.setServerConnected(false);
            break;

        case WStype_TEXT:
            _handleMessage(payload, length);
            break;

        case WStype_BIN:
            // Réception d'un flux audio binaire (ex: synthèse vocale TTS diffusée par le serveur)
            if (length > 0) {
                audioManager.playPcmData(payload, length);
            }
            break;

        case WStype_PONG:
            _lastPingTime = millis();
            break;

        case WStype_ERROR:
            Serial.printf("❌ [WebSocket] Erreur de communication (longueur: %u)\n", length);
            break;

        default:
            break;
    }
}

void Esp32WebSocketClient::_handleMessage(uint8_t* payload, size_t length) {
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, payload, length);

    if (error) {
        Serial.printf("⚠️ [WebSocket] Erreur désérialisation JSON : %s\n", error.c_str());
        return;
    }

    String type = doc["type"] | "";
    String cmd = doc["command"] | "";

    // ── 1. TRAITEMENT DE L'ORDRE DE CHANGEMENT D'ÉTAT OU DE COULEUR ───────────
    if (cmd == "set_state" || type == "state_update" || type == "command") {
        String state = doc["state"] | "";
        String ledColor = doc["led"] | "";
        String selectedClass = doc["selected_class"] | "";
        bool speaking = doc["speaking"] | (state == "SPEAKING") | (ledColor == "BLINK_WHITE") | (ledColor == "WHITE_BLINK");

        // Priorité 1 : Synthèse vocale TTS en cours d'élocution (Blanc Clignotant)
        if (speaking) {
            ledManager.setTtsSpeaking(true);
            return;
        } else if (doc.containsKey("speaking") && !speaking) {
            ledManager.setTtsSpeaking(false);
        }

        // Priorité 2 : État CONNECTÉ au serveur -> LED VERTE ALLUMÉE FIXE OBLIGATOIRE !
        // Garantit que dès la connexion réussie au serveur, la couleur verte s'allume fermement
        if (state == "CONNECTED" || state == "CONNECTED_IDLE" || state == "IDLE" || ledColor == "GREEN") {
            ledManager.setState(STATE_CONNECTED_IDLE);
            Serial.println(F("🟢 [LED] Ordre serveur reçu : CONNECTÉ -> LED VERTE ALLUMÉE FIXE"));
        }
        // Priorité 3 : Couleur explicite demandée par le serveur
        else if (ledColor == "BLUE") {
            ledManager.setState(STATE_CLASS_10EME);
        } else if (ledColor == "RED") {
            ledManager.setState(STATE_CLASS_11EME);
        } else if (ledColor == "YELLOW") {
            ledManager.setState(STATE_CLASS_12EME);
        }
        // Priorité 4 : Classe sélectionnée depuis l'interface élève device.alterniamali.com
        else if (state == "CLASS_SELECTED" || cmd == "select_class" || selectedClass.length() > 0) {
            ledManager.selectClass(selectedClass);
        }
        // Fallback sécurisé : si connecté au serveur, maintenir la LED Verte allumée
        else if (_isConnected) {
            ledManager.setState(STATE_CONNECTED_IDLE);
        }
    }
    // ── 2. RÉCEPTION D'UN PING SERVEUR ────────────────────────────────────────
    else if (type == "ping") {
        StaticJsonDocument<128> pong;
        pong["type"] = "pong";
        pong["time"] = millis();
        String out;
        serializeJson(pong, out);
        _webSocket.sendTXT(out);
    }
}

void Esp32WebSocketClient::sendClassSelected(const String& className) {
    if (!_isConnected) return;

    StaticJsonDocument<256> doc;
    doc["type"] = "class_selected";
    doc["device_id"] = DEVICE_ID;
    doc["selected_class"] = className;
    doc["timestamp"] = millis();

    String jsonOut;
    serializeJson(doc, jsonOut);
    _webSocket.sendTXT(jsonOut);
    Serial.printf("🎓 [WebSocket] Notification classe « %s » transmise au serveur Runpod\n", className.c_str());
}

void Esp32WebSocketClient::sendTelemetry() {
    if (!_isConnected) return;

    StaticJsonDocument<256> doc;
    doc["type"] = "telemetry";
    doc["device_id"] = DEVICE_ID;
    doc["rssi"] = WiFi.RSSI();
    doc["free_heap"] = ESP.getFreeHeap();
    doc["ap_clients"] = captiveAp.getConnectedStationsCount();
    doc["sta_ip"] = captiveAp.getStaIp();
    doc["ap_ip"] = captiveAp.getApIp();
    doc["led_state"] = ledManager.getCurrentStateName();
    doc["led_color"] = ledManager.getCurrentColorName();

    String jsonOut;
    serializeJson(doc, jsonOut);
    _webSocket.sendTXT(jsonOut);
}

void Esp32WebSocketClient::sendButtonPress(const String& buttonName) {
    if (!_isConnected) return;

    StaticJsonDocument<128> doc;
    doc["type"] = "button_press";
    doc["button"] = buttonName;
    doc["timestamp"] = millis();

    String jsonOut;
    serializeJson(doc, jsonOut);
    _webSocket.sendTXT(jsonOut);
    Serial.printf("🔘 [WebSocket] Signal bouton « %s » transmis au serveur\n", buttonName.c_str());
}

void Esp32WebSocketClient::sendVoiceQuery(const String& textQuery) {
    if (!_isConnected) return;

    StaticJsonDocument<256> doc;
    doc["type"] = "voice_query";
    doc["text"] = textQuery;

    String jsonOut;
    serializeJson(doc, jsonOut);
    _webSocket.sendTXT(jsonOut);
}

void Esp32WebSocketClient::sendAudioChunk(const uint8_t* pcmData, size_t length) {
    if (!_isConnected || length == 0) return;
    _webSocket.sendBIN(pcmData, length);
}

void Esp32WebSocketClient::loop() {
    _webSocket.loop();

    // Télémétrie périodique
    unsigned long now = millis();
    if (now - _lastTelemetryTime >= TELEMETRY_INTERVAL_MS) {
        _lastTelemetryTime = now;
        sendTelemetry();
    }
}
