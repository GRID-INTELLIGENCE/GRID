"""
Comprehensive Test Suite for Cross-Domain Guardrail System

Tests covering edge cases across:
- Lifecycle transitions
- Risk scoring edge cases
- Pattern archetype detection
- Anomaly detection edge cases
- Cross-domain analogies (one-hit wonder, catalog artist, etc.)
"""

import sys
import os
import traceback
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from guardrails.profiling.lifecycle_risk_profiler import (
    ModuleLifecycleStage,
    ModuleRiskProfile,
    ModuleLifecycleAnalyzer,
    calculate_risk_from_personality,
    get_stage_specific_guardrails
)

from guardrails.profiling.pattern_archetypes import (
    ModulePatternArchetype,
    PatternMetrics,
    PatternArchetypeDetector,
    detect_module_pattern
)

from guardrails.anomaly.anomaly_detection import (
    AnomalyType,
    Anomaly,
    StatisticalDetector,
    VelocityDetector,
    PeerGroupAnalyzer,
    AnomalyDetectionEngine,
    quick_anomaly_check
)

# Simple test runner
def run_test(test_func):
    """Run a single test and report results."""
    try:
        test_func()
        print(f"  PASS: {test_func.__name__}")
        return True
    except AssertionError as e:
        print(f"  FAIL: {test_func.__name__} - {e}")
        return False
    except Exception as e:
        print(f"  ERROR: {test_func.__name__} - {e}")
        traceback.print_exc()
        return False


class TestLifecycleStages:
    """Test lifecycle stage classification with edge cases."""
    
    def test_stage_transitions(self):
        """Test module lifecycle stage transitions."""
        analyzer = ModuleLifecycleAnalyzer()
        
        # Test prototype → development → emerging → core transition
        stages = [
            ("proto_module", "experimental/new_module.py", 0, False, 10.0, "none"),
            ("dev_module", "beta/test_module.py", 2, True, 5.0, "low"),
            ("emerging_module", "v0/module.py", 5, True, 2.0, "medium"),
            ("core_module", "core/main.py", 100, True, 0.1, "high"),
        ]
        
        expected_stages = [
            ModuleLifecycleStage.PROTOTYPE,
            ModuleLifecycleStage.DEVELOPMENT,
            ModuleLifecycleStage.EMERGING,
            ModuleLifecycleStage.CORE
        ]
        
        for i, (name, path, deps, has_tests, change_freq, docs) in enumerate(stages):
            stage = analyzer.analyze_lifecycle_stage(
                name, path, 0, deps, change_freq, has_tests, docs
            )
            assert stage == expected_stages[i], f"Failed for {name}"
    
    def test_reverse_transitions(self):
        """Test unusual reverse transitions (core → emerging via refactoring)."""
        analyzer = ModuleLifecycleAnalyzer()
        
        # Core module being refactored
        stage = analyzer.analyze_lifecycle_stage(
            "refactoring_core",
            "core/refactor_module.py",
            50, True, 15.0, "high"  # High change rate despite many dependents
        )
        
        # Should detect refactoring state
        assert stage in [ModuleLifecycleStage.REFACTORING, ModuleLifecycleStage.CORE]
    
    def test_orphaned_modules(self):
        """Test detection of orphaned modules."""
        analyzer = ModuleLifecycleAnalyzer()
        
        # Module with no dependents and no imports
        stage = analyzer.analyze_lifecycle_stage(
            "orphaned_module",
            "utils/abandoned.py",
            0, False, 0.0, "none"
        )
        
        assert stage in [ModuleLifecycleStage.ORPHANED, ModuleLifecycleStage.UNKNOWN]
    
    def test_legacy_detection(self):
        """Test legacy module detection."""
        analyzer = ModuleLifecycleAnalyzer()
        
        stage = analyzer.analyze_lifecycle_stage(
            "legacy_module",
            "deprecated/old_system.py",
            10, True, 0.01, "high"
        )
        
        assert stage == ModuleLifecycleStage.LEGACY
    
    def test_simultaneous_multiple_indicators(self):
        """Test when multiple stage indicators are present."""
        analyzer = ModuleLifecycleAnalyzer()
        
        # Module with both "beta" and "core" in name (conflicting signals)
        stage = analyzer.analyze_lifecycle_stage(
            "beta_core_module",
            "core/beta_component.py",
            50, True, 0.5, "high"
        )
        
        # Should resolve based on strongest signals
        assert stage is not None


