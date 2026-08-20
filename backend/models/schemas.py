from pydantic import BaseModel
from typing import Optional

# ── Ingestion ──────────────────────────────────────────────
class NoteRequest(BaseModel):
    title: str
    content: str

class IngestResponse(BaseModel):
    message: str
    chunks_added: int
    source: str

# ── Query ──────────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str
    chat_history: Optional[list] = []

class SourceDocument(BaseModel):
    source: str
    page: Optional[int] = None
    preview: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]

# ── Admin ──────────────────────────────────────────────────
class AdminLoginRequest(BaseModel):
    secret: str

class AdminLoginResponse(BaseModel):
    success: bool
    message: str