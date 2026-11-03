from typing import List, Literal

from pydantic import BaseModel, Field, field_validator

SupportedLanguage = Literal["en", "hi", "kn"]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    language: SupportedLanguage = "en"
    history: List[ChatMessage] = Field(default_factory=list, max_length=50)

    @field_validator("language", mode="before")
    @classmethod
    def normalise_language(cls, v):
        return v.strip().lower() if isinstance(v, str) else v

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty.")
        return v


class CitationInfo(BaseModel):
    scheme_id: str
    scheme_name: str
    scheme_title: str
    state: str
    category: str


class ChatResponse(BaseModel):
    response: str
    citations: List[CitationInfo] = []
    confidence_score: int = Field(0, ge=0, le=100)
    language: str = "en"
