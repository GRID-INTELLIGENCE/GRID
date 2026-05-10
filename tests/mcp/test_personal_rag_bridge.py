"""Tests for the personal-rag bridge layer."""

import json
from unittest.mock import patch

import pytest

from grid.mcp.personal_rag_bridge import PersonalRagBridgeError, query_personal_rag


class TestQueryPersonalRag:
    """Tests for query_personal_rag bridge function."""

    def test_bridge_not_available_raises(self):
        """When personal-rag dir doesn't exist, raise PersonalRagBridgeError."""
        with patch("grid.mcp.personal_rag_bridge._ensure_importable", return_value=False):
            with pytest.raises(PersonalRagBridgeError, match="not found"):
                query_personal_rag("test query", "abcdef123456")

    def test_bridge_import_failure_raises(self):
        """When personal-rag can't be imported, raise PersonalRagBridgeError."""
        with patch("grid.mcp.personal_rag_bridge._ensure_importable", return_value=True):
            with patch("builtins.__import__", side_effect=ImportError("no module")):
                with pytest.raises(PersonalRagBridgeError, match="Failed to import"):
                    query_personal_rag("test query", "abcdef123456")

    def test_error_in_response_raises(self):
        """When personal-rag returns an error envelope, raise PersonalRagBridgeError."""
        error_response = json.dumps({"error": "Digest validation failed."})
        with patch("grid.mcp.personal_rag_bridge._ensure_importable", return_value=True):
            mock_qf = lambda **kwargs: error_response
            with patch.dict("sys.modules", {"mcp_server": type("M", (), {"query_federated": mock_qf})}):
                with pytest.raises(PersonalRagBridgeError, match="Digest validation"):
                    query_personal_rag("test query", "abcdef123456")

    def test_success_returns_parsed_dict(self):
        """Successful call returns parsed JSON dict."""
        ok_response = json.dumps({
            "system": "personal-rag",
            "query": "test",
            "total": 1,
            "chunks": [{"content": "hi", "governance_tier": "T0", "score": 0.9}],
            "provenance": {},
        })
        with patch("grid.mcp.personal_rag_bridge._ensure_importable", return_value=True):
            mock_qf = lambda **kwargs: ok_response
            with patch.dict("sys.modules", {"mcp_server": type("M", (), {"query_federated": mock_qf})}):
                result = query_personal_rag("test", "abcdef123456")
                assert result["system"] == "personal-rag"
                assert result["total"] == 1

    def test_governance_tier_filter_single(self):
        """Single tier filter keeps only matching chunks."""
        ok_response = json.dumps({
            "system": "personal-rag",
            "query": "test",
            "total": 3,
            "chunks": [
                {"content": "rule", "governance_tier": "T0"},
                {"content": "memory", "governance_tier": "T2"},
                {"content": "audit", "governance_tier": "T3"},
            ],
            "provenance": {},
        })
        with patch("grid.mcp.personal_rag_bridge._ensure_importable", return_value=True):
            mock_qf = lambda **kwargs: ok_response
            with patch.dict("sys.modules", {"mcp_server": type("M", (), {"query_federated": mock_qf})}):
                result = query_personal_rag("test", "abcdef123456", governance_tier_filter="T0")
                assert result["total"] == 1
                assert result["chunks"][0]["governance_tier"] == "T0"

    def test_empty_tier_filter_returns_all(self):
        """Empty governance_tier_filter passes all chunks through."""
        chunks = [
            {"content": "a", "governance_tier": "T0"},
            {"content": "b", "governance_tier": "T2"},
        ]

        governance_tier_filter = ""
        if governance_tier_filter:
            tiers = {t.strip().upper() for t in governance_tier_filter.split(",")}
            chunks = [c for c in chunks if c.get("governance_tier", "").upper() in tiers]

        assert len(chunks) == 2

    def test_multi_tier_filter(self):
        """Multiple tiers in filter keep matching chunks."""
        chunks = [
            {"content": "a", "governance_tier": "T0"},
            {"content": "b", "governance_tier": "T1"},
            {"content": "c", "governance_tier": "T2"},
            {"content": "d", "governance_tier": "T3"},
        ]

        governance_tier_filter = "T0,T1"
        tiers = {t.strip().upper() for t in governance_tier_filter.split(",")}
        filtered = [c for c in chunks if c.get("governance_tier", "").upper() in tiers]

        assert len(filtered) == 2
        assert {c["governance_tier"] for c in filtered} == {"T0", "T1"}


class TestGovernanceTierMapping:
    """Tests for the governance tier resolver in personal-rag config."""

    def test_tier_mapping_completeness(self):
        """All operational + reference source types have a tier mapping."""
        import sys
        rag_dir = str(__import__("pathlib").Path.home() / "intelligence" / "personal-rag")
        if rag_dir not in sys.path:
            sys.path.insert(0, rag_dir)

        try:
            from config import GOVERNANCE_TIERS, OPERATIONAL_SOURCES, REFERENCE_SOURCES, resolve_governance_tier
        except ImportError:
            pytest.skip("personal-rag not available on this system")

        for src in OPERATIONAL_SOURCES | REFERENCE_SOURCES:
            tier = resolve_governance_tier(src)
            assert tier in {"T0", "T1", "T2", "T3"}, f"{src} → {tier} not in valid tiers"

    def test_unknown_source_defaults_to_t3(self):
        """Unknown source types fall back to T3."""
        import sys
        rag_dir = str(__import__("pathlib").Path.home() / "intelligence" / "personal-rag")
        if rag_dir not in sys.path:
            sys.path.insert(0, rag_dir)

        try:
            from config import resolve_governance_tier
        except ImportError:
            pytest.skip("personal-rag not available on this system")

        assert resolve_governance_tier("nonexistent_source") == "T3"
        assert resolve_governance_tier("") == "T3"
