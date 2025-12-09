"""Document processing and ingestion service."""
import os
from typing import List, Optional
from pathlib import Path
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from ..core.llm import LLMClient
from ..core.vectorstore import VectorStoreManager
from ..core.ocr import OCRProcessor
from ..core.pdf_processor import PDFProcessor
from ..config import Settings
from ..utils.logger import get_logger
from .invoice_extractor import InvoiceExtractor, InvoiceData  # <-- ADD THIS

logger = get_logger()


class DocumentService:
    """Service for document processing and ingestion."""

    def __init__(
        self,
        settings: Settings,
        vectorstore: VectorStoreManager,
        ocr_processor: OCRProcessor,
        pdf_processor: PDFProcessor,
        llm_client: LLMClient,
        db: AsyncSession,
        invoice_extractor: Optional[InvoiceExtractor] = None,
    ):
        """
        Initialize document service.

        Args:
            settings: Application settings
            vectorstore: Vector store manager
            ocr_processor: OCR processor
            pdf_processor: PDF processor
        """
        self.settings = settings
        self.vectorstore = vectorstore
        self.ocr_processor = ocr_processor
        self.pdf_processor = pdf_processor
        self.llm_client = llm_client
        self.db = db  # <-- STORE DB SESSION
        self.invoice_extractor = InvoiceExtractor(llm_client, settings)
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
        )
    
    def _is_invoice(self, text: str) -> bool:
        keywords = ["invoice", "bill", "total", "amount due", "tax", "invoice no", "invoice #"]
        text_lower = text.lower()
        return sum(1 for kw in keywords if kw in text_lower) >= 2

    async def process_file(self, file_path: str, use_ocr: bool = False,user_id: Optional[uuid.UUID] = None) -> int:
        """Process file: extract invoice if detected, AND add to vector store."""
        logger.info(f"📂 Processing file: {file_path} (OCR: {use_ocr})")
        
        file_ext = Path(file_path).suffix.lower()
        documents: List[Document] = []

        try:
            if file_ext == ".pdf":
                # ✅ Use PDFProcessor for ALL PDFs (it handles OCR internally)
                documents = self.pdf_processor.process_pdf_to_documents(
                    pdf_path=file_path,
                    use_ocr=use_ocr
                )
            elif file_ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
                # ✅ Use OCRProcessor for images
                doc = self.ocr_processor.process_image_to_document(image_path=file_path)
                documents = [doc]
            else:
                logger.warning(f"Unsupported file type: {file_ext}")
                return 0

            if not documents:
                logger.warning("No content extracted from file")
                return 0

            # Get full text for invoice detection
            full_text = "\n\n".join([doc.page_content for doc in documents])
            logger.info(f"📄 Full text preview: {full_text[:80]}...")
            # === INVOICE EXTRACTION ===
            if self._is_invoice(full_text):
                logger.info("✅ File detected as invoice")
                logger.info(f"Processing invoice now to databas")
                try:
                    invoice_data = self.invoice_extractor.extract(full_text)
                    logger.info(f"Pushing invoice now into databas")
                    await self.invoice_extractor.save_to_db(self.db, invoice_data, file_path,user_id=user_id )
                except Exception as e:
                    logger.warning(f"⚠️ Invoice extraction failed: {e}")
            
            logger.info(f"Not invoice henc skipping database commit")
            # === VECTOR STORE INDEXING (RAG) ===
            chunks_added = self.process_documents(documents)
            return chunks_added

        except Exception as e:
            logger.error(f"❌ File processing failed: {str(e)}")
            raise

    def add_texts(self, texts: List[str], metadatas: List[dict] = None) -> int:
        """
        Add texts directly to vector store.

        Args:
            texts: List of texts to add
            metadatas: Optional metadata for each text

        Returns:
            Number of texts added
        """
        logger.info(f"📝 Adding {len(texts)} texts to knowledge base")

        try:
            self.vectorstore.add_texts(texts, metadatas=metadatas)
            logger.success(f"✅ Successfully added {len(texts)} texts")
            return len(texts)

        except Exception as e:
            logger.error(f"❌ Failed to add texts: {str(e)}")
            raise

    def process_documents(self, documents: List[Document]) -> int:
        """
        Process and add documents to vector store.

        Args:
            documents: List of documents to process

        Returns:
            Number of chunks added
        """
        logger.info(f"📄 Processing {len(documents)} documents")

        try:
            # Split documents into chunks
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"✂️ Split into {len(chunks)} chunks")

            # Add to vector store
            self.vectorstore.add_documents(chunks)
            logger.success(f"✅ Processed {len(documents)} documents ({len(chunks)} chunks)")

            return len(chunks)

        except Exception as e:
            logger.error(f"❌ Failed to process documents: {str(e)}")
            raise


    def process_directory(self, directory_path: str) -> int:
        """
        Process all supported files in a directory.

        Args:
            directory_path: Path to directory

        Returns:
            Total number of chunks added
        """
        logger.info(f"📂 Processing directory: {directory_path}")

        try:
            # Process all images with OCR
            documents = self.ocr_processor.process_directory(directory_path)

            if not documents:
                logger.warning("No documents found to process")
                return 0

            # Add to vector store
            chunks_added = self.process_documents(documents)

            logger.success(f"✅ Processed directory: {len(documents)} docs, {chunks_added} chunks")
            return chunks_added

        except Exception as e:
            logger.error(f"❌ Failed to process directory {directory_path}: {str(e)}")
            raise

    def clear_vectorstore(self) -> None:
        """Clear all data from vector store."""
        self.vectorstore.clear()
