#include "captive_ap.h"
#include "led_manager.h"
#include "websocket_client.h"
#include <esp_wifi.h>

CaptiveApManager captiveAp;

CaptiveApManager::CaptiveApManager()
    : _webServer(80),
      _isApActive(false),
      _isStaActive(false) {}

void CaptiveApManager::begin() {
    Serial.println(F("\n📡 [Wi-Fi Manager] Démarrage du mode Dual AP + Station..."));

    // 1. Mode Dual : Émettre un Point d'Accès tout en se connectant à Internet / Runpod
    WiFi.mode(WIFI_AP_STA);

    // 2. Configurer et démarrer le SoftAP pour les élèves
    WiFi.softAPConfig(WIFI_AP_IP, WIFI_AP_GATEWAY, WIFI_AP_SUBNET);
    bool apOk = WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASSWORD, WIFI_AP_CHANNEL, 0, WIFI_AP_MAX_CONN);

    if (apOk) {
        _isApActive = true;
        Serial.printf("✅ [SoftAP] Point d'Accès actif : SSID « %s »\n", WIFI_AP_SSID);
        Serial.printf("   • IP Passerelle : %s\n", WiFi.softAPIP().toString().c_str());
    } else {
        Serial.println(F("❌ [SoftAP] Échec de création du point d'accès"));
    }

    // 3. Connexion au réseau Internet local (Hotspot 4G ou Box)
    Serial.printf("🌐 [Wi-Fi STA] Connexion à « %s »...\n", WIFI_STA_SSID);
    WiFi.begin(WIFI_STA_SSID, WIFI_STA_PASSWORD);

    // 4. Démarrer le serveur DNS captif intelligent
    _setupDns();

    // 5. Configurer le serveur Web local
    _setupWebServer();
}

void CaptiveApManager::_setupDns() {
    _dnsUdp.begin(53);
    Serial.println(F("🌐 [DNS Server] Serveur DNS captif démarré sur le port UDP 53"));
}

void CaptiveApManager::_processDns() {
    int packetSize = _dnsUdp.parsePacket();
    if (packetSize < 12) return;

    uint8_t buffer[384];
    int len = _dnsUdp.read(buffer, sizeof(buffer));
    if (len < 12) return;

    // Vérifier s'il s'agit d'une requête standard (QR == 0, Opcode == 0)
    uint8_t qr = (buffer[2] >> 7) & 0x01;
    uint8_t opcode = (buffer[2] >> 3) & 0x0F;
    if (qr != 0 || opcode != 0) return;

    // Extraire le nom de domaine de la première question
    String domain = "";
    int pos = 12;
    while (pos < len && buffer[pos] != 0) {
        int labelLen = buffer[pos++];
        for (int i = 0; i < labelLen && pos < len; i++) {
            domain += (char)tolower(buffer[pos++]);
        }
        if (pos < len && buffer[pos] != 0) {
            domain += '.';
        }
    }

    if (pos >= len) return;
    pos++; // Sauter l'octet nul de fin de nom

    if (pos + 4 > len) return;
    uint16_t qType = (buffer[pos] << 8) | buffer[pos + 1];
    int questionEnd = pos + 4;

    // PROTECTION CRITIQUE : Ne jamais piéger alterniamali.com (device.alterniamali.com / api.alterniamali.com)
    // afin que le navigateur se connecte directement aux serveurs réels en HTTPS (port 443)
    if (domain.indexOf("alterniamali") != -1) {
        // Renvoyer NXDOMAIN (Domaine inexistant en local) pour forcer le repli vers le réseau réel
        buffer[2] = 0x81;
        buffer[3] = 0x83; // Flags: Response, NXDOMAIN
        buffer[6] = 0x00; buffer[7] = 0x00; // ANCount = 0
        _dnsUdp.beginPacket(_dnsUdp.remoteIP(), _dnsUdp.remotePort());
        _dnsUdp.write(buffer, questionEnd);
        _dnsUdp.endPacket();
        return;
    }

    // Pour les requêtes IPv6 (AAAA), répondre NoError avec 0 réponse pour forcer le repli IPv4
    if (qType != 1) { // Pas Type A (IPv4)
        buffer[2] = 0x81;
        buffer[3] = 0x80; // Flags: Response, No error
        buffer[6] = 0x00; buffer[7] = 0x00; // ANCount = 0
        _dnsUdp.beginPacket(_dnsUdp.remoteIP(), _dnsUdp.remotePort());
        _dnsUdp.write(buffer, questionEnd);
        _dnsUdp.endPacket();
        return;
    }

    // Réponse Type A (IPv4) : Rediriger toutes les sondes captives vers 192.168.4.1
    buffer[2] = 0x81;
    buffer[3] = 0x80; // Flags: QR=1, RD=1, RA=1, No error
    buffer[4] = 0x00; buffer[5] = 0x01; // QDCount = 1
    buffer[6] = 0x00; buffer[7] = 0x01; // ANCount = 1
    buffer[8] = 0x00; buffer[9] = 0x00; // NSCount = 0
    buffer[10] = 0x00; buffer[11] = 0x00; // ARCount = 0

    // Enregistrement de réponse DNS A
    uint8_t ans[] = {
        0xc0, 0x0c,                   // Pointeur vers le nom de domaine à l'offset 12
        0x00, 0x01,                   // Type: A (Host Address)
        0x00, 0x01,                   // Class: IN (Internet)
        0x00, 0x00, 0x00, 0x3c,       // TTL: 60 secondes
        0x00, 0x04,                   // Longueur des données IP: 4 octets
        192, 168, 4, 1                // IP de redirection : 192.168.4.1
    };

    _dnsUdp.beginPacket(_dnsUdp.remoteIP(), _dnsUdp.remotePort());
    _dnsUdp.write(buffer, questionEnd);
    _dnsUdp.write(ans, sizeof(ans));
    _dnsUdp.endPacket();
}

