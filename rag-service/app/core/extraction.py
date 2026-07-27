"""Text extraction from physical files."""

import pypdf
import os

class UnsupportedFileExtensionError(Exception):
    """Raised when an extraction is requested for an unsupported file extension."""
    pass

class ExtractionError(Exception):
    """Raised when text extraction fails for an unexpected reason."""
    pass

def extract_text(file_path: str, ext: str) -> str:
    """
    Extracts raw text from a file based on its extension.
    
    Args:
        file_path: The absolute path to the physical file.
        ext: The file extension (e.g., 'pdf', 'txt', 'md').
        
    Returns:
        The extracted raw text as a string.
        
    Raises:
        UnsupportedFileExtensionError: If the extension is not .txt, .md, or .pdf.
        ExtractionError: If there's an I/O error or pypdf fails.
    """
    if not os.path.exists(file_path):
        raise ExtractionError(f"File not found: {file_path}")
        
    ext_lower = ext.lower().lstrip(".")
    
    try:
        if ext_lower in ["txt", "md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
                
        elif ext_lower == "pdf":
            text = []
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text.append(extracted)
            return "\n\n".join(text)
            
        else:
            raise UnsupportedFileExtensionError(f"Extension '{ext}' is not supported for text extraction.")
            
    except UnsupportedFileExtensionError:
        raise
    except Exception as e:
        raise ExtractionError(f"Failed to extract text from {file_path}: {str(e)}") from e
