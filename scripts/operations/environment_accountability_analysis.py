"""
Environmental Accountability Analysis
======================================
Comprehensive analysis of environment scopes, profiling, and accountability
for detecting corruption, masking, and parasitic functions.

This script performs:
1. Foundation environmental analysis
2. Pattern recognition for corruption
3. Accountable components and entities generation
4. Helper and masking function profiling
5. Precise accountability report generation
"""

import gc
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# =============================================================================
# Foundation Analysis
# =============================================================================

def analyze_import_system() -> dict[str, Any]:
    """Analyze Python import system for scope pollution."""
    results = {
        'total_modules': len(sys.modules),
        'module_sources': defaultdict(list),
        'duplicate_names': {},
        'shadowing_candidates': [],
        'import_order': []
    }

    # Track module origins
    for name, module in sys.modules.items():
        if hasattr(module, '__file__') and module.__file__:
            path = module.__file__
            results['module_sources'][path].append(name)
        else:
            results['module_sources']['built-in'].append(name)

    # Find duplicate module names across different paths
    name_to_paths = defaultdict(set)
    for path, modules in results['module_sources'].items():
        for module in modules:
            base_name = module.split('.')[0]
            name_to_paths[base_name].add(path)

    results['duplicate_names'] = {
        k: list(v) for k, v in name_to_paths.items()
        if len(v) > 1 and not k.startswith('_')
    }

    # Identify potential shadowing
    builtins = set(dir(__builtins__))
    user_modules = set(sys.modules.keys()) - builtins
    results['shadowing_candidates'] = [
        name for name in user_modules if name in builtins
    ]

    return results


def analyze_environment_variables() -> dict[str, Any]:
    """Analyze environment variables for pollution."""
    env_vars = dict(os.environ)

    # Categorize variables
    categories = {
        'python': [],
        'path': [],
        'database': [],
        'security': [],
        'config': [],
        'other': []
    }

    for key in env_vars.keys():
        key_lower = key.lower()
        if any(x in key_lower for x in ['python', 'py', 'pip', 'virtualenv', 'venv']):
            categories['python'].append(key)
        elif 'path' in key_lower:
            categories['path'].append(key)
        elif any(x in key_lower for x in ['db', 'database', 'sql', 'postgres', 'redis']):
            categories['database'].append(key)
        elif any(x in key_lower for x in ['secret', 'key', 'token', 'password', 'auth']):
            categories['security'].append(key)
        elif any(x in key_lower for x in ['config', 'setting', 'env']):
            categories['config'].append(key)
        else:
            categories['other'].append(key)

    # Check for duplicates in PATH
    path_entries = os.environ.get('PATH', '').split(os.pathsep)
    duplicates = [p for p in path_entries if path_entries.count(p) > 1]

    return {
        'total_vars': len(env_vars),
        'categorized': categories,
        'path_duplicates': list(set(duplicates)),
        'sensitive_keys': [k for k in env_vars.keys() if any(
            x in k.lower() for x in ['secret', 'key', 'token', 'password']
        )]
    }


def analyze_memory_state() -> dict[str, Any]:
    """Analyze memory state for leaks and corruption."""
    all_objects = gc.get_objects()
    type_counts = Counter(type(obj).__name__ for obj in all_objects)

    # Find objects with suspicious counts
    suspicious_types = {
        name: count for name, count in type_counts.most_common(50)
        if count > 1000 and not any(
            x in name.lower() for x in ['str', 'int', 'tuple', 'dict', 'list']
        )
    }

    return {
        'total_objects': len(all_objects),
        'top_types': dict(type_counts.most_common(30)),
        'suspicious_types': suspicious_types,
        'garbage_count': len(gc.garbage),
        'gc_stats': {
            'collections': gc.get_stats(),
            'thresholds': gc.get_threshold()
        }
    }


# =============================================================================
# Pattern Recognition for Corruption
# =============================================================================

def should_skip(path: Path) -> bool:
    """Check if a path should be skipped in analysis."""
    skip_dirs = {'.venv', 'venv', '__pycache__', '.git', '.pytest_cache', '.mypy_cache'}
    return any(part in skip_dirs for part in path.parts)


