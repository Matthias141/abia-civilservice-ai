"""
Configuration and Settings
━━━━━━━━━━━━━━━━━━━━━━━━━
Loads environment variables and provides app-wide configuration.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1500"))

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# CORS
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Rate limiting
RATE_LIMIT = os.getenv("RATE_LIMIT", "20/minute")

# Paths
DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", "./documents")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")

# Embedding model
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# RAG settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))

# System prompt for the AI assistant
SYSTEM_PROMPT = """You are AbiaCS Assistant, an AI-powered chatbot for the Abia State Civil Service.
Your role is to provide accurate, helpful answers about Abia State Civil Service rules, regulations,
procedures, and policies.

RULES:
1. ONLY answer questions based on the provided document context. If the context doesn't contain
   relevant information, say so honestly.
2. Always cite your sources by referencing the document name and section when possible.
3. Be professional, clear, and concise.
4. If a question is outside the scope of civil service matters, politely redirect the user.
5. If the user writes in Igbo, respond in Igbo. If in Pidgin English, respond in Pidgin English.
   Always maintain accuracy regardless of language.
6. Format your responses with clear structure — use numbered lists, bullet points, and bold text
   where appropriate to improve readability.
7. When quoting specific rules or regulations, use the exact wording from the documents.
8. If a question requires interpretation of rules, provide the relevant rule text first,
   then your interpretation clearly labeled as such.

CONTEXT FROM CIVIL SERVICE DOCUMENTS:
{context}

Answer the user's question based on the above context. If the context doesn't contain enough
information to fully answer, state what you can confirm from the documents and what would need
further verification from the appropriate authority."""
