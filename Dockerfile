# Use official Python image
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock* /app/

# Install system dependencies (Tesseract OCR + Poppler for PDF)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir "poetry>=1.7.0"

# Install Python dependencies (skip installing the project itself)
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Copy source code
COPY src/ /app/src/

# Expose port
EXPOSE 8000

# Create data directories
RUN mkdir -p /app/data/uploads /app/data/processed /app/data/vectorstore

# Run the FastAPI app with Uvicorn
# Use PORT environment variable from Render, default to 8000 for local development
CMD uvicorn src.adamani_ai_rag.api.app:app --host 0.0.0.0 --port ${PORT:-8000}