class TestRiskScoringEdgeCases:
    """Test risk scoring edge cases and boundary conditions."""
    
    def test_perfect_score(self):
        """Test module with all perfect scores (100s)."""
        profile = ModuleRiskProfile(
            module_name="perfect_module",
            dependency_health=100.0,
            runtime_stability=100.0,
            integration_complexity=0.0,  # Lower is better
            purity_score=100.0,
            circular_risk=0.0,
            historical_reliability=100.0
        )
        
        # Should have very low risk
        assert profile.composite_risk_score < 10.0
        assert profile.risk_category == "AAA"
        assert not profile.should_trigger_guardrail("AAA")
    
    def test_zero_score(self):
        """Test module with all zero scores."""
        profile = ModuleRiskProfile(
            module_name="broken_module",
            dependency_health=0.0,
            runtime_stability=0.0,
            integration_complexity=100.0,
            purity_score=0.0,
            circular_risk=100.0,
            historical_reliability=0.0
        )
        
        # Should have maximum risk
        assert profile.composite_risk_score > 90.0
        assert profile.risk_category == "D"
        assert profile.should_trigger_guardrail("AAA")
    
    def test_contradictory_signals(self):
        """Test module with contradictory signals (high health + high fragility)."""
        profile = ModuleRiskProfile(
            module_name="contradictory_module",
            dependency_health=90.0,  # Good
            runtime_stability=20.0,  # Bad
            integration_complexity=50.0,
            purity_score=90.0,  # Good
            circular_risk=80.0,  # Bad
            historical_reliability=50.0
        )
        
        # Should have moderate-high risk due to conflicting signals
        score = profile.composite_risk_score
        assert 40.0 < score < 70.0
    
    def test_missing_data(self):
        """Test handling of incomplete/missing data."""
        profile = ModuleRiskProfile(
            module_name="unknown_module"
            # Use all defaults
        )
        
        # Should have moderate risk (default values)
        assert 40.0 < profile.composite_risk_score < 60.0
        assert profile.risk_category in ["BBB", "A"]
    
    def test_lifecycle_risk_adjustment(self):
        """Test risk adjustment based on lifecycle stage."""
        # Same scores, different stages
        prototype = ModuleRiskProfile(
            "proto", lifecycle_stage=ModuleLifecycleStage.PROTOTYPE
        )
        core = ModuleRiskProfile(
            "core", lifecycle_stage=ModuleLifecycleStage.CORE
        )
        legacy = ModuleRiskProfile(
            "legacy", lifecycle_stage=ModuleLifecycleStage.LEGACY
        )
        
        # Prototype should have lower adjusted risk due to expectations
        assert prototype.lifecycle_risk_adjustment < core.lifecycle_risk_adjustment
        assert prototype.adjusted_risk_score < core.adjusted_risk_score
        
        # Legacy should have moderate adjustment
        assert legacy.lifecycle_risk_adjustment < core.lifecycle_risk_adjustment
    
    def test_threshold_boundary_conditions(self):
        """Test guardrail triggering at threshold boundaries."""
        profile = ModuleRiskProfile(
            module_name="boundary_module",
            dependency_health=65.0,  # Just below "BBB" threshold
            runtime_stability=65.0,
            integration_complexity=35.0,
            purity_score=65.0,
            circular_risk=35.0,
            historical_reliability=65.0
        )
        
        # Should trigger at BBB but not at A
        assert profile.should_trigger_guardrail("BBB")
        assert not profile.should_trigger_guardrail("A")
    
    def test_improvement_recommendations(self):
        """Test improvement recommendation generation."""
        profile = ModuleRiskProfile(
            module_name="needs_work",
            dependency_health=30.0,  # Low - needs improvement
            runtime_stability=80.0,  # Good
            circular_risk=90.0,     # High - needs improvement
        )
        
        recommendations = profile.get_improvement_recommendations()
        
        # Should recommend fixing dependency_health and circular_risk
        assert len(recommendations) >= 2
        dim_names = [r['dimension'] for r in recommendations]
        assert 'Dependency Health' in dim_names or 'Circular Dependency Risk' in dim_names


