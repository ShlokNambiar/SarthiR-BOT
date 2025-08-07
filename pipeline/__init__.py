"""
RAG Pipeline Package

This package contains all the components for the RAG (Retrieval-Augmented Generation) pipeline:
- PDF text extraction
- Text chunking
- Embeddings generation
- Pinecone vector database operations
- Query interface
"""

__version__ = "1.0.0"
__author__ = "UDCPR RAG Team"

# Import main pipeline functions for easy access
from .pdf_extractor import extract_text_from_pdf
from .text_chunker import chunk_text
from .embeddings_generator import generate_embeddings
from .pinecone_uploader import upload_to_pinecone
from .query_interface import search_pinecone, query_rag_system

__all__ = [
    "extract_text_from_pdf",
    "chunk_text", 
    "generate_embeddings",
    "upload_to_pinecone",
    "search_pinecone",
    "query_rag_system"
]