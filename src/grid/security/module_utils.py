"""
Safe module management utilities with isolation and cleanup.

Provides context managers and utilities for safely importing, reloading,
and managing Python modules with proper isolation and cleanup.
"""

import importlib
import importlib.util
import sys
import types
from contextlib import contextmanager
from typing import Iterator, TypeVar

T = TypeVar("T")


class ModuleIsolationError(Exception):
    """Raised when module isolation fails."""


@contextmanager
def isolate_module(module_name: str) -> Iterator[None]:
    """
    Context manager that isolates module imports and ensures cleanup.

    Args:
        module_name: Name of the module to isolate

    Yields:
        None

    Raises:
        ModuleIsolationError: If isolation setup fails
        ImportError: If the module cannot be imported
    """
    # Store original module state
    original_module = sys.modules.get(module_name)
    original_attrs = {}

    try:
        # Create a new module with a clean state
        if module_name in sys.modules:
            # Save original attributes
            if original_module is not None:
                for name, attr in vars(original_module).items():
                    if not name.startswith("__"):
                        original_attrs[name] = attr

            # Remove from sys.modules to force re-import
            del sys.modules[module_name]

        # Import the module fresh
        module = importlib.import_module(module_name)

        # Create a clean module copy
        clean_module = types.ModuleType(module_name)
        clean_module.__file__ = module.__file__
        clean_module.__package__ = module.__package__
        clean_module.__name__ = module.__name__

        # Copy only non-dunder attributes
        for name, attr in vars(module).items():
            if not name.startswith("__"):
                setattr(clean_module, name, attr)

        # Replace in sys.modules
        sys.modules[module_name] = clean_module

        yield

    except ImportError as e:
        raise ModuleIsolationError(f"Failed to isolate module {module_name}: {e}")
    finally:
        # Cleanup
        if module_name in sys.modules:
            del sys.modules[module_name]
        if original_module is not None:
            sys.modules[module_name] = original_module


def safe_reload(module_name: str) -> types.ModuleType:
    """
    Safely reload a module with isolation.

    Args:
        module_name: Name of the module to reload

    Returns:
        The reloaded module

    Raises:
        ModuleIsolationError: If reload fails
    """
    with isolate_module(module_name):
        module = importlib.import_module(module_name)
        return importlib.reload(module)


def get_module_dependencies(module_name: str) -> set[str]:
    """
    Get all direct dependencies of a module.

    Args:
        module_name: Name of the module to analyze

    Returns:
        Set of dependency module names
    """
    module = sys.modules.get(module_name)
    if not module:
        return set()

    dependencies = set()
    for attr in dir(module):
        try:
            value = getattr(module, attr)
            if hasattr(value, "__module__") and value.__module__ != module_name:
                dependencies.add(value.__module__)
        except (AttributeError, ImportError):
            continue

    return dependencies


def cleanup_module(module_name: str) -> None:
    """
    Clean up a module and its dependencies.

    Args:
        module_name: Name of the module to clean up
    """
    if module_name in sys.modules:
        # Clear module attributes
        module = sys.modules[module_name]
        for name in list(vars(module).keys()):
            if not name.startswith("__"):
                delattr(module, name)

        # Clear from sys.modules
        del sys.modules[module_name]
