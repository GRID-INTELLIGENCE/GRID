"""Tests for runtime behavior and artifact management."""

import pytest

from coinbase.runtimebehavior import (
    Artifact,
    collect_diagnostics,
    goldcoin,
    interviewevent,
    refine_completion,
    runtimebehavior,
    search_failure_reasons,
    should_trigger_refinement,
)


def test_goldcoin_creation() -> None:
    """Test goldcoin returns artifact with tier=artifact and value=TOP."""
    artifact = goldcoin()
    assert artifact.tier == "artifact"
    assert artifact.value == "TOP"
    assert artifact.multiplier == 1


def test_artifact_compounding_basic() -> None:
    """Test artifact compounding multiplies value by 10."""
    artifact = Artifact(tier="artifact", value="10", multiplier=1)
    compounded = artifact.compound()
    assert compounded.value == "100"
    assert compounded.multiplier == 10
    assert compounded.tier == "artifact"


def test_artifact_compounding_super_rare() -> None:
    """Test artifact compounding becomes super rare after threshold."""
    artifact = Artifact(tier="artifact", value="10", multiplier=10)
    compounded = artifact.compound()
    assert compounded.tier == "super rare"
    assert compounded.multiplier == 100


def test_artifact_compounding_string_value() -> None:
    """Test artifact compounding preserves string values."""
    artifact = Artifact(tier="artifact", value="TOP", multiplier=1)
    compounded = artifact.compound()
    assert compounded.value == "TOP"
    assert compounded.multiplier == 10


def test_runtimebehavior_logging(capsys: pytest.CaptureFixture[str]) -> None:
    """Test runtimebehavior logs correctly."""
    artifact = goldcoin()
    behavior = runtimebehavior(
        batch_name="First Batch",
        test_count=8,
        passed=8,
        color="green",
        retries=1,
        artifact=artifact,
    )
    captured = capsys.readouterr()
    assert "First Batch" in captured.out
    assert "pass(all)" in captured.out
    assert "color=green" in captured.out
    assert "retries=1" in captured.out
    assert behavior["status"] == "pass(all)"


def test_runtimebehavior_partial_pass(capsys: pytest.CaptureFixture[str]) -> None:
    """Test runtimebehavior with partial pass."""
    artifact = goldcoin()
    behavior = runtimebehavior(
        batch_name="Second Batch",
        test_count=10,
        passed=7,
        color="yellow",
        retries=0,
        artifact=artifact,
    )
    captured = capsys.readouterr()
    assert "pass(7/10)" in captured.out
    assert behavior["status"] == "pass(7/10)"


def test_interviewevent_prompt_only() -> None:
    """Test interviewevent returns prompt without answer."""
    prompt, answer = interviewevent()
    assert "do you want to save progress" in prompt
    assert answer is None


def test_interviewevent_with_answer_fetcher() -> None:
    """Test interviewevent with answer fetcher."""

    def mock_fetch() -> str:
        return "build on the momentup right away"

    prompt, answer = interviewevent(answer_fetcher=mock_fetch)
    assert "do you want to save progress" in prompt
    assert answer == "build on the momentup right away"


def test_interviewevent_custom_prompt() -> None:
    """Test interviewevent with custom prompt."""
    custom_prompt = "custom question?"
    prompt, answer = interviewevent(prompt=custom_prompt)
    assert prompt == custom_prompt
    assert answer is None


def test_artifact_with_metadata() -> None:
    """Test artifact with batch and retries metadata."""
    artifact = Artifact(
        tier="artifact",
        value="TOP",
        multiplier=1,
        batch="First Batch",
        retries=1,
    )
    assert artifact.batch == "First Batch"
    assert artifact.retries == 1
    compounded = artifact.compound()
    assert compounded.batch == "First Batch"
    assert compounded.retries == 1


def test_tier_hierarchy_levels() -> None:
    """Test tier level hierarchy."""
    artifact_top = Artifact(tier="TOP", value="100")
    artifact_artifact = Artifact(tier="artifact", value="100")
    artifact_gold = Artifact(tier="gold", value="100")
    artifact_silver = Artifact(tier="silver", value="100")
    artifact_bronze = Artifact(tier="bronze", value="100")

    assert artifact_top.tier_level() == 5
    assert artifact_artifact.tier_level() == 4
    assert artifact_gold.tier_level() == 3
    assert artifact_silver.tier_level() == 2
    assert artifact_bronze.tier_level() == 1


def test_is_silver_or_lower() -> None:
    """Test silver or lower detection."""
    artifact_silver = Artifact(tier="silver", value="100")
    artifact_bronze = Artifact(tier="bronze", value="100")
    artifact_gold = Artifact(tier="gold", value="100")

    assert artifact_silver.is_silver_or_lower() is True
    assert artifact_bronze.is_silver_or_lower() is True
    assert artifact_gold.is_silver_or_lower() is False


def test_collect_diagnostics() -> None:
    """Test diagnostics collection."""
    errors = ["AssertionError: test failed"]
    warnings = ["deprecated feature"]
    verbose_info = ["INFO: running test"]
    test_results = {"test1": "passed", "test2": "failed"}

    diagnostics = collect_diagnostics(errors, warnings, verbose_info, test_results)
    assert diagnostics["errors"] == errors
    assert diagnostics["warnings"] == warnings
    assert diagnostics["verbose_info"] == verbose_info
    assert diagnostics["test_results"] == test_results


def test_search_failure_reasons() -> None:
    """Test web search placeholder."""
    query = "test assertion error"
    results = search_failure_reasons(query)
    assert len(results) == 3
    assert query in results[0]


def test_refine_completion_with_errors() -> None:
    """Test refinement with assertion errors."""
    code_context = "def test_example(): assert True"
    diagnostics = {
        "errors": ["AssertionError: expected True but got False"],
        "warnings": [],
        "verbose_info": [],
        "test_results": {},
    }
    search_results = ["Check test assertions"]

    refined = refine_completion(code_context, diagnostics, search_results)
    assert refined["state"] == "refined"
    assert "Review test assertions for correctness" in refined["suggestions"]


def test_refine_completion_with_warnings() -> None:
    """Test refinement with deprecation warnings."""
    code_context = "import old_module"
    diagnostics = {
        "errors": [],
        "warnings": ["deprecated: old_module is deprecated"],
        "verbose_info": [],
        "test_results": {},
    }
    search_results = []

    refined = refine_completion(code_context, diagnostics, search_results)
    assert "Update deprecated API usage" in refined["suggestions"]


def test_should_trigger_refinement() -> None:
    """Test refinement trigger conditions."""
    artifact_silver = Artifact(tier="silver", value="100")
    artifact_gold = Artifact(tier="gold", value="100")

    # Should trigger: more than 1 test AND silver or lower
    assert should_trigger_refinement(2, artifact_silver) is True

    # Should not trigger: only 1 test
    assert should_trigger_refinement(1, artifact_silver) is False

    # Should not trigger: gold tier (higher than silver)
    assert should_trigger_refinement(2, artifact_gold) is False


def test_refine_completion_multiple_errors() -> None:
    """Test refinement with multiple error types."""
    diagnostics = {
        "errors": [
            "AssertionError: test failed",
            "ImportError: module not found",
            "RuntimeError: scope not enabled",
        ],
        "warnings": [],
        "verbose_info": [],
        "test_results": {},
    }

    refined = refine_completion("", diagnostics, [])
    assert len(refined["suggestions"]) == 3
    assert "Review test assertions for correctness" in refined["suggestions"]
    assert "Check module imports and dependencies" in refined["suggestions"]
    assert "Verify runtime conditions and state" in refined["suggestions"]
