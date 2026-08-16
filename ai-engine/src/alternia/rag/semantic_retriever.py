import math
import re
import unicodedata
from alternia.core.models import (
    KnowledgeChunk,
    StudentQuestion,
)
from alternia.rag.embeddings import EmbeddingService
from alternia.rag.vector_store import LocalVectorStore


class SemanticRetriever:
    """
    Moteur de recherche hybride (Dense Sémantique + Lexical BM25) d'AlternIA.

    Pipeline haute efficacité :
        StudentQuestion
              ↓
        Embedding sémantique de la question
              ↓
        Recherche vectorielle large + multi-niveaux fallback
              ↓
        Scoring lexical BM25 avec normalisation sans accents
              ↓
        Reranking hybride pondéré (0.65 Sémantique + 0.35 BM25 + Bonus didactiques)
              ↓
        Déduplication et sélection Top-K
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: LocalVectorStore,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    # =========================================================
    # INDEXATION
    # =========================================================

    def add_documents(
        self,
        documents: list[KnowledgeChunk],
    ) -> None:

        if not documents:
            return

        texts = [
            self._build_document_text(document)
            for document in documents
        ]

        vectors = self.embedding_service.encode_many(
            texts
        )

        self.vector_store.add_many(
            documents,
            vectors,
        )

    # =========================================================
    # RECHERCHE
    # =========================================================

    def search(
        self,
        question: StudentQuestion,
        top_k: int = 5,
    ) -> list[tuple[KnowledgeChunk, float]]:

        if top_k <= 0:
            return []

        query_text = self._build_query_text(question)
        query_vector = self.embedding_service.encode(query_text)

        # 1. Recherche vectorielle large avec filtrage hiérarchique de classe & série
        candidate_k = max(top_k * 5, 30)

        results = self.vector_store.search(
            query_vector=query_vector,
            top_k=candidate_k,
            student_class=question.student_class,
            student_series=getattr(question, "series", None),
            subject=question.subject,
            allow_fallback=True,
        )

        # 2. Nettoyage
        results = self._remove_duplicates(results)
        results = self._remove_empty_content(results)

        if not results:
            return []

        # 3. Reranking hybride (Dense + BM25)
        results = self._rerank(
            question=question,
            results=results,
        )

        return results[:top_k]

    # =========================================================
    # RERANKING HYBRIDE
    # =========================================================

    @classmethod
    def _rerank(
        cls,
        question: StudentQuestion,
        results: list[tuple[KnowledgeChunk, float]],
    ) -> list[tuple[KnowledgeChunk, float]]:

        question_text = question.question.strip()
        norm_q = cls._normalize_text(question_text)
        question_tokens = cls._tokenize(norm_q)
        query_tokens_set = set(question_tokens)

        definition_query = cls._is_definition_question(norm_q)
        formula_query = cls._is_formula_or_method_question(norm_q)

        # Calcul des fréquences de termes pour BM25 simplifié
        ranked = []

        for document, semantic_score in results:
            content_norm = cls._normalize_text(document.content)
            title_norm = cls._normalize_text(f"{document.chapter or ''} {document.title or ''}")
            doc_tokens = cls._tokenize(content_norm)

            # Score lexical BM25 normalisé
            lexical_score = cls._compute_bm25_score(
                query_tokens=query_tokens_set,
                doc_tokens=doc_tokens,
                title_tokens=set(cls._tokenize(title_norm)),
            )

            # Boost pédagogique
            pedagogical_boost = 0.0

            # Bonus définition
            if definition_query:
                def_markers = [
                    "definition", "on appelle", "est un", "est une",
                    "designe", "signifie", "se definit", "on dit que"
                ]
                if any(m in content_norm for m in def_markers):
                    pedagogical_boost += 0.15

            # Bonus formule / calcul / théorème
            if formula_query:
                form_markers = [
                    "formule", "theoreme", "methode", "propriete",
                    "calculer", "resolution", "regle", "enonce"
                ]
                if any(m in content_norm for m in form_markers):
                    pedagogical_boost += 0.15

            # Bonus si des mots-clés apparaissent dans le titre de chapitre / leçon
            title_matches = sum(1 for tok in question_tokens if tok in title_norm)
            if title_matches > 0:
                pedagogical_boost += min(title_matches * 0.10, 0.25)

            # Score final combiné
            final_score = (
                semantic_score * 0.65
                + lexical_score * 0.35
                + pedagogical_boost
            )

            ranked.append((document, final_score))

        ranked.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return ranked

    # =========================================================
    # CALCUL BM25 NORMALISÉ
    # =========================================================

    @classmethod
    def _compute_bm25_score(
        cls,
        query_tokens: set[str],
        doc_tokens: list[str],
        title_tokens: set[str],
        k1: float = 1.5,
        b: float = 0.75,
        avg_doc_len: float = 120.0,
    ) -> float:
        if not query_tokens or not doc_tokens:
            return 0.0

        doc_len = len(doc_tokens)
        score = 0.0

        # Term frequencies
        tf_dict: dict[str, int] = {}
        for token in doc_tokens:
            tf_dict[token] = tf_dict.get(token, 0) + 1

        matched_tokens = 0
        for token in query_tokens:
            tf = tf_dict.get(token, 0)
            if tf > 0:
                matched_tokens += 1
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_len / avg_doc_len))
                score += numerator / max(denominator, 1e-6)

                # Bonus titre
                if token in title_tokens:
                    score += 1.0

        # Normalisation entre 0 et 1
        coverage = matched_tokens / max(len(query_tokens), 1)
        normalized_score = min((score / (len(query_tokens) * (k1 + 1))) * 0.6 + coverage * 0.4, 1.0)
        return float(normalized_score)

    # =========================================================
    # INTENTIONS PÉDAGOGIQUES
    # =========================================================

    @staticmethod
    def _is_definition_question(text: str) -> bool:
        definition_patterns = (
            "qu'est-ce que", "qu est ce que", "c'est quoi", "c est quoi",
            "definition de", "definis", "definir", "que signifie",
            "signification de", "qu'entend-on par", "citer"
        )
        return any(p in text for p in definition_patterns)

    @staticmethod
    def _is_formula_or_method_question(text: str) -> bool:
        formula_patterns = (
            "comment resoudre", "comment calculer", "formule",
            "enonce", "lois de", "comment determiner", "quelles sont les",
            "comment distinguer", "methode", "etapes"
        )
        return any(p in text for p in formula_patterns)

    # =========================================================
    # NORMALISATION & TOKENISATION
    # =========================================================

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Supprime les accents, met en minuscule et nettoie la ponctuation."""
        if not text:
            return ""
        nfkd = unicodedata.normalize("NFKD", text)
        no_accents = "".join([c for c in nfkd if not unicodedata.combining(c)])
        return no_accents.lower().strip()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        words = re.findall(r"[a-z0-9_²³]+", text)
        stopwords = {
            "le", "la", "les", "un", "une", "des", "du", "de", "d",
            "ce", "cette", "ces", "est", "sont", "ete", "etre",
            "que", "qu", "qui", "quoi", "dans", "pour", "par",
            "sur", "avec", "sans", "sous", "et", "ou", "a", "au",
            "aux", "en", "je", "tu", "il", "elle", "on", "nous",
            "vous", "ils", "elles", "mon", "ton", "son", "notre",
            "votre", "leur", "ne", "pas", "plus", "moins", "tres"
        }
        return [
            w for w in words
            if len(w) > 1 and w not in stopwords
        ]

    # =========================================================
    # CONSTRUCTION TEXTE DOCUMENT ET REQUÊTE
    # =========================================================

    @staticmethod
    def _build_document_text(document: KnowledgeChunk) -> str:
        """Construit le texte textuel dense destiné à l'embedding."""
        header_parts = []
        if document.subject:
            header_parts.append(document.subject.value)
        if document.chapter and document.chapter not in {"Non défini", "unknown-chapter"}:
            header_parts.append(document.chapter)
        if document.title and document.title not in {"Sans titre", "Document sans titre", "unknown-lesson"}:
            header_parts.append(document.title)

        header = " - ".join(header_parts)
        if header:
            return f"{header}\n{document.content.strip()}"
        return document.content.strip()

    @staticmethod
    def _build_query_text(question: StudentQuestion) -> str:
        """Construit la requête sémantique naturelle pour l'embedding."""
        q = question.question.strip()
        # Si la matière est connue et pas déjà dans la question, on l'associe discrètement
        if question.subject and question.subject.value not in q.lower():
            return f"{question.subject.value} : {q}"
        return q

    # =========================================================
    # DÉDUPLICATION ET FILTRAGE
    # =========================================================

    @staticmethod
    def _remove_duplicates(
        results: list[tuple[KnowledgeChunk, float]],
    ) -> list[tuple[KnowledgeChunk, float]]:
        seen: set[str] = set()
        unique = []
        for doc, score in results:
            if doc.chunk_id in seen:
                continue
            seen.add(doc.chunk_id)
            unique.append((doc, score))
        return unique

    @staticmethod
    def _remove_empty_content(
        results: list[tuple[KnowledgeChunk, float]],
    ) -> list[tuple[KnowledgeChunk, float]]:
        return [
            (doc, score)
            for doc, score in results
            if doc.content and doc.content.strip()
        ]