/**
 * Service de streaming d'avatar vidéo interactif photoréaliste via le SDK Simli WebRTC.
 */

export class SimliService {
  constructor(videoElementId = 'modal-avatar-video', audioElementId = 'simli-audio') {
    this.videoElementId = videoElementId;
    this.audioElementId = audioElementId;
    this.videoElement = document.getElementById(videoElementId);
    this.audioElement = document.getElementById(audioElementId);
    this.client = null;
    this.isInitialized = false;
    this.isConnecting = false;
    this.apiKey = "1e1ikibdppliekw9mt04nf";
    this.faceId = "b9e5fba3-071a-4e35-896e-211c4d6eaa7b"; // Face ID configuré par l'utilisateur
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
    if (this.isInitialized || this.isConnecting) return;
    this.isConnecting = true;

    if (customFaceId) {
      this.faceId = customFaceId;
    }

    const videoEl = this.getVideoElement();
    const audioEl = this.getAudioElement();

    try {
      console.log(`🚀 [SimliService] Initialisation du client WebRTC Simli (Face ID: ${this.faceId})...`);

      const statusText = document.getElementById('modal-status-text');
      const statusDot = document.getElementById('modal-status-dot');
      if (statusText) statusText.textContent = "Connexion à l'avatar en direct...";
      if (statusDot) statusDot.className = "w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse";

      let SimliClientModule;
      try {
        SimliClientModule = await import('https://esm.sh/simli-client@1.2.20');
      } catch (err) {
        console.warn("⚠️ [SimliService] Échec esm.sh 1.2.20, tentative unpkg...");
        SimliClientModule = await import('https://unpkg.com/simli-client@1.2.20/dist/index.js');
      }

      const SimliClient = SimliClientModule.SimliClient || SimliClientModule.default?.SimliClient || SimliClientModule.default;
      if (!SimliClient) {
        throw new Error("Classe SimliClient introuvable dans le module importé.");
      }

      this.client = new SimliClient();
      this.client.Initialize({
        apiKey: this.apiKey,
        faceID: this.faceId,
        handleSilence: true,
        videoRef: videoEl,
        audioRef: audioEl,
      });

      this.client.on("connected", () => {
        console.log("✅ [SimliService] Connecté avec succès au flux WebRTC Simli !");
        if (videoEl) {
          videoEl.classList.remove('hidden');
          videoEl.style.display = 'block';
          videoEl.play().catch(() => {});
          const canvas = document.getElementById('modal-avatar-canvas');
          if (canvas) {
            canvas.classList.add('hidden');
            canvas.style.display = 'none';
          }
        }
        if (statusText) statusText.textContent = "Avatar en direct (Simli WebRTC)";
        if (statusDot) statusDot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400";
      });

      this.client.on("disconnected", () => {
        console.log("ℹ️ [SimliService] Déconnecté de Simli.");
        this.isInitialized = false;
        this.isConnecting = false;
      });

      this.client.on("failed", (err) => {
        console.error("❌ [SimliService] Échec de la connexion Simli :", err);
        this.isInitialized = false;
        this.isConnecting = false;
        if (statusText) statusText.textContent = "Prêt à répondre";
        if (statusDot) statusDot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400";
      });

      await this.client.start();
      this.isInitialized = true;
      this.isConnecting = false;
      console.log("🌟 [SimliService] Client WebRTC Simli opérationnel !");
    } catch (err) {
      this.isConnecting = false;
      this.isInitialized = false;
      console.warn("⚠️ [SimliService] Erreur d'initialisation de SimliClient :", err);
    }
  }

  async sendAudioBuffer(audioBuffer) {
    if (!this.isInitialized && !this.isConnecting) {
      console.log("🔄 [SimliService] Client non connecté. Connexion en cours...");
      await this.init();
    }
    if (!this.client || !this.isInitialized) {
      console.warn("⚠️ [SimliService] Impossible d'envoyer l'audio : client non connecté.");
      return;
    }

    try {
      if (audioBuffer instanceof ArrayBuffer) {
        this.client.sendAudioData(new Uint8Array(audioBuffer));
      } else if (audioBuffer instanceof Uint8Array) {
        this.client.sendAudioData(audioBuffer);
      } else {
        this.client.sendAudioData(new Uint8Array(audioBuffer.buffer || audioBuffer));
      }
    } catch (err) {
      console.error("❌ [SimliService] Erreur lors de l'envoi de l'audio à Simli :", err);
    }
  }

  close() {
    if (this.client) {
      try {
        this.client.close();
      } catch (e) {}
      this.client = null;
      this.isInitialized = false;
      this.isConnecting = false;
    }
  }
}