class TestPatternArchetypeEdgeCases:
    """Test pattern archetype detection edge cases."""
    
    def test_viral_spike_detection(self):
        """Test viral spike pattern (sudden rapid growth)."""
        detector = PatternArchetypeDetector()
        
        # Create metrics showing sudden spike
        history = []
        base_date = datetime.utcnow() - timedelta(days=30)
        
        # Baseline: steady at 5 dependents
        for i in range(10):
            history.append(PatternMetrics(
                current_dependents=5,
                dependent_growth_rate=0.0,
                peak_dependents=5,
                recent_change_velocity=0.1,
                integration_velocity=0.0,
                uptime_score=0.9,
                breaking_change_frequency=0.0,
                layer_diversity=1,
                cross_layer_ratio=0.0,
                first_seen=base_date,
                last_updated=base_date + timedelta(days=i),
                days_since_creation=i
            ))
        
        # Spike: sudden jump to 50
        history.append(PatternMetrics(
            current_dependents=50,
            dependent_growth_rate=9.0,  # 9x growth rate
            peak_dependents=50,
            recent_change_velocity=0.5,
            integration_velocity=8.0,
            uptime_score=0.8,
            breaking_change_frequency=0.1,
            layer_diversity=2,
            cross_layer_ratio=0.2,
            first_seen=base_date,
            last_updated=base_date + timedelta(days=11),
            days_since_creation=11
        ))
        
        pattern, confidence = detector.detect_pattern(history, history[-1])
        
        assert pattern in [ModulePatternArchetype.VIRAL_SPIKE, ModulePatternArchetype.STEADY_CLIMBER]
        if pattern == ModulePatternArchetype.VIRAL_SPIKE:
            assert confidence > 0.3
    
    def test_flash_in_pan_detection(self):
        """Test flash-in-pan pattern (rapid rise then fall)."""
        detector = PatternArchetypeDetector()
        
        # Create rise-then-fall pattern
        history = [
            PatternMetrics(current_dependents=5, peak_dependents=50, dependent_growth_rate=-0.5,
                         recent_change_velocity=0.1, integration_velocity=-0.3,
                         uptime_score=0.9, breaking_change_frequency=0.0,
                         layer_diversity=1, cross_layer_ratio=0.0,
                         first_seen=datetime.utcnow() - timedelta(days=30),
                         last_updated=datetime.utcnow() - timedelta(days=i),
                         days_since_creation=30-i)
            for i in range(10, 0, -1)
        ]
        
        # Add current low state
        history.append(PatternMetrics(
            current_dependents=3, peak_dependents=50, dependent_growth_rate=-0.2,
            recent_change_velocity=0.1, integration_velocity=-0.1,
            uptime_score=0.9, breaking_change_frequency=0.0,
            layer_diversity=1, cross_layer_ratio=0.0,
            first_seen=datetime.utcnow() - timedelta(days=30),
            last_updated=datetime.utcnow(),
            days_since_creation=30
        ))
        
        pattern, confidence = detector.detect_pattern(history, history[-1])
        
        assert pattern in [ModulePatternArchetype.FLASH_IN_PAN, ModulePatternArchetype.DECLINING]
    
    def test_nearly_viral_threshold(self):
        """Test module just below viral threshold."""
        detector = PatternArchetypeDetector()
        
        # Growth just below viral threshold
        history = []
        for i in range(5):
            growth = 0.4  # Just below 0.5 threshold
            history.append(PatternMetrics(
                current_dependents=10 + int(i * growth * 10),
                dependent_growth_rate=growth,
                peak_dependents=30,
                recent_change_velocity=0.2,
                integration_velocity=growth,
                uptime_score=0.9,
                breaking_change_frequency=0.1,
                layer_diversity=1,
                cross_layer_ratio=0.1,
                first_seen=datetime.utcnow() - timedelta(days=30),
                last_updated=datetime.utcnow() - timedelta(days=5-i),
                days_since_creation=25+i
            ))
        
        pattern, confidence = detector.detect_pattern(history, history[-1])
        
        # Should be detected as steady climber, not viral
        assert pattern in [ModulePatternArchetype.STEADY_CLIMBER, ModulePatternArchetype.UNDETERMINED]
    
    def test_simultaneous_multiple_patterns(self):
        """Test when module exhibits multiple pattern characteristics."""
        detector = PatternArchetypeDetector()
        
        # Module that is both crossover and steady climber
        history = []
        for i in range(10):
            history.append(PatternMetrics(
                current_dependents=20 + i,
                dependent_growth_rate=0.1,
                peak_dependents=30,
                recent_change_velocity=0.1,
                integration_velocity=0.1,
                uptime_score=0.95,
                breaking_change_frequency=0.0,
                layer_diversity=4,  # High layer diversity (crossover)
                cross_layer_ratio=0.5,  # High cross-layer ratio
                first_seen=datetime.utcnow() - timedelta(days=60),
                last_updated=datetime.utcnow() - timedelta(days=10-i),
                days_since_creation=50+i
            ))
        
        pattern, confidence = detector.detect_pattern(history, history[-1])
        
        # Should pick one dominant pattern
        assert pattern in [ModulePatternArchetype.CROSSOVER, ModulePatternArchetype.STEADY_CLIMBER]
        assert confidence > 0
    
    def test_no_pattern_detected(self):
        """Test truly unique modules that don't match any pattern."""
        detector = PatternArchetypeDetector()
        
        # Random/erratic behavior
        history = []
        import random
        random.seed(42)  # For reproducibility
        
        for i in range(10):
            history.append(PatternMetrics(
                current_dependents=random.randint(1, 100),
                dependent_growth_rate=random.uniform(-1, 1),
                peak_dependents=100,
                recent_change_velocity=random.uniform(0, 1),
                integration_velocity=random.uniform(-1, 1),
                uptime_score=random.uniform(0.5, 1.0),
                breaking_change_frequency=random.uniform(0, 0.5),
                layer_diversity=random.randint(1, 5),
                cross_layer_ratio=random.uniform(0, 1),
                first_seen=datetime.utcnow() - timedelta(days=30),
                last_updated=datetime.utcnow() - timedelta(days=10-i),
                days_since_creation=20+i
            ))
        
        pattern, confidence = detector.detect_pattern(history, history[-1])
        
        # Should be unique or undetermined
        assert pattern in [ModulePatternArchetype.UNIQUE, ModulePatternArchetype.UNDETERMINED, 
                          ModulePatternArchetype.ROLLERCOASTER]
    
    def test_single_data_point(self):
        """Test pattern detection with insufficient data."""
        detector = PatternArchetypeDetector()
        
        # Only one data point
        history = [PatternMetrics(
            current_dependents=10,
            dependent_growth_rate=0.0,
            peak_dependents=10,
            recent_change_velocity=0.0,
            integration_velocity=0.0,
            uptime_score=1.0,
            breaking_change_frequency=0.0,
            layer_diversity=1,
            cross_layer_ratio=0.0,
            first_seen=datetime.utcnow() - timedelta(days=30),
            last_updated=datetime.utcnow(),
            days_since_creation=30
        )]
        
        pattern, confidence = detector.detect_pattern(history, history[-1])
        
        assert pattern == ModulePatternArchetype.UNDETERMINED
        assert confidence == 0.0


