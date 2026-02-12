# Guardrail System - Module Personality Profiler & Boundary Enforcer

A comprehensive system that characterizes module "personalities" and enforces dynamic boundaries to prevent the critical gap between compile-time success and runtime failures.

## Overview

The guardrail system addresses a common issue in large codebases where modules compile successfully but fail at runtime due to:
- Hardcoded paths (e.g., `E:/grid/logs/xai_traces`)
- Missing runtime dependencies
- Circular import patterns
- Module-level side effects
- Conditional import failures

## Architecture

The system consists of four main components:

### 1. Module Personality Profiler
Analyzes modules and assigns personality traits based on their patterns:
- **Path-Dependent**: Uses hardcoded filesystem paths
- **Runtime-Fragile**: Has conditional imports that may fail
- **Circular-Prone**: Participates in circular import chains
- **Import-Heavy**: Imports many modules (performance concern)
- **Side-Effect-Heavy**: Executes code at import time
- **Stateful**: Maintains global state

Each personality has fine-grained adjustments:
- **Tone**: Defensive (strict) vs Permissive (lenient)
- **Style**: Eager (load upfront) vs Lazy (load on demand)
- **Nuance**: Fail-fast vs Graceful degradation

### 2. Guardrail Middleware
Enforces boundaries based on module personalities:
- Validates paths before runtime
- Checks dependencies at import time
- Detects circular imports
- Provides real-time violation feedback

### 3. Event Integration
Connects with the UnifiedEventBus for:
- Real-time violation monitoring
- Historical analysis
- Pattern detection
- Metrics collection

### 4. Adaptive Learning Engine
Learns from violations to:
- Extract recurring patterns
- Generate new guardrail rules
- Provide intelligent recommendations
- Improve detection accuracy over time

## Quick Start

### Installation

```bash
# The guardrail system is part of the main codebase
# Ensure you're in the src directory
cd src
```

### Basic Usage

```python
from guardrails import setup_guardrails

# Initialize guardrails for your codebase
system = setup_guardrails('/path/to/your/code', mode='warning')

# Check a specific module
results = system.check_module('my_package.my_module')

if results['violations']:
    print(f"Found {len(results['violations'])} violations:")
    for violation in results['violations']:
        print(f"  - {violation.violation_type}: {violation}")
        
if results['recommendations']:
    print(f"Recommendations:")
    for rec in results['recommendations']:
        print(f"  - {rec['suggestion']}")
```

### Operating Modes

1. **Observer** (default): Log violations without blocking
2. **Warning**: Show warnings but allow execution
3. **Enforcement**: Block critical violations with exceptions
4. **Adaptive**: Self-adjusting strictness based on patterns

## CLI Tool

The guardrail system includes a comprehensive CLI for analysis and monitoring:

```bash
# Analyze a module or package
python -m guardrails.cli.guardrail_cli analyze /path/to/code

# Monitor with active guardrails
python -m guardrails.cli.guardrail_cli monitor /path/to/code --mode enforcement

# Show riskiest modules
python -m guardrails.cli.guardrail_cli risky /path/to/code --limit 10

# Generate comprehensive report
python -m guardrails.cli.guardrail_cli report /path/to/code --output report.txt

# Get recommendations for a module
python -m guardrails.cli.guardrail_cli recommend my.module /path/to/code
```

## Examples

### Detecting Hardcoded Paths

```python
from guardrails.profiler import analyze_module

personality = analyze_module('my_module.py')

if personality.is_path_dependent:
    print("Found hardcoded paths:")
    for path in personality.hardcoded_paths:
        print(f"  - {path}")
        # Suggest using environment variables instead
```

### Custom Violation Handling

```python
from guardrails.middleware import GuardrailMiddleware, get_middleware

def custom_violation_handler(violation):
    if violation.violation_type == "hardcoded_path":
        # Send to monitoring system
        alert_system.send_alert(violation)
    elif violation.severity == "error":
        # Create JIRA ticket
        jira.create_ticket(violation)

middleware = get_middleware()
middleware.register_violation_handler(custom_violation_handler)
```

### Real-time Monitoring

```python
from guardrails.events import setup_realtime_monitoring

def monitor_callback(event):
    if event['severity'] == 'error':
        print(f"CRITICAL: {event['module']} - {event['details']['message']}")
        # Trigger appropriate response

setup_realtime_monitoring(monitor_callback)
```

## Personality Traits Explained

### Path-Dependent Modules
These modules use hardcoded filesystem paths that:
- Break across different environments
- Cause runtime failures when paths don't exist
- Make deployment and testing difficult

**Detection**: Looks for absolute paths in string literals
**Recommendation**: Use environment variables or configuration files

### Runtime-Fragile Modules
These modules have conditional imports that:
- May fail depending on installed packages
- Create unpredictable runtime behavior
- Make dependency management complex

