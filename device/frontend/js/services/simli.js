import { SimliClient } from 'https://esm.sh/simli-client@1.2.0-beta.0';

export class SimliService {
  constructor(videoElementId, audioElementId) {
    this.videoElement = document.getElementById(videoElementId);
    this.audioElement = document.getElementById(audioElementId);
    this.client = null;
    this.isInitialized = false;
    this.apiKey = "1e1ikibdppliekw9mt04nf";
    this.faceId = "cace3ef7-a4c4-425d-a8cf-a5358eb0c427"; // Fallback: Tina. User must replace with Prof Hamza's Face ID
  }

  async init(customFaceId = null) {
    if (this.isInitialized) return;
    if (customFaceId) {
      this.faceId = customFaceId;
    }

    this.client = new SimliClient();
    this.client.Initialize({
      apiKey: this.apiKey,
      faceID: this.faceId,
      handleSilence: true,
      videoRef: this.videoElement,
      audioRef: this.audioElement,
    });

    console.log("🚀 [SimliService] Initialisation du client WebRTC Simli...");
    
    this.client.on("connected", () => {
      console.log("✅ [SimliService] Connecté avec succès à Simli !");
      if (this.videoElement) {
        this.videoElement.classList.remove('hidden');
        const canvas = document.getElementById('modal-avatar-canvas');
        if (canvas) canvas.classList.add('hidden');
      }
    });
    
    this.client.on("disconnected", () => {
      console.log("❌ [SimliService] Déconnecté de Simli.");
    });
    
    this.client.on("failed", () => {
      console.error("❌ [SimliService] Échec de la connexion Simli.");
    });

    await this.client.start();
    this.isInitialized = true;
  }

  async sendAudioBuffer(audioBuffer) {
    if (!this.isInitialized) {
      console.warn("⚠️ [SimliService] Client non initialisé. Initialisation en cours...");
      await this.init();
    }
    
    try {
      if (audioBuffer instanceof ArrayBuffer) {
          this.client.sendAudioData(new Uint8Array(audioBuffer));
      } else {
          this.client.sendAudioData(audioBuffer);
      }
    } catch (err) {
      console.error("❌ [SimliService] Erreur lors de l'envoi de l'audio :", err);
    }
  }
  
  close() {
    if (this.client) {
      this.client.close();
      this.isInitialized = false;
    }
  }
}
