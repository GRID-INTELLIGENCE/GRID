"""
ADSR Envelope for Activity Resonance.

Models the attack, decay, sustain, and release phases of activity feedback,
like a pluck in a string defining vibration, waves, and resonance.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class EnvelopePhase(str, Enum):
    """Phases of the ADSR envelope."""

    ATTACK = "attack"  # Initial rise to peak
    DECAY = "decay"  # Drop from peak to sustain
    SUSTAIN = "sustain"  # Maintained level
    RELEASE = "release"  # Fade to zero
    IDLE = "idle"  # No activity


@dataclass
class EnvelopeMetrics:
    """Metrics for ADSR envelope state."""

    phase: EnvelopePhase = EnvelopePhase.IDLE
    amplitude: float = 0.0  # Current amplitude (0.0 to 1.0)
    velocity: float = 0.0  # Rate of change
    time_in_phase: float = 0.0  # Seconds in current phase
    total_time: float = 0.0  # Total envelope time
    peak_amplitude: float = 0.0  # Peak reached during attack


@dataclass
class ADSREnvelope:
    """
    ADSR Envelope for activity feedback.

    Like a pluck in a string:
    - Attack: Initial response, quick rise
    - Decay: Settle to working level
    - Sustain: Maintained feedback during activity
    - Release: Fade when activity completes

    Provides haptic-like feedback through amplitude and velocity metrics.
    """

    # Timing parameters (seconds)
    attack_time: float = 0.1  # Quick initial response
    decay_time: float = 0.2  # Settle to sustain
    sustain_level: float = 0.7  # Working amplitude (0.0 to 1.0)
    sustain_time: float = 1.0  # How long to sustain (or until release)
    release_time: float = 0.3  # Fade out time

    # Dynamics
    attack_curve: float = 2.0  # Exponential curve (higher = sharper)
    decay_curve: float = 1.5  # Decay curve
    release_curve: float = 2.0  # Release curve

    # State
    _start_time: float | None = field(default=None, init=False, repr=False)
    _release_start: float | None = field(default=None, init=False, repr=False)
    _metrics: EnvelopeMetrics = field(default_factory=EnvelopeMetrics, init=False, repr=False)

    def trigger(self) -> None:
        """Trigger the envelope (start attack phase)."""
        self._start_time = time.time()
        self._release_start = None
        self._metrics = EnvelopeMetrics(
            phase=EnvelopePhase.ATTACK,
            amplitude=0.0,
            velocity=1.0,
            time_in_phase=0.0,
            total_time=0.0,
            peak_amplitude=0.0,
        )

    def release(self) -> None:
        """Start release phase (fade out)."""
        if self._start_time is not None and self._release_start is None:
            self._release_start = time.time()
            self._metrics.phase = EnvelopePhase.RELEASE

    def update(self) -> EnvelopeMetrics:
        """
        Update envelope state and return current metrics.

        Returns:
            Current envelope metrics
        """
        if self._start_time is None:
            # Idle state
            if self._metrics.amplitude > 0.0:
                # Fade to zero if not already
                self._metrics.amplitude = max(0.0, self._metrics.amplitude - 0.1)
                self._metrics.velocity = -0.1
                if self._metrics.amplitude <= 0.0:
                    self._metrics = EnvelopeMetrics()
            return self._metrics

        current_time = time.time()
        elapsed = current_time - self._start_time

        # Check if in release phase
        if self._release_start is not None:
            release_elapsed = current_time - self._release_start
            if release_elapsed >= self.release_time:
                # Release complete, go to idle
                self._start_time = None
                self._release_start = None
                self._metrics = EnvelopeMetrics()
                return self._metrics

            # Calculate release amplitude
            progress = release_elapsed / self.release_time
            # Exponential decay
            self._metrics.amplitude = self.sustain_level * ((1.0 - progress) ** self.release_curve)
            self._metrics.velocity = (
                -(self.sustain_level * self.release_curve * (1.0 - progress) ** (self.release_curve - 1.0))
                / self.release_time
            )
            self._metrics.phase = EnvelopePhase.RELEASE
            self._metrics.time_in_phase = release_elapsed
            self._metrics.total_time = elapsed
            return self._metrics

        # Attack phase
        if elapsed < self.attack_time:
            progress = elapsed / self.attack_time
            # Exponential rise
            curve = self.attack_curve if self.attack_curve and self.attack_curve > 0.0 else 1.0
            self._metrics.amplitude = progress ** (1.0 / curve)
            if progress <= 0.0:
                # On some platforms/time resolutions, elapsed can be 0.0 right after trigger().
                # Avoid 0.0 ** negative-power in the derivative term.
                self._metrics.velocity = 0.0
            else:
                self._metrics.velocity = ((1.0 / curve) * progress ** ((1.0 / curve) - 1.0)) / self.attack_time
            self._metrics.phase = EnvelopePhase.ATTACK
            self._metrics.time_in_phase = elapsed
            self._metrics.total_time = elapsed
            self._metrics.peak_amplitude = max(self._metrics.peak_amplitude, self._metrics.amplitude)
            return self._metrics

        # Decay phase
        decay_start = self.attack_time
        if elapsed < decay_start + self.decay_time:
            decay_progress = (elapsed - decay_start) / self.decay_time
            # Exponential decay from 1.0 to sustain_level
            amplitude_range = 1.0 - self.sustain_level
            self._metrics.amplitude = self.sustain_level + (
                amplitude_range * ((1.0 - decay_progress) ** self.decay_curve)
            )
            self._metrics.velocity = (
                -(amplitude_range * self.decay_curve * (1.0 - decay_progress) ** (self.decay_curve - 1.0))
                / self.decay_time
            )
            self._metrics.phase = EnvelopePhase.DECAY
            self._metrics.time_in_phase = elapsed - decay_start
            self._metrics.total_time = elapsed
            self._metrics.peak_amplitude = 1.0
            return self._metrics

        # Sustain phase
        sustain_start = decay_start + self.decay_time
        if elapsed < sustain_start + self.sustain_time:
            self._metrics.amplitude = self.sustain_level
            self._metrics.velocity = 0.0
            self._metrics.phase = EnvelopePhase.SUSTAIN
            self._metrics.time_in_phase = elapsed - sustain_start
            self._metrics.total_time = elapsed
            return self._metrics

        # Sustain time exceeded, auto-release
        self.release()
        return self.update()

    def get_metrics(self) -> EnvelopeMetrics:
        """Get current envelope metrics without updating."""
        return self._metrics

    def is_active(self) -> bool:
        """Check if envelope is currently active."""
        return self._start_time is not None

    def reset(self) -> None:
        """Reset envelope to idle state."""
        self._start_time = None
        self._release_start = None
        self._metrics = EnvelopeMetrics()
