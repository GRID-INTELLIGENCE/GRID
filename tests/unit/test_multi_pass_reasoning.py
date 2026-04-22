import pytest
import asyncio
from cognition.core.processor import CognitiveProcessor
from cognition.models.core import CognitiveState, ProcessingMode

@pytest.mark.asyncio
async def test_multi_pass_reasoning_complex_pattern():
    processor = CognitiveProcessor()
    
    # Force optimal load for System 2
    processor.metrics.cognitive_load = 4.5
    processor.metrics.attention_level = 0.8
    processor.metrics.decision_confidence = 0.5
    
    # Input that triggers COMPLEX_PATTERN (mocked in detection logic)
    # Since we can't easily mock PatternManager here, we'll manually set patterns
    # or rely on the processor's detect_patterns logic if it finds it.
    
    # We will override _detect_patterns for this test
    async def mock_detect_patterns(input_data):
        return ["COMPLEX_PATTERN"]
    
    processor._detect_patterns = mock_detect_patterns
    
    result = await processor.process_input("Complex architectural problem")
    
    assert result.success
    assert result.pass_count > 1
    assert "full" in result.output["mode"]
    assert "refinement_level" in result.output
    assert result.output["refinement_level"] == result.pass_count
    
    print(f"\nPass Count: {result.pass_count}")
    print(f"Insights: {result.output['insights']}")

@pytest.mark.asyncio
async def test_single_pass_high_confidence():
    processor = CognitiveProcessor()
    
    # Force optimal load for System 2
    processor.metrics.cognitive_load = 4.5
    processor.metrics.attention_level = 0.8
    processor.metrics.decision_confidence = 0.9 # High confidence
    
    async def mock_detect_patterns(input_data):
        return ["SIMPLE_PATTERN"]
    
    processor._detect_patterns = mock_detect_patterns
    
    result = await processor.process_input("Simple task")
    
    assert result.success
    assert result.pass_count == 1
    assert result.output["refinement_level"] == 1