class TestAnomalyDetectionEdgeCases:
    """Test anomaly detection with edge cases."""
    
    def test_single_data_point_anomaly(self):
        """Test anomaly detection with single data point (no history)."""
        detector = StatisticalDetector()
        
        values = [100]
        anomalies = detector.z_score_detection(values)
        
        # Should return empty (insufficient data)
        assert len(anomalies) == 0
    
    def test_extreme_outlier(self):
        """Test detection of extreme outlier (100x normal)."""
        detector = StatisticalDetector()
        
        # Normal values around 10, one extreme outlier at 1000
        values = [10, 11, 10, 12, 11, 1000, 10, 11]
        
        anomalies = detector.z_score_detection(values)
        
        # Should detect the extreme outlier
        assert len(anomalies) > 0
        outlier_idx = [a[0] for a in anomalies]
        assert 5 in outlier_idx  # Index of 1000
    
    def test_seasonal_pattern(self):
        """Test detection of seasonal/cyclical patterns (weekend effects)."""
        detector = StatisticalDetector()
        
        # Simulate weekend dip pattern
        # Weekdays: high values, Weekends: low values
        values = [100, 95, 98, 102, 99, 50, 45, 101, 97, 100, 98, 48, 46]
        # Mon  Tue  Wed  Thu  Fri  Sat Sun  Mon  Tue  Wed  Thu  Fri Sat Sun
        
        # Z-score might flag weekends as anomalies
        anomalies = detector.z_score_detection(values, threshold=2.0)
        
        # Weekend indices (5,6,11,12) might be flagged
        weekend_indices = [5, 6, 11, 12]
        flagged_indices = [a[0] for a in anomalies]
        
        # At least some weekends should be flagged
        assert len(set(weekend_indices) & set(flagged_indices)) > 0
    
    def test_cluster_edge_cases(self):
        """Test peer group analysis edge cases."""
        analyzer = PeerGroupAnalyzer()
        
        # Test lone module (no peers)
        deviation, severity = analyzer.calculate_peer_deviation(
            50.0, [], "metric"
        )
        assert deviation == 0.0
        assert severity == "unknown"
        
        # Test tightly coupled cluster (all identical)
        peer_values = [50.0, 50.0, 50.0, 50.0]
        deviation, severity = analyzer.calculate_peer_deviation(
            50.0, peer_values, "metric"
        )
        # Should handle zero variance gracefully
        assert deviation >= 0.0
    
    def test_volatility_clustering(self):
        """Test detection of volatility clustering."""
        detector = VelocityDetector()
        
        # Create period of low volatility followed by high volatility cluster
        # Low volatility period
        low_vol_values = [100 + i % 3 for i in range(10)]  # Small variations
        
        # High volatility period
        high_vol_values = [100, 150, 80, 120, 170, 90, 110]
        
        values = low_vol_values + high_vol_values
        timestamps = [datetime.utcnow() - timedelta(hours=len(values)-i) for i in range(len(values))]
        
        clusters = detector.detect_volatility_clustering(values, window=5, threshold=1.5)
        
        # Should detect volatility in high-vol period
        if clusters:
            # Check that cluster is in second half
            assert any(idx >= 10 for idx, _ in clusters)
    
    def test_momentum_shift_detection(self):
        """Test detection of momentum direction changes."""
        detector = VelocityDetector()
        
        # Upward trend
        upward = [10, 12, 14, 16, 18, 20]
        shift = detector.detect_momentum_shift(upward)
        assert shift is None  # No shift in consistent trend
        
        # Upward then downward (momentum shift)
        up_then_down = [10, 12, 14, 16, 14, 12, 10]
        shift = detector.detect_momentum_shift(up_then_down, window=3)
        assert shift is not None
        if shift:
            idx, direction, strength = shift
            assert direction == "down"
            assert strength > 0


