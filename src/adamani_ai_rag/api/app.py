"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine

from ..config import get_settings
from ..utils.logger import setup_logger, get_logger
from ..database.base import Base
from ..database.models import User, Organization, OrganizationMember, Document
from .routes import health, chat, documents, auth, invoices

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
    expose_headers=["*"],
    max_age=3600,
)

# Log CORS configuration for debugging
logger.info(f"🌐 CORS enabled for origins: {settings.cors_origins_list}")

# Include routers
app.include_router(health.router)
app.include_router(auth.router)  # Authentication routes
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(invoices.router, prefix="/api")  # ← Add this line


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    # Create database tables if they don't exist
    try:
        logger.info("🗄️  Initializing database tables...")
        engine = create_async_engine(settings.database_url)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.success("✅ Database tables initialized!")

        # Log existing tables for verification
        async with engine.connect() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
            tables = [row[0] for row in result]
            logger.info(f"📊 Database tables: {', '.join(tables)}")

        await engine.dispose()
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        # Don't fail startup if tables already exist or minor issues
        logger.warning("⚠️  Continuing startup despite database initialization error")

    logger.success("✅ Application startup complete!")
    logger.info(f"📚 API Documentation: http://{settings.api_host}:{settings.api_port}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.warning("🛑 Application shutting down...")
