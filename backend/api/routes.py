import os
import sys
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from config import UPLOAD_DIR
from core.ingestion import ingest_document, ingest_note
from core.vectorstore import add_to_vectorstore, load_vectorstore
from core.llm_chain import ask_question
from models.schemas import (
    NoteRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    SourceDocument
)

router = APIRouter()


# ── 1. Health Check ────────────────────────────────────────────────
@router.get("/health")
def health_check():
    return {"status": "ok", "message": "RAG Knowledge System is running"}


# ── 2. Ingest Document ─────────────────────────────────────────────
@router.post("/ingest/document", response_model=IngestResponse)
async def ingest_document_route(file: UploadFile = File(...)):
    """Upload a PDF or TXT file and add it to the knowledge base."""

    # Validate file type
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Only PDF and TXT allowed."
        )

    # Save file to uploads/
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Ingest and add to vectorstore
    chunks = ingest_document(file_path)
    add_to_vectorstore(chunks)

    return IngestResponse(
        message=f"'{file.filename}' ingested successfully.",
        chunks_added=len(chunks),
        source=file.filename
    )


# ── 3. Ingest Note ─────────────────────────────────────────────────
@router.post("/ingest/note", response_model=IngestResponse)
async def ingest_note_route(request: NoteRequest):
    """Submit a plain text note and add it to the knowledge base."""

    chunks = ingest_note(request.title, request.content)
    add_to_vectorstore(chunks)

    return IngestResponse(
        message=f"Note '{request.title}' ingested successfully.",
        chunks_added=len(chunks),
        source=request.title
    )


# ── 4. Query ───────────────────────────────────────────────────────
@router.post("/query", response_model=QueryResponse)
async def query_route(request: QueryRequest):
    """Ask a question against the knowledge base."""

    try:
        retriever = load_vectorstore().as_retriever(search_kwargs={"k": 4})
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    answer, sources = ask_question(
        retriever=retriever,
        question=request.question,
        chat_history=request.chat_history
    )

    source_docs = [SourceDocument(**s) for s in sources]

    return QueryResponse(answer=answer, sources=source_docs)


# ── 5. List Documents ──────────────────────────────────────────────
@router.get("/documents")
def list_documents():
    """Return all unique sources currently in the knowledge base."""

    try:
        vectorstore = load_vectorstore()
    except FileNotFoundError:
        return JSONResponse(content={"documents": []})

    # Pull metadata from all stored vectors
    all_docs = vectorstore.docstore._dict.values()

    seen = set()
    documents = []
    for doc in all_docs:
        source = doc.metadata.get("source", "unknown")
        if source not in seen:
            seen.add(source)
            documents.append({
                "source": source,
                "page": doc.metadata.get("page", 0)
            })

    return {"documents": documents, "total": len(documents)}