# RAG

RAG signifie Retrieval-Augmented Generation.

Ce module permet à AlternIA de rechercher les informations pertinentes
dans les programmes scolaires maliens avant de générer une réponse.

## Pipeline

Question
→ recherche sémantique
→ récupération des documents
→ filtrage par classe
→ filtrage par matière
→ contexte documentaire
→ LLM

## Exemple

Classe : 10ème

Question :

"Qu'est-ce qu'une équation du premier degré ?"

Le RAG doit rechercher en priorité les documents de la 10ème
correspondant aux mathématiques.

## Sources

Les sources principales se trouvent dans :

knowledge-base/
