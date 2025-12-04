# """Chat and RAG endpoints."""
# from fastapi import APIRouter, HTTPException, Depends

# from ...services.rag_service import RAGService
# from ...core.memory import MemoryManager
# from ..models import ChatRequest, ChatResponse
# from ..dependencies import get_rag_service, get_memory_manager
# from ...utils.logger import get_logger

# logger = get_logger()
# router = APIRouter(prefix="/chat", tags=["chat"])


# @router.post("/", response_model=ChatResponse)
# async def chat(
#     request: ChatRequest,
#     rag_service: RAGService = Depends(get_rag_service),
# ):
#     """
#     Chat with AI using RAG (Retrieval-Augmented Generation).

#     This endpoint retrieves relevant documents and generates contextual responses.
#     """
#     try:
#         result = rag_service.query(
#             question=request.question,
#             session_id=request.session_id,
#             k=request.k,
#         )
#         return ChatResponse(**result)

#     except Exception as e:
#         logger.error(f"Chat endpoint error: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/memory/{session_id}")
# async def clear_memory(
#     session_id: str,
#     memory_manager: MemoryManager = Depends(get_memory_manager),
# ):
#     """Clear chat history for a specific session."""
#     try:
#         memory_manager.clear_history(session_id)
#         return {"status": "success", "message": f"Cleared memory for session: {session_id}"}

#     except Exception as e:
#         logger.error(f"Clear memory error: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/memory")
# async def clear_all_memory(
#     memory_manager: MemoryManager = Depends(get_memory_manager),
# ):
#     """Clear all chat histories."""
#     try:
#         count = memory_manager.get_session_count()
#         memory_manager.clear_all()
#         return {
#             "status": "success",
#             "message": f"Cleared {count} session histories",
#         }

#     except Exception as e:
#         logger.error(f"Clear all memory error: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))
"""Chat and RAG endpoints."""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from ...services.rag_service import RAGService
from ...core.memory import MemoryManager
from ..models import ChatRequest, ChatResponse
from ..dependencies import get_rag_service, get_memory_manager
from ...utils.logger import get_logger

logger = get_logger()
router = APIRouter(prefix="/chat", tags=["chat"])


def process_query_background(question: str, session_id: str, k: int, rag_service: RAGService):
    """Background task to process RAG query."""
    try:
        result = rag_service.query(
            question=question,
            session_id=session_id,
            k=k,
        )
        logger.success(f"✅ Query processed: {question[:50]}...")
        # Store result somewhere for frontend to retrieve
        # For now, just log it
    except Exception as e:
        logger.error(f"❌ Background query error: {str(e)}")


@router.post("/")
async def chat(
    background_tasks: BackgroundTasks,
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    Chat with AI using RAG (Retrieval-Augmented Generation).

    This endpoint retrieves relevant documents and generates contextual responses.
    """
    try:
        # For now, process synchronously but with timeout protection
        # Better: implement streaming or webhook callback
        result = rag_service.query(
            question=request.question,
            session_id=request.session_id,
            k=request.k,
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "session_id": result.get("session_id", request.session_id)
            }
        )

    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "answer": "I encountered an error processing your question. Please try again.",
                "sources": [],
                "session_id": request.session_id
            }
        )


@router.delete("/memory/{session_id}")
async def clear_memory(
    session_id: str,
    memory_manager: MemoryManager = Depends(get_memory_manager),
):
    """Clear chat history for a specific session."""
    try:
        memory_manager.clear_history(session_id)
        return {"status": "success", "message": f"Cleared memory for session: {session_id}"}

    except Exception as e:
        logger.error(f"Clear memory error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory")
async def clear_all_memory(
    memory_manager: MemoryManager = Depends(get_memory_manager),
):
    """Clear all chat histories."""
    try:
        count = memory_manager.get_session_count()
        memory_manager.clear_all()
        return {
            "status": "success",
            "message": f"Cleared {count} session histories",
        }

    except Exception as e:
        logger.error(f"Clear all memory error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
