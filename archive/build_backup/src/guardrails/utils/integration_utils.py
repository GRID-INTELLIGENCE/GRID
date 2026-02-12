"""
Guardrail Integration Utilities

Helper functions for integrating the guardrail system with existing codebases.
"""

import ast
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import json

from ..profiler.module_profiler import analyze_module, ModulePersonality


def scan_for_issues(
    codebase_path: str,
    issue_types: Optional[List[str]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Scan a codebase for specific issue types.
    
    Args:
        codebase_path: Root path of the codebase
        issue_types: List of issue types to scan for (None = all)
        
    Returns:
        Dictionary mapping issue types to list of occurrences
    """
    issue_types = issue_types or [
        "hardcoded_paths",
        "conditional_imports",
        "circular_imports",
        "side_effects",
        "global_state"
    ]
    
    results = {issue: [] for issue in issue_types}
    
    # Find all Python files
    codebase = Path(codebase_path)
    if not codebase.exists():
        raise FileNotFoundError(f"Codebase not found: {codebase_path}")
        
    python_files = list(codebase.rglob("*.py"))
    
    # Analyze each file
    for py_file in python_files:
        try:
            personality = analyze_module(py_file)
            
            if "hardcoded_paths" in issue_types and personality.hardcoded_paths:
                results["hardcoded_paths"].append({
                    "file": str(py_file),
                    "paths": personality.hardcoded_paths,
                    "severity": "high" if len(personality.hardcoded_paths) > 1 else "medium"
                })
                
            if "conditional_imports" in issue_types and personality.conditional_imports:
                results["conditional_imports"].append({
                    "file": str(py_file),
                    "imports": personality.conditional_imports,
                    "severity": "medium"
                })
                
            if "circular_imports" in issue_types and personality.is_circular_prone:
                results["circular_imports"].append({
                    "file": str(py_file),
                    "dependencies": list(personality.circular_dependencies),
                    "severity": "high"
                })
                
            if "side_effects" in issue_types and personality.has_side_effects:
                results["side_effects"].append({
                    "file": str(py_file),
                    "severity": "medium"
                })
                
            if "global_state" in issue_types and personality.global_state:
                results["global_state"].append({
                    "file": str(py_file),
                    "variables": personality.global_state,
                    "severity": "low"
                })
                
        except Exception as e:
            results.setdefault("errors", []).append({
                "file": str(py_file),
                "error": str(e),
                "severity": "error"
            })
            
    return results


def generate_fix_suggestions(issue: Dict[str, Any]) -> List[str]:
    """Generate fix suggestions for a specific issue."""
    issue_type = issue.get("type", "")
    
    suggestions = {
        "hardcoded_paths": [
            f"Replace '{issue.get('paths', [''])[0]}' with environment variable",
            "Use pathlib.Path for cross-platform compatibility",
            "Consider using a configuration file",
        ],
        "conditional_imports": [
            "Add missing dependency to requirements.txt",
            "Add optional import documentation",
            "Consider using importlib for dynamic imports",
        ],
        "circular_imports": [
            "Extract shared code to separate module",
            "Use dependency injection pattern",
            "Consider using protocols/interfaces",
        ],
        "side_effects": [
            "Move initialization code to __init__.py",
            "Use lazy initialization with functions",
            "Add configuration flag to control initialization",
        ],
        "global_state": [
            "Encapsulate state in a class",
            "Use dependency injection",
            "Consider using a configuration object",
        ],
    }
    
    return suggestions.get(issue_type, ["Review and refactor the code"])


def create_remediation_plan(
    issues: Dict[str, List[Dict[str, Any]]],
    priority_order: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a prioritized remediation plan.
    
    Args:
        issues: Dictionary of issues from scan_for_issues
        priority_order: Custom priority order for issue types
        
    Returns:
        Prioritized remediation plan with steps
    """
    priority_order = priority_order or [
        "hardcoded_paths",
        "circular_imports",
        "conditional_imports",
        "side_effects",
        "global_state"
    ]
    
    # Severity scores
    severity_scores = {
        "high": 10,
        "medium": 5,
        "low": 2,
        "error": 15
    }
    
    # Calculate total risk score
    total_score = 0
    all_issues = []
    
    for issue_type, occurrences in issues.items():
        for occurrence in occurrences:
            severity = occurrence.get("severity", "low")
            score = severity_scores.get(severity, 1)
            total_score += score
            
            all_issues.append({
                "type": issue_type,
                "file": occurrence.get("file", "unknown"),
                "severity": severity,
                "score": score,
                "details": occurrence,
            })
            
    # Sort by priority and severity
    def sort_key(issue):
        type_priority = priority_order.index(issue["type"]) if issue["type"] in priority_order else 999
        severity_priority = severity_scores.get(issue["severity"], 0)
        return (type_priority, -severity_priority)
        
    sorted_issues = sorted(all_issues, key=sort_key)
    
    # Group by priority level
    high_priority = [i for i in sorted_issues if i["severity"] == "high"]
    medium_priority = [i for i in sorted_issues if i["severity"] == "medium"]
    low_priority = [i for i in sorted_issues if i["severity"] == "low"]
    
    # Create plan
    plan = {
        "summary": {
            "total_issues": len(all_issues),
            "total_score": total_score,
            "high_priority": len(high_priority),
            "medium_priority": len(medium_priority),
            "low_priority": len(low_priority),
        },
        "phases": [
            {
                "name": "Critical Issues",
                "priority": 1,
                "issues": high_priority[:10],  # Top 10 high priority
                "estimated_effort": f"{len(high_priority)} hours",
            },
            {
                "name": "Important Issues",
                "priority": 2,
                "issues": medium_priority[:15],
                "estimated_effort": f"{len(medium_priority)} hours",
            },
            {
                "name": "Nice to Have",
                "priority": 3,
                "issues": low_priority[:10],
                "estimated_effort": f"{len(low_priority)} hours",
            },
        ],
        "total_estimated_effort": f"{len(high_priority) + len(medium_priority) + len(low_priority)} hours",
    }
    
    # Add fix suggestions to each issue
    for phase in plan["phases"]:
        for issue in phase["issues"]:
            issue["suggestions"] = generate_fix_suggestions(issue)
            
    return plan


def export_to_json(
    data: Dict[str, Any],
    output_path: str,
    pretty: bool = True
) -> None:
    """Export analysis results to JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        if pretty:
            json.dump(data, f, indent=2, default=str)
        else:
            json.dump(data, f, default=str)
            

def import_from_json(input_path: str) -> Dict[str, Any]:
    """Import analysis results from JSON file."""
    with open(input_path, 'r') as f:
        return json.load(f)


def compare_analyses(
    baseline: Dict[str, Any],
    current: Dict[str, Any]
) -> Dict[str, Any]:
    """Compare two analyses to show progress or regressions."""
    comparison = {
        "timestamp": str(Path(__file__).stat().st_mtime),
        "baseline_date": baseline.get("timestamp", "unknown"),
        "current_date": current.get("timestamp", "unknown"),
        "improvements": [],
        "regressions": [],
        "unchanged": [],
    }
    
    # Extract issue counts
    baseline_counts = {
        issue_type: len(issues)
        for issue_type, issues in baseline.items()
        if isinstance(issues, list)
    }
    
    current_counts = {
        issue_type: len(issues)
        for issue_type, issues in current.items()
        if isinstance(issues, list)
    }
    
    # Compare
    all_types = set(baseline_counts.keys()) | set(current_counts.keys())
    
    for issue_type in all_types:
        baseline_count = baseline_counts.get(issue_type, 0)
        current_count = current_counts.get(issue_type, 0)
        
        difference = baseline_count - current_count
        
        if difference > 0:
            comparison["improvements"].append({
                "type": issue_type,
                "before": baseline_count,
                "after": current_count,
                "difference": difference,
            })
        elif difference < 0:
            comparison["regressions"].append({
                "type": issue_type,
                "before": baseline_count,
                "after": current_count,
                "difference": abs(difference),
            })
        else:
            comparison["unchanged"].append({
                "type": issue_type,
                "count": current_count,
            })
            
    # Calculate net improvement
    total_improvements = sum(i["difference"] for i in comparison["improvements"])
    total_regressions = sum(r["difference"] for r in comparison["regressions"])
    
    comparison["net_improvement"] = total_improvements - total_regressions
    comparison["status"] = "improved" if comparison["net_improvement"] > 0 else "regressed" if comparison["net_improvement"] < 0 else "unchanged"
    
    return comparison


def generate_migration_guide(
    old_module: Path,
    new_module: Path,
    old_personality: ModulePersonality,
    new_personality: ModulePersonality
) -> Dict[str, Any]:
    """
    Generate a migration guide when refactoring modules.
    
    Shows what issues were fixed and what new issues were introduced.
    """
    # Compare personalities
    fixed_issues = []
    introduced_issues = []
    
    if old_personality.is_path_dependent and not new_personality.is_path_dependent:
        fixed_issues.append("Removed hardcoded paths")
    elif not old_personality.is_path_dependent and new_personality.is_path_dependent:
        introduced_issues.append("Added hardcoded paths")
        
    if old_personality.is_runtime_fragile and not new_personality.is_runtime_fragile:
        fixed_issues.append("Fixed conditional imports")
    elif not old_personality.is_runtime_fragile and new_personality.is_runtime_fragile:
        introduced_issues.append("Added conditional imports")
        
    if old_personality.is_circular_prone and not new_personality.is_circular_prone:
        fixed_issues.append("Removed circular dependencies")
    elif not old_personality.is_circular_prone and new_personality.is_circular_prone:
        introduced_issues.append("Introduced circular dependencies")
        
    if old_personality.has_side_effects and not new_personality.has_side_effects:
        fixed_issues.append("Removed module-level side effects")
    elif not old_personality.has_side_effects and new_personality.has_side_effects:
        introduced_issues.append("Added module-level side effects")
        
    return {
        "old_module": str(old_module),
        "new_module": str(new_module),
        "fixed_issues": fixed_issues,
        "introduced_issues": introduced_issues,
        "old_score": calculate_risk_score(old_personality),
        "new_score": calculate_risk_score(new_personality),
        "net_improvement": calculate_risk_score(old_personality) - calculate_risk_score(new_personality),
        "recommendations": generate_refactoring_recommendations(new_personality),
    }


def calculate_risk_score(personality: ModulePersonality) -> int:
    """Calculate a risk score for a module personality."""
    score = 0
    
    if personality.is_path_dependent:
        score += 10 * len(personality.hardcoded_paths)
    if personality.is_runtime_fragile:
        score += 5
    if personality.is_circular_prone:
        score += 15
    if personality.is_import_heavy:
        score += 3
    if personality.has_side_effects:
        score += 2
    if personality.is_stateful:
        score += 1
        
    return score


def generate_refactoring_recommendations(personality: ModulePersonality) -> List[str]:
    """Generate refactoring recommendations based on personality."""
    recommendations = []
    
    if personality.is_path_dependent:
        recommendations.append(
            "Replace hardcoded paths with environment variables or configuration files"
        )
        
    if personality.is_import_heavy:
        recommendations.append(
            "Consider splitting into smaller modules or using lazy loading"
        )
        
    if personality.is_runtime_fragile:
        recommendations.append(
            "Add proper error handling for optional dependencies"
        )
        
    if personality.is_circular_prone:
        recommendations.append(
            "Refactor to remove circular dependencies"
        )
        
    if personality.has_side_effects:
        recommendations.append(
            "Move side-effect code into functions or classes"
        )
        
    if personality.is_stateful:
        recommendations.append(
            "Consider encapsulating global state in a configuration object"
        )
        
    return recommendations or ["Module looks good! No major refactoring needed."]


def create_issue_template(issue: Dict[str, Any]) -> str:
    """Create a GitHub/GitLab issue template for an issue."""
    issue_type = issue.get("type", "")
    file = issue.get("file", "unknown")
    severity = issue.get("severity", "unknown")
    
    template = f"""## Guardrail Issue: {issue_type.replace('_', ' ').title()}

**File:** `{file}`  
**Severity:** {severity.upper()}  
**Detected by:** Guardrail System

### Issue Details
"""
    
    if issue_type == "hardcoded_paths":
        template += f"""
The following hardcoded paths were detected:
"""
        for path in issue.get("paths", []):
            template += f"- `{path}`\n"
            
        template += f"""
### Why This Matters
Hardcoded paths can break when the code is deployed to different environments.
They make testing difficult and reduce code portability.

### Suggested Fix
Replace hardcoded paths with environment variables or configuration files:

```python
import os
from pathlib import Path

# Instead of:
DATA_DIR = "{issue.get('paths', [''])[0]}"

# Use:
DATA_DIR = Path(os.getenv("YOUR_APP_ROOT", "/default/path")) / "data"
```
"""
    
    elif issue_type == "conditional_imports":
        template += f"""
The following conditional imports were detected:
"""
        for imp in issue.get("imports", []):
            template += f"- `{imp}`\n"
            
        template += f"""
### Why This Matters
Conditional imports can cause runtime failures when dependencies are missing.
They make it unclear what the actual requirements are.

### Suggested Fix
- Document optional dependencies clearly
- Add to requirements-optional.txt
- Provide fallback implementations
"""
    
    template += f"""
### Additional Resources
- [Guardrail System Documentation](../docs/guardrails/README.md)
- Run `python -m guardrails.cli analyze {file}` for more details

### Acceptance Criteria
- [ ] Hardcoded paths replaced with environment variables
- [ ] Code works across different environments
- [ ] Tests pass in CI/CD pipeline
"""
    
    return template


# Convenience functions for quick use
def quick_scan(codebase_path: str) -> Dict[str, Any]:
    """Quick scan for common issues."""
    issues = scan_for_issues(codebase_path)
    plan = create_remediation_plan(issues)
    return {
        "issues": issues,
        "plan": plan,
        "summary": plan["summary"],
    }


def quick_fix_recommendations(module_path: str) -> List[str]:
    """Get quick fix recommendations for a module."""
    personality = analyze_module(module_path)
    return generate_refactoring_recommendations(personality)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        path = sys.argv[1]
        print(f"Scanning {path}...")
        results = quick_scan(path)
        
        print(f"\nFound {results['summary']['total_issues']} issues")
        print(f"Risk score: {results['summary']['total_score']}")
        
        print("\nTop issues to fix:")
        for issue in results['plan']['phases'][0]['issues'][:5]:
            print(f"  - {issue['type']}: {issue['file']} ({issue['severity']})")
    else:
        print("Usage: python integration_utils.py <codebase_path>")
