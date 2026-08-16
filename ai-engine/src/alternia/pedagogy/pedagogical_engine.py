"""
Compatibilité historique pour PedagogicalEngine.

Le moteur pédagogique officiel se trouve désormais dans :

    alternia.pedagogical.engine

Ce module conserve l'ancien chemin d'import afin d'éviter
de casser les anciens composants et tests pendant la migration.
"""

from alternia.pedagogical.engine import PedagogicalEngine

__all__ = [
    "PedagogicalEngine",
]