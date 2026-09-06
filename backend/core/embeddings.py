from langchain_huggingface import HuggingFaceEmbeddings

# Module-level singleton — loaded once at startup, reused for all requests.
# Prevents reloading the 80MB model on every API call.
_embeddings = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Return the cached embedding model (initialised on first call only).

    Swap model_name here to change the embedding model across the entire app.
    Current: all-MiniLM-L6-v2  (local, CPU, no API key needed)
    Future:  gemini-embedding-001 (API-based, higher accuracy)
    """
    global _embeddings
    if _embeddings is None:
        print("[embeddings] Loading all-MiniLM-L6-v2 model (first-time only)…")
        _embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"}
        )
        print("[embeddings] Model loaded and cached.")
    return _embeddings
