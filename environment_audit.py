# 1. Environment Scopes Analysis
from datetime import UTC


def analyze_environment_scopes():
    """Analyze Python environment scopes and potential pollution."""
    import os
    import sys
    from collections import defaultdict

    try:
        # Track module imports and their origins
        module_sources = defaultdict(list)
        for name, module in sys.modules.items():
            if hasattr(module, '__file__'):
                source = module.__file__ or 'built-in'
                module_sources[source].append(name)

        # Find duplicate module names across different paths
        name_to_paths = defaultdict(set)
        for path, modules in module_sources.items():
            for module in modules:
                name = module.split('.')[0]  # Get top-level package
                name_to_paths[name].add(path)

        # Identify potential scope conflicts
        # Convert sets to lists for JSON serialization
        conflicts = {k: list(v) for k, v in name_to_paths.items()
                    if len(v) > 1 and not k.startswith('_')}

        return {
            'module_sources': dict(module_sources),
            'conflicts': conflicts,
            'python_path': sys.path,
            'environment_vars': {k: v for k, v in os.environ.items()
                               if any(s in k.lower() for s in ['path', 'python', 'home', 'lib'])},
            'loaded_modules': len(sys.modules)
        }
    except Exception as e:
        return {'error': str(e)}

# 2. Memory Profiling
def profile_memory_usage():
    """Profile memory usage by object types."""
    import gc
    from collections import Counter

    try:
        # Get all objects in memory
        all_objects = gc.get_objects()
        types = Counter(type(obj).__name__ for obj in all_objects)

        return {
            'total_objects': len(all_objects),
            'top_object_types': dict(types.most_common(20)),
            'garbage': len(gc.garbage)
        }
    except Exception as e:
        return {'error': str(e)}

# 3. System Resources
def check_system_resources():
    """Check system resource utilization."""
    try:
        import platform

        import psutil

        process = psutil.Process()
        return {
            'system': {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'total_memory': psutil.virtual_memory().total,
                'available_memory': psutil.virtual_memory().available
            },
            'process': {
                'pid': process.pid,
                'name': process.name(),
                'memory_info': process.memory_info()._asdict(),
                'open_files': len(process.open_files()),
            }
        }
    except ImportError as e:
        return {'error': f"Dependency missing: {str(e)}"}
    except Exception as e:
        return {'error': str(e)}

# 4. Generate Accountability Report
def generate_accountability_report():
    """Generate comprehensive environment accountability report."""
    # Use timezone-aware UTC if available or fallback
    try:
        from datetime import datetime, timezone
        now_str = datetime.now(UTC).isoformat()
    except ImportError:
        from datetime import datetime
        now_str = datetime.utcnow().isoformat()

    report = {
        'timestamp': now_str,
        'environment_analysis': analyze_environment_scopes(),
        'memory_profile': profile_memory_usage(),
        'system_resources': check_system_resources(),
        'recommendations': []
    }

    # Add analysis and recommendations
    env = report['environment_analysis']
    if 'error' not in env and env.get('conflicts'):
        report['recommendations'].append({
            'severity': 'high',
            'issue': 'Module path conflicts detected',
            'details': f"Found {len(env['conflicts'])} modules with multiple load paths",
            'suggested_action': 'Resolve module path conflicts to prevent version mismatches'
        })

    mem = report['memory_profile']
    if 'error' not in mem and mem.get('garbage', 0) > 0:
        report['recommendations'].append({
            'severity': 'medium',
            'issue': 'Uncollectable garbage found',
            'details': f"Found {mem['garbage']} uncollectable objects",
            'suggested_action': 'Investigate and fix reference cycles'
        })

    return report

# 5. Run and save report
if __name__ == "__main__":
    import json
    import traceback

    try:
        report = generate_accountability_report()
        output_file = 'environment_accountability_report.json'
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Accountability report generated: {output_file}")
    except Exception:
        traceback.print_exc()
