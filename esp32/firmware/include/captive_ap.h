#ifndef CAPTIVE_AP_H
#define CAPTIVE_AP_H

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <WebServer.h>
#include "config.h"

class CaptiveApManager {
public:
    CaptiveApManager();
    void begin();
    void update();

    // Télémétrie
    int getConnectedStationsCount() const;
    bool isStationConnected() const;
    String getApIp() const;
    String getStaIp() const;

private:
    WiFiUDP _dnsUdp;
    WebServer _webServer;
    bool _isApActive;
    bool _isStaActive;

    void _setupDns();
    void _processDns();
    void _setupWebServer();
    void _handleCaptivePortal();
    void _handleDeviceAuth();
    void _handleStatusApi();
};

extern CaptiveApManager captiveAp;

#endif // CAPTIVE_AP_H
