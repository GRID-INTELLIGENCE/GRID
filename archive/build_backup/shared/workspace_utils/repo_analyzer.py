"""
Repository Analysis Module

Migrated from analyze_repo.py - provides static repository analysis
with Cascade integration for context awareness.
"""

import os
import json
import ast
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from .config import config
from .exceptions import AnalysisError, ValidationError
from .validators import validate_root_path, validate_output_dir
from .logging_config import get_logger

# Constants from original script
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_RECURSION_DEPTH = 6

LANGUAGE_EXTENSIONS = {
    '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
    '.jsx': 'JavaScript', '.tsx': 'TypeScript', '.java': 'Java',
    '.cpp': 'C++', '.c': 'C', '.cs': 'C#', '.go': 'Go', '.rs': 'Rust',
    '.rb': 'Ruby', '.php': 'PHP', '.swift': 'Swift', '.kt': 'Kotlin',
    '.scala': 'Scala', '.r': 'R', '.m': 'Objective-C', '.mm': 'Objective-C++',
    '.sql': 'SQL', '.html': 'HTML', '.css': 'CSS', '.scss': 'SCSS',
    '.sass': 'SASS', '.vue': 'Vue', '.json': 'JSON', '.yaml': 'YAML',
    '.yml': 'YAML', '.xml': 'XML', '.md': 'Markdown', '.sh': 'Shell',
    '.ps1': 'PowerShell', '.bat': 'Batch', '.cmd': 'Batch'
}

SIDE_EFFECT_PATTERNS = {
    'Python': [
        r'open\(', r'with open\(', r'requests\.(get|post|put|delete)',
        r'urllib\.', r'subprocess\.', r'os\.(system|popen)', r'sqlite3\.',
        r'mysql\.', r'psycopg2\.', r'sqlalchemy\.', r'django\.', r'flask\.',
        r'pymongo\.', r'redis\.', r'boto3\.', r'aws\.'
    ],
    'JavaScript': [
        r'require\(["\']fs["\']', r'fs\.(read|write)', r'fetch\(', r'XMLHttpRequest',
        r'axios\.', r'superagent\.', r'mongoose\.', r'sequelize\.', r'pg\.',
        r'mysql\.', r'redis\.', r'aws-sdk', r'@aws-sdk'
    ],
    'Java': [
        r'java\.io\.', r'java\.nio\.', r'java\.sql\.', r'java\.net\.',
        r'javax\.sql\.', r'jdbc:', r'FileInputStream', r'FileOutputStream',
        r'HttpURLConnection', r'RestTemplate', r'OkHttp'
    ]
}

SENSITIVE_PATTERNS = [
    r'\.env$', r'secrets\.', r'credentials\.', r'id_rsa$', r'id_ed25519$',
    r'\.pem$', r'\.key$', r'private_key', r'api_key', r'access_token'
]

SENSITIVE_JSON_KEYS = [
    'password', 'secret', 'token', 'key', 'credential', 'api_key',
    'private_key', 'access_token', 'auth', 'authorization'
]


@dataclass
class FileMetrics:
    """Metrics for a single file."""
    path: str
    size: int
    language: Optional[str]
    lines: int
    non_empty_lines: int
    functions: int
    classes: int
    imports: List[str]
    import_lines: List[int]
    complexity_estimate: float
    comment_density: float
    has_docstrings: bool
    side_effects: List[str]


@dataclass
class ModuleNode:
    """Node in the dependency graph."""
    path: str
    metrics: FileMetrics
    incoming: Set[str]
    outgoing: Set[str]
    fan_in: int
    fan_out: int


