"""
Guardrail System Demo

Demonstrates the guardrail system detecting and preventing common issues
that cause modules to compile but fail at runtime.
"""

import os
import sys
import tempfile
from pathlib import Path
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from guardrails import (
    setup_guardrails,
    GuardrailSystem,
    PersonalityTone,
    PersonalityStyle,
    PersonalityNuance,
)


def create_demo_codebase(tmpdir: Path) -> Path:
    """Create a demo codebase with various issues."""
    
    # Create package structure
    pkg_dir = tmpdir / "demo_package"
    pkg_dir.mkdir()
    
    # 1. Module with hardcoded paths (common issue)
    hardcoded_module = pkg_dir / "data_loader.py"
    hardcoded_module.write_text("""
# Data loader with hardcoded paths - COMMON ISSUE
DATA_DIR = "E:/grid/logs/xai_traces"  # Hardcoded path!
CONFIG_PATH = "C:/Users/admin/app_config.json"  # Another hardcoded path

class DataLoader:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.config_path = CONFIG_PATH
        
    def load_data(self):
        # This will fail at runtime if paths don't exist
        with open(self.data_dir / "data.json") as f:
            return json.load(f)
            
    def load_config(self):
        with open(self.config_path) as f:
            return json.load(f)
""")
    
    # 2. Module with conditional imports (runtime fragile)
    fragile_module = pkg_dir / "ml_processor.py"
    fragile_module.write_text("""
# ML processor with optional dependencies - RUNTIME FRAGILE
try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    torch = None
    nn = None
    
try:
    from transformers import AutoModel
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = True
    AutoModel = None

class MLProcessor:
    def __init__(self):
        self.has_torch = HAS_TORCH
        self.has_transformers = HAS_TRANSFORMERS
        
    def process_with_torch(self, data):
        if not HAS_TORCH:
            raise ImportError("PyTorch is required for this function")
        return torch.tensor(data)
        
    def process_with_transformers(self, text):
        if not HAS_TRANSFORMERS:
            raise ImportError("Transformers is required for this function")
        return AutoModel.from_pretrained("bert-base-uncased")
""")
    
    # 3. Module with circular import
    circular_a = pkg_dir / "component_a.py"
    circular_a.write_text("""
# Component A - CIRCULAR IMPORT ISSUE
from .component_b import ComponentB

class ComponentA:
    def __init__(self):
        self.b = ComponentB()
        
    def process(self):
        return "A processed: " + self.b.get_data()
""")
    
    circular_b = pkg_dir / "component_b.py"
    circular_b.write_text("""
# Component B - CIRCULAR IMPORT ISSUE
from .component_a import ComponentA

class ComponentB:
    def __init__(self):
        self.a = ComponentA()
        
    def get_data(self):
        return "B data: " + self.a.process()
""")
    
    # 4. Module with side effects
    side_effect_module = pkg_dir / "initializer.py"
    side_effect_module.write_text("""
# Initializer with side effects - BAD PATTERN
import os
import logging

# Module-level side effect - runs on import!
os.makedirs("E:/grid/logs", exist_ok=True)
logging.basicConfig(level=logging.DEBUG)

# Global state modification
GLOBAL_CONFIG = {"debug": True}
CACHE = {}

def initialize():
    # More side effects
    print("Initializing system...")
    CACHE["initialized"] = True
""")
    
    # 5. Import-heavy module
    heavy_module = pkg_dir / "utils.py"
    heavy_module.write_text(
"""# Import-heavy module - PERFORMANCE ISSUE
import os
import sys
import json
import yaml
import csv
import xml
import sqlite3
import hashlib
import base64
import uuid
import datetime
import time
import random
import math
import itertools
import collections
import functools
import operator
import re
import string
import typing
import pathlib
import copy
import pickle
import heapq
import bisect
import array
import weakref
import types
import inspect
import importlib
import pkgutil

# Many more imports...
from typing import (
    Any, List, Dict, Set, Tuple, Optional, Union,
    Callable, Iterator, Generator, Type, TypeVar,
    Protocol, runtime_checkable
)

class Utils:
    \"\"\"Utility class with many dependencies.\"\"\"
    pass
"""
    )
    
    # 6. Clean module for comparison
    clean_module = pkg_dir / "clean_module.py"
    clean_module.write_text(
        """# Clean module - GOOD EXAMPLE
from pathlib import Path
from typing import List, Dict

class CleanModule:
    \"\"\"Well-behaved module with no issues.\"\"\"
    
    def __init__(self, config_path: Path = None):
        self.config_path = config_path or Path("config.json")
        
    def process_data(self, data: List[Dict]) -> List[Dict]:
        \"\"\"Process data safely.\"\"\"
        return [item for item in data if item.get("active")]
        
    def load_config(self) -> Dict:
        \"\"\"Load config with proper error handling.\"\"\"
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return {"default": True}
        except json.JSONDecodeError:
            raise ValueError(f"Invalid config file: {self.config_path}")
"""
    )
    
    return pkg_dir


