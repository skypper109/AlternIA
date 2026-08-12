# AlternIA

AlternIA est un dispositif pédagogique intelligent destiné aux élèves
du lycée au Mali.

Le dispositif embarque les programmes scolaires maliens de :

- 10ème année
- 11ème année
- 12ème année

L'élève sélectionne sa classe directement sur le dispositif.
AlternIA adapte ensuite ses réponses au programme correspondant.

## Architecture générale

Le projet est organisé autour de plusieurs composants :

- device : interface et matériel
- ai-engine : moteur d'intelligence pédagogique
- knowledge-base : programmes scolaires et contenus pédagogiques
- backend : services applicatifs
- data : données utilisées pour construire la base de connaissances
- tests : tests du système
- docs : documentation
- scripts : automatisation

## Principe pédagogique

AlternIA repose principalement sur :

1. Moteur pédagogique
2. RAG
3. Gestion du contexte
4. Profil d'apprentissage
5. LLM
6. Orchestration

## Flux général

Élève
→ Dispositif
→ Sélection de la classe
→ Question
→ Orchestrateur
→ Contexte élève
→ Moteur pédagogique
→ RAG
→ LLM
→ Validation pédagogique
→ Réponse adaptée à l'élève
