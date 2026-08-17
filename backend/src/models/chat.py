"""
Schémas Pydantic pour le chat pédagogique et les interactions d'apprentissage.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class ChatMessagePayload(BaseModel):
    role: str = "user"
    text: str


class ChatRequest(BaseModel):
    question: str
    student_class: str = "12eme"
    subject: Optional[str] = None
    student_id: str = "eleve_mobile"
    student_name: Optional[str] = "Élève"
    session_id: Optional[str] = None
    enable_rag: bool = True
    history: Optional[list[ChatMessagePayload]] = None


class ChatSource(BaseModel):
    chunk_id: Optional[str] = None
    document: str
    chapter: Optional[str] = None
    lesson: Optional[str] = None
    score: float = 0.0
    content_preview: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    intent: str
    student_class: str
    subject: Optional[str] = None
    sources: list[ChatSource] = Field(default_factory=list)
    should_ask_followup: bool = False
    followup_question: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class InteractionRecord(BaseModel):
    intent: str
    subject: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    success: Optional[bool] = None


class ResetSessionRequest(BaseModel):
    session_id: str
