"""
Pattern Archetype Detection System

Detects behavioral patterns in modules inspired by:
- Music industry: viral hits, steady climbers, one-hit wonders, catalog tracks
- Market analysis: growth stocks, value stocks, volatile assets
- Product design: viral products, slow burners, fads
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import math


class ModulePatternArchetype(Enum):
    """
    Pattern archetypes inspired by cross-domain analysis.
    
    These patterns help predict module behavior and potential issues.
    """
    
    # High Growth Patterns (Market: Growth stocks, Music: Breakout hits)
    VIRAL_SPIKE = "viral_spike"           # Sudden rapid adoption (high risk)
    STEADY_CLIMBER = "steady_climber"     # Consistent, sustainable growth (low risk)
    PLATFORM_BOOST = "platform_boost"     # Adoption due to framework feature
    
    # Volatile Patterns (Market: Penny stocks, Music: Flash-in-pan)
    FLASH_IN_PAN = "flash_in_pan"         # Rapid adoption then abandonment
    ROLLERCOASTER = "rollercoaster"       # Erratic adoption patterns
    
    # Stable Patterns (Market: Blue-chip, Music: Catalog artists)
    SLEEPING_GIANT = "sleeping_giant"     # High quality, underutilized
    STEADY_WORKHORSE = "steady_workhorse" # Consistent, reliable usage
    CATALOG_STABLE = "catalog_stable"     # Long-term stability, rarely changes
    
    # Crossover Patterns (Market: Conglomerates, Music: Genre-blenders)
    CROSSOVER = "crossover"               # Used across multiple architecture layers
    BRIDGE = "bridge"                     # Connects otherwise separate systems
    
    # Problematic Patterns (Market: Distressed assets, Music: Flops)
    ONE_HIT_WONDER = "one_hit_wonder"     # Brief popularity then orphaned
    DECLINING = "declining"               # Losing adoption over time
    ORPHANED = "orphaned"                 # No longer used by anyone
    
    # Unique Patterns
    UNIQUE = "unique"                     # Doesn't fit any pattern (innovator)
    UNDETERMINED = "undetermined"         # Insufficient data to classify


@dataclass
class PatternMetrics:
    """Metrics used for pattern detection."""
    
    # Adoption metrics
    current_dependents: int
    dependent_growth_rate: float  # Change in dependents over time
    peak_dependents: int
    
    # Velocity metrics
    recent_change_velocity: float  # How fast is module changing
    integration_velocity: float  # How fast is adoption changing
    
    # Stability metrics
    uptime_score: float  # Reliability track record
    breaking_change_frequency: float
    
    # Cross-layer metrics
    layer_diversity: int  # How many architecture layers use this
    cross_layer_ratio: float  # % of dependents from different layers
    
    # Time-based metrics
    first_seen: datetime
    last_updated: datetime
    days_since_creation: int
    
    @property
    def maturity_score(self) -> float:
        """Calculate maturity based on age and stability."""
        age_factor = min(self.days_since_creation / 365, 1.0)  # Max at 1 year
        stability_factor = 1.0 - self.recent_change_velocity
        return (age_factor + stability_factor) / 2


class PatternArchetypeDetector:
    """
    Detects pattern archetypes in module behavior.
    
    Inspired by:
    - Chartmetric's artist trajectory classification
    - Financial technical analysis pattern recognition
    - Product lifecycle pattern detection
    """
    
    def __init__(self):
        # Pattern detection thresholds
        self.thresholds = {
            'viral_growth_rate': 0.5,      # 50% growth in short period
            'steady_growth_rate': 0.1,     # 10% consistent growth
            'flash_threshold': 0.7,        # 70% of peak then decline
            'crossover_ratio': 0.3,          # 30% cross-layer adoption
            'rollercoaster_variance': 0.4,   # High variance in growth
        }
    
    def detect_pattern(
        self,
        metrics_history: List[PatternMetrics],
        current_metrics: PatternMetrics
    ) -> Tuple[ModulePatternArchetype, float]:
        """
        Detect pattern archetype from metrics history.
        
        Returns:
            (pattern, confidence_score)
        """
        if len(metrics_history) < 3:
            return (ModulePatternArchetype.UNDETERMINED, 0.0)
        
        # Calculate pattern match scores
        scores = {}
        
        # Viral Spike: Sudden rapid growth
        scores[ModulePatternArchetype.VIRAL_SPIKE] = self._score_viral_spike(
            metrics_history, current_metrics
        )
        
        # Steady Climber: Consistent, sustainable growth
        scores[ModulePatternArchetype.STEADY_CLIMBER] = self._score_steady_climber(
            metrics_history, current_metrics
        )
        
        # Flash in Pan: Rapid growth then decline
        scores[ModulePatternArchetype.FLASH_IN_PAN] = self._score_flash_in_pan(
            metrics_history, current_metrics
        )
        
        # Sleeping Giant: High quality, low adoption
        scores[ModulePatternArchetype.SLEEPING_GIANT] = self._score_sleeping_giant(
            metrics_history, current_metrics
        )
        
        # Steady Workhorse: Consistent usage, stable
        scores[ModulePatternArchetype.STEADY_WORKHORSE] = self._score_steady_workhorse(
            metrics_history, current_metrics
        )
        
        # Crossover: Used across multiple layers
        scores[ModulePatternArchetype.CROSSOVER] = self._score_crossover(
            metrics_history, current_metrics
        )
        
        # One Hit Wonder: Brief popularity then orphaned
        scores[ModulePatternArchetype.ONE_HIT_WONDER] = self._score_one_hit_wonder(
            metrics_history, current_metrics
        )
        
        # Declining: Losing adoption
        scores[ModulePatternArchetype.DECLINING] = self._score_declining(
            metrics_history, current_metrics
        )
        
        # Rollercoaster: Erratic patterns
        scores[ModulePatternArchetype.ROLLERCOASTER] = self._score_rollercoaster(
            metrics_history, current_metrics
        )
        
        # Catalog Stable: Long-term stability
        scores[ModulePatternArchetype.CATALOG_STABLE] = self._score_catalog_stable(
            metrics_history, current_metrics
        )
        
        # Determine winning pattern
        best_pattern = max(scores, key=scores.get)
        best_score = scores[best_pattern]
        
        # Check if confidence is high enough
        if best_score < 0.3:
            return (ModulePatternArchetype.UNIQUE, best_score)
        
        return (best_pattern, best_score)
    
    def _score_viral_spike(
        self,
        history: List[PatternMetrics],
        current: PatternMetrics
    ) -> float:
        """Score viral spike pattern (sudden rapid adoption)."""
        if len(history) < 3:
            return 0.0
        
        # Check for sudden growth spike
        recent_growth = current.dependent_growth_rate
        historical_avg = sum(m.dependent_growth_rate for m in history[:-3]) / max(len(history) - 3, 1)
        
        if historical_avg <= 0:
            historical_avg = 0.01  # Avoid division by zero
        
        growth_ratio = recent_growth / historical_avg
        
        # High ratio = viral spike
        if growth_ratio > 10 and recent_growth > self.thresholds['viral_growth_rate']:
            return min(growth_ratio / 20, 1.0)  # Normalize to 0-1
        
        return 0.0
    
    def _score_steady_climber(
        self,
        history: List[PatternMetrics],
        current: PatternMetrics
    ) -> float:
        """Score steady climber pattern (consistent sustainable growth)."""
        if len(history) < 5:
            return 0.0
        
        # Check for consistent positive growth
        growth_rates = [m.dependent_growth_rate for m in history[-5:]]
        
        # All should be positive and steady
        if all(g > 0 for g in growth_rates):
            avg_growth = sum(growth_rates) / len(growth_rates)
            variance = sum((g - avg_growth) ** 2 for g in growth_rates) / len(growth_rates)
            
            # Low variance + positive growth = steady climber
            if variance < 0.01 and avg_growth > 0.05:
                return 0.7 + (avg_growth * 3)  # Up to 1.0
        
        return 0.0
    
    def _score_flash_in_pan(
        self,
        history: List[PatternMetrics],
        current: PatternMetrics
    ) -> float:
        """Score flash in pan pattern (rapid growth then decline)."""
        if len(history) < 5 or current.peak_dependents == 0:
            return 0.0
        
        # Check if we reached a peak and then declined significantly
        current_ratio = current.current_dependents / current.peak_dependents
        
        if current_ratio < self.thresholds['flash_threshold']:
            # Was there a rapid rise before the fall?
            peak_idx = max(range(len(history)), key=lambda i: history[i].current_dependents)
            
            if peak_idx > 1:  # Must have had time to rise
                pre_peak_growth = (history[peak_idx].current_dependents / 
                                 max(history[0].current_dependents, 1))
                
                if pre_peak_growth > 2:  # Doubled before peak
                    return 0.5 + (1 - current_ratio) * 0.5
        
        return 0.0
    
    def _score_sleeping_giant(
        self,
        history: List[PatternMetrics],
        current: PatternMetrics
    ) -> float:
        """Score sleeping giant pattern (high quality, low adoption)."""
        # High quality indicators
        high_quality = (
            current.uptime_score > 0.9 and
            current.breaking_change_frequency < 0.1 and
            current.recent_change_velocity < 0.1
        )
        
        # Low adoption
        low_adoption = current.current_dependents < 5
        
        # Mature module
        mature = current.maturity_score > 0.5
        
        if high_quality and low_adoption and mature:
            return 0.8
        elif high_quality and low_adoption:
            return 0.5
        
        return 0.0
    
    def _score_steady_workhorse(
        self,
        history: List[PatternMetrics],
        current: PatternMetrics
    ) -> float:
        """Score steady workhorse pattern (consistent usage, stable)."""
        # Consistent dependents over time
        if len(history) < 5:
            return 0.0
        
        dependents = [m.current_dependents for m in history[-5:]]
        variance = self._calculate_variance(dependents)
        
        # Low variance + decent adoption
        if variance < 0.1 and current.current_dependents > 3:
            # High uptime
            if current.uptime_score > 0.8:
                return 0.7 + (current.uptime_score - 0.8) * 1.5
        
        return 0.0
    
    def _score_crossover(
        self,
        history: List[PatternMetrics],
        current: PatternMetrics
    ) -> float:
        """Score crossover pattern (used across multiple architecture layers)."""
        # High cross-layer ratio
        if current.cross_layer_ratio > self.thresholds['crossover_ratio']:
            return 0.5 + (current.cross_layer_ratio - self.thresholds['crossover_ratio']) * 1.5
        
        # Multiple layers
        if current.layer_diversity >= 3:
            return 0.4 + (current.layer_diversity - 3) * 0.1
        
        return 0.0
    
    def _score_one_hit_wonder(
        self,
        history: List[PatternMetrics],
        current: PatternMetrics
    ) -> float:
        """Score one hit wonder pattern (brief popularity then orphaned)."""
        if current.current_dependents > 0:
            return 0.0
        
        # Previously had dependents but now has none
        if current.peak_dependents > 2:
            # Short lifecycle
            if current.days_since_creation < 90:
                return 0.7
            return 0.5
        
        return 0.0
    
    def _score_declining(
        self,
        history: List[PatternMetrics],
        current: PatternMetrics
    ) -> float:
        """Score declining pattern (losing adoption over time)."""
        if len(history) < 5:
            return 0.0
        
        # Check for consistent decline
        recent = history[-5:]
        dependents_trend = [m.current_dependents for m in recent]
        
        # Declining trend
        if all(dependents_trend[i] >= dependents_trend[i+1] for i in range(len(dependents_trend)-1)):
            if dependents_trend[0] > dependents_trend[-1] * 1.5:  # 50% decline
                decline_ratio = dependents_trend[-1] / dependents_trend[0]
                return 0.5 + (1 - decline_ratio) * 0.5
        
        return 0.0
    
    def _score_rollercoaster(
        self,
        history: List[PatternMetrics],
        current: PatternMetrics
    ) -> float:
        """Score rollercoaster pattern (erratic adoption patterns)."""
        if len(history) < 5:
            return 0.0
        
        # High variance in adoption
        growth_rates = [m.dependent_growth_rate for m in history[-5:]]
        variance = self._calculate_variance(growth_rates)
        
        if variance > self.thresholds['rollercoaster_variance']:
            return min(variance * 2, 1.0)
        
        return 0.0
    
    def _score_catalog_stable(
        self,
        history: List[PatternMetrics],
        current: PatternMetrics
    ) -> float:
        """Score catalog stable pattern (long-term stability)."""
        # Old module
        if current.days_since_creation < 365:
            return 0.0
        
        # Stable
        if current.maturity_score > 0.8 and current.recent_change_velocity < 0.05:
            # High adoption
            if current.current_dependents > 10:
                return 0.9
            return 0.7
        
        return 0.0
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        
        # Normalize by mean to get coefficient of variation
        if mean != 0:
            return variance / (mean ** 2)
        return variance
    
    def get_pattern_recommendations(
        self,
        pattern: ModulePatternArchetype,
        confidence: float
    ) -> Dict[str, Any]:
        """Get recommendations based on detected pattern."""
        
        recommendations = {
            ModulePatternArchetype.VIRAL_SPIKE: {
                'risk_level': 'high',
                'description': 'Module experiencing sudden rapid adoption',
                'concerns': [
                    'May have unproven stability',
                    'API may not be mature',
                    'Breaking changes likely'
                ],
                'recommendations': [
                    'Monitor for stability issues',
                    'Add comprehensive tests',
                    'Document API clearly',
                    'Prepare for breaking change requests'
                ],
                'timeline': 'Monitor closely for 2-4 weeks'
            },
            
            ModulePatternArchetype.STEADY_CLIMBER: {
                'risk_level': 'low',
                'description': 'Module with consistent, sustainable growth',
                'concerns': [
                    'None significant'
                ],
                'recommendations': [
                    'Consider promoting to core',
                    'Add performance benchmarks',
                    'Document best practices'
                ],
                'timeline': 'Standard maintenance'
            },
            
            ModulePatternArchetype.FLASH_IN_PAN: {
                'risk_level': 'high',
                'description': 'Module gained rapid popularity then lost adoption',
                'concerns': [
                    'May have fundamental issues',
                    'API design problems',
                    'Better alternatives exist'
                ],
                'recommendations': [
                    'Investigate reasons for decline',
                    'Consider deprecation',
                    'Migrate dependents to alternatives'
                ],
                'timeline': 'Plan deprecation within 3-6 months'
            },
            
            ModulePatternArchetype.SLEEPING_GIANT: {
                'risk_level': 'low',
                'description': 'High quality module with low adoption',
                'concerns': [
                    'Underutilized resource',
                    'May lack visibility'
                ],
                'recommendations': [
                    'Promote module to teams',
                    'Add to recommended modules list',
                    'Create usage examples'
                ],
                'timeline': 'Promote over 1-2 months'
            },
            
            ModulePatternArchetype.STEADY_WORKHORSE: {
                'risk_level': 'low',
                'description': 'Reliable module with consistent usage',
                'concerns': [
                    'May become legacy if not maintained'
                ],
                'recommendations': [
                    'Regular maintenance',
                    'Keep dependencies updated',
                    'Monitor for modernization needs'
                ],
                'timeline': 'Standard maintenance'
            },
            
            ModulePatternArchetype.CROSSOVER: {
                'risk_level': 'medium',
                'description': 'Module used across multiple architecture layers',
                'concerns': [
                    'Breaking changes affect many systems',
                    'Difficult to refactor',
                    'May violate separation of concerns'
                ],
                'recommendations': [
                    'Enforce strict backward compatibility',
                    'Add integration tests',
                    'Consider splitting by layer',
                    'Document cross-layer usage'
                ],
                'timeline': 'Monitor continuously'
            },
            
            ModulePatternArchetype.ONE_HIT_WONDER: {
                'risk_level': 'medium',
                'description': 'Module had brief popularity then abandoned',
                'concerns': [
                    'Orphaned code',
                    'Technical debt',
                    'Security issues may go unpatched'
                ],
                'recommendations': [
                    'Evaluate for removal',
                    'Check for security vulnerabilities',
                    'Document alternatives'
                ],
                'timeline': 'Evaluate for removal within 1 month'
            },
            
            ModulePatternArchetype.DECLINING: {
                'risk_level': 'medium',
                'description': 'Module losing adoption over time',
                'concerns': [
                    'May become legacy',
                    'Maintenance burden'
                ],
                'recommendations': [
                    'Plan deprecation strategy',
                    'Communicate with remaining users',
                    'Provide migration guide'
                ],
                'timeline': 'Plan deprecation within 6 months'
            },
            
            ModulePatternArchetype.CATALOG_STABLE: {
                'risk_level': 'low',
                'description': 'Long-term stable, mature module',
                'concerns': [
                    'May resist needed modernization'
                ],
                'recommendations': [
                    'Maintain stability',
                    'Security updates only',
                    'Document as reference implementation'
                ],
                'timeline': 'Long-term support'
            },
            
            ModulePatternArchetype.UNIQUE: {
                'risk_level': 'unknown',
                'description': 'Module with unique pattern not matching archetypes',
                'concerns': [
                    'Unknown behavior patterns',
                    'Difficult to predict'
                ],
                'recommendations': [
                    'Monitor closely',
                    'Collect more metrics',
                    'Document special characteristics'
                ],
                'timeline': 'Evaluate after more data collected'
            }
        }
        
        return recommendations.get(pattern, {
            'risk_level': 'unknown',
            'description': 'Unknown pattern',
            'concerns': ['Insufficient data'],
            'recommendations': ['Monitor module behavior'],
            'timeline': 'Re-evaluate in 30 days'
        })


def detect_module_pattern(
    module_name: str,
    metrics_history: List[PatternMetrics]
) -> Tuple[ModulePatternArchetype, float, Dict[str, Any]]:
    """
    Convenience function to detect pattern for a module.
    
    Returns:
        (pattern, confidence, recommendations)
    """
    if not metrics_history:
        return (ModulePatternArchetype.UNDETERMINED, 0.0, {})
    
    detector = PatternArchetypeDetector()
    current = metrics_history[-1]
    
    pattern, confidence = detector.detect_pattern(metrics_history, current)
    recommendations = detector.get_pattern_recommendations(pattern, confidence)
    
    return (pattern, confidence, recommendations)