void CaptiveApManager::_setupWebServer() {
    // Endpoints captifs pour tous les systèmes d'exploitation (iOS, Android, Windows, Mac, Firefox)
    _webServer.on("/", HTTP_GET, [this]() { this->_handleCaptivePortal(); });
    _webServer.on("/device", HTTP_GET, [this]() { this->_handleCaptivePortal(); });
    _webServer.on("/hotspot-detect.html", HTTP_GET, [this]() { this->_handleCaptivePortal(); });
    _webServer.on("/canonical.html", HTTP_GET, [this]() { this->_handleCaptivePortal(); });
    _webServer.on("/generate_204", HTTP_GET, [this]() { this->_handleCaptivePortal(); });
    _webServer.on("/gen_204", HTTP_GET, [this]() { this->_handleCaptivePortal(); });
    _webServer.on("/ncsi.txt", HTTP_GET, [this]() { this->_handleCaptivePortal(); });
    _webServer.on("/connecttest.txt", HTTP_GET, [this]() { this->_handleCaptivePortal(); });
    _webServer.on("/success.txt", HTTP_GET, [this]() { this->_handleCaptivePortal(); });

    // Endpoint d'authentification du dispositif (utilisé par le serveur Runpod)
    _webServer.on("/api/device/verify", HTTP_GET, [this]() { this->_handleDeviceAuth(); });
    _webServer.on("/api/device/status", HTTP_GET, [this]() { this->_handleStatusApi(); });

    // Endpoint de sélection de classe en direct sur le canal ESP
    _webServer.on("/api/select-class", HTTP_ANY, [this]() {
        String c = this->_webServer.arg("classe");
        if (c.length() == 0) c = this->_webServer.arg("c");
        if (c.length() > 0) {
            ledManager.selectClass(c);
            wsClient.sendClassSelected(c);
            this->_webServer.sendHeader("Access-Control-Allow-Origin", "*");
            this->_webServer.send(200, "application/json", "{\"status\":\"ok\",\"selected_class\":\"" + c + "\",\"led\":\"" + ledManager.getCurrentColorName() + "\"}");
        } else {
            this->_webServer.send(400, "application/json", "{\"error\":\"missing_class\"}");
        }
    });

    // En cas d'URL inconnue, rediriger immédiatement
    _webServer.onNotFound([this]() { this->_handleCaptivePortal(); });

    _webServer.begin();
    Serial.println(F("🖥️ [HTTP Server] Portail Web ESP32 démarré sur le port 80"));
}

