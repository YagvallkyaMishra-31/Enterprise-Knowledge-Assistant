"""Core module for retrieving relevant chunks from the vector database."""

from typing import List, Dict, Any
import logging
from pgvector.psycopg2 import register_vector

from app.core.db import get_db_connection
from app.core.config import settings
from app.core.embeddings import get_embedding, EmbeddingError

logger = logging.getLogger(__name__)

class RetrievalError(Exception):
    """Raised when vector retrieval fails."""
    pass

def retrieve_chunks(user_id: str, question: str, top_k: int, max_distance: float) -> List[Dict[str, Any]]:
    """
    Retrieves the most relevant chunks from the database based on cosine distance.
    Filters by the specified user_id and documents in READY status.
    
    Args:
        user_id: The UUID of the user issuing the query.
        question: The user's question text.
        top_k: Maximum number of chunks to return.
        max_distance: The cosine distance threshold. Chunks with distance > max_distance are excluded.
        
    Returns:
        A list of dictionaries representing the retrieved chunks.
        Empty list if no chunks pass the threshold.
        
    Raises:
        EmbeddingError: If generating the question embedding fails.
        RetrievalError: If the database query fails.
    """
    try:
        query_embedding = get_embedding(question)
    except EmbeddingError as e:
        logger.error(f"Failed to embed question: {str(e)}")
        raise

    conn = None
    try:
        conn = get_db_connection()
        register_vector(conn)
        
        with conn.cursor() as cur:
            # We use the <=> operator provided by pgvector for cosine distance.
            # We join documents to filter by owner and status, and to fetch the filename.
            cur.execute(
                """
                SELECT 
                    dc.document_id,
                    d.filename,
                    dc.chunk_index,
                    dc.page_number,
                    dc.chunk_text,
                    (dc.embedding <=> %s::vector) AS distance
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE d.user_id = %s
                  AND d.upload_status = 'READY'
                  AND (dc.embedding <=> %s::vector) <= %s
                ORDER BY distance ASC
                LIMIT %s
                """,
                (query_embedding, user_id, query_embedding, max_distance, top_k)
            )
            
            results = []
            for row in cur.fetchall():
                results.append({
                    "documentId": str(row[0]),
                    "filename": row[1],
                    "chunkIndex": row[2],
                    "pageNumber": row[3],
                    "chunkText": row[4],
                    "distance": float(row[5])
                })
                
            return results
            
    except Exception as e:
        logger.error(f"Failed to retrieve chunks from database: {str(e)}")
        raise RetrievalError(f"Database query failed: {str(e)}") from e
    finally:
        if conn:
            conn.close()
