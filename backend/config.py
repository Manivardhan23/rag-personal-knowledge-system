import os
from dotenv import load_dotenv

load_dotenv()

# LLM Provider — switch between "gemini" and "groq" in .env
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Storage paths — always absolute, works on any machine
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
FAISS_INDEX_DIR = os.path.join(DATA_DIR, "faiss_index")

# Chunking config
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Retrieval config
RETRIEVER_K = 4