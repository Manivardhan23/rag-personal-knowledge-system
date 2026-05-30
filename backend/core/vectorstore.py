import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from config import FAISS_INDEX_DIR, RETRIEVER_K


def get_embeddings():
    """Initialize local embedding model — no API call needed."""
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )


def add_to_vectorstore(chunks: list[Document]) -> None:
    """Add document chunks to FAISS index, creating it if it doesn't exist."""
    embeddings = get_embeddings()

    if os.path.exists(FAISS_INDEX_DIR) and os.listdir(FAISS_INDEX_DIR):
        print("[vectorstore] Loading existing index...")
        vectorstore = FAISS.load_local(
            FAISS_INDEX_DIR,
            embeddings,
            allow_dangerous_deserialization=True
        )
        vectorstore.add_documents(chunks)
        print(f"[vectorstore] Added {len(chunks)} chunks to existing index")
    else:
        print("[vectorstore] Creating new index...")
        os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
        vectorstore = FAISS.from_documents(chunks, embeddings)
        print(f"[vectorstore] Created new index with {len(chunks)} chunks")

    vectorstore.save_local(FAISS_INDEX_DIR)
    print(f"[vectorstore] Index saved to {FAISS_INDEX_DIR}")


def load_vectorstore() -> FAISS:
    """Load the FAISS index from disk."""
    if not os.path.exists(FAISS_INDEX_DIR) or not os.listdir(FAISS_INDEX_DIR):
        raise FileNotFoundError(
            "No FAISS index found. Please ingest at least one document or note first."
        )

    embeddings = get_embeddings()
    vectorstore = FAISS.load_local(
        FAISS_INDEX_DIR,
        embeddings,
        allow_dangerous_deserialization=True
    )
    print("[vectorstore] Index loaded successfully")
    return vectorstore


def get_retriever():
    """Return a retriever from the loaded vectorstore."""
    vectorstore = load_vectorstore()
    return vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})