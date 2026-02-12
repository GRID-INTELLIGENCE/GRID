"""
Tests for project comparator.
"""

import pytest
import json
from pathlib import Path
from workspace_utils.project_comparator import ProjectComparator


@pytest.fixture
def mock_analysis_output(temp_dir: Path) -> Path:
    """Create mock analysis output directory."""
    analysis_dir = temp_dir / "analysis"
    (analysis_dir / "file_metrics").mkdir(parents=True)
    
    # Create mock metrics file
    metrics_file = analysis_dir / "file_metrics" / "test_module.json"
    metrics_file.write_text(json.dumps({
        "path": "src/test_module.py",
        "language": "Python",
        "lines": 100,
        "complexity": 10,
        "fan_in": 2,
        "comment_density": 0.2,
        "has_docstrings": True
    }))
    
    # Create mock graph file
    graph_file = analysis_dir / "module_graph.json"
    graph_file.write_text(json.dumps({
        "nodes": [
            {
                "id": "src/test_module.py",
                "path": "src/test_module.py",
                "fan_in": 2,
                "fan_out": 1,
                "lines": 100,
                "complexity": 10,
                "language": "Python"
            }
        ],
        "edges": []
    }))
    
    # Create mock candidates file
    candidates_file = analysis_dir / "candidates.json"
    candidates_file.write_text(json.dumps({
        "candidates_for_refactor": [],
        "reference_high_value_components": [
            {
                "path": "src/test_module.py",
                "fan_in": 2,
                "complexity": 10,
                "comment_density": 0.2,
                "lines": 100
            }
        ]
    }))
    
    return analysis_dir


def test_project_comparator_initialization(mock_analysis_output: Path, temp_dir: Path):
    """Test ProjectComparator initialization."""
    output_dir = temp_dir / "comparison"
    
    comparator = ProjectComparator(
        project1_analysis_dir=str(mock_analysis_output),
        project2_analysis_dir=str(mock_analysis_output),
        output_dir=str(output_dir)
    )
    
    assert comparator.project1_dir == mock_analysis_output
    assert comparator.project2_dir == mock_analysis_output
    assert comparator.output_dir == output_dir


def test_project_comparator_load_metrics(mock_analysis_output: Path):
    """Test loading metrics from analysis directory."""
    output_dir = mock_analysis_output.parent / "comparison"
    comparator = ProjectComparator(
        project1_analysis_dir=str(mock_analysis_output),
        project2_analysis_dir=str(mock_analysis_output),
        output_dir=str(output_dir)
    )
    
    assert len(comparator.project1_metrics) > 0
    assert "src/test_module.py" in comparator.project1_metrics


def test_project_comparator_load_graph(mock_analysis_output: Path):
    """Test loading graph from analysis directory."""
    output_dir = mock_analysis_output.parent / "comparison"
    comparator = ProjectComparator(
        project1_analysis_dir=str(mock_analysis_output),
        project2_analysis_dir=str(mock_analysis_output),
        output_dir=str(output_dir)
    )
    
    assert "nodes" in comparator.project1_graph
    assert len(comparator.project1_graph["nodes"]) > 0


def test_project_comparator_extract_module_name():
    """Test module name extraction."""
    output_dir = Path("temp") / "comparison"
    comparator = ProjectComparator(
        project1_analysis_dir="temp/analysis1",
        project2_analysis_dir="temp/analysis2",
        output_dir=str(output_dir)
    )
    
    assert comparator.extract_module_name("src/app/main.py") == "main"
    assert comparator.extract_module_name("components/Button.tsx") == "button"


def test_project_comparator_compute_signature_similarity():
    """Test signature similarity computation."""
    output_dir = Path("temp") / "comparison"
    comparator = ProjectComparator(
        project1_analysis_dir="temp/analysis1",
        project2_analysis_dir="temp/analysis2",
        output_dir=str(output_dir)
    )
    
    node1 = {
        "language": "Python",
        "lines": 100,
        "complexity": 10,
        "fan_in": 2
    }
    
    node2 = {
        "language": "Python",
        "lines": 100,
        "complexity": 10,
        "fan_in": 2
    }
    
    similarity = comparator.compute_signature_similarity(node1, node2)
    assert 0.0 <= similarity <= 1.0


def test_project_comparator_find_similar_modules(mock_analysis_output: Path, temp_dir: Path):
    """Test finding similar modules between projects."""
    output_dir = temp_dir / "comparison"
    comparator = ProjectComparator(
        project1_analysis_dir=str(mock_analysis_output),
        project2_analysis_dir=str(mock_analysis_output),
        output_dir=str(output_dir)
    )
    
    similar_modules = comparator.find_similar_modules()
    assert isinstance(similar_modules, list)


def test_project_comparator_generate_comparison_report(mock_analysis_output: Path, temp_dir: Path):
    """Test generating comparison report."""
    output_dir = temp_dir / "comparison"
    comparator = ProjectComparator(
        project1_analysis_dir=str(mock_analysis_output),
        project2_analysis_dir=str(mock_analysis_output),
        output_dir=str(output_dir)
    )
    
    report = comparator.generate_comparison_report()
    
    assert "summary" in report
    assert "similar_modules" in report
    assert "high_traffic_comparisons" in report
    assert "recommendations" in report


def test_project_comparator_save_comparison_report(mock_analysis_output: Path, temp_dir: Path):
    """Test saving comparison report."""
    output_dir = temp_dir / "comparison"
    comparator = ProjectComparator(
        project1_analysis_dir=str(mock_analysis_output),
        project2_analysis_dir=str(mock_analysis_output),
        output_dir=str(output_dir)
    )
    
    report = comparator.save_comparison_report()
    
    # Verify JSON file was created
    comparison_file = output_dir / "cross_project_comparison.json"
    assert comparison_file.exists()
    
    # Verify JSON is valid
    with open(comparison_file, 'r') as f:
        saved_report = json.load(f)
        assert isinstance(saved_report, dict)
        assert "summary" in saved_report