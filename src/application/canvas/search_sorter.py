"""
GRID Canvas Search Sorter - MCP Server Context
Advanced sorting for search results with safety and relevance integration

LIMITATIONS:
    This module provides heuristic-based sorting for search results in the GRID
    framework. It integrates with the existing RelevanceEngine and SafetyGuard
    systems to provide comprehensive result ranking.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, List

logger = logging.getLogger(__name__)


@dataclass
class CanvasSearchResult:
    """Enhanced search result for GRID Canvas with safety and relevance"""
    
    id: str
    content: str
    route: Path
    score: float
    timestamp: datetime
    safety_verdict: str
    pii_detected: bool = False
    relevance_metrics: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_safe(self) -> bool:
        """Check if result passed safety validation"""
        return self.safety_verdict in ("pass", "warn")
    
    @property
    def confidence(self) -> float:
        """Get overall confidence score"""
        return self.relevance_metrics.get("confidence", 0.5)


class CanvasSearchSorter:
    """Advanced sorting for GRID Canvas MCP server search results"""
    
    def __init__(self):
        """Initialize Canvas search sorter"""
        self.usage_history: dict[str, int] = {}
        self.pii_patterns = {
            "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
            "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
            "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        }
    
    def sort_by_relevance(self, results: List[CanvasSearchResult]) -> List[CanvasSearchResult]:
        """Sort by relevance score (descending) with safety filtering"""
        safe_results = [r for r in results if r.is_safe]
        
        return sorted(
            safe_results,
            key=lambda x: (x.score, x.confidence),
            reverse=True
        )
    
    def sort_by_recency(self, results: List[CanvasSearchResult]) -> List[CanvasSearchResult]:
        """Sort by timestamp (most recent first) with safety filtering"""
        safe_results = [r for r in results if r.is_safe]
        
        return sorted(
            safe_results,
            key=lambda x: x.timestamp,
            reverse=True
        )
    
    def sort_by_safety_then_relevance(self, results: List[CanvasSearchResult]) -> List[CanvasSearchResult]:
        """Prioritize safety, then relevance. PII-free results get priority."""
        clean_results = [r for r in results if r.is_safe and not r.pii_detected]
        pii_results = [r for r in results if r.is_safe and r.pii_detected]
        unsafe_results = [r for r in results if not r.is_safe]
        
        # Sort each category by relevance
        clean_sorted = sorted(clean_results, key=lambda x: (x.score, x.confidence), reverse=True)
        pii_sorted = sorted(pii_results, key=lambda x: (x.score, x.confidence), reverse=True)
        unsafe_sorted = sorted(unsafe_results, key=lambda x: (x.score, x.confidence), reverse=True)
        
        return clean_sorted + pii_sorted + unsafe_sorted
    
    def sort_by_confidence_then_score(self, results: List[CanvasSearchResult]) -> List[CanvasSearchResult]:
        """Multi-criteria sort: confidence then relevance score"""
        safe_results = [r for r in results if r.is_safe]
        
        return sorted(
            safe_results,
            key=lambda x: (x.confidence, x.score),
            reverse=True
        )
    
    def sort_by_path_complexity(self, results: List[CanvasSearchResult]) -> List[CanvasSearchResult]:
        """Sort by path complexity (simpler paths first)"""
        safe_results = [r for r in results if r.is_safe]
        
        return sorted(
            safe_results,
            key=lambda x: x.relevance_metrics.get("path_complexity", 1.0)
        )
    
    def create_search_result(
        self,
        route: Path,
        query: str,
        content: str,
        timestamp: datetime | None = None
    ) -> CanvasSearchResult:
        """Create a CanvasSearchResult with safety and relevance analysis"""
        
        # Safety validation
        safety_verdict, pii_detected = self._validate_safety(content)
        
        # Relevance scoring
        relevance_metrics = self._calculate_relevance(route, query)
        
        # Record usage
        self.record_usage(route)
        
        return CanvasSearchResult(
            id=str(route),
            content=content,
            route=route,
            score=relevance_metrics["final_score"],
            timestamp=timestamp or datetime.now(),
            safety_verdict=safety_verdict,
            pii_detected=pii_detected,
            relevance_metrics=relevance_metrics,
            metadata={
                "route_complexity": relevance_metrics.get("path_complexity", 0.0),
                "semantic_similarity": relevance_metrics.get("semantic_similarity", 0.0),
                "usage_frequency": relevance_metrics.get("usage_frequency", 0.0),
            }
        )
    
    def _validate_safety(self, text: str) -> tuple[str, bool]:
        """Simple safety validation"""
        if not isinstance(text, str):
            return "reject", False
        
        # Check for PII
        for pattern in self.pii_patterns.values():
            if pattern.search(text):
                return "warn", True
        
        return "pass", False
    
    def _calculate_relevance(self, route: Path, query: str) -> dict[str, float]:
        """Calculate relevance metrics"""
        query_lower = query.lower()
        route_str = str(route).lower()
        
        # Semantic similarity
        query_words = set(query_lower.split())
        route_words = set(route_str.replace("/", " ").replace("_", " ").split())
        
        intersection = query_words.intersection(route_words)
        union = query_words.union(route_words)
        semantic_sim = len(intersection) / len(union) if union else 0.0
        
        # Path complexity
        depth = len(route.parts)
        complexity = min(1.0, depth / 10.0)
        
        # Usage frequency
        usage_count = self.usage_history.get(str(route), 0)
        frequency = min(1.0, usage_count / 10.0)
        
        # Weighted score
        final_score = (
            semantic_sim * 0.4 +
            (1.0 - complexity) * 0.2 +
            frequency * 0.2 +
            0.5 * 0.2  # Context and alignment
        )
        
        # Confidence
        confidence = min(1.0, final_score + 0.1)
        
        return {
            "final_score": final_score,
            "semantic_similarity": semantic_sim,
            "path_complexity": complexity,
            "usage_frequency": frequency,
            "context_match": 0.5,
            "integration_alignment": 0.5,
            "confidence": confidence,
        }
    
    def record_usage(self, route: Path) -> None:
        """Record route usage for frequency scoring"""
        route_str = str(route)
        self.usage_history[route_str] = self.usage_history.get(route_str, 0) + 1


# MCP Server Tool Definitions
CANVAS_SEARCH_SORT_TOOLS = [
    {
        "name": "sort_canvas_search_results",
        "description": "Sort Canvas search results by various criteria",
        "inputSchema": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "description": "Array of search results to sort",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "content": {"type": "string"},
                            "route": {"type": "string"},
                            "score": {"type": "number"},
                            "timestamp": {"type": "string"},
                            "safety_verdict": {"type": "string"},
                            "pii_detected": {"type": "boolean"}
                        }
                    }
                },
                "sort_method": {
                    "type": "string",
                    "enum": ["relevance", "recency", "safety_first", "confidence", "complexity"],
                    "default": "relevance",
                    "description": "Sorting method to use"
                }
            },
            "required": ["results"]
        }
    },
    {
        "name": "create_canvas_search_result",
        "description": "Create a new Canvas search result with analysis",
        "inputSchema": {
            "type": "object",
            "properties": {
                "route": {"type": "string", "description": "File route path"},
                "query": {"type": "string", "description": "Search query"},
                "content": {"type": "string", "description": "File content"},
                "timestamp": {"type": "string", "description": "ISO timestamp (optional)"}
            },
            "required": ["route", "query", "content"]
        }
    }
]
