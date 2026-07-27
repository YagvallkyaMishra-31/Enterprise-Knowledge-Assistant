"""Internal API routes for service-to-service communication."""

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel
import logging

from app.core.config import settings
from app.services.document_processor import process_document

logger = logging.getLogger(__name__)

router = APIRouter()

class ProcessDocumentRequest(BaseModel):
    documentId: str
    userId: str
    filePath: str

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
