import time
from typing import Any

from alternia.llm.client import LLMClient

from alternia.pedagogical.legacy_adapter import (
    PedagogicalEngineAdapter,
)

from alternia.pedagogical.models import (
    PedagogicalRequest,
    QuestionAnalysis,
    StudentProfile,
)
from alternia.pedagogical.prompt_builder import (
    PedagogicalPromptBuilder,
)
from alternia.pedagogical.response_validator import (
    PedagogicalResponseValidator,
)
from alternia.rag.service import RAGService

from alternia.learner.manager import LearnerManager
from alternia.learner.models import LearningInteraction

from alternia.conversation.context import (
    ConversationContextBuilder,
)
from alternia.conversation.manager import (
    ConversationManager,
)
from alternia.pedagogical.curriculum_scope import (
    CurriculumScopeChecker,
)

class AlterniaOrchestrator:
    """
    Orchestrateur principal d'AlternIA.

    Pipeline :

        Question élève
              ↓
        RAG / contexte
              ↓
        IntentDetector
              ↓
        Moteur pédagogique
              ↓
        Stratégie pédagogique
              ↓
        PromptBuilder
              ↓
        LLM local
              ↓
        Validation
              ↓
        Réponse finale

    L'orchestrateur ne contient aucune logique
    pédagogique métier.

    Il coordonne les différents composants.
    """

    def __init__(
        self,
        pedagogical_engine,
        llm_client: LLMClient,
        rag_service: RAGService | None = None,
        validator: PedagogicalResponseValidator | None = None,
        prompt_builder: PedagogicalPromptBuilder | None = None,
        learner_manager: LearnerManager | None = None,
        conversation_manager: ConversationManager | None = None,
        conversation_context_builder: ConversationContextBuilder | None = None,
    ):
        if isinstance(
            pedagogical_engine,
            PedagogicalEngineAdapter,
        ):
            self.pedagogical_engine = pedagogical_engine
        else:
            self.pedagogical_engine = (
                PedagogicalEngineAdapter(
                    engine=pedagogical_engine
                )
            )

        self.llm_client = llm_client

        self.rag_service = rag_service

        self.validator = (
            validator
            or PedagogicalResponseValidator()
        )

        self.learner_manager = (
            learner_manager
            or LearnerManager()
        )

        self.prompt_builder = (
            prompt_builder
            or PedagogicalPromptBuilder()
        )
        self.conversation_manager = (
            conversation_manager
            or ConversationManager()
        )

        self.conversation_context_builder = (
            conversation_context_builder
            or ConversationContextBuilder()
        )
        self.curriculum_scope_checker = CurriculumScopeChecker()


    # =========================================================
    # RAG
    # =========================================================

    def ask_with_rag(
        self,
        question: str,
        student_class: str,
        subject: str | None = None,
        student_id: str = "anonymous",
        session_id: str | None = None,
        series: str | None = None,
    ):

        if self.rag_service is None:
            raise RuntimeError(
                "RAGService non configuré."
            )

        context = self.rag_service.retrieve(
            question=question,
            student_class=student_class,
            subject=subject,
            student_id=student_id,
            series=series,
        )

        return self.ask(
            question=question,
            context=context,
            student_class=student_class,
            subject=subject,
            student_id=student_id,
            session_id=session_id,
            series=series,
        )

    # =========================================================
    # RAG + STREAM
    # =========================================================

    def ask_with_rag_stream(
        self,
        question: str,
        student_class: str,
        subject: str | None = None,
        student_id: str = "anonymous",
        session_id: str | None = None,
        series: str | None = None,
    ):

        if self.rag_service is None:
            raise RuntimeError(
                "RAGService non configuré."
            )

        context = self.rag_service.retrieve(
            question=question,
            student_class=student_class,
            subject=subject,
            student_id=student_id,
            series=series,
        )

        return self.ask_stream(
            question=question,
            context=context,
            student_class=student_class,
            subject=subject,
            student_id=student_id,
            session_id=session_id,
            series=series,
        )

    # =========================================================
    # STREAMING
    # =========================================================

    def ask_stream(
        self,
        question: str,
        context: Any = None,
        student_class: str = "10eme",
        subject: str | None = None,
        student_id: str = "anonymous",
        session_id: str | None = None,
        series: str | None = None,
    ):
        """
        Génère progressivement la réponse du LLM.
        """
        # GUARD PÉDAGOGIQUE CENTRALISÉ :
        # Si un RAG est configuré et qu'aucune source valide n'est trouvée (ou score < 0.40),
        # l'orchestrateur refuse immédiatement SANS appeler le LLM.
        # if self.rag_service is not None:
        #     # Bypass RAG strictness for identity or greeting questions
        #     import re
        #     q_clean = question.strip().lower()
        #     is_identity = bool(re.search(r"^(qui es tu|qui es-tu|presente toi|présente toi|présente-toi|presente-toi|tu es qui|qui est tu|bonjour|salut)", q_clean))
            
        #     sources = getattr(context, "sources", []) if context else []
        #     max_score = max((getattr(s, "score", 0.0) for s in sources), default=0.0)
            
        #     if not is_identity and (not sources or max_score < 0.40):
        #         subject_label = subject or "la matière sélectionnée"
        #         refusal_text = (
        #             f"Je n'ai pas trouvé d'information sur ce sujet dans le programme officiel "
        #             f"de {student_class} pour {subject_label}. "
        #             f"Pose-moi une question sur {subject_label} conforme au programme de ta classe "
        #             f"pour que je puisse t'aider."
        #         )

        #         def refusal_generator():
        #             yield refusal_text

        #         return refusal_generator()

        # VÉRIFICATION DE LA PERTINENCE PÉDAGOGIQUE (Scope Guardrail)
        # Refuse les questions totalement hors-scolaires sans aucun lien avec le programme ou la conversation
        import re
        q_clean = question.strip().lower()
        is_greeting_or_id = bool(re.search(r"^(bonjour|bonsoir|salut|coucou|qui es-tu|qui est-tu|tu es qui|présente-toi|presente toi|merci|d'accord|ok|au revoir|qu'est-ce que tu peux faire|que peux-tu faire|que sais-tu faire|comment tu peux m'aider|aide|aide-moi)\b", q_clean))
        has_rag_sources = bool(context and getattr(context, "sources", []))
        
        is_conversation_followup = False
        if session_id:
            session = self.conversation_manager.get(session_id)
            if session and session.messages:
                is_conversation_followup = True

        from alternia.pedagogical.curriculum_keywords import detect_malian_curriculum_subject
        detected_subj = detect_malian_curriculum_subject(question)
        is_curriculum_topic = (detected_subj is not None)

        is_culture = (
            student_class == "culture"
            or "culture" in (student_class or "").lower()
            or "culture" in (subject or "").lower()
            or "patrimoine" in (subject or "").lower()
        )

        if not is_culture and not (is_greeting_or_id or has_rag_sources or is_conversation_followup or is_curriculum_topic):
            refusal_text = (
                "Je suis ALTA, le tuteur pédagogique d'AlternIA dédié aux programmes scolaires du secondaire au Mali. "
                "Je ne peux pas répondre aux questions hors du cadre scolaire. "
                "Pose-moi une question sur tes cours (Maths, Physique-Chimie, SVT, Histoire, Français, Anglais...) pour que je puisse t'aider !"
            )
            def refusal_stream():
                yield refusal_text
            return refusal_stream()

        t0_orch = time.perf_counter()
        print(f"\033[36m⏱️  [orchestrator.py]\033[0m Préparation orchestrateur (profil, conversation, pédagogie, prompt)...")

        profile = (
            self.learner_manager
            .to_optional_pedagogical_profile(
                student_id=student_id,
            )
        )

        learner_context = ""

        if profile is not None:
            learner_context = (
                self.learner_manager
                .build_profile_context(
                    student_id
                )
            )

        session_messages = []
        conversation_context = ""

        if session_id is not None:
            session = self.conversation_manager.get_or_create(
                session_id=session_id,
                student_id=student_id,
                student_class=student_class,
                subject=subject,
            )
            session_messages = session.last_messages(6)
            conversation_context = (
                self.conversation_context_builder
                .build(session)
            )

        pedagogical_response = (
            self._generate_pedagogical_response(
                question=question,
                context=context,
                student_class=student_class,
                subject=subject,
                profile=profile,
            )
        )

        request = self._build_pedagogical_request(
            question=question,
            context=context,
            student_class=student_class,
            subject=subject,
            pedagogical_response=pedagogical_response,
            learner_context=learner_context,
            conversation_context=conversation_context,
            profile=profile,
            series=series,
        )

        native_messages = None
        if hasattr(self.prompt_builder, "build_messages"):
            native_messages = self.prompt_builder.build_messages(
                request=request,
                strategy_instruction=pedagogical_response.answer,
                session_messages=session_messages,
            )

        prompt = self.prompt_builder.build(
            request=request,
            strategy_instruction=(
                pedagogical_response.answer
            ),
        )

        dt_prep = time.perf_counter() - t0_orch
        print(f"\033[36m⏱️  [orchestrator.py]\033[0m Préparation complète terminée en \033[1;33m{dt_prep:.4f}s\033[0m -> Démarrage de la génération LLM streaming...")

        if not hasattr(
            self.llm_client,
            "generate_stream",
        ):
            raise RuntimeError(
                "Le LLM configuré ne supporte pas "
                "le streaming."
            )

        try:
            if native_messages is not None:
                raw_stream = self.llm_client.generate_stream(
                    prompt=prompt,
                    messages=native_messages,
                    system_prompt=self.prompt_builder.system_prompt(),
                )
            else:
                raw_stream = self.llm_client.generate_stream(
                    prompt=prompt,
                    system_prompt=self.prompt_builder.system_prompt(),
                )
        except TypeError:
            raw_stream = self.llm_client.generate_stream(
                prompt=prompt,
                system_prompt=(
                    self.prompt_builder.system_prompt()
                ),
            )

        def stream_with_memory():
            full_text = ""
            for chunk in raw_stream:
                full_text += chunk
                yield chunk

            if session_id is not None and full_text.strip():
                self.conversation_manager.add_student_message(
                    session_id=session_id,
                    content=question,
                )
                self.conversation_manager.add_assistant_message(
                    session_id=session_id,
                    content=full_text.strip(),
                )

            self._register_learning_interaction(
                student_id=student_id,
                question=question,
                pedagogical_response=pedagogical_response,
                subject=subject,
            )

        return stream_with_memory()

    # =========================================================
    # PIPELINE PRINCIPAL
    # =========================================================

    @staticmethod
    def validate_followup_question(
        question: str,
        answer: str,
        intent: str,
        raw_should_ask: bool,
        followup_q: str | None,
    ) -> tuple[bool, str | None]:
        """
        Vérifie scrupuleusement si une relance/conseil AlternIA (ex: demande d'exemple)
        est pertinente par rapport à la réponse réellement fournie.
        
        RÈGLES IMPÉRATIVES :
        1. Si la réponse est un refus, un rappel hors-programme ou concerne un sujet hors cursus (ex: Harry Potter),
           INTERDICTION STRICTE de demander un exemple.
        2. Si la réponse contient DÉJÀ un exemple ("par exemple", "exemple :", etc.), ne pas redemander.
        3. Si la question est une salutation, une politesse, ou un accord simple ("oui", "merci"), pas de relance d'exemple.
        4. La relance ne doit JAMAIS être automatique : elle doit être réservée aux explications théoriques
           du programme malien où un exemple apporte une réelle valeur pédagogique ajoutée.
        """
        if not raw_should_ask or not followup_q:
            return False, None

        ans_lower = answer.lower()
        q_lower = question.lower()

        # 1. Sujet hors-programme ou refus explicite
        out_of_scope_cues = [
            "ne fait pas partie du programme",
            "ne font pas partie du programme",
            "hors programme",
            "hors-programme",
            "pas au programme",
            "hors du cadre",
            "hors du programme",
            "ne figure pas au programme",
            "je ne peux pas répondre",
            "personnage fictif",
            "n'est pas au programme",
            "n'est pas inscrit au programme",
            "n'hésite pas à me poser une question sur le programme",
        ]
        if any(cue in ans_lower for cue in out_of_scope_cues):
            return False, None

        # 2. Salutations, présentations ou politesses courtes
        greeting_cues = ["bonjour", "salut", "qui es-tu", "tu es qui", "présente-toi", "presente-toi", "au revoir", "merci"]
        if any(q_lower.startswith(g) for g in greeting_cues) and len(q_lower.split()) <= 4:
            return False, None

        # 3. La réponse donne DÉJÀ un exemple concret
        example_cues = [
            "par exemple",
            "prenons l'exemple",
            "à titre d'exemple",
            "a titre d'exemple",
            "comme exemple",
            "exemple :",
            "exemple concret",
            "illustrons cela",
            "dans la vie quotidienne",
            "dans la vie courante",
        ]
        if any(cue in ans_lower for cue in example_cues):
            return False, None

        # 4. La question demandait DÉJÀ un exemple ou validait un exemple précédent
        import re
        if re.search(r"^(oui|ouais|d'accord|dac|dacc|ok|vas-y|vas y|je veux bien|donne(-moi)? un exemple)\b", q_lower):
            return False, None

        # 5. Intentions qui ne justifient pas d'exemple
        if intent in {"out_of_scope", "exercise_solution", "greeting", "farewell"}:
            return False, None

        return True, followup_q

    def ask(
        self,
        question: str,
        context: Any = None,
        student_class: str = "10eme",
        subject: str | None = None,
        student_id: str = "anonymous",
        session_id: str | None = None,
        series: str | None = None,
    ):
        """
        Exécute le pipeline complet AlternIA.
        """
        # GUARD PÉDAGOGIQUE CENTRALISÉ :
        # Si un RAG est configuré et qu'aucune source valide n'est trouvée (ou score < 0.40),
        # l'orchestrateur refuse immédiatement SANS appeler le LLM.
        if self.rag_service is not None:
            # Bypass RAG strictness for identity or greeting questions
            import re
            q_clean = question.strip().lower()
            is_identity = bool(re.search(r"^(qui es tu|qui es-tu|presente toi|présente toi|présente-toi|presente-toi|tu es qui|qui est tu|bonjour|salut)", q_clean))

        # VÉRIFICATION DE LA PERTINENCE PÉDAGOGIQUE (Scope Guardrail)
        import re
        q_clean = question.strip().lower()
        is_greeting_or_id = bool(re.search(r"^(bonjour|bonsoir|salut|coucou|qui es-tu|qui est-tu|tu es qui|présente-toi|presente toi|merci|d'accord|ok|au revoir|qu'est-ce que tu peux faire|que peux-tu faire|que sais-tu faire|comment tu peux m'aider|aide|aide-moi)\b", q_clean))
        has_rag_sources = bool(context and getattr(context, "sources", []))
        
        is_conversation_followup = False
        if session_id:
            session = self.conversation_manager.get(session_id)
            if session and session.messages:
                is_conversation_followup = True

        from alternia.pedagogical.curriculum_keywords import detect_malian_curriculum_subject
        detected_subj = detect_malian_curriculum_subject(question)
        is_curriculum_topic = (detected_subj is not None)

        is_culture = (
            student_class == "culture"
            or "culture" in (student_class or "").lower()
            or "culture" in (subject or "").lower()
            or "patrimoine" in (subject or "").lower()
        )

        if not is_culture and not (is_greeting_or_id or has_rag_sources or is_conversation_followup or is_curriculum_topic):
            refusal_text = (
                "Je suis ALTA, le tuteur pédagogique d'AlternIA dédié aux programmes scolaires du secondaire au Mali. "
                "Je ne peux pas répondre aux questions hors du cadre scolaire. "
                "Pose-moi une question sur tes cours (Maths, Physique-Chimie, SVT, Histoire, Français, Anglais...) pour que je puisse t'aider !"
            )
            return {
                "answer": refusal_text,
                "intent": "out_of_scope",
                "student_class": student_class,
                "subject": subject,
                "sources": [],
                "should_ask_followup": False,
                "followup_question": None,
                "metadata": {
                    "rag_sources": 0,
                    "out_of_scope": True,
                    "llm_used": False,
                },
            }

        # -----------------------------------------------------
        # 1. MOTEUR PÉDAGOGIQUE
        # -----------------------------------------------------
        t0_orch = time.perf_counter()
        print(f"\033[36m⏱️  [orchestrator.py]\033[0m Préparation orchestrateur (mode synchrone ask)...")

        profile = (
            self.learner_manager
            .to_optional_pedagogical_profile(
                student_id=student_id,
            )
        )

        learner_context = ""

        if profile is not None:
            learner_context = (
                self.learner_manager
                .build_profile_context(
                    student_id
                )
            )

        session_messages = []
        conversation_context = ""

        if session_id is not None:
            session = self.conversation_manager.get_or_create(
                session_id=session_id,
                student_id=student_id,
                student_class=student_class,
                subject=subject,
            )
            session_messages = session.last_messages(6)
            conversation_context = (
                self.conversation_context_builder
                .build(session)
            )

        pedagogical_response = (
            self._generate_pedagogical_response(
                question=question,
                context=context,
                student_class=student_class,
                subject=subject,
                profile=profile,
            )
        )

        # -----------------------------------------------------
        # 2. REQUÊTE PÉDAGOGIQUE
        # -----------------------------------------------------

        request = self._build_pedagogical_request(
            question=question,
            context=context,
            student_class=student_class,
            subject=subject,
            pedagogical_response=pedagogical_response,
            learner_context=learner_context,
            conversation_context=conversation_context,
            profile=profile,
            series=series,
        )

        # -----------------------------------------------------
        # 3. PROMPT
        # -----------------------------------------------------

        native_messages = None
        if hasattr(self.prompt_builder, "build_messages"):
            native_messages = self.prompt_builder.build_messages(
                request=request,
                strategy_instruction=pedagogical_response.answer,
                session_messages=session_messages,
            )

        prompt = self.prompt_builder.build(
            request=request,
            strategy_instruction=(
                pedagogical_response.answer
            ),
        )

        dt_prep = time.perf_counter() - t0_orch
        print(f"\033[36m⏱️  [orchestrator.py]\033[0m Préparation terminée en \033[1;33m{dt_prep:.4f}s\033[0m -> Appel LLM synchrone...")

        # -----------------------------------------------------
        # 4. GÉNÉRATION LLM
        # -----------------------------------------------------

        try:
            if native_messages is not None:
                answer = self.llm_client.generate(
                    prompt=prompt,
                    messages=native_messages,
                    system_prompt=self.prompt_builder.system_prompt(),
                )
            else:
                answer = self.llm_client.generate(
                    prompt=prompt,
                    system_prompt=self.prompt_builder.system_prompt(),
                )
        except TypeError:
            answer = self.llm_client.generate(
                prompt=prompt,
                system_prompt=(
                    self.prompt_builder.system_prompt()
                ),
            )

        answer = self.validator.validate(
            answer,
            question=question,
            context=request.context,
        )

        self._register_learning_interaction(
            student_id=student_id,
            question=question,
            pedagogical_response=pedagogical_response,
            subject=subject,
        )

        if session_id is not None:
            self.conversation_manager.add_student_message(
                session_id=session_id,
                content=question,
            )
            self.conversation_manager.add_assistant_message(
                session_id=session_id,
                content=answer,
            )

        # -----------------------------------------------------
        # 6. RÉPONSE STRUCTURÉE AVEC VALIDATION DE COHÉRENCE DU CONSEIL
        # -----------------------------------------------------

        final_should_ask, final_followup = self.validate_followup_question(
            question=question,
            answer=answer,
            intent=pedagogical_response.intent,
            raw_should_ask=pedagogical_response.should_ask_followup,
            followup_q=pedagogical_response.followup_question,
        )

        return {
            "answer": answer,

            "intent": (
                pedagogical_response.intent
            ),

            "student_class": (
                student_class
            ),

            "subject": subject,

            "sources": (
                pedagogical_response.sources
            ),

            "should_ask_followup": final_should_ask,

            "followup_question": final_followup,

            "metadata": {
                **pedagogical_response.metadata,

                "llm_used": True,

                "prompt_builder": (
                    "alternia.pedagogical"
                ),

                "response_validator": (
                    "alternia.pedagogical"
                ),
            },
        }

    # =========================================================
    # CONSTRUCTION DE LA REQUÊTE PÉDAGOGIQUE
    # =========================================================
    def _generate_pedagogical_response(
        self,
        question: str,
        context: Any,
        student_class: str,
        subject: str | None,
        profile: StudentProfile | None,
    ):
        """
        Compatible avec :

        1. PedagogicalEngineAdapter
        → generate()

        2. PedagogicalEngine
        → process()

        L'orchestrateur reste compatible avec
        l'ancienne architecture pendant la migration.
        """

        # =====================================================
        # NOUVELLE INTERFACE : ADAPTER
        # =====================================================

        if hasattr(
            self.pedagogical_engine,
            "generate",
        ):
            try:
                return self.pedagogical_engine.generate(
                    question=question,
                    context=context,
                    student_class=student_class,
                    subject=subject,
                    profile=profile,
                )

            except TypeError as exc:

                if (
                    "unexpected keyword argument 'profile'"
                    not in str(exc)
                ):
                    raise

                return self.pedagogical_engine.generate(
                    question=question,
                    context=context,
                    student_class=student_class,
                    subject=subject,
                )

        # =====================================================
        # ANCIEN / NOUVEAU MOTEUR DIRECT : process()
        # =====================================================

        if hasattr(
            self.pedagogical_engine,
            "process",
        ):

            if profile is None:
                profile = StudentProfile(
                    student_class=student_class,
                )

            context_text = ""

            if isinstance(context, str):
                context_text = context.strip()

            elif context is not None:
                context_text = str(
                    getattr(
                        context,
                        "context_text",
                        "",
                    )
                ).strip()

            # -------------------------------------------------
            # Détection d'intention
            # -------------------------------------------------

            from alternia.pedagogy.intent import (
                IntentDetector,
                PedagogicalIntent,
            )

            detector = IntentDetector()

            detected_intent = detector.detect(
                question
            )

            intent_mapping = {
                PedagogicalIntent.CONCEPT_EXPLANATION:
                    "explanation",

                PedagogicalIntent.PROBLEM_SOLVING:
                    "explanation",

                PedagogicalIntent.PRACTICE:
                    "exercise",

                PedagogicalIntent.REEXPLANATION:
                    "explanation",

                PedagogicalIntent.CORRECTION:
                    "correction",

                PedagogicalIntent.REVISION:
                    "revision",

                PedagogicalIntent.SUMMARY:
                    "summary",

                PedagogicalIntent.UNKNOWN:
                    "explanation",
            }

            intent = intent_mapping.get(
                detected_intent,
                "explanation",
            )

            # -------------------------------------------------
            # Requête pédagogique
            # -------------------------------------------------

            request = PedagogicalRequest(
                question=question,
                profile=profile,
                analysis=QuestionAnalysis(
                    original_question=question,
                    intent=intent,
                    student_class=student_class,
                    subject=subject,
                ),
                context=context_text,
            )

            # -------------------------------------------------
            # Nouveau moteur
            # -------------------------------------------------

            response = self.pedagogical_engine.process(
                request
            )

            # -------------------------------------------------
            # Normalisation du résultat
            # -------------------------------------------------

            from types import SimpleNamespace

            sources = []

            if context is not None:
                sources = list(
                    getattr(
                        context,
                        "sources",
                        [],
                    )
                )

            scope_result = self.curriculum_scope_checker.check_scope(
                question=question,
                student_class=student_class,
                subject=subject,
            )

            followup_q = response.follow_up_question
            if scope_result.is_higher_level and scope_result.prerequisites:
                followup_q = (
                    f"Souhaites-tu que l'on révise d'abord un prérequis de {student_class} "
                    f"(par exemple : {scope_result.prerequisites[0]}) ?"
                )

            return SimpleNamespace(
                answer=response.answer,
                intent=response.intent,
                student_class=response.student_class,
                subject=response.subject,
                sources=sources,
                should_ask_followup=(
                    response.needs_follow_up or scope_result.is_higher_level
                ),
                followup_question=followup_q,
                metadata={
                    "context_used": bool(
                        context_text
                    ),
                    "source_count": len(
                        sources
                    ),
                    "pedagogical_engine": (
                        "alternia.pedagogical"
                    ),
                    "intent_detector": (
                        "alternia.pedagogy"
                    ),
                    "curriculum_scope": {
                        "is_higher_level": scope_result.is_higher_level,
                        "target_class": scope_result.target_class,
                        "target_series": scope_result.target_series,
                        "topic_name": scope_result.topic_name,
                        "prerequisites": scope_result.prerequisites,
                        "suggested_questions": scope_result.suggested_questions,
                    },
                },
            )


        # =====================================================
        # COMPOSANT INVALIDE
        # =====================================================

        raise TypeError(
            "Le moteur pédagogique fourni doit exposer "
            "une méthode generate() ou process()."
        )


    # =========================================================
    # APPRENTISSAGE
    # =========================================================

    def _register_learning_interaction(
        self,
        student_id: str,
        question: str,
        pedagogical_response: Any,
        subject: str | None = None,
        success: bool | None = None,
    ) -> None:
        """
        Enregistre l'interaction dans la mémoire
        pédagogique de l'élève.

        Une interaction peut être enregistrée sans
        résultat d'apprentissage connu.

        Dans ce cas :
            success=None

        Le résultat pourra être renseigné plus tard
        lorsqu'un exercice ou une correction sera évalué.
        """

        if not student_id:
            return

        if not self.learner_manager.has_profile(
            student_id
        ):
            return

        interaction = LearningInteraction(
            question=question,
            intent=pedagogical_response.intent,
            subject=subject,
            topic=self._extract_learning_topic(
                pedagogical_response
            ),
            difficulty=self._extract_learning_difficulty(
                pedagogical_response
            ),
            success=success,
        )

        self.learner_manager.register_interaction(
            student_id=student_id,
            interaction=interaction,
        )

    @staticmethod
    def _extract_learning_topic(
        pedagogical_response: Any,
    ) -> str | None:
        """
        Essaie de récupérer la notion depuis
        la réponse pédagogique.
        """

        metadata = getattr(
            pedagogical_response,
            "metadata",
            {},
        )

        if not isinstance(metadata, dict):
            return None

        topic = metadata.get("topic")

        if topic:
            return str(topic).strip()

        return None

    @staticmethod
    def _extract_learning_difficulty(
        pedagogical_response: Any,
    ) -> str | None:
        """
        Essaie de récupérer le niveau de difficulté
        depuis les métadonnées pédagogiques.
        """

        metadata = getattr(
            pedagogical_response,
            "metadata",
            {},
        )

        if not isinstance(metadata, dict):
            return None

        difficulty = metadata.get(
            "difficulty"
        )

        if difficulty:
            return str(difficulty).strip()

        return None
    
    @staticmethod
    def _build_pedagogical_request(
        question: str,
        context: Any,
        student_class: str,
        subject: str | None,
        pedagogical_response: Any,
        learner_context: str = "",
        conversation_context: str = "",
        profile: StudentProfile | None = None,
        series: str | None = None,
    ) -> PedagogicalRequest:

        context_text = ""

        if isinstance(context, str):
            context_text = context.strip()

        elif context is not None:
            context_text = str(
                getattr(
                    context,
                    "context_text",
                    "",
                )
            ).strip()

        if profile is None:
            profile = StudentProfile(
                student_id="anonymous",
                student_class=student_class,
                series=series,
            )
        elif series and not getattr(profile, "series", None):
            profile.series = series

        if learner_context.strip():

            if context_text:
                context_text = (
                    learner_context.strip()
                    + "\n\n"
                    + context_text
                )
            else:
                context_text = (
                    learner_context.strip()
                )

        return PedagogicalRequest(
            question=question,

            profile=(
                profile
                if profile is not None
                else StudentProfile(
                    student_class=student_class,
                )
            ),
            analysis=QuestionAnalysis(
                original_question=question,
                intent=pedagogical_response.intent,
                student_class=student_class,
                subject=subject,
            ),
            conversation_context=conversation_context,

            context=context_text,
        )

    # =========================================================
    # REQUÊTES ASYNCHRONES / UTILITAIRES (Flashcards, Podcasts, etc.)
    # =========================================================
    async def process_message(
        self,
        user_message: str,
        conversation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Traite un message utilisateur de manière asynchrone pour les requêtes utilitaires
        (génération de flashcards, podcasts, synthèses, etc.).
        Prend en charge les métadonnées telles que 'system_override' et exécute l'appel LLM
        dans un thread pool afin d'éviter de bloquer la boucle d'événements asyncio.
        """
        import asyncio

        meta = metadata or {}
        system_override = meta.get("system_override")
        max_tokens = meta.get("max_tokens")

        content = await asyncio.to_thread(
            self.llm_client.generate,
            prompt=user_message,
            system_prompt=system_override,
            max_tokens=max_tokens,
        )

        return {
            "content": content,
            "conversation_id": conversation_id,
            "metadata": meta,
        }