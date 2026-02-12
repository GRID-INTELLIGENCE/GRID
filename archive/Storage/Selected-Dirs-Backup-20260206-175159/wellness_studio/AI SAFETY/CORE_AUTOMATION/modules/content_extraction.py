"""
Content Extraction Module
Handles content extraction from various sources (HTML, PDF, JavaScript-rendered pages)
"""
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Content cache
_content_cache = {}

def get_content_hash(content: str) -> str:
    """Generate hash for content"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def get_cached_content(url: str) -> Optional[str]:
    """Get cached content for URL"""
    return _content_cache.get(url)

def set_cached_content(url: str, content: str) -> None:
    """Cache content for URL"""
    _content_cache[url] = content

def is_content_cached(url: str) -> bool:
    """Check if content is cached"""
    return url in _content_cache

def extract_text_from_html(html: str) -> str:
    """Extract text content from HTML, focusing on main content areas"""
    import re
    
    # Remove script and style tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Extract text from common content containers
    content_patterns = [
        r'<main[^>]*>(.*?)</main>',
        r'<article[^>]*>(.*?)</article>',
        r'<section[^>]*>(.*?)</section>',
        r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
    ]
    
    extracted_texts = []
    for pattern in content_patterns:
        matches = re.findall(pattern, html, flags=re.DOTALL | re.IGNORECASE)
        extracted_texts.extend(matches)
    
    if extracted_texts:
        # Remove all HTML tags
        text = ' '.join(extracted_texts)
        text = re.sub(r'<[^>]+>', ' ', text)
        return text.strip()
    
    # Fallback: extract all text
    text = re.sub(r'<[^>]+>', ' ', html)
    return text.strip()

def clean_text(text: str) -> str:
    """Clean and normalize extracted text"""
    import re
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    return text.strip()

def extract_content_from_response(response: Dict[str, Any]) -> str:
    """Extract and clean content from API response"""
    content = response.get('content', '')
    
    # Check if content is HTML
    if '<' in content and '>' in content:
        content = extract_text_from_html(content)
    
    # Clean the content
    content = clean_text(content)
    
    return content

def get_content_metadata(response: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata from content response"""
    metadata = {
        "url": response.get('url', ''),
        "status": response.get('status', 0),
        "content_length": response.get('content_length', 0),
        "method": response.get('method', 'unknown'),
        "cached": response.get('cached', False),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Add PDF metadata if available
    if 'metadata' in response:
        metadata['pdf_metadata'] = response['metadata']
    
    return metadata
