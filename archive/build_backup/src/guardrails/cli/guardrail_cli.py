"""
Guardrail CLI - Command-line interface for the guardrail system.

Provides commands to analyze, monitor, and manage guardrails.
"""

import click
import json
import sys
from pathlib import Path
from typing import Optional
import logging
from datetime import datetime, timezone

from .. import GuardrailSystem, setup_guardrails
from ..profiler.module_profiler import analyze_module, analyze_package
from ..middleware.personality_guardrails import get_middleware

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose):
    """Guardrail CLI - Module Personality Profiler & Boundary Enforcer"""
    if verbose:
        logging.getLogger('guardrails').setLevel(logging.DEBUG)


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for results')
@click.option('--format', 'output_format', type=click.Choice(['json', 'table']), default='table')
def analyze(path: str, output: Optional[str], output_format: str):
    """Analyze a module or package for guardrail issues."""
    
    path_obj = Path(path)
    
    if path_obj.is_file() and path_obj.suffix == '.py':
        # Analyze single module
        click.echo(f"Analyzing module: {path}")
        personality = analyze_module(path)
        
        results = {
            "module": personality.name,
            "path": personality.path,
            "personality": {
                "tone": personality.tone.value,
                "style": personality.style.value,
                "nuance": personality.nuance.value,
            },
            "traits": {
                "path_dependent": personality.is_path_dependent,
                "import_heavy": personality.is_import_heavy,
                "runtime_fragile": personality.is_runtime_fragile,
                "circular_prone": personality.is_circular_prone,
                "has_side_effects": personality.has_side_effects,
                "stateful": personality.is_stateful,
            },
            "issues": {
                "hardcoded_paths": personality.hardcoded_paths,
                "conditional_imports": personality.conditional_imports,
                "global_state": personality.global_state,
            }
        }
    else:
        # Analyze package
        click.echo(f"Analyzing package: {path}")
        personalities = analyze_package(path)
        
        results = {
            "package": path,
            "total_modules": len(personalities),
            "modules": []
        }
        
        for name, personality in personalities.items():
            module_data = {
                "name": name,
                "path": personality.path,
                "personality": {
                    "tone": personality.tone.value,
                    "style": personality.style.value,
                    "nuance": personality.nuance.value,
                },
                "traits": {
                    "path_dependent": personality.is_path_dependent,
                    "import_heavy": personality.is_import_heavy,
                    "runtime_fragile": personality.is_runtime_fragile,
                    "circular_prone": personality.is_circular_prone,
                    "has_side_effects": personality.has_side_effects,
                    "stateful": personality.is_stateful,
                },
                "issues": {
                    "hardcoded_paths_count": len(personality.hardcoded_paths),
                    "conditional_imports_count": len(personality.conditional_imports),
                    "global_state_count": len(personality.global_state),
                }
            }
            results["modules"].append(module_data)
    
    # Output results
    if output_format == 'json':
        output_text = json.dumps(results, indent=2)
    else:
        output_text = format_table(results)
    
    if output:
        with open(output, 'w') as f:
            f.write(output_text)
        click.echo(f"Results saved to: {output}")
    else:
        click.echo(output_text)


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--mode', type=click.Choice(['observer', 'warning', 'enforcement', 'adaptive']), 
              default='observer', help='Operating mode')
