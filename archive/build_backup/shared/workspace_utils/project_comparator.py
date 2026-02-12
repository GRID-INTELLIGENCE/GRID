"""
Project Comparison Module

Migrated from compare_projects.py - provides cross-project comparison
with Cascade-friendly JSON output.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
import re

from .config import config
from .exceptions import ComparisonError, ValidationError
from .validators import validate_analysis_dir, validate_output_dir


class ProjectComparator:
    """Compare two analyzed projects."""

    def __init__(self, project1_analysis_dir: str, project2_analysis_dir: str, output_dir: Optional[str] = None):
        # Validate inputs
        try:
            self.project1_dir = validate_analysis_dir(project1_analysis_dir)
            self.project2_dir = validate_analysis_dir(project2_analysis_dir)
            self.output_dir = validate_output_dir(output_dir, create=True) if output_dir else config.get_output_dir()
        except ValidationError as e:
            raise ComparisonError(
                f"Invalid comparison inputs: {str(e)}\n"
                f"Please ensure both analysis directories are valid and contain required files."
            ) from e

        # Load analysis data
        self.project1_metrics = self.load_metrics(project1_analysis_dir)
        self.project2_metrics = self.load_metrics(project2_analysis_dir)
        self.project1_graph = self.load_graph(project1_analysis_dir)
        self.project2_graph = self.load_graph(project2_analysis_dir)
        self.project1_candidates = self.load_candidates(project1_analysis_dir)
        self.project2_candidates = self.load_candidates(project2_analysis_dir)

    def load_metrics(self, analysis_dir: str) -> Dict:
        """Load file metrics from analysis directory."""
        metrics_dir = Path(analysis_dir) / 'file_metrics'
        metrics = {}
        if metrics_dir.exists():
            for file in metrics_dir.glob('*.json'):
                with open(file, 'r') as f:
                    data = json.load(f)
                    path = data.get('path', '')
                    if path:
                        metrics[path] = data
        return metrics

    def load_graph(self, analysis_dir: str) -> Dict:
        """Load module graph from analysis directory."""
        graph_file = Path(analysis_dir) / 'module_graph.json'
        if graph_file.exists():
            with open(graph_file, 'r') as f:
                return json.load(f)
        return {'nodes': [], 'edges': []}

    def load_candidates(self, analysis_dir: str) -> Dict:
        """Load candidates from analysis directory."""
        candidates_file = Path(analysis_dir) / 'candidates.json'
        if candidates_file.exists():
            with open(candidates_file, 'r') as f:
                return json.load(f)
        return {'candidates_for_refactor': [], 'reference_high_value_components': []}

    def extract_module_name(self, path: str) -> str:
        """Extract module name from path."""
        name = Path(path).stem
        name = re.sub(r'^(src|lib|app|components|modules)/', '', name)
        return name.lower()

    def compute_signature_similarity(self, node1: Dict, node2: Dict) -> float:
        """Compute similarity score between two module signatures."""
        score = 0.0

        if node1.get('language') == node2.get('language'):
            score += 0.2

        lines1 = node1.get('lines', 0)
        lines2 = node2.get('lines', 0)
        if lines1 > 0 and lines2 > 0:
            size_ratio = min(lines1, lines2) / max(lines1, lines2)
            score += size_ratio * 0.3

        complexity1 = node1.get('complexity', 0)
        complexity2 = node2.get('complexity', 0)
        if complexity1 > 0 and complexity2 > 0:
            complexity_ratio = min(complexity1, complexity2) / max(complexity1, complexity2)
            score += complexity_ratio * 0.2

        fan_in1 = node1.get('fan_in', 0)
        fan_in2 = node2.get('fan_in', 0)
        if fan_in1 > 0 and fan_in2 > 0:
            fan_in_ratio = min(fan_in1, fan_in2) / max(fan_in1, fan_in2)
            score += fan_in_ratio * 0.3

        return score

    def find_similar_modules(self) -> List[Dict]:
        """Find similar modules between projects."""
        similar_modules = []

        nodes1 = {node['id']: node for node in self.project1_graph.get('nodes', [])}
        nodes2 = {node['id']: node for node in self.project2_graph.get('nodes', [])}

        for id1, node1 in nodes1.items():
            name1 = self.extract_module_name(id1)

            best_match = None
            best_score = 0.0

            for id2, node2 in nodes2.items():
                name2 = self.extract_module_name(id2)

                name_score = 0.0
                if name1 == name2:
                    name_score = 0.5
                elif name1 in name2 or name2 in name1:
                    name_score = 0.3

                sig_score = self.compute_signature_similarity(node1, node2)
                total_score = name_score + sig_score

                if total_score > best_score and total_score > 0.4:
                    best_score = total_score
                    best_match = {
                        'project1_module': id1,
                        'project2_module': id2,
                        'similarity_score': total_score,
                        'project1_metrics': node1,
                        'project2_metrics': node2
                    }

            if best_match:
                similar_modules.append(best_match)

        similar_modules.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar_modules[:50]

    def compare_high_traffic_modules(self) -> List[Dict]:
        """Compare high-traffic modules between projects."""
        comparisons = []

        refactor1 = self.project1_candidates.get('candidates_for_refactor', [])[:10]
        refactor2 = self.project2_candidates.get('candidates_for_refactor', [])[:10]
        reference1 = self.project1_candidates.get('reference_high_value_components', [])[:10]
        reference2 = self.project2_candidates.get('reference_high_value_components', [])[:10]

        similar = self.find_similar_modules()

        for candidate1 in refactor1:
            path1 = candidate1['path']
            metrics1 = self.project1_metrics.get(path1, {})

            match = next((m for m in similar if m['project1_module'] == path1), None)

            if match:
                path2 = match['project2_module']
                metrics2 = self.project2_metrics.get(path2, {})

                comparison = {
                    'type': 'refactor_candidate',
                    'project1_module': path1,
                    'project2_module': path2,
                    'similarity_score': match['similarity_score'],
                    'project1_metrics': {
                        'fan_in': candidate1.get('fan_in', 0),
                        'complexity': candidate1.get('complexity', 0),
                        'comment_density': candidate1.get('comment_density', 0),
                        'lines': candidate1.get('lines', 0)
                    },
                    'project2_metrics': {
                        'fan_in': metrics2.get('fan_in', 0),
                        'complexity': metrics2.get('complexity', 0),
                        'comment_density': metrics2.get('comment_density', 0),
                        'lines': metrics2.get('lines', 0)
                    },
                    'recommendations': []
                }

                if metrics2.get('comment_density', 0) > candidate1.get('comment_density', 0):
                    comparison['recommendations'].append({
                        'action': 'improve_documentation',
                        'reason': f'Project2 module has {metrics2.get("comment_density", 0):.2%} comment density vs {candidate1.get("comment_density", 0):.2%}',
                        'source': 'project2'
                    })

                if metrics2.get('complexity', 0) < candidate1.get('complexity', 0) * 0.8:
                    comparison['recommendations'].append({
                        'action': 'reduce_complexity',
                        'reason': f'Project2 module has lower complexity ({metrics2.get("complexity", 0)} vs {candidate1.get("complexity", 0)})',
                        'source': 'project2'
                    })

                comparisons.append(comparison)

        for ref1 in reference1:
            path1 = ref1['path']
            match = next((m for m in similar if m['project1_module'] == path1), None)

            if match:
                path2 = match['project2_module']
                metrics2 = self.project2_metrics.get(path2, {})

                comparison = {
                    'type': 'reference_component',
                    'project1_module': path1,
                    'project2_module': path2,
                    'similarity_score': match['similarity_score'],
                    'project1_metrics': {
                        'fan_in': ref1.get('fan_in', 0),
                        'complexity': ref1.get('complexity', 0),
                        'comment_density': ref1.get('comment_density', 0),
                        'lines': ref1.get('lines', 0)
                    },
                    'project2_metrics': {
                        'fan_in': metrics2.get('fan_in', 0),
                        'complexity': metrics2.get('complexity', 0),
                        'comment_density': metrics2.get('comment_density', 0),
                        'lines': metrics2.get('lines', 0)
                    },
                    'recommendations': [
                        {
                            'action': 'mirror_patterns',
                            'reason': 'Both are high-value reference components - consider sharing patterns',
                            'source': 'both'
                        }
                    ]
                }
                comparisons.append(comparison)

        return comparisons

    def generate_comparison_report(self) -> Dict:
        """Generate comprehensive comparison report (JSON for Cascade)."""
        similar_modules = self.find_similar_modules()
        comparisons = self.compare_high_traffic_modules()

        report = {
            'summary': {
                'project1_modules_analyzed': len(self.project1_metrics),
                'project2_modules_analyzed': len(self.project2_metrics),
                'similar_modules_found': len(similar_modules),
                'high_traffic_comparisons': len(comparisons)
            },
            'similar_modules': similar_modules,
            'high_traffic_comparisons': comparisons,
            'recommendations': self.generate_recommendations(comparisons)
        }

        return report

    def generate_recommendations(self, comparisons: List[Dict]) -> List[Dict]:
        """Generate optimization recommendations from comparisons."""
        recommendations = []

        rec_by_type = defaultdict(list)
        for comp in comparisons:
            for rec in comp.get('recommendations', []):
                rec_by_type[rec['action']].append({
                    'project1_module': comp['project1_module'],
                    'project2_module': comp.get('project2_module'),
                    'reason': rec['reason'],
                    'source': rec['source']
                })

        for action, recs in rec_by_type.items():
            recommendations.append({
                'action': action,
                'priority': 'high' if len(recs) > 3 else 'medium',
                'affected_modules': len(recs),
                'details': recs[:10]
            })

        return recommendations

    def save_comparison_report(self):
        """Save comparison report to output directory (always JSON for Cascade)."""
        report = self.generate_comparison_report()

        output_file = self.output_dir / 'cross_project_comparison.json'
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Comparison report saved to {output_file}")
        return report