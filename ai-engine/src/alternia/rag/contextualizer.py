import re
import time
from typing import Any
from alternia.pedagogical.curriculum_keywords import detect_malian_curriculum_subject


class QueryContextualizer:
    """
    Contextualise intelligemment les requêtes de suivi pour la recherche sémantique RAG.
    
    Prend en compte toutes les tournures de questions d'élèves curieux :
    - Demandes de réexplication, simplification et vulgarisation ("explique simplement", "j'ai rien compris")
    - Demandes d'exemples concrets et vie réelle ("dans la vraie vie", "donne une analogie")
    - Demandes de formules, unités et calculs ("quelle est la formule", "comment on calcule")
    - Demandes de rôle, importance et utilité ("à quoi ça sert", "quel est le but")
    - Demandes d'étapes, processus et mécanismes ("comment ça marche", "étape par étape")
    - Demandes de causes, conséquences et conditions ("pourquoi ça", "dans quel cas")
    - Demandes de concision ("soit bref", "résume en une phrase")
    - Résolution des anaphores ("son rôle", "sa formule", "ses limites").
    
    Ne pollue JAMAIS les nouvelles questions indépendantes.
    """

    STOP_PHRASES = [
        # Formules interrogatives
        r"^(c'est quoi exactement|c'est quoi au juste|c'est quoi la notion de|c'est quoi le concept de|c'est quoi la définition de|c'est quoi la definition de|c'est quoi le principe de|c'est quoi l'idée de|c'est quoi l'idee de)",
        r"^(c'est quoi|qu'est-ce que|qu'est ce que|qu'est-ce qu'|qu'est ce qu'|qu'est ce que c'est que|qu'est-ce que c'est|que désigne|que designe|que veut dire|que signifie|qu'entend-on par|qu'entend on par)",
        # Demandes d'explication
        r"^(peux-tu m'expliquer|peux tu m'expliquer|pourrais-tu m'expliquer|pourrais tu m'expliquer|explique-moi|explique moi|peux-tu m'en dire plus sur|peux tu m'en dire plus sur|parle-moi de|parle moi de|dis-moi c'est quoi|dis moi c'est quoi|dis-moi tout sur|dis moi tout sur|fais-moi un cours sur|fais moi un cours sur|apprends-moi|apprends moi)",
        # Demandes de don / citation / énoncé
        r"^(donne-moi la liste de|donne la liste de|donne-moi|donne moi|peux-tu me donner|peux tu me donner|peux-tu me citer|cite-moi|cite moi|énonce-moi|énonce moi|enonce-moi|enonce moi)",
        # Questions de calcul / méthode
        r"^(comment résoudre|comment resoudre|comment calculer|comment trouver|comment déterminer|comment determiner|comment faire pour|comment fonctionne|comment marche|comment s'applique|comment démontrer|comment demontrer)",
        # Articles interrogatifs
        r"^(quelles sont les|quels sont les|quelle est la|quel est le|quelles sont ses|quels sont ses|quelle est sa|quel est son|donne-moi les|donne les|montre-moi les|montre les)",
        # Questions fermées
        r"^(est-ce que|est ce que|est-il|est il|est-elle|est elle|sont-ils|sont ils|sont-elles|sont elles|peut-on|peut on|faut-il|faut il|doit-on|doit on|y a-t-il|y a t il|existe-t-il|existe t il)",
        # Accroches orales / interjections / politesse
        r"^(dis ALTA|salut alta|bonjour alta|coucou alta|wesh alta|yo alta|en fait|au fait|dis|dis-moi|dis moi)",
        r"^(s'il te plaît|s'il te plait|stp|s'il vous plaît|s'il vous plait|svp|merci de m'expliquer|merci de me dire)",
    ]

    FOLLOW_UP_ONLY_PATTERNS = [
        # Réexplication & Vulgarisation
        r"^(reexplique|réexplique|explique encore|explique davantage|explique mieux|développe|developpe|approfondis|approfondir)",
        r"^(je n'ai pas compris|j'ai pas compris|je ne comprends? pas|j'ai rien compris|j'ai rien capté|je comprends? toujours pas|c'est pas clair|c'est trop compliqué|c'est difficile)",
        r"^(simplifie|vulgarise|explique simplement|plus simplement|en des termes simples|comme si j'avais 10 ans|avec des mots simples)",
        # Concision & Synthèse
        r"(soit|sois|rendre|fais|en)\s+(très\s+|tres\s+|plus\s+)?(bref|court|simple|résumé|resume|synthétique|synthetique|concis)",
        r"^(en une phrase|en 2 mots|en deux mots|en quelques mots|l'essentiel seulement|va droit au but|sans trop de blabla|résume-moi ça|resume moi ca)",
        # Exemples & Vie réelle
        r"^(donne(-moi)? un exemple|un exemple|des exemples|illustre|donne une illustration|donne une analogie)",
        r"^(dans la vraie vie|dans la réalité|dans la realite|dans la vie courante|dans la vie de tous les jours|à quoi ça sert dans la vie|un cas pratique|une application concrète|une application concrete)",
        # Mécanismes & Processus
        r"^(comment ça marche|comment ca marche|comment ça fonctionne|comment ca fonctionne|comment ça se passe|comment ca se passe)",
        r"^(quelles sont les étapes|quelles sont les etapes|quelles sont les phases|étape par étape|etape par etape|décompose le mécanisme|developpe le processus)",
        # Causes & Conséquences
        r"^(pourquoi\s*\??$|pourquoi ça\s*\??$|pourquoi c'est comme ça\s*\??$|à cause de quoi\s*\??$)",
        r"^(quelles sont les causes|quelles sont les conséquences|quelles sont les consequences|qu'est-ce que ça provoque|qu'est ce que ca provoque|quel est l'impact|quel est l'effet)",
        r"^(dans quelles conditions|dans quel cas|sous quelle condition|quand est-ce que ça arrive|quand est ce que ca arrive)",
        # Rôle & Utilité
        r"^(à quoi ça sert\s*\??$|a quoi ca sert\s*\??$|quel est son rôle\s*\??$|quel est son role\s*\??$|quelle est sa fonction\s*\??$)",
        r"^(quelle est son importance\s*\??$|pourquoi c'est important\s*\??$|quel est le but\s*\??$|quelle est son utilité\s*\??$)",
        # Formules & Unités
        r"^(quelle est sa formule|donne sa formule|quelles sont ses unités|quelles sont ses unites|comment on le calcule|comment la calculer|comment le calculer)",
        r"^(quelle est son unité|quelle est l'unité si|donne l'équation|donne l'equation|quelle est son expression|donne son expression)",
        # Propriétés & Types
        r"^(quelles sont ses propriétés|quelles sont ses proprietes|quelles sont ses caractéristiques|quelles sont ses caracteristiques)",
        r"^(quels sont ses types|combien il y en a|quelles sont ses différentes formes|cite ses différentes formes|quelles sont ses limites)",
        # Comparaisons relatives
        r"^(et par rapport à|et si on compare|quelle est la différence|quelle est la difference|contrairement à quoi)",
        # Enchaînements & Conditions
        r"^(et ensuite\s*\??$|et après\s*\??$|et apres\s*\??$|qu'est-ce qui se passe après\s*\??$|et si la température|et si la pression|et dans le cas contraire)",
        # Anaphores universelles (ex: "quel est son but", "quelle est son équation bilan", "sa formule", "ses limites")
        r"^(et\s+)?(quel(le)?s?\s+(est|sont)\s+)?(son|sa|ses|leur|leurs|ce|cette|cet|ces)\s+[a-zàâéèêëîïôùûç\s-]{1,35}\??$",
    ]

    @classmethod
    def clean_core_terms(cls, text: str) -> str:
        """Extrait les termes substantiels d'une question en retirant les formules introductives."""
        cleaned = text.strip()
        for pat in cls.STOP_PHRASES:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"[?!.,;:«»\"']", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @classmethod
    def is_follow_up(cls, question: str) -> bool:
        """
        Détermine si la question est une relance dépendante du contexte précédent.
        Une question définissant un nouveau sujet ('c'est quoi X') n'est PAS un follow-up.
        """
        q = question.strip().lower()

        # 1. Relances évidentes de reformulation / précision / curiosité sans nouveau concept
        for pat in cls.FOLLOW_UP_ONLY_PATTERNS:
            if re.search(pat, q):
                return True

        # 2. Anaphores et pronoms possessifs/démonstratifs (ex: "son importance", "sa formule", "ses propriétés", "ce principe")
        if re.search(r"\b(son|sa|ses|leur|leurs|cet|cette|ces)\s+[a-zàâéèêëîïôùûç]", q):
            return True

        # 3. Marqueurs explicites de continuité (alors, donc, du coup, et ensuite)
        if re.search(r"\b(alors|donc|du coup|dans ce cas|par conséquent|et ensuite|et après|et apres)\b", q):
            return True

        # 4. Précisions elliptiques courtes (ex: "en biologie", "en physique", "dans la nature", "pour les plantes")
        if re.search(r"^(en|dans|pour|chez|sur)\s+[a-zàâéèêëîïôùûç\s-]{2,25}\??$", q):
            return True

        # 5. Si la question contient une interrogation de nouveau sujet SANS anaphore ni marqueur
        if re.search(r"^(c'est quoi|qu'est-ce que|qu'est ce que|définis|définition de)\s+", q):
            return False

        # Si un concept spécifique du programme est explicitement mentionné, nouvelle question indépendante
        if detect_malian_curriculum_subject(question) is not None:
            return False

        # 6. Mots ultra-courts de relance
        if q in {"encore", "plus", "pourquoi ?", "comment ?", "aide-moi", "je ne comprends pas", "je ne comprend pas", "je comprends pas", "et alors ?"}:
            return True

        return False

    @classmethod
    def contextualize(
        cls,
        current_question: str,
        past_student_messages: list[str] | None = None,
        current_topic: str | None = None,
    ) -> str:
        """
        Génère une requête RAG enrichie et adaptée à l'intention spécifique de l'élève curieux.
        """
        t0 = time.perf_counter()
        if not past_student_messages and not current_topic:
            return current_question.strip()

        if not cls.is_follow_up(current_question):
            return current_question.strip()

        # Récupération du sujet précédent valide
        prev_topic = ""
        if current_topic:
            prev_topic = current_topic.strip()
        elif past_student_messages:
            for past_msg in reversed(past_student_messages):
                if cls.is_follow_up(past_msg):
                    continue
                extracted = cls.clean_core_terms(past_msg)
                if len(extracted.split()) >= 1 and extracted.lower() not in {"quit", "aide", "/aide", "/classe", "merci", "salut", "bonjour"}:
                    prev_topic = extracted
                    break

        if not prev_topic:
            return current_question.strip()

        q_lower = current_question.strip().lower()

        # 1. Formule, calcul, équation, unité
        if re.search(r"\b(formule|calcul|calculer|calcule|equation|équation|unités?|unites?|système international|unite(s)?\s+si|unité(s)?\s+si)\b", q_lower):
            enriched = f"{prev_topic} formule calcul unité expression cours"
        # 2. Étapes, mécanisme, fonctionnement, processus
        elif re.search(r"\b(étapes?|etapes?|phases?|mécanismes?|mecanismes?|fonctionne|marche|processus)\b", q_lower):
            enriched = f"{prev_topic} étapes phases mécanisme processus fonctionnement"
        # 3. Rôle, utilité, importance, but, fonction
        elif re.search(r"\b(importance|rôle|role|fonction|but|utilité|utilite|sert)\b", q_lower):
            enriched = f"{prev_topic} rôle importance utilité but fonction"
        # 4. Exemples, vie réelle, applications pratiques
        elif re.search(r"\b(exemples?|vie|réel|reel|pratique|analogie|quotidien)\b", q_lower):
            enriched = f"{prev_topic} exemple concret application pratique vie courante"
        # 5. Causes, conséquences, conditions
        elif re.search(r"\b(causes?|conséquences?|consequences?|provoque|impact|effet|conditions?)\b", q_lower):
            enriched = f"{prev_topic} causes conséquences effets impact conditions"
        # 6. Caractéristiques, propriétés, types, classification
        elif re.search(r"\b(propriétés?|proprietes?|caractéristiques?|caracteristiques?|types?|limites?)\b", q_lower):
            enriched = f"{prev_topic} caractéristiques propriétés types classification"
        # 7. Réexplication, simplification, vulgarisation, concision, résumé
        elif re.search(r"\b(reexplique|réexplique|détails?|details?|bref|court|résume|resume|simple|simplement|simplifie|vulgarise|vulgariser|compris|capté|capte)\b", q_lower):
            enriched = f"{prev_topic} explication cours définition essentiel résumé"
        else:
            curr_clean = cls.clean_core_terms(current_question)
            enriched = f"{prev_topic} {curr_clean}".strip() if curr_clean else prev_topic

        dt = time.perf_counter() - t0
        print(f"\033[36m⏱️  [contextualizer.py]\033[0m Requête contextualisée : '{enriched}' (auparavant: '{current_question}') en \033[1;33m{dt:.4f}s\033[0m")
        return enriched
