"""
Multi-Review-Marking Tool

A comprehensive, multi-dimensional code analysis and review system that provides
structured remarks across multiple evaluation criteria. Designed for systematic
code review with actionable feedback.

Features:
- Multi-dimensional analysis (logic, performance, security, maintainability, etc.)
- Structured severity-based marking system
- Actionable remarks with specific recommendations
- Historical tracking and trend analysis
- Integration with existing code review workflows
"""

from __future__ import annotations

import ast
import inspect
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple, Callable
from datetime import datetime
import json


class ReviewSeverity(Enum):
    """Severity levels for review remarks"""
    BLOCKER = "blocker"      # Must fix immediately - breaks functionality
    CRITICAL = "critical"    # Critical issue - severe impact
    MAJOR = "major"         # Major issue - significant impact
    MINOR = "minor"         # Minor issue - small impact
    INFO = "info"           # Informational - improvement opportunity
    POSITIVE = "positive"   # Positive finding - good practice


class ReviewDimension(Enum):
    """Analysis dimensions for comprehensive review"""
    LOGIC = "logic"                    # Logical correctness and behavior
    PERFORMANCE = "performance"        # Performance and efficiency
    SECURITY = "security"             # Security vulnerabilities
    MAINTAINABILITY = "maintainability" # Code maintainability
    RELIABILITY = "reliability"        # Error handling and robustness
    ARCHITECTURE = "architecture"     # Architectural decisions
    TESTING = "testing"              # Test coverage and quality
    DOCUMENTATION = "documentation"   # Documentation completeness
    COMPLIANCE = "compliance"         # Standards and conventions
    INNOVATION = "innovation"         # Innovative approaches


class RemarkType(Enum):
    """Types of remarks that can be made"""
    BUG = "bug"                       # Code bug or error
    VULNERABILITY = "vulnerability"    # Security vulnerability
    PERFORMANCE_ISSUE = "performance"  # Performance problem
    CODE_SMELL = "smell"               # Code quality issue
    IMPROVEMENT = "improvement"        # General improvement
    BEST_PRACTICE = "practice"         # Best practice violation
    ARCHITECTURAL = "architectural"    # Architectural concern
    COMPLIANCE = "compliance"          # Standards violation
    INNOVATION = "innovation"          # Innovative solution
    POSITIVE = "positive"              # Positive finding


@dataclass
class CodeLocation:
    """Specific location in code for a remark"""
    file_path: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    code_snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "function_name": self.function_name,
            "class_name": self.class_name,
            "code_snippet": self.code_snippet
        }


@dataclass
class ReviewRemark:
    """A single remark from the review process"""
    remark_id: str
    severity: ReviewSeverity
    dimension: ReviewDimension
    remark_type: RemarkType
    title: str
    description: str
    location: CodeLocation
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    related_remarks: List[str] = field(default_factory=list)
    confidence_score: float = 1.0  # 0.0 to 1.0
    effort_estimate: str = "unknown"  # "trivial", "minor", "moderate", "major", "complex"
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    reviewer: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "remark_id": self.remark_id,
            "severity": self.severity.value,
            "dimension": self.dimension.value,
            "remark_type": self.remark_type.value,
            "title": self.title,
            "description": self.description,
            "location": self.location.to_dict(),
            "evidence": self.evidence,
            "recommendations": self.recommendations,
            "related_remarks": self.related_remarks,
            "confidence_score": self.confidence_score,
            "effort_estimate": self.effort_estimate,
            "tags": list(self.tags),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "reviewer": self.reviewer
        }


@dataclass
class ReviewSummary:
    """Summary statistics for a review session"""
    total_remarks: int = 0
    severity_breakdown: Dict[ReviewSeverity, int] = field(default_factory=dict)
    dimension_breakdown: Dict[ReviewDimension, int] = field(default_factory=dict)
    type_breakdown: Dict[RemarkType, int] = field(default_factory=dict)
    effort_distribution: Dict[str, int] = field(default_factory=dict)
    confidence_distribution: Dict[str, int] = field(default_factory=dict)
    top_issues: List[str] = field(default_factory=list)
    positive_findings: List[str] = field(default_factory=list)
    review_duration: float = 0.0
    files_analyzed: int = 0
    lines_analyzed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_remarks": self.total_remarks,
            "severity_breakdown": {k.value: v for k, v in self.severity_breakdown.items()},
            "dimension_breakdown": {k.value: v for k, v in self.dimension_breakdown.items()},
            "type_breakdown": {k.value: v for k, v in self.type_breakdown.items()},
            "effort_distribution": self.effort_distribution,
            "confidence_distribution": self.confidence_distribution,
            "top_issues": self.top_issues,
            "positive_findings": self.positive_findings,
            "review_duration": self.review_duration,
            "files_analyzed": self.files_analyzed,
            "lines_analyzed": self.lines_analyzed
        }