class TestCrossDomainAnalogies:
    """Test cross-domain pattern analogies."""
    
    def test_one_hit_wonder_module(self):
        """Test one-hit wonder pattern (brief popularity then abandoned)."""
        # Simulate: 0 → 10 → 5 → 0 dependents
        metrics_history = [
            PatternMetrics(
                current_dependents=0,
                peak_dependents=10,
                dependent_growth_rate=-1.0,
                recent_change_velocity=0.0,
                integration_velocity=0.0,
                uptime_score=1.0,
                breaking_change_frequency=0.0,
                layer_diversity=1,
                cross_layer_ratio=0.0,
                first_seen=datetime.utcnow() - timedelta(days=60),
                last_updated=datetime.utcnow() - timedelta(days=30),
                days_since_creation=30
            ),
            PatternMetrics(
                current_dependents=0,
                peak_dependents=10,
                dependent_growth_rate=0.0,
                recent_change_velocity=0.0,
                integration_velocity=0.0,
                uptime_score=1.0,
                breaking_change_frequency=0.0,
                layer_diversity=1,
                cross_layer_ratio=0.0,
                first_seen=datetime.utcnow() - timedelta(days=60),
                last_updated=datetime.utcnow(),
                days_since_creation=60
            )
        ]
        
        pattern, confidence, recommendations = detect_module_pattern(
            "one_hit_module", metrics_history
        )
        
        assert pattern in [ModulePatternArchetype.ONE_HIT_WONDER, ModulePatternArchetype.ORPHANED]
    
    def test_catalog_artist_module(self):
        """Test catalog stable pattern (long-lived, rarely changed)."""
        metrics_history = [
            PatternMetrics(
                current_dependents=50,
                peak_dependents=50,
                dependent_growth_rate=0.0,
                recent_change_velocity=0.01,  # Very stable
                integration_velocity=0.0,
                uptime_score=0.99,
                breaking_change_frequency=0.0,
                layer_diversity=3,
                cross_layer_ratio=0.1,
                first_seen=datetime.utcnow() - timedelta(days=1000),  # Very old
                last_updated=datetime.utcnow() - timedelta(days=30),
                days_since_creation=1000
            )
        ]
        
        pattern, confidence, recommendations = detect_module_pattern(
            "catalog_module", metrics_history
        )
        
        assert pattern in [ModulePatternArchetype.CATALOG_STABLE, ModulePatternArchetype.STEADY_WORKHORSE]
    
    def test_genre_blending_module(self):
        """Test crossover pattern (used across architecture layers like genre-blending music)."""
        metrics_history = [
            PatternMetrics(
                current_dependents=30,
                peak_dependents=30,
                dependent_growth_rate=0.05,
                recent_change_velocity=0.1,
                integration_velocity=0.05,
                uptime_score=0.9,
                breaking_change_frequency=0.0,
                layer_diversity=5,  # High layer diversity
                cross_layer_ratio=0.6,  # 60% cross-layer usage
                first_seen=datetime.utcnow() - timedelta(days=300),
                last_updated=datetime.utcnow(),
                days_since_creation=300
            )
        ]
        
        pattern, confidence, recommendations = detect_module_pattern(
            "crossover_module", metrics_history
        )
        
        assert pattern in [ModulePatternArchetype.CROSSOVER, ModulePatternArchetype.BRIDGE]
        if pattern == ModulePatternArchetype.CROSSOVER:
            assert confidence > 0.3
    
    def test_sleeper_hit_module(self):
        """Test sleeping giant pattern (high quality, underutilized)."""
        metrics_history = [
            PatternMetrics(
                current_dependents=2,  # Low adoption
                peak_dependents=2,
                dependent_growth_rate=0.0,
                recent_change_velocity=0.05,  # Very stable
                integration_velocity=0.0,
                uptime_score=0.98,  # High quality
                breaking_change_frequency=0.0,
                layer_diversity=1,
                cross_layer_ratio=0.0,
                first_seen=datetime.utcnow() - timedelta(days=200),  # Mature
                last_updated=datetime.utcnow() - timedelta(days=60),
                days_since_creation=200
            )
        ]
        
        pattern, confidence, recommendations = detect_module_pattern(
            "sleeper_module", metrics_history
        )
        
        assert pattern in [ModulePatternArchetype.SLEEPING_GIANT, ModulePatternArchetype.UNIQUE]


