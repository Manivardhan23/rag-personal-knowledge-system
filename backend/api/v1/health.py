from fastapi import APIRouter

router = APIRouter()


# ── Health Check ───────────────────────────────────────────────────
@router.get("/health")
def health_check():
    return {"status": "ok", "message": "RAG Knowledge System is running"}
