"""
Test Suite: Sustain/Decay Mechanisms in Arena (The Chase)

================================================================================
MAIN TOPIC OF DISCUSSION: Sustain/Decay Semantics Across Systems
================================================================================

This test suite explores the relationship between:
1. ADSR Envelope (application/resonance/adsr_envelope.py)
   - Sustain: Maintained amplitude level during activity
   - Decay: Exponential drop from peak to sustain level

2. Arena Cache Layer (Arena/the_chase/python/src/the_chase/core/cache.py)
   - Sustain: Cache entries maintaining priority/state over time
   - Decay: TTL expiration, priority reduction, behavioral contrast

3. Arena Reward System (Arena/the_chase/python/src/the_chase/overwatch/rewards.py)
   - Sustain: Honor/reward levels maintained over time
   - Decay: Natural decay of honor without new achievements

================================================================================
PROBLEMS IDENTIFIED
================================================================================

1. MISSING DECAY MECHANISM IN REWARD STATES
   - CharacterRewardState tracks honor growth but has no explicit decay
   - Honor should naturally decay over time without new achievements
   - Reward levels should de-escalate if no activity (mirroring penalty escalation)
   - Current: Honor only grows, never decays (unlike reputation in penalty system)

2. NO EXPLICIT SUSTAIN PHASE TRACKING IN CACHE
   - Cache entries have TTL but no explicit "sustain period" concept
   - ADSR envelope has sustain_time parameter, cache doesn't
   - Cache sustain is implicit (entry exists until TTL expires)
   - Missing: Explicit sustain phase where priority/state is maintained

3. DISCONNECT BETWEEN ADSR ENVELOPE AND ARENA SYSTEMS
   - ADSR envelope is in application/resonance/ (activity feedback)
   - Arena cache/rewards are in Arena/the_chase/ (game simulation)
   - No integration between ADSR sustain/decay and Arena's behavioral feedback
   - Opportunity: Map ADSR phases to Arena reward/penalty states

4. TTL-BASED DECAY IS BINARY, NOT GRADUAL
   - Cache entries expire instantly (hard TTL) or not at all
   - ADSR decay is gradual (exponential curve from peak to sustain)
   - Missing: Gradual priority/priority decay over time in cache
   - Current: Priority is static until expiration

5. REWARD STATE DECAY NOT IMPLEMENTED
   - RewardEscalator has escalation but no de-escalation
   - Honor should decay naturally (e.g., 0.01 per day without achievements)
   - Reward levels should step down: PROMOTED → REWARDED → ACKNOWLEDGED → NEUTRAL
   - Current: Once promoted, always promoted (no natural decay)

================================================================================
TEST COVERAGE
================================================================================

This suite tests:
- Cache entry sustain (maintaining state over time)
- Cache entry decay (TTL expiration, priority reduction)
- Reward state sustain (honor maintained with achievements)
- Reward state decay (honor/reward level decay without activity)
- Integration between ADSR concepts and Arena systems
- Behavioral contrast in sustain/decay (rewards vs penalties)
"""

import time

import pytest

# Try to import the_chase modules, skip tests if not available
try:
    from pathlib import Path

    # Check if Arena path exists before attempting import
    the_chase_path = Path(__file__).parent.parent / "Arena" / "the_chase" / "python" / "src"
    if not the_chase_path.exists():
        raise ImportError("the_chase path does not exist")

    # Add to path if needed
    import sys

    if str(the_chase_path) not in sys.path:
        sys.path.insert(0, str(the_chase_path))

    from the_chase.core.cache import CacheLayer, CacheMeta, MemoryTier
    from the_chase.overwatch.rewards import (
        Achievement,
        AchievementType,
        CharacterRewardState,
        RewardLevel,
    )

    HAS_THE_CHASE = True
