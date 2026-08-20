import os
import shutil

from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from typing import Optional

from config import DATA_DIR, personal_collection, admin_collection
from core.ingestion import ingest_document, ingest_note
from core.vectorstore import add_to_vectorstore
from models.schemas import NoteRequest, IngestResponse

router = APIRouter()


def _resolve_collection(member_id: Optional[str], is_admin: Optional[str]) -> tuple[str, str]:
    """Return (collection_name, upload_dir) based on who is calling."""
    if is_admin == "true":
        col = admin_collection()
        upload_dir = os.path.join(DATA_DIR, "admin", "uploads")
    elif member_id:
        col = personal_collection(member_id)
        upload_dir = os.path.join(DATA_DIR, "members", member_id, "uploads")
    else:
        raise HTTPException(status_code=400, detail="Missing x-member-id or x-is-admin header.")
    os.makedirs(upload_dir, exist_ok=True)
    return col, upload_dir


# ── Ingest Document ────────────────────────────────────────────────
@router.post("/ingest/document", response_model=IngestResponse)
async def ingest_document_route(
    file: UploadFile = File(...),
    x_member_id: Optional[str] = Header(None),
    x_is_admin: Optional[str] = Header(None),
):
    """Upload a PDF or TXT file and add it to the caller's knowledge base."""

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Only PDF and TXT allowed."
        )

    collection, upload_dir = _resolve_collection(x_member_id, x_is_admin)
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
    x_member_id: Optional[str] = Header(None),
    x_is_admin: Optional[str] = Header(None),
):
    """Submit a plain text note and add it to the caller's knowledge base."""

    collection, _ = _resolve_collection(x_member_id, x_is_admin)
    chunks = ingest_note(request.title, request.content)
    add_to_vectorstore(chunks, collection)

    return IngestResponse(
        message=f"Note '{request.title}' ingested successfully.",
        chunks_added=len(chunks),
        source=request.title
    )

