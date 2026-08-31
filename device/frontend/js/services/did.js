export class DidService {
    constructor(videoElementId) {
        this.videoElement = document.getElementById(videoElementId);
        this.peerConnection = null;
        this.streamId = null;
        this.sessionId = null;
        this.isInitialized = false;
        // La clé doit en théorie être stockée de façon sécurisée via le backend
        // Pour les tests en local et selon la clé fournie :
        this.apiKey = "Z29vZ2xlLW9hdXRoMnwxMTQyMTA0MDM5NTY3ODQzNzUzMDFAYWtfMmVUSmYzdGhkRDUyTkQ4TkppYVp6:Ydp-hWUy2wQ_rRxQ6Usrc";
        
        // Mapping de la voix locale vers une voix Microsoft équivalente
        this.voiceMapping = {
            'vivienne': 'fr-FR-DeniseNeural',
            'henri': 'fr-FR-HenriNeural',
            'default': 'fr-FR-DeniseNeural'
        };
    }

    async init(sourceUrl) {
        if (this.isInitialized) return;
        console.log("🚀 [DidService] Initialisation du client WebRTC D-ID...");
        
        try {
            // 1. Créer le stream WebRTC côté serveur D-ID
            const sessionResponse = await fetch("https://api.d-id.com/talks/streams", {
                method: "POST",
                headers: {
                    Authorization: `Basic ${this.apiKey}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    source_url: sourceUrl
                })
            });

            const sessionData = await sessionResponse.json();
            this.streamId = sessionData.id;
            this.sessionId = sessionData.session_id;

            // 2. Initialiser la connexion locale avec les serveurs ICE fournis
            this.peerConnection = new RTCPeerConnection({ iceServers: sessionData.ice_servers });

            this.peerConnection.addEventListener('icecandidate', async (event) => {
                if (event.candidate) {
                    await fetch(`https://api.d-id.com/talks/streams/${this.streamId}/ice`, {
                        method: "POST",
                        headers: {
                            Authorization: `Basic ${this.apiKey}`,
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            candidate: event.candidate.candidate,
                            sdpMid: event.candidate.sdpMid,
                            sdpMLineIndex: event.candidate.sdpMLineIndex,
                            session_id: this.sessionId
                        })
                    });
                }
            });

            this.peerConnection.addEventListener('track', (event) => {
                console.log("✅ [DidService] Flux vidéo WebRTC reçu !");
                if (!this.videoElement.srcObject) {
                    this.videoElement.srcObject = event.streams[0];
                    this.videoElement.play().catch(console.warn);
                }
            });

            // 3. Définir l'offre SDP distante et envoyer la réponse locale
            await this.peerConnection.setRemoteDescription(
                new RTCSessionDescription(sessionData.offer)
            );
            
            const localDescription = await this.peerConnection.createAnswer();
            await this.peerConnection.setLocalDescription(localDescription);

            await fetch(`https://api.d-id.com/talks/streams/${this.streamId}/sdp`, {
                method: "POST",
                headers: {
                    Authorization: `Basic ${this.apiKey}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    answer: localDescription,
                    session_id: this.sessionId
                })
            });

            this.isInitialized = true;
            console.log("✅ [DidService] WebRTC établi avec succès.");
        } catch (error) {
            console.error("❌ [DidService] Erreur lors de l'initialisation :", error);
        }
    }

    async speak(text, localVoiceName) {
        if (!this.isInitialized || !text) return;
        
        const mappedVoice = this.voiceMapping[localVoiceName] || this.voiceMapping['default'];
        
        try {
            await fetch(`https://api.d-id.com/talks/streams/${this.streamId}`, {
                method: "POST",
                headers: {
                    Authorization: `Basic ${this.apiKey}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    script: {
                        type: 'text',
                        subtitles: false,
                        provider: {
                            type: 'microsoft',
                            voice_id: mappedVoice
                        },
                        input: text
                    },
                    config: {
                        fluent: true,
                        pad_audio: 0.0,
                        stitch: true
                    },
                    session_id: this.sessionId
                })
            });
            console.log(`🔊 [DidService] Phrase envoyée à D-ID : "${text}" avec la voix ${mappedVoice}`);
        } catch (error) {
            console.error("❌ [DidService] Erreur d'envoi du script :", error);
        }
    }

    close() {
        if (this.peerConnection) {
            this.peerConnection.close();
        }
        if (this.streamId && this.sessionId) {
            fetch(`https://api.d-id.com/talks/streams/${this.streamId}`, {
                method: "DELETE",
                headers: {
                    Authorization: `Basic ${this.apiKey}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ session_id: this.sessionId })
            }).catch(console.warn);
        }
        this.peerConnection = null;
        this.streamId = null;
        this.sessionId = null;
        this.isInitialized = false;
        if (this.videoElement) {
            this.videoElement.srcObject = null;
        }
    }
}
