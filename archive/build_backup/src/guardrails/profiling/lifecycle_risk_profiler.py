"""
Module Lifecycle & Risk Profiling System

Enhanced profiling based on cross-domain pattern analysis from market analysis,
product design trends, and music industry analytics.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import math


class ModuleLifecycleStage(Enum):
    """
    Lifecycle classification mirroring market/product/music industry stages.
    
    Based on cross-domain analysis:
    - Market: IPO → Early growth → Bull market → Blue-chip → Decline → Turnaround
    - Product: Concept → Beta → Market penetration → Category leader → Discontinued → Reboot
    - Music: Demo → Indie → Breakout → Chart topper → Catalog → Comeback
    """
    
    # Nascent/Emerging (High risk, high change rate)
    PROTOTYPE = "prototype"          # Experimental, unstable, API changes frequently
    DEVELOPMENT = "development"        # Active development, stabilizing APIs
    
    # Growth (Moderate risk, adoption increasing)
    EMERGING = "emerging"            # Gaining adoption, stabilizing interfaces
    INTEGRATING = "integrating"      # Being adopted by other modules
    
    # Peak/Mature (Low risk, stable)
    CORE = "core"                    # Critical infrastructure, very stable
    CATALOG = "catalog"              # Mature, rarely changes, reliable
    
    # Decline/Revival (Variable risk, depending on strategy)
    LEGACY = "legacy"                # Deprecated but still used (maintenance mode)
    REFACTORING = "refactoring"      # Being modernized (temporary instability)
    
    # Special states
    UNKNOWN = "unknown"              # Insufficient data to classify
    ORPHANED = "orphaned"           # No longer maintained, no dependents


@dataclass
class ModuleRiskProfile:
    """
    Composite risk score inspired by Chartmetric artist analytics and
    financial multi-factor risk models.
    
    Tracks 6 dimensions of module health:
    1. Dependency Health (external ecosystem stability)
    2. Runtime Stability (internal code quality)
    3. Integration Complexity (architectural coupling)
    4. Purity Score (side effect minimization)
    5. Circular Dependency Risk (graph topology health)
    6. Historical Reliability (track record)
    """
    
    module_name: str
    
    # Dimension 1: Dependency Health Score (0-100, higher is better)
    # Inspired by: Market dependency on economic indicators
    dependency_health: float = 50.0
    
    # Dimension 2: Runtime Stability Score (0-100, higher is better)
    # Inspired by: Product stability and crash rates
    runtime_stability: float = 50.0
    
    # Dimension 3: Integration Complexity Score (0-100, lower is better)
    # Inspired by: Music cross-platform integration complexity
    integration_complexity: float = 50.0
    
    # Dimension 4: Purity Score (0-100, higher is better)
    # Side effect minimization (functional programming principles)
    purity_score: float = 50.0
    
    # Dimension 5: Circular Dependency Risk (0-100, lower is better)
    # Inspired by: Market circular dependencies (e.g., bank interconnections)
    circular_risk: float = 0.0
    
    # Dimension 6: Historical Reliability (0-100, higher is better)
    # Track record of incidents (like artist consistency)
    historical_reliability: float = 75.0
    
    # Lifecycle classification
    lifecycle_stage: ModuleLifecycleStage = ModuleLifecycleStage.UNKNOWN
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.utcnow)
    data_points: int = 1
    
    # Dimension weights (customizable per organization)
    _weights: Dict[str, float] = field(default_factory=lambda: {
        'dependency_health': 0.20,
        'runtime_stability': 0.25,
        'integration_complexity': 0.15,
        'purity_score': 0.15,
        'circular_risk': 0.15,
        'historical_reliability': 0.10
    })
    
    @property
    def composite_risk_score(self) -> float:
        """
        Weighted composite risk score (0-100, lower is better).
        
        Algorithm inspired by:
        - Chartmetric's Artist Score (multi-platform aggregation)
        - Credit scoring models (weighted factors)
        - Financial beta calculations (risk vs stability)
        """
        # Invert scores where lower is better
        risk_factors = {
            'dependency_health': (100 - self.dependency_health) * self._weights['dependency_health'],
            'runtime_stability': (100 - self.runtime_stability) * self._weights['runtime_stability'],
            'integration_complexity': self.integration_complexity * self._weights['integration_complexity'],
            'purity_score': (100 - self.purity_score) * self._weights['purity_score'],
            'circular_risk': self.circular_risk * self._weights['circular_risk'],
            'historical_reliability': (100 - self.historical_reliability) * self._weights['historical_reliability']
        }
        
        return sum(risk_factors.values())
    
    @property
    def risk_category(self) -> str:
        """
        Risk category based on composite score.
        
        Categories inspired by:
        - Credit ratings (AAA → D)
        - Music chart tiers (Top 10 → Uncharted)
        - Market volatility classifications
        """
        score = self.composite_risk_score
        
        if score < 20:
            return "AAA"  # Excellent
        elif score < 35:
            return "AA"   # Very good
        elif score < 50:
            return "A"    # Good
        elif score < 65:
            return "BBB"  # Adequate
        elif score < 75:
            return "BB"   # Moderate risk
        elif score < 85:
            return "B"    # High risk
        elif score < 95:
            return "CCC"  # Very high risk
        else:
            return "D"    # Default/crippled
    
    @property
    def lifecycle_risk_adjustment(self) -> float:
        """
        Risk adjustment factor based on lifecycle stage.
        
        Different stages have different risk tolerances:
        - Prototype: High risk expected
        - Core: Low risk expected
        - Legacy: Moderate risk (technical debt)
        """
        stage_multipliers = {
            ModuleLifecycleStage.PROTOTYPE: 0.5,      # Expected to be risky
            ModuleLifecycleStage.DEVELOPMENT: 0.7,    # Still stabilizing
            ModuleLifecycleStage.EMERGING: 0.9,       # Becoming stable
            ModuleLifecycleStage.INTEGRATING: 0.95,   # Almost stable
            ModuleLifecycleStage.CORE: 1.0,           # Full strictness
            ModuleLifecycleStage.CATALOG: 1.0,        # Full strictness
            ModuleLifecycleStage.LEGACY: 0.8,         # Some tolerance
            ModuleLifecycleStage.REFACTORING: 0.6,   # Temporary instability
            ModuleLifecycleStage.UNKNOWN: 0.75,       # Unknown = moderate
            ModuleLifecycleStage.ORPHANED: 0.3,       # Not critical
        }
        
        return stage_multipliers.get(self.lifecycle_stage, 0.75)
    
    @property
    def adjusted_risk_score(self) -> float:
        """Risk score adjusted for lifecycle stage expectations."""
        return self.composite_risk_score * self.lifecycle_risk_adjustment
    
    def should_trigger_guardrail(self, threshold: str = "BBB") -> bool:
        """
        Determine if guardrail enforcement should trigger.
        
        Threshold mapping:
        - "AAA": Only block critical issues (score > 20)
        - "AA": Block high-risk (score > 35)
        - "A": Block moderate+ risk (score > 50)
        - "BBB": Standard enforcement (score > 65)
        - "BB": Strict enforcement (score > 75)
        - "B": Very strict (score > 85)
        """
        thresholds = {
            "AAA": 20, "AA": 35, "A": 50,
            "BBB": 65, "BB": 75, "B": 85,
            "CCC": 95, "D": 100
        }
        
        return self.adjusted_risk_score > thresholds.get(threshold, 65)
    
    def get_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate prioritized improvement recommendations.
        
        Priorities based on:
        1. Current score gaps (biggest improvement potential)
        2. Weight in composite (high-weight dimensions first)
        3. Lifecycle stage (stage-appropriate recommendations)
        """
        recommendations = []
        
        # Check each dimension for improvement opportunity
        dimensions = [
            ('dependency_health', self.dependency_health, 'high'),
            ('runtime_stability', self.runtime_stability, 'high'),
            ('integration_complexity', 100 - self.integration_complexity, 'high'),
            ('purity_score', self.purity_score, 'medium'),
            ('circular_risk', 100 - self.circular_risk, 'high'),
            ('historical_reliability', self.historical_reliability, 'low')
        ]
        
        # Sort by gap from perfect (100) * weight
        weighted_gaps = []
        for dim_name, score, priority in dimensions:
            weight = self._weights.get(dim_name, 0.1)
            gap = (100 - score) * weight
            weighted_gaps.append((dim_name, gap, score, priority))
        
        weighted_gaps.sort(key=lambda x: x[1], reverse=True)
        
        # Generate recommendations for top gaps
        for dim_name, gap, current_score, priority in weighted_gaps[:3]:
            if gap > 10:  # Only recommend if significant gap
                rec = self._generate_dimension_recommendation(dim_name, current_score)
                rec['priority'] = priority
                rec['improvement_potential'] = f"{gap:.1f} points"
                recommendations.append(rec)
        
        return recommendations
    
    def _generate_dimension_recommendation(self, dimension: str, current_score: float) -> Dict[str, Any]:
        """Generate recommendation for a specific dimension."""
        
        recommendations = {
            'dependency_health': {
                'dimension': 'Dependency Health',
                'current_score': current_score,
                'suggestions': [
                    'Update outdated dependencies',
                    'Pin dependency versions',
                    'Audit for security vulnerabilities',
                    'Remove unused dependencies'
                ],
                'impact': 'Reduces external failure points'
            },
            'runtime_stability': {
                'dimension': 'Runtime Stability',
                'current_score': current_score,
                'suggestions': [
                    'Add comprehensive test coverage',
                    'Implement error handling',
                    'Fix conditional import issues',
                    'Add runtime type checking'
                ],
                'impact': 'Prevents runtime failures'
            },
            'integration_complexity': {
                'dimension': 'Integration Complexity',
                'current_score': current_score,
                'suggestions': [
                    'Reduce import dependencies',
                    'Implement interface segregation',
                    'Use dependency injection',
                    'Create facade layer'
                ],
                'impact': 'Easier to integrate and test'
            },
            'purity_score': {
                'dimension': 'Code Purity',
                'current_score': current_score,
                'suggestions': [
                    'Remove module-level side effects',
                    'Encapsulate global state',
                    'Make functions pure where possible',
                    'Use dependency injection'
                ],
                'impact': 'More predictable, testable code'
            },
            'circular_risk': {
                'dimension': 'Circular Dependency Risk',
                'current_score': current_score,
                'suggestions': [
                    'Extract shared code to separate module',
                    'Use dependency inversion principle',
                    'Create abstraction layer',
                    'Refactor to remove cycles'
                ],
                'impact': 'Prevents import failures'
            },
            'historical_reliability': {
                'dimension': 'Historical Reliability',
                'current_score': current_score,
                'suggestions': [
                    'Document known issues',
                    'Create incident response plan',
                    'Add monitoring and alerts',
                    'Implement graceful degradation'
                ],
                'impact': 'Better handling of edge cases'
            }
        }
        
        return recommendations.get(dimension, {
            'dimension': dimension,
            'current_score': current_score,
            'suggestions': ['Review and improve'],
            'impact': 'General improvement'
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'module_name': self.module_name,
            'composite_risk_score': self.composite_risk_score,
            'adjusted_risk_score': self.adjusted_risk_score,
            'risk_category': self.risk_category,
            'lifecycle_stage': self.lifecycle_stage.value,
            'dimensions': {
                'dependency_health': self.dependency_health,
                'runtime_stability': self.runtime_stability,
                'integration_complexity': self.integration_complexity,
                'purity_score': self.purity_score,
                'circular_risk': self.circular_risk,
                'historical_reliability': self.historical_reliability
            },
            'last_updated': self.last_updated.isoformat(),
            'data_points': self.data_points
        }


class ModuleLifecycleAnalyzer:
    """
    Analyzes module characteristics to determine lifecycle stage.
    
    Inspired by:
    - Music industry artist career stage classification
    - Product lifecycle management (PLM)
    - Software maturity models (CMM)
    """
    
    def __init__(self):
        self.stage_indicators = {
            ModuleLifecycleStage.PROTOTYPE: [
                'experimental', 'draft', 'wip', 'todo', 'fixme'
            ],
            ModuleLifecycleStage.DEVELOPMENT: [
                'beta', 'alpha', 'dev', 'develop'
            ],
            ModuleLifecycleStage.EMERGING: [
                'new', 'recent', 'v0', 'initial'
            ],
            ModuleLifecycleStage.CORE: [
                'main', 'core', 'essential', 'foundation'
            ],
            ModuleLifecycleStage.CATALOG: [
                'stable', 'mature', 'v1', 'legacy'
            ],
            ModuleLifecycleStage.LEGACY: [
                'deprecated', 'obsolete', 'old'
            ],
            ModuleLifecycleStage.REFACTORING: [
                'refactor', 'rewrite', 'modernize'
            ]
        }
    
    def analyze_lifecycle_stage(
        self,
        module_name: str,
        module_path: str,
        import_count: int,
        dependent_count: int,
        change_frequency: float,
        has_tests: bool,
        documentation_quality: str
    ) -> ModuleLifecycleStage:
        """
        Determine lifecycle stage based on multiple signals.
        
        Signals:
        - Naming conventions (path indicators)
        - Import/dependent ratio (adoption rate)
        - Change frequency (stability)
        - Test coverage (maturity)
        - Documentation (professionalization)
        """
        scores = defaultdict(int)
        
        # Check naming conventions
        path_lower = module_path.lower()
        name_lower = module_name.lower()
        
        for stage, indicators in self.stage_indicators.items():
            for indicator in indicators:
                if indicator in path_lower or indicator in name_lower:
                    scores[stage] += 2
        
        # Analyze adoption (import/dependent ratio)
        # Inspired by music industry: streams + playlist adds
        if dependent_count == 0:
            scores[ModuleLifecycleStage.PROTOTYPE] += 2
        elif dependent_count < 3:
            scores[ModuleLifecycleStage.DEVELOPMENT] += 1
        elif dependent_count < 10:
            scores[ModuleLifecycleStage.EMERGING] += 1
        elif dependent_count < 50:
            scores[ModuleLifecycleStage.INTEGRATING] += 2
        else:
            scores[ModuleLifecycleStage.CORE] += 2
        
        # Analyze stability (change frequency)
        # Inspired by: Product version stability, artist consistency
        if change_frequency > 0.5:  # More than 1 change per 2 days
            scores[ModuleLifecycleStage.PROTOTYPE] += 3
        elif change_frequency > 0.2:
            scores[ModuleLifecycleStage.DEVELOPMENT] += 2
        elif change_frequency > 0.05:
            scores[ModuleLifecycleStage.EMERGING] += 1
        elif change_frequency < 0.01:  # Very stable
            scores[ModuleLifecycleStage.CATALOG] += 2
        
        # Check maturity indicators
        if has_tests and documentation_quality == "high":
            scores[ModuleLifecycleStage.CORE] += 2
        elif has_tests:
            scores[ModuleLifecycleStage.EMERGING] += 1
        else:
            scores[ModuleLifecycleStage.PROTOTYPE] += 1
        
        # Determine winning stage
        if not scores:
            return ModuleLifecycleStage.UNKNOWN
            
        winning_stage = max(scores, key=scores.get)
        return winning_stage


# Convenience functions
def calculate_risk_from_personality(personality) -> ModuleRiskProfile:
    """
    Convert ModulePersonality to ModuleRiskProfile.
    
    This bridges the personality system with the risk profiling system.
    """
    # Map personality traits to risk dimensions
    dependency_health = 30.0 if personality.is_runtime_fragile else 70.0
    runtime_stability = 20.0 if personality.is_runtime_fragile else 80.0
    integration_complexity = 80.0 if personality.is_import_heavy else 40.0
    purity_score = 20.0 if personality.has_side_effects else 80.0
    circular_risk = 90.0 if personality.is_circular_prone else 10.0
    
    # Historical reliability based on stability
    historical_reliability = 50.0
    if not any([
        personality.is_runtime_fragile,
        personality.is_path_dependent,
        personality.is_circular_prone
    ]):
        historical_reliability = 85.0
    
    return ModuleRiskProfile(
        module_name=personality.name,
        dependency_health=dependency_health,
        runtime_stability=runtime_stability,
        integration_complexity=integration_complexity,
        purity_score=purity_score,
        circular_risk=circular_risk,
        historical_reliability=historical_reliability
    )


def get_stage_specific_guardrails(stage: ModuleLifecycleStage) -> List[str]:
    """
    Get recommended guardrail strictness by lifecycle stage.
    
    Returns list of guardrail types that should be enforced.
    """
    all_guardrails = [
        'hardcoded_path',
        'missing_dependency',
        'circular_import',
        'side_effect',
        'global_state',
        'import_heavy',
        'documentation_missing'
    ]
    
    stage_guardrails = {
        ModuleLifecycleStage.PROTOTYPE: [
            'hardcoded_path', 'missing_dependency'
        ],  # Focus on basics
        ModuleLifecycleStage.DEVELOPMENT: [
            'hardcoded_path', 'missing_dependency', 'side_effect'
        ],
        ModuleLifecycleStage.EMERGING: [
            'hardcoded_path', 'missing_dependency', 'side_effect', 'circular_import'
        ],
        ModuleLifecycleStage.INTEGRATING: all_guardrails[:-1],
        ModuleLifecycleStage.CORE: all_guardrails,
        ModuleLifecycleStage.CATALOG: all_guardrails,
        ModuleLifecycleStage.LEGACY: [
            'hardcoded_path', 'security_vulnerability'
        ],  # Security only
        ModuleLifecycleStage.REFACTORING: [
            'circular_import', 'side_effect'
        ],  # Architecture focus
        ModuleLifecycleStage.UNKNOWN: [
            'hardcoded_path', 'missing_dependency'
        ]
    }
    
    return stage_guardrails.get(stage, all_guardrails)