void CaptiveApManager::_handleCaptivePortal() {
    String deviceKioskUrl = String("https://") + DEVICE_HOST + "/?token=" + DEVICE_AUTH_TOKEN;

    Serial.printf("📲 [Captive Portal] Redirection immédiate du client vers : %s\n", deviceKioskUrl.c_str());

    // 1. Définir le cookie de session de sécurité pour autoriser l'accès à device.alterniamali.com
    _webServer.sendHeader("Set-Cookie", "alternia_box_session=" + String(DEVICE_AUTH_TOKEN) + "; Path=/; Domain=.alterniamali.com");

    // 2. En-têtes HTTP de redirection immédiate 302
    _webServer.sendHeader("Location", deviceKioskUrl, true);
    _webServer.sendHeader("Cache-Control", "no-cache, no-store, must-revalidate");
    _webServer.sendHeader("Pragma", "no-cache");
    _webServer.sendHeader("Expires", "0");
    _webServer.sendHeader("Access-Control-Allow-Origin", "*");

    // 3. Corps HTML avec meta-refresh 0s et JavaScript replace pour une redirection instantanée
    String html = F("<!DOCTYPE html><html lang='fr'><head>"
                    "<meta charset='UTF-8'>"
                    "<meta name='viewport' content='width=device-width,initial-scale=1.0'>"
                    "<meta http-equiv='refresh' content='0;url=");
    html += deviceKioskUrl;
    html += F("'>"
              "<title>AlterniA - Redirection Tuteur</title>"
              "<script>"
              "window.location.replace('");
    html += deviceKioskUrl;
    html += F("');"
              "</script>"
              "<style>"
              "*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,-apple-system,sans-serif;}"
              "body{background:#0D1525;color:#f8fafc;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:24px;text-align:center;}"
              ".card{background:#141B2D;border:1px solid rgba(255,255,255,0.1);border-radius:24px;max-width:400px;width:100%;padding:36px 28px;box-shadow:0 25px 50px rgba(0,0,0,0.6);}"
              ".spinner{width:44px;height:44px;border:3px solid rgba(64,187,204,0.15);border-top:3px solid #40BBCC;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 20px;}"
              "@keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}"
              "h1{font-size:20px;font-weight:800;margin-bottom:8px;letter-spacing:-0.5px;}"
              "p{color:#94a3b8;font-size:14px;line-height:1.5;margin-bottom:24px;}"
              ".btn{display:block;width:100%;padding:14px;background:linear-gradient(135deg,#314999,#0284c7);color:#fff;text-decoration:none;border-radius:16px;font-weight:700;font-size:14px;box-shadow:0 8px 20px rgba(2,132,199,0.3);}"
              "</style></head><body><div class='card'>"
              "<div class='spinner'></div>"
              "<h1>Boîtier AlterniA Mali</h1>"
              "<p>Redirection en cours vers l'Espace Élève...</p>"
              "<a class='btn' href='");
    html += deviceKioskUrl;
    html += F("'>Accéder directement ➔</a>"
              "</div></body></html>");

    _webServer.send(302, "text/html", html);
}

void CaptiveApManager::_handleDeviceAuth() {
    String json = "{";
    json += "\"authorized\": true,";
    json += "\"device_id\": \"" DEVICE_ID "\",";
    json += "\"token\": \"" DEVICE_AUTH_TOKEN "\",";
    json += "\"ap_ssid\": \"" WIFI_AP_SSID "\",";
    json += "\"sta_connected\": " + String(WiFi.status() == WL_CONNECTED ? "true" : "false") + ",";
    json += "\"clients_connected\": " + String(WiFi.softAPgetStationNum());
    json += "}";

    _webServer.sendHeader("Access-Control-Allow-Origin", "*");
    _webServer.send(200, "application/json", json);
}

void CaptiveApManager::_handleStatusApi() {
    String json = "{";
    json += "\"ap_ip\": \"" + WiFi.softAPIP().toString() + "\",";
    json += "\"sta_ip\": \"" + WiFi.localIP().toString() + "\",";
    json += "\"sta_status\": " + String(WiFi.status()) + ",";
    json += "\"clients\": " + String(WiFi.softAPgetStationNum());
    json += "}";

    _webServer.sendHeader("Access-Control-Allow-Origin", "*");
    _webServer.send(200, "application/json", json);
}

void CaptiveApManager::update() {
    _processDns();
    _webServer.handleClient();

    // Vérifier l'état de connexion Station (STA)
    if (WiFi.status() == WL_CONNECTED && !_isStaActive) {
        _isStaActive = true;
        Serial.printf("\n🎉 [Wi-Fi STA] Connecté avec succès à Internet ! IP : %s\n", WiFi.localIP().toString().c_str());
    } else if (WiFi.status() != WL_CONNECTED && _isStaActive) {
        _isStaActive = false;
        Serial.println(F("⚠️ [Wi-Fi STA] Déconnexion d'Internet, tentative de reconnexion..."));
    }
}

int CaptiveApManager::getConnectedStationsCount() const {
    return WiFi.softAPgetStationNum();
}

bool CaptiveApManager::isStationConnected() const {
    return (WiFi.status() == WL_CONNECTED);
}

String CaptiveApManager::getApIp() const {
    return WiFi.softAPIP().toString();
}

String CaptiveApManager::getStaIp() const {
    return WiFi.localIP().toString();
}
