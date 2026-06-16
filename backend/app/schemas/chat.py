from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    language: str = "en" # "en", "hi", "kn"
    history: List[ChatMessage] = []

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
