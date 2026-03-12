"""
Unit tests for GRID Search Sorter components
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from src.application.canvas.search_sorter import CanvasSearchSorter, CanvasSearchResult
from src.mycelium.search_safety import SearchSafetyGuard, SearchSafetyVerdict


class TestCanvasSearchSorter:
    """Test cases for CanvasSearchSorter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sorter = CanvasSearchSorter()
        self.query = "test query"
        self.base_time = datetime.now()
        
        # Create test results
        self.results = [
            CanvasSearchResult(
                id="1",
                content="Test content with relevance",
                route=Path("src/test/file1.py"),
                score=0.8,
                timestamp=self.base_time,
                safety_verdict="pass",
                pii_detected=False,
                relevance_metrics={"confidence": 0.9, "path_complexity": 0.3}
            ),
            CanvasSearchResult(
                id="2",
                content="Content with email@example.com PII",
                route=Path("src/test/file2.py"),
                score=0.9,
                timestamp=self.base_time + timedelta(hours=1),
                safety_verdict="warn",
                pii_detected=True,
                relevance_metrics={"confidence": 0.7, "path_complexity": 0.5}
            ),
            CanvasSearchResult(
                id="3",
                content="Unsafe content",
                route=Path("src/test/file3.py"),
                score=0.7,
                timestamp=self.base_time + timedelta(hours=2),
                safety_verdict="reject",
                pii_detected=False,
                relevance_metrics={"confidence": 0.6, "path_complexity": 0.2}
            ),
        ]
    
    def test_sort_by_relevance(self):
        """Test sorting by relevance score."""
        sorted_results = self.sorter.sort_by_relevance(self.results)
        
        # Should filter out unsafe results and sort by score
        assert len(sorted_results) == 2
        assert sorted_results[0].score == 0.9  # Higher score first
        assert sorted_results[1].score == 0.8
        assert all(r.is_safe for r in sorted_results)
    
    def test_sort_by_recency(self):
        """Test sorting by timestamp."""
        sorted_results = self.sorter.sort_by_recency(self.results)
        
        # Should filter unsafe and sort by timestamp (newest first)
        assert len(sorted_results) == 2
        assert sorted_results[0].timestamp == self.base_time + timedelta(hours=1)
        assert sorted_results[1].timestamp == self.base_time
    
    def test_sort_by_safety_then_relevance(self):
        """Test safety-first sorting."""
        sorted_results = self.sorter.sort_by_safety_then_relevance(self.results)
        
        # Should prioritize clean results over PII results
        assert len(sorted_results) == 3
        assert sorted_results[0].pii_detected == False  # Clean first
        assert sorted_results[0].safety_verdict == "pass"
        assert sorted_results[1].pii_detected == True   # PII second
        assert sorted_results[2].safety_verdict == "reject"  # Unsafe last
    
    def test_sort_by_confidence_then_score(self):
        """Test confidence-then-score sorting."""
        sorted_results = self.sorter.sort_by_confidence_then_score(self.results)
        
        # Should sort by confidence first, then score
        assert len(sorted_results) == 2  # Safe only
        assert sorted_results[0].relevance_metrics["confidence"] == 0.9
        assert sorted_results[1].relevance_metrics["confidence"] == 0.7
    
    def test_sort_by_path_complexity(self):
        """Test sorting by path complexity."""
        sorted_results = self.sorter.sort_by_path_complexity(self.results)
        
        # Should sort by complexity (simpler first)
        assert len(sorted_results) == 2  # Safe only
        complexities = [r.relevance_metrics.get("path_complexity", 1.0) for r in sorted_results]
        assert complexities == sorted(complexities)
    
    def test_create_search_result(self):
        """Test creating search results with analysis."""
        route = Path("src/test/example.py")
        content = "Example test content"
        
        result = self.sorter.create_search_result(route, self.query, content)
        
        assert isinstance(result, CanvasSearchResult)
        assert result.route == route
        assert result.content == content
        assert result.is_safe
        assert not result.pii_detected
        assert "final_score" in result.relevance_metrics
        assert "confidence" in result.relevance_metrics
    
    def test_create_search_result_with_pii(self):
        """Test creating search result with PII detection."""
        route = Path("src/test/example.py")
        content = "Contact me at user@example.com or call 555-123-4567"
        
        result = self.sorter.create_search_result(route, self.query, content)
        
        assert result.pii_detected
        assert result.safety_verdict == "warn"
        assert "email" in result.content.lower() or "555" in result.content
    
    def test_record_usage(self):
        """Test usage recording for frequency scoring."""
        route = Path("src/test/popular.py")
        
        # Record multiple uses
        for _ in range(5):
            self.sorter.record_usage(route)
        
        # Check usage was recorded
        usage_count = self.sorter.usage_history.get(str(route), 0)
        assert usage_count == 5


class TestSearchSafetyGuard:
    """Test cases for SearchSafetyGuard."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.guard = SearchSafetyGuard()
    
    def test_validate_safe_content(self):
        """Test validation of safe content."""
        content = "This is safe content for testing"
        report = self.guard.validate_search_result(content)
        
        assert report.verdict == SearchSafetyVerdict.PASS
        assert report.is_safe
        assert not report.pii_detected
        assert len(report.reasons) == 0
    
    def test_validate_pii_content(self):
        """Test validation of content with PII."""
        content = "Contact me at user@example.com or call 555-123-4567"
        report = self.guard.validate_search_result(content)
        
        assert report.verdict == SearchSafetyVerdict.WARN
        assert report.is_safe
        assert report.pii_detected
        assert "email_address" in report.pii_types
        assert "phone_number" in report.pii_types
        assert len(report.reasons) > 0
    
    def test_validate_empty_content(self):
        """Test validation of empty content."""
        content = ""
        report = self.guard.validate_search_result(content)
        
        assert report.verdict == SearchSafetyVerdict.REJECT
        assert not report.is_safe
        assert "empty" in report.reasons[0].lower()
    
    def test_validate_oversized_content(self):
        """Test validation of oversized content."""
        content = "x" * (self.guard.max_content_length + 1)
        report = self.guard.validate_search_result(content)
        
        assert report.verdict == SearchSafetyVerdict.REJECT
        assert not report.is_safe
        assert "exceeds maximum length" in " ".join(report.reasons).lower()
    
    def test_validate_non_string_content(self):
        """Test validation of non-string content."""
        content = 12345
        report = self.guard.validate_search_result(content)  # type: ignore
        
        assert report.verdict == SearchSafetyVerdict.REJECT
        assert not report.is_safe
        assert "must be a string" in " ".join(report.reasons).lower()
    
    def test_pii_detection_types(self):
        """Test PII detection for different types."""
        test_cases = [
            ("email@example.com", ["email_address"]),
            ("123-45-6789", ["social_security_number"]),
            ("555-123-4567", ["phone_number"]),
            ("1234-5678-9012-3456", ["credit_card_number"]),
            ("192.168.1.1", ["ip_address"]),
        ]
        
        for content, expected_types in test_cases:
            detected = self.guard._detect_pii_types(content)
            for expected_type in expected_types:
                assert expected_type in detected
    
    def test_stats_tracking(self):
        """Test statistics tracking."""
        initial_stats = self.guard.stats
        assert initial_stats["checks_performed"] == 0
        
        # Perform some checks
        self.guard.validate_search_result("test content 1")
        self.guard.validate_search_result("test content 2")
        
        updated_stats = self.guard.stats
        assert updated_stats["checks_performed"] == 2
        assert updated_stats["last_check_time"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
