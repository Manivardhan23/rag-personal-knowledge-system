from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from typing import Optional

from config import personal_collection, admin_collection
from core.vectorstore import list_documents

router = APIRouter()


# ── List Documents ─────────────────────────────────────────────────
@router.get("/documents")
def list_documents_route(
    x_member_id: Optional[str] = Header(None),
    x_is_admin: Optional[str] = Header(None),
):
    """Return all unique sources in the caller's knowledge base."""

    if x_is_admin == "true":
        collection = admin_collection()
    elif x_member_id:
        collection = personal_collection(x_member_id)
    else:
        return JSONResponse(content={"documents": [], "total": 0})

    docs = list_documents(collection)
    return {"documents": docs, "total": len(docs)}

