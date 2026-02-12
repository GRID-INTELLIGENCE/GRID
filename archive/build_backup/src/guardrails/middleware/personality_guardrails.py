"""
Personality-Aware Guardrail Middleware

Enforces dynamic boundaries based on module personalities to prevent
runtime failures even when modules compile successfully.
"""

import sys
import importlib.util
import importlib.machinery
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Callable
import logging
from functools import wraps
from collections import defaultdict
import warnings

from ..profiler.module_profiler import (
    ModulePersonality,
    PersonalityTone,
    PersonalityStyle,
    PersonalityNuance,
    ModuleProfiler,
)

logger = logging.getLogger(__name__)


class GuardrailViolation(Exception):
    """Raised when a guardrail violation is detected."""
    
    def __init__(self, message: str, module: str, violation_type: str, severity: str = "warning"):
        super().__init__(message)
        self.module = module
        self.violation_type = violation_type
        self.severity = severity


class PathValidator:
    """Validates and normalizes hardcoded paths in modules."""
    
    def __init__(self, allowed_roots: List[str] = None):
        self.allowed_roots = allowed_roots or []
        self.env_mappings = {
            'E:/grid': 'GRID_ROOT',
            'e:/grid': 'GRID_ROOT',
            'C:/Users': 'USER_ROOT',
            'D:/Build': 'BUILD_ROOT',
        }
        
    def validate_path(self, path: str, module: str) -> Optional[str]:
        """Validate a path and suggest environment variable replacement."""
        # Check if path is hardcoded
        for hardcoded, env_var in self.env_mappings.items():
            if path.startswith(hardcoded):
                suggested = path.replace(hardcoded, f"${{{env_var}}}")
                return suggested
                
        # Check against allowed roots
        for root in self.allowed_roots:
            if path.startswith(root):
                return None  # Path is valid
                
        return path  # Invalid path


class DependencyValidator:
    """Validates module dependencies before runtime."""
    
    def __init__(self):
        self.missing_cache: Dict[str, Set[str]] = {}
        
    def check_import(self, module_name: str) -> Optional[str]:
        """Check if a module can be imported."""
        if module_name in self.missing_cache:
            return module_name if self.missing_cache[module_name] else None
            
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                self.missing_cache[module_name] = {module_name}
                return module_name
            self.missing_cache[module_name] = set()
            return None
        except (ImportError, ValueError):
            self.missing_cache[module_name] = {module_name}
            return module_name
            
    def check_conditional_imports(self, personality: ModulePersonality) -> List[str]:
        """Check conditional imports in a module."""
        missing = []
        for import_stmt in personality.conditional_imports:
            # Extract module name from import statement
            parts = import_stmt.split()
            if len(parts) >= 2 and parts[0] == "import":
                module_name = parts[1].split('.')[0]
                if self.check_import(module_name):
                    missing.append(module_name)
            elif len(parts) >= 4 and parts[0] == "from":
                module_name = parts[1].split('.')[0]
                if self.check_import(module_name):
                    missing.append(module_name)
        return missing


