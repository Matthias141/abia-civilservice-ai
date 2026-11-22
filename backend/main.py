"""
AbiaCS Assistant — Backend Server
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FastAPI server with RAG pipeline for Abia State Civil Service chatbot.

Usage: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import os
import re
import secrets
import shutil
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path, PureWindowsPath
from tempfile import TemporaryDirectory
from typing import BinaryIO

import anthropic
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from multipart.exceptions import MultipartParseError
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.datastructures import UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser

from config import (
    ADMIN_TOKEN,
    ANTHROPIC_API_KEY,
    CHROMA_DIR,
    CLAUDE_MODEL,
    DOCUMENTS_DIR,
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
admin_bearer = HTTPBearer(auto_error=False)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MULTIPART_OVERHEAD_BYTES = 64 * 1024


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
async def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(admin_bearer),
):
    if not ADMIN_TOKEN.strip():
        raise HTTPException(503, "Document administration is disabled.")
    if credentials is None or not secrets.compare_digest(
        credentials.credentials.encode(), ADMIN_TOKEN.encode()
    ):
        raise HTTPException(401, "Admin token required.", headers={"WWW-Authenticate": "Bearer"})


class UploadTooLarge(MultiPartException):
    pass


async def bounded_upload_stream(request: Request) -> AsyncGenerator[bytes, None]:
    received = 0
    async for chunk in request.stream():
        received += len(chunk)
        if received > MAX_UPLOAD_BYTES + MULTIPART_OVERHEAD_BYTES:
            raise UploadTooLarge("Multipart upload exceeds the size limit.")
        yield chunk


def safe_pdf_filename(filename: str | None) -> str:
    if not filename or not filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted.")
    stem = filename[:-4]
    if (
        len(filename.encode()) > 240
        or not re.fullmatch(r"[\w-][\w. ()-]*", stem)
        or PureWindowsPath(filename).is_reserved()
    ):
        raise HTTPException(400, "Invalid PDF filename.")
    return f"{stem}.pdf"


def save_pdf(filename: str, source: BinaryIO):
    documents_dir = Path(DOCUMENTS_DIR)
    documents_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=documents_dir, prefix=".upload-") as staging_dir:
        staged = Path(staging_dir) / "document"
        with staged.open("wb") as target:
            shutil.copyfileobj(source, target)
        # Publish only the complete file, without following or replacing an existing entry.
        os.link(staged, documents_dir / filename)


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


@app.post("/api/ingest", dependencies=[Depends(require_admin)])
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


@app.post(
    "/api/upload",
    dependencies=[Depends(require_admin)],
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["file"],
                        "properties": {"file": {"type": "string", "format": "binary"}},
                    },
                },
            },
        },
    },
)
@limiter.limit("5/minute")
async def upload_document(request: Request):
    """Upload a PDF document and trigger re-ingestion."""
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "multipart/form-data":
        raise HTTPException(400, "Expected a multipart PDF upload.")
    try:
        form = await MultiPartParser(
            request.headers, bounded_upload_stream(request), max_files=1, max_fields=0
        ).parse()
    except UploadTooLarge as exc:
        raise HTTPException(413, "PDF upload exceeds the size limit.") from exc
    except (MultiPartException, MultipartParseError) as exc:
        raise HTTPException(400, "Invalid multipart upload.") from exc

    try:
        file = form.get("file")
        if not isinstance(file, UploadFile):
            raise HTTPException(400, "A PDF file is required.")
        filename = safe_pdf_filename(file.filename)
        if file.size is None or file.size > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "PDF upload exceeds the size limit.")
        try:
            await run_in_threadpool(save_pdf, filename, file.file)
        except FileExistsError as exc:
            raise HTTPException(409, "A document with this filename already exists.") from exc
    finally:
        await form.close()

    # Re-ingest all documents
    indexed = False
    try:
        from ingest import ingest
        ingest()
        indexed = True
        load_vector_store()
        count = vector_store._collection.count() if vector_store else 0
        return {
            "status": "success",
            "filename": filename,
            "chunks_loaded": count,
        }
    except Exception as e:
        if not indexed:
            (Path(DOCUMENTS_DIR) / filename).unlink(missing_ok=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Could not complete upload and indexing: {str(e)}"},
        )


@app.get("/api/documents")
async def list_documents():
    """List all PDF documents in the knowledge base."""
    if not os.path.exists(DOCUMENTS_DIR):
        return {"documents": []}
    pdfs = [f for f in os.listdir(DOCUMENTS_DIR) if f.lower().endswith(".pdf")]
    return {"documents": sorted(pdfs)}


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
