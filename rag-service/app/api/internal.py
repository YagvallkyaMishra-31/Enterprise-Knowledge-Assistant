"""Internal API routes for service-to-service communication."""

from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
import json

from app.core.config import settings
from app.services.document_processor import process_document
from app.services.rag_query_service import execute_rag_query
from app.core.retrieval import retrieve_chunks
from app.core.generation import generate_answer_stream

logger = logging.getLogger(__name__)

router = APIRouter()

class ProcessDocumentRequest(BaseModel):
    documentId: str
    userId: str
    filePath: str

class QueryRequest(BaseModel):
    userId: str
    question: str

@router.post("/process-document")
def handle_process_document(
    request: ProcessDocumentRequest,
    x_internal_api_key: str = Header(None)
):
    """
    Triggers the synchronous processing of a document (extraction, chunking, embedding).
    Secured via X-Internal-Api-Key.
    """
    if not x_internal_api_key or x_internal_api_key != settings.INTERNAL_API_KEY:
        logger.warning("Unauthorized access attempt to internal API")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key"
        )
        
    try:
        process_document(request.documentId, request.userId, request.filePath)
        return {"status": "success", "message": "Document processed successfully"}
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )

@router.post("/query")
def handle_query(
    request: QueryRequest,
    x_internal_api_key: str = Header(None)
):
    """
    Executes a RAG query (retrieval and generation).
    Secured via X-Internal-Api-Key.
    """
    if not x_internal_api_key or x_internal_api_key != settings.INTERNAL_API_KEY:
        logger.warning("Unauthorized access attempt to internal query API")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key"
        )
        
    try:
        response = execute_rag_query(request.userId, request.question)
        return response
    except Exception as e:
        logger.error(f"Error executing RAG query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/query-stream")
def handle_query_stream(
    request: QueryRequest,
    x_internal_api_key: str = Header(None)
):
    """
    Executes a RAG query and returns a streaming response of NDJSON lines.
    Secured via X-Internal-Api-Key.
    """
    if not x_internal_api_key or x_internal_api_key != settings.INTERNAL_API_KEY:
        logger.warning("Unauthorized access attempt to internal query-stream API")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key"
        )
        
    def stream_generator():
        try:
            chunks = retrieve_chunks(
                user_id=request.userId,
                question=request.question,
                top_k=settings.RAG_TOP_K,
                max_distance=settings.RAG_MAX_DISTANCE
            )
            
            formatted_sources = []
            for c in chunks:
                formatted_sources.append({
                    "documentId": c["documentId"],
                    "filename": c["filename"],
                    "chunkIndex": c["chunkIndex"],
                    "pageNumber": c["pageNumber"],
                    "distance": c["distance"]
                })
                
            yield json.dumps({"type": "sources", "sources": formatted_sources}) + "\n"
            
            for token_line in generate_answer_stream(request.question, chunks):
                yield token_line
                
            yield json.dumps({"type": "done"}) + "\n"
            
        except Exception as e:
            logger.error(f"Error executing RAG stream query: {str(e)}")
            yield json.dumps({"type": "error", "message": f"Query failed: {str(e)}"}) + "\n"

    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")
