from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional


class ParseLessonRequest(BaseModel):
    text: str = Field(min_length=1)
    num_students: int = Field(default=500, ge=1, le=2000)

    @field_validator("text")
    @classmethod
    def require_lesson(cls, text: str) -> str:
        if not text.strip():
            raise ValueError("Lesson text must not be blank")
        return text


class ConceptChunk(BaseModel):
    order: int
    text: str
    concepts: List[str]
    prerequisites: List[str]
    embedding: List[float]


class PersonalityModifiers(BaseModel):
    comprehension_bonus: float
    random_dropout_chance: float
    threshold_modifier: float


class Student(BaseModel):
    id: int
    personality: str
    knowledge_vector: List[float]
    dropout_threshold: float
    modifiers: PersonalityModifiers


class HandoffResponse(BaseModel):
    chunks: List[ConceptChunk]
    students: List[Student]
    personality_modifiers: Dict[str, PersonalityModifiers]


class HealthResponse(BaseModel):
    status: str
