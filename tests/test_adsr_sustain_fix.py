"""
Tests for ADSR sustain phase fix validation.

Ensures the sustain phase maintains quality at sustain_level (0.6)
instead of incorrectly applying decay rate during sustain.
"""

import pytest

from Arena.the_chase.python.src.the_chase.core.adsr_envelope import (
    ADSREnvelope,
    EnvelopePhase,
)
from Arena.the_chase.python.src.the_chase.overwatch.core import OverwatchConfig


class TestADSREnvelopeSustainPhase:
    """Test suite for ADSR sustain phase fix."""

    @pytest.fixture
    def config(self) -> OverwatchConfig:
        """Create test configuration."""
        return OverwatchConfig(
            attack_energy=0.15,
            decay_rate=0.25,
            sustain_level=0.6,
            release_rate=0.3,
            release_threshold=0.05,
        )

    @pytest.fixture
    def envelope(self, config: OverwatchConfig) -> ADSREnvelope:
        """Create ADSR envelope for testing."""
        return ADSREnvelope(config)

    def test_sustain_phase_maintains_quality(self, envelope: ADSREnvelope):
        """Verify sustain phase maintains quality at sustain_level."""
        envelope.update(4.0)  # After attack phase (sustain_start = 0.6)
        assert envelope.quality == 0.6
        assert envelope.phase == EnvelopePhase.SUSTAIN

    def test_sustain_phase_no_decay_applied(self, envelope: ADSREnvelope):
        """Verify decay rate is NOT applied during sustain phase."""
        envelope.update(4.0)  # Enter sustain
        initial_quality = envelope.quality
        envelope.update(10.0)  # Stay in sustain
        assert envelope.quality == initial_quality
        assert envelope.quality == 0.6

    def test_sustain_phase_transition_from_attack(self, envelope: ADSREnvelope):
        """Verify correct transition from attack to sustain."""
        envelope.update(0.1)  # During attack
        assert envelope.phase == EnvelopePhase.ATTACK
        envelope.update(4.0)  # Move to sustain
        assert envelope.phase == EnvelopePhase.SUSTAIN
        assert envelope.quality == 0.6

    def test_quality_not_dropped_during_sustain(self, envelope: ADSREnvelope):
        """Critical test: quality should NOT drop to 0.0 during sustain."""
        envelope.update(4.0)  # Enter sustain
        for _ in range(10):
            envelope.update(4.0 + float(_))
        assert envelope.quality == 0.6
        assert envelope.phase == EnvelopePhase.SUSTAIN

    def test_decay_phase_after_sustain(self, envelope: ADSREnvelope):
        """Verify decay phase works correctly after sustain ends."""
        envelope.update(4.0)  # Enter sustain
        envelope.update(20.0)  # After sustain ends (sustain_end = 15)
        assert envelope.phase == EnvelopePhase.DECAY
        assert envelope.quality < 0.6  # Should start decaying

    def test_release_phase(self, envelope: ADSREnvelope):
        """Verify release phase transitions correctly."""
        envelope.update(4.0)  # Enter sustain
        envelope.update(20.0)  # Enter decay
        assert envelope.phase == EnvelopePhase.DECAY
        # After enough decay, quality drops below threshold
        envelope.update(25.0)
        # Quality should be >= 0
        assert envelope.quality >= 0.0

    def test_attack_phase_quality_increases(self, envelope: ADSREnvelope):
        """Verify attack phase increases quality correctly."""
        envelope.update(0.05)  # Early attack
        assert envelope.phase == EnvelopePhase.ATTACK
        assert envelope.quality > 0.0
        assert envelope.quality <= 0.6

    def test_envelope_initial_state(self, envelope: ADSREnvelope):
        """Verify envelope starts in correct initial state."""
        assert envelope.phase == EnvelopePhase.ATTACK
        assert envelope.quality == 0.0

    def test_sustain_level_configurable(self):
        """Verify sustain_level is configurable."""
        config = OverwatchConfig(sustain_level=0.8)
        envelope = ADSREnvelope(config)
        envelope.update(4.0)
        assert envelope.quality == 0.8

    def test_multiple_sustain_cycles(self, envelope: ADSREnvelope):
        """Verify multiple updates during sustain maintain quality."""
        for i in range(1, 11):
            envelope.update(float(i))
            if envelope.phase == EnvelopePhase.SUSTAIN:
                assert envelope.quality == 0.6


