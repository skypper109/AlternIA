/**
 * Service de streaming d'avatar vidéo interactif photoréaliste via l'API WebRTC de D-ID.
 */

export class DidService {
    constructor(videoElementId = 'modal-avatar-video', onConnectedCallback = null) {
        this.videoElementId = videoElementId;
        this.videoElement = document.getElementById(videoElementId);
        this.onConnectedCallback = onConnectedCallback;
        this.peerConnection = null;
        this.streamId = null;
        this.sessionId = null;
        this.isInitialized = false;
        this.isConnecting = false;
        
        // Clé API D-ID (Peut être injectée par l'environnement ou les headers)
        this.apiKey = "Z29vZ2xlLW9hdXRoMnwxMTQyMTA0MDM5NTY3ODQzNzUzMDFAYWtfMmVUSmYzdGhkRDUyTkQ4TkppYVp6:Ydp-hWUy2wQ_rRxQ6Usrc";
        
        // Image par défaut si l'avatar n'a pas de photo distante disponible
        this.defaultSourceUrl = "https://create-images-results.d-id.com/DefaultPresenters/Noam_m/image.jpeg";

        // Mapping des voix locales AlternIA vers les voix neurales haute fidélité Microsoft D-ID
        this.voiceMapping = {
            'vivienne': 'fr-FR-DeniseNeural',
            'henri': 'fr-FR-HenriNeural',
            'alain': 'fr-FR-HenriNeural',
            'default': 'fr-FR-DeniseNeural'
        };
    }

    getVideoElement() {
        if (!this.videoElement) {
            this.videoElement = document.getElementById(this.videoElementId);
        }
        return this.videoElement;
    }

    async initFromAvatar(avatar) {
        if (this.isInitialized || this.isConnecting) return;
        
        let sourceUrl = this.defaultSourceUrl;

        if (avatar) {
            if (avatar.photoUrl && avatar.photoUrl.startsWith('https://')) {
                sourceUrl = avatar.photoUrl;
            } else if (avatar.id) {
                try {
                    const resp = await fetch(`/api/avatars/${avatar.id}/did-image`, { method: 'POST' });
                    if (resp.ok) {
                        const data = await resp.json();
                        if (data.source_url) {
                            sourceUrl = data.source_url;
                        }
                    }
                } catch (e) {
                    console.warn("⚠️ [DidService] Note upload image locale vers D-ID, utilisation du fallback :", e);
                }
            }
        }

        await this.init(sourceUrl);
    }

    async init(sourceUrl = this.defaultSourceUrl) {
        if (this.isInitialized || this.isConnecting) return;
        this.isConnecting = true;
        console.log("🚀 [DidService] Initialisation du client WebRTC D-ID avec l'image :", sourceUrl);
        
        try {
            // 1. Créer la session de streaming WebRTC sur l'API D-ID
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

            if (!sessionResponse.ok) {
                const errText = await sessionResponse.text();
                throw new Error(`D-ID stream creation failed: ${sessionResponse.status} ${errText}`);
            }

            const sessionData = await sessionResponse.json();
            this.streamId = sessionData.id;
            this.sessionId = sessionData.session_id;

            // 2. Créer l'objet RTCPeerConnection avec les serveurs STUN/TURN fournis par D-ID
            this.peerConnection = new RTCPeerConnection({ iceServers: sessionData.ice_servers });

            this.peerConnection.addEventListener('icecandidate', async (event) => {
                if (event.candidate && this.streamId) {
                    try {
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
                    } catch (e) {
                        console.warn("⚠️ [DidService] ICE candidate error:", e);
                    }
                }
            });

            this.peerConnection.addEventListener('track', (event) => {
                console.log("🎬 [DidService] Flux vidéo WebRTC en direct reçu de D-ID !");
                const videoEl = this.getVideoElement();
                if (videoEl) {
                    videoEl.srcObject = event.streams[0];
                    videoEl.classList.remove('hidden');
                    videoEl.play().catch(console.warn);
                }
                if (this.onConnectedCallback) {
                    this.onConnectedCallback();
                }
            });

            // 3. Négociation SDP WebRTC
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
            this.isConnecting = false;
            console.log("✅ [DidService] Connexion WebRTC D-ID établie avec succès.");
        } catch (error) {
            this.isConnecting = false;
            console.error("❌ [DidService] Erreur lors de l'initialisation D-ID :", error);
        }
    }

    async speak(text, localVoiceName = 'vivienne') {
        if (!text || !text.trim()) return;
        
        if (!this.isInitialized) {
            console.log("⏳ [DidService] Initialisation en tâche de fond avant envoi du texte...");
            await this.init();
        }

        if (!this.isInitialized || !this.streamId) {
            console.warn("⚠️ [DidService] Impossible d'envoyer le script : flux D-ID non prêt.");
            return false;
        }
        
        const mappedVoice = this.voiceMapping[localVoiceName] || this.voiceMapping['default'];
        
        try {
            const resp = await fetch(`https://api.d-id.com/talks/streams/${this.streamId}`, {
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

            if (resp.ok) {
                console.log(`🔊 [DidService] Phrase envoyée à D-ID : "${text}" (Voix: ${mappedVoice})`);
                return true;
            } else {
                const errText = await resp.text();
                console.warn(`⚠️ [DidService] Échec envoi script D-ID (${resp.status}):`, errText);
                return false;
            }
        } catch (error) {
            console.error("❌ [DidService] Erreur réseau d'envoi du script D-ID :", error);
            return false;
        }
    }

    close() {
        if (this.peerConnection) {
            try { this.peerConnection.close(); } catch (e) {}
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
        this.isConnecting = false;
        const videoEl = this.getVideoElement();
        if (videoEl) {
            videoEl.srcObject = null;
        }
    }
}
