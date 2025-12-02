
# Adamani AI RAG - Project Structure

A modular AI automation backend providing local LLM-powered RAG, memory-enabled conversational AI, and OCR-based document processing.

## Directory Structure

```
adamani_ai_rag/
├── src/adamani_ai_rag/
│   ├── core/                    # Core business logic modules
│   │   ├── llm.py              # LLM client management (Ollama)
│   │   ├── embeddings.py       # Embedding model management
│   │   ├── vectorstore.py      # Vector store operations (FAISS)
│   │   ├── memory.py           # Conversation memory management
│   │   └── ocr.py              # OCR processing (Tesseract)
│   │
│   ├── services/               # Service layer (business logic)
│   │   ├── rag_service.py      # RAG query processing
│   │   └── document_service.py # Document ingestion & processing
│   │
│   ├── api/                    # FastAPI application
│   │   ├── app.py             # Main FastAPI app initialization
│   │   ├── dependencies.py     # Dependency injection
│   │   ├── models/            # Pydantic models
│   │   │   ├── requests.py    # Request models
│   │   │   └── responses.py   # Response models
│   │   └── routes/            # API endpoints
│   │       ├── health.py      # Health check
│   │       ├── chat.py        # Chat/RAG endpoints
│   │       └── documents.py   # Document management
│   │
│   ├── config/                 # Configuration management
│   │   └── settings.py        # Application settings (env vars)
│   │
│   └── utils/                  # Utility modules
│       └── logger.py          # Logging configuration (Loguru)
│
├── data/                       # Data storage
│   ├── uploads/               # Uploaded files
│   ├── processed/             # Processed documents
│   └── vectorstore/           # Vector database files
│
├── pyproject.toml             # Project dependencies
├── Dockerfile                 # Docker configuration
└── .env                       # Environment variables (not in git)
```

## Module Responsibilities

### Core Layer
**Purpose**: Low-level integrations with external services and libraries

- **llm.py**: Manages Ollama LLM client, handles text generation
- **embeddings.py**: Manages HuggingFace embeddings for document vectorization
- **vectorstore.py**: Handles FAISS vector store operations (add, search, persist)
- **memory.py**: Manages conversation history per session
- **ocr.py**: Processes images with Tesseract OCR

### Service Layer
**Purpose**: Business logic that orchestrates core modules

- **rag_service.py**: Implements RAG pipeline (retrieve → augment → generate)
- **document_service.py**: Handles document ingestion, chunking, and indexing

### API Layer
**Purpose**: HTTP interface for external clients