class TestADSREnvelopeEdgeCases:
    """Edge case tests for ADSR envelope."""

    @pytest.fixture
    def config(self) -> OverwatchConfig:
        """Create test configuration."""
        return OverwatchConfig()

    @pytest.fixture
    def envelope(self, config: OverwatchConfig) -> ADSREnvelope:
        """Create ADSR envelope for testing."""
        return ADSREnvelope(config)

    def test_zero_elapsed_time(self, envelope: ADSREnvelope):
        """Verify behavior at zero elapsed time."""
        envelope.update(0.0)
        assert envelope.phase == EnvelopePhase.ATTACK
        assert envelope.quality == 0.0

    def test_negative_elapsed_time(self, envelope: ADSREnvelope):
        """Verify behavior with negative elapsed time."""
        envelope.update(-1.0)
        assert envelope.phase == EnvelopePhase.ATTACK

    def test_zero_sustain_level(self):
        """Verify behavior with zero sustain level."""
        config = OverwatchConfig(sustain_level=0.0)
        envelope = ADSREnvelope(config)
        envelope.update(4.0)
        assert envelope.quality == 0.0

    def test_max_sustain_level(self):
        """Verify behavior with maximum sustain level."""
        config = OverwatchConfig(sustain_level=1.0)
        envelope = ADSREnvelope(config)
        envelope.update(4.0)
        assert envelope.quality == 1.0

    def test_high_decay_rate(self):
        """Verify sustain works with high decay rate."""
        config = OverwatchConfig(decay_rate=1.0)
        envelope = ADSREnvelope(config)
        envelope.update(4.0)  # Enter sustain
        envelope.update(5.0)  # Stay in sustain
        assert envelope.quality == 0.6  # Should NOT decay

    def test_zero_decay_rate(self):
        """Verify sustain with zero decay rate."""
        config = OverwatchConfig(decay_rate=0.0)
        envelope = ADSREnvelope(config)
        envelope.update(4.0)
        assert envelope.quality == 0.6


class TestADSREnvelopePhaseTransitions:
    """Test phase transition logic."""

    @pytest.fixture
    def config(self) -> OverwatchConfig:
        """Create test configuration."""
        return OverwatchConfig()

    @pytest.fixture
    def envelope(self, config: OverwatchConfig) -> ADSREnvelope:
        """Create ADSR envelope for testing."""
        return ADSREnvelope(config)

    def test_attack_phase(self, envelope: ADSREnvelope):
        """Test attack phase."""
        assert envelope.phase == EnvelopePhase.ATTACK
        envelope.update(0.1)
        assert envelope.phase == EnvelopePhase.ATTACK

    def test_sustain_phase(self, envelope: ADSREnvelope):
        """Test sustain phase."""
        envelope.update(4.0)
        assert envelope.phase == EnvelopePhase.SUSTAIN

    def test_decay_phase(self, envelope: ADSREnvelope):
        """Test decay phase."""
        envelope.update(4.0)  # Sustain
        envelope.update(20.0)  # Decay
        assert envelope.phase == EnvelopePhase.DECAY

    def test_complete_lifecycle(self, envelope: ADSREnvelope):
        """Test complete ADSR lifecycle."""
        assert envelope.phase == EnvelopePhase.ATTACK
        envelope.update(0.1)
        assert envelope.phase == EnvelopePhase.ATTACK
        envelope.update(4.0)
        assert envelope.phase == EnvelopePhase.SUSTAIN
        envelope.update(20.0)
        assert envelope.phase == EnvelopePhase.DECAY
