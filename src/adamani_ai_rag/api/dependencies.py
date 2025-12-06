"""Dependency injection for FastAPI."""
from functools import lru_cache
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from ..config import get_settings, Settings
from ..core.llm import LLMClient
from ..core.embeddings import EmbeddingManager
from ..core.vectorstore import VectorStoreManager
from ..core.memory import MemoryManager
from ..core.ocr import OCRProcessor
from ..core.pdf_processor import PDFProcessor
from ..services.rag_service import RAGService
from ..services.document_service import DocumentService
from ..database.session import async_session_maker

# Singleton instances
_llm_client = None
_embedding_manager = None
_vectorstore_manager = None
_memory_manager = None
_ocr_processor = None
_pdf_processor = None
_rag_service = None
_document_service = None


def get_llm_client() -> LLMClient:
    """Get LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        settings = get_settings()
        _llm_client = LLMClient(settings)
    return _llm_client


def get_embedding_manager() -> EmbeddingManager:
    """Get embedding manager singleton."""
    global _embedding_manager
    if _embedding_manager is None:
        settings = get_settings()
        _embedding_manager = EmbeddingManager(settings)
    return _embedding_manager


def get_vectorstore_manager() -> VectorStoreManager:
    """Get vector store manager singleton."""
    global _vectorstore_manager
    if _vectorstore_manager is None:
        settings = get_settings()
        embedding_manager = get_embedding_manager()
        _vectorstore_manager = VectorStoreManager(settings, embedding_manager)
    return _vectorstore_manager


def get_memory_manager() -> MemoryManager:
    """Get memory manager singleton."""
    global _memory_manager
    if _memory_manager is None:
        settings = get_settings()
        _memory_manager = MemoryManager(settings)
    return _memory_manager


def get_ocr_processor() -> OCRProcessor:
    """Get OCR processor singleton."""
    global _ocr_processor
    if _ocr_processor is None:
        settings = get_settings()
        _ocr_processor = OCRProcessor(settings)
    return _ocr_processor


def get_pdf_processor() -> PDFProcessor:
    """Get PDF processor singleton."""
    global _pdf_processor
    if _pdf_processor is None:
        settings = get_settings()
        _pdf_processor = PDFProcessor(settings)
    return _pdf_processor


def get_rag_service() -> RAGService:
    """Get RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        settings = get_settings()
        llm_client = get_llm_client()
        vectorstore = get_vectorstore_manager()
        memory = get_memory_manager()
        _rag_service = RAGService(settings, llm_client, vectorstore, memory)
    return _rag_service


async def get_db():
    async with async_session_maker() as session:
        yield session

async def get_document_service(
    db: AsyncSession = Depends(get_db),
) -> DocumentService:
    settings = get_settings()
    return DocumentService(
        settings=settings,
        vectorstore=get_vectorstore_manager(),
        ocr_processor=get_ocr_processor(),
        pdf_processor=get_pdf_processor(),
        llm_client=get_llm_client(),  
        db=db,
    )
