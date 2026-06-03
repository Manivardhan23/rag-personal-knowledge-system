import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routes import router
from core.vectorstore import load_vectorstore


# ── Lifespan: runs on startup and shutdown ─────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the vectorstore when the server starts."""
    print("[main] Starting up RAG Knowledge System...")
    try:
        load_vectorstore()
        print("[main] Vectorstore loaded successfully.")
    except FileNotFoundError:
        print("[main] No vectorstore found yet — ingest a document first.")
    yield
    print("[main] Shutting down.")


# ── App instance ───────────────────────────────────────────────────
app = FastAPI(
    title="RAG Personal Knowledge System",
    description="Upload documents and notes, then query them with AI.",
    version="1.0.0",
    lifespan=lifespan
)


# ── CORS Middleware ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Mount Router ───────────────────────────────────────────────────
app.include_router(router)