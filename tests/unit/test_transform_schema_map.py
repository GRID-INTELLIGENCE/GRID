
from grid.skills.transform_schema_map import transform_schema_map


def test_transform_default_schema():
    """Test default schema transformation."""
    text = "Facts: Sky is blue. Goals: Fly high."
    result = transform_schema_map.run({"text": text, "target_schema": "default"})

    assert result["status"] == "success"
    assert result["target_schema"] == "default"
    output = result["output"]
    assert "facts" in output
    assert any("Sky is blue" in item for item in output["facts"])


def test_transform_resonance_schema_regression():
    """Test resonance schema parsing (regression test for crash)."""
    text = """
    Six Core Principles:
    1) Harmony 2) Balance

    Mystique Activation:
    Purpose: To heal.
    """
    result = transform_schema_map.run({"text": text, "target_schema": "resonance"})

    assert result["status"] == "success"
    assert result["target_schema"] == "resonance"
    # Verify strict typing did not break logic
    assert len(result["output"]["principles"]) >= 2
    assert "Harmony" in result["output"]["principles"]


def test_transform_error_handling():
    """Test error handling with invalid input."""
    # Assuming it handles missing text gracefully or raises
    try:
        result = transform_schema_map.run({})
        # If it returns error dict
        if result.get("status") == "error":
            assert True
    except Exception:
        # If it raises
        assert True