class PersonalityGuardrail:
    """Individual guardrail for a specific module personality."""
    
    def __init__(self, personality: ModulePersonality):
        self.personality = personality
        self.path_validator = PathValidator()
        self.dependency_validator = DependencyValidator()
        self.violations: List[GuardrailViolation] = []
        
    def validate_before_import(self) -> List[GuardrailViolation]:
        """Validate module before it's imported."""
        violations = []
        
        # Check hardcoded paths
        if self.personality.is_path_dependent:
            for path in self.personality.hardcoded_paths:
                suggested = self.path_validator.validate_path(path, self.personality.name)
                if suggested:
                    violations.append(GuardrailViolation(
                        f"Hardcoded path detected: {path}. Consider using: {suggested}",
                        self.personality.name,
                        "hardcoded_path",
                        "warning" if self.personality.tone == PersonalityTone.PERMISSIVE else "error"
                    ))
                    
        # Check runtime dependencies
        if self.personality.is_runtime_fragile:
            missing = self.dependency_validator.check_conditional_imports(self.personality)
            for dep in missing:
                violations.append(GuardrailViolation(
                    f"Missing runtime dependency: {dep}",
                    self.personality.name,
                    "missing_dependency",
                    "error" if self.personality.nuance == PersonalityNuance.FAIL_FAST else "warning"
                ))
                
        # Check circular dependencies
        if self.personality.is_circular_prone:
            for circular in self.personality.circular_dependencies:
                violations.append(GuardrailViolation(
                    f"Circular import detected with: {circular}",
                    self.personality.name,
                    "circular_import",
                    "warning"
                ))
                
        self.violations.extend(violations)
        return violations
        
    def suggest_refactoring(self) -> List[str]:
        """Suggest refactoring based on personality traits."""
        suggestions = []
        
        if self.personality.is_path_dependent:
            suggestions.append(
                "Replace hardcoded paths with environment variables or "
                "configuration files. Use pathlib.Path for cross-platform compatibility."
            )
            
        if self.personality.is_import_heavy:
            suggestions.append(
                "Consider lazy loading imports or splitting into smaller modules. "
                "Use importlib.import_module for dynamic imports."
            )
            
        if self.personality.is_runtime_fragile:
            suggestions.append(
                "Add proper try/except blocks around imports. "
                "Provide meaningful error messages for missing dependencies."
            )
            
        if self.personality.is_circular_prone:
            suggestions.append(
                "Refactor to remove circular dependencies. Consider using "
                "dependency injection or moving shared code to a separate module."
            )
            
        if self.personality.has_side_effects:
            suggestions.append(
                "Move side-effect code out of module level. "
                "Use functions or classes to control when effects occur."
            )
            
        return suggestions


