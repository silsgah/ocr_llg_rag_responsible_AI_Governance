"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import get_settings
from ..utils.logger import setup_logger, get_logger
from .routes import health, chat, documents, auth

# Setup logging
settings = get_settings()
setup_logger(settings.log_level)
logger = get_logger()

# Log startup
logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
logger.info(f"📝 LLM Model: {settings.ollama_model}")
logger.info(f"🔤 Embedding Model: {settings.embedding_model}")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="A modular AI automation backend with local LLM, RAG, memory, and OCR processing",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log CORS configuration for debugging
logger.info(f"🌐 CORS enabled for origins: {settings.cors_origins_list}")

# Include routers
app.include_router(health.router)
app.include_router(auth.router)  # Authentication routes
app.include_router(chat.router)
app.include_router(documents.router)


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.success("✅ Application startup complete!")
    logger.info(f"📚 API Documentation: http://{settings.api_host}:{settings.api_port}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.warning("🛑 Application shutting down...")
