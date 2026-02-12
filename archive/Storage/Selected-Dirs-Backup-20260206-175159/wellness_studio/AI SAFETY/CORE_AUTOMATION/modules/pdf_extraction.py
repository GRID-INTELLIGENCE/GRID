"""
PDF Extraction Module
Handles PDF text extraction with metadata
"""
import hashlib
from typing import Dict, Any
from datetime import datetime, timezone

def extract_pdf_metadata(pdf_reader) -> Dict[str, Any]:
    """Extract metadata from PDF reader"""
    metadata = pdf_reader.metadata

    return {
        "title": metadata.get('/Title', 'Unknown') if metadata else 'Unknown',
        "author": metadata.get('/Author', 'Unknown') if metadata else 'Unknown',
        "subject": metadata.get('/Subject', 'Unknown') if metadata else 'Unknown',
        "creator": metadata.get('/Creator', 'Unknown') if metadata else 'Unknown',
        "pages": len(pdf_reader.pages)
    }

def extract_pdf_text(pdf_reader) -> str:
    """Extract full text content from PDF"""
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def get_pdf_content_hash(content: bytes) -> str:
    """Generate hash for PDF content"""
    return hashlib.md5(content).hexdigest()

def parse_pdf_content(content: bytes) -> Dict[str, Any]:
    """Parse PDF content and extract text and metadata"""
    try:
        from pypdf import PdfReader  # type: ignore
        from io import BytesIO

        pdf_file = BytesIO(content)
        pdf_reader = PdfReader(pdf_file)

        # Extract metadata
        metadata = extract_pdf_metadata(pdf_reader)

        # Extract full text content
        text = extract_pdf_text(pdf_reader)

        # Generate content hash
        content_hash = get_pdf_content_hash(content)

        return {
            "text": text,
            "metadata": metadata,
            "content_hash": content_hash,
            "success": True
        }
    except Exception as e:
        return {
            "text": "",
            "metadata": {},
            "content_hash": "",
            "success": False,
            "error": str(e)
        }