@click.option('--check-module', help='Check specific module for violations')
def monitor(path: str, mode: str, check_module: Optional[str]):
    """Monitor codebase with active guardrails."""
    
    click.echo(f"Starting guardrail monitoring in {mode} mode")
    
    # Setup guardrails
    system = setup_guardrails(path, mode)
    
    if check_module:
        # Check specific module
        click.echo(f"\nChecking module: {check_module}")
        results = system.check_module(check_module)
        
        click.echo(f"\nViolations found: {len(results['violations'])}")
        for violation in results['violations']:
            click.echo(f"  - {violation.violation_type}: {violation}")
            
        click.echo(f"\nRecommendations: {len(results['recommendations'])}")
        for rec in results['recommendations']:
            click.echo(f"  - [{rec['type']}] {rec['suggestion']}")
    else:
        # Show system status
        report = system.get_system_report()
        
        click.echo(f"\nSystem Status:")
        click.echo(f"  Modules analyzed: {report['stats']['modules_analyzed']}")
        click.echo(f"  Violations detected: {report['stats']['violations_detected']}")
        click.echo(f"  Rules generated: {report['learning']['rules_generated']}")
        
        # Show risky modules
        risky = system.get_risky_modules(5)
        if risky:
            click.echo(f"\nTop 5 Riskiest Modules:")
            for i, module in enumerate(risky, 1):
                click.echo(f"  {i}. {module['module']} (score: {module['score']})")
                for reason in module['reasons']:
                    click.echo(f"     - {reason}")
    
    # Keep running in enforcement mode
    if mode == 'enforcement':
        click.echo("\nGuardrails are actively enforcing. Press Ctrl+C to stop...")
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            click.echo("\nStopping guardrail monitoring...")
            system.shutdown()


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--limit', '-l', default=10, help='Number of risky modules to show')
def risky(path: str, limit: int):
    """Show modules with highest risk scores."""
    
    system = setup_guardrails(path, 'observer')
    risky_modules = system.get_risky_modules(limit)
    
    if not risky_modules:
        click.echo("No risky modules found!")
        return
        
    click.echo(f"\nTop {len(risky_modules)} Riskiest Modules:\n")
    
    for i, module in enumerate(risky_modules, 1):
        click.echo(f"{i}. {module['module']}")
        click.echo(f"   Path: {module['path']}")
        click.echo(f"   Risk Score: {module['score']}")
        click.echo(f"   Reasons:")
        for reason in module['reasons']:
            click.echo(f"     - {reason}")
        if module.get('violations_count', 0) > 0:
            click.echo(f"   Violations: {module['violations_count']}")
        click.echo()


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for report')
def report(path: str, output: Optional[str]):
    """Generate comprehensive guardrail report."""
    
    click.echo("Generating guardrail report...")
    
    system = setup_guardrails(path, 'observer')
    report_data = system.get_system_report()
    
    # Format report
    report_text = format_report(report_data)
    
    if output:
        with open(output, 'w') as f:
            f.write(report_text)
        click.echo(f"Report saved to: {output}")
    else:
        click.echo(report_text)


@cli.command()
@click.argument('module_name')
@click.argument('path', type=click.Path(exists=True))
def recommend(module_name: str, path: str):
    """Get recommendations for a specific module."""
    
    from ..learning import get_module_recommendations
    
    # First analyze to get module data
    personalities = analyze_package(path)
    personality = personalities.get(module_name)
    
    if not personality:
        click.echo(f"Module {module_name} not found in {path}")
        return
        
    module_data = {
        "has_hardcoded_paths": personality.is_path_dependent,
        "is_circular_prone": personality.is_circular_prone,
        "has_conditional_imports": len(personality.conditional_imports) > 0,
    }
    
    recommendations = get_module_recommendations(module_name, module_data)
    
    click.echo(f"\nRecommendations for {module_name}:\n")
    
    if not recommendations:
        click.echo("No recommendations available.")
        return
        
    for i, rec in enumerate(recommendations, 1):
        click.echo(f"{i}. [{rec['type'].upper()}] {rec['suggestion']}")
        if rec.get('based_on'):
            click.echo(f"   Based on similar module: {rec['based_on']}")
            click.echo(f"   Similarity: {rec['similarity']:.2f}")
        if rec.get('confidence'):
            click.echo(f"   Confidence: {rec['confidence']:.2f}")
        if rec.get('fixes'):
            click.echo("   Suggested fixes:")
            for fix in rec['fixes']:
                click.echo(f"     - {fix}")
        click.echo()


def format_table(results: dict) -> str:
    """Format results as a table."""
    if 'modules' not in results:
        # Single module
        return format_single_module(results)
    
    # Package analysis
    lines = []
    lines.append(f"Package: {results['package']}")
    lines.append(f"Total Modules: {results['total_modules']}")
    lines.append("")
    
    # Header
    lines.append(f"{'Module':<40} {'Personality':<20} {'Risk Factors':<30}")
    lines.append("-" * 90)
    
    # Modules
    for module in results['modules']:
        name = module['name'][:39]
        personality = f"{module['personality']['tone']}/{module['personality']['style']}"
        
        risk_factors = []
        if module['traits']['path_dependent']:
            risk_factors.append("paths")
        if module['traits']['runtime_fragile']:
            risk_factors.append("fragile")
        if module['traits']['circular_prone']:
            risk_factors.append("circular")
        if module['traits']['import_heavy']:
            risk_factors.append("heavy")
            
        risk_str = ", ".join(risk_factors) if risk_factors else "none"
        
        lines.append(f"{name:<40} {personality:<20} {risk_str:<30}")
    
    return "\n".join(lines)


