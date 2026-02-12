"""
Module Personality Profiler - Analyzes modules to classify their behavioral patterns.

This profiler identifies personality traits that indicate potential runtime issues
even when modules compile successfully.
"""

import ast
import importlib.util
import sys
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class PersonalityTone(Enum):
    """Defines how strictly a module should be validated."""
    DEFENSIVE = "defensive"  # Strict validation, fail-fast
    PERMISSIVE = "permissive"  # Lenient, fallback behaviors


class PersonalityStyle(Enum):
    """Defines how a module handles its dependencies."""
    EAGER = "eager"  # Load everything upfront
    LAZY = "lazy"  # Load on demand


class PersonalityNuance(Enum):
    """Defines how a module handles failures."""
    FAIL_FAST = "fail_fast"  # Crash immediately on error
    GRACEFUL = "graceful"  # Degrade gracefully


@dataclass
class ModulePersonality:
    """Represents the personality profile of a module."""
    name: str
    path: str
    
    # Core personality traits
    is_path_dependent: bool = False
    is_import_heavy: bool = False
    is_runtime_fragile: bool = False
    is_circular_prone: bool = False
    has_side_effects: bool = False
    is_stateful: bool = False
    
    # Fine-grained adjustments
    tone: PersonalityTone = PersonalityTone.PERMISSIVE
    style: PersonalityStyle = PersonalityStyle.EAGER
    nuance: PersonalityNuance = PersonalityNuance.GRACEFUL
    
    # Evidence collection
    hardcoded_paths: List[str] = field(default_factory=list)
    conditional_imports: List[str] = field(default_factory=list)
    missing_deps: List[str] = field(default_factory=list)
    global_state: List[str] = field(default_factory=list)
    import_count: int = 0
    line_count: int = 0
    
    # Dependency information
    imports: Set[str] = field(default_factory=set)
    imported_by: Set[str] = field(default_factory=set)
    circular_dependencies: Set[str] = field(default_factory=set)


class ModuleVisitor(ast.NodeVisitor):
    """AST visitor to extract personality traits from module code."""
    
    def __init__(self, module_path: str):
        self.module_path = module_path
        self.hardcoded_paths = []
        self.conditional_imports = []
        self.global_state = []
        self.has_side_effects = False
        self.import_count = 0
        self._conditional_depth = 0
        
    def visit_Import(self, node: ast.Import) -> None:
        self.import_count += len(node.names)
        if self._conditional_depth > 0:
            for alias in node.names:
                self.conditional_imports.append(f"import {alias.name}")
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.import_count += 1
        # Check for conditional imports
        if self._conditional_depth > 0:
            module_part = node.module or ""
            self.conditional_imports.append(
                f"from {'.' * node.level}{module_part} import [...]"
            )
        self.generic_visit(node)
        
    def visit_Call(self, node: ast.Call) -> None:
        # Check for module-level function calls (side effects)
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            func_name = f"{node.func.value.id}.{node.func.attr}"
            if func_name in ["os.makedirs", "sys.path.append", "logging.basicConfig"]:
                self.has_side_effects = True
        elif isinstance(node.func, ast.Name):
            if node.func.id in ["os", "sys", "logging"]:
                self.has_side_effects = True
                
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self._conditional_depth += 1
        self.generic_visit(node)
        self._conditional_depth -= 1

    def visit_Try(self, node: ast.Try) -> None:
        self._conditional_depth += 1
        self.generic_visit(node)
        self._conditional_depth -= 1
        
    def visit_Assign(self, node: ast.Assign) -> None:
        # Check for hardcoded paths
        if isinstance(node.value, ast.Constant):
            value = node.value.value
            if isinstance(value, str) and (value.startswith(('C:', 'D:', 'E:', '/e:', 'E:'))):
                self.hardcoded_paths.append(value)
                
        # Check for global state
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                self.global_state.append(target.id)
                
        self.generic_visit(node)


