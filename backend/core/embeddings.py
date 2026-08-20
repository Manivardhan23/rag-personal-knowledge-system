from langchain_huggingface import HuggingFaceEmbeddings


def get_embeddings():
    """Return the active embedding model.

    Swap this function to change the embedding model across the entire app.
    Current: all-MiniLM-L6-v2 (local, CPU, no API key needed)
    Future:  gemini-embedding-001 (API-based, higher accuracy)
    """
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )
