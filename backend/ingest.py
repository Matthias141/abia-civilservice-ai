"""
Document Ingestion Script
━━━━━━━━━━━━━━━━━━━━━━━━
Run this script whenever you add new PDF documents.
It reads all PDFs, splits them into searchable chunks,
and stores them in the vector database.

Usage: python ingest.py
"""

import os
import shutil

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from config import CHROMA_DIR, CHUNK_OVERLAP, CHUNK_SIZE, DOCUMENTS_DIR, EMBEDDING_MODEL


def ingest():
    """Process all PDFs in the documents directory and store in vector DB."""
    # Check if documents exist
    if not os.path.exists(DOCUMENTS_DIR):
        os.makedirs(DOCUMENTS_DIR)
        print("No documents folder found. Created one at ./documents/")
        print("Add your civil service PDFs there and run this script again.")
        return

    pdf_files = [f for f in os.listdir(DOCUMENTS_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        print("No PDF files found in ./documents/")
        print("Add your civil service PDFs and run again.")
        return

    print(f"Found {len(pdf_files)} PDF files:")
    for f in pdf_files:
        print(f"  - {f}")

    # Step 1: Load all PDFs
    print("\nLoading documents...")
    loader = DirectoryLoader(
        DOCUMENTS_DIR,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True,
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} pages from {len(pdf_files)} PDFs")

    # Step 2: Split into chunks
    print("\nSplitting into searchable chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} text chunks")

    # Step 3: Create embeddings and store in vector DB
    print("\nCreating embeddings (this may take a few minutes on first run)...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    # Remove old database if it exists
    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)
        print("Cleared old vector database")

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
    )

    print(f"\nSUCCESS! Ingested {len(chunks)} chunks into vector database")
    print(f"Database stored at: {CHROMA_DIR}")
    print(f"\nYou can now start the server with: uvicorn main:app --reload")


if __name__ == "__main__":
    ingest()
