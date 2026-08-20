import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.router import v1_router


# ── App instance ───────────────────────────────────────────────────
app = FastAPI(
    title="The Archive — Group Knowledge System",
    description="Personal + group knowledge base. Each user brings their own Groq API key.",
    version="2.0.0",
)


# ── CORS Middleware ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Mount Router ───────────────────────────────────────────────────
app.include_router(v1_router)