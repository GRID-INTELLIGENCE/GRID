"""
Tests for ADSR sustain phase fix validation.

Ensures the sustain phase maintains quality at sustain_level (0.6)
instead of incorrectly applying decay rate during sustain.

ArenaADSREnvelope phase boundaries (default OverwatchConfig):
  attack_time=0.15, decay_time=0.25, sustain_level=0.6,
  sustain_time=1.0, release_time=0.3
  Attack:  0.00 – 0.15
  Decay:   0.15 – 0.40
  Sustain: 0.40 – 1.40
  Release: auto-triggered at 1.40, lasts 0.3s
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
        """Create ADSR envelope triggered at t=0 for testing."""
        env = ADSREnvelope(config)
        env.trigger(current_time=0.0)
        return env

    def test_sustain_phase_maintains_quality(self, envelope: ADSREnvelope):
        """Verify sustain phase maintains quality at sustain_level."""
        envelope.update(0.5)  # Within sustain phase (0.40–1.40)
        assert envelope.quality == 0.6
        assert envelope.phase == EnvelopePhase.SUSTAIN

    def test_sustain_phase_no_decay_applied(self, envelope: ADSREnvelope):
        """Verify decay rate is NOT applied during sustain phase."""
        envelope.update(0.5)  # Enter sustain (0.40–1.40)
        initial_quality = envelope.quality
        envelope.update(1.0)  # Stay in sustain
        assert envelope.quality == initial_quality
        assert envelope.quality == 0.6

    def test_sustain_phase_transition_from_attack(self, envelope: ADSREnvelope):
        """Verify correct transition from attack to sustain."""
        envelope.update(0.1)  # During attack (< 0.15)
        assert envelope.phase == EnvelopePhase.ATTACK
        envelope.update(0.5)  # Move to sustain (0.40–1.40)
        assert envelope.phase == EnvelopePhase.SUSTAIN
        assert envelope.quality == 0.6

    def test_quality_not_dropped_during_sustain(self, envelope: ADSREnvelope):
        """Critical test: quality should NOT drop to 0.0 during sustain."""
        envelope.update(0.5)  # Enter sustain
        for i in range(10):
            envelope.update(0.5 + float(i) * 0.09)  # 0.5 to 1.31, all in sustain
        assert envelope.quality == 0.6
        assert envelope.phase == EnvelopePhase.SUSTAIN

    def test_release_after_sustain(self, envelope: ADSREnvelope):
        """Verify release phase after sustain ends."""
        envelope.update(0.5)  # Enter sustain
        assert envelope.phase == EnvelopePhase.SUSTAIN
        envelope.release(current_time=1.0)  # Explicitly start release
        envelope.update(1.1)  # During release (release_time=0.3)
        assert envelope.phase == EnvelopePhase.RELEASE
        assert envelope.quality < 0.6

    def test_release_completes(self, envelope: ADSREnvelope):
        """Verify release phase completes and envelope goes idle."""
        envelope.update(0.5)  # Sustain
        envelope.release(current_time=1.0)
        envelope.update(1.4)  # Past release end (1.0 + 0.3 = 1.3)
        assert envelope.phase == EnvelopePhase.IDLE
        assert envelope.quality == 0.0

    def test_attack_phase_quality_increases(self, envelope: ADSREnvelope):
        """Verify attack phase increases quality correctly."""
        envelope.update(0.05)  # Early attack (< 0.15)
        assert envelope.phase == EnvelopePhase.ATTACK
        assert envelope.quality > 0.0
        assert envelope.quality <= 0.6

    def test_envelope_initial_state(self):
        """Verify envelope starts in correct initial state."""
        config = OverwatchConfig(sustain_level=0.6)
        env = ADSREnvelope(config)
        # Before trigger: IDLE
        assert env.phase == EnvelopePhase.IDLE
        assert env.quality == 0.0
        # After trigger: ATTACK at amplitude 0.0
        env.trigger(current_time=0.0)
        assert env.phase == EnvelopePhase.ATTACK
        assert env.quality == 0.0

    def test_sustain_level_configurable(self):
        """Verify sustain_level is configurable."""
        config = OverwatchConfig(sustain_level=0.8)
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        envelope.update(0.5)  # Within sustain phase
        assert envelope.quality == 0.8

    def test_multiple_sustain_cycles(self, envelope: ADSREnvelope):
        """Verify multiple updates during sustain maintain quality."""
        for i in range(10):
            t = 0.4 + float(i) * 0.1  # 0.4, 0.5, ..., 1.3 — all in sustain
            envelope.update(t)
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
        """Create ADSR envelope triggered at t=0 for testing."""
        env = ADSREnvelope(config)
        env.trigger(current_time=0.0)
        return env

    def test_zero_elapsed_time(self, envelope: ADSREnvelope):
        """Verify behavior at zero elapsed time."""
        envelope.update(0.0)
        assert envelope.phase == EnvelopePhase.ATTACK
        assert envelope.quality == 0.0

    def test_negative_elapsed_time(self, envelope: ADSREnvelope):
        """Verify behavior with negative elapsed time (clamped to zero)."""
        envelope.update(-1.0)
        assert envelope.phase == EnvelopePhase.ATTACK

    def test_zero_sustain_level(self):
        """Verify behavior with zero sustain level."""
        config = OverwatchConfig(sustain_level=0.0)
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        envelope.update(0.5)  # Sustain phase
        assert envelope.quality == 0.0

    def test_max_sustain_level(self):
        """Verify behavior with maximum sustain level."""
        config = OverwatchConfig(sustain_level=1.0)
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        envelope.update(0.5)  # Sustain phase
        assert envelope.quality == 1.0

    def test_high_decay_rate(self):
        """Verify sustain works with high decay rate."""
        config = OverwatchConfig(decay_rate=1.0)
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        # decay_time=1.0 → sustain starts at 1.15, ends at 2.15
        envelope.update(1.5)  # Enter sustain
        envelope.update(2.0)  # Stay in sustain
        assert envelope.quality == 0.6  # Should NOT decay

    def test_zero_decay_rate(self):
        """Verify sustain with zero decay rate."""
        config = OverwatchConfig(decay_rate=0.0)
        envelope = ADSREnvelope(config)
        envelope.trigger(current_time=0.0)
        # decay_time=0.0 → sustain starts at 0.15, ends at 1.15
        envelope.update(0.5)
        assert envelope.quality == 0.6


class TestADSREnvelopePhaseTransitions:
    """Test phase transition logic."""

    @pytest.fixture
    def config(self) -> OverwatchConfig:
        """Create test configuration."""
        return OverwatchConfig()

    @pytest.fixture
    def envelope(self, config: OverwatchConfig) -> ADSREnvelope:
        """Create ADSR envelope triggered at t=0 for testing."""
        env = ADSREnvelope(config)
        env.trigger(current_time=0.0)
        return env

    def test_attack_phase(self, envelope: ADSREnvelope):
        """Test attack phase."""
        assert envelope.phase == EnvelopePhase.ATTACK
        envelope.update(0.1)
        assert envelope.phase == EnvelopePhase.ATTACK

    def test_decay_phase(self, envelope: ADSREnvelope):
        """Test decay phase (between attack and sustain)."""
        envelope.update(0.2)  # In decay range (0.15–0.40)
        assert envelope.phase == EnvelopePhase.DECAY

    def test_sustain_phase(self, envelope: ADSREnvelope):
        """Test sustain phase."""
        envelope.update(0.5)  # In sustain range (0.40–1.40)
        assert envelope.phase == EnvelopePhase.SUSTAIN

    def test_complete_lifecycle(self, envelope: ADSREnvelope):
        """Test complete ADSR lifecycle: Attack → Decay → Sustain → Release."""
        assert envelope.phase == EnvelopePhase.ATTACK
        envelope.update(0.1)
        assert envelope.phase == EnvelopePhase.ATTACK
        envelope.update(0.2)
        assert envelope.phase == EnvelopePhase.DECAY
        envelope.update(0.5)
        assert envelope.phase == EnvelopePhase.SUSTAIN
        envelope.release(current_time=1.0)
        envelope.update(1.1)
        assert envelope.phase == EnvelopePhase.RELEASE
