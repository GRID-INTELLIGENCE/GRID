#!/usr/bin/env python3
"""
Cross-project comparison tool for analyzing two repositories.
Compares modules, patterns, and suggests optimization opportunities.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import re


class ProjectComparator:
    """Compare two analyzed projects."""

    def __init__(self, grid_analysis_dir: str, eufle_analysis_dir: str, output_dir: str):
        self.grid_dir = Path(grid_analysis_dir)
        self.eufle_dir = Path(eufle_analysis_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load analysis data
        self.grid_metrics = self.load_metrics(grid_analysis_dir)
        self.eufle_metrics = self.load_metrics(eufle_analysis_dir)
        self.grid_graph = self.load_graph(grid_analysis_dir)
        self.eufle_graph = self.load_graph(eufle_analysis_dir)
        self.grid_candidates = self.load_candidates(grid_analysis_dir)
        self.eufle_candidates = self.load_candidates(eufle_analysis_dir)

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
        # Remove extensions, normalize path
        name = Path(path).stem
        # Remove common prefixes
        name = re.sub(r'^(src|lib|app|components|modules)/', '', name)
        return name.lower()

    def compute_signature_similarity(self, grid_node: Dict, eufle_node: Dict) -> float:
        """Compute similarity score between two module signatures."""
        score = 0.0

        # Compare language
        if grid_node.get('language') == eufle_node.get('language'):
            score += 0.2

        # Compare size (lines) - similar sizes get higher score
        grid_lines = grid_node.get('lines', 0)
        eufle_lines = eufle_node.get('lines', 0)
        if grid_lines > 0 and eufle_lines > 0:
            size_ratio = min(grid_lines, eufle_lines) / max(grid_lines, eufle_lines)
            score += size_ratio * 0.3

        # Compare complexity
        grid_complexity = grid_node.get('complexity', 0)
        eufle_complexity = eufle_node.get('complexity', 0)
        if grid_complexity > 0 and eufle_complexity > 0:
            complexity_ratio = min(grid_complexity, eufle_complexity) / max(grid_complexity, eufle_complexity)
            score += complexity_ratio * 0.2

        # Compare fan-in/fan-out (traffic patterns)
        grid_fan_in = grid_node.get('fan_in', 0)
        eufle_fan_in = eufle_node.get('fan_in', 0)
        if grid_fan_in > 0 and eufle_fan_in > 0:
            fan_in_ratio = min(grid_fan_in, eufle_fan_in) / max(grid_fan_in, eufle_fan_in)
            score += fan_in_ratio * 0.3

        return score

    def find_similar_modules(self) -> List[Dict]:
        """Find similar modules between projects."""
        similar_modules = []

        grid_nodes = {node['id']: node for node in self.grid_graph.get('nodes', [])}
        eufle_nodes = {node['id']: node for node in self.eufle_graph.get('nodes', [])}

        for grid_id, grid_node in grid_nodes.items():
            grid_name = self.extract_module_name(grid_id)

            best_match = None
            best_score = 0.0

            for eufle_id, eufle_node in eufle_nodes.items():
                eufle_name = self.extract_module_name(eufle_id)

                # Name similarity
                name_score = 0.0
                if grid_name == eufle_name:
                    name_score = 0.5
                elif grid_name in eufle_name or eufle_name in grid_name:
                    name_score = 0.3

                # Signature similarity
                sig_score = self.compute_signature_similarity(grid_node, eufle_node)

                total_score = name_score + sig_score

                if total_score > best_score and total_score > 0.4:  # Threshold
                    best_score = total_score
                    best_match = {
                        'grid_module': grid_id,
                        'eufle_module': eufle_id,
                        'similarity_score': total_score,
                        'grid_metrics': grid_node,
                        'eufle_metrics': eufle_node
                    }

            if best_match:
                similar_modules.append(best_match)

        # Sort by similarity score
        similar_modules.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar_modules[:50]  # Top 50 matches

    def compare_high_traffic_modules(self) -> List[Dict]:
        """Compare high-traffic modules between projects."""
        comparisons = []

        # Get top candidates from each project
        grid_refactor = self.grid_candidates.get('candidates_for_refactor', [])[:10]
        eufle_refactor = self.eufle_candidates.get('candidates_for_refactor', [])[:10]
        grid_reference = self.grid_candidates.get('reference_high_value_components', [])[:10]
        eufle_reference = self.eufle_candidates.get('reference_high_value_components', [])[:10]

        # Compare refactor candidates
        for grid_candidate in grid_refactor:
            grid_path = grid_candidate['path']
            grid_metrics = self.grid_metrics.get(grid_path, {})

            # Find similar in EUFLE
            similar = self.find_similar_modules()
            eufle_match = next((m for m in similar if m['grid_module'] == grid_path), None)

            if eufle_match:
                eufle_path = eufle_match['eufle_module']
                eufle_metrics = self.eufle_metrics.get(eufle_path, {})

                # Compare metrics
                comparison = {
                    'type': 'refactor_candidate',
                    'grid_module': grid_path,
                    'eufle_module': eufle_path,
                    'similarity_score': eufle_match['similarity_score'],
                    'grid_metrics': {
                        'fan_in': grid_candidate.get('fan_in', 0),
                        'complexity': grid_candidate.get('complexity', 0),
                        'comment_density': grid_candidate.get('comment_density', 0),
                        'lines': grid_candidate.get('lines', 0)
                    },
                    'eufle_metrics': {
                        'fan_in': eufle_metrics.get('fan_in', 0),
                        'complexity': eufle_metrics.get('complexity', 0),
                        'comment_density': eufle_metrics.get('comment_density', 0),
                        'lines': eufle_metrics.get('lines', 0)
                    },
                    'recommendations': []
                }

                # Generate recommendations
                if eufle_metrics.get('comment_density', 0) > grid_candidate.get('comment_density', 0):
                    comparison['recommendations'].append({
                        'action': 'improve_documentation',
                        'reason': f'EUFLE module has {eufle_metrics.get("comment_density", 0):.2%} comment density vs {grid_candidate.get("comment_density", 0):.2%}',
                        'source': 'eufle'
                    })

                if eufle_metrics.get('complexity', 0) < grid_candidate.get('complexity', 0) * 0.8:
                    comparison['recommendations'].append({
                        'action': 'reduce_complexity',
                        'reason': f'EUFLE module has lower complexity ({eufle_metrics.get("complexity", 0)} vs {grid_candidate.get("complexity", 0)})',
                        'source': 'eufle'
                    })

                comparisons.append(comparison)

        # Compare reference components
        for grid_ref in grid_reference:
            grid_path = grid_ref['path']
            similar = self.find_similar_modules()
            eufle_match = next((m for m in similar if m['grid_module'] == grid_path), None)

            if eufle_match:
                eufle_path = eufle_match['eufle_module']
                eufle_metrics = self.eufle_metrics.get(eufle_path, {})

                comparison = {
                    'type': 'reference_component',
                    'grid_module': grid_path,
                    'eufle_module': eufle_path,
                    'similarity_score': eufle_match['similarity_score'],
                    'grid_metrics': {
                        'fan_in': grid_ref.get('fan_in', 0),
                        'complexity': grid_ref.get('complexity', 0),
                        'comment_density': grid_ref.get('comment_density', 0),
                        'lines': grid_ref.get('lines', 0)
                    },
                    'eufle_metrics': {
                        'fan_in': eufle_metrics.get('fan_in', 0),
                        'complexity': eufle_metrics.get('complexity', 0),
                        'comment_density': eufle_metrics.get('comment_density', 0),
                        'lines': eufle_metrics.get('lines', 0)
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
        """Generate comprehensive comparison report."""
        similar_modules = self.find_similar_modules()
        comparisons = self.compare_high_traffic_modules()

        report = {
            'summary': {
                'grid_modules_analyzed': len(self.grid_metrics),
                'eufle_modules_analyzed': len(self.eufle_metrics),
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

        # Group by recommendation type
        rec_by_type = defaultdict(list)
        for comp in comparisons:
            for rec in comp.get('recommendations', []):
                rec_by_type[rec['action']].append({
                    'grid_module': comp['grid_module'],
                    'eufle_module': comp.get('eufle_module'),
                    'reason': rec['reason'],
                    'source': rec['source']
                })

        # Create prioritized recommendations
        for action, recs in rec_by_type.items():
            recommendations.append({
                'action': action,
                'priority': 'high' if len(recs) > 3 else 'medium',
                'affected_modules': len(recs),
                'details': recs[:10]  # Top 10
            })

        return recommendations

    def save_comparison_report(self):
        """Save comparison report to output directory."""
        report = self.generate_comparison_report()

        output_file = self.output_dir / 'cross_project_comparison.json'
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Comparison report saved to {output_file}")
        return report


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Compare two analyzed projects')
    parser.add_argument('--grid', required=True, help='Path to GRID analysis output directory')
    parser.add_argument('--eufle', required=True, help='Path to EUFLE analysis output directory')
    parser.add_argument('--out', required=True, help='Output directory for comparison report')

    args = parser.parse_args()

    comparator = ProjectComparator(args.grid, args.eufle, args.out)
    comparator.save_comparison_report()


if __name__ == '__main__':
    main()
