from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from config import ADMIN_GROQ_KEY, personal_collection, admin_collection
from core.vectorstore import get_retriever
from core.llm_chain import ask_question
from models.schemas import QueryRequest, QueryResponse, SourceDocument

router = APIRouter()


# ── Query ──────────────────────────────────────────────────────────
@router.post("/query", response_model=QueryResponse)
async def query_route(
    request: QueryRequest,
    x_groq_api_key: Optional[str] = Header(None),
    x_member_id: Optional[str] = Header(None),
    x_is_admin: Optional[str] = Header(None),
):
    """Ask a question against the caller's personal knowledge base."""

    # Determine API key to use
    if x_is_admin == "true":
        api_key = ADMIN_GROQ_KEY
        collection = admin_collection()
    elif x_groq_api_key and x_member_id:
        api_key = x_groq_api_key
        collection = personal_collection(x_member_id)
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide x-groq-api-key + x-member-id headers, or x-is-admin: true."
        )

    try:
        retriever = get_retriever(collection)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    answer, sources = ask_question(
        retriever=retriever,
        question=request.question,
        api_key=api_key,
        chat_history=request.chat_history
    )

    source_docs = [SourceDocument(**s) for s in sources]
    return QueryResponse(answer=answer, sources=source_docs)

