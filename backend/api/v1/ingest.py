import os
import shutil

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from config import DATA_DIR
from core.ingestion import ingest_document, ingest_note
from core.vectorstore import add_to_vectorstore
from models.schemas import NoteRequest, IngestResponse
from api.deps import validate_session

router = APIRouter()


def _resolve_upload_dir(collection: str) -> str:
    """Return upload_dir based on collection."""
    upload_dir = os.path.join(DATA_DIR, collection, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


# ── Ingest Document ────────────────────────────────────────────────
@router.post("/ingest/document", response_model=IngestResponse)
async def ingest_document_route(
    file: UploadFile = File(...),
    collection: str = Depends(validate_session)
):
    """Upload a PDF or TXT file and add it to the personal knowledge base."""

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Only PDF and TXT allowed."
        )

    upload_dir = _resolve_upload_dir(collection)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    chunks = ingest_document(file_path)
    add_to_vectorstore(chunks, collection)

    return IngestResponse(
        message=f"'{file.filename}' ingested successfully.",
        chunks_added=len(chunks),
        source=file.filename
    )


# ── Ingest Note ────────────────────────────────────────────────────
@router.post("/ingest/note", response_model=IngestResponse)
async def ingest_note_route(
    request: NoteRequest,
    collection: str = Depends(validate_session)
):
    """Submit a plain text note and add it to the personal knowledge base."""

    chunks = ingest_note(request.title, request.content)
    add_to_vectorstore(chunks, collection)

    return IngestResponse(
        message=f"Note '{request.title}' ingested successfully.",
        chunks_added=len(chunks),
        source=request.title
    )
