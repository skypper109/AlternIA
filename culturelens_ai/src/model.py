"""Architecture du modèle d'extraction de caractéristiques visuelles CultureLens."""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from torchvision.models import MobileNet_V3_Small_Weights

from .config import EMBEDDING_DIM


class CultureLensVisionBackbone(nn.Module):
    """Backbone de vision profonde pré-entraîné avec projection d'embeddings L2."""

    def __init__(self, pretrained: bool = True):
        super().__init__()
        weights = MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
        base = models.mobilenet_v3_small(weights=weights)

        # On conserve les couches convolutives d'extraction de features
        self.features = base.features
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))

        # Couche de projection linéaire pour les embeddings
        # mobilenet_v3_small sort 576 canaux
        self.projection = nn.Sequential(
            nn.Linear(576, EMBEDDING_DIM),
            nn.BatchNorm1d(EMBEDDING_DIM),
            nn.SiLU(),
            nn.Linear(EMBEDDING_DIM, EMBEDDING_DIM),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Extrait les embeddings et les normalise sur la sphère unité (L2)."""
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.projection(x)
        # Normalisation L2 unitaire pour similarité cosinus directe
        embeddings = F.normalize(x, p=2, dim=1)
        return embeddings


def build_feature_extractor(device: str = "cpu") -> CultureLensVisionBackbone:
    """Instancie et initialise le modèle sur le device cible (CPU ou MPS/CUDA)."""
    model = CultureLensVisionBackbone(pretrained=True)
    model.eval()
    model.to(device)
    return model
