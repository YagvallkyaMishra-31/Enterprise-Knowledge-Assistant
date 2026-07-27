"""Text chunking for RAG."""

from typing import List, Tuple, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text: str) -> List[Tuple[int, str, Optional[int]]]:
    """
    Splits raw text into manageable chunks for embedding and retrieval.
    
    Args:
        text: The full raw text of the document.
        
    Returns:
        A list of tuples: (chunk_index, chunk_text, page_number).
        page_number is None for now since we extract the whole document as one string.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )
    
    raw_chunks = splitter.split_text(text)
    
    result = []
    for i, chunk in enumerate(raw_chunks):
        # We use None for page_number as requested for initial phase
        result.append((i, chunk, None))
        
    return result
