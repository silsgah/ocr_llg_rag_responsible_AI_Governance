"""Application configuration and settings."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Adamani AI RAG"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # LLM Configuration
    llm_provider: str = "ollama"  # ollama, openai, anthropic

    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # OpenAI settings
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Anthropic settings
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    # General LLM settings
    llm_temperature: float = 0.1
    llm_timeout: int = 120

    # Embedding Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"

    # Vector Store Configuration
    vector_store_type: str = "chroma"  # chroma, faiss
    vectordb_path: str = "./data/vectorstore"

    # RAG Configuration
    retrieval_top_k: int = 3
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Memory Configuration
    memory_type: str = "buffer"  # buffer, summary, etc.
    max_memory_tokens: int = 2000

    # OCR Configuration
    ocr_engine: str = "tesseract"  # tesseract, easyocr, paddleocr
    ocr_languages: str = "eng"
    supported_doc_formats: list = [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = int(os.getenv("PORT", "8000"))  # Use PORT from Render or default to 8000
    cors_origins: str = "http://localhost:3000,http://localhost:8080,https://adamani-ai-rag-frontend.onrender.com"

    # Storage
    upload_dir: str = "./data/uploads"
    processed_dir: str = "./data/processed"

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/adamani_rag"

    # JWT/Auth
    jwt_secret_key: str = "change-this-to-a-random-secret-key-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_seconds: int = 604800  # 7 days

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Convert postgres:// to postgresql+asyncpg:// for Render compatibility
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif self.database_url.startswith("postgresql://") and "asyncpg" not in self.database_url:
            self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if isinstance(self.cors_origins, list):
            return self.cors_origins
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
