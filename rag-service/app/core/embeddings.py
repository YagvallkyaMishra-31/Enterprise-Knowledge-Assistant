"""Integration with Ollama for text embeddings."""

import httpx
from typing import List
from app.core.config import settings

class EmbeddingError(Exception):
    """Raised when the embedding generation fails."""
    pass

def get_embedding(text: str) -> List[float]:
    """
    Fetches a 768-length float vector from Ollama's /api/embeddings endpoint using nomic-embed-text.
    
    Raises:
        EmbeddingError: If Ollama is unreachable, returns an error, or the vector shape is unexpected.
    """
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/embeddings"
    payload = {
        "model": "nomic-embed-text",
        "prompt": text
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            embedding = data.get("embedding")
            
            if not embedding or not isinstance(embedding, list):
                raise EmbeddingError("Response from Ollama did not contain a valid 'embedding' list.")
                
            if len(embedding) != 768:
                raise EmbeddingError(f"Expected embedding of length 768, got {len(embedding)}.")
                
            return embedding
    except httpx.RequestError as e:
        raise EmbeddingError(f"Failed to connect to Ollama: {str(e)}") from e
    except httpx.HTTPStatusError as e:
        raise EmbeddingError(f"Ollama returned HTTP {e.response.status_code}: {e.response.text}") from e
