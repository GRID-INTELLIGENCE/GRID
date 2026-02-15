#!/usr/bin/env python3
"""
Read-only static analysis tool for code repositories.
Performs architecture analysis, dependency mapping, and component identification
without executing any repository code.
"""

import ast
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

# Constants
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_RECURSION_DEPTH = 6
DEFAULT_EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "build",
    "dist",
    "vendor",
    ".cache",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "target",
    "bin",
    "obj",
    ".idea",
    ".vscode",
}
SENSITIVE_PATTERNS = [
    r"\.env$",
    r"secrets\.",
    r"credentials\.",
    r"id_rsa$",
    r"id_ed25519$",
    r"\.pem$",
    r"\.key$",
    r"private_key",
    r"api_key",
    r"access_token",
]
SENSITIVE_JSON_KEYS = [
    "password",
    "secret",
    "token",
    "key",
    "credential",
    "api_key",
    "private_key",
    "access_token",
    "auth",
    "authorization",
]

# Language extensions mapping
LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JavaScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".r": "R",
    ".m": "Objective-C",
    ".mm": "Objective-C++",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "SASS",
    ".vue": "Vue",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".xml": "XML",
    ".md": "Markdown",
    ".sh": "Shell",
    ".ps1": "PowerShell",
    ".bat": "Batch",
    ".cmd": "Batch",
}

# Side-effect indicators by language
SIDE_EFFECT_PATTERNS = {
    "Python": [
        r"open\(",
        r"with open\(",
        r"requests\.(get|post|put|delete)",
        r"urllib\.",
        r"subprocess\.",
        r"os\.(system|popen)",
        r"sqlite3\.",
        r"mysql\.",
        r"psycopg2\.",
        r"sqlalchemy\.",
        r"django\.",
        r"flask\.",
        r"pymongo\.",
        r"redis\.",
        r"boto3\.",
        r"aws\.",
    ],
    "JavaScript": [
        r'require\(["\']fs["\']',
        r"fs\.(read|write)",
        r"fetch\(",
        r"XMLHttpRequest",
        r"axios\.",
        r"superagent\.",
        r"mongoose\.",
        r"sequelize\.",
        r"pg\.",
        r"mysql\.",
        r"redis\.",
        r"aws-sdk",
        r"@aws-sdk",
    ],
    "Java": [
        r"java\.io\.",
        r"java\.nio\.",
        r"java\.sql\.",
        r"java\.net\.",
        r"javax\.sql\.",
        r"jdbc:",
        r"FileInputStream",
        r"FileOutputStream",
        r"HttpURLConnection",
        r"RestTemplate",
        r"OkHttp",
    ],
}


@dataclass
class FileMetrics:
    """Metrics for a single file."""

    path: str
    size: int
    language: str | None
    lines: int
    non_empty_lines: int
    functions: int
    classes: int
    imports: list[str]
    import_lines: list[int]
    complexity_estimate: float
    comment_density: float
    has_docstrings: bool
    side_effects: list[str]


@dataclass
class ModuleNode:
    """Node in the dependency graph."""

    path: str
    metrics: FileMetrics
    incoming: set[str]  # modules that import this
    outgoing: set[str]  # modules this imports
    fan_in: int
    fan_out: int