class GuardrailMiddleware:
    """Main middleware that enforces guardrails across the codebase."""
    
    def __init__(self, mode: str = "observer"):
        """
        Initialize the guardrail middleware.
        
        Args:
            mode: "observer" (log only), "warning" (show warnings), 
                  "enforcement" (block violations), "adaptive" (self-adjusting)
        """
        self.mode = mode
        self.profiler = ModuleProfiler("")
        self.guardrails: Dict[str, PersonalityGuardrail] = {}
        self.violation_handlers: List[Callable] = []
        self.whitelist: Set[str] = set()
        self.stats = {
            'modules_checked': 0,
            'violations_detected': 0,
            'violations_blocked': 0,
        }
        
        # Register default violation handler
        self.register_violation_handler(self._default_violation_handler)
        
    def analyze_and_register(self, package_path: str) -> None:
        """Analyze a package and register guardrails for all modules."""
        self.profiler.root_path = Path(package_path)
        personalities = self.profiler.analyze_package(package_path)
        
        for name, personality in personalities.items():
            self.guardrails[name] = PersonalityGuardrail(personality)
            
        logger.info(f"Registered {len(personalities)} guardrails for {package_path}")
        
    def register_violation_handler(self, handler: Callable) -> None:
        """Register a custom violation handler."""
        self.violation_handlers.append(handler)
        
    def add_to_whitelist(self, module_name: str) -> None:
        """Add a module to the whitelist (bypasses all checks)."""
        self.whitelist.add(module_name)
        
    def check_module(self, module_name: str) -> List[GuardrailViolation]:
        """Check a module for violations."""
        if module_name in self.whitelist:
            return []
            
        guardrail = self.guardrails.get(module_name)
        if not guardrail:
            # Analyze on-the-fly if not already registered
            try:
                personality = self.profiler.analyze_module(module_name)
                guardrail = PersonalityGuardrail(personality)
                self.guardrails[module_name] = guardrail
            except Exception as e:
                logger.warning(f"Failed to analyze {module_name}: {e}")
                return []
                
        violations = guardrail.validate_before_import()
        self.stats['modules_checked'] += 1
        self.stats['violations_detected'] += len(violations)
        
        # Handle violations based on mode
        for violation in violations:
            for handler in self.violation_handlers:
                handler(violation)
                
            if self.mode == "enforcement" and violation.severity == "error":
                self.stats['violations_blocked'] += 1
                raise violation
                
            elif self.mode == "warning":
                if violation.severity == "error":
                    logger.error(str(violation))
                else:
                    logger.warning(str(violation))
                    
        return violations
        
    def get_guardrail(self, module_name: str) -> Optional[PersonalityGuardrail]:
        """Get the guardrail for a specific module."""
        return self.guardrails.get(module_name)
        
    def get_violations_summary(self) -> Dict[str, Any]:
        """Get a summary of all violations."""
        all_violations = []
        violation_types = defaultdict(int)
        
        for guardrail in self.guardrails.values():
            all_violations.extend(guardrail.violations)
            for violation in guardrail.violations:
                violation_types[violation.violation_type] += 1
                
        return {
            'stats': self.stats,
            'violation_types': dict(violation_types),
            'total_violations': len(all_violations),
            'modules_with_violations': len(set(v.module for v in all_violations)),
        }
        
    def _default_violation_handler(self, violation: GuardrailViolation) -> None:
        """Default violation handler that logs the violation."""
        if self.mode == "observer":
            logger.debug(f"[{violation.severity.upper()}] {violation.module}: {violation}")
            
    def install_import_hook(self) -> None:
        """Install a custom import hook to check modules before import."""
        import builtins
        # Store original import
        self._original_import = builtins.__import__
        middleware = self

        @wraps(self._original_import)
        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            # Check module before import
            try:
                middleware.check_module(name)
            except Exception:
                pass  # Never block importing; violations are recorded
            # Perform actual import
            return middleware._original_import(name, globals, locals, fromlist, level)

        # Replace built-in import
        builtins.__import__ = guarded_import
        self._import_hook_installed = True
        logger.info("Installed guardrail import hook")

    def uninstall_import_hook(self) -> None:
        """Uninstall the custom import hook."""
        import builtins
        if hasattr(self, '_original_import') and self._original_import is not None:
            builtins.__import__ = self._original_import
            self._original_import = None
        self._import_hook_installed = False
        logger.info("Uninstalled guardrail import hook")

    def _has_import_hook(self) -> bool:
        """Check whether a guardrail import hook is currently installed."""
        return getattr(self, '_import_hook_installed', False)


# Global middleware instance
_middleware: Optional[GuardrailMiddleware] = None


def get_middleware() -> GuardrailMiddleware:
    """Get the global guardrail middleware instance."""
    global _middleware
    if _middleware is None:
        _middleware = GuardrailMiddleware()
    return _middleware


def initialize_guardrails(package_path: str, mode: str = "observer") -> GuardrailMiddleware:
    """Initialize guardrails for a package."""
    middleware = get_middleware()
    middleware.mode = mode
    middleware.analyze_and_register(package_path)
    
    # Install import hook if not in observer mode
    if mode != "observer":
        middleware.install_import_hook()
        
    return middleware


# Decorator for protecting functions
def guardrail_check(module_name: str = None):
    """Decorator to check guardrails before function execution."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            middleware = get_middleware()
            check_module = module_name or func.__module__
            middleware.check_module(check_module)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Context manager for temporary guardrail enforcement
class GuardrailContext:
    """Context manager for temporary guardrail enforcement."""
    
    def __init__(self, mode: str = "enforcement"):
        self.mode = mode
        self.original_mode = None
        self.middleware = get_middleware()
        
    def __enter__(self):
        self.original_mode = self.middleware.mode
        self.middleware.mode = self.mode
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.middleware.mode = self.original_mode