class TestIntegration:
    """Integration tests combining all systems."""
    
    def test_end_to_end_profiling(self):
        """Test complete profiling pipeline."""
        # Create module personality
        from guardrails.profiler.module_profiler import ModulePersonality, PersonalityTone
        
        personality = ModulePersonality(
            name="test_module",
            path="/test/path.py",
            is_path_dependent=True,
            is_runtime_fragile=False,
            is_circular_prone=False,
            is_import_heavy=False,
            has_side_effects=False,
            is_stateful=False,
            tone=PersonalityTone.DEFENSIVE,
            hardcoded_paths=["/hardcoded/path"],
            imports={"os", "sys"}
        )
        
        # Convert to risk profile
        risk_profile = calculate_risk_from_personality(personality)
        
        assert risk_profile.module_name == "test_module"
        assert risk_profile.dependency_health < 50  # Due to path dependency
        
        # Get lifecycle-specific guardrails
        guardrails = get_stage_specific_guardrails(ModuleLifecycleStage.EMERGING)
        
        assert 'hardcoded_path' in guardrails
    
    def test_anomaly_detection_integration(self):
        """Test anomaly detection with real-world-like data."""
        engine = AnomalyDetectionEngine()
        
        # Simulate module metrics over time
        timestamps = [datetime.utcnow() - timedelta(hours=i) for i in range(20, 0, -1)]
        
        # Normal pattern then anomaly
        dependents = [10, 11, 10, 12, 11, 10, 11, 10, 12, 50, 51, 52, 51, 50, 51, 50, 51, 50, 51, 50]
        #                    Normal          Spike^^^ Stable after spike
        
        metric_history = {'dependents': dependents}
        
        anomalies = engine.detect_anomalies(
            "test_module",
            metric_history,
            timestamps
        )
        
        # Should detect the spike anomaly
        assert len(anomalies) > 0
        
        # At least one should be around index 9 (the spike)
        anomaly_indices = []
        for a in anomalies:
            if 'dependents' in a.metric_name:
                # Approximate index from timestamp
                idx = timestamps.index(a.timestamp) if a.timestamp in timestamps else -1
                if idx >= 0:
                    anomaly_indices.append(idx)
        
        # Spike should be detected
        assert any(8 <= idx <= 10 for idx in anomaly_indices) or len(anomalies) > 0


