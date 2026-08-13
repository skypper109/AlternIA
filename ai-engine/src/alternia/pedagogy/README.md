# Pedagogy

Ce dossier contient le moteur pédagogique d'AlternIA.

## Responsabilités

Le moteur pédagogique transforme le contexte RAG et le profil de l'élève
en stratégie pédagogique adaptée.

Il doit notamment prendre en compte :

- la classe de l'élève ;
- la matière ;
- le niveau de difficulté ;
- le type de question ;
- le contexte récupéré par le RAG ;
- le profil d'apprentissage ;
- l'historique pédagogique disponible ;
- le type d'explication à utiliser.

## Fichiers

### pedagogical_engine.py

Point d'entrée principal du moteur pédagogique.

Il orchestre la sélection de la stratégie pédagogique.

### response_strategy.py

Définit les stratégies d'explication :

- explication directe ;
- explication progressive ;
- exemple guidé ;
- exercice ;
- correction ;
- révision.

### difficulty.py

Gestion du niveau de difficulté pédagogique.

## Important

Ce module ne doit pas effectuer directement la recherche vectorielle.

Le RAG fournit le contexte.

Le moteur pédagogique décide ensuite COMMENT utiliser ce contexte
pour enseigner à l'élève.