def identify_corruption_patterns(codebase_path: Path) -> dict[str, Any]:
    """Identify patterns that indicate environment corruption."""
    patterns = {
        'module_manipulation': [],
        'environment_manipulation': [],
        'monkey_patching': [],
        'dynamic_imports': [],
        'global_state_modification': [],
        'reflection_abuse': []
    }

    # Search for dangerous patterns
    dangerous_patterns = {
        'module_manipulation': [
            'del sys.modules',
            'sys.modules.clear',
            'sys.modules.update',
            'sys.modules.__setitem__'
        ],
        'environment_manipulation': [
            'os.environ',
            'os.putenv',
            'os.unsetenv'
        ],
        'monkey_patching': [
            '.__setattr__',
            '.__delattr__',
            'setattr(',
            'delattr('
        ],
        'dynamic_imports': [
            'importlib.import_module',
            '__import__',
            'exec(',
            'eval('
        ],
        'global_state_modification': [
            'globals()[',
            'locals()[',
            'vars()['
        ]
    }

    # Scan Python files
    for py_file in codebase_path.rglob('*.py'):
        if should_skip(py_file):
            continue
        try:
            with open(py_file, encoding='utf-8', errors='ignore') as f:
                content = f.read()

                for category, search_terms in dangerous_patterns.items():
                    for term in search_terms:
                        if term in content:
                            patterns[category].append({
                                'file': str(py_file),
                                'pattern': term,
                                'line': content[:content.index(term)].count('\n') + 1
                            })
        except Exception:
            continue

    return patterns


def identify_masking_functions(codebase_path: Path) -> dict[str, Any]:
    """Identify functions that mask or hide behavior."""
    masking_indicators = {
        'wrapper': [],
        'proxy': [],
        'delegate': [],
        'intercept': [],
        'override': [],
        'sanitize': [],
        'filter': [],
        'transform': []
    }

    for py_file in codebase_path.rglob('*.py'):
        if should_skip(py_file):
            continue
        try:
            with open(py_file, encoding='utf-8', errors='ignore') as f:
                content = f.read()

                for category, keywords in masking_indicators.items():
                    for keyword in keywords:
                        if keyword in content.lower():
                            # Find function definitions
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if f'def {keyword}' in line.lower() or f'class {keyword}' in line.lower():
                                    masking_indicators[category].append({
                                        'file': str(py_file),
                                        'line': i + 1,
                                        'definition': line.strip()
                                    })
        except Exception:
            continue

    return masking_indicators


# =============================================================================
# Accountable Components and Entities
# =============================================================================

