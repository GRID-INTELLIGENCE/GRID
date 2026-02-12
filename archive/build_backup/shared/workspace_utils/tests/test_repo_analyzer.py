"""
Tests for repository analyzer.
"""

import pytest
from pathlib import Path
from workspace_utils.repo_analyzer import RepositoryAnalyzer, FileMetrics


def test_repo_analyzer_initialization(temp_dir: Path):
    """Test RepositoryAnalyzer initialization."""
    output_dir = temp_dir / "output"
    analyzer = RepositoryAnalyzer(
        root_path=str(temp_dir),
        output_dir=str(output_dir)
    )
    
    assert analyzer.root_path == temp_dir.resolve()
    assert analyzer.output_dir == output_dir.resolve()
    assert analyzer.max_depth == 6


def test_repo_analyzer_is_sensitive_file(temp_dir: Path):
    """Test sensitive file detection."""
    analyzer = RepositoryAnalyzer(str(temp_dir), str(temp_dir / "out"))
    
    # Create sensitive file
    env_file = temp_dir / ".env"
    env_file.write_text("SECRET_KEY=test")
    
    assert analyzer.is_sensitive_file(env_file) is True
    
    # Create normal file
    normal_file = temp_dir / "normal.py"
    normal_file.write_text("print('hello')")
    
    assert analyzer.is_sensitive_file(normal_file) is False


def test_repo_analyzer_should_exclude(temp_dir: Path):
    """Test exclusion pattern handling."""
    analyzer = RepositoryAnalyzer(str(temp_dir), str(temp_dir / "out"))
    
    # Should exclude __pycache__
    pycache_dir = temp_dir / "__pycache__"
    pycache_dir.mkdir()
    
    assert analyzer.should_exclude(pycache_dir, depth=0) is True
    
    # Should not exclude normal directory
    normal_dir = temp_dir / "normal"
    normal_dir.mkdir()
    
    assert analyzer.should_exclude(normal_dir, depth=0) is False


def test_repo_analyzer_get_file_language(sample_python_file: Path):
    """Test file language detection."""
    analyzer = RepositoryAnalyzer(
        str(sample_python_file.parent),
        str(sample_python_file.parent / "out")
    )
    
    assert analyzer.get_file_language(sample_python_file) == "Python"
    assert analyzer.get_file_language(sample_python_file.parent / "test.js") == "JavaScript"
    assert analyzer.get_file_language(sample_python_file.parent / "unknown.xyz") is None


def test_repo_analyzer_analyze_file(sample_python_file: Path):
    """Test file analysis."""
    analyzer = RepositoryAnalyzer(
        str(sample_python_file.parent),
        str(sample_python_file.parent / "out")
    )
    
    metrics = analyzer.analyze_file(sample_python_file)
    
    assert metrics is not None
    assert metrics.language == "Python"
    assert metrics.functions > 0
    assert metrics.classes > 0
    assert len(metrics.imports) >= 0
    assert metrics.has_docstrings is True


def test_repo_analyzer_generate_manifest(sample_repo_structure: Path):
    """Test manifest generation."""
    output_dir = sample_repo_structure / "output"
    analyzer = RepositoryAnalyzer(
        root_path=str(sample_repo_structure),
        output_dir=str(output_dir)
    )
    
    analyzer.generate_manifest()
    
    assert len(analyzer.file_manifest) > 0
    # Should not include excluded directories
    manifest_paths = [f['path'] for f in analyzer.file_manifest]
    assert not any('__pycache__' in path for path in manifest_paths)


def test_repo_analyzer_build_dependency_graph(sample_repo_structure: Path):
    """Test dependency graph building."""
    output_dir = sample_repo_structure / "output"
    analyzer = RepositoryAnalyzer(
        root_path=str(sample_repo_structure),
        output_dir=str(output_dir)
    )
    
    # Analyze files first
    python_files = [f for f in sample_repo_structure.rglob("*.py")]
    for py_file in python_files:
        metrics = analyzer.analyze_file(py_file)
        if metrics:
            analyzer.file_metrics[metrics.path] = metrics
    
    analyzer.build_dependency_graph()
    
    assert len(analyzer.module_graph) > 0


def test_repo_analyzer_identify_candidates(sample_repo_structure: Path):
    """Test candidate identification."""
    output_dir = sample_repo_structure / "output"
    analyzer = RepositoryAnalyzer(
        root_path=str(sample_repo_structure),
        output_dir=str(output_dir)
    )
    
    # Analyze files and build graph
    python_files = [f for f in sample_repo_structure.rglob("*.py")]
    for py_file in python_files:
        metrics = analyzer.analyze_file(py_file)
        if metrics:
            analyzer.file_metrics[metrics.path] = metrics
    
    analyzer.build_dependency_graph()
    candidates = analyzer.identify_candidates()
    
    assert "candidates_for_refactor" in candidates
    assert "reference_high_value_components" in candidates
    assert isinstance(candidates["candidates_for_refactor"], list)
    assert isinstance(candidates["reference_high_value_components"], list)


@pytest.mark.integration
def test_repo_analyzer_full_workflow(sample_repo_structure: Path):
    """Test full repository analysis workflow."""
    output_dir = sample_repo_structure / "output"
    analyzer = RepositoryAnalyzer(
        root_path=str(sample_repo_structure),
        output_dir=str(output_dir)
    )
    
    candidates = analyzer.analyze_repository()
    analyzer.save_outputs(candidates)
    
    # Verify outputs were created
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "candidates.json").exists()
    assert (output_dir / "module_graph.json").exists()
    assert (output_dir / "language_summary.json").exists()


def test_repo_analyzer_json_output(sample_repo_structure: Path):
    """Test JSON output format for Cascade."""
    output_dir = sample_repo_structure / "output"
    analyzer = RepositoryAnalyzer(
        root_path=str(sample_repo_structure),
        output_dir=str(output_dir)
    )
    
    candidates = analyzer.analyze_repository()
    analyzer.save_outputs(candidates, output_json=True)
    
    # Verify JSON files are valid
    import json
    
    candidates_file = output_dir / "candidates.json"
    assert candidates_file.exists()
    with open(candidates_file, 'r') as f:
        candidates_data = json.load(f)
        assert isinstance(candidates_data, dict)
        assert "candidates_for_refactor" in candidates_data