"""
ADSR-Arena Integration Bridge

ORI PROBE NOTE (2026-04-09):
  Scope: This module is the sole cross-boundary link between
  Arena's ADSR envelope, cache layer, and reward system.
  Signal: KEEP — core integration point, well-tested
  (test_adsr_arena_integration.py, test_edge_cases.py).

  Architectural smell — dual ADSR:
    src/application/resonance/adsr_envelope.py (production)
    Arena/the_chase/.../core/adsr_envelope.py   (Arena-specific)
  Both implement EnvelopePhase state machines independently.
  Consolidation candidate for next refactor pass.

  Architectural smell — duplicated RewardLevel:
    Arena/the_chase/.../overwatch/rewards.py  defines RewardLevel
    Arena/the_chase/.../core/cache.py         defines RewardLevel (copy)
  Should canonicalize to one source.

  Removed in this sweep (dead stubs, no real logic):
    overwatch/arena_mode.py, hooks.py, mcp.py, models.py, plan_mode.py
    overwatch/audit.py (zero importers), orchestrator (broken imports)
    resonance_chase_demo.py, fix_types_incrementally.py (one-shot scripts)
    api/, brain/, cli/ (empty stub packages)
"""

from ..core.adsr_envelope import ADSREnvelope, EnvelopePhase
from ..core.cache import CacheLayer
from ..overwatch.rewards import CharacterRewardState


class ADSRArenaBridge:
    """Bridge between GRID ADSR and Arena systems"""

    def __init__(self, grid_adsr: ADSREnvelope, cache: CacheLayer, rewards: CharacterRewardState) -> None:
        self.grid_adsr = grid_adsr
        self.cache = cache
        self.rewards = rewards

    def sync_sustain_phase(self) -> None:
        """Sync sustain phase between ADSR and Arena cache"""
        if self.grid_adsr.phase == EnvelopePhase.SUSTAIN:
            # Maintain cache entries during sustain
            # This is a placeholder for the actual logic
            for key in self.cache.l1.keys():
                self.cache.l1[key]["priority"] = "maintained"

    def sync_decay_phase(self) -> None:
        """Sync decay phase between ADSR and Arena rewards"""
        if self.grid_adsr.phase in [EnvelopePhase.DECAY, EnvelopePhase.RELEASE]:
            # Apply honor decay during ADSR decay or release
            self.rewards.decay_honor(rate=0.01)
