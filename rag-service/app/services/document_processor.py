"""Orchestrates the document processing pipeline."""

import logging
import os
from pgvector.psycopg2 import register_vector

from app.core.config import settings
from app.core.db import get_db_connection
from app.core.extraction import extract_text, UnsupportedFileExtensionError, ExtractionError
from app.core.chunking import chunk_text
from app.core.embeddings import get_embedding, EmbeddingError

logger = logging.getLogger(__name__)

def process_document(document_id: str, user_id: str, file_path: str):
    """
    Executes the full RAG pipeline for a single document.
    
    Args:
        document_id: The UUID of the document record.
        user_id: The UUID of the owner.
        file_path: The relative path to the physical file.
    """
    # Resolve the absolute physical path by prepending UPLOAD_ROOT_PATH
    full_path = os.path.join(settings.UPLOAD_ROOT_PATH, file_path)
    
    conn = None
    try:
        conn = get_db_connection()
        # Register pgvector on the connection to handle vector types
        register_vector(conn)
        
        with conn.cursor() as cur:
            # 1. Update status to PROCESSING
            cur.execute(
                "UPDATE documents SET upload_status = 'PROCESSING' WHERE id = %s",
                (document_id,)
            )
            conn.commit()
            
            # 2. Extract text
            ext = os.path.splitext(full_path)[1]
            raw_text = extract_text(full_path, ext)
            
            # 3. Chunk text
            chunks = chunk_text(raw_text)
            
            # 4. Embed and Insert chunks
            # Start a new transaction for the chunks
            for chunk_index, chunk_text_content, page_number in chunks:
                embedding = get_embedding(chunk_text_content)
                
                cur.execute(
                    """
                    INSERT INTO document_chunks 
                    (document_id, content, chunk_index, embedding, page_number)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (document_id, chunk_text_content, chunk_index, embedding, page_number)
                )
            
            # 5. Update status to READY
            cur.execute(
                "UPDATE documents SET upload_status = 'READY' WHERE id = %s",
                (document_id,)
            )
            conn.commit()
            logger.info(f"Successfully processed document {document_id}")
            
    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {str(e)}")
        if conn:
            # Rollback any pending transaction (like partially inserted chunks)
            conn.rollback()
            try:
                # Attempt to mark as FAILED
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE documents SET upload_status = 'FAILED' WHERE id = %s",
                        (document_id,)
                    )
                conn.commit()
            except Exception as inner_e:
                logger.error(f"Failed to update document status to FAILED: {str(inner_e)}")
        # Re-raise the exception as requested
        raise
        
    finally:
        if conn:
            conn.close()
