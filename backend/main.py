"""
AbiaCS Assistant — Backend Server
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FastAPI server with RAG pipeline for Abia State Civil Service chatbot.

Usage: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import os
import re
import uuid
from contextlib import asynccontextmanager

import anthropic
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config import (
    ANTHROPIC_API_KEY,
    CHROMA_DIR,
    CLAUDE_MODEL,
    EMBEDDING_MODEL,
    FRONTEND_URL,
    MAX_TOKENS,
    RATE_LIMIT,
    SYSTEM_PROMPT,
    TOP_K_RESULTS,
)

# --- Globals ---
vector_store = None
client = None


def load_vector_store():
    """Load the ChromaDB vector store from disk."""
    global vector_store
    if os.path.exists(CHROMA_DIR):
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        vector_store = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings,
        )
        count = vector_store._collection.count()
        print(f"Loaded {count} document chunks into vector store")
    else:
        print("Warning: No vector database found. Run 'python ingest.py' first.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global client
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    load_vector_store()
    yield


# --- App setup ---
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="AbiaCS Assistant API",
    description="AI-powered chatbot for Abia State Civil Service",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter

# CORS
allowed_origins = [FRONTEND_URL]
if FRONTEND_URL != "http://localhost:3000":
    allowed_origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limit error handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded. Please wait a moment and try again."},
    )


# --- Models ---
class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    sources: list[str]
    conversation_id: str


# --- Helper functions ---
def sanitize_input(text: str) -> str:
    """Basic input sanitization."""
    text = text.strip()
    # Remove potential prompt injection patterns
    text = re.sub(r"<\|.*?\|>", "", text)
    # Limit length
    if len(text) > 2000:
        text = text[:2000]
    return text


def search_documents(query: str) -> tuple[str, list[str]]:
    """Search the vector store for relevant document chunks."""
    if vector_store is None:
        return "", []

    results = vector_store.similarity_search(query, k=TOP_K_RESULTS)

    if not results:
        return "", []

    context_parts = []
    sources = set()
    for doc in results:
        context_parts.append(doc.page_content)
        source = doc.metadata.get("source", "Unknown document")
        # Extract just the filename
        source = os.path.basename(source)
        sources.add(source)

    context = "\n\n---\n\n".join(context_parts)
    return context, list(sources)


def get_ai_response(message: str, context: str) -> str:
    """Get a response from Claude using the RAG context."""
    prompt_with_context = SYSTEM_PROMPT.format(context=context if context else "No relevant documents found.")

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        system=prompt_with_context,
        messages=[{"role": "user", "content": message}],
    )

    return response.content[0].text


# --- Routes ---
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    documents_loaded = vector_store is not None and vector_store._collection.count() > 0
    return {
        "status": "ok",
        "documents_loaded": documents_loaded,
        "chunk_count": vector_store._collection.count() if vector_store else 0,
    }


@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit(RATE_LIMIT)
async def chat(request: Request, chat_request: ChatRequest):
    """Main chat endpoint — receives a question and returns an AI-generated answer."""
    message = sanitize_input(chat_request.message)

    if not message:
        return JSONResponse(
            status_code=400,
            content={"error": "Message cannot be empty."},
        )

    conversation_id = chat_request.conversation_id or str(uuid.uuid4())

    # RAG pipeline
    context, sources = search_documents(message)
    response_text = get_ai_response(message, context)

    return ChatResponse(
        response=response_text,
        sources=sources,
        conversation_id=conversation_id,
    )


@app.post("/api/ingest")
@limiter.limit("2/minute")
async def trigger_ingest(request: Request):
    """Trigger document re-ingestion without restarting the server."""
    try:
        from ingest import ingest
        ingest()
        load_vector_store()
        count = vector_store._collection.count() if vector_store else 0
        return {"status": "success", "chunks_loaded": count}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Ingestion failed: {str(e)}"},
        )


@app.get("/api/suggested-questions")
async def suggested_questions():
    """Return a list of suggested questions for the UI."""
    return {
        "questions": [
            "How do I apply for annual leave?",
            "What are the requirements for promotion from GL 08 to GL 09?",
            "How is pension calculated under the Contributory Pension Scheme?",
            "What is the disciplinary procedure for a civil servant?",
            "What are the salary grade levels in the civil service?",
            "How do I apply for study leave with pay?",
            "What are the functions of the Civil Service Commission?",
            "What is the probation period for new civil servants?",
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