@dataclass
class ReviewConfiguration:
    """Configuration for the review process"""
    dimensions: Set[ReviewDimension] = field(default_factory=lambda: set(ReviewDimension))
    min_confidence: float = 0.3
    include_positive_findings: bool = True
    max_remarks_per_file: int = 50
    enable_ast_analysis: bool = True
    enable_pattern_matching: bool = True
    custom_rules: Dict[str, Any] = field(default_factory=dict)
    exclude_patterns: List[str] = field(default_factory=list)
    include_patterns: List[str] = field(default_factory=list)


class BaseReviewAnalyzer:
    """Base class for review analyzers"""

    def __init__(self, config: ReviewConfiguration):
        self.config = config

    def analyze_file(self, file_path: Path, content: str) -> List[ReviewRemark]:
        """Analyze a single file and return remarks"""
        raise NotImplementedError

    def analyze_code(self, code: str, file_path: Path) -> List[ReviewRemark]:
        """Analyze code content"""
        raise NotImplementedError

    def _create_remark(self, severity: ReviewSeverity, dimension: ReviewDimension,
                      remark_type: RemarkType, title: str, description: str,
                      location: CodeLocation, **kwargs) -> ReviewRemark:
        """Create a standardized remark"""
        remark_id = f"{dimension.value}_{remark_type.value}_{hash(title + str(location.line_number)) % 10000:04d}"

        return ReviewRemark(
            remark_id=remark_id,
            severity=severity,
            dimension=dimension,
            remark_type=remark_type,
            title=title,
            description=description,
            location=location,
            **kwargs
        )


class LogicAnalyzer(BaseReviewAnalyzer):
    """Analyzes logical correctness and behavior"""

    def analyze_file(self, file_path: Path, content: str) -> List[ReviewRemark]:
        remarks = []

        if not self.config.enable_ast_analysis:
            return remarks

        try:
            tree = ast.parse(content, filename=str(file_path))
            remarks.extend(self._analyze_ast(tree, file_path, content))
        except SyntaxError as e:
            remarks.append(self._create_remark(
                ReviewSeverity.CRITICAL, ReviewDimension.LOGIC, RemarkType.BUG,
                "Syntax Error", f"File contains syntax error: {e.msg}",
                CodeLocation(str(file_path), e.lineno, e.offset)
            ))

        remarks.extend(self._analyze_logic_patterns(content, file_path))
        return remarks

    def _analyze_ast(self, tree: ast.AST, file_path: Path, content: str) -> List[ReviewRemark]:
        """Analyze AST for logical issues"""
        remarks = []
        lines = content.split('\n')

        class LogicVisitor(ast.NodeVisitor):
            def __init__(self, analyzer, file_path, lines):
                self.analyzer = analyzer
                self.file_path = file_path
                self.lines = lines
                self.remarks = []

            def visit_Compare(self, node):
                # Check for potential comparison issues
                if isinstance(node.left, ast.Name) and len(node.comparators) == 1:
                    comp = node.comparators[0]
                    if isinstance(comp, ast.Name) and node.left.id == comp.id:
                        # Self-comparison like x == x
                        line_content = self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else ""
                        self.remarks.append(self.analyzer._create_remark(
                            ReviewSeverity.MAJOR, ReviewDimension.LOGIC, RemarkType.BUG,
                            "Self Comparison", f"Comparing {node.left.id} with itself",
                            CodeLocation(str(self.file_path), node.lineno, node.col_offset, code_snippet=line_content.strip())
                        ))
                self.generic_visit(node)

            def visit_BinOp(self, node):
                # Check for potential division by zero
                if isinstance(node.op, ast.Div) and isinstance(node.right, ast.Num) and node.right.n == 0:
                    line_content = self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else ""
                    self.remarks.append(self.analyzer._create_remark(
                        ReviewSeverity.CRITICAL, ReviewDimension.LOGIC, RemarkType.BUG,
                        "Division by Zero", "Explicit division by zero detected",
                        CodeLocation(str(self.file_path), node.lineno, node.col_offset, code_snippet=line_content.strip())
                    ))
                self.generic_visit(node)

        visitor = LogicVisitor(self, file_path, lines)
        visitor.visit(tree)
        return visitor.remarks

    def _analyze_logic_patterns(self, content: str, file_path: Path) -> List[ReviewRemark]:
        """Analyze code patterns for logical issues"""
        remarks = []
        lines = content.split('\n')

        # Check for TODO/FIXME comments
        for i, line in enumerate(lines, 1):
            if 'TODO' in line.upper() or 'FIXME' in line.upper():
                remarks.append(self._create_remark(
                    ReviewSeverity.INFO, ReviewDimension.LOGIC, RemarkType.IMPROVEMENT,
                    "TODO/FIXME Comment", "Unresolved TODO or FIXME comment found",
                    CodeLocation(str(file_path), i, code_snippet=line.strip()),
                    recommendations=["Address the TODO/FIXME comment or remove if no longer relevant"]
                ))

        return remarks


