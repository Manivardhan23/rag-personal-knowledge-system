import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.generativeai as genai
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import (
    LLM_PROVIDER,
    GEMINI_API_KEY,
    GROQ_API_KEY,
    GEMINI_LLM_MODEL
)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are a helpful personal knowledge assistant.
Answer the question using ONLY the context provided below.
If the answer is not found in the context, say "I don't have enough information in my knowledge base to answer this."
Always be concise and accurate. Mention which document or note your answer came from.

Context:
{context}

Question:
{question}

Answer:"""


def get_answer_from_gemini(context: str, question: str) -> str:
    """Call Gemini directly using google-generativeai package."""
    model = genai.GenerativeModel(GEMINI_LLM_MODEL)
    prompt = SYSTEM_PROMPT.format(context=context, question=question)
    response = model.generate_content(prompt)
    return response.text


def get_answer_from_groq(context: str, question: str) -> str:
    """Call Groq using LangChain."""
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=GROQ_API_KEY,
        temperature=0.2
    )
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=SYSTEM_PROMPT
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context": context, "question": question})


def ask_question(retriever, question: str, chat_history: list = []):
    """Retrieve relevant docs and generate answer."""

    # Step 1 — retrieve relevant chunks
    source_docs = retriever.invoke(question)

    # Step 2 — format context from chunks
    context = "\n\n".join([doc.page_content for doc in source_docs])

    # Step 3 — generate answer
    if LLM_PROVIDER == "groq":
        print("[llm_chain] Using Groq LLM")
        answer = get_answer_from_groq(context, question)
    else:
        print("[llm_chain] Using Gemini LLM")
        answer = get_answer_from_gemini(context, question)

    # Step 4 — build sources list
    sources = []
    seen = set()
    for doc in source_docs:
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", 0)
        preview = doc.page_content[:150].strip()
        key = f"{source}-{page}"
        if key not in seen:
            seen.add(key)
            sources.append({
                "source": source,
                "page": page,
                "preview": preview
            })

    return answer, sources