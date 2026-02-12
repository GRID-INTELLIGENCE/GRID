"""
Standalone Guardrail System Demo

Demonstrates the guardrail system without external dependencies.
"""

import os
import sys
import tempfile
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Any, Set
from collections import defaultdict
import ast

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Simplified Event class for standalone demo
class Event:
    def __init__(self, event_type: str, data: Dict[str, Any], source: str = "demo"):
        self.type = event_type
        self.data = data
        self.source = source
        self.timestamp = datetime.utcnow()


# Standalone demo without full guardrail system
def create_demo_codebase(tmpdir: Path) -> Path:
    """Create a demo codebase with various issues."""
    
    # Create package structure
    pkg_dir = tmpdir / "demo_package"
    pkg_dir.mkdir()
    
    # 1. Module with hardcoded paths
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
""")
    
    # 2. Module with conditional imports
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
    HAS_TRANSFORMERS = False
    AutoModel = None

class MLProcessor:
    def __init__(self):
        self.has_torch = HAS_TORCH
        self.has_transformers = HAS_TRANSFORMERS
        
    def process_with_torch(self, data):
        if not HAS_TORCH:
            raise ImportError("PyTorch is required for this function")
        return torch.tensor(data)
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
    
    # 4. Clean module for comparison
    clean_module = pkg_dir / "clean_module.py"
    clean_module.write_text("""
# Clean module - GOOD EXAMPLE
from pathlib import Path
from typing import List, Dict
import os