class SecurityAnalyzer(BaseReviewAnalyzer):
    """Analyzes security vulnerabilities"""

    def analyze_file(self, file_path: Path, content: str) -> List[ReviewRemark]:
        remarks = []

        # Check for common security issues
        remarks.extend(self._check_hardcoded_secrets(content, file_path))
        remarks.extend(self._check_injection_vulnerabilities(content, file_path))
        remarks.extend(self._check_access_control(content, file_path))

        return remarks

    def _check_hardcoded_secrets(self, content: str, file_path: Path) -> List[ReviewRemark]:
        """Check for hardcoded secrets and credentials"""
        remarks = []
        lines = content.split('\n')

        # Patterns for potential secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, description in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    remarks.append(self._create_remark(
                        ReviewSeverity.CRITICAL, ReviewDimension.SECURITY, RemarkType.VULNERABILITY,
                        "Hardcoded Secret", f"{description} detected in code",
                        CodeLocation(str(file_path), i, code_snippet=line.strip()),
                        recommendations=[
                            "Move secrets to environment variables",
                            "Use a secrets management system",
                            "Never commit secrets to version control"
                        ]
                    ))

        return remarks

    def _check_injection_vulnerabilities(self, content: str, file_path: Path) -> List[ReviewRemark]:
        """Check for injection vulnerabilities"""
        remarks = []
        lines = content.split('\n')

        # Check for dangerous string formatting
        for i, line in enumerate(lines, 1):
            if re.search(r'exec\s*\(|eval\s*\(|os\.system\s*\(', line):
                remarks.append(self._create_remark(
                    ReviewSeverity.CRITICAL, ReviewDimension.SECURITY, RemarkType.VULNERABILITY,
                    "Code Injection Risk", "Use of exec/eval/system detected",
                    CodeLocation(str(file_path), i, code_snippet=line.strip()),
                    recommendations=[
                        "Use subprocess with proper argument passing",
                        "Validate and sanitize all inputs",
                        "Consider using safer alternatives"
                    ]
                ))

        return remarks

    def _check_access_control(self, content: str, file_path: Path) -> List[ReviewRemark]:
        """Check for access control issues"""
        remarks = []
        lines = content.split('\n')

        # Check for missing authentication
        for i, line in enumerate(lines, 1):
            if '@app.' in line and 'auth' not in content[max(0, i-10):i+10].lower():
                remarks.append(self._create_remark(
                    ReviewSeverity.MAJOR, ReviewDimension.SECURITY, RemarkType.VULNERABILITY,
                    "Potential Missing Authentication", "Endpoint without apparent authentication",
                    CodeLocation(str(file_path), i, code_snippet=line.strip()),
                    recommendations=["Ensure proper authentication is implemented"]
                ))

        return remarks


