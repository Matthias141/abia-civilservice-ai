# AbiaCS Assistant — Development Guide

## Project Overview
AI-powered chatbot for Abia State Civil Service using RAG (Retrieval-Augmented Generation).

## Architecture
- **Frontend**: Next.js 14 + React 18 + Tailwind CSS (`frontend/`)
- **Backend**: Python 3.11 + FastAPI (`backend/`)
- **AI Model**: Claude Sonnet via Anthropic API
- **Embeddings**: HuggingFace all-MiniLM-L6-v2
- **Vector DB**: ChromaDB

## Quick Start
```bash
# Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your ANTHROPIC_API_KEY
python ingest.py      # Process documents
uvicorn main:app --reload

# Frontend
cd frontend && npm install
cp .env.example .env.local
npm run dev
```

## Key Files
- `backend/main.py` — FastAPI server, RAG pipeline, API routes
- `backend/ingest.py` — PDF ingestion into ChromaDB
- `backend/config.py` — All configuration and system prompt
- `frontend/src/app/page.tsx` — Main chat page
- `frontend/src/lib/api.ts` — API client

## API Endpoints
- `POST /api/chat` — Send message, get AI response
- `GET /health` — Health check
- `POST /api/ingest` — Re-ingest documents
- `GET /api/suggested-questions` — Get suggested questions
