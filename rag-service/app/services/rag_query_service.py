"""Service for orchestrating RAG queries."""

from typing import Dict, Any
import logging

from app.core.config import settings
from app.core.retrieval import retrieve_chunks
from app.core.generation import generate_answer

logger = logging.getLogger(__name__)

def execute_rag_query(user_id: str, question: str) -> Dict[str, Any]:
    """
    Orchestrates the retrieval and generation steps to answer a user's question.
    
    Args:
        user_id: The UUID of the user.
        question: The user's query text.
        
    Returns:
        A dictionary containing the structured response:
        {
            "answer": str,
            "hasContext": bool,
            "sources": List[Dict]
        }
    """
    logger.info(f"Executing RAG query for user {user_id}")
    
    # 1. Retrieve relevant chunks
    chunks = retrieve_chunks(
        user_id=user_id,
        question=question,
        top_k=settings.RAG_TOP_K,
        max_distance=settings.RAG_MAX_DISTANCE
    )
    
    has_context = len(chunks) > 0
    
    # 2. Generate answer
    answer = generate_answer(question=question, context_chunks=chunks)
    
    # 3. Assemble response
    # We only return specific fields for sources
    formatted_sources = []
    for c in chunks:
        formatted_sources.append({
            "documentId": c["documentId"],
            "filename": c["filename"],
            "chunkIndex": c["chunkIndex"],
            "pageNumber": c["pageNumber"],
            "distance": c["distance"]
        })
        
    return {
        "answer": answer,
        "hasContext": has_context,
        "sources": formatted_sources
    }
