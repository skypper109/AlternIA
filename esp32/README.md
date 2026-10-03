# 📡 AlternIA - Passerelle Matérielle ESP32 & Connexion Serveur Distant

Ce dossier contient l'ensemble de la logique, du firmware et des outils de simulation pour connecter un microcontrôleur **ESP32** au serveur distant **AlternIA** (Google Colab Pro, AWS GPU ou serveur local).

---

## 🌟 Logique Fonctionnelle Demandée

1. **Connexion au Serveur Distant** :
   - Dès que l'ESP32 établit la connexion WebSocket avec le serveur (`/ws/esp32`), la **LED VERTE (Broche 27)** s'allume en continu.
2. **Sélection de Classe & Microphone** :
   - Dès qu'une classe est sélectionnée (ex: 10ème, 11ème, Terminale TSE) et que le microphone est prêt/connecté, la **LED BLANCHE (Broche 26)** s'allume.
3. **Simulation Complète** :
   - Si vous n'avez qu'une seule LED sur le PIN 27, le code gère l'état et vous pouvez également tester l'ensemble des scénarios via le **tableau de bord web** ou le **simulateur Python**.

---

## 🔌 Schéma de Câblage Matériel (GPIO Pinout)

| Composant | Broche ESP32 (GPIO) | Description / Rôle |
| :--- | :---: | :--- |
| **LED Verte** | **PIN 27** | **Allumée fixe** dès que l'ESP32 est connecté au serveur distant. |
| **LED Blanche** | **PIN 26** | **Allumée fixe** lorsqu'une classe est sélectionnée et le micro actif. |
| **LED Rouge** *(optionnel)* | **PIN 25** | Indique la déconnexion ou la recherche de réseau Wi-Fi. |
| **LED Bleue** *(optionnel)* | **PIN 33** | Indique le traitement IA (RAG / LLM en réflexion). |
| **Bouton BOOT** | **GPIO 0** | Bouton physique déjà intégré à votre carte ESP32. Sert de Push-to-Talk pour prendre la parole. |
| **Microphone** | **GPIO 34 / I2S** | Entrée audio micro ou jack de détection. |

> [!TIP]
> **Vous avez déjà branché la LED sur le PIN 27 ?**
> Le code l'utilise directement comme indicateur de connexion réussie au serveur.

---

## 📁 Structure du Dossier

```
AlternIA/esp32/
├── README.md                      # Ce guide complet
├── firmware/                      # Projet PlatformIO C++ pour votre ESP32 physique
│   ├── platformio.ini             # Dépendances (WebSockets, ArduinoJson)
│   ├── include/
│   │   └── config.h               # Wi-Fi SSID, IP serveur, assignation des broches
│   └── src/
│       └── main.cpp               # Logique temps réel WebSocket & contrôle des LEDs
└── simulator/
    └── esp32_simulator.py         # Simulateur Python avec affichage des LEDs en console
```

---

## 🚀 Étape 1 : Démarrer le Serveur AlternIA

Vous pouvez lancer le serveur localement ou via Google Colab :

### Option A : Lancement Local
```bash
cd /Users/ibrahimsorydiallo/Desktop/OSC/AlternIA
./.venv/bin/python cloud/colab_server.py --port 8000
# ou simplement :
./.venv/bin/uvicorn backend.src.main:app --host 0.0.0.0 --port 8000
```

Le serveur sera alors joignable sur :
- **Tableau de bord de test ESP32** : `http://localhost:8000/esp32` (ou `/api/esp32/dashboard`)
- **WebSocket ESP32** : `ws://127.0.0.1:8000/ws/esp32` (ou `ws://192.168.100.223:8000/ws/esp32`)
- **Interface Kiosk Élève** : `http://localhost:8000/device/`

---

## 🎮 Étape 2 : Simuler le Tout Immédiatement (Sans attendre)

Pour voir la logique en action et tester les transitions de LEDs :

1. Ouvrez le tableau de bord web : [http://localhost:8000/esp32](http://localhost:8000/esp32)
2. Dans un second terminal, lancez le simulateur console :
```bash
python3 /Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/esp32/simulator/esp32_simulator.py
```
3. Vous verrez immédiatement :
   - La **LED Verte** s'allumer dès la connexion établie.
   - En appuyant sur **[1]**, **[2]** ou **[3]** (ou en cliquant sur une classe dans le Kiosk), la **LED Blanche** s'allume.
   - En appuyant sur **[5]** (Bouton BOOT), le signal de parole est transmis au serveur distant.

---

## ⚡ Étape 3 : Flasher votre ESP32 Physique

Votre ESP32 est actuellement branché sur votre Mac sur le port série `/dev/cu.usbserial-0001`.

1. Éditez [config.h](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/esp32/firmware/include/config.h) pour renseigner votre Wi-Fi :
```cpp
#define WIFI_SSID       "Votre_Nom_WiFi"
#define WIFI_PASSWORD   "Votre_Mot_De_Passe"
#define SERVER_HOST     "192.168.100.223" // Votre Mac sur le Wi-Fi
```
2. Téléversez le code dans l'ESP32 :
```bash
cd /Users/ibrahimsorydiallo/Documents/PlatformIO/Projects/test1
pio run -t upload
```
3. Ouvrez le moniteur série pour voir les messages en temps réel :
```bash
pio device monitor -b 115200
```
Dès que l'ESP32 se connecte à votre réseau Wi-Fi et au serveur, **la LED du PIN 27 s'allume en VERT** !
