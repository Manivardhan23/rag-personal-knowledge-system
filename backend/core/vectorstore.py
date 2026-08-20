import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_chroma import Chroma
from langchain_core.documents import Document
from config import CHROMA_DIR, RETRIEVER_K
from core.embeddings import get_embeddings


def _get_chroma(collection_name: str) -> Chroma:
    """Return a Chroma vectorstore for a specific named collection."""
    os.makedirs(CHROMA_DIR, exist_ok=True)
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_DIR
    )


def add_to_vectorstore(chunks: list[Document], collection_name: str) -> None:
    """Embed and add document chunks to a named ChromaDB collection."""
    vectorstore = _get_chroma(collection_name)
    vectorstore.add_documents(chunks)
    total = vectorstore._collection.count()
    print(f"[vectorstore] [{collection_name}] Added {len(chunks)} chunks. Total: {total}")


def load_vectorstore(collection_name: str) -> Chroma:
    """Load a named ChromaDB collection. Raises FileNotFoundError if empty."""
    vectorstore = _get_chroma(collection_name)
    count = vectorstore._collection.count()
    if count == 0:
        raise FileNotFoundError(
            "Knowledge base is empty. Please ingest at least one document or note first."
        )
    print(f"[vectorstore] [{collection_name}] Loaded — {count} chunks available.")
    return vectorstore


def get_retriever(collection_name: str):
    """Return a retriever from a named ChromaDB collection."""
    vectorstore = load_vectorstore(collection_name)
    return vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})


def list_documents(collection_name: str) -> list[dict]:
    """Return unique sources in a named collection."""
    try:
        vectorstore = load_vectorstore(collection_name)
    except FileNotFoundError:
        return []
    result = vectorstore._collection.get(include=["metadatas"])
    metadatas = result.get("metadatas") or []
    seen = set()
    documents = []
    for meta in metadatas:
        source = meta.get("source", "unknown")
        if source not in seen:
            seen.add(source)
            documents.append({"source": source, "page": meta.get("page", 0)})
    return documents