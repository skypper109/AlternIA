# Context Manager

Ce module gère le contexte conversationnel de l'élève.

## Il conserve notamment

- classe sélectionnée
- matière
- question précédente
- réponse précédente
- conversation actuelle
- sujet étudié
- niveau de difficulté

## Exemple

Élève :

"Explique la photosynthèse."

AlternIA répond.

Élève :

"Et pourquoi elle est importante ?"

Le Context Manager comprend que "elle" fait référence à la photosynthèse.

## Objectif

Éviter qu'AlternIA traite chaque question comme une nouvelle conversation.
