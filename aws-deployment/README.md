# 🇲🇱 AlternIA — Déploiement & Configuration Automatique sur AWS EC2 `t3.xlarge`

Ce dossier contient l'infrastructure de déploiement haute disponibilité pour faire tourner **AlternIA** sur une instance **AWS EC2 `t3.xlarge`** (4 vCPUs / 16 Go de RAM).

La configuration est conçue pour un **fonctionnement 100% autonome (« Zero-Touch »)** :  
Dès que l'instance est démarrée ou redémarrée dans la console AWS, **tous les services s'exécutent directement en arrière-plan sans aucune commande manuelle**, se réparent automatiquement en cas de plantage et se reconnectent immédiatement aux noms de domaine officiels sécurisés en HTTPS.

---

## 📋 Table des Matières

1. [Architecture & Dimensionnement sur `t3.xlarge`](#1-architecture--dimensionnement-sur-t3xlarge)
2. [Création de l'Instance sur AWS (Guide Pas-à-Pas)](#2-création-de-linstance-sur-aws-guide-pas-à-pas)
3. [Méthode 1 : Lancement 100% Automatique via AWS User Data (Recommandé)](#3-méthode-1--lancement-100-automatique-via-aws-user-data)
4. [Méthode 2 : Installation sur une Instance AWS Déjà Créée](#4-méthode-2--installation-sur-une-instance-aws-déjà-créée)
5. [Fonctionnement de l'Auto-Start au Boot (Systemd)](#5-fonctionnement-de-lauto-start-au-boot-systemd)
6. [Routage des Noms de Domaine Officiels](#6-routage-des-noms-de-domaine-officiels)
7. [Connexion de l'Application Mobile Flutter](#7-connexion-de-lapplication-mobile-flutter)
8. [Surveillance, Logs et Auto-Guérison (Watchdog)](#8-surveillance-logs-et-auto-guérison-watchdog)
9. [Mise à Jour du Code & Redémarrage Zéro-Downtime](#9-mise-à-jour-du-code--redémarrage-zéro-downtime)
10. [Alternative Docker Compose](#10-alternative-docker-compose)

---

## 1. Architecture & Dimensionnement sur `t3.xlarge`

L'instance **AWS EC2 `t3.xlarge`** est idéale pour la charge nationale d'AlternIA :
* **4 vCPUs** : Exploités par 4 workers Uvicorn parallèles indépendants + multithreading pour l'analyse vectorielle et les embeddings.
* **16 Go de RAM** : Permet de maintenir en mémoire vive l'index vectoriel Qdrant de tout le programme curriculaire malien (Fondamental + Lycée), le cache des conversations et les modèles de traitement du langage sans aucun risque d'OOM.
* **Swap de 4 Go** configuré pour encaisser les pics de trafic lors des examens (DEF et BAC).
* **Cloudflare Tunnel (`cloudflared`)** : Établit un tunnel sortant sécurisé vers le réseau mondial de Cloudflare. **Aucun port entrant public n'a besoin d'être ouvert dans le Security Group AWS**, ce qui élimine 100% des attaques DDoS et des scans de ports.

```
                                  [ CLOUDFLARE EDGE ]
                                           |
                           (Tunnel Sortant Chiffré TLS)
                                           v
+-----------------------------------------------------------------------------------------+
| AWS EC2 t3.xlarge (Ubuntu 22.04/24.04 LTS)                                              |
|                                                                                         |
|  [alternia-tunnel.service] (cloudflared daemon)                                         |
|            |                                                                            |
|            +---> http://127.0.0.1:8000 (FastAPI 4-Workers)                              |
|                         |                                                               |
|                         +---> [alternia-backend.service]                                |
|                         |       - Worker 1 (CPU 0)                                      |
|                         |       - Worker 2 (CPU 1)                                      |
|                         |       - Worker 3 (CPU 2)                                      |
|                         |       - Worker 4 (CPU 3)                                      |
|                         |                                                               |
|                         +---> [qdrant.service] (Base Vectorielle RAG - Port 6333)       |
|                         |                                                               |
|                         +---> [Interfaces Statiques Servies]                            |
|                                 - device.alterniamali.com (Kiosk Tactile Élève)         |
|                                 - admin.alterniamali.com  (Portail Direction Alta)      |
|                                 - api.alterniamali.com    (API Mobile & ESP32)          |
|                                                                                         |
|  [alternia-watchdog.timer] (Vérification toutes les 30s + Auto-Restart si panne)       |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Création de l'Instance sur AWS (Guide Pas-à-Pas)

Dans la console AWS EC2 (**EC2 > Instances > Lancer une instance**) :

1. **Nom** : `AlternIA-Production-Server`
2. **Image AMI** : `Ubuntu Server 24.04 LTS` ou `Ubuntu Server 22.04 LTS` (64-bit x86 / amd64).
3. **Type d'instance** : `t3.xlarge` (4 vCPUs, 16 GiB RAM).
4. **Paire de clés** : Choisissez votre clé SSH (ex: `alternia-key.pem`).
5. **Paramètres réseau (Security Group)** :
   * Autoriser le trafic SSH (port 22) depuis votre IP.
   * *Note de sécurité :* Grâce au tunnel Cloudflare, vous n'avez **pas besoin d'ouvrir les ports 80 ou 443 au monde entier** ! Le tunnel fonctionne de l'intérieur vers l'extérieur.
6. **Stockage (Disque EBS)** :
   * Taille : **50 Go** (ou plus) en type **`gp3`** (3000 IOPS / 125 Mo/s inclus).

---

## 3. Méthode 1 : Lancement 100% Automatique via AWS User Data

C'est la méthode **la plus rapide et sans intervention humaine**.

Lors de la création de votre instance à l'étape 2 :
1. Déroulez la section tout en bas : **Détails avancés (Advanced details)**.
2. Allez dans le champ : **Données utilisateur (User data)**.
3. Copiez-collez l'intégralité du script :  
   👉 **[`user_data_cloud_init.sh`](file:///Users/ibrahimsorydiallo/Desktop/OSC/AlternIA/aws-deployment/user_data_cloud_init.sh)**
4. Cliquez sur **Lancer l'instance**.

### Que fait ce script tout seul au boot ?
* Alloue et active le swap de 4 Go.
* Ajuste les limites noyau Linux (`max_map_count=262144`, `somaxconn=65535`).
* Installe tous les paquets système nécessaires (`ffmpeg`, `poppler`, `tesseract`, audio, etc.).
* Télécharge et installe nativement **Qdrant** sur le port 6333.
* Télécharge et configure **Cloudflare Tunnel**.
* Active l'environnement virtuel Python et prépare les services systemd.
* Active le démarrage automatique au démarrage de l'instance.

Dès que vous copiez le code source dans `/home/ubuntu/AlternIA` et renseignez le fichier `.env`, tous les services démarrent immédiatement !

---

## 4. Méthode 2 : Installation sur une Instance AWS Déjà Créée

Si vous avez déjà une instance `t3.xlarge` en marche :

1. Connectez-vous en SSH :
   ```bash
   ssh -i /chemin/vers/cle.pem ubuntu@IP_PUBLIQUE_AWS
   ```

2. Transférez le code du projet AlternIA dans `/home/ubuntu/AlternIA` (ou clonez votre dépôt Git) :
   ```bash
   cd /home/ubuntu
   git clone https://votre-repo/AlternIA.git
   cd AlternIA
   ```

3. Assurez-vous que votre fichier `.env` est bien configuré (vos clés API Groq/Gemini et votre `CLOUDFLARE_TUNNEL_TOKEN`).

4. Lancez le script de configuration parfaite :
   ```bash
   chmod +x aws-deployment/setup_aws_t3_xlarge.sh
   sudo ./aws-deployment/setup_aws_t3_xlarge.sh
   ```

Le script configure tout en 2 minutes et affiche les statuts de confirmation.

---

## 5. Fonctionnement de l'Auto-Start au Boot (Systemd)

Le serveur utilise la suite de services systemd suivante configurée avec `Restart=always` et `WantedBy=multi-user.target` :

* **`qdrant.service`** : Moteur de recherche vectoriel démarré en premier.
* **`alternia-backend.service`** : Serveur FastAPI démarré avec 4 workers Uvicorn.
* **`alternia-tunnel.service`** : Tunnel Cloudflare reconnectant instantanément les 4 domaines officiels.
* **`alternia-watchdog.timer`** : Lance le vérificateur de santé toutes les 30 secondes.

### ⚡ Test de l'extinction / redémarrage
Vous pouvez arrêter l'instance dans la console AWS (**Arrêter l'instance**) pour économiser des coûts, puis la redémarrer (**Démarrer l'instance**) :  
**En moins de 10 secondes après le démarrage du système, tous les services et vos sites web sont 100% fonctionnels sans que vous n'ayez besoin d'ouvrir une session SSH !**

---

## 6. Routage des Noms de Domaine Officiels

Le serveur gère automatiquement l'aiguillage du trafic en fonction du nom d'hôte (`Host` / `X-Forwarded-Host`) :

| Nom de Domaine | Destination / Rôle |
| :--- | :--- |
| **`https://alterniamali.com`** | Portail public d'AlternIA Mali. |
| **`https://api.alterniamali.com`** | Endpoints API pour l'Application Mobile Flutter & synchronisation. |
| **`https://admin.alterniamali.com`** | Backoffice d'Administration Alta (Directeurs d'école, Professeurs). |
| **`https://device.alterniamali.com`** | Interface tactile et vocale Kiosk Élève (Fondamental & Lycée). |

---

## 7. Connexion de l'Application Mobile Flutter

L'application mobile Flutter (`det-mobile`) est déjà configurée pour pointer de façon transparente vers l'URL officielle :
```
https://api.alterniamali.com
```

Aucun changement d'adresse IP ou de port n'est nécessaire pour les élèves ou les parents : la connexion est permanente et chiffrée de bout en bout en HTTPS.

---

## 8. Surveillance, Logs et Auto-Guérison (Watchdog)

### Commandes utiles pour inspecter les services :

* **Voir l'état général des 3 services** :
  ```bash
  systemctl status qdrant alternia-backend alternia-tunnel
  ```

* **Consulter les logs du backend en temps réel** :
  ```bash
  journalctl -u alternia-backend -f
  ```

* **Consulter les logs du tunnel Cloudflare** :
  ```bash
  journalctl -u alternia-tunnel -f
  ```

* **Consulter les logs de Qdrant** :
  ```bash
  journalctl -u qdrant -f
  ```

* **Lancer un test de santé manuel** :
  ```bash
  sudo /home/ubuntu/AlternIA/aws-deployment/scripts/healthcheck.sh
  ```

---

## 9. Mise à Jour du Code & Redémarrage Zéro-Downtime

Lorsque vous effectuez des modifications sur votre code :
```bash
cd /home/ubuntu/AlternIA
./aws-deployment/scripts/update_and_restart.sh
```
Ce script :
1. Récupère les derniers commits (`git pull`).
2. Met à jour les dépendances Python (`pip install -r requirements.txt`).
3. Recompile les interfaces frontend si nécessaire.
4. Redémarre proprement les workers FastAPI sans perte de connexion.

---

## 10. Alternative Docker Compose

Si vous préférez exécuter AlternIA dans des conteneurs Docker :

1. Démarrez la pile Docker complète avec politique `restart: always` :
   ```bash
   cd /home/ubuntu/AlternIA/aws-deployment/docker
   docker compose up -d
   ```
2. Vérifiez l'état des conteneurs :
   ```bash
   docker compose ps
   ```
Tous les conteneurs redémarreront automatiquement au redémarrage de la machine grâce au démon Docker.
