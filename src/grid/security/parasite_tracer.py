"""
Parasitic Call Tracer - Systematic Detection & Tracing
========================================================

Identifies and traces parasitic function calls through their complete lifecycle:
- **Environment**: Runtime context (process, thread, contextvars, modules)
- **Source**: Immediate call site
- **Seed**: Original initiating code
- **Helpers**: All intermediate functions
- **Instances**: Runtime objects involved

Author: GRID Intelligence Framework
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import contextvars
import gc
import inspect
import os
import sys
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

# Type definitions
CallStack = list["SourceLocation"]

# Context var to track call chain across async boundaries
_call_chain: contextvars.ContextVar[CallStack] = contextvars.ContextVar("call_chain", default=[])
_is_tracing: contextvars.ContextVar[bool] = contextvars.ContextVar("is_tracing", default=False)


# ============================================================================
# Data Models
# ============================================================================


@dataclass(frozen=True)
class EnvironmentContext:
    """Complete runtime environment snapshot."""

    python_version: str
    process_id: int
    thread_id: int
    asyncio_task: str | None
    contextvars_snapshot: dict[str, str]
    environment_vars: dict[str, str]
    working_directory: str
    imported_modules: list[str]
    memory_usage_mb: float


@dataclass(frozen=True)
class SourceLocation:
    """Precise location in source code."""

    module: str
    function: str
    qualified_name: str  # Full dotted path
    line: int
    file: Path
    code_context: list[str]  # 5 lines before + line + 5 after
    local_variables: dict[str, str]  # name -> repr(value)


@dataclass(frozen=True)
class SeedLocation:
    """Original code that started the parasitic chain."""

    module: str
    function: str
    line: int
    file: Path
    reason: str  # Why identified as seed
    import_chain: list[str]  # How it entered the system
    is_external: bool  # From third-party lib?


@dataclass(frozen=True)
class HelperLocation:
    """Intermediate function in call chain."""

    module: str
    function: str
    qualified_name: str
    line: int
    depth: int  # Distance from seed
    is_decorator: bool
    is_property: bool
    is_async: bool
    is_classmethod: bool
    is_staticmethod: bool


@dataclass(frozen=True)
class InstanceInfo:
    """Runtime object instance metadata."""

    type_name: str
    type_module: str
    object_id: int  # id(obj)
    attributes: dict[str, str]  # name -> repr(value)
    reference_count: int
    size_bytes: int
    is_singleton: bool


@dataclass(frozen=True)
class CallGraph:
    """Dependency graph of the call chain."""

    nodes: list[str]  # Function names
    edges: list[tuple[str, str]]  # (caller, callee)
    depths: dict[str, int]  # node -> depth from seed
    cycles: list[list[str]]  # Detected cycles


@dataclass
class ParasiteTrace:
    """Complete trace of a parasitic call."""

    # Identification
    id: uuid.UUID
    timestamp: datetime
    detection_rule: str

    # Core components
    environment: EnvironmentContext
    source: SourceLocation
    seed: SeedLocation
    helpers: list[HelperLocation]
    instances: list[InstanceInfo]
    call_graph: CallGraph

    # Metadata
    is_async: bool
    total_depth: int
    has_cycles: bool

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for logging."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "detection_rule": self.detection_rule,
            "seed": {
                "module": self.seed.module,
                "function": self.seed.function,
                "file": str(self.seed.file),
                "line": self.seed.line,
                "reason": self.seed.reason,
            },
            "source": {
                "module": self.source.module,
                "function": self.source.function,
                "file": str(self.source.file),
                "line": self.source.line,
            },
            "helpers_count": len(self.helpers),
            "instances_count": len(self.instances),
            "total_depth": self.total_depth,
            "has_cycles": self.has_cycles,
            "is_async": self.is_async,
        }


# ============================================================================
# Core Tracer Implementation
# ============================================================================


class ParasiteCallTracer:
    """
    Systematically traces function calls to identify parasitic patterns.

    Usage:
        tracer = ParasiteCallTracer()
        tracer.start()
        # ... code that might contain parasites ...
        trace = tracer.extract_trace("my_detection_rule")
        tracer.stop()
    """

    def __init__(self) -> None:
        self.active = False
        self._original_trace: Callable[[Any, str, Any], Any] | None = None
        self._call_depths: dict[str, int] = defaultdict(int)
        self._seen_functions: set[str] = set()

    def start(self) -> None:
        """Begin tracing all function calls."""
        if self.active:
            return

        _is_tracing.set(True)
        self._original_trace = sys.gettrace()
        sys.settrace(self._trace_calls)
        self.active = True

    def stop(self) -> None:
        """Stop tracing."""
        if not self.active:
            return

        sys.settrace(self._original_trace)
        _is_tracing.set(False)
        self.active = False

    def _trace_calls(self, frame: Any, event: str, arg: Any) -> Callable[[Any, str, Any], Any] | None:
        """Callback invoked by sys.settrace for every function call."""
        if event == "call":
            loc = self._extract_location(frame)
            if loc:
                chain = _call_chain.get([])
                chain.append(loc)
                _call_chain.set(chain)

                # Track depth
                qual_name = loc.qualified_name
                self._call_depths[qual_name] += 1
                self._seen_functions.add(qual_name)

        elif event == "return":
            chain = _call_chain.get([])
            if chain:
                loc = chain.pop()
                _call_chain.set(chain)

                # Decrement depth
                self._call_depths[loc.qualified_name] = max(0, self._call_depths[loc.qualified_name] - 1)

        return self._trace_calls

    def _extract_location(self, frame: Any) -> SourceLocation | None:
        """Extract source location from a stack frame."""
        try:
            code = frame.f_code
            module = frame.f_globals.get("__name__", "<unknown>")
            function = code.co_name
            line = frame.f_lineno
            file_path = Path(code.co_filename)

            # Skip stdlib and site-packages (focus on user code)
            if self._is_stdlib_or_external(file_path):
                return None

            # Get code context
            try:
                source_lines, start_line = inspect.getsourcelines(frame)
                context_start = max(0, line - start_line - 5)
                context_end = min(len(source_lines), line - start_line + 6)
                code_context = source_lines[context_start:context_end]
            except (OSError, TypeError):
                code_context = []

            # Get local variables (sanitized)
            local_vars = {
                k: repr(v)[:100]  # Truncate to 100 chars
                for k, v in frame.f_locals.items()
                if not k.startswith("_") and not inspect.ismodule(v)
            }

            # Build qualified name
            qual_name = f"{module}.{function}"
            if "self" in frame.f_locals:
                obj = frame.f_locals["self"]
                qual_name = f"{obj.__class__.__module__}.{obj.__class__.__name__}.{function}"

            return SourceLocation(
                module=module,
                function=function,
                qualified_name=qual_name,
                line=line,
                file=file_path,
                code_context=code_context,
                local_variables=local_vars,
            )

        except Exception:
            return None

    def _is_stdlib_or_external(self, file_path: Path) -> bool:
        """Check if file is from stdlib or site-packages."""
        path_str = str(file_path).lower()
        return any(
            marker in path_str for marker in ["site-packages", "dist-packages", "lib/python", "stdlib", "<frozen"]
        )

    def extract_trace(self, detection_rule: str) -> ParasiteTrace:
        """Build complete ParasiteTrace from current call chain."""
        chain = _call_chain.get([])

        if not chain:
            raise ValueError("No active call chain to trace")

        # Identify seed (first application code)
        seed = self._identify_seed(chain)

        # Identify helpers (everything between seed and source)
        helpers = self._identify_helpers(chain, seed)

        # Capture environment
        environment = self._capture_environment()

        # Capture instances
        instances = self._capture_instances(chain)

        # Build call graph
        call_graph = self._build_call_graph(chain)

        # Determine if async
        is_async = any(
            asyncio.iscoroutinefunction(getattr(sys.modules.get(loc.module), loc.function, None)) for loc in chain
        )

        return ParasiteTrace(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            detection_rule=detection_rule,
            environment=environment,
            source=chain[-1],
            seed=seed,
            helpers=helpers,
            instances=instances,
            call_graph=call_graph,
            is_async=is_async,
            total_depth=len(chain),
            has_cycles=len(call_graph.cycles) > 0,
        )

    def _identify_seed(self, chain: CallStack) -> SeedLocation:
        """Identify the original initiating function."""
        # Seed = first call that's not stdlib/site-packages
        for idx, loc in enumerate(chain):
            # Check if this looks like an entry point
            if any(indicator in loc.function.lower() for indicator in ["main", "run", "execute", "start", "handle"]):
                return SeedLocation(
                    module=loc.module,
                    function=loc.function,
                    line=loc.line,
                    file=loc.file,
                    reason=f"Entry point function: {loc.function}",
                    import_chain=self._build_import_chain(loc.module),
                    is_external=False,
                )

        # Fallback: first in chain
        first = chain[0]
        return SeedLocation(
            module=first.module,
            function=first.function,
            line=first.line,
            file=first.file,
            reason="First call in chain",
            import_chain=self._build_import_chain(first.module),
            is_external=False,
        )

    def _build_import_chain(self, module_name: str) -> list[str]:
        """Build the import chain for a module."""
        chain: list[str] = []
        current = module_name

        while current:
            chain.append(current)
            if "." in current:
                current = current.rsplit(".", 1)[0]
            else:
                break

        return list(reversed(chain))

    def _identify_helpers(self, chain: CallStack, seed: SeedLocation) -> list[HelperLocation]:
        """Extract all helper functions between seed and source."""
        helpers: list[HelperLocation] = []

        # Find seed index
        seed_idx = next(
            (i for i, loc in enumerate(chain) if loc.module == seed.module and loc.function == seed.function), 0
        )

        for idx in range(seed_idx + 1, len(chain)):
            loc = chain[idx]

            # Check if it's a decorator/property/etc
            is_decorator = self._is_decorator(loc)
            is_property = loc.function in ("__get__", "__set__", "__delete__") or "@property" in "".join(
                loc.code_context
            )
            is_async = asyncio.iscoroutinefunction(getattr(sys.modules.get(loc.module), loc.function, None))

            helpers.append(
                HelperLocation(
                    module=loc.module,
                    function=loc.function,
                    qualified_name=loc.qualified_name,
                    line=loc.line,
                    depth=idx - seed_idx,
                    is_decorator=is_decorator,
                    is_property=is_property,
                    is_async=is_async,
                    is_classmethod="@classmethod" in "".join(loc.code_context),
                    is_staticmethod="@staticmethod" in "".join(loc.code_context),
                )
            )

        return helpers

    def _is_decorator(self, loc: SourceLocation) -> bool:
        """Check if location represents a decorator."""
        # Look for @ symbol in code context
        return any(line.strip().startswith("@") for line in loc.code_context)

    def _capture_environment(self) -> EnvironmentContext:
        """Capture complete runtime environment."""
        import psutil

        process = psutil.Process()

        # Get current asyncio task if in async context
        task_name: str | None = None
        try:
            task = asyncio.current_task()
            if task:
                task_name = task.get_name()
        except RuntimeError:
            pass

        # Capture contextvars (sanitized)
        ctx_snapshot: dict[str, str] = {}
        for var in contextvars.copy_context():
            try:
                ctx_snapshot[str(var)] = repr(var.get())[:100]
            except LookupError:
                continue

        # Environment variables (sanitized - no secrets)
        safe_env_vars = {
            k: v
            for k, v in os.environ.items()
            if not any(secret in k.upper() for secret in ["SECRET", "KEY", "PASSWORD", "TOKEN"])
        }

        return EnvironmentContext(
            python_version=sys.version,
            process_id=os.getpid(),
            thread_id=threading.get_ident(),
            asyncio_task=task_name,
            contextvars_snapshot=ctx_snapshot,
            environment_vars=safe_env_vars,
            working_directory=os.getcwd(),
            imported_modules=list(sys.modules.keys())[:100],  # Limit to 100
            memory_usage_mb=process.memory_info().rss / 1024 / 1024,
        )

    def _capture_instances(self, chain: CallStack) -> list[InstanceInfo]:
        """Capture runtime object instances from the call chain."""
        instances: list[InstanceInfo] = []
        seen_ids: set[int] = set()

        # Walk all objects in local vars of each frame
        for loc in chain:
            for var_name, var_repr in loc.local_variables.items():
                # Try to find the actual object (limited scan)
                for obj in gc.get_objects():
                    obj_id = id(obj)
                    if obj_id in seen_ids:
                        continue

                    # Check if this object matches the repr (heuristic)
                    if repr(obj)[:100] == var_repr:
                        seen_ids.add(obj_id)

                        # Extract metadata
                        type_obj = type(obj)
                        attrs = dict(list({
                            k: repr(getattr(obj, k, None))[:100]
                            for k in dir(obj)
                            if not k.startswith("_") and not callable(getattr(obj, k, None))
                        }.items())[:10])  # Limit to 10 attributes

                        # Check if singleton
                        is_singleton = sum(1 for o in gc.get_objects() if type(o) == type_obj) == 1

                        instances.append(
                            InstanceInfo(
                                type_name=type_obj.__name__,
                                type_module=type_obj.__module__,
                                object_id=obj_id,
                                attributes=attrs,
                                reference_count=sys.getrefcount(obj),
                                size_bytes=sys.getsizeof(obj),
                                is_singleton=is_singleton,
                            )
                        )

                        if len(instances) >= 50:  # Limit total instances
                            return instances

        return instances

    def _build_call_graph(self, chain: CallStack) -> CallGraph:
        """Build dependency graph from call chain."""
        nodes: list[str] = []
        edges: list[tuple[str, str]] = []
        depths: dict[str, int] = {}

        for idx, loc in enumerate(chain):
            qual_name = loc.qualified_name
            if qual_name not in nodes:
                nodes.append(qual_name)

            depths[qual_name] = idx

            # Add edge from previous call
            if idx > 0:
                prev_name = chain[idx - 1].qualified_name
                edges.append((prev_name, qual_name))

        # Detect cycles
        cycles = self._detect_cycles(nodes, edges)

        return CallGraph(nodes=nodes, edges=edges, depths=depths, cycles=cycles)

    def _detect_cycles(self, nodes: list[str], edges: list[tuple[str, str]]) -> list[list[str]]:
        """Detect cycles in the call graph using DFS."""
        # Build adjacency list
        graph: dict[str, list[str]] = defaultdict(list)
        for src, dst in edges:
            graph[src].append(dst)

        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str, path: list[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    dfs(neighbor, path[:])
                elif neighbor in rec_stack:
                    # Cycle detected
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])

            rec_stack.remove(node)

        for node in nodes:
            if node not in visited:
                dfs(node, [])

        return cycles


# ============================================================================
# Convenience Functions
# ============================================================================


def trace_function(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to automatically trace a function for parasitic behavior."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        tracer = ParasiteCallTracer()
        tracer.start()

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            tracer.stop()

    return wrapper


async def trace_async_function(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to trace async functions."""

    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        tracer = ParasiteCallTracer()
        tracer.start()

        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            tracer.stop()

    return wrapper


# Missing import
import threading
