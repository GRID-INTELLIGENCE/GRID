"""Tests for secure compression skill."""


from grid.skills.compress_secure import compress_secure


def test_secure_compress_basic():
    """Test basic secure compression functionality."""
    text = "The company's quarterly earnings exceeded expectations, driving stock prices up 15% in after-hours trading."

    result = compress_secure.handler(
        {
            "text": text,
            "max_chars": 100,
            "security_level": 0.7,
        }
    )

    assert result["status"] == "success"
    assert "output" in result
    assert "security_layer" in result
    assert "semantic_analysis" in result
    assert "security_metadata" in result

    # Check security layer
    security = result["security_layer"]
    assert security["enabled"] is True
    assert "semantic_hash" in security
    assert "compression_signature" in security
    assert security["security_level"] == 0.7

    # Check semantic analysis
    semantic = result["semantic_analysis"]
    assert "entities" in semantic
    assert "relationships" in semantic
    assert "context" in semantic

    # Check compression occurred
    assert len(result["output"]) <= 100
    assert result["security_metadata"]["compression_ratio"] < 1.0


def test_secure_compress_semantic_preservation():
    """Test that semantics are preserved during compression."""
    text = "Neural networks process information through interconnected nodes with weighted connections."

    result = compress_secure.handler(
        {
            "text": text,
            "max_chars": 50,
            "security_level": 0.5,
        }
    )

    assert result["status"] == "success"

    # Check semantic preservation score
    preservation = result["security_metadata"]["semantic_preservation"]
    assert 0.0 <= preservation <= 1.0

    # Check that entities are detected
    semantic = result["semantic_analysis"]
    assert len(semantic["entities"]) > 0


def test_secure_compress_missing_text():
    """Test error handling for missing text."""
    result = compress_secure.handler({})

    assert result["status"] == "error"
    assert "error" in result


def test_secure_compress_different_security_levels():
    """Test compression with different security levels."""
    text = "Information flows through networks creating influence vectors."

    for security_level in [0.3, 0.5, 0.7, 0.9]:
        result = compress_secure.handler(
            {
                "text": text,
                "max_chars": 80,
                "security_level": security_level,
            }
        )

        assert result["status"] == "success"
        assert result["security_layer"]["security_level"] == security_level