class CleanModule:
    def __init__(self, config_path: Path = None):
        self.config_path = config_path or Path("config.json")
        
    def process_data(self, data: List[Dict]) -> List[Dict]:
        return [item for item in data if item.get("active")]
        
    def load_config(self) -> Dict:
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return {"default": True}
""")
    
    return pkg_dir


def analyze_module_simple(module_path: Path) -> Dict[str, Any]:
    """Simple module analysis without full profiler."""
    
    with open(module_path, 'r') as f:
        content = f.read()
        
    # Parse AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return {"error": str(e), "path": str(module_path)}
    
    # Extract basic info
    issues = {
        "hardcoded_paths": [],
        "conditional_imports": [],
        "import_count": 0,
        "has_side_effects": False,
        "line_count": len(content.splitlines())
    }
    
    # Walk AST
    for node in ast.walk(tree):
        # Count imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            issues["import_count"] += 1
            
            # Check for conditional imports
            for parent in ast.walk(node):
                if isinstance(parent, (ast.If, ast.Try)):
                    if isinstance(node, ast.ImportFrom):
                        issues["conditional_imports"].append(
                            f"from {'.' * node.level}{node.module or ''} import [...]"
                        )
                    break
        
        # Check for hardcoded paths
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and 'PATH' in target.id.upper():
                    if isinstance(node.value, ast.Constant):
                        value = node.value.value
                        if isinstance(value, str) and any(
                            value.startswith(prefix) for prefix in ['C:', 'D:', 'E:', '/e:', '/']
                        ):
                            issues["hardcoded_paths"].append(value)
        
        # Check for side effects
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ['os.makedirs', 'sys.path.append', 'logging.basicConfig']:
                    issues["has_side_effects"] = True
    
    # Determine personality traits
    traits = {
        "is_path_dependent": len(issues["hardcoded_paths"]) > 0,
        "is_runtime_fragile": len(issues["conditional_imports"]) > 0,
        "is_import_heavy": issues["import_count"] > 10,
        "has_side_effects": issues["has_side_effects"],
    }
    
    return {
        "path": str(module_path),
        "issues": issues,
        "traits": traits,
        "risk_score": sum([
            10 * len(issues["hardcoded_paths"]),
            5 * len(issues["conditional_imports"]),
            3 * issues["import_count"],
            2 if issues["has_side_effects"] else 0
        ])
    }


def demo_analysis():
    """Run the standalone demo."""
    print("\n" + "="*60)
    print("STANDALONE GUARDRAIL DEMO")
    print("="*60)
    print("\nThis demo shows how the guardrail system identifies issues")
    print("that cause modules to compile but fail at runtime.\n")
    
    # Create demo codebase
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        pkg_dir = create_demo_codebase(tmpdir)
        
        print(f"Created demo codebase with modules:")
        for py_file in pkg_dir.glob("*.py"):
            print(f"  - {py_file.name}")
        
        # Analyze each module
        print("\n" + "="*60)
        print("MODULE ANALYSIS RESULTS")
        print("="*60)
        
        results = []
        for py_file in pkg_dir.glob("*.py"):
            analysis = analyze_module_simple(py_file)
            results.append(analysis)
            
            module_name = py_file.stem
            print(f"\n{module_name}:")
            print(f"  Risk Score: {analysis['risk_score']}")
            
            if "error" in analysis:
                print(f"  ERROR: {analysis['error']}")
                continue
            
            traits = analysis["traits"]
            print(f"  Traits:")
            for trait, value in traits.items():
                status = "[X]" if value else "[ ]"
                print(f"    {status} {trait.replace('_', ' ').title()}")
            
            issues = analysis["issues"]
            if issues["hardcoded_paths"]:
                print(f"  Hardcoded Paths:")
                for path in issues["hardcoded_paths"]:
                    print(f"    - {path}")
            
            if issues["conditional_imports"]:
                print(f"  Conditional Imports: {len(issues['conditional_imports'])}")
            
            if issues["has_side_effects"]:
                print(f"  [!] Has module-level side effects")
        
        # Show summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        total_issues = sum(len(r.get("issues", {}).get("hardcoded_paths", [])) for r in results)
        total_conditional = sum(len(r.get("issues", {}).get("conditional_imports", [])) for r in results)
        
        print(f"\nTotal modules analyzed: {len(results)}")
        print(f"Modules with hardcoded paths: {sum(1 for r in results if r.get('traits', {}).get('is_path_dependent'))}")
        print(f"Modules with conditional imports: {sum(1 for r in results if r.get('traits', {}).get('is_runtime_fragile'))}")
        print(f"Total hardcoded paths found: {total_issues}")
        print(f"Total conditional imports: {total_conditional}")
        
        # Show riskiest modules
        print("\nRiskiest Modules:")
        sorted_results = sorted(results, key=lambda x: x.get('risk_score', 0), reverse=True)
        for i, result in enumerate(sorted_results[:3], 1):
            if 'error' not in result:
                module_name = Path(result['path']).stem
                print(f"  {i}. {module_name} (score: {result['risk_score']})")
        
        # Recommendations
        print("\n" + "="*60)
        print("RECOMMENDATIONS")
        print("="*60)
        
        print("\n1. For Hardcoded Paths:")
        print("   - Use environment variables (e.g., os.getenv('GRID_ROOT'))")
        print("   - Use configuration files")
        print("   - Use pathlib.Path for cross-platform compatibility")
        
        print("\n2. For Conditional Imports:")
        print("   - Document optional dependencies clearly")
        print("   - Provide meaningful error messages")
        print("   - Consider using importlib.import_module for dynamic imports")
        
        print("\n3. For Circular Imports:")
        print("   - Extract shared code to separate modules")
        print("   - Use dependency injection pattern")
        print("   - Reorganize module structure")
        
        print("\n4. General Best Practices:")
        print("   - Avoid module-level side effects")
        print("   - Keep import count reasonable")
        print("   - Use lazy loading for heavy dependencies")
        
        # Example fix
        print("\n" + "="*60)
        print("EXAMPLE FIX")
        print("="*60)
        
        print("\nBefore (problematic):")
        print('  DATA_DIR = "E:/grid/logs/xai_traces"')
        
        print("\nAfter (fixed):")
        print('  import os')
        print('  from pathlib import Path')
        print('  ')
        print('  DATA_DIR = Path(os.getenv("GRID_ROOT", "E:/grid")) / "logs" / "xai_traces"')
        
        print("\n" + "="*60)
        print("DEMO COMPLETE")
        print("="*60)
        print("\nThe full guardrail system provides:")
        print("  - Real-time violation detection")
        print("  - Event-based monitoring")
        print("  - Adaptive learning from patterns")
        print("  - CLI tools for analysis")
        print("  - Integration with the UnifiedEventBus")
        print("\nTo use the full system:")
        print("  from guardrails import setup_guardrails")
        print("  system = setup_guardrails('/path/to/code', mode='warning')")


if __name__ == "__main__":
    demo_analysis()
