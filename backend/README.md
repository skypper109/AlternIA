# Backend

Le backend expose les services nécessaires au dispositif AlternIA.

## Responsabilités possibles

- API
- authentification
- gestion des profils
- gestion des sessions
- communication avec AI Engine
- stockage des données
- statistiques
- administration
- synchronisation du dispositif

## Exemple d'API

POST /api/question

{
  "student_id": "...",
  "class": "10eme",
  "question": "..."
}

Réponse :

{
  "answer": "...",
  "subject": "mathematiques",
  "confidence": 0.94
}
