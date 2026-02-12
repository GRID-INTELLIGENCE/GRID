# Sustain/Decay Arena Integration Analysis

**Date**: 2026-01-07
**Branch**: `test/sustain-decay-arena-integration`
**Test File**: `tests/test_sustain_decay_arena.py`

---

## Executive Summary

This analysis explores the relationship between ADSR envelope sustain/decay semantics and Arena's cache/reward systems. The test suite identifies **5 critical problems** and provides comprehensive test coverage for sustain/decay mechanisms across three systems.

---

## Main Topic of Discussion

### Sustain/Decay Semantics Across Systems

The analysis examines how **sustain** and **decay** concepts manifest in three different systems:

1. **ADSR Envelope** (`application/resonance/adsr_envelope.py`)
   - **Sustain**: Maintained amplitude level (0.7) during activity
   - **Decay**: Exponential drop from peak (1.0) to sustain level (0.7)
   - **Phases**: Attack → Decay → Sustain → Release

2. **Arena Cache Layer** (`Arena/the_chase/python/src/the_chase/core/cache.py`)
   - **Sustain**: Cache entries maintaining priority/state over time
   - **Decay**: TTL expiration, priority reduction, behavioral contrast
   - **Mechanism**: TTL-based expiration with reward/penalty adjustments

3. **Arena Reward System** (`Arena/the_chase/python/src/the_chase/overwatch/rewards.py`)
   - **Sustain**: Honor/reward levels maintained over time
   - **Decay**: Natural decay of honor without new achievements (NOT IMPLEMENTED)
   - **Mechanism**: Honor growth with achievements, but no decay

---

## Problems Identified

### 1. Missing Decay Mechanism in Reward States

**Problem**: `CharacterRewardState` tracks honor growth but has **no explicit decay mechanism**.

**Current Behavior**:
- Honor only grows with achievements (0.05 to 0.50 per achievement)
- Honor never decays, even without activity
- Reward levels only escalate, never de-escalate

**Expected Behavior**:
- Honor should decay naturally (e.g., 0.01 per day without achievements)
- Reward levels should de-escalate: `PROMOTED → REWARDED → ACKNOWLEDGED → NEUTRAL`
- Should mirror reputation decay in penalty system

**Impact**: Creates asymmetry with penalty system where reputation can decay. Once a player is promoted, they remain promoted indefinitely.

**Recommendation**: Implement `decay_honor()` method and `de_escalate_reward_level()` method.

---

### 2. No Explicit Sustain Phase Tracking in Cache

**Problem**: Cache entries have TTL but **no explicit "sustain period" concept**.

**Current Behavior**:
- Cache entries exist until TTL expires (implicit sustain)
- Priority is static during entry lifetime
- No distinction between "active sustain" and "decay" phases

**Expected Behavior**:
- Explicit `sustain_time` parameter (like ADSR `sustain_time`)
- Track sustain phase separately from TTL
- Priority maintained during sustain phase

**Impact**: Cannot model ADSR-like sustain behavior where amplitude is maintained at a specific level for a duration.

**Recommendation**: Add `sustain_time` to `CacheMeta` and track explicit sustain phase.

---

### 3. Disconnect Between ADSR Envelope and Arena Systems

**Problem**: **No integration** between ADSR envelope and Arena's behavioral feedback systems.

**Current State**:
- ADSR envelope: `application/resonance/` (activity feedback)
- Arena cache/rewards: `Arena/the_chase/` (game simulation)
- No shared semantics or integration code

**Opportunity**: Map ADSR phases to Arena behavioral states:
- **ADSR Attack** → Reward escalation (honor growth)
- **ADSR Decay** → Priority reduction (penalty decay)
- **ADSR Sustain** → Maintained reward/penalty state
- **ADSR Release** → State reset/expiration

**Impact**: Missing opportunity to create unified sustain/decay semantics across systems.

**Recommendation**: Create integration module mapping ADSR phases to Arena states.

---

### 4. TTL-Based Decay is Binary, Not Gradual

**Problem**: Cache entries expire **instantly** (hard TTL) or not at all. No gradual decay.

