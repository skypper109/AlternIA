/**
 * Service de communication avec l'API Backend Alternia (FastAPI & RAG Local).
 */

import { API_BASE_URL } from '../config/curriculum.js';

export class ApiService {
  /**
   * Vérifie la santé du backend et le nombre d'extraits RAG disponibles.
   */
  static async checkHealth() {
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.warn("Backend FastAPI non joignable :", e);
    }
    return null;
  }

  /**
   * Réinitialise la session de conversation.
   */
  static async resetSession(sessionId) {
    try {
      await fetch(`${API_BASE_URL}/api/session/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
    } catch (e) {
      console.warn("Erreur réinitialisation session :", e);
    }
  }

  /**
   * Télécharge un blob audio généré par le moteur TTS local.
   */
  static async fetchTTSBlob(text, voice = 'vivienne') {
    try {
      const res = await fetch(`${API_BASE_URL}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice })
      });
      if (res.ok) {
        return await res.blob();
      }
    } catch (e) {
      console.warn("TTS Backend indisponible, bascule fallback local :", e);
    }
    return null;
  }

  /**
   * Envoie un enregistrement audio au backend pour transcription via Faster-Whisper local.
   */
  static async transcribeAudioBlob(audioBlob) {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.wav');
      formData.append('language', 'fr');
      const res = await fetch(`${API_BASE_URL}/api/stt`, {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        return (data.text || '').trim();
      }
    } catch (e) {
      console.warn("Erreur transcription STT backend :", e);
    }
    return '';
  }

  /**
   * Écoute en streaming SSE la réponse pédagogique générée par ALTA.
   */
  static async streamChat({
    question,
    studentClass,
    subject,
    sessionId,
    onChunk,
    onDone,
    onError
  }) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          student_class: studentClass,
          subject,
          session_id: sessionId,
          enable_rag: true
        })
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data:')) continue;
          const dataStr = trimmed.replace(/^data:\s*/, '');
          if (!dataStr) continue;

          try {
            const parsed = JSON.parse(dataStr);
            if (parsed.chunk && onChunk) {
              onChunk(parsed.chunk);
            }
            if (parsed.done && onDone) {
              onDone(parsed);
            }
          } catch (jsonErr) {
            console.warn("Erreur parsing SSE chunk :", jsonErr);
          }
        }
      }
      return true;
    } catch (err) {
      if (onError) onError(err);
      return false;
    }
  }
}