class PerformanceAnalyzer(BaseReviewAnalyzer):
    """Analyzes performance and efficiency issues"""

    def analyze_file(self, file_path: Path, content: str) -> List[ReviewRemark]:
        remarks = []

        # Check for performance anti-patterns
        remarks.extend(self._check_loops(content, file_path))
        remarks.extend(self._check_memory_usage(content, file_path))
        remarks.extend(self._check_inefficient_operations(content, file_path))

        return remarks

    def _check_loops(self, content: str, file_path: Path) -> List[ReviewRemark]:
        """Check for inefficient loops"""
        remarks = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for nested loops
            if 'for ' in line and any('for ' in lines[j] for j in range(max(0, i-5), min(len(lines), i+5)) if j != i):
                remarks.append(self._create_remark(
                    ReviewSeverity.MINOR, ReviewDimension.PERFORMANCE, RemarkType.PERFORMANCE_ISSUE,
                    "Nested Loops", "Consider optimizing nested loop performance",
                    CodeLocation(str(file_path), i, code_snippet=line.strip()),
                    recommendations=["Consider algorithm optimization", "Use more efficient data structures"]
                ))

        return remarks

    def _check_memory_usage(self, content: str, file_path: Path) -> List[ReviewRemark]:
        """Check for potential memory issues"""
        remarks = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for large data structures
            if re.search(r'list\([^)]*\)\s*\*\s*\d{3,}', line) or re.search(r'\[.*\]\s*\*\s*\d{3,}', line):
                remarks.append(self._create_remark(
                    ReviewSeverity.MAJOR, ReviewDimension.PERFORMANCE, RemarkType.PERFORMANCE_ISSUE,
                    "Large Data Structure Creation", "Creating potentially large data structures",
                    CodeLocation(str(file_path), i, code_snippet=line.strip()),
                    recommendations=["Use generators for large datasets", "Consider memory-efficient alternatives"]
                ))

        return remarks

    def _check_inefficient_operations(self, content: str, file_path: Path) -> List[ReviewRemark]:
        """Check for inefficient operations"""
        remarks = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # Check for string concatenation in loops
            if '+' in line and any('for ' in lines[j] for j in range(max(0, i-3), i)):
                context = '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                if 'str' in context or '"' in context or "'" in context:
                    remarks.append(self._create_remark(
                        ReviewSeverity.MINOR, ReviewDimension.PERFORMANCE, RemarkType.PERFORMANCE_ISSUE,
                        "String Concatenation in Loop", "Inefficient string concatenation in loop",
                        CodeLocation(str(file_path), i, code_snippet=line.strip()),
                        recommendations=["Use ''.join() or list comprehension", "Use io.StringIO for large strings"]
                    ))

        return remarks