def demo_personality_profiling(pkg_dir: Path):
    """Demonstrate personality profiling."""
    print("\n" + "="*60)
    print("DEMO 1: Module Personality Profiling")
    print("="*60)
    
    from guardrails.profiler.module_profiler import analyze_package
    
    # Analyze the package
    personalities = analyze_package(str(pkg_dir))
    
    print(f"\nAnalyzed {len(personalities)} modules:")
    print("-" * 40)
    
    for name, personality in personalities.items():
        print(f"\nModule: {name}")
        print(f"  Personality: {personality.tone.value}/{personality.style.value}/{personality.nuance.value}")
        print(f"  Traits:")
        print(f"    - Path dependent: {'✓' if personality.is_path_dependent else '✗'}")
        print(f"    - Runtime fragile: {'✓' if personality.is_runtime_fragile else '✗'}")
        print(f"    - Circular prone: {'✓' if personality.is_circular_prone else '✗'}")
        print(f"    - Import heavy: {'✓' if personality.is_import_heavy else '✗'}")
        print(f"    - Has side effects: {'✓' if personality.has_side_effects else '✗'}")
        print(f"    - Stateful: {'✓' if personality.is_stateful else '✗'}")
        
        if personality.hardcoded_paths:
            print(f"  Hardcoded paths: {personality.hardcoded_paths}")
        if personality.conditional_imports:
            print(f"  Conditional imports: {len(personality.conditional_imports)}")
        if personality.circular_dependencies:
            print(f"  Circular deps: {personality.circular_dependencies}")


def demo_guardrail_detection(pkg_dir: Path):
    """Demonstrate guardrail violation detection."""
    print("\n" + "="*60)
    print("DEMO 2: Guardrail Violation Detection")
    print("="*60)
    
    # Setup guardrails in warning mode
    system = setup_guardrails(str(pkg_dir), mode="warning")
    
    # Check each module
    modules_to_check = [
        "demo_package.data_loader",
        "demo_package.ml_processor", 
        "demo_package.component_a",
        "demo_package.initializer",
        "demo_package.utils",
        "demo_package.clean_module"
    ]
    
    for module_name in modules_to_check:
        print(f"\nChecking: {module_name}")
        print("-" * 40)
        
        results = system.check_module(module_name)
        
        if results['violations']:
            print(f"Violations found ({len(results['violations'])}):")
            for violation in results['violations']:
                print(f"  - {violation.violation_type}: {violation}")
        else:
            print("✓ No violations detected")
            
        if results['recommendations']:
            print(f"\nRecommendations ({len(results['recommendations'])}):")
            for i, rec in enumerate(results['recommendations'][:3], 1):
                print(f"  {i}. [{rec['type'].upper()}] {rec['suggestion']}")


def demo_risky_modules(pkg_dir: Path):
    """Demonstrate risky module identification."""
    print("\n" + "="*60)
    print("DEMO 3: Risky Module Identification")
    print("="*60)
    
    system = setup_guardrails(str(pkg_dir), mode="observer")
    
    # Get risky modules
    risky = system.get_risky_modules(10)
    
    print(f"\nTop {len(risky)} riskiest modules:")
    print("-" * 40)
    
    for i, module in enumerate(risky, 1):
        print(f"\n{i}. {module['module']} (Risk Score: {module['score']})")
        print(f"   Path: {module['path']}")
        print(f"   Issues:")
        for reason in module['reasons']:
            print(f"     - {reason}")


def demo_adaptive_learning(pkg_dir: Path):
    """Demonstrate adaptive learning from violations."""
    print("\n" + "="*60)
    print("DEMO 4: Adaptive Learning")
    print("="*60)
    
    from guardrails.learning import get_adaptive_engine
    
    # Get the adaptive engine
    engine = get_adaptive_engine()
    
    # Simulate learning from violations
    print("\nSimulating learning from violations...")
    
    # Add some violation patterns
    violations = [
        {
            'type': 'hardcoded_path',
            'module': 'demo_package.data_loader',
            'details': {'path': 'E:/grid/logs/xai_traces'}
        },
        {
            'type': 'hardcoded_path', 
            'module': 'demo_package.initializer',
            'details': {'path': 'E:/grid/logs'}
        },
        {
            'type': 'circular_import',
            'module': 'demo_package.component_a',
            'details': {'circular_with': 'demo_package.component_b'}
        },
        {
            'type': 'missing_dependency',
            'module': 'demo_package.ml_processor',
            'details': {'missing': 'torch'}
        }
    ]
    
    for violation in violations:
        engine.add_violation(violation)
    
    # Trigger learning
    engine.learn()
    
    # Show learning results
    summary = engine.get_learning_summary()
    print(f"\nLearning Summary:")
    print(f"  Violations analyzed: {summary['violations_analyzed']}")
    print(f"  Patterns discovered: {summary['patterns_discovered']}")
    print(f"  Rules generated: {summary['rules_generated']}")
    
    # Show generated rules
    if engine.rules:
        print(f"\nGenerated Rules:")
        for rule in engine.rules[:3]:
            print(f"  - {rule['id']}: {rule['type']} (confidence: {rule['confidence']:.2f})")
            print(f"    Condition: {rule['condition']}")
            print(f"    Action: {rule['action']}")


