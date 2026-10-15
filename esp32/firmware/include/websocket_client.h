#ifndef WEBSOCKET_CLIENT_H
#define WEBSOCKET_CLIENT_H

#include <Arduino.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include "config.h"

class Esp32WebSocketClient {
public:
    Esp32WebSocketClient();
    void begin();
    void loop();

    bool isConnected() const { return _isConnected; }
    void sendTelemetry();
    void sendButtonPress(const String& buttonName = "boot");
    void sendClassSelected(const String& className);
    void sendVoiceQuery(const String& textQuery);
    void sendAudioChunk(const uint8_t* pcmData, size_t length);

private:
    WebSocketsClient _webSocket;
    bool _isConnected;
    unsigned long _lastPingTime;
    unsigned long _lastTelemetryTime;

    void _handleMessage(uint8_t* payload, size_t length);
    void _onWebSocketEvent(WStype_t type, uint8_t* payload, size_t length);
    static void _webSocketEventWrapper(WStype_t type, uint8_t* payload, size_t length);
};

extern Esp32WebSocketClient wsClient;

#endif // WEBSOCKET_CLIENT_H
