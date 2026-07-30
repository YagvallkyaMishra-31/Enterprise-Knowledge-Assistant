"""Core module for generating answers using the Ollama LLM."""

import httpx
import logging
from typing import List, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

class GenerationError(Exception):
    """Raised when generating an answer from the LLM fails."""
    pass

def generate_answer(question: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Generates an answer to the question based on the provided context chunks.
    If context_chunks is empty, returns a fixed response without calling the LLM.
    
    Args:
        question: The user's question text.
        context_chunks: The list of retrieved chunk dictionaries.
        
    Returns:
        The generated answer string.
        
    Raises:
        GenerationError: If the call to Ollama fails.
    """
    if not context_chunks:
        return "I don't have enough information in your documents to answer that."
        
    # Assemble the context text
    context_texts = [f"Source: {c['filename']}\nContent: {c['chunkText']}" for c in context_chunks]
    joined_context = "\n\n---\n\n".join(context_texts)
    
    system_prompt = (
        "You are a helpful and accurate enterprise knowledge assistant. "
        "You MUST answer the user's question based strictly on the provided context. "
        "If the answer cannot be found in the context, you must explicitly state that you do not know. "
        "Do NOT invent, guess, or hallucinate information outside of the context provided."
    )
    
    user_prompt = f"Context Information:\n{joined_context}\n\nQuestion:\n{question}"
    
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload = {
        "model": settings.OLLAMA_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }
    
    try:
        # Generation can take time, using a generous timeout
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            message = data.get("message", {})
            return message.get("content", "").strip()
            
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Ollama for generation: {str(e)}")
        raise GenerationError(f"Failed to connect to Ollama: {str(e)}") from e
    except httpx.HTTPStatusError as e:
        logger.error(f"Ollama returned HTTP {e.response.status_code} during generation: {e.response.text}")
        raise GenerationError(f"Ollama returned HTTP {e.response.status_code}") from e
    except Exception as e:
        logger.error(f"Unexpected error during generation: {str(e)}")
        raise GenerationError(f"Unexpected error: {str(e)}") from e

def generate_answer_stream(question: str, context_chunks: List[Dict[str, Any]]):
    """
    Generates an answer to the question based on the context chunks as a stream.
    Yields NDJSON strings containing each token as it arrives.
    
    Args:
        question: The user's question text.
        context_chunks: The list of retrieved chunk dictionaries.
        
    Yields:
        NDJSON strings of format {"type": "token", "text": "..."}
    """
    import json
    
    if not context_chunks:
        # Fallback text if no chunks
        fallback_text = "I don't have enough information in your documents to answer that."
        yield json.dumps({"type": "token", "text": fallback_text}) + "\n"
        return
        
    # Assemble the context text
    context_texts = [f"Source: {c['filename']}\nContent: {c['chunkText']}" for c in context_chunks]
    joined_context = "\n\n---\n\n".join(context_texts)
    
    system_prompt = (
        "You are a helpful and accurate enterprise knowledge assistant. "
        "You MUST answer the user's question based strictly on the provided context. "
        "If the answer cannot be found in the context, you must explicitly state that you do not know. "
        "Do NOT invent, guess, or hallucinate information outside of the context provided."
    )
    
    user_prompt = f"Context Information:\n{joined_context}\n\nQuestion:\n{question}"
    
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload = {
        "model": settings.OLLAMA_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": True
    }
    
    try:
        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            message = data.get("message", {})
                            content = message.get("content", "")
                            if content:
                                yield json.dumps({"type": "token", "text": content}) + "\n"
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        logger.error(f"Error during stream generation: {str(e)}")
        # Don't throw if we're mid-stream, just yield an error line or close.
        # Returning here gracefully closes the stream. 
        # The java side relies on the stream ending before "done" as an error flag, or we could emit an error here.
        yield json.dumps({"type": "error", "message": f"LLM generation failed: {str(e)}"}) + "\n"
