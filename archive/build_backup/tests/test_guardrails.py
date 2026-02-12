"""
Test suite for the Guardrail System.

Tests the module profiler, middleware, events, and learning components.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json

from guardrails import (
    ModuleProfiler,
    ModulePersonality,
    PersonalityTone,
    PersonalityStyle,
    PersonalityNuance,
    GuardrailMiddleware,
    GuardrailViolation,
    GuardrailSystem,
    setup_guardrails,
)
from guardrails.learning import AdaptiveEngine, learn_from_violation


class TestModuleProfiler:
    """Test the ModuleProfiler component."""
    
    def test_analyze_simple_module(self):
        """Test analyzing a simple, clean module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple module
            module_path = Path(tmpdir) / "simple.py"
            module_path.write_text("""
# Simple clean module
import os
import sys

def hello():
    return "Hello, World!"

if __name__ == "__main__":
    print(hello())
""")
            
            profiler = ModuleProfiler(tmpdir)
            personality = profiler.analyze_module(module_path)
            
            assert personality.name == "simple"
            assert not personality.is_path_dependent
            assert not personality.is_runtime_fragile
            assert not personality.is_circular_prone
            assert personality.tone == PersonalityTone.PERMISSIVE
            
    def test_analyze_path_dependent_module(self):
        """Test analyzing a module with hardcoded paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create module with hardcoded paths
            module_path = Path(tmpdir) / "path_dependent.py"
            module_path.write_text("""
# Module with hardcoded paths
DATA_DIR = "E:/grid/logs/xai_traces"
CONFIG_PATH = "C:/Users/admin/config.json"

def load_data():
    with open(DATA_DIR) as f:
        return f.read()
""")
            
            profiler = ModuleProfiler(tmpdir)
            personality = profiler.analyze_module(module_path)
            
            assert personality.is_path_dependent
            assert len(personality.hardcoded_paths) == 2
            assert "E:/grid/logs/xai_traces" in personality.hardcoded_paths
            assert personality.tone == PersonalityTone.DEFENSIVE
            
    def test_analyze_runtime_fragile_module(self):
        """Test analyzing a module with conditional imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create module with conditional imports
            module_path = Path(tmpdir) / "fragile.py"
            module_path.write_text("""
# Module with conditional imports
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    torch = None

try:
    from .optional_module import optional_func
except ImportError:
    def optional_func():
        return "fallback"
""")
            
            profiler = ModuleProfiler(tmpdir)
            personality = profiler.analyze_module(module_path)
            
            assert personality.is_runtime_fragile
            assert len(personality.conditional_imports) > 0
            assert personality.tone == PersonalityTone.DEFENSIVE
            
    def test_detect_circular_imports(self):
        """Test detection of circular imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create circular modules
            module_a = Path(tmpdir) / "a.py"
            module_b = Path(tmpdir) / "b.py"
            
            module_a.write_text("""
from . import b

def func_a():
    return b.func_b()
""")
            
            module_b.write_text("""
from . import a

def func_b():
    return a.func_a()
""")
            
            profiler = ModuleProfiler(tmpdir)
            personalities = profiler.analyze_package(tmpdir)
            
            # Both modules should be marked as circular prone
            assert personalities["a"].is_circular_prone
            assert personalities["b"].is_circular_prone
            assert "b" in personalities["a"].circular_dependencies
            assert "a" in personalities["b"].circular_dependencies


class TestGuardrailMiddleware:
    """Test the GuardrailMiddleware component."""
    
    def test_path_validation(self):
        """Test path validation in guardrails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create module with hardcoded paths
            module_path = Path(tmpdir) / "test.py"
            module_path.write_text('PATH = "E:/grid/logs/test"')
            
            middleware = GuardrailMiddleware(mode="observer")
            middleware.analyze_and_register(tmpdir)
            
            violations = middleware.check_module("test")
            
            assert len(violations) > 0
            assert any(v.violation_type == "hardcoded_path" for v in violations)
            
    def test_missing_dependency_detection(self):
        """Test detection of missing dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create module with non-existent import
            module_path = Path(tmpdir) / "test.py"
            module_path.write_text("""
