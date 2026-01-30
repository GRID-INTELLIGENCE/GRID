"""Enhanced skill extraction with comprehensive metadata.

Features:
- AST-based complexity calculation
- Tag inference from imports and keywords
- Schema extraction from type hints
- Performance profile inference
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ExtendedSkillMetadata:
    """Comprehensive skill metadata."""

    id: str
    name: str
    description: str
    version: str
    category: str
    subcategory: str
    tags: list[str]
    input_schema: dict[str, Any] | None
    output_schema: dict[str, Any] | None
    dependencies: list[str]
    handler: Callable
    file_path: str
    line_number: int
    author: str = "GRID"
    complexity_score: int = 0
    performance_profile: str = "unknown"  # "fast", "moderate", "slow"
    source_hash: str = ""


class SkillExtractionEngine:
    """Enhanced extraction engine with comprehensive metadata.

    Caches AST parsing results to avoid repeated file reads.
    """

    _CACHE_TTL = 300  # 5 minutes

    # Tag keywords mapping
    TAG_KEYWORDS = {
        "llm": ["ollama", "openai", "llm", "model", "generate", "completion"],
        "vector": ["vector", "embedding", "chroma", "faiss", "dense"],
        "git": ["git", "repository", "branch", "commit"],
        "nlp": ["entity", "sentiment", "topic", "token", "ner", "nlp"],
        "rag": ["rag", "retrieval", "knowledge", "context"],
        "async": ["async", "await", "asyncio"],
        "streaming": ["stream", "chunk", "yield"],
        "analysis": ["analyze", "detect", "pattern", "insight"],
        "transform": ["transform", "map", "convert", "schema"],
    }

    def __init__(self):
        self._ast_cache: dict[str, tuple[ast.AST, str, float]] = {}

    def extract_skill_metadata(self, skill_file: Path) -> ExtendedSkillMetadata:
        """Extract comprehensive metadata from a skill file.

        Args:
            skill_file: Path to the skill Python file

        Returns:
            ExtendedSkillMetadata with all extracted information

        Raises:
            ValueError: If no skill class found in file
        """
        import importlib.util

        # Read and cache source
        source, source_hash = self._read_source(skill_file)
        tree = self._get_ast(skill_file, source)

        # Load module to get skill instance
        spec = importlib.util.spec_from_file_location(f"skill_{skill_file.stem}", skill_file)
        if not spec or not spec.loader:
            raise ValueError(f"Could not load spec for {skill_file}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find skill class
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and hasattr(obj, "id") and hasattr(obj, "run"):
                try:
                    skill_instance = obj()

                    # Calculate complexity
                    complexity = self._calculate_complexity(tree)

                    # Extract schemas
                    input_schema = self._extract_input_schema(obj)
                    output_schema = self._extract_output_schema(obj)

                    # Determine category and tags
                    category = self._determine_category(source)
                    tags = self._extract_tags(source, category)
                    subcategory = self._determine_subcategory(tags)

                    # Extract dependencies
                    dependencies = self._extract_module_dependencies(tree)

                    # Infer performance profile
                    performance_profile = self._infer_performance_profile(complexity, tags, source)

                    return ExtendedSkillMetadata(
                        id=skill_instance.id,
                        name=getattr(skill_instance, "name", skill_instance.id),
                        description=getattr(skill_instance, "description", ""),
                        version=getattr(skill_instance, "version", "1.0.0"),
                        category=category,
                        subcategory=subcategory,
                        tags=tags,
                        input_schema=input_schema,
                        output_schema=output_schema,
                        dependencies=dependencies,
                        handler=skill_instance.run,
                        file_path=str(skill_file),
                        line_number=inspect.getsourcelines(obj)[1],
                        complexity_score=complexity,
                        performance_profile=performance_profile,
                        source_hash=source_hash,
                    )
                except Exception as e:
                    logger.debug(f"Failed to extract from {name}: {e}")
                    continue

        raise ValueError(f"No valid skill class found in {skill_file}")

    def _read_source(self, skill_file: Path) -> tuple[str, str]:
        """Read source and compute hash."""
        with open(skill_file, encoding="utf-8") as f:
            source = f.read()
        source_hash = hashlib.md5(source.encode()).hexdigest()[:12]
        return source, source_hash

    def _get_ast(self, skill_file: Path, source: str) -> ast.AST:
        """Get AST with caching."""
        now = time.time()
        cache_key = str(skill_file)

        if cache_key in self._ast_cache:
            cached_tree, cached_hash, cached_at = self._ast_cache[cache_key]
            current_hash = hashlib.md5(source.encode()).hexdigest()[:12]

            if cached_hash == current_hash and now - cached_at < self._CACHE_TTL:
                return cached_tree

        tree = ast.parse(source)
        source_hash = hashlib.md5(source.encode()).hexdigest()[:12]
        self._ast_cache[cache_key] = (tree, source_hash, now)

        return tree

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.comprehension):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers)

        return complexity

    def _extract_input_schema(self, skill_class: type) -> dict[str, Any] | None:
        """Extract input schema from run() method type hints."""
        try:
            run_method = getattr(skill_class, "run", None)
            if not run_method:
                return None

            import typing

            hints = typing.get_type_hints(run_method)

            if not hints:
                return None

            schema = {"type": "object", "properties": {}}
            for param_name, param_type in hints.items():
                if param_name == "return":
                    continue

                type_name = getattr(param_type, "__name__", str(param_type))
                schema["properties"][param_name] = {"type": type_name}

            return schema if schema["properties"] else None

        except Exception:
            return None

    def _extract_output_schema(self, skill_class: type) -> dict[str, Any] | None:
        """Extract output schema from run() return type hint."""
        try:
            run_method = getattr(skill_class, "run", None)
            if not run_method:
                return None

            import typing

            hints = typing.get_type_hints(run_method)

            if "return" in hints:
                return_type = hints["return"]
                type_name = getattr(return_type, "__name__", str(return_type))
                return {"type": type_name}

            return None

        except Exception:
            return None

    def _determine_category(self, source: str) -> str:
        """Determine skill category from source analysis."""
        source_lower = source.lower()

        if "rag" in source_lower or "query" in source_lower or "retriev" in source_lower:
            return "query"
        elif "transform" in source_lower or "schema" in source_lower or "map" in source_lower:
            return "transformation"
        elif "analyz" in source_lower or "detect" in source_lower or "pattern" in source_lower:
            return "analysis"
        elif "capture" in source_lower or "save" in source_lower or "store" in source_lower:
            return "capture"
        elif "git" in source_lower or "repository" in source_lower:
            return "devops"
        elif "compress" in source_lower or "articulate" in source_lower:
            return "compression"
        else:
            return "misc"

    def _determine_subcategory(self, tags: list[str]) -> str:
        """Determine subcategory from tags."""
        if "llm" in tags:
            return "ai"
        elif "vector" in tags or "rag" in tags:
            return "retrieval"
        elif "git" in tags:
            return "vcs"
        elif "nlp" in tags:
            return "nlp"
        elif "async" in tags:
            return "async"
        else:
            return "generic"

    def _extract_tags(self, source: str, category: str) -> list[str]:
        """Extract tags from source code analysis."""
        tags = set()
        source_lower = source.lower()

        for tag, keywords in self.TAG_KEYWORDS.items():
            if any(kw in source_lower for kw in keywords):
                tags.add(tag)

        # Add category as tag
        tags.add(category)

        return sorted(tags)

    def _extract_module_dependencies(self, tree: ast.AST) -> list[str]:
        """Extract external module dependencies from AST."""
        deps = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root not in ("grid", "typing", "dataclasses", "enum", "abc"):
                        deps.add(root)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]
                    if root not in ("grid", "typing", "dataclasses", "enum", "abc"):
                        deps.add(root)

        return sorted(deps)

    def _infer_performance_profile(self, complexity: int, tags: list[str], source: str) -> str:
        """Infer performance profile from complexity and tags."""
        # LLM calls are inherently slow
        if "llm" in tags:
            return "slow"

        # Check for network calls
        if any(kw in source.lower() for kw in ["httpx", "requests", "aiohttp", "urllib"]):
            return "moderate"

        # Async operations tend to be faster
        if "async" in tags and complexity < 15:
            return "fast"

        # Complexity-based inference
        if complexity < 10:
            return "fast"
        elif complexity < 25:
            return "moderate"
        else:
            return "slow"

    def clear_cache(self) -> None:
        """Clear AST cache."""
        self._ast_cache.clear()
        logger.debug("Extraction engine cache cleared")
