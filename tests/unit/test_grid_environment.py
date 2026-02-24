"""Unit tests for the GRID Environmental Intelligence Engine.

Validates the homeostatic triad-balancing mechanism: keyword sensing,
Le Chatelier recalibration, API payload generation, LLM proxy integration,
and audit trail.

Structure: 9 test classes, ~38 tests.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from grid.agentic.grid_environment import (
    ArenaAmbiance,
    EnvironmentalLLMProxy,
    GridDimension,
    GridEnvironment,
)

# ---------------------------------------------------------------------------
# 1. GridDimension enum
# ---------------------------------------------------------------------------


class TestGridDimension:
    def test_enum_has_three_members(self) -> None:
        assert len(GridDimension) == 3

    def test_enum_values_are_strings(self) -> None:
        for dim in GridDimension:
            assert isinstance(dim.value, str)
        assert GridDimension.PRACTICAL.value == "practical"
        assert GridDimension.LEGAL.value == "legal"
        assert GridDimension.PSYCHOLOGICAL.value == "psychological"


# ---------------------------------------------------------------------------
# 2. ArenaAmbiance data class
# ---------------------------------------------------------------------------


class TestArenaAmbiance:
    def test_default_values(self) -> None:
        a = ArenaAmbiance()
        assert a.reverb_temperature == 0.5
        assert a.quantization_drift == 0.2
        assert a.hologram_density == 0.5

    def test_custom_values(self) -> None:
        a = ArenaAmbiance(
            reverb_temperature=0.9,
            quantization_drift=0.6,
            hologram_density=0.1,
            active_nudge="custom",
        )
        assert a.reverb_temperature == 0.9
        assert a.quantization_drift == 0.6
        assert a.hologram_density == 0.1
        assert a.active_nudge == "custom"

    def test_nudge_default_text(self) -> None:
        a = ArenaAmbiance()
        assert "synthesize" in a.active_nudge.lower()


# ---------------------------------------------------------------------------
# 3. Lexicon sensor (_sense)
# ---------------------------------------------------------------------------


class TestLexiconSensor:
    def test_practical_keywords_detected(self) -> None:
        env = GridEnvironment()
        env._scan_lexicon("launch the app fast to market for revenue users")
        assert env._weights[GridDimension.PRACTICAL] > 0.0

    def test_legal_keywords_detected(self) -> None:
        env = GridEnvironment()
        env._scan_lexicon("protect the IP with legal ownership and secure locks")
        assert env._weights[GridDimension.LEGAL] > 0.0

    def test_psychological_keywords_detected(self) -> None:
        env = GridEnvironment()
        env._scan_lexicon("wellness and balance create collective impact on mindset")
        assert env._weights[GridDimension.PSYCHOLOGICAL] > 0.0

    def test_case_insensitive_matching(self) -> None:
        env = GridEnvironment()
        env._scan_lexicon("REVENUE Market LAUNCH")
        assert env._weights[GridDimension.PRACTICAL] > 0.0

    def test_no_keywords_returns_zero_weights(self) -> None:
        env = GridEnvironment()
        env._scan_lexicon("hello world this is a random string")
        assert all(w == 0.0 for w in env._weights.values())

    def test_multi_keyword_frequency_counting(self) -> None:
        """Multiple occurrences of the same keyword add up."""
        env = GridEnvironment()
        env._scan_lexicon("revenue revenue revenue")
        # 3 hits × 0.1 increment = 0.3
        assert abs(env._weights[GridDimension.PRACTICAL] - 0.3) < 1e-9

    def test_mixed_dimension_keywords(self) -> None:
        env = GridEnvironment()
        env._scan_lexicon("revenue protect wellness")
        assert env._weights[GridDimension.PRACTICAL] > 0.0
        assert env._weights[GridDimension.LEGAL] > 0.0
        assert env._weights[GridDimension.PSYCHOLOGICAL] > 0.0

    def test_punctuation_adjacent_keywords(self) -> None:
        """Keywords attached to punctuation are NOT matched (split on whitespace)."""
        env = GridEnvironment()
        env._scan_lexicon("revenue, protect! wellness.")
        # "revenue," != "revenue" — the simple split won't strip punctuation
        assert env._weights[GridDimension.PRACTICAL] == 0.0
        assert env._weights[GridDimension.LEGAL] == 0.0
        assert env._weights[GridDimension.PSYCHOLOGICAL] == 0.0


# ---------------------------------------------------------------------------
# 4. Weight accumulation
# ---------------------------------------------------------------------------


class TestWeightAccumulation:
    def test_single_wave_increments_by_point_one(self) -> None:
        env = GridEnvironment()
        env.process_wave("revenue")
        assert abs(env.get_weights()["practical"] - 0.1) < 1e-9

    def test_weights_are_cumulative_across_waves(self) -> None:
        env = GridEnvironment()
        env.process_wave("revenue market")
        first = env.get_weights()["practical"]

        env.process_wave("launch users deploy")
        second = env.get_weights()["practical"]
        assert second > first

    def test_absent_dimensions_remain_zero(self) -> None:
        env = GridEnvironment()
        env.process_wave("revenue market launch")
        w = env.get_weights()
        assert w["legal"] == 0.0
        assert w["psychological"] == 0.0


# ---------------------------------------------------------------------------
# 5. Recalibration (Le Chatelier)
# ---------------------------------------------------------------------------


class TestRecalibration:
    def test_legal_dominance_raises_temperature_and_drift(self) -> None:
        """Legal > Psych + threshold AND Legal > Practical + threshold
        → temperature 0.7, drift 0.4, nudge toward psychological."""
        env = GridEnvironment()
        payload = env.process_wave("protect legal ownership defend ip secure lock compliance")
        params = payload["llm_parameters"]
        assert params["temperature"] == 0.7
        # drift 0.4 → top_p = max(0.1, 1.0 - 0.4) = 0.6
        assert params["top_p"] == 0.6
        nudge = payload["system_instruction"].lower()
        assert "mental" in nudge or "routine" in nudge

    def test_practical_dominance_raises_density(self) -> None:
        """Practical > Legal + threshold AND Practical > Psych + threshold
        → density 0.8 → low top_k, nudge toward legal + psychological."""
        env = GridEnvironment()
        payload = env.process_wave("launch app fast revenue market users deploy ship execute")
        params = payload["llm_parameters"]
        # density 0.8 → top_k = int(40 * (1.1 - 0.8)) = int(12) = 12
        assert params["top_k"] == 12
        nudge = payload["system_instruction"].lower()
        assert "defensive" in nudge or "psychological" in nudge

    def test_psychological_dominance_lowers_temperature(self) -> None:
        """Psych > Practical + threshold AND Psych > Legal + threshold
        → temperature 0.3, density 0.9, nudge toward practical."""
        env = GridEnvironment()
        payload = env.process_wave("wellness mindset balance routine impact collective empathy trust")
        params = payload["llm_parameters"]
        assert params["temperature"] == 0.3
        # density 0.9 → top_k = int(40 * (1.1 - 0.9)) = int(8) = 8
        assert params["top_k"] == 8
        nudge = payload["system_instruction"].lower()
        assert "executable" in nudge or "market" in nudge

    def test_balanced_state_resets_to_baseline(self) -> None:
        env = GridEnvironment()
        payload = env.process_wave("hello random topic with no keywords")
        params = payload["llm_parameters"]
        assert params["temperature"] == 0.5
        assert env.get_shifts() == []

    def test_threshold_boundary_exact_point_two_gap(self) -> None:
        """When the gap is exactly 0.2 the condition (strictly >) should NOT fire."""
        env = GridEnvironment()
        # Manually set weights so legal - practical == 0.2 exactly
        env._weights[GridDimension.LEGAL] = 0.4
        env._weights[GridDimension.PRACTICAL] = 0.2
        env._weights[GridDimension.PSYCHOLOGICAL] = 0.2
        env._recalibrate()
        # Should remain at baseline because 0.4 > 0.2 + 0.2 is 0.4 > 0.4 → False
        assert env._ambiance.reverb_temperature == 0.5

    def test_below_threshold_no_shift(self) -> None:
        """Small imbalance (< 0.2) should not trigger recalibration."""
        env = GridEnvironment()
        env._weights[GridDimension.LEGAL] = 0.3
        env._weights[GridDimension.PRACTICAL] = 0.2
        env._weights[GridDimension.PSYCHOLOGICAL] = 0.2
        env._recalibrate()
        assert env._ambiance.reverb_temperature == 0.5


# ---------------------------------------------------------------------------
# 6. API output structure
# ---------------------------------------------------------------------------


class TestApiOutput:
    def test_output_contains_required_keys(self) -> None:
        env = GridEnvironment()
        payload = env.process_wave("test")
        assert "llm_parameters" in payload
        assert "system_instruction" in payload
        assert "internal_state_weights" in payload

    def test_llm_parameters_structure(self) -> None:
        env = GridEnvironment()
        params = env.process_wave("test")["llm_parameters"]
        assert "temperature" in params
        assert "top_p" in params
        assert "presence_penalty" in params
        assert "top_k" in params

    def test_top_p_clamped_to_minimum(self) -> None:
        """top_p should never go below 0.1 even with extreme drift."""
        env = GridEnvironment()
        env._ambiance.quantization_drift = 1.0
        payload = env._generate_api_output()
        assert payload["llm_parameters"]["top_p"] >= 0.1

    def test_top_k_is_integer(self) -> None:
        env = GridEnvironment()
        payload = env.process_wave("revenue market launch")
        assert isinstance(payload["llm_parameters"]["top_k"], int)

    def test_values_properly_rounded(self) -> None:
        env = GridEnvironment()
        payload = env.process_wave("test")
        params = payload["llm_parameters"]
        for key in ("temperature", "top_p", "presence_penalty"):
            val = params[key]
            assert val == round(val, 2)

    def test_system_instruction_contains_nudge(self) -> None:
        env = GridEnvironment()
        payload = env.process_wave("test")
        assert "Current room constraint:" in payload["system_instruction"]

    def test_internal_weights_has_all_dimensions(self) -> None:
        env = GridEnvironment()
        payload = env.process_wave("test")
        w = payload["internal_state_weights"]
        assert "practical" in w
        assert "legal" in w
        assert "psychological" in w


# ---------------------------------------------------------------------------
# 7. Homeostatic simulation
# ---------------------------------------------------------------------------


class TestHomeostasis:
    def test_three_turn_simulation_sequence(self) -> None:
        """Replicate the design spec 3-turn demo:
        Turn 1: Practical dominance → density 0.8
        Turn 2: Legal dominance → temperature 0.7
        Turn 3: Psychological introduced → rebalancing
        """
        env = GridEnvironment()

        # Turn 1 — Practical blast
        p1 = env.process_wave("launch the app fast to secure market users and liquid revenue")
        assert p1["llm_parameters"]["top_k"] == 12  # density 0.8

        # Turn 2 — Legal blast (must overcome accumulated practical weight)
        p2 = env.process_wave(
            "protect legal ownership defend ip secure lock compliance "
            "regulation patent trademark license liability contract audit enforce"
        )
        # After accumulation, legal should dominate over the others
        assert p2["llm_parameters"]["temperature"] == 0.7

        # Turn 3 — Psychological wave introduces balance
        env.process_wave("we lose the core wellness impact on mindset and collective balance")
        # After adding psychological weight, the system may rebalance or
        # shift to a new dominant; verify the engine actually processed it
        w = env.get_weights()
        assert w["psychological"] > 0.0

    def test_counterbalancing_input_restores_equilibrium(self) -> None:
        """Feed dominant text, then counterbalance. The system should
        return toward baseline ambiance."""
        env = GridEnvironment()
        env.process_wave("revenue market launch users app fast deploy ship execute")
        # Practical dominates — density at 0.8
        assert env._ambiance.hologram_density == 0.8

        # Now counterbalance with legal + psychological
        env.process_wave("protect wellness compliance balance mindset legal secure trust")
        # Should return toward baseline
        assert env._ambiance.reverb_temperature == 0.5

    def test_extreme_single_dimension_dominance(self) -> None:
        """Flood one dimension — engine must still recalibrate."""
        env = GridEnvironment()
        env.process_wave(
            "revenue revenue revenue revenue market market market launch launch users users users deploy deploy ship"
        )
        shifts = env.get_shifts()
        assert len(shifts) >= 1
        assert shifts[0].dominant_dimension == "practical"


# ---------------------------------------------------------------------------
# 8. Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_string_input(self) -> None:
        env = GridEnvironment()
        payload = env.process_wave("")
        assert payload["llm_parameters"]["temperature"] == 0.5
        assert all(v == 0.0 for v in env.get_weights().values())

    def test_input_with_no_recognized_keywords(self) -> None:
        env = GridEnvironment()
        payload = env.process_wave("the quick brown fox jumps over the lazy dog")
        assert payload["llm_parameters"]["temperature"] == 0.5

    def test_repeated_single_keyword(self) -> None:
        env = GridEnvironment()
        env.process_wave("revenue " * 20)
        w = env.get_weights()
        assert w["practical"] == pytest.approx(2.0, abs=1e-9)


# ---------------------------------------------------------------------------
# 9. EnvironmentalLLMProxy
# ---------------------------------------------------------------------------


def _make_mock_llm() -> MagicMock:
    """Create a MagicMock that mimics BaseLLMProvider."""
    mock = MagicMock()
    mock.generate.return_value = "mocked response"
    mock.stream.return_value = iter(["mocked", " stream"])
    mock.async_generate = AsyncMock(return_value="async mocked response")
    mock.async_stream = AsyncMock(return_value=iter(["async", " stream"]))
    return mock


class TestEnvironmentalLLMProxy:
    def test_proxy_calls_inner_llm_generate(self) -> None:
        llm = _make_mock_llm()
        env = GridEnvironment()
        proxy = EnvironmentalLLMProxy(llm, env)

        result = proxy.generate("hello world")
        assert result == "mocked response"
        llm.generate.assert_called_once()

    def test_proxy_overrides_temperature_from_environment(self) -> None:
        llm = _make_mock_llm()
        env = GridEnvironment()
        proxy = EnvironmentalLLMProxy(llm, env)

        # Feed practical-dominant text → temperature stays 0.5 (practical path)
        proxy.generate("launch app fast revenue market users deploy ship execute")
        _, kwargs = llm.generate.call_args
        # Practical dominance: temperature unchanged at 0.5
        assert kwargs["temperature"] == 0.5

    def test_proxy_prepends_nudge_to_system_message(self) -> None:
        llm = _make_mock_llm()
        env = GridEnvironment()
        proxy = EnvironmentalLLMProxy(llm, env)

        proxy.generate("hello world", system="You are helpful.")
        _, kwargs = llm.generate.call_args
        system_msg = kwargs["system"]
        # Nudge should be prepended before the original system message
        assert "Current room constraint:" in system_msg
        assert "You are helpful." in system_msg
        # Nudge comes first
        nudge_pos = system_msg.index("Current room constraint:")
        original_pos = system_msg.index("You are helpful.")
        assert nudge_pos < original_pos

    def test_proxy_preserves_original_system_when_no_nudge_shift(self) -> None:
        """Even with neutral text, the default nudge is prepended."""
        llm = _make_mock_llm()
        env = GridEnvironment()
        proxy = EnvironmentalLLMProxy(llm, env)

        proxy.generate("neutral text", system="Original system.")
        _, kwargs = llm.generate.call_args
        assert "Original system." in kwargs["system"]
        assert "Current room constraint:" in kwargs["system"]

    def test_proxy_processes_wave_before_each_call(self) -> None:
        """Verify that environment.process_wave is called on each generate."""
        llm = _make_mock_llm()
        env = GridEnvironment()
        proxy = EnvironmentalLLMProxy(llm, env)

        proxy.generate("revenue market launch")
        w1 = env.get_weights()["practical"]
        assert w1 > 0.0

        proxy.generate("more revenue and users")
        w2 = env.get_weights()["practical"]
        assert w2 > w1  # weights accumulated

    def test_proxy_multi_turn_adjusts_progressively(self) -> None:
        """Multi-turn calls cause progressive parameter shifts."""
        llm = _make_mock_llm()
        env = GridEnvironment()
        proxy = EnvironmentalLLMProxy(llm, env)

        # Turn 1 — practical dominance
        proxy.generate("launch app fast revenue market users deploy ship execute")
        call1_kwargs = llm.generate.call_args[1]
        temp1 = call1_kwargs["temperature"]

        # Turn 2 — legal dominance should shift temperature
        proxy.generate("protect legal ownership defend ip secure lock compliance governance audit enforce")
        call2_kwargs = llm.generate.call_args[1]
        temp2 = call2_kwargs["temperature"]

        # The two calls should produce different parameters
        assert temp1 != temp2 or call1_kwargs["system"] != call2_kwargs["system"]

    def test_proxy_passthrough_stream(self) -> None:
        """Stream delegates directly to the inner LLM."""
        llm = _make_mock_llm()
        env = GridEnvironment()
        proxy = EnvironmentalLLMProxy(llm, env)

        result = proxy.stream("hello", system="sys", temperature=0.8)
        llm.stream.assert_called_once_with("hello", system="sys", temperature=0.8)
        assert result is llm.stream.return_value

    @pytest.mark.asyncio
    async def test_proxy_passthrough_async_generate(self) -> None:
        """Async generate delegates directly to the inner LLM."""
        llm = _make_mock_llm()
        env = GridEnvironment()
        proxy = EnvironmentalLLMProxy(llm, env)

        result = await proxy.async_generate("hello", system="sys")
        llm.async_generate.assert_called_once()
        assert result == "async mocked response"