try:
    import non_existent_module_12345
except ImportError:
    pass
""")
            
            middleware = GuardrailMiddleware(mode="observer")
            middleware.analyze_and_register(tmpdir)
            
            violations = middleware.check_module("test")
            
            # Should detect potential missing dependency
            assert any("non_existent_module_12345" in str(v) for v in violations)
            
    def test_whitelist_bypass(self):
        """Test that whitelisted modules bypass checks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir) / "test.py"
            module_path.write_text('PATH = "E:/grid/test"')
            
            middleware = GuardrailMiddleware(mode="enforcement")
            middleware.analyze_and_register(tmpdir)
            middleware.add_to_whitelist("test")
            
            # Should not raise an exception even in enforcement mode
            violations = middleware.check_module("test")
            assert len(violations) == 0


class TestGuardrailEvents:
    """Test the event integration."""
    
    def test_violation_event_publishing(self):
        """Test that violations are published as events."""
        from guardrails.events import GuardrailEventPublisher, GuardrailEventTypes
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup event system
            publisher = GuardrailEventPublisher()
            
            # Create a violation
            violation = GuardrailViolation(
                "Test violation",
                "test_module",
                "hardcoded_path",
                "warning"
            )
            
            # Publish violation
            publisher.publish_violation(violation)
            
            # Check event was published
            history = publisher.bus.get_history()
            guardrail_events = [e for e in history if "guardrail" in e.type]
            
            assert len(guardrail_events) > 0
            assert any(e.type == GuardrailEventTypes.HARDCODED_PATH for e in guardrail_events)
            
    def test_event_analytics(self):
        """Test event analytics collection."""
        from guardrails.events import GuardrailEventAnalyzer
        
        analyzer = GuardrailEventAnalyzer()
        
        # Simulate some violations
        for i in range(5):
            analyzer._handle_guardrail_event(type('MockEvent', (), {
                'type': 'guardrail:violation:hardcoded_path',
                'data': {
                    'module': f'test_module_{i % 2}',
                    'severity': 'warning',
                    'timestamp': datetime.utcnow().isoformat(),
                    'details': {'violation_type': 'hardcoded_path'}
                }
            })())
            
        trends = analyzer.get_violation_trends()
        assert trends['total_violations'] == 5
        assert 'hardcoded_path' in trends['violations_per_type']


class TestAdaptiveEngine:
    """Test the adaptive learning engine."""
    
    def test_pattern_extraction(self):
        """Test pattern extraction from violations."""
        engine = AdaptiveEngine()
        
        # Add similar violations
        for i in range(5):
            engine.add_violation({
                'type': 'hardcoded_path',
                'module': f'test_module_{i}',
                'details': {'path': f'E:/grid/test_{i}'}
            })
            
        # Trigger learning
        engine.learn()
        
        # Should have extracted patterns
        assert len(engine.patterns) > 0
        assert any(p.violation_type == 'hardcoded_path' for p in engine.patterns)
        
    def test_rule_generation(self):
        """Test rule generation from patterns."""
        engine = AdaptiveEngine()
        
        # Add violations to learn from
        engine.add_violation({
            'type': 'hardcoded_path',
            'module': 'test_module',
            'details': {'path': 'E:/grid/test'}
        })
        
        engine.learn()
        
        # Should have generated rules
        assert len(engine.rules) > 0
        
        # Check rule structure
        rule = engine.rules[0]
        assert 'id' in rule
        assert 'type' in rule
        assert 'condition' in rule
        assert 'action' in rule
        
    def test_recommendation_generation(self):
        """Test generation of module recommendations."""
        engine = AdaptiveEngine()
        
        # Learn from some violations
        engine.add_violation({
            'type': 'hardcoded_path',
            'module': 'similar_module',
            'details': {'path': 'E:/grid/test'}
        })
        
        engine.learn()
        
        # Get recommendations for similar module
        recommendations = engine.get_recommendations(
            'new_module',
            {'has_hardcoded_paths': True}
        )
        
        assert len(recommendations) > 0
        assert any(r['type'] == 'prevention' for r in recommendations)


