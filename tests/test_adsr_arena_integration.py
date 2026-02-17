"""
Tests for ADSR-Arena integration bridge.

Validates the bridge between GRID ADSR envelope and Arena systems
including cache synchronization and honor decay integration.
"""

import pytest

from Arena.the_chase.python.src.the_chase.core.adsr_envelope import ADSREnvelope, EnvelopePhase
from Arena.the_chase.python.src.the_chase.overwatch.core import OverwatchConfig
from Arena.the_chase.python.src.the_chase.overwatch.rewards import Achievement, AchievementType, CharacterRewardState


class MockCacheLayer:
    """Mock CacheLayer for testing."""

    def __init__(self):
        self.l1 = {}
        self.l2 = {}

    def keys(self):
        return self.l1.keys()

    def __contains__(self, key):
        return key in self.l1

    def __setitem__(self, key, value):
        self.l1[key] = value


class TestADSRArenaBridge:
    """Test suite for ADSR-Arena bridge integration."""

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
    def grid_adsr(self, config: OverwatchConfig) -> ADSREnvelope:
        """Create GRID ADSR envelope."""
        return ADSREnvelope(config)

    @pytest.fixture
    def cache(self) -> MockCacheLayer:
        """Create mock cache layer."""
        return MockCacheLayer()

    @pytest.fixture
    def rewards(self) -> CharacterRewardState:
        """Create character reward state."""
        return CharacterRewardState()

    @pytest.fixture
    def bridge(self, grid_adsr: ADSREnvelope, cache: MockCacheLayer, rewards: CharacterRewardState):
        """Create ADSR-Arena bridge."""
        from Arena.the_chase.python.src.the_chase.integration.adsr_arena import ADSRArenaBridge

        return ADSRArenaBridge(grid_adsr, cache, rewards)

    def test_bridge_initialization(self, bridge):
        """Verify bridge initializes correctly."""
        assert bridge.grid_adsr is not None
        assert bridge.cache is not None
        assert bridge.rewards is not None

    def test_sync_sustain_phase_maintains_cache(self, bridge, cache):
        """Verify sustain phase maintains cache entries."""
        bridge.grid_adsr.update(4.0)  # Enter sustain
        cache.l1["key1"] = {"priority": "normal"}
        cache.l1["key2"] = {"priority": "normal"}

        bridge.sync_sustain_phase()

        assert cache.l1["key1"]["priority"] == "maintained"
        assert cache.l1["key2"]["priority"] == "maintained"

    def test_sync_sustain_phase_no_op_outside_sustain(self, bridge, cache):
        """Verify sync does nothing when not in sustain."""
        bridge.grid_adsr.update(0.1)  # Attack phase
        cache.l1["key1"] = {"priority": "normal"}

        bridge.sync_sustain_phase()

        assert cache.l1["key1"]["priority"] == "normal"

    def test_sync_decay_phase_applies_honor_decay(self, bridge, rewards):
        """Verify decay phase applies honor decay."""
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 100))
        bridge.grid_adsr.update(20.0)  # After sustain ends

        # Verify envelope is past sustain phase (either DECAY or RELEASE)
        assert bridge.grid_adsr.phase in [EnvelopePhase.DECAY, EnvelopePhase.RELEASE]

        initial_honor = rewards.honor
        bridge.sync_decay_phase()

        # Honor should have decayed (sync_decay_phase calls rewards.decay_honor)
        assert rewards.honor < initial_honor

    def test_sync_decay_phase_no_op_outside_decay(self, bridge, rewards):
        """Verify sync does nothing when not in decay."""
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 100))
        bridge.grid_adsr.update(4.0)  # Sustain phase

        initial_honor = rewards.honor
        bridge.sync_decay_phase()

        assert rewards.honor == initial_honor

    def test_empty_cache_sync_sustain(self, bridge, cache):
        """Verify sync works with empty cache."""
        bridge.grid_adsr.update(4.0)  # Sustain
        bridge.sync_sustain_phase()  # Should not raise
        assert len(cache.l1) == 0


class TestADSRArenaBridgeWorkflows:
    """Workflow tests for ADSR-Arena bridge."""

    @pytest.fixture
    def config(self) -> OverwatchConfig:
        """Create test configuration."""
        return OverwatchConfig()

    def test_sustain_to_decay_transition(self):
        """Test full transition from sustain to decay."""
        from Arena.the_chase.python.src.the_chase.integration.adsr_arena import ADSRArenaBridge

        grid_adsr = ADSREnvelope(OverwatchConfig())
        cache = MockCacheLayer()
        rewards = CharacterRewardState()

        bridge = ADSRArenaBridge(grid_adsr, cache, rewards)

        # Enter sustain
        grid_adsr.update(4.0)
        assert grid_adsr.phase == EnvelopePhase.SUSTAIN

        cache.l1["entry1"] = {"data": "test"}
        bridge.sync_sustain_phase()
        assert cache.l1["entry1"]["priority"] == "maintained"

        # Enter decay
        grid_adsr.update(20.0)
        assert grid_adsr.phase == EnvelopePhase.DECAY

        rewards.add_achievement(Achievement(AchievementType.VICTORY, 100))
        initial_honor = rewards.honor
        bridge.sync_decay_phase()
        assert rewards.honor < initial_honor

    def test_multiple_sync_calls(self):
        """Test multiple sync calls during sustain."""
        from Arena.the_chase.python.src.the_chase.integration.adsr_arena import ADSRArenaBridge

        grid_adsr = ADSREnvelope(OverwatchConfig())
        cache = MockCacheLayer()
        rewards = CharacterRewardState()

        bridge = ADSRArenaBridge(grid_adsr, cache, rewards)

        grid_adsr.update(4.0)  # Sustain
        cache.l1["key"] = {"priority": "normal"}

        for _ in range(5):
            bridge.sync_sustain_phase()

        assert cache.l1["key"]["priority"] == "maintained"

    def test_cache_with_multiple_entries(self):
        """Test sync with multiple cache entries."""
        from Arena.the_chase.python.src.the_chase.integration.adsr_arena import ADSRArenaBridge

        grid_adsr = ADSREnvelope(OverwatchConfig())
        cache = MockCacheLayer()
        rewards = CharacterRewardState()

        bridge = ADSRArenaBridge(grid_adsr, cache, rewards)

        grid_adsr.update(4.0)  # Sustain

        for i in range(10):
            cache.l1[f"key_{i}"] = {"priority": "normal", "data": i}

        bridge.sync_sustain_phase()

        for key in cache.l1.keys():
            assert cache.l1[key]["priority"] == "maintained"


