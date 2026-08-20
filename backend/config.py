import os
from dotenv import load_dotenv

load_dotenv()

# Admin credentials (server-side only)
ADMIN_GROQ_KEY = os.getenv("ADMIN_GROQ_KEY", "")
ADMIN_SECRET   = os.getenv("ADMIN_SECRET", "")

# Storage paths
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "data")

# Chunking config
CHUNK_SIZE    = 1000
CHUNK_OVERLAP = 200

# Retrieval config
RETRIEVER_K = 4

# Groq model config — primary 120B, fallback 20B
GROQ_PRIMARY_MODEL  = "openai/gpt-oss-120b"
GROQ_FALLBACK_MODEL = "openai/gpt-oss-20b"

# ── Named collection helpers ────────────────────────────────
# Each user gets their own ChromaDB collection inside one shared chroma folder.

CHROMA_DIR = os.path.join(DATA_DIR, "chroma")

def personal_collection(member_id: str) -> str:
    """Collection name for a user's private knowledge base."""
    return f"personal_{member_id}"

def admin_collection() -> str:
    """Collection name for the admin's private knowledge base."""
    return "personal_admin"