class RepositoryAnalyzer:
    """Main analyzer class for static repository analysis."""

    def __init__(self, root_path: str, output_dir: Optional[str] = None, max_depth: int = None):
        # Validate and normalize paths
        self.root_path = validate_root_path(root_path)
        self.output_dir = validate_output_dir(output_dir, create=True) if output_dir else config.get_output_dir()
        self.max_depth = max_depth or config.get("max_recursion_depth", MAX_RECURSION_DEPTH)
        
        # Validate max_depth
        from .validators import validate_max_depth
        self.max_depth = validate_max_depth(self.max_depth)
        
        self.excluded_dirs = set(config.get_excluded_dirs())
        self.file_manifest: List[Dict] = []
        self.file_metrics: Dict[str, FileMetrics] = {}
        self.module_graph: Dict[str, ModuleNode] = {}
        self.redacted_files: List[Dict] = []
        self.language_counter = Counter()
        self.logger = get_logger("repo_analyzer")

        # Create output directory structure
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            (self.output_dir / 'file_metrics').mkdir(exist_ok=True)
            (self.output_dir / 'deep_dive').mkdir(exist_ok=True)
        except (OSError, PermissionError) as e:
            raise AnalysisError(
                f"Cannot create output directory: {self.output_dir}\n"
                f"Error: {str(e)}\n"
                f"Please check write permissions."
            ) from e

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

    def get_file_language(self, path: Path) -> Optional[str]:
        """Determine file language from extension."""
        ext = path.suffix.lower()
        return LANGUAGE_EXTENSIONS.get(ext)

    def redact_secrets_in_json(self, content: str) -> Tuple[str, bool]:
        """Redact secret values in JSON/YAML content."""
        redacted = False
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                for key in list(data.keys()):
                    if any(sensitive in key.lower() for sensitive in SENSITIVE_JSON_KEYS):
                        data[key] = 'REDACTED'
                        redacted = True
            return json.dumps(data, indent=2), redacted
        except:
            return content, False

    def read_file_safely(self, path: Path) -> Tuple[Optional[str], bool]:
        """Read file with size limit and secret detection."""
        if not path.exists() or not path.is_file():
            return None, False

        try:
            size = path.stat().st_size
            max_size = config.get("max_file_size_mb", 5) * 1024 * 1024
            if size > max_size:
                return None, False

            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if self.is_sensitive_file(path):
                redacted_content, _ = self.redact_secrets_in_json(content)
                self.redacted_files.append({
                    'path': str(path.relative_to(self.root_path)),
                    'reason': 'sensitive_filename_pattern',
                    'original_size': size,
                    'redacted': True
                })
                return 'REDACTED', True

            if path.suffix.lower() in ['.json', '.yaml', '.yml']:
                content, was_redacted = self.redact_secrets_in_json(content)
                if was_redacted:
                    self.redacted_files.append({
                        'path': str(path.relative_to(self.root_path)),
                        'reason': 'sensitive_json_keys',
                        'redacted': True
                    })
                    return content, True

            return content, False
        except (PermissionError, Exception) as e:
            self.redacted_files.append({
                'path': str(path.relative_to(self.root_path)),
                'reason': f'error: {str(e)}',
                'redacted': False
            })
            return None, False

    def parse_python_ast(self, content: str, path: Path) -> FileMetrics:
        """Parse Python file using AST."""
        try:
            tree = ast.parse(content)
        except:
            lines = content.split('\n')
            return FileMetrics(
                path=str(path.relative_to(self.root_path)),
                size=len(content.encode()),
                language='Python',
                lines=len(lines),
                non_empty_lines=sum(1 for l in lines if l.strip()),
                functions=0,
                classes=0,
                imports=[],
                import_lines=[],
                complexity_estimate=0.0,
                comment_density=0.0,
                has_docstrings=False,
                side_effects=[]
            )

        lines = content.split('\n')
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

        docstrings = sum(1 for node in ast.walk(tree)
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module))
                        and ast.get_docstring(node))

        comments = sum(1 for line in lines if line.strip().startswith('#'))
        comment_density = comments / len(lines) if lines else 0.0

        complexity = sum(
            1 for node in ast.walk(tree)
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.ExceptHandler))
        )

        content_lower = content.lower()
        side_effects = []
        for pattern in SIDE_EFFECT_PATTERNS.get('Python', []):
            if re.search(pattern, content):
                side_effects.append(pattern)

        return FileMetrics(
            path=str(path.relative_to(self.root_path)),
            size=len(content.encode()),
            language='Python',
            lines=len(lines),
            non_empty_lines=sum(1 for l in lines if l.strip()),
            functions=functions,
            classes=classes,
            imports=imports,
            import_lines=import_lines,
            complexity_estimate=float(complexity),
            comment_density=comment_density,
            has_docstrings=docstrings > 0,
            side_effects=side_effects
        )

    def detect_jsdoc(self, content: str) -> bool:
        """Detect JSDoc comments in TypeScript/JavaScript files."""
        jsdoc_pattern = r'/\*\*\s*\n(?:\s*\*[^\n]*\n)*\s*\*/'
        single_line_jsdoc = r'/\*\*[^*]+\*/'
        if re.search(jsdoc_pattern, content, re.MULTILINE) or re.search(single_line_jsdoc, content):
            return True
        jsdoc_before_export = r'/\*\*.*?\*/\s*(?:export\s+)?(?:function|const|class|interface|type)\s+\w+'
        return bool(re.search(jsdoc_before_export, content, re.MULTILINE | re.DOTALL))

    def parse_generic_file(self, content: str, path: Path, language: str) -> FileMetrics:
        """Parse non-Python files with basic heuristics."""
        lines = content.split('\n')
        imports = []
        import_lines = []

        if language in ['JavaScript', 'TypeScript']:
            for i, line in enumerate(lines, 1):
                match = re.search(r'import\s+.*?\s+from\s+["\']([^"\']+)["\']', line)
                if match:
                    imports.append(match.group(1))
                    import_lines.append(i)
                match = re.search(r'require\(["\']([^"\']+)["\']\)', line)
                if match:
                    imports.append(match.group(1))
                    import_lines.append(i)

            content_lower = content.lower()
            side_effects = []
            for pattern in SIDE_EFFECT_PATTERNS.get('JavaScript', []):
                if re.search(pattern, content):
                    side_effects.append(pattern)
        elif language == 'Java':
            for i, line in enumerate(lines, 1):
                match = re.search(r'^import\s+([\w.]+)', line)
                if match:
                    imports.append(match.group(1))
                    import_lines.append(i)
            side_effects = []
            for pattern in SIDE_EFFECT_PATTERNS.get('Java', []):
                if re.search(pattern, content):
                    side_effects.append(pattern)
        else:
            side_effects = []

        if language in ['JavaScript', 'TypeScript']:
            functions = len(re.findall(
                r'(?:export\s+)?(?:function|const|let|var)\s+\w+\s*[=:]?\s*(?:\(|=>)',
                content, re.MULTILINE
            ))
            functions += len(re.findall(r'\w+\s*[:=]\s*\([^)]*\)\s*=>', content))
        else:
            functions = len(re.findall(r'\bfunction\s+\w+|def\s+\w+|^\s*def\s+\w+', content, re.MULTILINE))

        classes = len(re.findall(r'\bclass\s+\w+', content))

        comment_patterns = {
            'JavaScript': r'^\s*//|/\*|\*/',
            'TypeScript': r'^\s*//|/\*|\*/',
            'Java': r'^\s*//|/\*|\*/',
            'C++': r'^\s*//|/\*|\*/',
            'C': r'^\s*//|/\*|\*/'
        }
        pattern = comment_patterns.get(language, r'#')
        comments = sum(1 for line in lines if re.search(pattern, line))
        comment_density = comments / len(lines) if lines else 0.0

        has_docstrings = False
        if language in ['TypeScript', 'JavaScript']:
            has_docstrings = self.detect_jsdoc(content)

        complexity_keywords = r'\b(if|else|for|while|switch|case|try|catch|except|await|async)\b'
        complexity = len(re.findall(complexity_keywords, content, re.IGNORECASE))

        return FileMetrics(
            path=str(path.relative_to(self.root_path)),
            size=len(content.encode()),
            language=language,
            lines=len(lines),
            non_empty_lines=sum(1 for l in lines if l.strip()),
            functions=functions,
            classes=classes,
            imports=imports,
            import_lines=import_lines,
            complexity_estimate=float(complexity),
            comment_density=comment_density,
            has_docstrings=has_docstrings,
            side_effects=side_effects
        )

    def analyze_file(self, path: Path) -> Optional[FileMetrics]:
        """Analyze a single file and return metrics."""
        content, was_redacted = self.read_file_safely(path)
        if content is None or content == 'REDACTED':
            return None

        language = self.get_file_language(path)
        if language:
            self.language_counter[language] += 1

        if language == 'Python':
            return self.parse_python_ast(content, path)
        elif language:
            return self.parse_generic_file(content, path, language)
        else:
            lines = content.split('\n')
            return FileMetrics(
                path=str(path.relative_to(self.root_path)),
                size=len(content.encode()),
                language=None,
                lines=len(lines),
                non_empty_lines=sum(1 for l in lines if l.strip()),
                functions=0,
                classes=0,
                imports=[],
                import_lines=[],
                complexity_estimate=0.0,
                comment_density=0.0,
                has_docstrings=False,
                side_effects=[]
            )

    def normalize_import(self, imp: str, current_file: Path) -> Optional[str]:
        """Normalize import path to module identifier."""
        if imp.startswith('.'):
            parts = imp.split('.')
            parent = current_file.parent
            for part in parts[1:]:
                if part:
                    parent = parent / part
            return str(parent.relative_to(self.root_path)).replace('\\', '/').replace('/', '.')
        return imp.replace('/', '.').replace('\\', '.')

    def build_dependency_graph(self):
        """Build module dependency graph from file metrics."""
        for file_path, metrics in self.file_metrics.items():
            full_path = self.root_path / metrics.path
            node = ModuleNode(
                path=metrics.path,
                metrics=metrics,
                incoming=set(),
                outgoing=set(),
                fan_in=0,
                fan_out=0
            )

            for imp in metrics.imports:
                normalized = self.normalize_import(imp, full_path)
                if normalized:
                    node.outgoing.add(normalized)

            self.module_graph[metrics.path] = node

        for file_path, node in self.module_graph.items():
            for outgoing in node.outgoing:
                for other_path, other_node in self.module_graph.items():
                    other_module = other_node.path.replace('\\', '/').replace('/', '.').replace('.py', '')
                    if outgoing in other_module or other_module.endswith(outgoing):
                        other_node.incoming.add(file_path)

        for node in self.module_graph.values():
            node.fan_in = len(node.incoming)
            node.fan_out = len(node.outgoing)

    def identify_candidates(self) -> Dict[str, List[Dict]]:
        """Identify candidates for refactoring and high-value components."""
        candidates_for_refactor = []
        reference_high_value_components = []

        for path, node in self.module_graph.items():
            metrics = node.metrics
            if not metrics.language or metrics.lines == 0:
                continue

            is_high_traffic = node.fan_in >= 3
            low_comment_density = metrics.comment_density < 0.1
            high_complexity = metrics.complexity_estimate > metrics.lines * 0.1
            no_docstrings = not metrics.has_docstrings
            high_loc = metrics.lines > 200

            if is_high_traffic and (low_comment_density or high_complexity or no_docstrings) and high_loc:
                score = node.fan_in * (metrics.complexity_estimate / max(metrics.lines, 1))
                candidates_for_refactor.append({
                    'module_id': f"module_{len(candidates_for_refactor) + 1:03d}",
                    'file_path': path,
                    'path': path,
                    'score': score,
                    'fan_in': node.fan_in,
                    'fan_out': node.fan_out,
                    'lines': metrics.lines,
                    'complexity': metrics.complexity_estimate,
                    'comment_density': metrics.comment_density,
                    'has_docstrings': metrics.has_docstrings,
                    'rationale': f'High fan-in ({node.fan_in}), low documentation/comments'
                })

            is_well_documented = metrics.comment_density >= 0.15 and metrics.has_docstrings
            low_complexity = metrics.complexity_estimate < metrics.lines * 0.05
            moderate_reuse = node.fan_in >= 2

            if is_well_documented and (low_complexity or moderate_reuse):
                score = node.fan_in * (1.0 / max(metrics.complexity_estimate, 1)) * (1.0 + metrics.comment_density)
                reference_high_value_components.append({
                    'module_id': f"module_ref_{len(reference_high_value_components) + 1:03d}",
                    'file_path': path,
                    'path': path,
                    'score': score,
                    'fan_in': node.fan_in,
                    'fan_out': node.fan_out,
                    'lines': metrics.lines,
                    'complexity': metrics.complexity_estimate,
                    'comment_density': metrics.comment_density,
                    'has_docstrings': metrics.has_docstrings,
                    'rationale': f'Well-documented, efficient, reused by {node.fan_in} modules'
                })

        candidates_for_refactor.sort(key=lambda x: x['score'], reverse=True)
        reference_high_value_components.sort(key=lambda x: x['score'], reverse=True)

        return {
            'candidates_for_refactor': candidates_for_refactor[:20],
            'reference_high_value_components': reference_high_value_components[:20]
        }

    def generate_manifest(self):
        """Generate file manifest."""
        self.logger.info("Generating file manifest...")
        self.file_manifest = []

        def walk_directory(path: Path, depth: int = 0):
            if self.should_exclude(path, depth):
                return

            try:
                if path.is_file():
                    size = path.stat().st_size
                    language = self.get_file_language(path)
                    self.file_manifest.append({
                        'path': str(path.relative_to(self.root_path)),
                        'size': size,
                        'language': language,
                        'depth': depth
                    })
                elif path.is_dir():
                    for item in path.iterdir():
                        walk_directory(item, depth + 1)
            except (PermissionError, Exception):
                pass

        walk_directory(self.root_path)
        self.logger.info(f"Found {len(self.file_manifest)} files")

    def analyze_repository(self):
        """Main analysis workflow."""
        self.logger.info(f"Analyzing repository: {self.root_path}")
        self.logger.info(f"Output directory: {self.output_dir}")

        self.generate_manifest()

        self.logger.info("Analyzing files...")
        python_files = [f for f in self.file_manifest if f.get('language') == 'Python']
        other_files = [f for f in self.file_manifest if f.get('language') and f.get('language') != 'Python']

        for file_info in python_files[:1000]:
            path = self.root_path / file_info['path']
            metrics = self.analyze_file(path)
            if metrics:
                self.file_metrics[metrics.path] = metrics

        for file_info in other_files[:500]:
            path = self.root_path / file_info['path']
            metrics = self.analyze_file(path)
            if metrics:
                self.file_metrics[metrics.path] = metrics

        self.logger.info(f"Analyzed {len(self.file_metrics)} files")

        self.logger.info("Building dependency graph...")
        self.build_dependency_graph()
        self.logger.info(f"Graph contains {len(self.module_graph)} nodes")

        self.logger.info("Identifying candidates...")
        candidates = self.identify_candidates()
        self.logger.info(f"Found {len(candidates['candidates_for_refactor'])} refactor candidates")
        self.logger.info(f"Found {len(candidates['reference_high_value_components'])} high-value components")

        return candidates

    def save_outputs(self, candidates: Dict, output_json: bool = None):
        """Save all output artifacts. Outputs JSON if Cascade integration is enabled."""
        self.logger.info("Saving outputs...")
        output_json = output_json if output_json is not None else config.should_output_json()

        # Manifest
        manifest_data = {
            'root_path': str(self.root_path),
            'total_files': len(self.file_manifest),
            'analyzed_files': len(self.file_metrics),
            'files': self.file_manifest[:1000],
            'timestamp': datetime.now().isoformat()
        }
        with open(self.output_dir / 'manifest.json', 'w') as f:
            json.dump(manifest_data, f, indent=2)

        # Language summary
        language_summary = {
            'total_files': len(self.file_manifest),
            'languages': dict(self.language_counter.most_common(20)),
            'top_languages': [{'name': lang, 'count': count}
                            for lang, count in self.language_counter.most_common(10)]
        }
        with open(self.output_dir / 'language_summary.json', 'w') as f:
            json.dump(language_summary, f, indent=2)

        # File metrics (sample)
        metrics_sample = {path: asdict(metrics)
                         for path, metrics in list(self.file_metrics.items())[:100]}
        for path, metrics_dict in metrics_sample.items():
            safe_path = path.replace('/', '_').replace('\\', '_').replace('..', '')
            with open(self.output_dir / 'file_metrics' / f'{safe_path}.json', 'w') as f:
                json.dump(metrics_dict, f, indent=2)

        # Module graph (JSON format - Cascade-friendly)
        graph_data = {
            'nodes': [
                {
                    'id': path,
                    'path': path,
                    'fan_in': node.fan_in,
                    'fan_out': node.fan_out,
                    'lines': node.metrics.lines,
                    'complexity': node.metrics.complexity_estimate,
                    'language': node.metrics.language
                }
                for path, node in list(self.module_graph.items())[:500]
            ],
            'edges': [
                {
                    'source': source_path,
                    'target': target_import,
                    'type': 'import'
                }
                for source_path, source_node in list(self.module_graph.items())[:500]
                for target_import in list(source_node.outgoing)[:10]
            ]
        }
        with open(self.output_dir / 'module_graph.json', 'w') as f:
            json.dump(graph_data, f, indent=2)

        # Candidates (always JSON for Cascade)
        with open(self.output_dir / 'candidates.json', 'w') as f:
            json.dump(candidates, f, indent=2)

        # Deep dive for top candidates
        if candidates['candidates_for_refactor']:
            top_candidate = candidates['candidates_for_refactor'][0]
            deep_dive = self.deep_dive_analysis(top_candidate['path'])
            with open(self.output_dir / 'deep_dive' / 'top_refactor_candidate.json', 'w') as f:
                json.dump(deep_dive, f, indent=2)

        if candidates['reference_high_value_components']:
            top_reference = candidates['reference_high_value_components'][0]
            deep_dive = self.deep_dive_analysis(top_reference['path'])
            with open(self.output_dir / 'deep_dive' / 'top_reference_component.json', 'w') as f:
                json.dump(deep_dive, f, indent=2)

        # Risk and redaction report
        with open(self.output_dir / 'risk_and_redaction_report.json', 'w') as f:
            json.dump({
                'total_redacted': len(self.redacted_files),
                'redacted_files': self.redacted_files,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)

        self.logger.info("All outputs saved successfully!")

    def deep_dive_analysis(self, file_path: str) -> Dict:
        """Perform deep-dive analysis on a specific file."""
        if file_path not in self.file_metrics:
            return {}

        metrics = self.file_metrics[file_path]
        node = self.module_graph.get(file_path)

        full_path = self.root_path / metrics.path
        content, _ = self.read_file_safely(full_path)

        if content is None or content == 'REDACTED':
            return {
                'path': file_path,
                'error': 'File cannot be read or was redacted'
            }

        parameter_routing = []
        if metrics.language == 'Python':
            try:
                tree = ast.parse(content)
                for node_ast in ast.walk(tree):
                    if isinstance(node_ast, ast.FunctionDef):
                        params = [arg.arg for arg in node_ast.args.args]
                        if params:
                            parameter_routing.append({
                                'function': node_ast.name,
                                'line': node_ast.lineno,
                                'parameters': params,
                                'parameter_count': len(params)
                            })
            except:
                pass

        call_sites = []
        for other_path, other_node in self.module_graph.items():
            if file_path in other_node.outgoing or file_path in str(other_node.metrics.imports):
                call_sites.append({
                    'caller': other_path,
                    'imports': [imp for imp in other_node.metrics.imports if file_path in imp or metrics.path in imp]
                })

        return {
            'path': file_path,
            'metrics': asdict(metrics),
            'fan_in': node.fan_in if node else 0,
            'fan_out': node.fan_out if node else 0,
            'parameter_routing': parameter_routing[:50],
            'call_sites': call_sites[:50],
            'side_effects': metrics.side_effects,
            'incoming_modules': list(node.incoming)[:20] if node else [],
            'outgoing_modules': list(node.outgoing)[:20] if node else []
        }