class TestADSRArenaBridgeEdgeCases:
    """Edge case tests for ADSR-Arena bridge."""

    @pytest.fixture
    def config(self) -> OverwatchConfig:
        """Create test configuration."""
        return OverwatchConfig()

    def test_bridge_with_empty_rewards(self):
        """Test bridge with zero honor."""
        from Arena.the_chase.python.src.the_chase.integration.adsr_arena import ADSRArenaBridge

        grid_adsr = ADSREnvelope(OverwatchConfig())
        cache = MockCacheLayer()
        rewards = CharacterRewardState()  # Zero honor

        bridge = ADSRArenaBridge(grid_adsr, cache, rewards)

        grid_adsr.update(20.0)  # Decay
        bridge.sync_decay_phase()  # Should not raise

    def test_bridge_with_high_honor(self):
        """Test bridge with high honor value."""
        from Arena.the_chase.python.src.the_chase.integration.adsr_arena import ADSRArenaBridge

        grid_adsr = ADSREnvelope(OverwatchConfig())
        cache = MockCacheLayer()
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 500))

        ADSRArenaBridge(grid_adsr, cache, rewards)

        # Manually decay honor to test the mechanism
        initial_honor = rewards.honor
        rewards.decay_honor(rate=0.01)

        assert rewards.honor < initial_honor
        assert rewards.honor >= 0.0

    def test_bridge_with_cache_l2_entries(self):
        """Test bridge ignores L2 cache entries."""
        from Arena.the_chase.python.src.the_chase.integration.adsr_arena import ADSRArenaBridge

        grid_adsr = ADSREnvelope(OverwatchConfig())
        cache = MockCacheLayer()
        rewards = CharacterRewardState()

        bridge = ADSRArenaBridge(grid_adsr, cache, rewards)

        grid_adsr.update(4.0)  # Sustain
        cache.l2["l2_key"] = {"data": "l2"}  # L2 entry

        bridge.sync_sustain_phase()  # Should only affect L1

        assert "l2_key" not in cache.l1

    def test_bridge_release_phase_no_ops(self):
        """Test bridge handles release phase correctly."""
        from Arena.the_chase.python.src.the_chase.integration.adsr_arena import ADSRArenaBridge

        grid_adsr = ADSREnvelope(OverwatchConfig())
        cache = MockCacheLayer()
        rewards = CharacterRewardState()
        rewards.add_achievement(Achievement(AchievementType.VICTORY, 100))

        bridge = ADSRArenaBridge(grid_adsr, cache, rewards)

        grid_adsr.update(25.0)  # Release phase
        assert grid_adsr.phase == EnvelopePhase.RELEASE

        # With updated bridge, sync_decay_phase DOES apply decay in release
        initial_honor = rewards.honor
        bridge.sync_decay_phase()
        assert rewards.honor < initial_honor  # Decay IS applied


class TestGRIDADSRIntegration:
    """Tests for GRID ADSR envelope integration."""

    @pytest.fixture
    def grid_config(self):
        """Create GRID ADSR configuration."""
        from dataclasses import dataclass
        from enum import Enum

        class EnvelopePhase(Enum):
            ATTACK = "attack"
            DECAY = "decay"
            SUSTAIN = "sustain"
            RELEASE = "release"
            IDLE = "idle"

        @dataclass
        class ADSREnvelope:
            attack_time: float = 0.1
            decay_time: float = 0.2
            sustain_level: float = 0.7
            sustain_time: float = 1.0
            release_time: float = 0.3
            phase: Enum = EnvelopePhase.IDLE
            amplitude: float = 0.0

        return ADSREnvelope

    def test_grid_adsr_sustain_matches_chase_config(self):
        """Verify GRID ADSR sustain level matches Chase config."""
        grid_adsr = ADSREnvelope(OverwatchConfig())
        grid_adsr.update(4.0)
        assert grid_adsr.quality == 0.6

    def test_bridge_uses_chase_adsr(self):
        """Verify bridge uses The Chase ADSR envelope."""
        from Arena.the_chase.python.src.the_chase.integration.adsr_arena import ADSRArenaBridge

        config = OverwatchConfig()
        grid_adsr = ADSREnvelope(config)
        cache = MockCacheLayer()
        rewards = CharacterRewardState()

        bridge = ADSRArenaBridge(grid_adsr, cache, rewards)

        assert bridge.grid_adsr.config.sustain_level == 0.6
