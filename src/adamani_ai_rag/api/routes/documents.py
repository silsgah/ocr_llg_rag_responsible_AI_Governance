
"""Document management endpoints."""
import os
import shutil
import uuid
from typing import List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncio
from time import time

from ...services.document_service import DocumentService
from ..models import AddTextsRequest, DocumentResponse
from ..dependencies import get_document_service, get_settings
from ...config import Settings
from ...utils.logger import get_logger

logger = get_logger()
router = APIRouter(prefix="/documents", tags=["documents"])

# Store for async processing results (use Redis/DB in production)
_upload_results: Dict[str, Any] = {}


@router.post("/texts", response_model=DocumentResponse)
async def add_texts(
    request: AddTextsRequest,
    doc_service: DocumentService = Depends(get_document_service),
):
    """
    Add text documents to the knowledge base.

    Texts will be chunked and embedded before adding to vector store.
    """
    try:
        count = doc_service.add_texts(request.texts, request.metadatas)

        return DocumentResponse(
            status="success",
            documents_added=len(request.texts),
            chunks_created=count,
            message=f"Successfully added {count} text chunks",
        )

    except Exception as e:
        logger.error(f"Add texts error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def process_file_background(file_path: str, filename: str, use_ocr: bool, doc_service: DocumentService, upload_id: str):
    """Background task to process file."""
    try:
        logger.info(f"🔄 Processing {filename} in background...")
        
        # ✅ RUN THE ASYNC METHOD PROPERLY
        try:
            loop = asyncio.get_running_loop()
            chunks = loop.run_until_complete(doc_service.process_file(file_path, use_ocr=use_ocr))
        except RuntimeError:
            # No event loop running → create new one
            chunks = asyncio.run(doc_service.process_file(file_path, use_ocr=use_ocr))
        
        # Store result for retrieval
        _upload_results[upload_id] = {
            "status": "success",
            "documents_added": 1,
            "chunks_created": chunks,
            "message": f"Successfully processed {filename}",
            "timestamp": time()
        }
        logger.success(f"✅ Background processing complete: {chunks} chunks created from {filename}")
        
    except Exception as e:
        logger.error(f"❌ Background processing error: {str(e)}")
        _upload_results[upload_id] = {
            "status": "error",
            "message": str(e)[:200],
            "timestamp": time()
        }

@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    use_ocr: bool = False,
    doc_service: DocumentService = Depends(get_document_service),
    settings: Settings = Depends(get_settings),
):
    """
    Upload and process a document file.

    Supports:
    - PDFs (.pdf) - with optional OCR for scanned documents
    - Images (.png, .jpg, .jpeg, .tiff) - automatic OCR
    
    Returns 202 Accepted with upload_id. Use /documents/status/{upload_id} to check progress.
    """
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.supported_doc_formats:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": f"Unsupported file format. Supported: {settings.supported_doc_formats}"
                }
            )

        # Save uploaded file
        os.makedirs(settings.upload_dir, exist_ok=True)
        file_path = os.path.join(settings.upload_dir, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"📥 Uploaded file: {file.filename} ({file_ext})")

        # Generate unique upload ID
        upload_id = str(uuid.uuid4())
        
        # Initialize status as processing
        _upload_results[upload_id] = {
            "status": "processing",
            "message": "Processing file..."
        }

        # Process file in background
        background_tasks.add_task(
            process_file_background,
            file_path,
            file.filename,
            use_ocr,
            doc_service,
            upload_id
        )
        
        # Return immediately with upload ID
        return JSONResponse(
            status_code=202,  # 202 Accepted
            content={
                "status": "processing",
                "upload_id": upload_id,
                "message": f"File {file.filename} uploaded and queued for processing"
            }
        )

    except Exception as e:
        logger.error(f"Upload file error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Upload failed"
            }
        )


@router.get("/status/{upload_id}")
async def get_upload_status(upload_id: str):
    """Check status of a background upload/processing task."""
    if upload_id not in _upload_results:
        return JSONResponse(
            status_code=404,
            content={
                "status": "not_found",
                "message": "Upload ID not found or expired"
            }
        )
    
    result_data = _upload_results[upload_id]
    return JSONResponse(status_code=200, content=result_data)

@router.post("/process-directory", response_model=DocumentResponse)
async def process_directory(
    directory_path: str,
    doc_service: DocumentService = Depends(get_document_service),
):
    """
    Process all supported documents in a directory.

    Recursively processes images with OCR.
    """
    try:
        if not os.path.exists(directory_path):
            raise HTTPException(status_code=404, detail="Directory not found")

        chunks = doc_service.process_directory(directory_path)

        return DocumentResponse(
            status="success",
            documents_added=0,
            chunks_created=chunks,
            message=f"Successfully processed directory: {directory_path}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process directory error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_knowledge_base(
    doc_service: DocumentService = Depends(get_document_service),
):
    """Clear all documents from the knowledge base."""
    try:
        doc_service.clear_vectorstore()
        return {
            "status": "success",
            "message": "Knowledge base cleared",
        }

    except Exception as e:
        logger.error(f"Clear knowledge base error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))