**Current Behavior**:
- Entry exists at set priority until TTL expires
- Priority is static (no gradual reduction)
- Expiration is binary (exists or doesn't exist)

**Expected Behavior**:
- Gradual priority decay over time (exponential curve)
- Similar to ADSR `decay_curve` parameter
- Priority should decrease during entry lifetime

**Impact**: Cannot model ADSR-like gradual decay where amplitude smoothly transitions from peak to sustain.

**Recommendation**: Implement priority decay curve (exponential decay over time).

---

### 5. Reward State Decay Not Implemented

**Problem**: `RewardEscalator` has escalation but **no de-escalation mechanism**.

**Current Behavior**:
- Reward levels only escalate: `NEUTRAL → ACKNOWLEDGED → REWARDED → PROMOTED`
- Once `PROMOTED`, always `PROMOTED` (no natural decay)
- No mechanism to step down reward levels

**Expected Behavior**:
- De-escalation if no achievements for extended period
- `PROMOTED → REWARDED → ACKNOWLEDGED → NEUTRAL`
- Mirror penalty escalation (which has de-escalation)

**Impact**: Creates asymmetry where penalties can escalate and de-escalate, but rewards only escalate.

**Recommendation**: Implement `de_escalate_reward_level()` method with time-based triggers.

---

## Test Coverage

The test suite (`test_sustain_decay_arena.py`) provides comprehensive coverage:

### Cache Sustain/Decay Tests
- ✅ Cache entry sustains priority over time
- ✅ Cache entry sustains with reward boost
- ✅ Cache entry sustains during soft TTL
- ✅ Cache entry decays on TTL expiration
- ✅ Cache entry decays faster with penalty
- ✅ Cache priority static during lifetime (limitation test)

### Reward State Sustain/Decay Tests
- ✅ Honor sustains with regular achievements
- ✅ Reward level sustains with continued achievements
- ❌ Honor does NOT decay naturally (problem test)
- ❌ Reward level does NOT de-escalate (problem test)
- ❌ Honor decay should mirror reputation decay (problem test)

### ADSR-Arena Integration Tests
- ✅ ADSR Attack maps to reward escalation
- ✅ ADSR Decay maps to priority reduction
- ✅ ADSR Sustain maps to maintained state
- ✅ ADSR Release maps to state expiration

### Behavioral Contrast Tests
- ✅ Rewarded entries sustain longer
- ✅ Penalized entries decay faster
- ✅ Reward/penalty contrast in sustain

**Total**: 20+ test cases covering sustain/decay mechanisms and identified problems.

---

## Recommendations

### Priority 1: Implement Honor Decay

```python
# Add to CharacterRewardState
def decay_honor(self, decay_rate: float = 0.01, days_without_achievement: float = 1.0) -> None:
    """Decay honor naturally over time without achievements."""
    if self.last_achievement_at is None:
        return

    days_elapsed = (time.time() - self.last_achievement_at) / 86400.0
    if days_elapsed >= days_without_achievement:
        decay_amount = decay_rate * (days_elapsed / days_without_achievement)
        self.honor = max(0.0, self.honor - decay_amount)
        self.honor_history.append(self.honor)
```

### Priority 2: Implement Reward Level De-escalation

```python
# Add to CharacterRewardState
def check_and_de_escalate(self, days_without_achievement: float = 7.0) -> RewardLevel:
    """De-escalate reward level if no achievements for extended period."""
    if self.last_achievement_at is None:
        return self.reward_level

    days_elapsed = (time.time() - self.last_achievement_at) / 86400.0
    if days_elapsed >= days_without_achievement:
        if self.reward_level == RewardLevel.PROMOTED:
            self.reward_level = RewardLevel.REWARDED
        elif self.reward_level == RewardLevel.REWARDED:
            self.reward_level = RewardLevel.ACKNOWLEDGED
        elif self.reward_level == RewardLevel.ACKNOWLEDGED:
            self.reward_level = RewardLevel.NEUTRAL

    return self.reward_level
```

### Priority 3: Add Gradual Priority Decay

```python
# Add to CacheMeta
def get_current_priority(self, decay_curve: float = 1.5) -> float:
    """Get current priority with gradual decay over time."""
    age = self.age_seconds()
    ttl_progress = min(1.0, age / self.ttl_seconds)

    # Exponential decay from initial priority to 0.0
    decay_factor = (1.0 - ttl_progress) ** decay_curve
    return self.priority * decay_factor
```

### Priority 4: Add Explicit Sustain Phase Tracking

```python
# Add to CacheMeta
sustain_time: float = 0.0  # Explicit sustain period

def is_in_sustain_phase(self) -> bool:
    """Check if entry is in sustain phase."""
    age = self.age_seconds()
    return age > (self.ttl_seconds - self.sustain_time) and age < self.ttl_seconds
```

### Priority 5: Create ADSR-Arena Integration Module

```python
# New file: Arena/the_chase/python/src/the_chase/integration/adsr_arena.py
class ADSRArenaMapper:
    """Map ADSR envelope phases to Arena behavioral states."""

    @staticmethod
    def map_attack_to_reward_escalation(envelope: ADSREnvelope, state: CharacterRewardState):
        """Map ADSR attack phase to reward escalation."""
        # Implementation
        pass

    @staticmethod
    def map_decay_to_priority_reduction(envelope: ADSREnvelope, cache: CacheLayer):
        """Map ADSR decay phase to cache priority reduction."""
        # Implementation
        pass
```

---

## Conclusion

The analysis reveals **5 critical problems** in sustain/decay mechanisms:

1. **Missing decay in reward states** (asymmetry with penalty system)
2. **No explicit sustain phase tracking** (implicit via TTL)
3. **Disconnect between ADSR and Arena** (no integration)
4. **Binary decay instead of gradual** (no exponential curves)
5. **No reward de-escalation** (only escalation)

The test suite provides comprehensive coverage and documents expected vs. actual behavior. Recommendations prioritize implementing missing decay mechanisms to create symmetry with the penalty system and enable ADSR-like gradual decay semantics.

---

## Next Steps

1. ✅ **Complete**: Created test suite with problem documentation
2. ⏳ **Next**: Implement honor decay mechanism
3. ⏳ **Next**: Implement reward level de-escalation
4. ⏳ **Next**: Add gradual priority decay to cache
5. ⏳ **Next**: Add explicit sustain phase tracking
6. ⏳ **Future**: Create ADSR-Arena integration module

---

**Status**: Test suite complete, ready for implementation of recommended fixes.
