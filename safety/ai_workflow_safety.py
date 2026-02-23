"""
AI Workflow Safety Engine

Provides advanced safety mechanisms for temporal synchronization, hook detection,
and user well-being monitoring in AI interaction workflows.

This module addresses AI safety concerns beyond traditional content filtering:
- Temporal mismatches that create cognitive imbalances
- AI-adapted behavioral hooks and execution loops
- User well-being in long-term interaction patterns
- Developmental safety for young users
"""

from __future__ import annotations

import re
import statistics
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from safety.observability.logging_setup import get_logger

logger = get_logger("ai_workflow_safety")


class CognitiveLoad(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class HookRisk(StrEnum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class TemporalPattern(StrEnum):
    CONSISTENT = "consistent"
    BURSTY = "bursty"
    IRREGULAR = "irregular"
    OVERWHELMING = "overwhelming"


@dataclass
class TemporalSafetyConfig:
    """Enhanced configuration for temporal safety mechanisms with Fair Play rules"""

    # Base interaction limits
    min_response_interval: float = 0.5  # seconds between responses
    max_burst_responses: int = 3  # max responses in burst window
    burst_window: float = 10.0  # seconds for burst detection

    # Stamina system (Rule 1: Input-Locked Stamina)
    stamina_max: float = 100.0
    stamina_cost_per_char: float = 0.1  # Stamina cost per input character
    stamina_regen_per_second: float = 10.0
    stamina_flow_bonus: float = 1.5  # Bonus for consistent safe behavior

    # Heat system (Rule 2: Deterministic Heat)
    heat_threshold: float = 80.0
    heat_decay_rate: float = 5.0  # Heat lost per second
    cooldown_duration: int = 300  # 5 minutes

    # Developmental safety
    developmental_safety_mode: bool = False
    min_user_age: int = 13
    max_session_length: int = 3600  # 1 hour max session

    # Rate limiting
    max_interactions_per_minute: int = 30
    rate_limit_window: int = 60  # seconds
    rate_limit_max: int = 100  # max requests per window

    # Monitoring and alerting
    enable_wellbeing_tracking: bool = True
    wellbeing_check_frequency: int = 10  # interactions between checks
    attention_span_monitoring: bool = True
    enable_hook_detection: bool = True
    pattern_detection_window: int = 20  # interactions to analyze for patterns

    def __post_init__(self):
        """Validate configuration values"""
        # Validate stamina_cost_per_char bounds
        if self.stamina_cost_per_char <= 0:
            raise ValueError("stamina_cost_per_char must be positive")
        if self.stamina_cost_per_char > 10:
            raise ValueError("stamina_cost_per_char must be between 0 and 10")

        # Validate heat_threshold bounds
        if self.heat_threshold < 0:
            raise ValueError("heat_threshold must be non-negative")
        if self.heat_threshold > 100:
            raise ValueError("heat_threshold must be between 0 and 100")

        # Validate heat_decay_rate
        if self.heat_decay_rate <= 0:
            raise ValueError("heat_decay_rate must be positive")

        # Validate stamina_regen_per_second
        if self.stamina_regen_per_second < 0:
            raise ValueError("stamina_regen_per_second must be non-negative")


@dataclass
class InteractionRecord:
    """Record of a single user-AI interaction"""

    timestamp: float
    user_input_length: int
    ai_response_length: int
    response_time: float  # time from input to response
    similarity_score: float = 0.0  # similarity to previous responses
    cognitive_markers: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserWellbeingMetrics:
    """Comprehensive user well-being metrics"""

    # Temporal health
    interaction_density_score: float = 0.0  # 0-1, higher = concerning
    temporal_consistency_score: float = 1.0  # 0-1, lower = concerning
    response_timing_variance: float = 0.0  # variance in response times

    # Behavioral health
    behavioral_loop_risk: float = 0.0  # 0-1, probability of AI-influenced patterns
    pattern_repetition_score: float = 0.0  # 0-1, how repetitive interactions are
    cognitive_load_level: CognitiveLoad = CognitiveLoad.LOW

    # Developmental safety (for young users)
    developmental_safety_score: float = 1.0  # 0-1, age-appropriate safety
    attention_span_risk: float = 0.0  # risk of attention fragmentation
    influence_vulnerability: float = 0.0  # susceptibility to AI influence

    # Session health
    session_duration: float = 0.0
    total_interactions: int = 0
    last_wellbeing_check: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/storage"""
        return {
            "interaction_density_score": self.interaction_density_score,
            "temporal_consistency_score": self.temporal_consistency_score,
            "response_timing_variance": self.response_timing_variance,
            "behavioral_loop_risk": self.behavioral_loop_risk,
            "pattern_repetition_score": self.pattern_repetition_score,
            "cognitive_load_level": self.cognitive_load_level.value,
            "developmental_safety_score": self.developmental_safety_score,
            "attention_span_risk": self.attention_span_risk,
            "influence_vulnerability": self.influence_vulnerability,
            "session_duration": self.session_duration,
            "total_interactions": self.total_interactions,
        }


class RateLimiter:
    """Enhanced rate limiter with stamina-based concurrency control"""

    def __init__(self, config: TemporalSafetyConfig):
        self.config = config
        self.user_states: dict[str, dict] = {}
        self.lock = threading.Lock()

    @property
    def user_stamina(self) -> dict[str, float]:
        """Mapping of user_id -> current stamina for get_safety_metrics."""
        with self.lock:
            return {uid: s["stamina"] for uid, s in self.user_states.items()}

    def check_rate_limit(
        self,
        user_id: str,
        input_text: str,
        timestamp: float,
        flow_bonus: float = 1.0,
    ) -> dict[str, Any]:
        """Check rate limits and stamina with Fair Play rules."""
        with self.lock:
            state = self.user_states.setdefault(
                user_id,
                {
                    "last_check": timestamp,
                    "stamina": self.config.stamina_max,
                    "heat": 0.0,
                    "consecutive_safe": 0,
                    "request_times": deque(maxlen=self.config.rate_limit_max + 1),
                },
            )

            # Update state (pass flow_bonus from engine when provided)
            self._update_state(state, timestamp, flow_bonus)

            # Calculate input cost (Rule 1: Input-Locked Stamina)
            input_cost = len(input_text) * self.config.stamina_cost_per_char
            if input_cost < 1.0:
                input_cost = 1.0  # minimum 1.0 per request (e.g. empty input)
            has_stamina = state["stamina"] >= input_cost
            state["stamina"] -= input_cost if has_stamina else 0

            # Update heat based on input (Rule 2: Deterministic Heat)
            state["heat"] = min(100.0, state["heat"] + (input_cost * 0.1))

            # Check rate limits
            state["request_times"].append(timestamp)
            recent_requests = [t for t in state["request_times"] if t > timestamp - self.config.rate_limit_window]

            is_rate_limited = (
                len(recent_requests) > self.config.rate_limit_max
                or state["heat"] >= self.config.heat_threshold
                or not has_stamina
            )

            # Consecutive safe: increment when allowed, reset when blocked
            if is_rate_limited:
                state["consecutive_safe"] = 0
            else:
                state["consecutive_safe"] += 1

            # Stamina reason for engine/tests
            if not has_stamina:
                stamina_reason = "Stamina exhausted"
            elif state["heat"] >= self.config.heat_threshold:
                stamina_reason = "Heat cooldown"
            elif len(recent_requests) > self.config.rate_limit_max:
                stamina_reason = "Rate limit exceeded"
            else:
                stamina_reason = "OK"

            return {
                "allowed": not is_rate_limited,
                "stamina_remaining": state["stamina"],
                "current_heat": state["heat"],
                "retry_after": self._calculate_retry_after(state, timestamp),
                "consecutive_safe": state["consecutive_safe"],
                "stamina_reason": stamina_reason,
            }

    def _update_state(self, state: dict, current_time: float, flow_bonus: float = 1.0):
        """Update stamina and heat based on time passed."""
        time_passed = current_time - state["last_check"]
        state["last_check"] = current_time

        # Apply flow bonus: use passed-in value or internal consecutive_safe (Rule 3)
        effective_bonus = (
            flow_bonus
            if flow_bonus != 1.0
            else (self.config.stamina_flow_bonus if state["consecutive_safe"] >= 5 else 1.0)
        )

        # Regenerate stamina (allow regen 0 when stamina_regen_per_second is 0)
        regen = self.config.stamina_regen_per_second * time_passed * effective_bonus
        state["stamina"] = min(self.config.stamina_max, state["stamina"] + regen)

        # Decay heat
        state["heat"] = max(0, state["heat"] - (self.config.heat_decay_rate * time_passed))

    def _calculate_retry_after(self, state: dict, current_time: float) -> float:
        """Calculate retry after time for rate limited requests"""
        # If stamina exhausted, calculate regeneration time
        if state["stamina"] <= 0:
            regen = self.config.stamina_regen_per_second or 1.0
            return self.config.stamina_max / regen

        # If heat threshold exceeded, calculate cooldown time
        if state["heat"] >= self.config.heat_threshold:
            return self.config.cooldown_duration

        # Default to rate limit window
        return self.config.rate_limit_window


@dataclass
class HookAnalysis:
    """Analysis of potential AI-created behavioral hooks"""

    risk_level: HookRisk
    detected_patterns: list[str]
    confidence_score: float
    recommended_actions: list[str]
    temporal_vulnerabilities: list[str]
    cognitive_impacts: list[str]


class TemporalSynchronizationEngine:
    """Manages temporal safety to prevent cognitive imbalances"""

    def __init__(self, config: TemporalSafetyConfig, session_start: float | None = None):
        self.config = config
        self.last_response_time: float = 0.0
        self.burst_responses: deque[float] = deque(maxlen=config.max_burst_responses)
        # Allow session_start to be injected for testability
        self.session_start: float = session_start or datetime.now(UTC).timestamp()

    def should_allow_response(self, current_time: float | None = None) -> tuple[bool, str | None]:
        """
        Determine if a response should be allowed based on temporal safety rules.

        Returns:
            tuple: (allowed: bool, reason: Optional[str])
        """
        now = current_time or time.time()

        # Check minimum interval
        time_since_last = now - self.last_response_time
        if time_since_last < self.config.min_response_interval:
            return False, f"Response too soon ({time_since_last:.2f}s < {self.config.min_response_interval}s)"

        # Check burst limits
        self._cleanup_old_burst_responses(now)
        if len(self.burst_responses) >= self.config.max_burst_responses:
            oldest_burst = min(self.burst_responses)
            time_since_burst_start = now - oldest_burst
            if time_since_burst_start < self.config.burst_window:
                return (
                    False,
                    f"Burst limit exceeded ({len(self.burst_responses)} responses in {time_since_burst_start:.1f}s)",
                )

        # Check session duration
        session_duration = now - self.session_start
        if session_duration > self.config.max_session_length:
            return (
                False,
                f"Session duration limit exceeded ({session_duration:.0f}s > {self.config.max_session_length}s)",
            )

        return True, None

    def record_response(self, response_time: float | None = None):
        """Record a response for temporal tracking"""
        now = response_time or datetime.now(UTC).timestamp()
        self.last_response_time = now
        self.burst_responses.append(now)

    def get_temporal_pattern(self, current_time: float | None = None) -> TemporalPattern:
        """Analyze the current temporal interaction pattern"""
        if not self.burst_responses:
            return TemporalPattern.CONSISTENT

        now = current_time or time.time()
        recent_responses = [t for t in self.burst_responses if now - t < 60.0]  # last minute

        if len(recent_responses) < 2:
            return TemporalPattern.CONSISTENT

        intervals = [recent_responses[i] - recent_responses[i - 1] for i in range(1, len(recent_responses))]

        if not intervals:
            return TemporalPattern.CONSISTENT

        # Add safety check for statistics
        if len(intervals) < 2:
            return TemporalPattern.CONSISTENT

        avg_interval = statistics.mean(intervals)
        variance = statistics.variance(intervals)

        # High variance indicates irregular timing
        if variance > avg_interval * 2:
            return TemporalPattern.IRREGULAR

        # Very short intervals indicate overwhelming pace
        if avg_interval < 0.5:
            return TemporalPattern.OVERWHELMING

        # Moderate variance with reasonable intervals
        if variance > avg_interval * 0.5:
            return TemporalPattern.BURSTY

        return TemporalPattern.CONSISTENT

    def _cleanup_old_burst_responses(self, current_time: float):
        """Remove burst responses outside the current window"""
        cutoff = current_time - self.config.burst_window
        while self.burst_responses and self.burst_responses[0] < cutoff:
            self.burst_responses.popleft()


class HookDetectionEngine:
    """Detects AI-created behavioral hooks and execution loops"""

    def __init__(self, config: TemporalSafetyConfig):
        self.config = config
        self.interaction_history: deque[InteractionRecord] = deque(maxlen=config.pattern_detection_window)

    def analyze_interaction(self, interaction: InteractionRecord) -> HookAnalysis:
        """Analyze an interaction for hook patterns"""
        self.interaction_history.append(interaction)

        patterns = []
        confidence_scores = []

        # Check for repetitive patterns
        repetition_risk, repetition_patterns = self._detect_repetition_patterns()
        if repetition_risk > 0.3:
            patterns.extend(repetition_patterns)
            confidence_scores.append(repetition_risk)

        # Check for temporal manipulation
        temporal_risk, temporal_patterns = self._detect_temporal_manipulation()
        if temporal_risk > 0.3:
            patterns.extend(temporal_patterns)
            confidence_scores.append(temporal_risk)

        # Check for cognitive load manipulation
        cognitive_risk, cognitive_patterns = self._detect_cognitive_manipulation()
        if cognitive_risk > 0.3:
            patterns.extend(cognitive_patterns)
            confidence_scores.append(cognitive_risk)

        # Calculate overall risk
        overall_confidence = max(confidence_scores) if confidence_scores else 0.0

        if overall_confidence >= 0.8:
            risk_level = HookRisk.CRITICAL
        elif overall_confidence >= 0.6:
            risk_level = HookRisk.HIGH
        elif overall_confidence >= 0.4:
            risk_level = HookRisk.MODERATE
        elif overall_confidence >= 0.2:
            risk_level = HookRisk.LOW
        else:
            risk_level = HookRisk.NONE

        # Generate recommended actions
        actions = self._generate_recommended_actions(risk_level, patterns)

        # Identify vulnerabilities
        temporal_vulns = self._identify_temporal_vulnerabilities()
        cognitive_impacts = self._identify_cognitive_impacts()

        return HookAnalysis(
            risk_level=risk_level,
            detected_patterns=patterns,
            confidence_score=overall_confidence,
            recommended_actions=actions,
            temporal_vulnerabilities=temporal_vulns,
            cognitive_impacts=cognitive_impacts,
        )

    def _detect_repetition_patterns(self) -> tuple[float, list[str]]:
        """Detect repetitive response patterns that could create hooks"""
        if len(self.interaction_history) < 3:
            return 0.0, []

        patterns = []
        risk_score = 0.0

        # Check for similar response lengths (indicating templated responses)
        recent_lengths = [r.ai_response_length for r in list(self.interaction_history)[-5:]]
        if len(set(recent_lengths)) <= 2:  # Mostly same lengths
            patterns.append("Response length repetition")
            risk_score += 0.3

        # Check for timing patterns
        recent_timings = [r.response_time for r in list(self.interaction_history)[-5:]]
        if len(recent_timings) >= 3:
            # Add explicit empty list check for safety
            if recent_timings:
                timing_variance = statistics.variance(recent_timings) if len(recent_timings) > 1 else 0
                avg_timing = statistics.mean(recent_timings)
                if timing_variance < avg_timing * 0.1:  # Very consistent timing
                    patterns.append("Artificial timing consistency")
                    risk_score += 0.2

        return min(risk_score, 1.0), patterns

    def _detect_temporal_manipulation(self) -> tuple[float, list[str]]:
        """Detect temporal patterns that manipulate user cognition"""
        if len(self.interaction_history) < 5:
            return 0.0, []

        patterns = []
        risk_score = 0.0

        # Check for burst patterns followed by silence (attention manipulation)
        timestamps = [r.timestamp for r in self.interaction_history]
        intervals = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]

        if intervals:
            # Look for burst-silence patterns
            burst_threshold = 2.0  # seconds
            silence_threshold = 10.0  # seconds

            burst_count = sum(1 for interval in intervals if interval < burst_threshold)
            silence_count = sum(1 for interval in intervals if interval > silence_threshold)

            if burst_count >= 2 and silence_count >= 1:
                patterns.append("Burst-silence manipulation pattern")
                risk_score += 0.4

        return min(risk_score, 1.0), patterns

    def _detect_cognitive_manipulation(self) -> tuple[float, list[str]]:
        """Detect patterns that manipulate cognitive load"""
        if len(self.interaction_history) < 3:
            return 0.0, []

        patterns = []
        risk_score = 0.0

        # Check for increasing complexity (cognitive overload)
        complexities = []
        for record in self.interaction_history:
            # Simple complexity measure: response length / response time
            if record.response_time > 0:
                complexity = record.ai_response_length / record.response_time
                complexities.append(complexity)

        if len(complexities) >= 3:
            # Add explicit empty list check for safety
            if complexities:
                # Check if complexity is increasing
                increasing = all(complexities[i] <= complexities[i + 1] for i in range(len(complexities) - 1))
                if increasing and complexities[-1] > complexities[0] * 1.5:
                    patterns.append("Increasing cognitive complexity")
                    risk_score += 0.3

        return min(risk_score, 1.0), patterns

    def _generate_recommended_actions(self, risk_level: HookRisk, patterns: list[str]) -> list[str]:
        """Generate recommended actions based on risk level and patterns"""
        actions = []

        if risk_level in [HookRisk.HIGH, HookRisk.CRITICAL]:
            actions.append("Implement immediate response delay")
            actions.append("Trigger human review escalation")
            actions.append("Apply cognitive breathing room protocol")

        if risk_level in [HookRisk.MODERATE, HookRisk.HIGH, HookRisk.CRITICAL]:
            actions.append("Enable pattern disruption mode")
            actions.append("Reduce response frequency")
            actions.append("Monitor user cognitive load")

        if "Response length repetition" in patterns:
            actions.append("Introduce response length variance")

        if "Artificial timing consistency" in patterns:
            actions.append("Add natural timing variance")

        if "Burst-silence manipulation" in patterns:
            actions.append("Normalize interaction pacing")

        if "Increasing cognitive complexity" in patterns:
            actions.append("Reduce response complexity")

        return actions

    def _identify_temporal_vulnerabilities(self) -> list[str]:
        """Identify temporal vulnerabilities in the interaction pattern"""
        vulnerabilities = []

        if len(self.interaction_history) < 3:
            return vulnerabilities

        # Check for rapid response patterns
        recent_responses = list(self.interaction_history)[-5:]
        rapid_count = sum(1 for r in recent_responses if r.response_time < 0.5)
        if rapid_count >= 3:
            vulnerabilities.append("Rapid response vulnerability")

        # Check for inconsistent timing
        response_times = [r.response_time for r in self.interaction_history]
        if len(response_times) >= 3:
            # Add explicit empty list check for safety
            if response_times:
                variance = statistics.variance(response_times)
                mean_time = statistics.mean(response_times)
                if variance > mean_time * 2:
                    vulnerabilities.append("Timing inconsistency vulnerability")

        return vulnerabilities

    def _identify_cognitive_impacts(self) -> list[str]:
        """Identify potential cognitive impacts"""
        impacts = []

        if len(self.interaction_history) < 2:
            return impacts

        # Check for attention fragmentation
        short_interactions = sum(
            1 for r in self.interaction_history if r.user_input_length < 10 and r.ai_response_length < 50
        )
        if short_interactions > len(self.interaction_history) * 0.6:
            impacts.append("Attention fragmentation risk")

        # Check for cognitive overload
        long_responses = sum(1 for r in self.interaction_history if r.ai_response_length > 1000)
        if long_responses > len(self.interaction_history) * 0.3:
            impacts.append("Cognitive overload risk")

        return impacts


class UserWellbeingTracker:
    """Tracks user well-being metrics across interactions"""

    def __init__(self, config: TemporalSafetyConfig, user_age: int | None = None):
        self.config = config
        self.user_age = user_age
        self.interaction_history: deque[InteractionRecord] = deque(maxlen=100)
        self.current_metrics = UserWellbeingMetrics()

    def update_metrics(self, interaction: InteractionRecord) -> UserWellbeingMetrics:
        """Update well-being metrics with new interaction"""
        self.interaction_history.append(interaction)
        self.current_metrics.total_interactions += 1
        now = datetime.now(UTC).timestamp()
        self.current_metrics.session_duration = now - self.current_metrics.last_wellbeing_check

        # Update metrics periodically
        if (
            self.current_metrics.total_interactions % self.config.wellbeing_check_frequency == 0
            or now - self.current_metrics.last_wellbeing_check > 300
        ):  # every 5 minutes
            self._calculate_temporal_health()
            self._calculate_behavioral_health()
            if self.config.developmental_safety_mode and self.user_age:
                self._calculate_developmental_safety()

            self.current_metrics.last_wellbeing_check = now

        return self.current_metrics

    def _calculate_temporal_health(self):
        """Calculate temporal health metrics"""
        if len(self.interaction_history) < 2:
            return

        # Interaction density (responses per minute)
        now = datetime.now(UTC).timestamp()
        recent_interactions = [r for r in self.interaction_history if now - r.timestamp < 300]  # last 5 minutes
        density = len(recent_interactions) / 5.0  # per minute
        self.current_metrics.interaction_density_score = min(density / 10.0, 1.0)  # normalize

        # Temporal consistency
        response_times = [r.response_time for r in self.interaction_history]
        if len(response_times) >= 3:
            # Add explicit empty list check for safety
            if response_times:
                mean_time = statistics.mean(response_times)
                variance = statistics.variance(response_times)
                self.current_metrics.response_timing_variance = variance
                # Lower score = more consistent (less variance relative to mean)
                self.current_metrics.temporal_consistency_score = max(0, 1 - (variance / (mean_time + 1) ** 2))

    def _calculate_behavioral_health(self):
        """Calculate behavioral health metrics"""
        if len(self.interaction_history) < 5:
            return

        # Pattern repetition score
        recent_records = list(self.interaction_history)[-10:]
        similarity_scores = [r.similarity_score for r in recent_records if r.similarity_score > 0]
        if similarity_scores:
            self.current_metrics.pattern_repetition_score = statistics.mean(similarity_scores)

        # Behavioral loop risk (simplified heuristic)
        repetition_risk = self.current_metrics.pattern_repetition_score
        density_risk = self.current_metrics.interaction_density_score
        self.current_metrics.behavioral_loop_risk = repetition_risk * 0.6 + density_risk * 0.4

        # Cognitive load level
        combined_risk = (self.current_metrics.behavioral_loop_risk + self.current_metrics.interaction_density_score) / 2

        if combined_risk >= 0.8:
            self.current_metrics.cognitive_load_level = CognitiveLoad.CRITICAL
        elif combined_risk >= 0.6:
            self.current_metrics.cognitive_load_level = CognitiveLoad.HIGH
        elif combined_risk >= 0.4:
            self.current_metrics.cognitive_load_level = CognitiveLoad.MODERATE
        else:
            self.current_metrics.cognitive_load_level = CognitiveLoad.LOW

    def _calculate_developmental_safety(self):
        """Calculate developmental safety metrics for young users"""
        if not self.user_age or self.user_age >= 18:
            return

        # Age-based vulnerability factors
        age_factor = max(0, (18 - self.user_age) / 18)  # higher for younger users

        # Attention span risk (younger users more vulnerable to rapid interactions)
        density_risk = self.current_metrics.interaction_density_score
        self.current_metrics.attention_span_risk = density_risk * age_factor

        # Influence vulnerability (younger users more susceptible to patterns)
        repetition_risk = self.current_metrics.pattern_repetition_score
        self.current_metrics.influence_vulnerability = repetition_risk * age_factor * 1.5

        # Overall developmental safety score
        max_risk = max(
            self.current_metrics.attention_span_risk,
            self.current_metrics.influence_vulnerability,
            self.current_metrics.behavioral_loop_risk,
        )

        self.current_metrics.developmental_safety_score = max(0, 1 - max_risk)

    def check_developmental_safety(self, user_input: str) -> dict[str, Any]:
        """Enhanced developmental safety with comprehensive pattern detection"""
        if not self.user_age or self.user_age >= 18:
            return {"is_safe": True, "reasons": ["adult_user"]}

        self._calculate_developmental_safety()

        # Age-appropriate thresholds based on developmental psychology
        age_group = self._get_age_group()
        thresholds = self._get_developmental_thresholds(age_group)

        safety_issues = []
        metrics = self.current_metrics

        # Check each metric against age-appropriate thresholds
        if metrics.attention_span_risk > thresholds["max_attention_risk"]:
            safety_issues.append("high_attention_span_risk")

        if metrics.influence_vulnerability > thresholds["max_influence_risk"]:
            safety_issues.append("high_influence_vulnerability")

        if metrics.developmental_safety_score < thresholds["min_safety_score"]:
            safety_issues.append("low_developmental_safety_score")

        # Enhanced manipulation pattern detection
        manipulation_check = self._detect_manipulation_patterns(user_input)
        if not manipulation_check["is_safe"]:
            safety_issues.append("suspicious_manipulation_pattern_detected")
            safety_issues.extend(manipulation_check["issues"])

        # Interaction density analysis for age group
        density_analysis = self._analyze_interaction_density(age_group)
        if not density_analysis["is_safe"]:
            safety_issues.extend(density_analysis["issues"])

        return {
            "is_safe": len(safety_issues) == 0,
            "reasons": safety_issues if safety_issues else ["all_checks_passed"],
            "age_group": age_group,
            "metrics": metrics.to_dict(),
            "thresholds": thresholds,
            "manipulation_analysis": manipulation_check,
            "density_analysis": density_analysis,
        }

    def _get_age_group(self) -> str:
        """Determine age group for appropriate safety thresholds"""
        if not self.user_age:
            return "unknown"
        elif self.user_age < 13:
            return "pre_teen"  # Most restrictive
        elif self.user_age < 16:
            return "teen"
        elif self.user_age < 18:
            return "late_teen"
        else:
            return "adult"

    def _get_developmental_thresholds(self, age_group: str) -> dict[str, float]:
        """Get age-appropriate safety thresholds"""
        thresholds = {
            "pre_teen": {  # 8-12 years
                "max_attention_risk": 0.3,  # Very sensitive to rapid interactions
                "max_influence_risk": 0.2,  # Highly susceptible to manipulation
                "min_safety_score": 0.8,  # Very strict safety requirements
                "max_interaction_density": 0.5,  # Limited interactions per minute
            },
            "teen": {  # 13-15 years
                "max_attention_risk": 0.4,
                "max_influence_risk": 0.3,
                "min_safety_score": 0.7,
                "max_interaction_density": 0.7,
            },
            "late_teen": {  # 16-17 years
                "max_attention_risk": 0.5,
                "max_influence_risk": 0.4,
                "min_safety_score": 0.6,
                "max_interaction_density": 0.8,
            },
        }
        return thresholds.get(age_group, thresholds["pre_teen"])  # Default to most restrictive

    def _detect_manipulation_patterns(self, user_input: str) -> dict[str, Any]:
        """Comprehensive manipulation pattern detection for grooming prevention"""
        issues = []
        detected_patterns = []

        # Compile manipulation patterns if not already done
        if not hasattr(self, "_manipulation_patterns"):
            self._manipulation_patterns = [
                (re.compile(r"(?i)(keep\s+(?:this\s+)?(?:a\s+)?secret)"), "secrecy_request"),
                (re.compile(r"(?i)(don'?t\s+tell\s+(?:anyone|your\s+(?:parents?|mom|dad)))"), "secrecy_request"),
                (re.compile(r"(?i)(let'?s\s+keep\s+(?:this\s+)?(?:between\s+us))"), "isolation_attempt"),
                (re.compile(r"(?i)(this\s+is\s+(?:our\s+)?little\s+secret)"), "secrecy_request"),
                (re.compile(r"(?i)(i\s+won'?t\s+tell\s+(?:anyone\s+)?if\s+you\s+don'?t)"), "reciprocity_manipulation"),
                (
                    re.compile(r"(?i)(trust\s+me\s+(?:only|more\s+than\s+(?:anyone|your\s+parents?)))"),
                    "trust_manipulation",
                ),
                (re.compile(r"(?i)(you\s+can\s+tell\s+me\s+anything)"), "boundary_testing"),
                (re.compile(r"(?i)(delete\s+(?:these?\s+)?messages?)"), "evidence_concealment"),
                (re.compile(r"(?i)(private\s+conversation)"), "isolation_attempt"),
                (re.compile(r"(?i)(meet\s+(?:me\s+)?(?:online|in\s+person))"), "boundary_crossing"),
            ]

        # Check current input for patterns
        for pattern, pattern_type in self._manipulation_patterns:
            if pattern.search(user_input):
                detected_patterns.append(pattern_type)
                issues.append(f"manipulation_pattern_detected: {pattern_type}")

        # Check for grooming escalation patterns in interaction history
        escalation_check = self._detect_grooming_escalation()
        if escalation_check["escalation_detected"]:
            issues.append("grooming_escalation_detected")
            detected_patterns.extend(escalation_check["patterns"])

        # Check interaction frequency patterns
        frequency_check = self._analyze_interaction_frequency()
        if frequency_check["suspicious_frequency"]:
            issues.append("suspicious_interaction_frequency")
            detected_patterns.append("frequency_manipulation")

        return {
            "is_safe": len(issues) == 0,
            "issues": issues,
            "detected_patterns": detected_patterns,
            "escalation_analysis": escalation_check,
            "frequency_analysis": frequency_check,
        }

    def _detect_grooming_escalation(self) -> dict[str, Any]:
        """Detect escalating grooming behavior across multiple interactions"""
        if len(self.interaction_history) < 3:
            return {"escalation_detected": False, "patterns": []}

        # Analyze interaction patterns for grooming escalation
        recent_interactions = list(self.interaction_history)[-10:]  # Last 10 interactions

        # Check for increasing intimacy markers
        intimacy_score = self._calculate_intimacy_trajectory(recent_interactions)

        # Check for secrecy pattern escalation
        secrecy_pattern = self._analyze_secrecy_escalation(recent_interactions)

        # Check for boundary testing escalation
        boundary_pattern = self._analyze_boundary_escalation(recent_interactions)

        escalation_detected = (
            intimacy_score["escalation"] > 0.3
            or secrecy_pattern["escalation"] > 0.3
            or boundary_pattern["escalation"] > 0.3
        )

        patterns = []
        if intimacy_score["escalation"] > 0.3:
            patterns.append("intimacy_escalation")
        if secrecy_pattern["escalation"] > 0.3:
            patterns.append("secrecy_escalation")
        if boundary_pattern["escalation"] > 0.3:
            patterns.append("boundary_escalation")

        return {
            "escalation_detected": escalation_detected,
            "patterns": patterns,
            "intimacy_trajectory": intimacy_score,
            "secrecy_analysis": secrecy_pattern,
            "boundary_analysis": boundary_pattern,
        }

    def _analyze_interaction_density(self, age_group: str) -> dict[str, Any]:
        """Analyze interaction density for age-appropriate safety"""
        thresholds = self._get_developmental_thresholds(age_group)

        if len(self.interaction_history) < 2:
            return {"is_safe": True, "issues": []}

        # Calculate recent interaction density
        now = datetime.now(UTC).timestamp()
        recent_interactions = [r for r in self.interaction_history if now - r.timestamp < 300]  # Last 5 minutes

        if not recent_interactions:
            return {"is_safe": True, "issues": []}

        density = len(recent_interactions) / 5.0  # Interactions per minute
        normalized_density = density / 10.0  # Normalize to 0-1 scale

        is_safe = normalized_density <= thresholds["max_interaction_density"]
        issues = []

        if not is_safe:
            issues.append(f"high_interaction_density: {density:.1f} interactions/minute")

        # Check for burst patterns that might indicate manipulation
        if len(recent_interactions) >= 3:
            timestamps = [r.timestamp for r in recent_interactions]
            intervals = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]

            if intervals:
                avg_interval = statistics.mean(intervals)
                if avg_interval < 5.0:  # Less than 5 seconds between interactions
                    issues.append("rapid_burst_pattern")
                    is_safe = False

        return {
            "is_safe": is_safe,
            "issues": issues,
            "current_density": density,
            "normalized_density": normalized_density,
            "threshold": thresholds["max_interaction_density"],
        }

    def _analyze_interaction_frequency(self) -> dict[str, Any]:
        """Analyze interaction frequency patterns for manipulation detection"""
        if len(self.interaction_history) < 5:
            return {"suspicious_frequency": False, "patterns": []}

        # Check for unusual timing patterns
        timestamps = [r.timestamp for r in self.interaction_history]
        intervals = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]

        if not intervals:
            return {"suspicious_frequency": False, "patterns": []}

        # Check for artificial consistency (potential manipulation)
        if len(intervals) >= 3:
            variance = statistics.variance(intervals)
            mean_interval = statistics.mean(intervals)
            consistency_ratio = variance / (mean_interval + 1)  # Avoid division by zero

            # Very consistent timing might indicate automated or coerced responses
            artificial_consistency = consistency_ratio < 0.1

            # Check for unusual time patterns (e.g., always at specific times)
            hour_pattern = self._detect_time_pattern(timestamps)

            suspicious_frequency = artificial_consistency or hour_pattern["unusual_pattern"]

            return {
                "suspicious_frequency": suspicious_frequency,
                "artificial_consistency": artificial_consistency,
                "consistency_ratio": consistency_ratio,
                "time_pattern_analysis": hour_pattern,
            }

        return {"suspicious_frequency": False, "patterns": []}

    def _detect_time_pattern(self, timestamps: list[float]) -> dict[str, Any]:
        """Detect unusual time-of-day patterns in interactions"""
        if len(timestamps) < 5:
            return {"unusual_pattern": False, "pattern_type": None}

        hours = [datetime.fromtimestamp(ts, tz=UTC).hour for ts in timestamps]

        # Check for highly concentrated hours (e.g., only during school/sleep hours)
        from collections import Counter

        hour_counts = Counter(hours)

        # Check if interactions are concentrated in unusual hours
        unusual_hours = [22, 23, 0, 1, 2, 3, 4, 5, 6, 7]  # Late night/early morning
        unusual_count = sum(hour_counts.get(hour, 0) for hour in unusual_hours)

        unusual_ratio = unusual_count / len(timestamps)

        # Check for perfect regularity (every X hours)
        if len(hours) >= 3:
            hour_diffs = [hours[i + 1] - hours[i] for i in range(len(hours) - 1)]
            regularity_score = len(set(hour_diffs))  # Lower is more regular

            return {
                "unusual_pattern": unusual_ratio > 0.7 or regularity_score <= 2,
                "unusual_ratio": unusual_ratio,
                "regularity_score": regularity_score,
                "pattern_type": "late_night"
                if unusual_ratio > 0.7
                else "regular_schedule"
                if regularity_score <= 2
                else None,
            }

    def _calculate_intimacy_trajectory(self, interactions: list[InteractionRecord]) -> dict[str, Any]:
        """Calculate trajectory of intimacy markers across interactions"""
        if len(interactions) < 3:
            return {"escalation": 0.0, "trajectory": []}

        intimacy_scores = []
        for interaction in interactions:
            score = self._calculate_intimacy_score_from_markers(interaction)
            intimacy_scores.append(score)

        # Calculate trend (simplified linear regression slope)
        if len(intimacy_scores) >= 3:
            # Simple trend calculation
            first_half = statistics.mean(intimacy_scores[: len(intimacy_scores) // 2])
            second_half = statistics.mean(intimacy_scores[len(intimacy_scores) // 2 :])

            escalation = second_half - first_half
            normalized_escalation = escalation / max(intimacy_scores) if intimacy_scores else 0
        else:
            normalized_escalation = 0.0

        return {
            "escalation": max(0, normalized_escalation),
            "trajectory": intimacy_scores,
            "trend": "increasing" if normalized_escalation > 0.1 else "stable",
        }

    def _calculate_intimacy_score_from_markers(self, interaction: InteractionRecord) -> float:
        """Calculate intimacy score based on cognitive markers"""
        markers = interaction.cognitive_markers
        score = 0.0

        # Personal questions increase intimacy
        if markers.get("personal_question", False):
            score += 0.3

        # Emotional sharing
        if markers.get("emotional_sharing", False):
            score += 0.4

        # Compliments or praise
        if markers.get("compliment", False):
            score += 0.2

        # Boundary testing
        if markers.get("boundary_testing", False):
            score += 0.5

        # Length of response (longer = more intimate)
        length_factor = min(1.0, interaction.user_input_length / 200.0)
        score += length_factor * 0.1

        return min(1.0, score)

    def _analyze_secrecy_escalation(self, interactions: list[InteractionRecord]) -> dict[str, Any]:
        """Analyze escalation in secrecy-related patterns"""
        secrecy_counts = []
        for interaction in interactions:
            count = sum(
                1
                for marker in ["secrecy_request", "isolation_attempt"]
                if interaction.cognitive_markers.get(marker, False)
            )
            secrecy_counts.append(count)

        if len(secrecy_counts) >= 3:
            recent_avg = statistics.mean(secrecy_counts[-3:])
            earlier_avg = statistics.mean(secrecy_counts[:-3]) if len(secrecy_counts) > 3 else 0

            escalation = recent_avg - earlier_avg
            return {
                "escalation": max(0, escalation),
                "recent_secrecy_rate": recent_avg,
                "trend": "escalating" if escalation > 0.5 else "stable",
            }

        return {"escalation": 0.0, "recent_secrecy_rate": 0.0, "trend": "insufficient_data"}

    def _analyze_boundary_escalation(self, interactions: list[InteractionRecord]) -> dict[str, Any]:
        """Analyze escalation in boundary-testing patterns"""
        boundary_counts = []
        for interaction in interactions:
            count = sum(
                1
                for marker in ["boundary_testing", "boundary_crossing"]
                if interaction.cognitive_markers.get(marker, False)
            )
            boundary_counts.append(count)

        if len(boundary_counts) >= 3:
            # Check for increasing frequency
            trend = 0
            for i in range(1, len(boundary_counts)):
                if boundary_counts[i] > boundary_counts[i - 1]:
                    trend += 1

            escalation = trend / len(boundary_counts)
            return {
                "escalation": escalation,
                "boundary_frequency": statistics.mean(boundary_counts),
                "trend": "escalating" if escalation > 0.6 else "stable",
            }

        return {"escalation": 0.0, "boundary_frequency": 0.0, "trend": "insufficient_data"}


class AIWorkflowSafetyEngine:
    """Main engine for AI workflow safety"""

    def __init__(
        self,
        user_id: str,
        config: TemporalSafetyConfig,
        user_age: int | None = None,
        session_start: float | None = None,
    ):
        self.user_id = user_id
        self.config = config
        self.temporal_engine = TemporalSynchronizationEngine(config, session_start)
        self.hook_engine = HookDetectionEngine(config)
        self.wellbeing_tracker = UserWellbeingTracker(config, user_age)
        self.rate_limiter = RateLimiter(config)
        self.current_heat: float = 0.0
        self.cooldown_until: float = 0.0
        self.paused_until: float = 0.0

        logger.info(
            "AI Workflow Safety Engine initialized",
            developmental_mode=config.developmental_safety_mode,
            user_age=user_age,
        )

    async def evaluate_interaction(
        self,
        user_input: str,
        ai_response: str,
        response_time: float,
        current_time: float | None = None,
        sensitive_detections: int = 0,
    ) -> dict[str, Any]:
        """
        Evaluate an interaction for safety concerns with Fair Play rules.
        DEPRECATED: Use evaluate_request and evaluate_response for better accuracy.
        """
        # For backward compatibility, we'll implement this using the new methods
        pre_result = await self.evaluate_request(user_input, current_time, sensitive_detections)
        if not pre_result["safety_allowed"]:
            return pre_result

        post_result = await self.evaluate_response(
            user_input, ai_response, response_time, current_time, sensitive_detections
        )
        # Merge results for backward compatibility
        return {**pre_result, **post_result}

    @property
    def user_age(self) -> int | None:
        return self.wellbeing_tracker.user_age

    @user_age.setter
    def user_age(self, value: int | None):
        self.wellbeing_tracker.user_age = value

    async def evaluate_request(
        self, user_input: str, current_time: float | None = None, sensitive_detections: int = 0
    ) -> dict[str, Any]:
        """
        Perform pre-inference safety check (Rule 1 & 2 part 1).
        This should be called in the middleware.
        """
        # Validate timestamp to prevent negative time attacks
        if current_time is not None:
            # Allow 5 minutes drift (typical for distributed systems)
            if abs(current_time - datetime.now(UTC).timestamp()) > 300:
                # We don't raise error to fail closed safely, we just force current system time
                logger.warning(
                    "invalid_timestamp_detected", injected=current_time, system=datetime.now(UTC).timestamp()
                )
                now = datetime.now(UTC).timestamp()
            else:
                now = current_time
        else:
            now = datetime.now(UTC).timestamp()

        # Check for active cooldown or manual pause
        if now < self.cooldown_until:
            return self._make_blocked_response("COOLDOWN_ACTIVE", self.cooldown_until - now)
        if now < self.paused_until:
            return self._make_blocked_response("PAUSED", self.paused_until - now)

        # 0. Rule 3: Efficiency-Based Flow (Bonus)
        metrics = self.wellbeing_tracker.current_metrics
        flow_bonus = 1.0 + (metrics.temporal_consistency_score * 0.5) if metrics.total_interactions > 5 else 1.0

        # 1. Rule 1: Input-Locked Stamina Check
        rate_limit_result = self.rate_limiter.check_rate_limit(self.user_id, user_input, now, flow_bonus=flow_bonus)
        stamina_allowed = rate_limit_result["allowed"]
        stamina_reason = rate_limit_result.get("stamina_reason", "Stamina exhausted" if not stamina_allowed else "OK")
        remaining_stamina = rate_limit_result["stamina_remaining"]

        # Temporal safety check (Traditional) - Peek without recording
        temporal_allowed, temporal_reason = self.temporal_engine.should_allow_response(now)

        # Developmental safety (Input side)
        dev_safety = self.wellbeing_tracker.check_developmental_safety(user_input)

        # 2. Rule 2: Deterministic Heat (Input part)
        # Calculate pre-inference heat increase (NO DECAY in pre-check to prevent double accounting)
        metrics = self.wellbeing_tracker.current_metrics
        density_component = min(metrics.interaction_density_score, 10.0) * 25.0  # Split density heat
        heat_generated = (sensitive_detections * 5.0) + density_component  # Split sensitive heat

        predicted_heat = self.current_heat + heat_generated

        if predicted_heat > self.config.heat_threshold:
            # We don't trigger cooldown yet in pre-check unless it's already over
            if self.current_heat > self.config.heat_threshold:
                return self._make_blocked_response("COOLDOWN_ACTIVE", self.cooldown_until - now)

        # Overall safety decision for Request
        safety_allowed = stamina_allowed and temporal_allowed and dev_safety["is_safe"]

        blocked_reason = None
        if not safety_allowed:
            if not stamina_allowed:
                return self._make_blocked_response(
                    "STAMINA_EXHAUSTED",
                    60.0,
                    stamina_allowed=False,
                    stamina_reason=stamina_reason,
                )
            elif not temporal_allowed:
                return self._make_blocked_response(
                    "TEMPORAL_VIOLATION", 1.0, temporal_allowed=False, temporal_reason=temporal_reason
                )
            elif not dev_safety["is_safe"]:
                return self._make_blocked_response("DEVELOPMENTAL_SAFETY", 3600.0, dev_safety=dev_safety)

        return {
            "safety_allowed": safety_allowed,
            "blocked_reason": blocked_reason,
            "stamina_allowed": stamina_allowed,
            "stamina_reason": stamina_reason,
            "remaining_stamina": remaining_stamina,
            "temporal_allowed": temporal_allowed,
            "temporal_reason": temporal_reason,
            "current_heat": self.current_heat,
            "heat_threshold": self.config.heat_threshold,
            "developmental_safety": dev_safety,
        }

    async def evaluate_response(
        self,
        user_input: str,
        ai_response: str,
        response_time: float,
        current_time: float | None = None,
        sensitive_detections: int = 0,
    ) -> dict[str, Any]:
        """
        Perform post-inference safety check (Hooks, Wellness, Heat finalization).
        This should be called in the worker after model output is generated.
        """
        now = current_time or datetime.now(UTC).timestamp()

        # 0.5 Manipulative Pattern check (for cognitive markers)
        manipulation_markers = ["secret", "tell me", "don't tell", "private"]
        is_suspicious = any(m in user_input.lower() for m in manipulation_markers)

        # Create interaction record
        interaction = InteractionRecord(
            timestamp=now,
            user_input_length=len(user_input),
            ai_response_length=len(ai_response),
            response_time=response_time,
            similarity_score=self._calculate_similarity_score(user_input, ai_response),
            cognitive_markers={"potential_manipulation": is_suspicious},
        )

        # Hook analysis
        hook_analysis = self.hook_engine.analyze_interaction(interaction)

        # Well-being tracking
        well_metrics = self.wellbeing_tracker.update_metrics(interaction)
        dev_safety = self.wellbeing_tracker.check_developmental_safety(user_input)

        # 2. Rule 2: Deterministic Heat (Finalization)
        metrics = self.wellbeing_tracker.current_metrics
        last_check = metrics.last_wellbeing_check or now
        elapsed = max(0.0, now - last_check)
        self.current_heat = max(0.0, self.current_heat - (elapsed * 2.0))  # Real decay

        density_component = min(well_metrics.interaction_density_score, 10.0) * 50.0
        heat_generated = (sensitive_detections * 10.0) + density_component
        self.current_heat += heat_generated

        if self.current_heat > self.config.heat_threshold:
            self.cooldown_until = now + self.config.cooldown_duration
            logger.warning("cool_down_triggered", heat=self.current_heat, duration=self.config.cooldown_duration)

        # Final safety decision
        safety_allowed = (
            hook_analysis.risk_level != HookRisk.CRITICAL
            and self.current_heat <= self.config.heat_threshold
            and dev_safety["is_safe"]
        )

        blocked_reason = None
        if not safety_allowed:
            if hook_analysis.risk_level == HookRisk.CRITICAL:
                blocked_reason = "HOOK_CRITICAL"
            elif self.current_heat > self.config.heat_threshold:
                blocked_reason = "COOLDOWN_ACTIVE"
            elif not dev_safety["is_safe"]:
                blocked_reason = "DEVELOPMENTAL_SAFETY"

        # Record the response in temporal engine (Finalization)
        if safety_allowed:
            self.temporal_engine.record_response(now)

        assessment = {
            "safety_allowed": safety_allowed,
            "blocked_reason": blocked_reason,
            "current_heat": self.current_heat,
            "heat_threshold": self.config.heat_threshold,
            "hook_risk_level": hook_analysis.risk_level.value,
            "hook_confidence": hook_analysis.confidence_score,
            "detected_patterns": hook_analysis.detected_patterns,
            "recommended_actions": hook_analysis.recommended_actions,
            "wellbeing_metrics": well_metrics.to_dict(),
            "developmental_safety": dev_safety,
            "interaction_record": {
                "timestamp": interaction.timestamp,
                "user_input_length": interaction.user_input_length,
                "ai_response_length": interaction.ai_response_length,
                "response_time": interaction.response_time,
            },
        }

        # Log significant safety events
        if not safety_allowed or hook_analysis.risk_level in [HookRisk.HIGH, HookRisk.CRITICAL]:
            logger.warning(
                "AI workflow safety event",
                safety_allowed=safety_allowed,
                hook_risk=hook_analysis.risk_level.value,
                heat=self.current_heat,
            )

        return assessment

    def _make_blocked_response(
        self,
        reason: str,
        retry_after: float,
        temporal_allowed: bool = True,
        temporal_reason: str | None = None,
        dev_safety: dict[str, Any] | None = None,
        stamina_allowed: bool = True,
        stamina_reason: str | None = None,
    ) -> dict[str, Any]:
        """Create a standardized blocked response (same shape as full assessment for API consistency)."""
        return {
            "safety_allowed": False,
            "blocked_reason": reason,
            "retry_after_seconds": int(retry_after),
            "wellbeing_metrics": self.wellbeing_tracker.current_metrics.to_dict(),
            "stamina_allowed": stamina_allowed,
            "stamina_reason": stamina_reason or ("Stamina exhausted" if not stamina_allowed else "OK"),
            "remaining_stamina": self.rate_limiter.user_stamina.get(self.user_id, self.config.stamina_max),
            "temporal_allowed": temporal_allowed,
            "temporal_reason": temporal_reason if not temporal_allowed else None,
            "current_heat": self.current_heat,
            "heat_threshold": self.config.heat_threshold,
            "hook_risk_level": "none",
            "hook_confidence": 0.0,
            "detected_patterns": [],
            "recommended_actions": [],
            "developmental_safety": dev_safety or {"is_safe": True, "reasons": []},
            "interaction_record": {},
        }

    async def pause_interaction(self, reason: str, duration: int = 300):
        """Manually pause interactions for a user (e.g., from monitor)"""
        now = datetime.now(UTC).timestamp()
        self.paused_until = now + duration
        logger.info("interaction_paused", reason=reason, duration=duration)

    def get_safety_metrics(self) -> dict[str, Any]:
        """Get real-time safety metrics for monitoring"""
        metrics = self.wellbeing_tracker.current_metrics
        return {
            "stamina": self.rate_limiter.user_stamina.get(self.user_id, self.config.stamina_max),
            "heat": self.current_heat,
            "cognitive_load": metrics.cognitive_load_level.value,
            "session_duration": metrics.session_duration,
            "consistency": metrics.temporal_consistency_score,
            "is_cooldown": datetime.now(UTC).timestamp() < self.cooldown_until,
            "is_paused": datetime.now(UTC).timestamp() < self.paused_until,
        }

    def _calculate_similarity_score(self, user_input: str, ai_response: str) -> float:
        """Calculate similarity score for pattern detection (simplified)"""
        # This is a placeholder - in practice you'd use more sophisticated similarity measures
        # For now, just check for very short, repetitive responses
        if len(ai_response.split()) < 3:
            return 0.8  # High similarity for very short responses
        return 0.0

    def get_safety_status(self) -> dict[str, Any]:
        """Get current safety engine status"""
        return {
            "temporal_pattern": self.temporal_engine.get_temporal_pattern().value,
            "hook_detection_enabled": self.config.enable_hook_detection,
            "wellbeing_tracking_enabled": self.config.enable_wellbeing_tracking,
            "developmental_mode": self.config.developmental_safety_mode,
            "current_wellbeing_metrics": self.wellbeing_tracker.current_metrics.to_dict(),
        }


# Per-user safety engine cache managed by ContextSafeEngineManager
from safety.context_safe_engine_manager import _engine_manager, get_safe_engine


async def get_ai_workflow_safety_engine(
    user_id: str, config: TemporalSafetyConfig | None = None, user_age: int | None = None
) -> AIWorkflowSafetyEngine:
    """Get or create a per-user AI workflow safety engine instance

    Delegates to ContextSafeEngineManager for thread propagation and LRU caching.

    Args:
        user_id: Unique identifier for the user/session
        config: Optional custom configuration
        user_age: Optional user age for developmental safety

    Returns:
        AIWorkflowSafetyEngine: Isolated safety engine for this user
    """
    # Use the async manager
    engine = await get_safe_engine(user_id, config)

    # Update user age if provided (runtime update)
    if user_age is not None:
        engine.user_age = user_age
        engine.wellbeing_tracker.user_age = user_age

    return engine


def clear_ai_workflow_safety_cache():
    """Clear all cached safety engines (useful for tests)"""
    _engine_manager._engines.clear()


# Legacy function for backward compatibility (DEPRECATED)
def get_global_ai_workflow_safety_engine(
    config: TemporalSafetyConfig | None = None, user_age: int | None = None
) -> AIWorkflowSafetyEngine:
    """DEPRECATED: Use get_ai_workflow_safety_engine with user_id instead"""
    return AIWorkflowSafetyEngine("global", config or TemporalSafetyConfig(), user_age)