def format_single_module(results: dict) -> str:
    """Format single module results."""
    lines = []
    lines.append(f"Module: {results['module']}")
    lines.append(f"Path: {results['path']}")
    lines.append("")
    
    # Personality
    p = results['personality']
    lines.append("Personality:")
    lines.append(f"  Tone: {p['tone']}")
    lines.append(f"  Style: {p['style']}")
    lines.append(f"  Nuance: {p['nuance']}")
    lines.append("")
    
    # Traits
    lines.append("Traits:")
    for trait, value in results['traits'].items():
        status = "✓" if value else "✗"
        lines.append(f"  {status} {trait.replace('_', ' ').title()}")
    lines.append("")
    
    # Issues
    issues = results['issues']
    if any(issues.values()):
        lines.append("Issues Found:")
        if issues['hardcoded_paths']:
            lines.append(f"  Hardcoded paths: {', '.join(issues['hardcoded_paths'])}")
        if issues['conditional_imports']:
            lines.append(f"  Conditional imports: {len(issues['conditional_imports'])}")
        if issues['global_state']:
            lines.append(f"  Global state: {', '.join(issues['global_state'])}")
    else:
        lines.append("No issues detected!")
    
    return "\n".join(lines)


def format_report(report_data: dict) -> str:
    """Format comprehensive report."""
    lines = []
    lines.append("GUARDRAIL SYSTEM REPORT")
    lines.append("=" * 50)
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Mode: {report_data['mode']}")
    lines.append("")
    
    # Stats
    stats = report_data['stats']
    lines.append("SYSTEM STATISTICS")
    lines.append("-" * 20)
    lines.append(f"Modules Analyzed: {stats['modules_analyzed']}")
    lines.append(f"Violations Detected: {stats['violations_detected']}")
    lines.append(f"Rules Generated: {stats['rules_generated']}")
    lines.append(f"Recommendations Made: {stats['recommendations_made']}")
    lines.append("")
    
    # Profiler summary
    profiler = report_data['profiler']
    lines.append("MODULE PERSONALITY DISTRIBUTION")
    lines.append("-" * 35)
    lines.append(f"Total Modules: {profiler['total_modules']}")
    lines.append("")
    
    traits = profiler['trait_distribution']
    if traits:
        lines.append("Trait Distribution:")
        for trait, count in traits.items():
            percentage = (count / profiler['total_modules']) * 100
            lines.append(f"  {trait}: {count} ({percentage:.1f}%)")
    lines.append("")
    
    # Top risky modules
    if 'top_risky_modules' in profiler:
        lines.append("TOP RISKY MODULES")
        lines.append("-" * 20)
        for i, module in enumerate(profiler['top_risky_modules'][:5], 1):
            lines.append(f"{i}. {module['module']} (score: {module['score']})")
            for reason in module['reasons']:
                lines.append(f"   - {reason}")
        lines.append("")
    
    # Violation summary
    middleware = report_data['middleware']
    lines.append("VIOLATION SUMMARY")
    lines.append("-" * 20)
    lines.append(f"Total Violations: {middleware['total_violations']}")
    lines.append(f"Modules with Violations: {middleware['modules_with_violations']}")
    
    if middleware['violation_types']:
        lines.append("\nViolation Types:")
        for vtype, count in middleware['violation_types'].items():
            lines.append(f"  {vtype}: {count}")
    lines.append("")
    
    # Learning summary
    learning = report_data['learning']
    lines.append("LEARNING SYSTEM")
    lines.append("-" * 20)
    lines.append(f"Violations Analyzed: {learning['violations_analyzed']}")
    lines.append(f"Patterns Discovered: {learning['patterns_discovered']}")
    lines.append(f"Rules Generated: {learning['rules_generated']}")
    lines.append(f"Modules Clustered: {learning['modules_clustered']}")
    lines.append("")
    
    return "\n".join(lines)


if __name__ == '__main__':
    cli()