except (ImportError, ModuleNotFoundError, OSError) as e:
    HAS_THE_CHASE = False
    pytestmark = pytest.mark.skip(reason=f"the_chase module not available: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# CACHE SUSTAIN/DECAY TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestCacheSustain:
    """
    Test cache entry sustain: maintaining priority/state over time.

    SUSTAIN CONCEPT (from ADSR):
    - In ADSR: Maintained amplitude level during activity
    - In Cache: Entry maintains priority/state during its lifetime
    - Problem: No explicit "sustain period" tracking, only implicit via TTL
    """

    def test_cache_entry_sustains_priority_over_time(self):
        """
        Test that cache entries maintain their priority during sustain phase.

        SUSTAIN BEHAVIOR:
        - Entry should maintain priority for duration of TTL
        - Priority should not decay during sustain phase
        - This mirrors ADSR sustain phase where amplitude stays constant
        """
        cache = CacheLayer(mem=MemoryTier(max_size=100))

        # Set entry with high priority
        cache.set(
            key="sustained_entry", value={"data": "test"}, ttl_seconds=10.0, priority=0.8, reward_level="rewarded"
        )

        # Check priority is maintained immediately
        entry = cache.mem.get("sustained_entry")
        assert entry is not None
        assert entry.meta.priority == 0.8 + 0.2  # Base + reward boost

        # Wait a bit (still within TTL)
        time.sleep(0.1)

        # Priority should still be maintained (sustain phase)
        entry = cache.mem.get("sustained_entry")
        assert entry is not None
        assert entry.meta.priority == 0.8 + 0.2  # Still sustained

        # PROBLEM: No explicit sustain phase tracking
        # ADSR has sustain_time parameter, cache doesn't
        # Cache sustain is implicit (exists until TTL expires)

    def test_cache_entry_sustains_with_reward_boost(self):
        """
        Test that rewarded entries sustain higher priority.

        BEHAVIORAL CONTRAST:
        - Rewarded entities get priority boost (sustain at higher level)
        - This creates semantic contrast: good actors remembered longer
        """
        cache = CacheLayer(mem=MemoryTier(max_size=100))

        # Set rewarded entry
        cache.set(
            key="rewarded_entry",
            value={"data": "test"},
            ttl_seconds=10.0,
            priority=0.5,
            reward_level="promoted",  # Highest reward level
        )

        entry = cache.mem.get("rewarded_entry")
        assert entry is not None

        # Priority should be boosted (sustained at higher level)
        expected_priority = 0.5 + 0.3  # Base + promoted boost
        assert entry.meta.priority == expected_priority

        # TTL should be extended (sustained longer)
        expected_ttl = 10.0 * 1.5  # Base TTL * promoted multiplier
        assert entry.meta.ttl_seconds == expected_ttl

    def test_cache_entry_sustains_during_soft_ttl(self):
        """
        Test that entries sustain during soft TTL (stale-while-revalidate).

        SUSTAIN CONCEPT:
        - Soft TTL allows stale entries to be served (sustain phase)
        - Hard TTL marks true expiration (decay complete)
        - This is similar to ADSR sustain phase before release
        """
        cache = CacheLayer(mem=MemoryTier(max_size=100))

        # Set entry with soft TTL
        cache.set(
            key="soft_ttl_entry",
            value={"data": "test"},
            ttl_seconds=2.0,
            soft_ttl_seconds=1.0,  # Soft TTL = half of hard TTL
            priority=0.5,
        )

        entry = cache.mem.get("soft_ttl_entry")
        assert entry is not None

        # Wait until soft TTL expires but before hard TTL
        time.sleep(1.1)

        # Entry should still exist (sustained, but stale)
        entry = cache.mem.get("soft_ttl_entry")
        assert entry is not None
        assert entry.meta.is_soft_expired()  # Stale but servable
        assert not entry.meta.is_expired()  # Not fully expired


class TestCacheDecay:
    """
    Test cache entry decay: TTL expiration, priority reduction.

    DECAY CONCEPT (from ADSR):
    - In ADSR: Exponential drop from peak (1.0) to sustain level (0.7)
    - In Cache: TTL expiration causes instant removal (binary decay)
    - Problem: Cache decay is binary, not gradual like ADSR
    """

    def test_cache_entry_decays_on_ttl_expiration(self):
        """
        Test that cache entries decay (expire) after TTL.

        DECAY BEHAVIOR:
        - Entry should be removed when TTL expires
        - This is the "release" phase of ADSR (fade to zero)
        - PROBLEM: Decay is instant (binary), not gradual
        """
        cache = CacheLayer(mem=MemoryTier(max_size=100))

        # Set entry with short TTL
        cache.set(
            key="decaying_entry",
            value={"data": "test"},
            ttl_seconds=0.5,  # Very short TTL
            priority=0.5,
        )

        # Entry should exist initially
        entry = cache.mem.get("decaying_entry")
        assert entry is not None

        # Wait for TTL to expire
        time.sleep(0.6)

        # Entry should be decayed (removed)
        entry = cache.mem.get("decaying_entry")
        assert entry is None

        # PROBLEM: Decay is binary (exists or not)
        # ADSR decay is gradual (exponential curve)
        # Missing: Gradual priority decay over time

    def test_cache_entry_decays_faster_with_penalty(self):
        """
        Test that penalized entries decay faster (shorter TTL).

        BEHAVIORAL CONTRAST:
        - Penalized entities get TTL reduction (decay faster)
        - This creates semantic contrast: bad actors forgotten faster
        """
        cache = CacheLayer(mem=MemoryTier(max_size=100))

        # Set penalized entry
        cache.set(
            key="penalized_entry",
            value={"data": "test"},
            ttl_seconds=10.0,
            priority=0.5,
            penalty_level="banned",  # Highest penalty level
        )

        entry = cache.mem.get("penalized_entry")
        assert entry is not None

        # TTL should be reduced (decays faster)
        expected_ttl = 10.0 * 0.5  # Base TTL * banned multiplier
        assert entry.meta.ttl_seconds == expected_ttl

        # Priority should be reduced (decays to lower level)
        expected_priority = max(0.0, 0.5 - 0.5)  # Base - banned reduction
        assert entry.meta.priority == expected_priority

    def test_cache_priority_static_during_lifetime(self):
        """
        Test that cache priority doesn't decay gradually (current limitation).

        PROBLEM IDENTIFIED:
        - Priority is static during entry lifetime
        - No gradual decay like ADSR envelope
        - Missing: Priority decay curve (e.g., exponential decay over time)
        """
        cache = CacheLayer(mem=MemoryTier(max_size=100))

        # Set entry
        cache.set(key="static_priority_entry", value={"data": "test"}, ttl_seconds=2.0, priority=0.8)

        initial_entry = cache.mem.get("static_priority_entry")
        initial_priority = initial_entry.meta.priority

        # Wait (but before TTL expires)
        time.sleep(0.5)

        # Priority should be the same (static, no gradual decay)
        entry = cache.mem.get("static_priority_entry")
        assert entry.meta.priority == initial_priority

        # PROBLEM: No gradual priority decay
        # ADSR has decay_curve parameter for exponential decay
        # Cache priority is binary: exists at set priority or doesn't exist


# ═══════════════════════════════════════════════════════════════════════════════
# REWARD STATE SUSTAIN/DECAY TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestRewardStateSustain:
    """
    Test reward state sustain: maintaining honor/reward levels over time.

    SUSTAIN CONCEPT:
    - Honor should be maintained with regular achievements
    - Reward levels should sustain with continued good behavior
    - This mirrors ADSR sustain phase where amplitude stays constant
    """

    def test_honor_sustains_with_regular_achievements(self):
        """
        Test that honor sustains (maintains level) with regular achievements.

        SUSTAIN BEHAVIOR:
        - Honor grows with achievements
        - With regular achievements, honor sustains at high level
        - This is the "sustain phase" of reward system
        """
        state = CharacterRewardState(entity_id="player1")

        # Add regular achievements (sustain phase)
        for i in range(5):
            achievement = Achievement(achievement_type=AchievementType.MODERATE, description=f"Achievement {i}")
            state.add_achievement(achievement)
            time.sleep(0.01)  # Small delay

        # Honor should be sustained at high level
        assert state.honor > 0.5  # Multiple moderate achievements
        assert state.achievement_count == 5

        # Reward level should be escalated (sustained at higher level)
        assert state.reward_level in (RewardLevel.ACKNOWLEDGED, RewardLevel.REWARDED)

    def test_reward_level_sustains_with_continued_achievements(self):
        """
        Test that reward level sustains with continued achievements.

        SUSTAIN CONCEPT:
        - Once at REWARDED level, continued achievements sustain that level
        - This is similar to ADSR sustain phase maintaining amplitude
        """
        state = CharacterRewardState(entity_id="player1")

        # Escalate to REWARDED level
        for i in range(10):
            achievement = Achievement(achievement_type=AchievementType.MODERATE, description=f"Achievement {i}")
            state.add_achievement(achievement)

        # Should be at REWARDED or PROMOTED level
        assert state.reward_level in (RewardLevel.REWARDED, RewardLevel.PROMOTED)

        # Add more achievements (sustain phase)
        for i in range(5):
            achievement = Achievement(achievement_type=AchievementType.MINOR, description=f"Sustain achievement {i}")
            state.add_achievement(achievement)

        # Reward level should be sustained (not de-escalated)
        assert state.reward_level in (RewardLevel.REWARDED, RewardLevel.PROMOTED)


class TestRewardStateDecay:
    """
    Test reward state decay: honor/reward level decay without activity.

    DECAY CONCEPT:
    - Honor should decay naturally over time without achievements
    - Reward levels should de-escalate if no activity
    - PROBLEM: This is NOT currently implemented in CharacterRewardState
    """

    def test_honor_does_not_decay_naturally(self):
        """
        Test that honor does NOT decay naturally (current limitation).

        PROBLEM IDENTIFIED:
        - Honor only grows, never decays
        - Unlike reputation in penalty system which can decay
        - Missing: Natural decay mechanism (e.g., 0.01 per day)
        """
        state = CharacterRewardState(entity_id="player1")

        # Add achievement to grow honor
        achievement = Achievement(achievement_type=AchievementType.SIGNIFICANT, description="Major achievement")
        state.add_achievement(achievement)

        initial_honor = state.honor
        assert initial_honor > 0.0

        # Wait (simulating time passing without achievements)
        time.sleep(0.1)

        # PROBLEM: Honor does not decay
        # Should decay naturally but doesn't
        # Missing: decay_honor() method or automatic decay
        assert state.honor == initial_honor  # No decay

        # EXPECTED BEHAVIOR (not implemented):
        # state.decay_honor(decay_rate=0.01, time_elapsed=1.0)
        # assert state.honor < initial_honor

    def test_reward_level_does_not_de_escalate(self):
        """
        Test that reward level does NOT de-escalate (current limitation).

        PROBLEM IDENTIFIED:
        - Reward levels only escalate, never de-escalate
        - Once PROMOTED, always PROMOTED (no natural decay)
        - Missing: De-escalation mechanism (mirroring penalty escalation)
        """
        state = CharacterRewardState(entity_id="player1")

        # Escalate to PROMOTED level
        for i in range(20):
            achievement = Achievement(
                achievement_type=AchievementType.EXCEPTIONAL, description=f"Exceptional achievement {i}"
            )
            state.add_achievement(achievement)

        # Should be at PROMOTED level
        assert state.reward_level == RewardLevel.PROMOTED

        # PROBLEM: No de-escalation mechanism
        # Should de-escalate if no achievements for extended period
        # Missing: de_escalate_reward_level() method

        # EXPECTED BEHAVIOR (not implemented):
        # time.sleep(86400)  # 1 day without achievements
        # state.check_and_de_escalate()
        # assert state.reward_level == RewardLevel.REWARDED  # De-escalated

    def test_honor_decay_mirrors_reputation_decay(self):
        """
        Test that honor decay should mirror reputation decay in penalty system.

        DESIGN CONSISTENCY:
        - Penalty system has reputation decay
        - Reward system should have honor decay (symmetry)
        - Currently missing: Honor decay implementation
        """
        state = CharacterRewardState(entity_id="player1")

        # Grow honor
        for i in range(5):
            achievement = Achievement(achievement_type=AchievementType.MODERATE, description=f"Achievement {i}")
            state.add_achievement(achievement)

        initial_honor = state.honor
        assert initial_honor > 0.0

        # PROBLEM: No decay mechanism
        # Should have: state.decay_honor(decay_rate=0.01, days_without_achievement=1)
        # Should mirror: CharacterState.reputation decay in penalty system

        # EXPECTED BEHAVIOR (not implemented):
        # # Simulate 1 day without achievements
        # state.decay_honor(decay_rate=0.01, days_without_achievement=1.0)
        # assert state.honor < initial_honor
        # assert state.honor >= 0.0  # Honor can't go below 0


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS: ADSR ENVELOPE ↔ ARENA SYSTEMS
# ═══════════════════════════════════════════════════════════════════════════════


class TestADSRArenaIntegration:
    """
    Test integration between ADSR envelope concepts and Arena systems.

    INTEGRATION CONCEPT:
    - Map ADSR phases to Arena behavioral states
    - ADSR Attack → Reward escalation
    - ADSR Decay → Reward/penalty decay
    - ADSR Sustain → Maintained reward/penalty state
    - ADSR Release → State reset/expiration
    """

    def test_adsr_attack_maps_to_reward_escalation(self):
        """
        Test that ADSR attack phase maps to reward escalation.

        MAPPING:
        - ADSR Attack: Initial rise to peak (amplitude 0.0 → 1.0)
        - Arena Reward: Honor growth, reward level escalation
        """
        state = CharacterRewardState(entity_id="player1")

        # ADSR Attack: Initial achievement (honor grows from 0.0)
        achievement = Achievement(achievement_type=AchievementType.SIGNIFICANT, description="First major achievement")
        state.add_achievement(achievement)

        # Honor should grow (attack phase: 0.0 → higher)
        assert state.honor > 0.0
        assert state.reward_level != RewardLevel.NEUTRAL  # Escalated

    def test_adsr_decay_maps_to_priority_reduction(self):
        """
        Test that ADSR decay phase maps to cache priority reduction.

        MAPPING:
        - ADSR Decay: Exponential drop from peak to sustain
        - Arena Cache: Priority reduction for penalized entries
        """
        cache = CacheLayer(mem=MemoryTier(max_size=100))

        # ADSR Decay: Penalized entry gets priority reduction
        cache.set(
            key="decay_entry",
            value={"data": "test"},
            ttl_seconds=10.0,
            priority=1.0,  # Peak (like ADSR peak amplitude)
            penalty_level="fined",  # Decay trigger
        )

        entry = cache.mem.get("decay_entry")

        # Priority should be reduced (decay from peak)
        # ADSR: 1.0 → sustain_level (e.g., 0.7)
        # Cache: 1.0 → 0.7 (base - penalty reduction)
        expected_priority = max(0.0, 1.0 - 0.3)  # Base - fined reduction
        assert entry.meta.priority == expected_priority

    def test_adsr_sustain_maps_to_maintained_state(self):
        """
        Test that ADSR sustain phase maps to maintained cache/reward state.

        MAPPING:
        - ADSR Sustain: Maintained amplitude during activity
        - Arena: Maintained priority/honor with continued activity
        """
        cache = CacheLayer(mem=MemoryTier(max_size=100))
        state = CharacterRewardState(entity_id="player1")

        # ADSR Sustain: Maintained state with continued activity
        # Cache: Maintained priority with reward boost
        cache.set(
            key="sustain_entry",
            value={"data": "test"},
            ttl_seconds=10.0,
            priority=0.7,  # Sustain level (like ADSR sustain_level)
            reward_level="rewarded",
        )

        # Reward: Maintained honor with regular achievements
        for i in range(3):
            achievement = Achievement(achievement_type=AchievementType.MODERATE, description=f"Sustain achievement {i}")
            state.add_achievement(achievement)

        # Both should be sustained
        entry = cache.mem.get("sustain_entry")
        assert entry.meta.priority == 0.7 + 0.2  # Sustained at boosted level
        assert state.honor > 0.0  # Sustained honor

    def test_adsr_release_maps_to_state_expiration(self):
        """
        Test that ADSR release phase maps to cache expiration/reward reset.

        MAPPING:
        - ADSR Release: Fade to zero (amplitude → 0.0)
        - Arena Cache: TTL expiration (entry removed)
        - Arena Reward: State reset (if decay implemented)
        """
        cache = CacheLayer(mem=MemoryTier(max_size=100))

        # ADSR Release: Entry expires (fades to zero)
        cache.set(
            key="release_entry",
            value={"data": "test"},
            ttl_seconds=0.5,  # Short TTL (quick release)
            priority=0.8,
        )

        # Wait for release (TTL expiration)
        time.sleep(0.6)

        # Entry should be released (removed, like ADSR fade to zero)
        entry = cache.mem.get("release_entry")
        assert entry is None  # Released (faded to zero)


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL CONTRAST IN SUSTAIN/DECAY
# ═══════════════════════════════════════════════════════════════════════════════


class TestBehavioralContrastSustainDecay:
    """
    Test behavioral contrast in sustain/decay: rewards vs penalties.

    BEHAVIORAL CONTRAST:
    - Rewarded entities: Sustain longer, decay slower
    - Penalized entities: Sustain shorter, decay faster
    - This creates semantic contrast in the system
    """

    def test_rewarded_entries_sustain_longer(self):
        """
        Test that rewarded entries sustain longer than neutral entries.

        BEHAVIORAL CONTRAST:
        - Rewarded: Extended TTL (sustain longer)
        - Neutral: Base TTL (normal sustain)
        """
        cache = CacheLayer(mem=MemoryTier(max_size=100))

        # Rewarded entry
        cache.set(key="rewarded", value={"data": "test"}, ttl_seconds=10.0, reward_level="promoted")

        # Neutral entry
        cache.set(key="neutral", value={"data": "test"}, ttl_seconds=10.0, reward_level=None)

        rewarded_entry = cache.mem.get("rewarded")
        neutral_entry = cache.mem.get("neutral")

        # Rewarded should sustain longer (extended TTL)
        assert rewarded_entry.meta.ttl_seconds > neutral_entry.meta.ttl_seconds
        assert rewarded_entry.meta.ttl_seconds == 10.0 * 1.5  # Promoted multiplier

    def test_penalized_entries_decay_faster(self):
        """
        Test that penalized entries decay faster than neutral entries.

        BEHAVIORAL CONTRAST:
        - Penalized: Reduced TTL (decay faster)
        - Neutral: Base TTL (normal decay)
        """
        cache = CacheLayer(mem=MemoryTier(max_size=100))

        # Penalized entry
        cache.set(key="penalized", value={"data": "test"}, ttl_seconds=10.0, penalty_level="banned")

        # Neutral entry
        cache.set(key="neutral", value={"data": "test"}, ttl_seconds=10.0, penalty_level=None)

        penalized_entry = cache.mem.get("penalized")
        neutral_entry = cache.mem.get("neutral")

        # Penalized should decay faster (reduced TTL)
        assert penalized_entry.meta.ttl_seconds < neutral_entry.meta.ttl_seconds
        assert penalized_entry.meta.ttl_seconds == 10.0 * 0.5  # Banned multiplier

    def test_reward_penalty_contrast_in_sustain(self):
        """
        Test contrast between reward and penalty in sustain phase.

        BEHAVIORAL CONTRAST:
        - Rewarded: Higher priority, longer TTL (sustain at higher level)
        - Penalized: Lower priority, shorter TTL (sustain at lower level)
        """
        cache = CacheLayer(mem=MemoryTier(max_size=100))

        # Rewarded entry
        cache.set(key="rewarded", value={"data": "test"}, ttl_seconds=10.0, priority=0.5, reward_level="promoted")

        # Penalized entry
        cache.set(key="penalized", value={"data": "test"}, ttl_seconds=10.0, priority=0.5, penalty_level="banned")

        rewarded_entry = cache.mem.get("rewarded")
        penalized_entry = cache.mem.get("penalized")

        # Contrast: Rewarded sustains at higher priority
        assert rewarded_entry.meta.priority > penalized_entry.meta.priority

        # Contrast: Rewarded sustains longer
        assert rewarded_entry.meta.ttl_seconds > penalized_entry.meta.ttl_seconds


# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY AND RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════════

"""
================================================================================
SUMMARY OF FINDINGS
================================================================================

1. CACHE SUSTAIN/DECAY:
   ✅ Cache entries sustain priority during TTL lifetime
   ✅ Rewarded entries sustain longer (extended TTL)
   ✅ Penalized entries decay faster (reduced TTL)
   ❌ No explicit sustain phase tracking (implicit via TTL)
   ❌ Priority is static (no gradual decay like ADSR)

2. REWARD STATE SUSTAIN/DECAY:
   ✅ Honor sustains with regular achievements
   ✅ Reward levels sustain with continued good behavior
   ❌ Honor does NOT decay naturally (only grows)
   ❌ Reward levels do NOT de-escalate (only escalate)

3. ADSR ↔ ARENA INTEGRATION:
   ✅ ADSR Attack maps to reward escalation
   ✅ ADSR Decay maps to priority reduction
   ✅ ADSR Sustain maps to maintained state
   ✅ ADSR Release maps to TTL expiration
   ❌ No explicit integration code (conceptual mapping only)

4. BEHAVIORAL CONTRAST:
   ✅ Rewarded entities sustain longer, decay slower
   ✅ Penalized entities sustain shorter, decay faster
   ✅ Semantic contrast creates behavioral feedback loop

================================================================================
RECOMMENDATIONS
================================================================================

1. IMPLEMENT HONOR DECAY:
   - Add decay_honor() method to CharacterRewardState
   - Honor should decay naturally (e.g., 0.01 per day without achievements)
   - Mirror reputation decay in penalty system

2. IMPLEMENT REWARD LEVEL DE-ESCALATION:
   - Add de_escalate_reward_level() method
   - Reward levels should step down if no achievements for extended period
   - PROMOTED → REWARDED → ACKNOWLEDGED → NEUTRAL

3. ADD GRADUAL PRIORITY DECAY:
   - Implement priority decay curve (exponential decay over time)
   - Similar to ADSR decay_curve parameter
   - Priority should gradually decrease during entry lifetime

4. ADD EXPLICIT SUSTAIN PHASE TRACKING:
   - Add sustain_time parameter to CacheMeta
   - Track explicit sustain phase (like ADSR sustain_time)
   - Separate from TTL (sustain is active period, TTL is total lifetime)

5. CREATE ADSR-ARENA INTEGRATION MODULE:
   - Map ADSR phases to Arena behavioral states
   - Create unified sustain/decay semantics
   - Bridge application/resonance/ and Arena/the_chase/
"""
