#!/usr/bin/env python3
"""
Comprehensive debugging script for basedpyright performance issues.
Tracks file analysis, memory usage patterns, and identifies bottlenecks.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict


class BasedpyrightDebugger:
    """Debug and analyze basedpyright performance issues."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.config_path = workspace_root / 'pyrightconfig.json'
        self.baseline_path = workspace_root / '.basedpyright' / 'baseline.json'
        self.log_patterns = {
            'long_operation': re.compile(r'Long operation: (\w+): (.+) \((\d+)ms\)'),
            'heap_overflow': re.compile(r'Emptying type cache to avoid heap overflow\. Used (\d+)MB out of (\d+)MB'),
            'file_count': re.compile(r'Found (\d+) source files'),
            'analyzing': re.compile(r'analyzing: (.+)'),
            'checking': re.compile(r'checking: (.+)'),
        }
    
    def load_config(self) -> Dict:
        """Load pyrightconfig.json."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}
    
    def parse_basedpyright_logs(self, log_content: str) -> Dict:
        """Parse basedpyright output logs to extract performance metrics."""
        metrics = {
            'long_operations': [],
            'heap_overflows': [],
            'file_count': None,
            'slow_files': defaultdict(list),
            'operation_times': defaultdict(list),
        }
        
        lines = log_content.split('\n')
        for line in lines:
            # Long operations
            match = self.log_patterns['long_operation'].search(line)
            if match:
                op_type, file_path, duration_ms = match.groups()
                duration_ms = int(duration_ms)
                metrics['long_operations'].append({
                    'type': op_type,
                    'file': file_path,
                    'duration_ms': duration_ms
                })
                metrics['slow_files'][file_path].append(duration_ms)
                metrics['operation_times'][op_type].append(duration_ms)
            
            # Heap overflow
            match = self.log_patterns['heap_overflow'].search(line)
            if match:
                used_mb, total_mb = map(int, match.groups())
                metrics['heap_overflows'].append({
                    'used_mb': used_mb,
                    'total_mb': total_mb,
                    'usage_percent': (used_mb / total_mb) * 100
                })
            
            # File count
            match = self.log_patterns['file_count'].search(line)
            if match:
                metrics['file_count'] = int(match.group(1))
        
        return metrics
    
    def analyze_slow_files(self, metrics: Dict, top_n: int = 20) -> List[Dict]:
        """Identify the slowest files to analyze."""
        slow_files = []
        for file_path, times in metrics['slow_files'].items():
            avg_time = sum(times) / len(times)
            max_time = max(times)
            total_time = sum(times)
            slow_files.append({
                'file': file_path,
                'avg_ms': avg_time,
                'max_ms': max_time,
                'total_ms': total_time,
                'count': len(times)
            })
        
        return sorted(slow_files, key=lambda x: x['total_ms'], reverse=True)[:top_n]
    
    def analyze_operation_types(self, metrics: Dict) -> Dict:
        """Analyze performance by operation type."""
        analysis = {}
        for op_type, times in metrics['operation_times'].items():
            if times:
                analysis[op_type] = {
                    'count': len(times),
                    'total_ms': sum(times),
                    'avg_ms': sum(times) / len(times),
                    'max_ms': max(times),
                    'min_ms': min(times)
                }
        return analysis
    
    def check_memory_patterns(self, metrics: Dict) -> Dict:
        """Analyze memory usage patterns."""
        if not metrics['heap_overflows']:
            return {'status': 'ok', 'message': 'No heap overflow events detected'}
        
        overflows = metrics['heap_overflows']
        usage_percentages = [o['usage_percent'] for o in overflows]
        
        return {
            'status': 'warning',
            'overflow_count': len(overflows),
            'avg_usage_percent': sum(usage_percentages) / len(usage_percentages),
            'max_usage_percent': max(usage_percentages),
            'min_usage_percent': min(usage_percentages),
            'first_overflow': overflows[0] if overflows else None,
            'last_overflow': overflows[-1] if overflows else None
        }
    
    def generate_report(self, metrics: Dict) -> str:
        """Generate a comprehensive debug report."""
        report = []
        report.append("=" * 80)
        report.append("Basedpyright Performance Debug Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")
        
        # File count
        if metrics['file_count']:
            report.append(f"Total files analyzed: {metrics['file_count']}")
            if metrics['file_count'] > 1000:
                report.append("  ⚠️  WARNING: High file count may cause performance issues")
            report.append("")
        
        # Long operations summary
        if metrics['long_operations']:
            report.append(f"Long operations detected: {len(metrics['long_operations'])}")
            report.append("")
            
            # Operation type breakdown
            op_analysis = self.analyze_operation_types(metrics)
            if op_analysis:
                report.append("Operation type breakdown:")
                for op_type, stats in sorted(op_analysis.items(), key=lambda x: x[1]['total_ms'], reverse=True):
                    report.append(f"  {op_type}:")
                    report.append(f"    Count: {stats['count']}")
                    report.append(f"    Total time: {stats['total_ms']/1000:.2f}s")
                    report.append(f"    Average: {stats['avg_ms']:.2f}ms")
                    report.append(f"    Max: {stats['max_ms']:.2f}ms")
                report.append("")
            
            # Slowest files
            slow_files = self.analyze_slow_files(metrics, top_n=15)
            if slow_files:
                report.append("Top 15 slowest files:")
                for i, file_info in enumerate(slow_files, 1):
                    file_path = file_info['file']
                    # Truncate long paths
                    if len(file_path) > 70:
                        file_path = '...' + file_path[-67:]
                    report.append(f"  {i:2d}. {file_info['total_ms']/1000:7.2f}s total "
                                f"({file_info['avg_ms']:.0f}ms avg, {file_info['count']} ops) - {file_path}")
                report.append("")
        
        # Memory analysis
        memory_analysis = self.check_memory_patterns(metrics)
        report.append("Memory Usage Analysis:")
        if memory_analysis['status'] == 'warning':
            report.append(f"  ⚠️  Heap overflow events: {memory_analysis['overflow_count']}")
            report.append(f"  Average usage: {memory_analysis['avg_usage_percent']:.1f}%")
            report.append(f"  Max usage: {memory_analysis['max_usage_percent']:.1f}%")
            if memory_analysis['first_overflow']:
                first = memory_analysis['first_overflow']
                report.append(f"  First overflow: {first['used_mb']}MB / {first['total_mb']}MB "
                            f"({first['usage_percent']:.1f}%)")
        else:
            report.append(f"  ✓ {memory_analysis['message']}")
        report.append("")
        
        # Recommendations
        report.append("=" * 80)
        report.append("Recommendations")
        report.append("=" * 80)
        
        config = self.load_config()
        exclude_patterns = config.get('exclude', [])
        
        recommendations = []
        
        if metrics['file_count'] and metrics['file_count'] > 1000:
            recommendations.append("Consider adding exclude patterns for:")
            recommendations.append("  - Test files: **/tests/**, **/test_*.py, **/*_test.py")
            recommendations.append("  - Site-packages tests: **/site-packages/**/tests/**")
            recommendations.append("  - Large third-party libraries")
        
        if memory_analysis['status'] == 'warning':
            recommendations.append("Memory optimization:")
            recommendations.append("  - Review and exclude large files identified above")
            recommendations.append("  - Consider splitting workspace into smaller projects")
            recommendations.append("  - Check for circular dependencies causing cache bloat")
        
        slow_files = self.analyze_slow_files(metrics, top_n=5)
        if slow_files and any(f['avg_ms'] > 1000 for f in slow_files):
            recommendations.append("Slow file optimization:")
            for file_info in slow_files[:5]:
                if file_info['avg_ms'] > 1000:
                    file_path = file_info['file']
                    # Check if it's a test file
                    if '/test' in file_path.lower() or 'test_' in Path(file_path).name:
                        recommendations.append(f"  - Exclude test file: {file_path}")
                    elif 'site-packages' in file_path:
                        recommendations.append(f"  - Consider excluding: {file_path}")
        
        if recommendations:
            for rec in recommendations:
                report.append(rec)
        else:
            report.append("No specific recommendations at this time.")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_analysis(self, log_file: Optional[Path] = None) -> str:
        """Run complete analysis and generate report."""
        metrics = {
            'long_operations': [],
            'heap_overflows': [],
            'file_count': None,
            'slow_files': defaultdict(list),
            'operation_times': defaultdict(list),
        }
        
        # If log file provided, parse it
        if log_file and log_file.exists():
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                log_content = f.read()
            metrics = self.parse_basedpyright_logs(log_content)
        
        return self.generate_report(metrics)


def main():
    """Main entry point."""
    workspace_root = Path('e:\\')
    debugger = BasedpyrightDebugger(workspace_root)
    
    # Check for log file argument
    log_file = None
    if len(sys.argv) > 1:
        log_file = Path(sys.argv[1])
        if not log_file.exists():
            print(f"Error: Log file not found: {log_file}")
            return
    
    # Generate report
    report = debugger.run_analysis(log_file)
    print(report)
    
    # Save report to file
    report_path = workspace_root / 'basedpyright_debug_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")


if __name__ == '__main__':
    main()
