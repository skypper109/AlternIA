# Orchestration

L'orchestrateur coordonne tous les modules du moteur IA.

## Flux

1. réception de la question
2. récupération de la classe
3. récupération du profil
4. récupération du contexte
5. identification de la matière
6. recherche RAG
7. stratégie pédagogique
8. génération LLM
9. validation
10. réponse

## Exemple

Question :

"Pourquoi le ciel est bleu ?"

L'orchestrateur doit déterminer :

Classe → 10ème
Matière → Sciences
RAG → contenu scientifique adapté
Profil → niveau de l'élève
Pedagogy → explication adaptée
LLM → génération
