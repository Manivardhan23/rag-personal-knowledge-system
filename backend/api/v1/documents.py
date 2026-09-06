from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from core.vectorstore import list_documents, delete_document
from api.deps import validate_session

router = APIRouter()


# ── List Documents ─────────────────────────────────────────────────
@router.get("/documents")
def list_documents_route(
    collection: str = Depends(validate_session)
):
    """Return all unique sources in the personal knowledge base."""
    docs = list_documents(collection)
    return {"documents": docs, "total": len(docs)}


# ── Delete Document ─────────────────────────────────────────────────
@router.delete("/documents")
def delete_document_route(
    source: str,
    collection: str = Depends(validate_session)
):
    """Delete a document from the personal knowledge base."""
    if not source:
        raise HTTPException(status_code=400, detail="Source parameter is required.")

    delete_document(collection, source)
    return {"message": "Document deleted.", "source": source}