def generate_accountable_entities(codebase_path: Path) -> dict[str, Any]:
    """Generate list of accountable components and entities."""
    entities = {
        'modules': [],
        'classes': [],
        'functions': [],
        'globals': [],
        'decorators': []
    }

    for py_file in codebase_path.rglob('*.py'):
        if should_skip(py_file):
            continue
        try:
            # Read and parse file
            with open(py_file, encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Extract module info
            module_name = str(py_file.relative_to(codebase_path)).replace('/', '.').replace('.py', '')
            entities['modules'].append({
                'name': module_name,
                'path': str(py_file),
                'size': len(content),
                'line_count': content.count('\n') + 1
            })

            # Extract classes
            lines = content.split('\n')
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('class '):
                    entities['classes'].append({
                        'module': module_name,
                        'name': stripped.split('(')[0].replace('class ', '').strip(':'),
                        'line': i + 1,
                        'file': str(py_file)
                    })
                elif stripped.startswith('def ') and not stripped.startswith('def _'):
                    entities['functions'].append({
                        'module': module_name,
                        'name': stripped.split('(')[0].replace('def ', '').strip(),
                        'line': i + 1,
                        'file': str(py_file)
                    })
                elif stripped.startswith('@'):
                    entities['decorators'].append({
                        'module': module_name,
                        'name': stripped,
                        'line': i + 1,
                        'file': str(py_file)
                    })

        except Exception:
            continue

    return entities


def identify_parasitic_functions(codebase_path: Path) -> dict[str, Any]:
    """Identify potentially parasitic or masking functions."""
    parasitic_indicators = [
        'hook', 'inject', 'patch', 'monkey', 'override',
        'intercept', 'wrap', 'proxy', 'delegate', 'mask',
        'hide', 'obscure', 'conceal', 'cloak', 'stealth'
    ]

    parasitic_functions = []

    for py_file in codebase_path.rglob('*.py'):
        if should_skip(py_file):
            continue
        try:
            with open(py_file, encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('def ') or stripped.startswith('async def '):
                    func_name = stripped.split('(')[0].replace('def ', '').replace('async def ', '').strip()

                    if any(indicator in func_name.lower() for indicator in parasitic_indicators):
                        parasitic_functions.append({
                            'name': func_name,
                            'file': str(py_file),
                            'line': i + 1,
                            'definition': stripped
                        })
        except Exception:
            continue

    return parasitic_functions


# =============================================================================
# Helper Profiling
# =============================================================================

def profile_helper_functions(codebase_path: Path) -> dict[str, Any]:
    """Profile helper functions for suspicious behavior."""
    helper_patterns = {
        'dynamic_execution': ['exec', 'eval', 'compile'],
        'reflection': ['getattr', 'setattr', 'delattr', 'hasattr'],
        'introspection': ['inspect', 'type', 'isinstance'],
        'module_manipulation': ['importlib', '__import__', 'reload'],
        'environment_access': ['os.environ', 'os.getenv', 'sys.modules']
    }

    helper_usage = defaultdict(list)

    for py_file in codebase_path.rglob('*.py'):
        if should_skip(py_file):
            continue
        try:
            with open(py_file, encoding='utf-8', errors='ignore') as f:
                content = f.read()

            for category, patterns in helper_patterns.items():
                for pattern in patterns:
                    if pattern in content:
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if pattern in line:
                                helper_usage[category].append({
                                    'file': str(py_file),
                                    'line': i + 1,
                                    'pattern': pattern,
                                    'context': line.strip()
                                })
        except Exception:
            continue

    return dict(helper_usage)


# =============================================================================
# Main Analysis
# =============================================================================

def run_comprehensive_analysis(codebase_root: str = None) -> dict[str, Any]:
    """Run comprehensive environmental accountability analysis."""
    if codebase_root is None:
        codebase_root = str(Path(__file__).parent.parent.parent)

    codebase_path = Path(codebase_root)

    print("🔍 Running Environmental Accountability Analysis")
    print(f"📂 Codebase: {codebase_path}")
    print(f"⏰ Started: {datetime.now().isoformat()}")
    print()

    # 1. Foundation Analysis
    print("1️⃣  Running foundation analysis...")
    foundation = {
        'import_system': analyze_import_system(),
        'environment_variables': analyze_environment_variables(),
        'memory_state': analyze_memory_state()
    }

    # 2. Pattern Recognition
    print("2️⃣  Identifying corruption patterns...")
    patterns = {
        'corruption_patterns': identify_corruption_patterns(codebase_path),
        'masking_functions': identify_masking_functions(codebase_path)
    }

    # 3. Accountable Entities
    print("3️⃣  Generating accountable entities...")
    entities = {
        'accountable_entities': generate_accountable_entities(codebase_path),
        'parasitic_functions': identify_parasitic_functions(codebase_path)
    }

    # 4. Helper Profiling
    print("4️⃣  Profiling helper functions...")
    profiling = {
        'helper_profiling': profile_helper_functions(codebase_path)
    }

    # 5. Generate Report
    print("5️⃣  Generating accountability report...")
    report = {
        'metadata': {
            'timestamp': datetime.utcnow().isoformat(),
            'analysis_type': 'environmental_accountability',
            'codebase_root': str(codebase_path),
            'python_version': sys.version,
            'platform': sys.platform
        },
        'foundation_analysis': foundation,
        'pattern_recognition': patterns,
        'accountable_entities': entities,
        'helper_profiling': profiling
    }

    # Add summary statistics
    report['summary'] = {
        'total_modules_scanned': len(foundation['import_system']['module_sources']),
        'corruption_patterns_found': sum(
            len(v) for v in patterns['corruption_patterns'].values()
        ),
        'masking_functions_found': sum(
            len(v) for v in patterns['masking_functions'].values()
        ),
        'parasitic_functions_found': len(entities['parasitic_functions']),
        'helper_usage_found': sum(
            len(v) for v in profiling['helper_profiling'].values()
        )
    }

    # Generate findings and recommendations
    report['findings'] = generate_findings(report)
    report['recommendations'] = generate_recommendations(report)

    print("✅ Analysis complete!")
    print("📊 Summary:")
    print(f"   - Modules scanned: {report['summary']['total_modules_scanned']}")
    print(f"   - Corruption patterns: {report['summary']['corruption_patterns_found']}")
    print(f"   - Masking functions: {report['summary']['masking_functions_found']}")
    print(f"   - Parasitic functions: {report['summary']['parasitic_functions_found']}")
    print(f"   - Helper usage: {report['summary']['helper_usage_found']}")

    return report


def generate_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate key findings from analysis."""
    findings = []

    # Check for module duplication
    dup_modules = report['foundation_analysis']['import_system']['duplicate_names']
    if dup_modules:
        findings.append({
            'severity': 'high',
            'category': 'module_duplication',
            'description': f"Found {len(dup_modules)} modules with duplicate load paths",
            'details': list(dup_modules.keys())[:10],
            'impact': '可能导致版本冲突和不可预测的行为'
        })

    # Check for environment manipulation
    env_patterns = report['pattern_recognition']['corruption_patterns']['environment_manipulation']
    if env_patterns:
        findings.append({
            'severity': 'medium',
            'category': 'environment_manipulation',
            'description': f"Found {len(env_patterns)} instances of environment manipulation",
            'details': [p['file'] for p in env_patterns[:10]],
            'impact': '可能污染运行时环境'
        })

    # Check for parasitic functions
    parasitic = report['accountable_entities']['parasitic_functions']
    if parasitic:
        findings.append({
            'severity': 'high',
            'category': 'parasitic_functions',
            'description': f"Found {len(parasitic)} potentially parasitic functions",
            'details': [f['name'] for f in parasitic[:10]],
            'impact': '可能隐藏恶意行为或掩盖真实操作'
        })

    # Check for memory issues
    suspicious = report['foundation_analysis']['memory_state']['suspicious_types']
    if suspicious:
        findings.append({
            'severity': 'medium',
            'category': 'memory_leak_suspects',
            'description': f"Found {len(suspicious)} object types with suspicious counts",
            'details': list(suspicious.keys())[:10],
            'impact': '可能存在内存泄漏'
        })

    return findings


def generate_recommendations(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate actionable recommendations."""
    recommendations = []

    # Module duplication recommendations
    if report['foundation_analysis']['import_system']['duplicate_names']:
        recommendations.append({
            'priority': 'high',
            'action': 'resolve_module_conflicts',
            'description': 'Resolve module path conflicts by consolidating imports',
            'steps': [
                'Identify which version of each module should be used',
                'Remove or shadow conflicting paths',
                'Use absolute imports consistently'
            ]
        })

    # Environment manipulation recommendations
    if report['pattern_recognition']['corruption_patterns']['environment_manipulation']:
        recommendations.append({
            'priority': 'medium',
            'action': 'audit_environment_manipulation',
            'description': 'Audit all environment manipulation code',
            'steps': [
                'Review each instance of os.environ modification',
                'Ensure changes are properly scoped',
                'Add logging for all environment changes'
            ]
        })

    # Parasitic function recommendations
    if report['accountable_entities']['parasitic_functions']:
        recommendations.append({
            'priority': 'high',
            'action': 'audit_parasitic_functions',
            'description': 'Audit all potentially parasitic functions',
            'steps': [
                'Review function purposes and implementations',
                'Ensure transparency and documentation',
                'Add audit logging for suspicious operations'
            ]
        })

    return recommendations


def save_report(report: dict[str, Any], output_path: str = None) -> str:
    """Save report to file."""
    if output_path is None:
        output_path = 'environment_accountability_report.json'

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n📄 Report saved to: {output_path}")
    return str(output_path)


if __name__ == '__main__':
    # Run analysis
    report = run_comprehensive_analysis()

    # Save report
    report_path = save_report(report)

    # Print summary
    print("\n" + "="*80)
    print("🔍 ENVIRONMENTAL ACCOUNTABILITY ANALYSIS COMPLETE")
    print("="*80)
    print("\n📊 Key Findings:")
    for finding in report['findings']:
        print(f"\n  ⚠️  {finding['category'].upper()}")
        print(f"     Severity: {finding['severity']}")
        print(f"     {finding['description']}")

    print("\n💡 Recommendations:")
    for rec in report['recommendations']:
        print(f"\n  🎯 {rec['action']} (Priority: {rec['priority']})")
        print(f"     {rec['description']}")

    print(f"\n📄 Full report: {report_path}")