class RepositoryAnalyzer:
    """Main analyzer class for static repository analysis."""

    def __init__(self, root_path: str, output_dir: str, max_depth: int = MAX_RECURSION_DEPTH):
        self.root_path = Path(root_path).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.max_depth = max_depth
        self.excluded_dirs = DEFAULT_EXCLUDED_DIRS.copy()
        self.file_manifest: list[dict] = []
        self.file_metrics: dict[str, FileMetrics] = {}
        self.module_graph: dict[str, ModuleNode] = {}
        self.redacted_files: list[dict] = []
        self.language_counter = Counter()

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "file_metrics").mkdir(exist_ok=True)
        (self.output_dir / "deep_dive").mkdir(exist_ok=True)

    def is_sensitive_file(self, path: Path) -> bool:
        """Check if a file should be treated as sensitive."""
        name = path.name.lower()
        return any(re.search(pattern, name, re.IGNORECASE) for pattern in SENSITIVE_PATTERNS)

    def should_exclude(self, path: Path, depth: int) -> bool:
        """Check if a path should be excluded from analysis."""
        if depth > self.max_depth:
            return True
        parts = path.parts
        return any(part in self.excluded_dirs for part in parts) or self.is_sensitive_file(path)

    def get_file_language(self, path: Path) -> str | None:
        """Determine file language from extension."""
        ext = path.suffix.lower()
        return LANGUAGE_EXTENSIONS.get(ext)

    def redact_secrets_in_json(self, content: str) -> tuple[str, bool]:
        """Redact secret values in JSON/YAML content."""
        redacted = False
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                for key in list(data.keys()):
                    if any(sensitive in key.lower() for sensitive in SENSITIVE_JSON_KEYS):
                        data[key] = "REDACTED"
                        redacted = True
            return json.dumps(data, indent=2), redacted
        except Exception:
            # Not valid JSON, return as-is
            return content, False

    def read_file_safely(self, path: Path) -> tuple[str | None, bool]:
        """Read file with size limit and secret detection."""
        if not path.exists() or not path.is_file():
            return None, False

        try:
            size = path.stat().st_size
            if size > MAX_FILE_SIZE:
                return None, False

            with open(path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Check for secrets
            if self.is_sensitive_file(path):
                redacted_content, _ = self.redact_secrets_in_json(content)
                self.redacted_files.append(
                    {
                        "path": str(path.relative_to(self.root_path)),
                        "reason": "sensitive_filename_pattern",
                        "original_size": size,
                        "redacted": True,
                    }
                )
                return "REDACTED", True

            # Redact secrets in JSON/YAML
            if path.suffix.lower() in [".json", ".yaml", ".yml"]:
                content, was_redacted = self.redact_secrets_in_json(content)
                if was_redacted:
                    self.redacted_files.append(
                        {
                            "path": str(path.relative_to(self.root_path)),
                            "reason": "sensitive_json_keys",
                            "redacted": True,
                        }
                    )
                    return content, True

            return content, False
        except PermissionError:
            self.redacted_files.append(
                {"path": str(path.relative_to(self.root_path)), "reason": "permission_denied", "redacted": False}
            )
            return None, False
        except Exception as e:
            self.redacted_files.append(
                {"path": str(path.relative_to(self.root_path)), "reason": f"error: {str(e)}", "redacted": False}
            )
            return None, False

    def parse_python_ast(self, content: str, path: Path) -> FileMetrics:
        """Parse Python file using AST."""
        try:
            tree = ast.parse(content)
        except Exception:
            # Fallback to basic metrics if AST parsing fails
            lines = content.split("\n")
            return FileMetrics(
                path=str(path.relative_to(self.root_path)),
                size=len(content.encode()),
                language="Python",
                lines=len(lines),
                non_empty_lines=sum(1 for line in lines if line.strip()),
                functions=0,
                classes=0,
                imports=[],
                import_lines=[],
                complexity_estimate=0.0,
                comment_density=0.0,
                has_docstrings=False,
                side_effects=[],
            )

        lines = content.split("\n")
        functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))

        imports = []
        import_lines = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_lines.append(node.lineno)
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)

        # Count docstrings
        docstrings = sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)) and ast.get_docstring(node)
        )

        # Comment density
        comments = sum(1 for line in lines if line.strip().startswith("#"))
        comment_density = comments / len(lines) if lines else 0.0

        # Complexity estimate (rough: count decision points)
        complexity = sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.ExceptHandler))
        )

        # Side effects
        side_effects = []
        for pattern in SIDE_EFFECT_PATTERNS.get("Python", []):
            if re.search(pattern, content):
                side_effects.append(pattern)

        return FileMetrics(
            path=str(path.relative_to(self.root_path)),
            size=len(content.encode()),
            language="Python",
            lines=len(lines),
            non_empty_lines=sum(1 for line in lines if line.strip()),
            functions=functions,
            classes=classes,
            imports=imports,
            import_lines=import_lines,
            complexity_estimate=float(complexity),
            comment_density=comment_density,
            has_docstrings=docstrings > 0,
            side_effects=side_effects,
        )

    def detect_jsdoc(self, content: str) -> bool:
        """Detect JSDoc comments in TypeScript/JavaScript files."""
        # JSDoc pattern: /** ... */ blocks, typically before functions/classes
        jsdoc_pattern = r"/\*\*\s*\n(?:\s*\*[^\n]*\n)*\s*\*/"
        # Also check for single-line JSDoc: /** ... */
        single_line_jsdoc = r"/\*\*[^*]+\*/"

        # Check for JSDoc blocks
        if re.search(jsdoc_pattern, content, re.MULTILINE):
            return True
        if re.search(single_line_jsdoc, content):
            return True

        # Check for JSDoc-style comments before exports/functions
        # Pattern: /** ... */ followed by export or function/const/class
        jsdoc_before_export = r"/\*\*.*?\*/\s*(?:export\s+)?(?:function|const|class|interface|type)\s+\w+"
        if re.search(jsdoc_before_export, content, re.MULTILINE | re.DOTALL):
            return True

        return False

    def parse_generic_file(self, content: str, path: Path, language: str) -> FileMetrics:
        """Parse non-Python files with basic heuristics."""
        lines = content.split("\n")

        # Try to detect imports/exports
        imports = []
        import_lines = []

        if language in ["JavaScript", "TypeScript"]:
            # Match import/require statements (including TypeScript import syntax)
            for i, line in enumerate(lines, 1):
                # Match: import ... from "..."
                match = re.search(r'import\s+.*?\s+from\s+["\']([^"\']+)["\']', line)
                if match:
                    imports.append(match.group(1))
                    import_lines.append(i)
                # Match: require("...")
                match = re.search(r'require\(["\']([^"\']+)["\']\)', line)
                if match:
                    imports.append(match.group(1))
                    import_lines.append(i)

            # Side effects
            side_effects = []
            for pattern in SIDE_EFFECT_PATTERNS.get("JavaScript", []):
                if re.search(pattern, content):
                    side_effects.append(pattern)
        elif language == "Java":
            # Match import statements
            for i, line in enumerate(lines, 1):
                match = re.search(r"^import\s+([\w.]+)", line)
                if match:
                    imports.append(match.group(1))
                    import_lines.append(i)

            # Side effects
            side_effects = []
            for pattern in SIDE_EFFECT_PATTERNS.get("Java", []):
                if re.search(pattern, content):
                    side_effects.append(pattern)
        else:
            side_effects = []

        # Count functions (heuristic) - improved for TypeScript
        if language in ["JavaScript", "TypeScript"]:
            # Match: function name(...), const name = (...), export function, etc.
            functions = len(
                re.findall(r"(?:export\s+)?(?:function|const|let|var)\s+\w+\s*[=:]?\s*(?:\(|=>)", content, re.MULTILINE)
            )
            # Also count arrow functions assigned to variables
            functions += len(re.findall(r"\w+\s*[:=]\s*\([^)]*\)\s*=>", content))
        else:
            functions = len(re.findall(r"\bfunction\s+\w+|def\s+\w+|^\s*def\s+\w+", content, re.MULTILINE))

        classes = len(re.findall(r"\bclass\s+\w+", content))

        # Comment density
        comment_patterns = {
            "JavaScript": r"^\s*//|/\*|\*/",
            "TypeScript": r"^\s*//|/\*|\*/",
            "Java": r"^\s*//|/\*|\*/",
            "C++": r"^\s*//|/\*|\*/",
            "C": r"^\s*//|/\*|\*/",
        }
        pattern = comment_patterns.get(language, r"#")
        comments = sum(1 for line in lines if re.search(pattern, line))
        comment_density = comments / len(lines) if lines else 0.0

        # Detect docstrings (JSDoc for TypeScript/JavaScript)
        has_docstrings = False
        if language in ["TypeScript", "JavaScript"]:
            has_docstrings = self.detect_jsdoc(content)
        elif language == "Python":
            # This shouldn't be called for Python, but just in case
            has_docstrings = False

        # Complexity estimate (count control flow keywords)
        complexity_keywords = r"\b(if|else|for|while|switch|case|try|catch|except|await|async)\b"
        complexity = len(re.findall(complexity_keywords, content, re.IGNORECASE))

        return FileMetrics(
            path=str(path.relative_to(self.root_path)),
            size=len(content.encode()),
            language=language,
            lines=len(lines),
            non_empty_lines=sum(1 for line in lines if line.strip()),
            functions=functions,
            classes=classes,
            imports=imports,
            import_lines=import_lines,
            complexity_estimate=float(complexity),
            comment_density=comment_density,
            has_docstrings=has_docstrings,
            side_effects=side_effects,
        )

    def analyze_file(self, path: Path) -> FileMetrics | None:
        """Analyze a single file and return metrics."""
        content, was_redacted = self.read_file_safely(path)
        if content is None or content == "REDACTED":
            return None

        language = self.get_file_language(path)
        if language:
            self.language_counter[language] += 1

        if language == "Python":
            return self.parse_python_ast(content, path)
        elif language:
            return self.parse_generic_file(content, path, language)
        else:
            # Unknown language, return basic metrics
            lines = content.split("\n")
            return FileMetrics(
                path=str(path.relative_to(self.root_path)),
                size=len(content.encode()),
                language=None,
                lines=len(lines),
                non_empty_lines=sum(1 for line in lines if line.strip()),
                functions=0,
                classes=0,
                imports=[],
                import_lines=[],
                complexity_estimate=0.0,
                comment_density=0.0,
                has_docstrings=False,
                side_effects=[],
            )

    def normalize_import(self, imp: str, current_file: Path) -> str | None:
        """Normalize import path to module identifier."""
        # Remove relative imports, convert to absolute-ish paths
        if imp.startswith("."):
            # Relative import - approximate resolution
            parts = imp.split(".")
            parent = current_file.parent
            for part in parts[1:]:
                if part:
                    parent = parent / part
            return str(parent.relative_to(self.root_path)).replace("\\", "/").replace("/", ".")

        # Absolute import - keep as module name
        return imp.replace("/", ".").replace("\\", ".")

    def build_dependency_graph(self):
        """Build module dependency graph from file metrics."""
        for file_path, metrics in self.file_metrics.items():
            full_path = self.root_path / metrics.path
            node = ModuleNode(path=metrics.path, metrics=metrics, incoming=set(), outgoing=set(), fan_in=0, fan_out=0)

            # Process imports
            for imp in metrics.imports:
                normalized = self.normalize_import(imp, full_path)
                if normalized:
                    node.outgoing.add(normalized)

            self.module_graph[metrics.path] = node

        # Build reverse edges (incoming)
        for file_path, node in self.module_graph.items():
            for outgoing in node.outgoing:
                # Find all nodes that match this import
                for other_path, other_node in self.module_graph.items():
                    # Check if other_node's path/name matches the import
                    other_module = other_node.path.replace("\\", "/").replace("/", ".").replace(".py", "")
                    if outgoing in other_module or other_module.endswith(outgoing):
                        other_node.incoming.add(file_path)

        # Calculate fan-in/fan-out
        for node in self.module_graph.values():
            node.fan_in = len(node.incoming)
            node.fan_out = len(node.outgoing)

    def identify_candidates(self) -> dict[str, list[dict]]:
        """Identify candidates for refactoring and high-value components."""
        candidates_for_refactor = []
        reference_high_value_components = []

        for path, node in self.module_graph.items():
            metrics = node.metrics
            if not metrics.language or metrics.lines == 0:
                continue

            # High-traffic, low-contribution heuristic
            is_high_traffic = node.fan_in >= 3  # Imported by 3+ modules
            low_comment_density = metrics.comment_density < 0.1  # < 10% comments
            high_complexity = metrics.complexity_estimate > metrics.lines * 0.1  # > 10% decision points
            no_docstrings = not metrics.has_docstrings
            high_loc = metrics.lines > 200

            if is_high_traffic and (low_comment_density or high_complexity or no_docstrings) and high_loc:
                score = node.fan_in * (metrics.complexity_estimate / max(metrics.lines, 1))
                candidates_for_refactor.append(
                    {
                        "module_id": f"module_{len(candidates_for_refactor) + 1:03d}",
                        "file_path": path,
                        "path": path,  # Keep both for compatibility
                        "score": score,
                        "fan_in": node.fan_in,
                        "fan_out": node.fan_out,
                        "lines": metrics.lines,
                        "complexity": metrics.complexity_estimate,
                        "comment_density": metrics.comment_density,
                        "has_docstrings": metrics.has_docstrings,
                        "rationale": f"High fan-in ({node.fan_in}), low documentation/comments",
                    }
                )

            # High-value, efficient components (inverse criteria)
            is_well_documented = metrics.comment_density >= 0.15 and metrics.has_docstrings
            low_complexity = metrics.complexity_estimate < metrics.lines * 0.05
            moderate_reuse = node.fan_in >= 2  # Used by 2+ modules

            if is_well_documented and (low_complexity or moderate_reuse):
                score = node.fan_in * (1.0 / max(metrics.complexity_estimate, 1)) * (1.0 + metrics.comment_density)
                reference_high_value_components.append(
                    {
                        "module_id": f"module_ref_{len(reference_high_value_components) + 1:03d}",
                        "file_path": path,
                        "path": path,  # Keep both for compatibility
                        "score": score,
                        "fan_in": node.fan_in,
                        "fan_out": node.fan_out,
                        "lines": metrics.lines,
                        "complexity": metrics.complexity_estimate,
                        "comment_density": metrics.comment_density,
                        "has_docstrings": metrics.has_docstrings,
                        "rationale": f"Well-documented, efficient, reused by {node.fan_in} modules",
                    }
                )

        # Sort by score
        candidates_for_refactor.sort(key=lambda x: x["score"], reverse=True)
        reference_high_value_components.sort(key=lambda x: x["score"], reverse=True)

        return {
            "candidates_for_refactor": candidates_for_refactor[:20],  # Top 20
            "reference_high_value_components": reference_high_value_components[:20],
        }

    def deep_dive_analysis(self, file_path: str) -> dict:
        """Perform deep-dive analysis on a specific file."""
        if file_path not in self.file_metrics:
            return {}

        metrics = self.file_metrics[file_path]
        node = self.module_graph.get(file_path)

        # Read file content for detailed analysis
        full_path = self.root_path / metrics.path
        content, _ = self.read_file_safely(full_path)

        if content is None or content == "REDACTED":
            return {"path": file_path, "error": "File cannot be read or was redacted"}

        # Parameter routing (heuristic for Python)
        parameter_routing = []
        if metrics.language == "Python":
            try:
                tree = ast.parse(content)
                for node_ast in ast.walk(tree):
                    if isinstance(node_ast, ast.FunctionDef):
                        params = [arg.arg for arg in node_ast.args.args]
                        if params:
                            parameter_routing.append(
                                {
                                    "function": node_ast.name,
                                    "line": node_ast.lineno,
                                    "parameters": params,
                                    "parameter_count": len(params),
                                }
                            )
            except Exception:
                pass

        # Call sites (who calls this module)
        call_sites = []
        for other_path, other_node in self.module_graph.items():
            if file_path in other_node.outgoing or file_path in str(other_node.metrics.imports):
                call_sites.append(
                    {
                        "caller": other_path,
                        "imports": [
                            imp for imp in other_node.metrics.imports if file_path in imp or metrics.path in imp
                        ],
                    }
                )

        return {
            "path": file_path,
            "metrics": asdict(metrics),
            "fan_in": node.fan_in if node else 0,
            "fan_out": node.fan_out if node else 0,
            "parameter_routing": parameter_routing[:50],  # Limit output
            "call_sites": call_sites[:50],
            "side_effects": metrics.side_effects,
            "incoming_modules": list(node.incoming)[:20] if node else [],
            "outgoing_modules": list(node.outgoing)[:20] if node else [],
        }

    def generate_manifest(self):
        """Generate file manifest."""
        print("Generating file manifest...")
        self.file_manifest = []

        def walk_directory(path: Path, depth: int = 0):
            if self.should_exclude(path, depth):
                return

            try:
                if path.is_file():
                    size = path.stat().st_size
                    language = self.get_file_language(path)
                    self.file_manifest.append(
                        {
                            "path": str(path.relative_to(self.root_path)),
                            "size": size,
                            "language": language,
                            "depth": depth,
                        }
                    )
                elif path.is_dir():
                    for item in path.iterdir():
                        walk_directory(item, depth + 1)
            except PermissionError:
                pass
            except Exception:
                pass

        walk_directory(self.root_path)
        print(f"Found {len(self.file_manifest)} files")

    def analyze_repository(self):
        """Main analysis workflow."""
        print(f"Analyzing repository: {self.root_path}")
        print(f"Output directory: {self.output_dir}")

        # Step 1: Generate manifest
        self.generate_manifest()

        # Step 2: Analyze files
        print("Analyzing files...")
        python_files = [f for f in self.file_manifest if f.get("language") == "Python"]
        other_files = [f for f in self.file_manifest if f.get("language") and f.get("language") != "Python"]

        # Analyze Python files first (AST parsing)
        for file_info in python_files[:1000]:  # Limit to first 1000 per language
            path = self.root_path / file_info["path"]
            metrics = self.analyze_file(path)
            if metrics:
                self.file_metrics[metrics.path] = metrics

        # Analyze other files
        for file_info in other_files[:500]:  # Limit for performance
            path = self.root_path / file_info["path"]
            metrics = self.analyze_file(path)
            if metrics:
                self.file_metrics[metrics.path] = metrics

        print(f"Analyzed {len(self.file_metrics)} files")

        # Step 3: Build dependency graph
        print("Building dependency graph...")
        self.build_dependency_graph()
        print(f"Graph contains {len(self.module_graph)} nodes")

        # Step 4: Identify candidates
        print("Identifying candidates...")
        candidates = self.identify_candidates()
        print(f"Found {len(candidates['candidates_for_refactor'])} refactor candidates")
        print(f"Found {len(candidates['reference_high_value_components'])} high-value components")

        return candidates

    def save_outputs(self, candidates: dict):
        """Save all output artifacts."""
        print("Saving outputs...")

        # Manifest
        with open(self.output_dir / "manifest.json", "w") as f:
            json.dump(
                {
                    "root_path": str(self.root_path),
                    "total_files": len(self.file_manifest),
                    "analyzed_files": len(self.file_metrics),
                    "files": self.file_manifest[:1000],  # Sample for manifest
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

        # Language summary
        language_summary = {
            "total_files": len(self.file_manifest),
            "languages": dict(self.language_counter.most_common(20)),
            "top_languages": [{"name": lang, "count": count} for lang, count in self.language_counter.most_common(10)],
        }
        with open(self.output_dir / "language_summary.json", "w") as f:
            json.dump(language_summary, f, indent=2)

        # File metrics (sample)
        metrics_sample = {path: asdict(metrics) for path, metrics in list(self.file_metrics.items())[:100]}
        for path, metrics_dict in metrics_sample.items():
            safe_path = path.replace("/", "_").replace("\\", "_").replace("..", "")
            with open(self.output_dir / "file_metrics" / f"{safe_path}.json", "w") as f:
                json.dump(metrics_dict, f, indent=2)

        # Module graph (JSON format)
        graph_data = {
            "nodes": [
                {
                    "id": path,
                    "path": path,
                    "fan_in": node.fan_in,
                    "fan_out": node.fan_out,
                    "lines": node.metrics.lines,
                    "complexity": node.metrics.complexity_estimate,
                    "language": node.metrics.language,
                }
                for path, node in list(self.module_graph.items())[:500]  # Limit for size
            ],
            "edges": [
                {"source": source_path, "target": target_import, "type": "import"}
                for source_path, source_node in list(self.module_graph.items())[:500]
                for target_import in list(source_node.outgoing)[:10]  # Limit outgoing per node
            ],
        }
        with open(self.output_dir / "module_graph.json", "w") as f:
            json.dump(graph_data, f, indent=2)

        # GraphML format (simplified)
        graphml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
            '<key id="fan_in" for="node" attr.name="fan_in" attr.type="int"/>',
            '<key id="fan_out" for="node" attr.name="fan_out" attr.type="int"/>',
            '<key id="lines" for="node" attr.name="lines" attr.type="int"/>',
            '<graph id="dependency_graph" edgedefault="directed">',
        ]

        # Add nodes (limited for size)
        for path, node in list(self.module_graph.items())[:200]:
            safe_id = path.replace("/", "_").replace("\\", "_").replace("..", "")
            graphml_lines.append(f'<node id="{safe_id}">')
            graphml_lines.append(f'<data key="fan_in">{node.fan_in}</data>')
            graphml_lines.append(f'<data key="fan_out">{node.fan_out}</data>')
            graphml_lines.append(f'<data key="lines">{node.metrics.lines}</data>')
            graphml_lines.append("</node>")

        # Add edges (limited)
        edge_count = 0
        for source_path, source_node in list(self.module_graph.items())[:200]:
            if edge_count > 500:
                break
            source_id = source_path.replace("/", "_").replace("\\", "_").replace("..", "")
            for target in list(source_node.outgoing)[:5]:
                if edge_count > 500:
                    break
                target_id = target.replace("/", "_").replace("\\", "_").replace("..", "")
                graphml_lines.append(f'<edge source="{source_id}" target="{target_id}"/>')
                edge_count += 1

        graphml_lines.extend(["</graph>", "</graphml>"])
        with open(self.output_dir / "module_graph.graphml", "w") as f:
            f.write("\n".join(graphml_lines))

        # Candidates
        with open(self.output_dir / "candidates.json", "w") as f:
            json.dump(candidates, f, indent=2)

        # Deep dive for top candidates
        if candidates["candidates_for_refactor"]:
            top_candidate = candidates["candidates_for_refactor"][0]
            deep_dive = self.deep_dive_analysis(top_candidate["path"])
            with open(self.output_dir / "deep_dive" / "top_refactor_candidate.json", "w") as f:
                json.dump(deep_dive, f, indent=2)

        if candidates["reference_high_value_components"]:
            top_reference = candidates["reference_high_value_components"][0]
            deep_dive = self.deep_dive_analysis(top_reference["path"])
            with open(self.output_dir / "deep_dive" / "top_reference_component.json", "w") as f:
                json.dump(deep_dive, f, indent=2)

        # Risk and redaction report
        with open(self.output_dir / "risk_and_redaction_report.json", "w") as f:
            json.dump(
                {
                    "total_redacted": len(self.redacted_files),
                    "redacted_files": self.redacted_files,
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

        print("All outputs saved successfully!")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Static repository analysis tool")
    parser.add_argument("--root", required=True, help="Root path of repository to analyze")
    parser.add_argument("--out", required=True, help="Output directory for artifacts")
    parser.add_argument("--max-depth", type=int, default=MAX_RECURSION_DEPTH, help="Maximum recursion depth")
    parser.add_argument("--exclude", help="Comma-separated list of directories to exclude")

    args = parser.parse_args()

    analyzer = RepositoryAnalyzer(args.root, args.out, args.max_depth)

    if args.exclude:
        analyzer.excluded_dirs.update(args.exclude.split(","))

    candidates = analyzer.analyze_repository()
    analyzer.save_outputs(candidates)


if __name__ == "__main__":
    main()
