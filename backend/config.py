import os
from dotenv import load_dotenv

load_dotenv()

# ── Credentials ────────────────────────────────────────────
ADMIN_GROQ_KEY = os.getenv("ADMIN_GROQ_KEY", "")
APP_USERNAME   = "Manivardhan"
APP_PASSWORD   = "Varikuti456"

# ── Storage paths ───────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ── Chunking config ─────────────────────────────────────────
CHUNK_SIZE    = 1000
CHUNK_OVERLAP = 200

# ── Retrieval config ────────────────────────────────────────
RETRIEVER_K = 4

# ── Groq model config — primary 120B, fallback 20B ─────────
GROQ_PRIMARY_MODEL  = "openai/gpt-oss-120b"
GROQ_FALLBACK_MODEL = "openai/gpt-oss-20b"

# ── Single user collection ──────────────────────────────────
CHROMA_DIR      = os.path.join(DATA_DIR, "chroma")
USER_COLLECTION = "personal_manivardhan"