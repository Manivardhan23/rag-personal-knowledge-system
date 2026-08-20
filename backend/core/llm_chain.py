import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import RateLimitError
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import GROQ_PRIMARY_MODEL, GROQ_FALLBACK_MODEL

SYSTEM_PROMPT = """You are a helpful personal knowledge assistant.
Answer the question using the context provided below.
You may reason, compute (e.g. calculate age from a date of birth using today's date), and give recommendations or prioritisation advice based on what is in the context.
If the answer cannot be reasonably derived from the context, say "I don't have enough information in my knowledge base to answer this."
Give clean, natural, conversational answers. Do NOT mention source names, document names, or note titles inside the answer — sources are shown separately.

System facts (always accurate, use freely):
Today's date: {today}

Context from your knowledge base:
{context}

Question:
{question}

Answer:"""


def _call_groq(model_name: str, context: str, question: str, today: str, api_key: str) -> str:
    """Call Groq with a specific model and API key."""
    llm = ChatGroq(
        model=model_name,
        api_key=api_key,
        temperature=0.2
    )
    prompt = PromptTemplate(
        input_variables=["context", "question", "today"],
        template=SYSTEM_PROMPT
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context": context, "question": question, "today": today})


def get_answer_from_groq(context: str, question: str, today: str, api_key: str) -> str:
    """
    Call Groq with the caller's API key, trying 70B first.
    Automatically falls back to 20B if rate limit is hit.
    """
    try:
        print(f"[llm_chain] Using primary model: {GROQ_PRIMARY_MODEL}")
        return _call_groq(GROQ_PRIMARY_MODEL, context, question, today, api_key)
    except RateLimitError:
        print(f"[llm_chain] Rate limit hit on {GROQ_PRIMARY_MODEL}, switching to fallback: {GROQ_FALLBACK_MODEL}")
        return _call_groq(GROQ_FALLBACK_MODEL, context, question, today, api_key)


def ask_question(retriever, question: str, api_key: str, chat_history: list = []):
    """Retrieve relevant docs and generate answer using the caller's API key."""

    today = datetime.now().strftime("%A, %d %B %Y")
    source_docs = retriever.invoke(question)
    context = "\n\n".join([doc.page_content for doc in source_docs])
    answer = get_answer_from_groq(context, question, today, api_key)

    sources = []
    seen = set()
    for doc in source_docs:
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", 0)
        preview = doc.page_content[:150].strip()
        key = f"{source}-{page}"
        if key not in seen:
            seen.add(key)
            sources.append({"source": source, "page": page, "preview": preview})

    return answer, sources