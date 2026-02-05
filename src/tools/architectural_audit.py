"""
Architectural Divergence Analyzer
Analyzes modules for divergence from Mothership architectural pattern
"""

import ast
import re
from pathlib import Path
from typing import Any


class ArchitecturalDivergenceAnalyzer:
    """Analyzes modules for divergence from Mothership pattern."""

    MOTHERSHIP_PATTERN: dict[str, Any] = {
        "structure": ["routers", "services", "repositories"],
        "naming": {
            "router": r".*_router\.py$|routers/.*\.py$",
            "service": r".*_service\.py$|services/.*\.py$",
            "repository": r".*_repository\.py$|repositories/.*\.py$",
        },
        "imports": {
            "router": ["from application.mothership.repositories", "from application.mothership.services"],
            "service": ["from application.mothership.repositories", "from application.mothership.db"],
            "repository": ["from application.mothership.db"],
        },
        "exception_handling": "from application.exceptions import wrap_mothership_exception",
    }

    def __init__(self, reference_modules: list[str] | None = None):
        """
        Initialize analyzer.

        Args:
            reference_modules: List of reference module paths (e.g., Security/Mothership modules)
        """
        self.reference_modules = reference_modules or [
            "application/mothership/routers",
            "application/mothership/services",
            "application/mothership/repositories",
            "application/resonance/routers",
            "application/resonance/services",
            "application/resonance/repositories",
        ]

    def analyze_module(self, module_path: Path) -> dict[str, Any]:
        """
        Analyze a module for architectural divergence.

        Args:
            module_path: Path to module file or directory

        Returns:
            Dictionary with divergence analysis
        """
        divergence_score = 0.0
        issues: list[str] = []

        if module_path.is_dir():
            # Analyze directory structure
            structure_issues = self._analyze_directory_structure(module_path)
            if structure_issues:
                divergence_score += 0.4
                issues.extend(structure_issues)
        else:
            # Analyze single file
            if not module_path.exists():
                return {
                    "module": str(module_path),
                    "divergence_score": 1.0,
                    "issues": ["Module file does not exist"],
                    "severity": "high",
                    "migration_path": [],
                }

            # Check if file is in expected location
            path_str = str(module_path)
            if not any(pattern in path_str for pattern in ["routers", "services", "repositories"]):
                divergence_score += 0.2
                issues.append("File not in routers/services/repositories structure")

            # Analyze file content
            try:
                with open(module_path, encoding="utf-8") as f:
                    content = f.read()

                # Check naming conventions
                naming_issues = self._check_naming_conventions(module_path, content)
                if naming_issues:
                    divergence_score += 0.2
                    issues.extend(naming_issues)

                # Check import patterns
                import_issues = self._check_import_patterns(content)
                if import_issues:
                    divergence_score += 0.3
                    issues.extend(import_issues)

                # Check exception handling
                exception_issues = self._check_exception_handling(content)
                if exception_issues:
                    divergence_score += 0.1
                    issues.extend(exception_issues)

                # Check AST structure
                try:
                    tree = ast.parse(content)
                    ast_issues = self._check_ast_structure(tree, module_path)
                    if ast_issues:
                        divergence_score += 0.2
                        issues.extend(ast_issues)
                except SyntaxError:
                    issues.append("Syntax error in file - cannot parse AST")
                    divergence_score += 0.1

            except Exception as e:
                issues.append(f"Error analyzing file: {str(e)}")
                divergence_score += 0.5

        severity = "high" if divergence_score > 0.7 else "medium" if divergence_score > 0.4 else "low"

        return {
            "module": str(module_path),
            "divergence_score": min(divergence_score, 1.0),
            "issues": issues,
            "severity": severity,
        }

    def _analyze_directory_structure(self, directory: Path) -> list[str]:
        """Analyze directory structure for Mothership pattern."""
        issues: list[str] = []
        expected_dirs: set[str] = set(self.MOTHERSHIP_PATTERN["structure"])
        actual_dirs: set[str] = {d.name for d in directory.iterdir() if d.is_dir()}

        missing_dirs: set[str] = expected_dirs - actual_dirs
        if missing_dirs:
            issues.append(f"Missing directories: {', '.join(missing_dirs)}")

        # Check for __init__.py files
        for expected_dir in expected_dirs:
            init_file = directory / expected_dir / "__init__.py"
            if not init_file.exists():
                issues.append(f"Missing __init__.py in {expected_dir}/")

        return issues

    def _check_naming_conventions(self, module_path: Path, content: str) -> list[str]:
        """Check if file follows Mothership naming conventions."""
        issues: list[str] = []
        filename = module_path.name

        # Check if filename matches expected patterns
        is_router = bool(re.search(self.MOTHERSHIP_PATTERN["naming"]["router"], filename))
        is_service = bool(re.search(self.MOTHERSHIP_PATTERN["naming"]["service"], filename))
        is_repository = bool(re.search(self.MOTHERSHIP_PATTERN["naming"]["repository"], filename))

        if not (is_router or is_service or is_repository):
            # Check if it's in the right directory
            path_str = str(module_path)
            if "routers" in path_str and not is_router:
                issues.append("File in routers/ but doesn't match router naming pattern")
            elif "services" in path_str and not is_service:
                issues.append("File in services/ but doesn't match service naming pattern")
            elif "repositories" in path_str and not is_repository:
                issues.append("File in repositories/ but doesn't match repository naming pattern")

        return issues

    def _check_import_patterns(self, content: str) -> list[str]:
        """Check if imports follow Mothership patterns."""
        issues: list[str] = []

        # Check for Mothership imports
        any(pattern in content for pattern in ["from application.mothership", "from application.exceptions"])

        # Check for direct database access (should go through repositories)
        if "from sqlalchemy" in content or "import sqlalchemy" in content:
            if "repository" not in content.lower():
                issues.append("Direct database access detected - should use repositories")

        # Check for missing exception wrapping
        if "except" in content and "wrap_mothership_exception" not in content:
            if "ApplicationError" not in content:
                issues.append("Exception handling doesn't use Mothership exception wrapping")

        return issues

    def _check_exception_handling(self, content: str) -> list[str]:
        """Check exception handling patterns."""
        issues: list[str] = []

        if "except" in content:
            if self.MOTHERSHIP_PATTERN["exception_handling"] not in content:
                issues.append("Missing Mothership exception wrapping import")

        return issues

    def _check_ast_structure(self, tree: ast.AST, module_path: Path) -> list[str]:
        """Check AST structure for Mothership patterns."""
        issues: list[str] = []

        # Check for class definitions
        classes: list[ast.ClassDef] = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

        # Check if classes follow naming conventions
        for cls in classes:
            if "router" in str(module_path).lower():
                if not cls.name.endswith("Router"):
                    issues.append(f"Router class '{cls.name}' should end with 'Router'")
            elif "service" in str(module_path).lower():
                if not cls.name.endswith("Service"):
                    issues.append(f"Service class '{cls.name}' should end with 'Service'")
            elif "repository" in str(module_path).lower():
                if not cls.name.endswith("Repository"):
                    issues.append(f"Repository class '{cls.name}' should end with 'Repository'")

        return issues

    def generate_migration_path(self, analysis: dict[str, Any]) -> list[str]:
        """
        Generate automated migration path for a module.

        Args:
            analysis: Analysis result from analyze_module

        Returns:
            List of migration steps
        """
        steps: list[str] = []
        module_path = Path(analysis["module"])

        # Determine target domain from path
        target_domain = self._extract_domain_from_path(module_path)

        if "Missing directories" in str(analysis["issues"]):
            steps.append(f"1. Create routers/ directory in {target_domain}/")
            steps.append(f"2. Create services/ directory in {target_domain}/")
            steps.append(f"3. Create repositories/ directory in {target_domain}/")
            steps.append("4. Create __init__.py files in each directory")

        if "naming" in str(analysis["issues"]).lower():
            steps.append("5. Rename files to match Mothership conventions")
            if "router" in str(module_path).lower():
                steps.append("   - Ensure router files end with _router.py or are in routers/")
            elif "service" in str(module_path).lower():
                steps.append("   - Ensure service files end with _service.py or are in services/")
            elif "repository" in str(module_path).lower():
                steps.append("   - Ensure repository files end with _repository.py or are in repositories/")

        if "import" in str(analysis["issues"]).lower() or "database" in str(analysis["issues"]).lower():
            steps.append("6. Update imports to use Mothership patterns")
            steps.append("   - Add: from application.mothership.repositories import ...")
            steps.append("   - Add: from application.exceptions import wrap_mothership_exception")
            steps.append("   - Remove direct database access, use repositories instead")

        if "exception" in str(analysis["issues"]).lower():
            steps.append("7. Add exception wrapping")
            steps.append("   - Import: from application.exceptions import wrap_mothership_exception")
            steps.append("   - Wrap exceptions in try/except blocks")

        if "class" in str(analysis["issues"]).lower():
            steps.append("8. Rename classes to match Mothership conventions")
            steps.append("   - Router classes: *Router")
            steps.append("   - Service classes: *Service")
            steps.append("   - Repository classes: *Repository")

        return steps

    def _extract_domain_from_path(self, path: Path) -> str:
        """Extract domain name from path."""
        path_str = str(path)

        # Try to extract domain from application/ path
        if "application/" in path_str:
            parts = path_str.split("application/")
            if len(parts) > 1:
                domain = parts[1].split("/")[0]
                return f"application/{domain}"

        # Try to extract from tools/ path
        if "tools/" in path_str:
            parts = path_str.split("tools/")
            if len(parts) > 1:
                domain = parts[1].split("/")[0]
                return f"application/{domain}"  # Suggest migration to application/

        return "application/<domain>"

    def analyze_codebase(self, base_path: Path, patterns: list[str] | None = None) -> list[dict[str, Any]]:
        """
        Analyze entire codebase for architectural divergence.

        Args:
            base_path: Base path to analyze
            patterns: Optional list of glob patterns to match files

        Returns:
            List of analysis results, sorted by divergence score
        """
        if patterns is None:
            patterns = ["**/*.py"]

        results: list[dict[str, Any]] = []

        for pattern in patterns:
            for file_path in base_path.glob(pattern):
                if file_path.is_file():
                    analysis = self.analyze_module(file_path)
                    if analysis["divergence_score"] > 0:
                        migration_path = self.generate_migration_path(analysis)
                        analysis["migration_path"] = migration_path
                        results.append(analysis)

        # Sort by divergence score (highest first)
        results.sort(key=lambda x: x["divergence_score"], reverse=True)

        return results


def main() -> None:
    """Example usage."""
    analyzer = ArchitecturalDivergenceAnalyzer()

    # Analyze tools/ directory
    tools_path = Path("tools")
    if tools_path.exists():
        print(f"Analyzing {tools_path}...")
        results = analyzer.analyze_codebase(tools_path)

        print(f"\nFound {len(results)} modules with architectural divergence:\n")
        for result in results[:10]:  # Show top 10
            print(f"Module: {result['module']}")
            print(f"  Divergence Score: {result['divergence_score']:.2f}")
            print(f"  Severity: {result['severity']}")
            print(f"  Issues: {len(result['issues'])}")
            if result.get("migration_path"):
                print(f"  Migration Steps: {len(result['migration_path'])}")
            print()


if __name__ == "__main__":
    main()
