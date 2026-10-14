#!/bin/bash
# ==============================================================================
# Script de Diagnostic et d'Auto-Guérison (Self-Healing) pour AlternIA
# Exécuté périodiquement par alternia-watchdog.timer
# ==============================================================================

BACKEND_URL="http://127.0.0.1:8000/docs"
QDRANT_URL="http://127.0.0.1:6333/healthz"
MAX_TIMEOUT=5

# 1. Vérification de Qdrant
if ! curl -sf --max-time $MAX_TIMEOUT "$QDRANT_URL" > /dev/null 2>&1; then
    echo "[$(date)] ⚠️ Qdrant ne répond pas. Redémarrage de qdrant.service..."
    systemctl restart qdrant.service
fi

# 2. Vérification du Backend FastAPI
if ! curl -sf --max-time $MAX_TIMEOUT "$BACKEND_URL" > /dev/null 2>&1; then
    echo "[$(date)] ⚠️ Backend FastAPI ne répond pas. Redémarrage de alternia-backend.service..."
    systemctl restart alternia-backend.service
fi

# 3. Vérification de Cloudflare Tunnel
if ! systemctl is-active --quiet alternia-tunnel.service; then
    echo "[$(date)] ⚠️ Cloudflare Tunnel inactif. Relance de alternia-tunnel.service..."
    systemctl start alternia-tunnel.service
fi
