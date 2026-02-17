#!/usr/bin/env python3
"""
Component Extraction Script for GRID

Extracts reusable components, utilities, and algorithms from light_of_the_seven
and related research directories.

Usage:
    python tools/extract_components.py [--dry-run] [--verbose] [--target-dir DIR]
"""

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


class ComponentExtractor:
    def __init__(self, target_dir: str = "lib/extracted", dry_run: bool = False, verbose: bool = False):
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.verbose = verbose
        self.extracted_files = []

    def log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[EXTRACT] {message}")

    def ensure_dir(self, path: Path) -> None:
        """Ensure directory exists."""
        if not self.dry_run:
            path.mkdir(parents=True, exist_ok=True)

    def copy_file(self, src: Path, dst: Path) -> None:
        """Copy file to destination."""
        if self.dry_run:
            print(f"Would copy: {src} -> {dst}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            self.extracted_files.append(str(dst))
            self.log(f"Copied: {src} -> {dst}")

    def extract_react_components(self) -> dict[str, Any]:
        """Extract React components from hogwarts-visualizer."""
        components_dir = Path("research/experiments/hogwarts-visualizer/src/components/common")
        target_components_dir = self.target_dir / "components" / "react" / "hogwarts-theme"

        if not components_dir.exists():
            self.log(f"Components directory not found: {components_dir}")
            return {"status": "skipped", "reason": "directory not found"}

        self.ensure_dir(target_components_dir)

        # Components to extract with metadata
        components = [
            {
                "name": "WizardButton",
                "file": "WizardButton.tsx",
                "description": "Themed button component with house colors and variants",
                "category": "ui-components",
                "dependencies": ["React", "useHouse context"],
            },
            {
                "name": "HouseThemedCard",
                "file": "HouseThemedCard.tsx",
                "description": "Card component with house-themed borders and backgrounds",
                "category": "ui-components",
                "dependencies": ["React", "useHouse context"],
            },
            {
                "name": "SpellboundInput",
                "file": "SpellboundInput.tsx",
                "description": "Input component with house theming and validation states",
                "category": "ui-components",
                "dependencies": ["React", "useHouse context"],
            },
            {
                "name": "LoadingSpinner",
                "file": "LoadingSpinner.tsx",
                "description": "Animated loading spinner component",
                "category": "ui-components",
                "dependencies": ["React"],
            },
            {
                "name": "ErrorBoundary",
                "file": "ErrorBoundary.tsx",
                "description": "React error boundary for graceful error handling",
                "category": "error-handling",
                "dependencies": ["React"],
            },
        ]

        extracted = []
        for component in components:
            src_file = components_dir / component["file"]
            if src_file.exists():
                dst_file = target_components_dir / component["file"]
                self.copy_file(src_file, dst_file)
                extracted.append(component)
                self.log(f"Extracted React component: {component['name']}")
            else:
                self.log(f"Component file not found: {component['file']}")

        # Also extract the index file
        index_file = components_dir / "index.ts"
        if index_file.exists():
            self.copy_file(index_file, target_components_dir / "index.ts")

        return {
            "status": "success",
            "category": "react-components",
            "count": len(extracted),
            "components": extracted,
            "target_dir": str(target_components_dir),
        }

    def extract_algorithms(self) -> dict[str, Any]:
        """Extract algorithms and computational patterns."""
        algorithms_dir = self.target_dir / "algorithms"

        # Look for algorithm implementations in various directories
        potential_sources = [
            Path("research/experiments/hogwarts-visualizer/src/utils"),
            Path("src/grid/quantum"),
            Path("src/grid/intelligence"),
            Path("src/cognitive"),
        ]

        algorithms = []
        for source_dir in potential_sources:
            if source_dir.exists():
                self.ensure_dir(algorithms_dir / source_dir.name)

                # Look for Python files that might contain algorithms
                for py_file in source_dir.glob("*.py"):
                    if any(
                        keyword in py_file.name.lower()
                        for keyword in ["algorithm", "compute", "math", "pattern", "logic"]
                    ):
                        dst_file = algorithms_dir / source_dir.name / py_file.name
                        self.copy_file(py_file, dst_file)
                        algorithms.append(
                            {"name": py_file.stem, "file": str(dst_file), "source": str(py_file), "type": "algorithm"}
                        )

        return {
            "status": "success" if algorithms else "no-algorithms",
            "category": "algorithms",
            "count": len(algorithms),
            "algorithms": algorithms,
            "target_dir": str(algorithms_dir),
        }

    def extract_visualizations(self) -> dict[str, Any]:
        """Extract visualization components and utilities."""
        viz_dir = self.target_dir / "visualizations"

        # Look for visualization files
        potential_sources = [
            Path("research/experiments/hogwarts-visualizer/src/components/charts"),
            Path("archive/misc/datakit/visualizations"),
        ]

        visualizations = []
        for source_dir in potential_sources:
            if source_dir.exists():
                for file_path in source_dir.rglob("*"):
                    if file_path.is_file() and file_path.suffix in [".tsx", ".ts", ".js", ".py", ".html"]:
                        relative_path = file_path.relative_to(source_dir)
                        dst_file = viz_dir / source_dir.name / relative_path
                        self.copy_file(file_path, dst_file)
                        visualizations.append(
                            {
                                "name": file_path.stem,
                                "file": str(dst_file),
                                "type": file_path.suffix[1:],
                                "source": str(file_path),
                            }
                        )

        return {
            "status": "success" if visualizations else "no-visualizations",
            "category": "visualizations",
            "count": len(visualizations),
            "visualizations": visualizations,
            "target_dir": str(viz_dir),
        }

    def extract_educational_content(self) -> dict[str, Any]:
        """Extract educational examples and tutorials."""
        examples_dir = self.target_dir / "examples" / "educational"

        # Look for example files in research directories
        potential_sources = [
            Path("research/experiments"),
            Path("docs/examples"),
        ]

        examples = []
        for source_dir in potential_sources:
            if source_dir.exists():
                for file_path in source_dir.rglob("*"):
                    if file_path.is_file() and any(
                        keyword in file_path.name.lower() for keyword in ["example", "tutorial", "demo", "guide"]
                    ):
                        relative_path = file_path.relative_to(source_dir)
                        dst_file = examples_dir / source_dir.name / relative_path
                        self.copy_file(file_path, dst_file)
                        examples.append(
                            {
                                "name": file_path.stem,
                                "file": str(dst_file),
                                "type": file_path.suffix[1:],
                                "source": str(file_path),
                            }
                        )

        return {
            "status": "success" if examples else "no-examples",
            "category": "educational-content",
            "count": len(examples),
            "examples": examples,
            "target_dir": str(examples_dir),
        }

    def extract_configuration_templates(self) -> dict[str, Any]:
        """Extract configuration templates and schemas."""
        config_dir = self.target_dir / "config-templates"

        # Look for configuration files
        potential_patterns = [
            "**/*.config.*",
            "**/*.template.*",
            "**/config/**/*.json",
            "**/config/**/*.yaml",
            "**/schemas/**/*.json",
        ]

        templates = []
        for pattern in potential_patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.is_file():
                    dst_file = config_dir / file_path.name
                    self.copy_file(file_path, dst_file)
                    templates.append(
                        {
                            "name": file_path.stem,
                            "file": str(dst_file),
                            "type": file_path.suffix[1:],
                            "source": str(file_path),
                        }
                    )

        return {
            "status": "success" if templates else "no-templates",
            "category": "config-templates",
            "count": len(templates),
            "templates": templates,
            "target_dir": str(config_dir),
        }

    def run_extraction(self) -> dict[str, Any]:
        """Run all extraction operations."""
        print("🏗️  Starting GRID Component Extraction")
        print(f"Target directory: {self.target_dir}")
        print(f"Dry run: {self.dry_run}")
        print()

        results = {
            "react_components": self.extract_react_components(),
            "algorithms": self.extract_algorithms(),
            "visualizations": self.extract_visualizations(),
            "educational_content": self.extract_educational_content(),
            "configuration_templates": self.extract_configuration_templates(),
        }

        # Generate summary
        total_extracted = sum(result.get("count", 0) for result in results.values())

        print("\n📊 Extraction Summary:")
        print(f"Total files extracted: {total_extracted}")

        for category, result in results.items():
            status = result.get("status", "unknown")
            count = result.get("count", 0)
            status_icon = "✅" if status == "success" else "⚠️" if status in ["no-files", "skipped"] else "❌"
            print(f"  {status_icon} {category.replace('_', ' ').title()}: {count} files")

        # Save extraction report
        if not self.dry_run:
            report_file = self.target_dir / "extraction_report.json"
            with open(report_file, "w") as f:
                json.dump(
                    {
                        "extraction_results": results,
                        "total_files": total_extracted,
                        "extracted_files": self.extracted_files,
                        "timestamp": str(Path.cwd()),
                    },
                    f,
                    indent=2,
                )
            print(f"\n📄 Report saved to: {report_file}")

        return results


def main():
    parser = argparse.ArgumentParser(description="Extract reusable components from GRID research")
    parser.add_argument("--target-dir", default="lib/extracted", help="Target directory for extracted components")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be extracted without copying files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    extractor = ComponentExtractor(target_dir=args.target_dir, dry_run=args.dry_run, verbose=args.verbose)

    extractor.run_extraction()

    if args.dry_run:
        print("\n🔍 This was a dry run. Use without --dry-run to perform actual extraction.")


if __name__ == "__main__":
    main()