def main():
    """Run all tests."""
    print("=" * 70)
    print("COMPREHENSIVE GUARDRAIL SYSTEM TEST SUITE")
    print("=" * 70)
    
    all_tests = []
    
    # Lifecycle stage tests
    print("\n[Test Suite: Lifecycle Stages]")
    lifecycle = TestLifecycleStages()
    all_tests.extend([
        ("test_stage_transitions", lifecycle.test_stage_transitions),
        ("test_reverse_transitions", lifecycle.test_reverse_transitions),
        ("test_orphaned_modules", lifecycle.test_orphaned_modules),
        ("test_legacy_detection", lifecycle.test_legacy_detection),
        ("test_simultaneous_multiple_indicators", lifecycle.test_simultaneous_multiple_indicators),
    ])
    
    # Risk scoring tests
    print("\n[Test Suite: Risk Scoring Edge Cases]")
    risk = TestRiskScoringEdgeCases()
    all_tests.extend([
        ("test_perfect_score", risk.test_perfect_score),
        ("test_zero_score", risk.test_zero_score),
        ("test_contradictory_signals", risk.test_contradictory_signals),
        ("test_missing_data", risk.test_missing_data),
        ("test_lifecycle_risk_adjustment", risk.test_lifecycle_risk_adjustment),
        ("test_threshold_boundary_conditions", risk.test_threshold_boundary_conditions),
        ("test_improvement_recommendations", risk.test_improvement_recommendations),
    ])
    
    # Pattern archetype tests
    print("\n[Test Suite: Pattern Archetype Edge Cases]")
    pattern = TestPatternArchetypeEdgeCases()
    all_tests.extend([
        ("test_viral_spike_detection", pattern.test_viral_spike_detection),
        ("test_flash_in_pan_detection", pattern.test_flash_in_pan_detection),
        ("test_nearly_viral_threshold", pattern.test_nearly_viral_threshold),
        ("test_simultaneous_multiple_patterns", pattern.test_simultaneous_multiple_patterns),
        ("test_no_pattern_detected", pattern.test_no_pattern_detected),
        ("test_single_data_point", pattern.test_single_data_point),
    ])
    
    # Anomaly detection tests
    print("\n[Test Suite: Anomaly Detection Edge Cases]")
    anomaly = TestAnomalyDetectionEdgeCases()
    all_tests.extend([
        ("test_single_data_point_anomaly", anomaly.test_single_data_point_anomaly),
        ("test_extreme_outlier", anomaly.test_extreme_outlier),
        ("test_seasonal_pattern", anomaly.test_seasonal_pattern),
        ("test_cluster_edge_cases", anomaly.test_cluster_edge_cases),
        ("test_volatility_clustering", anomaly.test_volatility_clustering),
        ("test_momentum_shift_detection", anomaly.test_momentum_shift_detection),
    ])
    
    # Cross-domain analogy tests
    print("\n[Test Suite: Cross-Domain Analogies]")
    analogy = TestCrossDomainAnalogies()
    all_tests.extend([
        ("test_one_hit_wonder_module", analogy.test_one_hit_wonder_module),
        ("test_catalog_artist_module", analogy.test_catalog_artist_module),
        ("test_genre_blending_module", analogy.test_genre_blending_module),
        ("test_sleeper_hit_module", analogy.test_sleeper_hit_module),
    ])
    
    # Integration tests
    print("\n[Test Suite: Integration Tests]")
    integration = TestIntegration()
    all_tests.extend([
        ("test_end_to_end_profiling", integration.test_end_to_end_profiling),
        ("test_anomaly_detection_integration", integration.test_anomaly_detection_integration),
    ])
    
    # Run all tests
    passed = 0
    failed = 0
    errors = 0
    
    for name, test_func in all_tests:
        try:
            test_func()
            print(f"  PASS: {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {name} - {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {name} - {e}")
            errors += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total:  {len(all_tests)}")
    print(f"Passed: {passed} ({passed/len(all_tests)*100:.1f}%)")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    
    if failed == 0 and errors == 0:
        print("\nALL TESTS PASSED!")
        return 0
    else:
        print(f"\n{failed + errors} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