class MultiReviewMarker:
    """Main class for multi-dimensional code review and remark generation"""

    def __init__(self, config: Optional[ReviewConfiguration] = None):
        self.config = config or ReviewConfiguration()
        self.analyzers: Dict[ReviewDimension, BaseReviewAnalyzer] = {}

        # Initialize analyzers
        if ReviewDimension.LOGIC in self.config.dimensions or not self.config.dimensions:
            self.analyzers[ReviewDimension.LOGIC] = LogicAnalyzer(self.config)

        if ReviewDimension.SECURITY in self.config.dimensions or not self.config.dimensions:
            self.analyzers[ReviewDimension.SECURITY] = SecurityAnalyzer(self.config)

        if ReviewDimension.PERFORMANCE in self.config.dimensions or not self.config.dimensions:
            self.analyzers[ReviewDimension.PERFORMANCE] = PerformanceAnalyzer(self.config)

    def review_file(self, file_path: Path) -> List[ReviewRemark]:
        """Review a single file"""
        if not file_path.exists():
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Skip binary files
            return []

        remarks = []
        for analyzer in self.analyzers.values():
            try:
                file_remarks = analyzer.analyze_file(file_path, content)
                remarks.extend(file_remarks)
            except Exception as e:
                # Create a remark about the analysis error
                error_remark = ReviewRemark(
                    remark_id=f"analysis_error_{hash(str(file_path)) % 1000:03d}",
                    severity=ReviewSeverity.INFO,
                    dimension=ReviewDimension.RELIABILITY,
                    remark_type=RemarkType.BUG,
                    title="Analysis Error",
                    description=f"Failed to analyze file: {str(e)}",
                    location=CodeLocation(str(file_path)),
                    confidence_score=1.0
                )
                remarks.append(error_remark)

        return remarks[:self.config.max_remarks_per_file]

    def review_directory(self, directory_path: Path) -> Tuple[List[ReviewRemark], ReviewSummary]:
        """Review all files in a directory"""
        start_time = time.time()

        all_remarks = []
        files_analyzed = 0
        lines_analyzed = 0

        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and self._should_analyze_file(file_path):
                remarks = self.review_file(file_path)
                all_remarks.extend(remarks)
                files_analyzed += 1

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines_analyzed += len(f.readlines())
                except:
                    pass

        review_duration = time.time() - start_time
        summary = self._generate_summary(all_remarks, review_duration, files_analyzed, lines_analyzed)

        return all_remarks, summary

    def review_code_snippet(self, code: str, file_path: Optional[Path] = None) -> List[ReviewRemark]:
        """Review a code snippet"""
        fake_path = file_path or Path("snippet.py")
        remarks = []

        for analyzer in self.analyzers.values():
            try:
                snippet_remarks = analyzer.analyze_file(fake_path, code)
                remarks.extend(snippet_remarks)
            except Exception as e:
                remarks.append(ReviewRemark(
                    remark_id=f"snippet_error_{hash(code[:50]) % 1000:03d}",
                    severity=ReviewSeverity.INFO,
                    dimension=ReviewDimension.RELIABILITY,
                    remark_type=RemarkType.BUG,
                    title="Snippet Analysis Error",
                    description=f"Failed to analyze code snippet: {str(e)}",
                    location=CodeLocation("snippet"),
                    confidence_score=1.0
                ))

        return remarks

    def _should_analyze_file(self, file_path: Path) -> bool:
        """Determine if a file should be analyzed"""
        # Check exclude patterns
        for pattern in self.config.exclude_patterns:
            if file_path.match(pattern):
                return False

        # Check include patterns (if specified)
        if self.config.include_patterns:
            for pattern in self.config.include_patterns:
                if file_path.match(pattern):
                    break
            else:
                return False

        # Default file types to analyze
        if file_path.suffix in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']:
            return True

        return False

    def _generate_summary(self, remarks: List[ReviewRemark], duration: float,
                         files: int, lines: int) -> ReviewSummary:
        """Generate a summary of the review"""
        summary = ReviewSummary(
            total_remarks=len(remarks),
            review_duration=duration,
            files_analyzed=files,
            lines_analyzed=lines
        )

        # Count by severity
        for remark in remarks:
            summary.severity_breakdown[remark.severity] = \
                summary.severity_breakdown.get(remark.severity, 0) + 1

        # Count by dimension
        for remark in remarks:
            summary.dimension_breakdown[remark.dimension] = \
                summary.dimension_breakdown.get(remark.dimension, 0) + 1

        # Count by type
        for remark in remarks:
            summary.type_breakdown[remark.remark_type] = \
                summary.type_breakdown.get(remark.remark_type, 0) + 1

        # Effort distribution
        for remark in remarks:
            summary.effort_distribution[remark.effort_estimate] = \
                summary.effort_distribution.get(remark.effort_estimate, 0) + 1

        # Confidence distribution
        for remark in remarks:
            conf_range = f"{int(remark.confidence_score * 10) * 10}%"
            summary.confidence_distribution[conf_range] = \
                summary.confidence_distribution.get(conf_range, 0) + 1

        # Top issues (by severity)
        blocker_critical = [r for r in remarks if r.severity in [ReviewSeverity.BLOCKER, ReviewSeverity.CRITICAL]]
        summary.top_issues = [r.title for r in blocker_critical[:5]]

        # Positive findings
        positive = [r for r in remarks if r.severity == ReviewSeverity.POSITIVE]
        summary.positive_findings = [r.title for r in positive[:5]]

        return summary

    def export_results(self, remarks: List[ReviewRemark], summary: ReviewSummary,
                      output_path: Path, format: str = "json") -> None:
        """Export review results to file"""
        if format == "json":
            data = {
                "summary": summary.to_dict(),
                "remarks": [r.to_dict() for r in remarks]
            }
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif format == "markdown":
            self._export_markdown(remarks, summary, output_path)

    def _export_markdown(self, remarks: List[ReviewRemark], summary: ReviewSummary,
                        output_path: Path) -> None:
        """Export results in markdown format"""
        with open(output_path, 'w') as f:
            f.write("# Code Review Report\n\n")

            # Summary section
            f.write("## Summary\n\n")
            f.write(f"- **Total Remarks:** {summary.total_remarks}\n")
            f.write(f"- **Files Analyzed:** {summary.files_analyzed}\n")
            f.write(f"- **Lines Analyzed:** {summary.lines_analyzed}\n")
            f.write(f"- **Review Duration:** {summary.review_duration:.2f}s\n\n")

            # Severity breakdown
            f.write("### Severity Breakdown\n\n")
            for severity, count in summary.severity_breakdown.items():
                f.write(f"- **{severity.value.title()}:** {count}\n")
            f.write("\n")

            # Top issues
            if summary.top_issues:
                f.write("### Top Issues\n\n")
                for issue in summary.top_issues:
                    f.write(f"- {issue}\n")
                f.write("\n")

            # Detailed remarks
            f.write("## Detailed Remarks\n\n")

            # Group by severity
            for severity in [ReviewSeverity.BLOCKER, ReviewSeverity.CRITICAL, ReviewSeverity.MAJOR,
                           ReviewSeverity.MINOR, ReviewSeverity.INFO, ReviewSeverity.POSITIVE]:
                severity_remarks = [r for r in remarks if r.severity == severity]
                if severity_remarks:
                    f.write(f"### {severity.value.title()} Issues\n\n")

                    for remark in severity_remarks:
                        f.write(f"#### {remark.title}\n\n")
                        f.write(f"**File:** {remark.location.file_path}")
                        if remark.location.line_number:
                            f.write(f":{remark.location.line_number}")
                        f.write(f"\n\n**Description:** {remark.description}\n\n")

                        if remark.recommendations:
                            f.write("**Recommendations:**\n")
                            for rec in remark.recommendations:
                                f.write(f"- {rec}\n")
                            f.write("\n")

                        if remark.evidence:
                            f.write("**Evidence:**\n")
                            for ev in remark.evidence:
                                f.write(f"- {ev}\n")
                            f.write("\n")

                        f.write("---\n\n")


