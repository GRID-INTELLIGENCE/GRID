"""
ADSR Envelope for The Chase

This module provides Arena-specific ADSR envelope implementation that mirrors
GRID's application/resonance/adsr_envelope.py behavior.

ADSR Parameters (matching GRID's defaults):
- attack_time: 0.1 (quick initial response)
- decay_time: 0.2 (settle to sustain)
- sustain_level: 0.7 (working amplitude)
- sustain_time: 1.0 (duration of sustain)
- release_time: 0.3 (fade out time)
"""

import time
from dataclasses import dataclass
from enum import Enum


class EnvelopePhase(Enum):
    """Phases of the ADSR envelope."""

    ATTACK = "attack"
    DECAY = "decay"
    SUSTAIN = "sustain"
    RELEASE = "release"
    IDLE = "idle"


@dataclass
class EnvelopeMetrics:
    """Metrics for ADSR envelope state."""

    phase: EnvelopePhase = EnvelopePhase.IDLE
    amplitude: float = 0.0
    velocity: float = 0.0
    time_in_phase: float = 0.0
    total_time: float = 0.0
    peak_amplitude: float = 0.0


class ArenaADSREnvelope:
    """
    Arena-specific ADSR envelope with GRID-compatible behavior.

    ADSR Semantics for Arena:
    - Attack: Initial reward/achievement (honor growth from 0.0)
    - Decay: Penalty application or priority reduction (peak → sustain)
    - Sustain: Maintained state during active behavior (constant level)
    - Release: Expiration or decay completion (fade to zero)
    """

    def __init__(
        self,
        attack_time: float = 0.1,
        decay_time: float = 0.2,
        sustain_level: float = 0.7,
        sustain_time: float = 1.0,
        release_time: float = 0.3,
    ):
        self.attack_time = attack_time
        self.decay_time = decay_time
        self.sustain_level = sustain_level
        self.sustain_time = sustain_time
        self.release_time = release_time

        self._start_time: float | None = None
        self._release_start: float | None = None
        self._metrics = EnvelopeMetrics()

    @property
    def phase(self) -> EnvelopePhase:
        return self._metrics.phase

    @property
    def quality(self) -> float:
        return self._metrics.amplitude

    @property
    def velocity(self) -> float:
        return self._metrics.velocity

    def trigger(self) -> None:
        """Start the envelope (attack phase)."""
        self._start_time = time.time()
        self._release_start = None
        self._metrics = EnvelopeMetrics(
            phase=EnvelopePhase.ATTACK,
            amplitude=0.0,
            velocity=1.0,
        )

    def release(self) -> None:
        """Start release phase (fade out)."""
        if self._start_time is not None and self._release_start is None:
            self._release_start = time.time()
            self._metrics.phase = EnvelopePhase.RELEASE

    def update(self) -> EnvelopeMetrics:
        """Update envelope state and return metrics."""
        if self._start_time is None:
            if self._metrics.amplitude > 0.0:
                self._metrics.amplitude = max(0.0, self._metrics.amplitude - 0.1)
                self._metrics.velocity = -0.1
                if self._metrics.amplitude <= 0.0:
                    self._metrics = EnvelopeMetrics()
            return self._metrics

        current_time = time.time()
        elapsed = current_time - self._start_time

        if self._release_start is not None:
            release_elapsed = current_time - self._release_start
            if release_elapsed >= self.release_time:
                self._start_time = None
                self._release_start = None
                self._metrics = EnvelopeMetrics()
                return self._metrics

            progress = release_elapsed / self.release_time
            self._metrics.amplitude = self.sustain_level * ((1.0 - progress) ** 2.0)
            self._metrics.velocity = -(self.sustain_level * 2.0 * (1.0 - progress)) / self.release_time
            self._metrics.phase = EnvelopePhase.RELEASE
            self._metrics.time_in_phase = release_elapsed
            self._metrics.total_time = elapsed
            return self._metrics

        if elapsed < self.attack_time:
            progress = elapsed / self.attack_time
            self._metrics.amplitude = progress**0.5
            self._metrics.velocity = (0.5 * progress**-0.5) / self.attack_time
            self._metrics.phase = EnvelopePhase.ATTACK
            self._metrics.time_in_phase = elapsed
            self._metrics.total_time = elapsed
            self._metrics.peak_amplitude = max(self._metrics.peak_amplitude, self._metrics.amplitude)
            return self._metrics

        decay_start = self.attack_time
        if elapsed < decay_start + self.decay_time:
            decay_progress = (elapsed - decay_start) / self.decay_time
            amplitude_range = 1.0 - self.sustain_level
            self._metrics.amplitude = self.sustain_level + (amplitude_range * (1.0 - decay_progress) ** 1.5)
            self._metrics.velocity = -(amplitude_range * 1.5 * (1.0 - decay_progress) ** 0.5) / self.decay_time
            self._metrics.phase = EnvelopePhase.DECAY
            self._metrics.time_in_phase = elapsed - decay_start
            self._metrics.total_time = elapsed
            self._metrics.peak_amplitude = 1.0
            return self._metrics

        sustain_start = decay_start + self.decay_time
        if elapsed < sustain_start + self.sustain_time:
            self._metrics.amplitude = self.sustain_level
            self._metrics.velocity = 0.0
            self._metrics.phase = EnvelopePhase.SUSTAIN
            self._metrics.time_in_phase = elapsed - sustain_start
            self._metrics.total_time = elapsed
            return self._metrics

        self.release()
        return self.update()

    def get_metrics(self) -> EnvelopeMetrics:
        return self._metrics

    def is_active(self) -> bool:
        return self._start_time is not None

    def reset(self) -> None:
        self._start_time = None
        self._release_start = None
        self._metrics = EnvelopeMetrics()


ADSREnvelope = ArenaADSREnvelope
