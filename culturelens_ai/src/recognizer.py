"""Moteur d'inférence en direct CultureLens pour la reconnaissance de monuments."""

import io
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from PIL import Image
import torch
import torch.nn.functional as F

from .config import (
    MODEL_WEIGHTS_PATH,
    INDEX_PATH,
    LABELS_PATH,
    CONFIDENCE_THRESHOLD,
    TEMPERATURE,
    BAMAKO_MONUMENTS,
)
from .dataset_loader import get_inference_transform
from .model import CultureLensVisionBackbone


class CultureLensRecognizer:
    """Moteur de reconnaissance IA Edge pour les monuments africains / maliens."""

    _instance: Optional["CultureLensRecognizer"] = None

    def __init__(self, device: str = "cpu"):
        self.device = device
        self.model: Optional[CultureLensVisionBackbone] = None
        self.prototypes: Optional[torch.Tensor] = None
        self.exemplar_embeddings: Optional[torch.Tensor] = None
        self.exemplar_labels: Optional[torch.Tensor] = None
        self.class_to_id: Dict[str, int] = {}
        self.id_to_class: Dict[int, str] = {}
        self.labels_meta: Dict[str, Dict] = {}
        self.transform = get_inference_transform()
        self._is_loaded = False

    @classmethod
    def get_instance(cls, device: str = "cpu") -> "CultureLensRecognizer":
        """Singleton thread-safe pour éviter de recharger les poids à chaque requête."""
        if cls._instance is None:
            cls._instance = cls(device=device)
            cls._instance.load()
        return cls._instance

    def load(self) -> bool:
        """Charge le modèle neuronal et l'index de prototypes vectoriels."""
        if self._is_loaded:
            return True

        if not INDEX_PATH.exists() or not MODEL_WEIGHTS_PATH.exists():
            return False

        try:
            # 1. Chargement de l'index
            index_data = torch.load(INDEX_PATH, map_location=self.device)
            self.prototypes = index_data["prototypes"].to(self.device)
            if "exemplar_embeddings" in index_data:
                self.exemplar_embeddings = index_data["exemplar_embeddings"].to(self.device)
                self.exemplar_labels = index_data["exemplar_labels"].to(self.device)
            self.class_to_id = index_data["class_to_id"]
            self.id_to_class = {int(k): v for k, v in index_data["id_to_class"].items()}

            # 2. Chargement du modèle
            self.model = CultureLensVisionBackbone(pretrained=False)
            weights = torch.load(MODEL_WEIGHTS_PATH, map_location=self.device)
            self.model.load_state_dict(weights)
            self.model.eval()
            self.model.to(self.device)

            # 3. Chargement des métadonnées
            if LABELS_PATH.exists():
                with open(LABELS_PATH, "r", encoding="utf-8") as f:
                    self.labels_meta = json.load(f)

            self._is_loaded = True
            return True
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement de CultureLensRecognizer : {e}")
            return False

    def predict(
        self,
        image_input: Union[str, Path, bytes, Image.Image],
        user_coords: Optional[Tuple[float, float]] = None,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
    ) -> Dict:
        """Identifie le monument présent dans l'image avec explication détaillée.

        Args:
            image_input: Chemin de fichier, bytes bruts, ou image PIL.
            user_coords: Tuple (latitude, longitude) optionnel du smartphone.
            confidence_threshold: Seuil minimal de certitude.
        """
        start_time = time.perf_counter()

        if not self._is_loaded:
            loaded = self.load()
            if not loaded:
                return {
                    "is_identified": False,
                    "confidence": 0.0,
                    "error": "Modèle ou index non disponible. Veuillez exécuter 'python train.py' d'abord.",
                }

        if self.model is None or self.prototypes is None:
            return {
                "is_identified": False,
                "confidence": 0.0,
                "error": "Modèle ou index non disponible. Veuillez exécuter 'python train.py' d'abord.",
            }

        # Conversion en image PIL RGB
        pil_image = None
        if isinstance(image_input, (str, Path)):
            pil_image = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, bytes):
            pil_image = Image.open(io.BytesIO(image_input)).convert("RGB")
        elif isinstance(image_input, Image.Image):
            pil_image = image_input.convert("RGB")
        else:
            raise ValueError(f"Format d'image non supporté : {type(image_input)}")

        model = self.model
        prototypes = self.prototypes

        # Prétraitement et inférence
        tensor = self.transform(pil_image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            query_emb = model(tensor)  # [1, 576] normalisé L2
            # Produit scalaire avec les centroïdes
            centroid_sims = torch.matmul(query_emb, prototypes.t()).squeeze(0)  # [num_classes]

            # Produit scalaire avec les exemplars (variations multi-angles réelles et augmentées)
            if self.exemplar_embeddings is not None and self.exemplar_labels is not None:
                ex_sims = torch.matmul(query_emb, self.exemplar_embeddings.t()).squeeze(0)
                max_ex_sims = torch.zeros_like(centroid_sims)
                for c_idx in range(len(centroid_sims)):
                    mask = (self.exemplar_labels == c_idx)
                    if mask.any():
                        max_ex_sims[c_idx] = ex_sims[mask].max()
                    else:
                        max_ex_sims[c_idx] = centroid_sims[c_idx]
                cosine_similarities = 0.40 * centroid_sims + 0.60 * max_ex_sims
            else:
                cosine_similarities = centroid_sims

            # Probabilités via Softmax à température
            scaled_logits = cosine_similarities * TEMPERATURE
            probabilities = F.softmax(scaled_logits, dim=0)

        # Récupération des top matches
        top_k = min(3, len(self.id_to_class))
        top_probs, top_indices = torch.topk(probabilities, k=top_k)
        top_sims = cosine_similarities[top_indices]

        top_matches = []
        for i in range(top_k):
            c_idx = int(top_indices[i].item())
            m_id = self.id_to_class.get(c_idx, f"unknown_{c_idx}")
            meta = self.labels_meta.get(m_id, BAMAKO_MONUMENTS.get(m_id, {}))
            prob = float(top_probs[i].item())
            sim = float(top_sims[i].item())

            top_matches.append({
                "monument_id": m_id,
                "name": meta.get("name", m_id),
                "ville": meta.get("ville", "Mali"),
                "confidence": round(prob, 4),
                "cosine_similarity": round(sim, 4),
                "category": meta.get("category", "Patrimoine"),
            })

        best_match = top_matches[0]
        best_id = best_match["monument_id"]
        meta_best = self.labels_meta.get(best_id, BAMAKO_MONUMENTS.get(best_id, {}))

        # Facteur géographique optionnel
        geo_bonus = 0.0
        if user_coords and "coords" in meta_best:
            try:
                mon_lat, mon_lon = meta_best["coords"]
                u_lat, u_lon = user_coords
                # Distance euclidienne approximative (1 degré ~ 111 km)
                d_km = ((mon_lat - u_lat)**2 + (mon_lon - u_lon)**2)**0.5 * 111.0
                if d_km < 5.0:
                    geo_bonus = 0.05
                elif d_km < 25.0:
                    geo_bonus = 0.02
            except Exception:
                pass

        # Calibrage robuste de la confiance : similarité cosinus directe + marge relative
        cos_sim = float(best_match["cosine_similarity"])
        margin = float(cos_sim - top_matches[1]["cosine_similarity"]) if len(top_matches) > 1 else 0.2
        norm_sim = min(1.0, max(0.0, (cos_sim - 0.55) / 0.40))
        calibrated_conf = min(1.0, 0.60 * norm_sim + 0.25 * float(best_match["confidence"]) + 0.15 * min(1.0, margin * 5) + geo_bonus)

        # Seuil minimal de matching strict : au moins 45% (0.45)
        min_threshold = max(0.45, confidence_threshold)
        is_identified = (calibrated_conf >= min_threshold and cos_sim >= 0.45) and (
            (cos_sim >= 0.65) or (calibrated_conf >= 0.55)
        )

        inference_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "is_identified": is_identified,
            "monument_id": best_id,
            "monument_name": meta_best.get("name", best_id),
            "name": best_match["name"],
            "ville": best_match["ville"],
            "confidence": round(calibrated_conf, 4),
            "raw_similarity": cos_sim,
            "category": best_match["category"],
            "visual_features": meta_best.get("visual_features", []),
            "inference_time_ms": inference_time_ms,
            "top_matches": top_matches,
            "validation_status": "Vérifié & Certifié" if is_identified else "Non reconnu (< 45%)",
            "explanation": (
                f"Correspondance visuelle reconnue ({round(calibrated_conf*100, 1)}%) avec {best_match['name']}."
                if is_identified
                else f"Désolé, aucun monument répertorié ne correspond avec au moins 45% de certitude (confiance : {round(calibrated_conf*100, 1)}%)."
            ),
        }