def create_comprehensive_review_config() -> ReviewConfiguration:
    """Create a comprehensive review configuration"""
    return ReviewConfiguration(
        dimensions=set(ReviewDimension),
        min_confidence=0.5,
        include_positive_findings=True,
        max_remarks_per_file=100,
        enable_ast_analysis=True,
        enable_pattern_matching=True,
        exclude_patterns=[
            "**/__pycache__/**",
            "**/node_modules/**",
            "**/.git/**",
            "**/build/**",
            "**/dist/**",
            "**/*.min.js",
            "**/*.pyc"
        ],
        include_patterns=[
            "**/*.py",
            "**/*.js",
            "**/*.ts",
            "**/*.java"
        ]
    )


# Convenience functions
def review_file(file_path: str, config: Optional[ReviewConfiguration] = None) -> List[ReviewRemark]:
    """Convenience function to review a single file"""
    marker = MultiReviewMarker(config or create_comprehensive_review_config())
    return marker.review_file(Path(file_path))


def review_directory(directory_path: str, config: Optional[ReviewConfiguration] = None) -> Tuple[List[ReviewRemark], ReviewSummary]:
    """Convenience function to review a directory"""
    marker = MultiReviewMarker(config or create_comprehensive_review_config())
    return marker.review_directory(Path(directory_path))


def review_code_snippet(code: str, config: Optional[ReviewConfiguration] = None) -> List[ReviewRemark]:
    """Convenience function to review a code snippet"""
    marker = MultiReviewMarker(config or create_comprehensive_review_config())
    return marker.review_code_snippet(code)


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python multi_review_marker.py <path>")
        sys.exit(1)

    path = Path(sys.argv[1])

    if path.is_file():
        remarks = review_file(str(path))
    elif path.is_dir():
        remarks, summary = review_directory(str(path))
        print(f"Review completed: {summary.total_remarks} remarks found")
    else:
        print(f"Path not found: {path}")
        sys.exit(1)

    # Print results
    for remark in remarks[:10]:  # Show first 10
        print(f"{remark.severity.value.upper()}: {remark.title}")
        print(f"  {remark.location.file_path}:{remark.location.line_number}")
        print(f"  {remark.description}")
        print()
