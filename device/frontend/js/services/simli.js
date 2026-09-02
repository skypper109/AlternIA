/**
 * Service de streaming d'avatar vidéo interactif photoréaliste via le SDK Simli WebRTC v3.x.x.
 * Utilise le flux session_token (generateSimliSessionToken) au lieu de passer l'API key au constructeur.
 */

import { SimliClient, generateSimliSessionToken } from 'simli-client';

export class SimliService {
  constructor(videoElementId = 'modal-avatar-video', audioElementId = 'simli-audio') {
    this.videoElementId = videoElementId;
    this.audioElementId = audioElementId;
    this.videoElement = document.getElementById(videoElementId);
    this.audioElement = document.getElementById(audioElementId);
    this.client = null;
    this.isConnected = false;
    this.isConnecting = false;
    this.apiKey = "1e1ikibdppliekw9mt04nf";
    this.faceId = "b9e5fba3-071a-4e35-896e-211c4d6eaa7b";
  }

  getVideoElement() {
    if (!this.videoElement) {
      this.videoElement = document.getElementById(this.videoElementId);
    }
    return this.videoElement;
  }

  getAudioElement() {
    if (!this.audioElement) {
      this.audioElement = document.getElementById(this.audioElementId);
    }
    return this.audioElement;
  }



  async init(customFaceId = null) {
    if (this.isConnected || this.isConnecting) return;
    this.isConnecting = true;

    if (customFaceId) {
      this.faceId = customFaceId;
    }

    const videoEl = this.getVideoElement();
    const audioEl = this.getAudioElement();

    const statusText = document.getElementById('modal-status-text');
    const statusDot = document.getElementById('modal-status-dot');
    if (statusText) statusText.textContent = "Connexion à l'avatar Simli...";
    if (statusDot) statusDot.className = "w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse";

    try {
      console.log(`🚀 [SimliService] Connexion WebRTC Simli v3 (Face ID: ${this.faceId})...`);

      if (!SimliClient) {
        throw new Error("Classe SimliClient introuvable.");
      }

      // Étape 1 : Obtenir un session_token via l'API Simli
      let sessionToken;
      if (generateSimliSessionToken) {
        const tokenResponse = await generateSimliSessionToken({
          apiKey: this.apiKey,
          config: {
            faceId: this.faceId,
            handleSilence: true,
            maxSessionLength: 600,
            maxIdleTime: 180,
          }
        });
        sessionToken = tokenResponse.session_token;
        console.log("🔑 [SimliService] Session token obtenu avec succès.");
      } else {
        // Fallback : obtenir le token via fetch direct si la fonction n'est pas exportée
        const tokenRes = await fetch("https://api.simli.ai/startAudioToVideoSession", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            apiKey: this.apiKey,
            faceId: this.faceId,
            handleSilence: true,
            maxSessionLength: 600,
            maxIdleTime: 180,
          })
        });
        const tokenData = await tokenRes.json();
        sessionToken = tokenData.session_token;
        console.log("🔑 [SimliService] Session token obtenu via API directe.");
      }

      if (!sessionToken) {
        throw new Error("Impossible d'obtenir un session_token Simli.");
      }

      this.client = new SimliClient(
        sessionToken,
        videoEl,
        audioEl,
        [], // iceServers (vide pour LiveKit)
        0, // logLevel (0 = DEBUG)
        "livekit" // transport_mode obligatoire pour LiveKit
      );

      // Étape 3 : Écouter les événements v3.x.x
      this.client.on("start", () => {
        console.log("✅ [SimliService] Avatar Simli connecté et rendu vidéo actif !");
        this.isConnected = true;
        this.isConnecting = false;
        if (videoEl) {
          videoEl.classList.remove('opacity-0');
          videoEl.classList.add('opacity-100');
          videoEl.play().catch(() => {});
        }
        if (statusText) statusText.textContent = "Prof Hamza est en direct !";
        if (statusDot) statusDot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse";
      });

      this.client.on("stop", (reason) => {
        console.log("ℹ️ [SimliService] Session Simli terminée :", reason);
        this._cleanup(videoEl, statusText, statusDot);
      });

      this.client.on("error", (reason) => {
        console.warn("⚠️ [SimliService] Erreur WebRTC Simli :", reason);
        this._cleanup(videoEl, statusText, statusDot);
      });

      this.client.on("startup_error", (reason) => {
        console.warn("⚠️ [SimliService] Erreur de démarrage Simli :", reason);
        this._cleanup(videoEl, statusText, statusDot);
      });

      // Étape 4 : Démarrer la connexion WebRTC
      await this.client.start();

    } catch (err) {
      this.isConnecting = false;
      this.isConnected = false;
      console.warn("⚠️ [SimliService] Échec initialisation SimliClient (mode vocal local sécurisé) :", err.message || err);
      if (statusText) statusText.textContent = "Prêt à répondre";
      if (statusDot) statusDot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400";
    }
  }

  _cleanup(videoEl, statusText, statusDot) {
    this.isConnected = false;
    this.isConnecting = false;
    this.client = null;
    if (videoEl) {
      videoEl.classList.remove('opacity-100');
      videoEl.classList.add('opacity-0');
    }
    if (statusText) statusText.textContent = "Prêt à répondre";
    if (statusDot) statusDot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400";
  }

  async sendAudioBuffer(audioBuffer) {
    if (!this.isConnected || !this.client) {
      return false;
    }

    try {
      if (audioBuffer instanceof ArrayBuffer) {
        this.client.sendAudioData(new Uint8Array(audioBuffer));
      } else if (audioBuffer instanceof Uint8Array) {
        this.client.sendAudioData(audioBuffer);
      } else {
        this.client.sendAudioData(new Uint8Array(audioBuffer.buffer || audioBuffer));
      }
      return true;
    } catch (err) {
      console.warn("⚠️ [SimliService] Erreur envoi audio Simli :", err);
      return false;
    }
  }

  close() {
    if (this.client) {
      try {
        this.client.stop();
      } catch (e) {}
      this.client = null;
      this.isConnected = false;
      this.isConnecting = false;
    }
  }
}
