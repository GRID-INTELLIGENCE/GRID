"""Token counting utilities for working memory metrics."""

import re
from typing import Any


class TokenCounter:
    """Simple token counter for context building metrics."""
    
    def __init__(self, token_limit: int = 4000):
        """Initialize token counter.
        
        Args:
            token_limit: Maximum token limit (default: 4000)
        """
        self.token_limit = token_limit
        self.tokens_used = 0
        self.chunks_retrieved = 0
        self.chunks_used = 0
        
    def count_tokens(self, text: str) -> int:
        """Count approximate tokens in text.
        
        Uses simple heuristic: ~4 characters per token for English text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Approximate token count
        """
        # Simple heuristic: split on whitespace and punctuation
        tokens = re.findall(r'\w+|[^\w\s]', text)
        return len(tokens)
    
    def build_context_with_limit(self, chunks: list[str]) -> str:
        """Build context while tracking token usage.
        
        Args:
            chunks: List of text chunks to include
            
        Returns:
            Built context string
        """
        context_parts = []
        self.chunks_retrieved = len(chunks)
        self.tokens_used = 0
        self.chunks_used = 0
        
        for chunk in chunks:
            chunk_tokens = self.count_tokens(chunk)
            
            # Check if adding this chunk would exceed limit
            if self.tokens_used + chunk_tokens > self.token_limit:
                break
                
            context_parts.append(chunk)
            self.tokens_used += chunk_tokens
            self.chunks_used += 1
        
        return "\n\n".join(context_parts)
    
    def get_metrics(self) -> dict[str, Any]:
        """Get token counting metrics.
        
        Returns:
            Dictionary with token metrics
        """
        return {
            "tokens_used": self.tokens_used,
            "tokens_limit": self.token_limit,
            "utilization": self.tokens_used / self.token_limit if self.token_limit > 0 else 0.0,
            "remaining_tokens": self.token_limit - self.tokens_used,
            "chunks_retrieved": self.chunks_retrieved,
            "chunks_used": self.chunks_used,
            "chunks_cap": self.chunks_retrieved  # Total available chunks
        }
    
    def reset(self) -> None:
        """Reset counters."""
        self.tokens_used = 0
        self.chunks_retrieved = 0
        self.chunks_used = 0