- **app.py**: FastAPI application setup, middleware, route registration
- **dependencies.py**: Singleton instances for dependency injection
- **routes/**: REST API endpoints organized by feature
- **models/**: Request/response validation with Pydantic

### Config Layer
**Purpose**: Centralized configuration management

- **settings.py**: Environment-based settings using Pydantic BaseSettings

### Utils Layer
**Purpose**: Shared utilities

- **logger.py**: Beautiful logging with Loguru

## Key Features

### 1. RAG (Retrieval-Augmented Generation)
- Retrieve relevant documents from vector store
- Augment LLM prompt with retrieved context
- Generate contextual responses

### 2. Memory-Enabled Chat
- Per-session conversation history
- Context-aware responses
- History management (clear, view)

### 3. OCR Processing
- Extract text from images (PNG, JPG, TIFF, etc.)
- Automatic chunking and indexing
- Batch directory processing

### 4. Modular Architecture
- Clean separation of concerns
- Dependency injection for testability
- Easy to extend with new features

## API Endpoints

### Health
- `GET /health` - Service health check

### Chat
- `POST /chat/` - RAG-powered chat
- `DELETE /chat/memory/{session_id}` - Clear session memory
- `DELETE /chat/memory` - Clear all memories

### Documents
- `POST /documents/texts` - Add text documents
- `POST /documents/upload` - Upload & process files
- `POST /documents/process-directory` - Batch process directory
- `DELETE /documents/clear` - Clear knowledge base

## Configuration
# Full Stack Setup Guide

Complete guide to running the Adamani AI RAG application (Backend + Frontend).

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend API   │────▶│     Ollama      │
│  (Next.js)      │     │   (FastAPI)     │     │    (LLM)        │
│  Port 3000      │     │   Port 8080     │     │  Port 11434     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   ChromaDB      │
                        │ (Vector Store)  │
                        └─────────────────┘
```

## Quick Start (Docker Compose)

### 1. Start Everything
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Pull Ollama model (first time only)
docker exec -it adamani_ai_rag-ollama-1 ollama pull llama3
```

### 2. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **Ollama**: http://localhost:11434

### 3. Stop Everything
```bash
docker-compose down

# Remove volumes too (clean slate)
docker-compose down -v
```

## Manual Setup (Development)

### Prerequisites
- Python 3.10+
- Node.js 18+
- Ollama installed locally
- Tesseract OCR

### Backend Setup

```bash
# 1. Install dependencies
cd /path/to/adamani_ai_rag
poetry install

# 2. Start Ollama (separate terminal)
ollama serve

# 3. Pull model
ollama pull llama3

# 4. Start backend
uvicorn src.adamani_ai_rag.api.app:app --reload --host 0.0.0.0 --port 8080
```

### Frontend Setup

```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Configure environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8080" > .env.local

# 3. Start frontend
npm run dev
```

## Testing the Application

### 1. Upload a Document
```bash
curl -X POST http://localhost:8080/documents/upload \
  -F "file=@invoice.pdf" \
  -F "use_ocr=true"
```

### 2. Ask a Question
```bash
curl -X POST http://localhost:8080/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the total amount?",
    "session_id": "test_user"
  }'
```

## Configuration

### Backend Environment Variables

```bash
# LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
LLM_TEMPERATURE=0.1

# Vector Store
VECTOR_STORE_TYPE=chroma  # or faiss
VECTORDB_PATH=./data/vectorstore

# RAG
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVAL_TOP_K=5

# OCR
OCR_LANGUAGES=eng

# API
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
```

### Frontend Environment Variables

```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
```

## Production Deployment

### 1. Build Images
```bash
# Backend
docker build -t adamani-backend:latest .

# Frontend
docker build -t adamani-frontend:latest ./frontend
```

### 2. Deploy with Docker Compose
```bash
# Production docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Configure Nginx (Optional)
```nginx
# /etc/nginx/sites-available/adamani

upstream backend {
    server localhost:8080;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /docs {
        proxy_pass http://backend;
    }
}
```

## Monitoring

### Health Checks

```bash
# Backend
curl http://localhost:8080/health

# Frontend
curl http://localhost:3000

# Ollama
curl http://localhost:11434/api/tags
```

### Logs

```bash
# Docker Compose logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f ollama

# Direct logs
tail -f backend.log
tail -f frontend.log
```

## Troubleshooting

### Backend Won't Start
```bash
# Check if port 8080 is in use
lsof -i :8080

# Check Ollama connection
curl http://localhost:11434/api/tags

# View backend logs
docker-compose logs backend
```

### Frontend Can't Connect
```bash
# Check backend is running
curl http://localhost:8080/health

# Verify environment variable
cat frontend/.env.local

# Check CORS settings
# Backend must allow frontend origin
```

### Ollama Model Issues
```bash
# List installed models
docker exec -it ollama ollama list

# Pull model
docker exec -it ollama ollama pull llama3

# Test model
docker exec -it ollama ollama run llama3 "Hello"
```

### ChromaDB Issues
```bash
# Clear vector store
rm -rf data/vectorstore/*

# Check permissions
ls -la data/vectorstore

# Recreate directory
mkdir -p data/vectorstore
chmod 755 data/vectorstore
```

## Performance Tuning

### Backend
- Increase `CHUNK_SIZE` for longer documents
- Adjust `RETRIEVAL_TOP_K` for more context
- Use `VECTOR_STORE_TYPE=faiss` for speed
- Lower `LLM_TEMPERATURE` for consistency

### Frontend
- Enable Next.js production build
- Use CDN for static assets
- Configure proper caching headers

### Ollama
- Use GPU if available
- Adjust model size (llama3, llama3:7b, llama3:13b)
- Configure memory limits

## Scaling

### Horizontal Scaling
```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 3
    environment:
      - WORKER_PROCESSES=2
```

### Load Balancing
```nginx
upstream backend_servers {
    server backend1:8080;
    server backend2:8080;
    server backend3:8080;
}
```

## Backup & Restore

### Backup Data
```bash
# Backup vector store
tar -czf vectorstore-backup.tar.gz data/vectorstore/

# Backup uploads
tar -czf uploads-backup.tar.gz data/uploads/
```

### Restore Data
```bash
# Restore vector store
tar -xzf vectorstore-backup.tar.gz -C data/

# Restore uploads
tar -xzf uploads-backup.tar.gz -C data/
```

## Security Checklist

- [ ] Use HTTPS in production
- [ ] Set strong CORS policies
- [ ] Implement rate limiting
- [ ] Add authentication/authorization
- [ ] Sanitize file uploads
- [ ] Encrypt sensitive data
- [ ] Regular security updates
- [ ] Monitor for suspicious activity

## Next Steps

1. ✅ Start services with Docker Compose
2. ✅ Upload test invoices/PDFs
3. ✅ Test chat functionality
4. ⬜ Add authentication
5. ⬜ Deploy to production
6. ⬜ Monitor and optimize

## Support

- Backend Docs: http://localhost:8080/docs
- Frontend README: `frontend/README.md`
- Project Structure: `PROJECT_STRUCTURE.md`
- Dependencies: `DEPENDENCIES.md`

**You're all set!** 🎉

Environment variables (`.env`):

```bash
# LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
LLM_TEMPERATURE=0.1

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# RAG
RETRIEVAL_TOP_K=3
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# OCR
OCR_ENGINE=tesseract
OCR_LANGUAGES=eng

# Storage
VECTORDB_PATH=./data/vectorstore
UPLOAD_DIR=./data/uploads

# API
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

## Development Workflow

1. **Add new core functionality**: Create module in `core/`
2. **Add business logic**: Create service in `services/`
3. **Expose via API**: Add route in `api/routes/`
4. **Configure**: Add settings to `config/settings.py`

## Design Principles

- **Separation of Concerns**: Each layer has distinct responsibilities
- **Dependency Injection**: Services receive dependencies, not create them
- **Configuration Management**: All settings in one place
- **Logging**: Consistent, beautiful logging throughout
- **Type Safety**: Pydantic models for validation
- **Modularity**: Easy to swap implementations (e.g., different vector stores)