class TestGuardrailSystem:
    """Test the integrated guardrail system."""
    
    def test_system_initialization(self):
        """Test full system initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test module
            module_path = Path(tmpdir) / "test.py"
            module_path.write_text('PATH = "E:/grid/test"')
            
            # Initialize system
            system = GuardrailSystem(tmpdir, mode="observer")
            system.initialize()
            
            assert system.initialized
            assert len(system.profiler.personalities) > 0
            
    def test_module_checking(self):
        """Test module violation checking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create module with issues
            module_path = Path(tmpdir) / "test.py"
            module_path.write_text("""
PATH = "E:/grid/logs/xai_traces"

try:
    import non_existent
except ImportError:
    pass
""")
            
            system = setup_guardrails(tmpdir, mode="observer")
            results = system.check_module("test")
            
            assert 'violations' in results
            assert 'recommendations' in results
            assert 'q_curve_profile' in results
            assert len(results['violations']) > 0
            
    def test_system_report_generation(self):
        """Test comprehensive report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test modules
            for i in range(3):
                module_path = Path(tmpdir) / f"test_{i}.py"
                module_path.write_text(f'PATH = "E:/grid/test_{i}"')
                
            system = setup_guardrails(tmpdir, mode="observer")
            report = system.get_system_report()
            
            assert 'stats' in report
            assert 'profiler' in report
            assert 'middleware' in report
            assert 'learning' in report
            assert report['stats']['modules_analyzed'] == 3
            
    def test_risky_modules_identification(self):
        """Test identification of risky modules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create modules with different risk levels
            risky_module = Path(tmpdir) / "risky.py"
            risky_module.write_text("""
import sys, os, json, pathlib, typing, collections, itertools, functools, datetime, re, math
PATH = "E:/grid/logs/xai_traces"
CONFIG = "C:/Users/admin/config.json"

try:
    import torch
except ImportError:
    pass
""")
            
            safe_module = Path(tmpdir) / "safe.py"
            safe_module.write_text("""
def hello():
    return "Hello"
""")
            
            system = setup_guardrails(tmpdir, mode="observer")
            risky = system.get_risky_modules(5)
            
            assert len(risky) > 0
            # Risky module should appear first
            assert risky[0]['module'] == 'risky'
            assert risky[0]['score'] > 0


class TestIntegration:
    """Integration tests for the complete system."""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from analysis to recommendations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a problematic package
            pkg_dir = Path(tmpdir) / "mypackage"
            pkg_dir.mkdir()
            
            # Main module with hardcoded paths
            main_module = pkg_dir / "main.py"
            main_module.write_text("""
from . import utils
DATA_DIR = "E:/grid/logs/xai_traces"

def main():
    return utils.process()
""")
            
            # Utils with circular import
            utils_module = pkg_dir / "utils.py"
            utils_module.write_text("""
from . import main

def process():
    return main.main()
""")
            
            # Config with missing deps
            config_module = pkg_dir / "config.py"
            config_module.write_text("""
try:
    import yaml
except ImportError:
    yaml = None
    
def load_config():
    if yaml:
        return yaml.load("config.yaml")
    return {}
""")
            
            # Run full analysis
            system = setup_guardrails(str(pkg_dir), mode="observer")
            
            # Check all modules
            for module_name in ["mypackage.main", "mypackage.utils", "mypackage.config"]:
                results = system.check_module(module_name)
                
                # Each should have some findings
                assert results['violations'] or results['recommendations']
                
            # Get system report
            report = system.get_system_report()
            
            # Verify findings
            assert report['stats']['modules_analyzed'] == 3
            assert report['stats']['violations_detected'] > 0
            
            # Check risky modules
            risky = system.get_risky_modules()
            assert len(risky) > 0
            
            # Verify learning happened
            assert report['learning']['patterns_discovered'] >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
