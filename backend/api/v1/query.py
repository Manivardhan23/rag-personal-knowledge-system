from fastapi import APIRouter, HTTPException, Depends

from config import ADMIN_GROQ_KEY
from core.vectorstore import get_retriever
from core.llm_chain import ask_question
from models.schemas import QueryRequest, QueryResponse, SourceDocument
from api.deps import validate_session

router = APIRouter()


# ── Query ──────────────────────────────────────────────────────────
@router.post("/query", response_model=QueryResponse)
async def query_route(
    request: QueryRequest,
    collection: str = Depends(validate_session)
):
    """Ask a question against the personal knowledge base."""
    try:
        retriever = get_retriever(collection)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    answer, sources = ask_question(
        retriever=retriever,
        question=request.question,
        api_key=ADMIN_GROQ_KEY,
        chat_history=request.chat_history
    )

    source_docs = [SourceDocument(**s) for s in sources]
    return QueryResponse(answer=answer, sources=source_docs)