class DependencyGraph:
    """Manages the dependency graph and detects circular imports."""
    
    def __init__(self):
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)
        self.visited: Set[str] = set()
        self.recursion_stack: Set[str] = set()
        self.circular_deps: List[Tuple[str, str]] = []
        
    def add_dependency(self, module: str, dependency: str) -> None:
        """Add a dependency relationship."""
        self.graph[module].add(dependency)
        self.reverse_graph[dependency].add(module)
        self.graph.setdefault(dependency, set())
        
    def find_circular_dependencies(self) -> List[Tuple[str, str]]:
        """Detect circular dependencies using DFS."""
        self.circular_deps = []
        self.visited = set()
        self.recursion_stack = set()
        
        for module in list(self.graph.keys()):
            if module not in self.visited:
                self._dfs_circular_check(module)
                
        return self.circular_deps
        
    def _dfs_circular_check(self, module: str) -> None:
        """DFS helper for circular dependency detection."""
        self.visited.add(module)
        self.recursion_stack.add(module)
        
        for dep in self.graph.get(module, set()):
            if dep in self.recursion_stack:
                self.circular_deps.append((module, dep))
            elif dep not in self.visited:
                self._dfs_circular_check(dep)
                
        self.recursion_stack.remove(module)


class ModuleProfiler:
    """Main profiler class that analyzes modules and assigns personalities."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.dependency_graph = DependencyGraph()
        self.personalities: Dict[str, ModulePersonality] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def analyze_module(self, module_path: str) -> ModulePersonality:
        """Analyze a single module and determine its personality."""
        module_path = Path(module_path)
        
        # Skip non-Python files
        if not module_path.suffix == '.py':
            raise ValueError(f"Not a Python module: {module_path}")
            
        # Get module name from path
        module_name = self._get_module_name(module_path)
        
        # Parse the AST
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                source = f.read()
                tree = ast.parse(source)
        except SyntaxError as e:
            self.logger.error(f"Syntax error in {module_path}: {e}")
            # Create a personality for broken modules
            personality = ModulePersonality(
                name=module_name,
                path=str(module_path),
                line_count=0,
                is_runtime_fragile=True,
                tone=PersonalityTone.DEFENSIVE,
                nuance=PersonalityNuance.FAIL_FAST
            )
            return personality
            
        # Visit the AST to extract traits
        visitor = ModuleVisitor(str(module_path))
        visitor.visit(tree)
        
        # Create personality
        personality = ModulePersonality(
            name=module_name,
            path=str(module_path),
            hardcoded_paths=visitor.hardcoded_paths,
            conditional_imports=visitor.conditional_imports,
            global_state=visitor.global_state,
            imports=self._extract_imports(tree),
            has_side_effects=visitor.has_side_effects,
            is_import_heavy=visitor.import_count > 10,
            is_stateful=len(visitor.global_state) > 0,
            import_count=visitor.import_count,
            line_count=len(source.splitlines()),
        )
        
        # Determine core traits
        personality.is_path_dependent = len(personality.hardcoded_paths) > 0
        personality.is_runtime_fragile = (
            len(personality.conditional_imports) > 0 or
            personality.is_path_dependent
        )
        
        # Set fine-grained adjustments based on traits
        if personality.is_path_dependent or personality.is_runtime_fragile:
            personality.tone = PersonalityTone.DEFENSIVE
            personality.nuance = PersonalityNuance.FAIL_FAST
            
        if personality.is_import_heavy:
            personality.style = PersonalityStyle.LAZY
            
        # Store the personality
        self.personalities[module_name] = personality
        
        # Add to dependency graph
        for imp in personality.imports:
            self.dependency_graph.add_dependency(module_name, imp)
            
        return personality
        
    def analyze_package(self, package_path: str) -> Dict[str, ModulePersonality]:
        """Analyze all modules in a package."""
        package_path = Path(package_path)
        
        if not package_path.exists():
            raise FileNotFoundError(f"Package not found: {package_path}")
            
        # Find all Python files
        python_files = list(package_path.rglob('*.py'))
        
        # Analyze each module
        for py_file in python_files:
            try:
                self.analyze_module(py_file)
            except Exception as e:
                self.logger.error(f"Failed to analyze {py_file}: {e}")
                
        # Detect circular dependencies
        circular_deps = self.dependency_graph.find_circular_dependencies()
        
        # Update personalities with circular dependency info
        for module_a, module_b in circular_deps:
            if module_a in self.personalities:
                self.personalities[module_a].is_circular_prone = True
                self.personalities[module_a].circular_dependencies.add(module_b)
            if module_b in self.personalities:
                self.personalities[module_b].is_circular_prone = True
                self.personalities[module_b].circular_dependencies.add(module_a)
                
        # Update imported_by relationships
        for module, personality in self.personalities.items():
            for imp in personality.imports:
                if imp in self.personalities:
                    self.personalities[imp].imported_by.add(module)
                    
        return self.personalities
        
    def get_personality(self, module_name: str) -> Optional[ModulePersonality]:
        """Get the personality of a specific module."""
        return self.personalities.get(module_name)
        
    def get_modules_by_trait(self, trait: str) -> List[ModulePersonality]:
        """Get all modules that have a specific trait."""
        result = []
        for personality in self.personalities.values():
            if trait == "has_side_effects":
                if personality.has_side_effects:
                    result.append(personality)
                continue
            if getattr(personality, f"is_{trait}", False):
                result.append(personality)
        return result
        
    def _get_module_name(self, module_path: Path) -> str:
        """Convert file path to module name."""
        # Remove .py extension and convert path separators to dots
        relative_path = module_path.relative_to(self.root_path)
        return str(relative_path.with_suffix('')).replace('/', '.').replace('\\', '.')
        
    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """Extract all import statements from AST."""
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
                else:
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                    
        return imports
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive analysis report."""
        total_modules = len(self.personalities)
        
        trait_counts = {
            'path_dependent': 0,
            'import_heavy': 0,
            'runtime_fragile': 0,
            'circular_prone': 0,
            'has_side_effects': 0,
            'stateful': 0,
        }
        
        tone_counts = defaultdict(int)
        style_counts = defaultdict(int)
        nuance_counts = defaultdict(int)
        
        for personality in self.personalities.values():
            for trait in trait_counts:
                if trait == "has_side_effects":
                    if personality.has_side_effects:
                        trait_counts[trait] += 1
                    continue
                if getattr(personality, f"is_{trait}"):
                    trait_counts[trait] += 1
                    
            tone_counts[personality.tone.value] += 1
            style_counts[personality.style.value] += 1
            nuance_counts[personality.nuance.value] += 1
            
        return {
            'total_modules': total_modules,
            'trait_distribution': trait_counts,
            'tone_distribution': dict(tone_counts),
            'style_distribution': dict(style_counts),
            'nuance_distribution': dict(nuance_counts),
            'circular_dependencies': self.dependency_graph.circular_deps,
            'top_risky_modules': self._get_riskiest_modules(),
        }
        
    def _get_riskiest_modules(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get modules with the highest risk scores."""
        risk_scores = []
        
        for personality in self.personalities.values():
            score = 0
            reasons = []
            
            if personality.is_path_dependent:
                score += 10
                reasons.append("Hardcoded paths")
            if personality.is_runtime_fragile:
                score += 8
                reasons.append("Runtime fragile")
            if personality.is_circular_prone:
                score += 15
                reasons.append("Circular dependencies")
            if personality.is_import_heavy:
                score += 5
                reasons.append("Import heavy")
            if personality.has_side_effects:
                score += 3
                reasons.append("Side effects")
                
            risk_scores.append({
                'module': personality.name,
                'path': personality.path,
                'score': score,
                'reasons': reasons,
                'personality': personality,
            })
            
        return sorted(risk_scores, key=lambda x: x['score'], reverse=True)[:top_n]


# Convenience function for quick analysis
def analyze_module(module_path: str) -> ModulePersonality:
    """Quickly analyze a single module."""
    profiler = ModuleProfiler(Path(module_path).parent)
    return profiler.analyze_module(module_path)


def analyze_package(package_path: str) -> Dict[str, ModulePersonality]:
    """Quickly analyze an entire package."""
    profiler = ModuleProfiler(package_path)
    return profiler.analyze_package(package_path)