**Detection**: Identifies try/except blocks around imports
**Recommendation**: Document optional dependencies clearly

### Circular-Prone Modules
These modules participate in circular imports that:
- Cause ImportError at runtime
- Create tightly coupled code
- Make testing and refactoring difficult

**Detection**: Builds dependency graph and finds cycles
**Recommendation**: Extract shared code to separate modules

### Import-Heavy Modules
These modules import many dependencies that:
- Slow down import time
- Increase memory usage
- May indicate poor separation of concerns

**Detection**: Counts import statements
**Recommendation**: Consider lazy loading or module splitting

## Event Types

The system publishes various events for monitoring:

```python
# Violations
guardrail:violation:hardcoded_path
guardrail:violation:circular_import
guardrail:violation:missing_dependency
guardrail:violation:side_effect

# Warnings
guardrail:warning:import_heavy
guardrail:warning:stateful_module
guardrail:warning:runtime_fragile

# Information
guardrail:info:personality_changed
guardrail:info:boundary_cross
guardrail:info:guardrail_created

# Metrics
guardrail:metric:violation_rate
guardrail:metric:personality_distribution
guardrail:metric:trend_analysis
```

## Adaptive Learning

The system learns from violations to improve detection:

```python
from guardrails.learning import get_adaptive_engine, learn_from_violation

# The system automatically learns when violations are detected
# But you can also manually add violations
learn_from_violation({
    'type': 'hardcoded_path',
    'module': 'my_module',
    'details': {'path': '/hardcoded/path'}
})

# Get recommendations based on learned patterns
engine = get_adaptive_engine()
recommendations = engine.get_module_recommendations(
    'new_module',
    module_data
)
```

## Integration with Existing Systems

### With the UnifiedEventBus

```python
from grid.events.unified import get_unified_bus
from guardrails.events import connect_guardrail_events

# Connect guardrail events to the unified bus
publisher = connect_guardrail_events()

# Subscribe to guardrail events
bus = get_unified_bus()
bus.subscribe('guardrail:*', handle_guardrail_event)
```

### With the BoundaryEnforcerMiddleware

```python
from application.mothership.middleware.boundary_enforcer import BoundaryEnforcerMiddleware
from guardrails.middleware import PersonalityGuardrail

# Extend existing boundary enforcement
class EnhancedBoundaryEnforcer(BoundaryEnforcerMiddleware):
    def __init__(self):
        super().__init__()
        self.guardrails = PersonalityGuardrail()
        
    def check_import(self, module_name, target_layer):
        # Check existing boundaries
        result = super().check_import(module_name, target_layer)
        
        # Add personality-based checks
        violations = self.guardrails.validate_before_import()
        if violations:
            result['guardrail_violations'] = violations
            
        return result
```

## Configuration

### Environment Variables

```bash
# Guardrail system configuration
GUARDRAIL_MODE=observer  # observer, warning, enforcement, adaptive
GUARDRAIL_STORAGE_PATH=/path/to/learning/data
GUARDRAIL_LOG_LEVEL=INFO
```

### Configuration File

```yaml
# guardrail_config.yaml
guardrails:
  mode: warning
  storage_path: ./guardrail_data
  
  path_validation:
    allowed_roots:
      - /opt/app
      - ${HOME}/.local/share/app
    env_mappings:
      E:/grid: GRID_ROOT
      C:/Users: USER_ROOT
      
  rules:
    disable_rules: []
    custom_rules:
      - id: custom_path_rule
        type: hardcoded_path
        condition: "module.name.startswith('legacy.')"
        action: "warn"
        message: "Legacy module with hardcoded path"
```

## Best Practices

1. **Start in Observer Mode**: Understand your codebase before enforcing
2. **Whitelist Critical Modules**: Some modules may need special handling
3. **Monitor Trends**: Use event analytics to track improvement over time
4. **Update Recommendations**: The system learns from your patterns
5. **Integrate with CI/CD**: Add guardrail checks to your pipeline

## Troubleshooting

### Common Issues

1. **False Positives**: Add modules to whitelist or adjust personality traits
2. **Performance Impact**: Use observer mode or limit analysis scope
3. **Missing Dependencies**: Ensure all required packages are installed
4. **Circular Imports**: May require refactoring to resolve

### Debug Mode

```python
import logging
logging.getLogger('guardrails').setLevel(logging.DEBUG)

# This will show detailed analysis information
```

## Contributing

The guardrail system is designed to be extensible:

1. **Add New Personality Traits**: Extend the `ModulePersonality` class
2. **Create Custom Rules**: Implement rule generators for specific patterns
3. **Add Event Handlers**: Subscribe to guardrail events for custom logic
4. **Extend Learning**: Implement new pattern extraction algorithms

## License

This guardrail system is part of the GRID Intelligence Framework.