def demo_event_monitoring(pkg_dir: Path):
    """Demonstrate event-based monitoring."""
    print("\n" + "="*60)
    print("DEMO 5: Real-time Event Monitoring")
    print("="*60)
    
    from guardrails.events import setup_realtime_monitoring, get_guardrail_analytics
    
    # Setup real-time monitoring
    events_received = []
    
    def event_handler(event):
        events_received.append(event)
        print(f"  Event: {event['type']} from {event['module']} ({event['severity']})")
    
    setup_realtime_monitoring(event_handler)
    
    # Trigger some violations
    system = setup_guardrails(str(pkg_dir), mode="warning")
    
    print("\nTriggering violations to generate events...")
    
    # Check problematic modules
    system.check_module("demo_package.data_loader")
    system.check_module("demo_package.component_a")
    
    # Show analytics
    print(f"\nEvents received: {len(events_received)}")
    
    analytics = get_guardrail_analytics()
    if analytics['violation_trends']:
        print("\nViolation Trends:")
        trends = analytics['violation_trends']
        print(f"  Total violations: {trends['total_violations']}")
        print(f"  Rate per hour: {trends['rate_per_hour']:.1f}")


def demo_comprehensive_report(pkg_dir: Path):
    """Generate a comprehensive report."""
    print("\n" + "="*60)
    print("DEMO 6: Comprehensive System Report")
    print("="*60)
    
    system = setup_guardrails(str(pkg_dir), mode="observer")
    
    # Generate full report
    report = system.get_system_report()
    
    print("\nSYSTEM REPORT SUMMARY")
    print("-" * 40)
    print(f"Mode: {report['mode']}")
    print(f"Modules analyzed: {report['stats']['modules_analyzed']}")
    print(f"Violations detected: {report['stats']['violations_detected']}")
    print(f"Rules generated: {report['learning']['rules_generated']}")
    
    # Trait distribution
    if report['profiler']['trait_distribution']:
        print("\nTrait Distribution:")
        for trait, count in report['profiler']['trait_distribution'].items():
            percentage = (count / report['profiler']['total_modules']) * 100
            print(f"  {trait}: {count} modules ({percentage:.1f}%)")
    
    # Violation types
    if report['middleware']['violation_types']:
        print("\nViolation Types:")
        for vtype, count in report['middleware']['violation_types'].items():
            print(f"  {vtype}: {count}")
    
    # Save detailed report
    report_file = Path("guardrail_demo_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nDetailed report saved to: {report_file}")


def main():
    """Run the complete demo."""
    print("\n" + "="*60)
    print("GUARDRAIL SYSTEM DEMONSTRATION")
    print("="*60)
    print("\nThis demo shows how the guardrail system detects and prevents")
    print("common issues that cause modules to compile but fail at runtime.")
    
    # Create demo codebase
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        print(f"\nCreating demo codebase in: {tmpdir}")
        
        pkg_dir = create_demo_codebase(tmpdir)
        
        # Run all demos
        demo_personality_profiling(pkg_dir)
        demo_guardrail_detection(pkg_dir)
        demo_risky_modules(pkg_dir)
        demo_adaptive_learning(pkg_dir)
        demo_event_monitoring(pkg_dir)
        demo_comprehensive_report(pkg_dir)
        
        print("\n" + "="*60)
        print("DEMO COMPLETE")
        print("="*60)
        print("\nKey Takeaways:")
        print("1. The guardrail system identifies risky patterns before runtime")
        print("2. Modules are classified by personality traits")
        print("3. Violations are detected and reported in real-time")
        print("4. The system learns from patterns to improve detection")
        print("5. Comprehensive reports help prioritize fixes")
        print("\nTo use in your project:")
        print("  from guardrails import setup_guardrails")
        print("  system = setup_guardrails('/path/to/your/code', mode='warning')")
        print("  results = system.check_module('your.module')")


if __name__ == "__main__":
    main()
