import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config import CHUNK_SIZE, CHUNK_OVERLAP


def get_text_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""]
    )


def ingest_document(file_path: str) -> list[Document]:
    """Load a PDF or TXT file and split into chunks."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}. Only PDF and TXT are allowed.")

    documents = loader.load()
    splitter = get_text_splitter()
    chunks = splitter.split_documents(documents)

    print(f"[ingestion] {os.path.basename(file_path)} → {len(chunks)} chunks")
    return chunks


def ingest_note(title: str, content: str) -> list[Document]:
    """Wrap a plain text note into Document chunks."""
    document = Document(
        page_content=content,
        metadata={
            "source": "user_note",
            "title": title,
            "page": 0
        }
    )

    splitter = get_text_splitter()
    chunks = splitter.split_documents([document])

    print(f"[ingestion] Note '{title}' → {len(chunks)} chunks")
    return chunks