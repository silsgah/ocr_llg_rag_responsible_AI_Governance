"""Vector store management with support for multiple backends."""
import os
from typing import Optional, List, Union
from langchain_community.vectorstores import FAISS, Chroma
from langchain_core.documents import Document
from ..config import Settings
from .embeddings import EmbeddingManager
from ..utils.logger import get_logger

logger = get_logger()


class VectorStoreManager:
    """Manages vector store operations with support for FAISS and ChromaDB."""

    def __init__(self, settings: Settings, embedding_manager: EmbeddingManager):
        """
        Initialize vector store manager.

        Args:
            settings: Application settings
            embedding_manager: Embedding manager instance
        """
        # self.settings = settings
        # self.embedding_manager = embedding_manager
        # self._store: Optional[Union[FAISS, Chroma]] = None
        self.settings = settings
        self.embedding_manager = embedding_manager
        self._store: Optional[Union[FAISS, Chroma]] = None
        self._chroma_needs_reload = True  # ✅ Track staleness

    # def get_store(self) -> Union[FAISS, Chroma]:
    #     """
    #     Get or create vector store instance.

    #     Returns:
    #         Initialized vector store (FAISS or ChromaDB)
    #     """
    #     if self._store is None:
    #         logger.info(f"🗄️ Initializing {self.settings.vector_store_type.upper()} vector store...")
    #         embeddings = self.embedding_manager.get_embeddings()

    #         if self.settings.vector_store_type.lower() == "chroma":
    #             self._store = self._init_chroma(embeddings)
    #         else:  # Default to FAISS
    #             self._store = self._init_faiss(embeddings)

    #     return self._store
    # def get_store(self) -> Union[FAISS, Chroma]:
    #     """Get FRESH vector store instance every time (no caching for Chroma)."""
    #     logger.info(f"🗄️ Initializing {self.settings.vector_store_type.upper()} vector store...")
    #     embeddings = self.embedding_manager.get_embeddings()

    #     if self.settings.vector_store_type.lower() == "chroma":
    #         # ✅ ALWAYS load fresh from disk (no caching)
    #         return self._init_chroma(embeddings)
    #     else:
    #         # FAISS: keep caching (since it's in-memory only)
    #         if self._store is None:
    #             self._store = self._init_faiss(embeddings)
    #         return self._store
    def get_store(self) -> Union[FAISS, Chroma]:
        """Get or create vector store instance with smart caching."""
        embeddings = self.embedding_manager.get_embeddings()

        if self.settings.vector_store_type.lower() == "chroma":
            # ✅ Only reload if marked stale OR never loaded
            if self._store is None or self._chroma_needs_reload:
                logger.info("🔄 Loading ChromaDB from disk...")
                self._store = self._init_chroma(embeddings)
                self._chroma_needs_reload = False  # Mark as fresh
            return self._store
        else:
            # FAISS: keep existing logic
            if self._store is None:
                self._store = self._init_faiss(embeddings)
            return self._store

    # def refresh_store(self):
    #     """Reload store from disk (for Chroma only)."""
    #     if self.settings.vector_store_type.lower() == "chroma":
    #         self._store = None  # Force reload on next get_store()      
    
    def refresh_store(self):
        """Force reload on next access."""
        if self.settings.vector_store_type.lower() == "chroma":
            self._chroma_needs_reload = True
            logger.debug("🔄 ChromaDB marked for reload")

    def _init_chroma(self, embeddings) -> Chroma:
        """Initialize ChromaDB vector store."""
        persist_directory = self.settings.vectordb_path

        # Try to load existing collection
        if os.path.exists(persist_directory):
            try:
                logger.info(f"Loading existing ChromaDB from {persist_directory}")
                store = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=embeddings,
                    collection_name="adamani_ai_rag",
                )
                logger.success(f"✅ Loaded existing ChromaDB from {persist_directory}")
                return store
            except Exception as e:
                logger.warning(f"Failed to load existing ChromaDB: {e}. Creating new one.")

        # Create new ChromaDB
        logger.info("Creating new ChromaDB collection...")
        os.makedirs(persist_directory, exist_ok=True)

        store = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
            collection_name="adamani_ai_rag",
        )

        # Add initial document
        store.add_texts(
            texts=["This is an empty knowledge base. Add documents to populate it."],
            metadatas=[{"source": "system", "type": "init"}],
        )

        logger.success("✅ New ChromaDB collection created")
        return store

    def _init_faiss(self, embeddings) -> FAISS:
        """Initialize FAISS vector store."""
        persist_directory = self.settings.vectordb_path

        # Try to load existing store
        if os.path.exists(persist_directory):
            try:
                logger.info(f"Loading existing FAISS from {persist_directory}")
                store = FAISS.load_local(
                    persist_directory,
                    embeddings,
                    allow_dangerous_deserialization=True,
                )
                logger.success(f"✅ Loaded existing FAISS from {persist_directory}")
                return store
            except Exception as e:
                logger.warning(f"Failed to load existing FAISS: {e}. Creating new one.")

        # Create new FAISS store
        logger.info("Creating new FAISS vector store...")
        store = FAISS.from_texts(
            texts=["This is an empty knowledge base. Add documents to populate it."],
            embedding=embeddings,
        )
        logger.success("✅ New FAISS vector store created")
        return store

    # def add_documents(self, documents: List[Document]) -> None:
    #     """
    #     Add documents to vector store.

    #     Args:
    #         documents: List of documents to add
    #     """
    #     store = self.get_store()
    #     logger.info(f"📄 Adding {len(documents)} documents to vector store")
    #     store.add_documents(documents)
    #     self.refresh_store()  # ✅ Invalidate cache

    #     # Auto-persist for ChromaDB
    #     if isinstance(store, Chroma):
    #         store.persist()
    #         logger.debug("💾 ChromaDB persisted")

    #     logger.success(f"✅ Added {len(documents)} documents")
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to vector store."""
        store = self.get_store()
        logger.info(f"📄 Adding {len(documents)} documents to vector store")
        store.add_documents(documents)

        # Persist and mark for reload
        if isinstance(store, Chroma):
            store.persist()
            logger.debug("💾 ChromaDB persisted")
            self._chroma_needs_reload = True  # ✅ Mark stale
            logger.debug("🔄 Cache invalidated - next query will reload")

        logger.success(f"✅ Added {len(documents)} documents")

    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        """
        Add texts to vector store.

        Args:
            texts: List of texts to add
            metadatas: Optional metadata for each text
        """
        store = self.get_store()
        logger.info(f"📝 Adding {len(texts)} texts to vector store")
        store.add_texts(texts, metadatas=metadatas)

        # Auto-persist for ChromaDB
        if isinstance(store, Chroma):
            store.persist()
            logger.debug("💾 ChromaDB persisted")

        logger.success(f"✅ Added {len(texts)} texts")

    def similarity_search(self, query: str, k: int = None) -> List[Document]:
        """
        Search for similar documents.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of similar documents
        """
        store = self.get_store()
        k = k or self.settings.retrieval_top_k
        logger.debug(f"🔍 Searching for: {query[:50]}... (k={k})")
        results = store.similarity_search(query, k=k)
        logger.debug(f"Found {len(results)} results")
        return results

    def save(self) -> None:
        """Save vector store to disk."""
        if self._store is None:
            logger.warning("No vector store to save")
            return

        persist_directory = self.settings.vectordb_path
        os.makedirs(os.path.dirname(persist_directory), exist_ok=True)

        if isinstance(self._store, Chroma):
            self._store.persist()
            logger.success(f"💾 ChromaDB persisted to {persist_directory}")
        elif isinstance(self._store, FAISS):
            self._store.save_local(persist_directory)
            logger.success(f"💾 FAISS saved to {persist_directory}")

    def clear(self) -> None:
        """Clear the vector store."""
        logger.warning("🗑️ Clearing vector store...")
        self._store = None
        logger.success("✅ Vector store cleared")
