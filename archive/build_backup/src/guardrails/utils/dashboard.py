"""
Guardrail Monitoring Dashboard

Provides real-time visualization and monitoring of guardrail violations
and trends. Can be run as a standalone script or integrated into
monitoring systems.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import sys

# Try to import optional dependencies for advanced features
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class GuardrailDashboard:
    """Dashboard for visualizing guardrail metrics and trends."""
    
    def __init__(self, data_source: Optional[str] = None):
        """
        Initialize the dashboard.
        
        Args:
            data_source: Path to JSON data file or None for empty dashboard
        """
        self.data_source = data_source
        self.data = self._load_data()
        self.violations = self.data.get("violations", [])
        self.metrics = self.data.get("metrics", {})
        
    def _load_data(self) -> Dict[str, Any]:
        """Load data from file or return empty structure."""
        if not self.data_source:
            return {"violations": [], "metrics": {}}
            
        data_file = Path(self.data_source)
        if data_file.exists():
            with open(data_file, 'r') as f:
                return json.load(f)
        return {"violations": [], "metrics": {}}
        
    def generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of current status."""
        if not self.violations:
            return {
                "status": "clean",
                "total_violations": 0,
                "message": "No violations detected. System is clean!"
            }
            
        # Calculate metrics
        total = len(self.violations)
        
        # Group by type
        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        by_module = defaultdict(int)
        
        for violation in self.violations:
            vtype = violation.get("type", "unknown")
            severity = violation.get("severity", "unknown")
            module = violation.get("module", "unknown")
            
            by_type[vtype] += 1
            by_severity[severity] += 1
            by_module[module] += 1
            
        # Determine status
        critical_count = by_severity.get("critical", 0)
        high_count = by_severity.get("high", 0)
        
        if critical_count > 0:
            status = "critical"
        elif high_count > 5:
            status = "warning"
        elif total > 20:
            status = "attention"
        else:
            status = "stable"
            
        return {
            "status": status,
            "total_violations": total,
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
            "by_module": dict(by_module),
            "critical_modules": [
                module for module, count in by_module.items()
                if count >= 3
            ],
            "recent_violations": len([
                v for v in self.violations
                if self._is_recent(v.get("timestamp"), hours=24)
            ]),
        }
        
    def _is_recent(self, timestamp: str, hours: int = 24) -> bool:
        """Check if a timestamp is within the specified hours."""
        if not timestamp:
            return False
            
        try:
            violation_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if violation_time.tzinfo is None:
                violation_time = violation_time.replace(tzinfo=timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            return violation_time > cutoff
        except:
            return False
            
    def print_summary(self) -> None:
        """Print a text-based summary to console."""
        summary = self.generate_summary()
        
        # Status banner
        status = summary["status"]
        status_colors = {
            "clean": "[OK]",
            "stable": "[OK]",
            "attention": "[!]",
            "warning": "[WARNING]",
            "critical": "[CRITICAL]"
        }
        
        print("\n" + "="*60)
        print(f"GUARDRAIL DASHBOARD - {status.upper()}")
        print("="*60)
        
        print(f"\nStatus: {status_colors.get(status, '[?]')} {status.upper()}")
        print(f"Total Violations: {summary['total_violations']}")
        print(f"Recent (24h): {summary['recent_violations']}")
        
        # By severity
        if summary['by_severity']:
            print("\nBy Severity:")
            for severity, count in sorted(summary['by_severity'].items(), 
                                         key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x[0], 4)):
                print(f"  {severity.upper()}: {count}")
                
        # By type
        if summary['by_type']:
            print("\nBy Type:")
            for vtype, count in sorted(summary['by_type'].items(), key=lambda x: -x[1])[:5]:
                print(f"  {vtype}: {count}")
                
        # Critical modules
        if summary['critical_modules']:
            print("\nModules Requiring Attention:")
            for module in summary['critical_modules']:
                count = summary['by_module'][module]
                print(f"  {module}: {count} violations")
                
        print("="*60)
        
    def generate_trends(self, days: int = 7) -> Dict[str, Any]:
        """Generate trend analysis over the specified number of days."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)
        
        # Filter recent violations
        recent = [
            v for v in self.violations
            if self._is_within_range(v.get("timestamp"), cutoff, now)
        ]
        
        if not recent:
            return {"message": f"No violations in the last {days} days"}
            
        # Group by day
        by_day = defaultdict(lambda: defaultdict(int))
        
        for violation in recent:
            timestamp = violation.get("timestamp", "")
            try:
                parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                day = parsed.date()
                vtype = violation.get("type", "unknown")
                by_day[day][vtype] += 1
            except:
                continue
                
        # Calculate trend
        days_list = sorted(by_day.keys())
        if len(days_list) >= 2:
            first_day_total = sum(by_day[days_list[0]].values())
            last_day_total = sum(by_day[days_list[-1]].values())
            
            if first_day_total > 0:
                change = ((last_day_total - first_day_total) / first_day_total) * 100
            else:
                change = 0
                
            trend = "improving" if change < 0 else "worsening" if change > 0 else "stable"
        else:
            change = 0
            trend = "insufficient_data"
            
        return {
            "period_days": days,
            "total_in_period": len(recent),
            "daily_breakdown": {
                str(day): dict(counts) for day, counts in by_day.items()
            },
            "trend": trend,
            "change_percent": round(change, 1),
        }
        
    def _is_within_range(self, timestamp: str, start: datetime, end: datetime) -> bool:
        """Check if timestamp is within a range."""
        if not timestamp:
            return False
            
        try:
            ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return start <= ts <= end
        except:
            return False
            
    def print_trends(self, days: int = 7) -> None:
        """Print trend analysis."""
        trends = self.generate_trends(days)
        
        print(f"\nTREND ANALYSIS (Last {days} Days)")
        print("="*60)
        
        if "message" in trends:
            print(trends["message"])
            return
            
        print(f"Total Violations: {trends['total_in_period']}")
        print(f"Trend: {trends['trend'].upper()}")
        print(f"Change: {trends['change_percent']}%")
        
        if trends['daily_breakdown']:
            print("\nDaily Breakdown:")
            for day, counts in sorted(trends['daily_breakdown'].items()):
                total = sum(counts.values())
                print(f"  {day}: {total} violations")
                for vtype, count in counts.items():
                    print(f"    - {vtype}: {count}")
                    
    def export_report(self, output_path: str, format: str = "html") -> None:
        """Export dashboard report to file."""
        if format == "html":
            self._export_html(output_path)
        elif format == "json":
            self._export_json(output_path)
        elif format == "markdown":
            self._export_markdown(output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    def _export_html(self, output_path: str) -> None:
        """Export as HTML report."""
        summary = self.generate_summary()
        trends = self.generate_trends()
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Guardrail Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #333; color: white; padding: 20px; border-radius: 5px; }}
        .status-clean {{ color: green; }}
        .status-warning {{ color: orange; }}
        .status-critical {{ color: red; }}
        .section {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ font-size: 12px; color: #666; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Guardrail Dashboard</h1>
        <p>Generated: {datetime.now(timezone.utc).isoformat()}</p>
    </div>
    
    <div class="section">
        <h2>Status: <span class="status-{summary['status']}">{summary['status'].upper()}</span></h2>
        <div class="metric">
            <div class="metric-value">{summary['total_violations']}</div>
            <div class="metric-label">Total Violations</div>
        </div>
        <div class="metric">
            <div class="metric-value">{summary.get('recent_violations', 0)}</div>
            <div class="metric-label">Recent (24h)</div>
        </div>
    </div>
    
    <div class="section">
        <h2>Violations by Type</h2>
        <table>
            <tr><th>Type</th><th>Count</th></tr>
"""
        
        for vtype, count in sorted(summary.get('by_type', {}).items(), key=lambda x: -x[1]):
            html += f"            <tr><td>{vtype}</td><td>{count}</td></tr>\n"
            
        html += """        </table>
    </div>
    
    <div class="section">
        <h2>Violations by Severity</h2>
        <table>
            <tr><th>Severity</th><th>Count</th></tr>
"""
        
        for severity, count in sorted(summary.get('by_severity', {}).items(), 
                                     key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x[0], 4)):
            html += f"            <tr><td>{severity.upper()}</td><td>{count}</td></tr>\n"
            
        html += f"""        </table>
    </div>
    
    <div class="section">
        <h2>Trends (Last 7 Days)</h2>
        <p>Trend: {trends.get('trend', 'N/A').upper()}</p>
        <p>Change: {trends.get('change_percent', 0)}%</p>
    </div>
</body>
</html>"""
        
        with open(output_path, 'w') as f:
            f.write(html)
            
    def _export_json(self, output_path: str) -> None:
        """Export as JSON report."""
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": self.generate_summary(),
            "trends": self.generate_trends(),
            "violations": self.violations,
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
            
    def _export_markdown(self, output_path: str) -> None:
        """Export as Markdown report."""
        summary = self.generate_summary()
        
        md = f"""# Guardrail Dashboard Report

**Generated:** {datetime.now(timezone.utc).isoformat()}

## Status: {summary['status'].upper()}

### Summary

- **Total Violations:** {summary['total_violations']}
- **Recent (24h):** {summary.get('recent_violations', 0)}

### By Severity

"""
        
        for severity, count in sorted(summary.get('by_severity', {}).items(),
                                     key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x[0], 4)):
            md += f"- **{severity.upper()}:** {count}\n"
            
        md += f"""

### By Type

"""
        
        for vtype, count in sorted(summary.get('by_type', {}).items(), key=lambda x: -x[1]):
            md += f"- {vtype}: {count}\n"
            
        md += f"""

### Critical Modules

"""
        
        if summary.get('critical_modules'):
            for module in summary['critical_modules']:
                count = summary['by_module'][module]
                md += f"- {module}: {count} violations\n"
        else:
            md += "No critical modules identified.\n"
            
        with open(output_path, 'w') as f:
            f.write(md)
            
    def plot_trends(self, output_path: Optional[str] = None) -> None:
        """Generate matplotlib plot of trends (if available)."""
        if not HAS_MATPLOTLIB:
            print("Matplotlib not available. Install with: pip install matplotlib")
            return
            
        trends = self.generate_trends(days=14)
        
        if "message" in trends:
            print(trends["message"])
            return
            
        # Prepare data
        daily = trends['daily_breakdown']
        dates = [datetime.strptime(d, '%Y-%m-%d') for d in sorted(daily.keys())]
        totals = [sum(daily[str(d.date())].values()) for d in dates]
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(dates, totals, marker='o', linewidth=2, markersize=8)
        ax.set_xlabel('Date')
        ax.set_ylabel('Violations')
        ax.set_title('Guardrail Violations Trend (Last 14 Days)')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Trend plot saved to: {output_path}")
        else:
            plt.show()
            
    def plot_distribution(self, output_path: Optional[str] = None) -> None:
        """Generate pie chart of violation distribution."""
        if not HAS_MATPLOTLIB:
            print("Matplotlib not available. Install with: pip install matplotlib")
            return
            
        summary = self.generate_summary()
        
        by_type = summary.get('by_type', {})
        if not by_type:
            print("No violations to plot")
            return
            
        # Create pie chart
        fig, ax = plt.subplots(figsize=(10, 8))
        
        types = list(by_type.keys())
        counts = list(by_type.values())
        
        colors = plt.cm.Set3(range(len(types)))
        
        wedges, texts, autotexts = ax.pie(
            counts, 
            labels=types, 
            autopct='%1.1f%%',
            colors=colors,
            textprops={'fontsize': 10}
        )
        
        ax.set_title('Guardrail Violations by Type', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Distribution plot saved to: {output_path}")
        else:
            plt.show()


def create_sample_data(output_path: str, num_violations: int = 50) -> None:
    """Create sample violation data for testing the dashboard."""
    violation_types = [
        "hardcoded_path",
        "conditional_import",
        "circular_import",
        "side_effect",
        "missing_dependency"
    ]
    
    modules = [
        "data_loader",
        "ml_processor",
        "component_a",
        "component_b",
        "config_manager",
        "utils",
        "main",
        "api_handler"
    ]
    
    severities = ["critical", "high", "medium", "low"]
    severities_weights = [0.1, 0.2, 0.4, 0.3]
    
    import random
    
    violations = []
    now = datetime.now(timezone.utc)
    
    for i in range(num_violations):
        # Random time in last 7 days
        hours_ago = random.randint(0, 24*7)
        timestamp = (now - timedelta(hours=hours_ago)).isoformat()
        
        violation = {
            "id": f"VIO-{i:04d}",
            "type": random.choice(violation_types),
            "module": random.choice(modules),
            "severity": random.choices(severities, weights=severities_weights)[0],
            "timestamp": timestamp,
            "message": f"Sample violation {i}",
            "file": f"src/{random.choice(modules)}.py",
        }
        
        violations.append(violation)
        
    data = {
        "generated_at": now.isoformat(),
        "violations": violations,
        "metrics": {
            "total_scanned": 100,
            "modules_analyzed": 20,
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    print(f"Sample data created: {output_path}")


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Guardrail Monitoring Dashboard")
    parser.add_argument("--data", "-d", help="Path to violations data JSON file")
    parser.add_argument("--summary", "-s", action="store_true", help="Print summary")
    parser.add_argument("--trends", "-t", action="store_true", help="Print trends")
    parser.add_argument("--export", "-e", help="Export report to file")
    parser.add_argument("--format", "-f", choices=["html", "json", "markdown"], 
                       default="html", help="Export format")
    parser.add_argument("--plot-trends", action="store_true", help="Generate trend plot")
    parser.add_argument("--plot-dist", action="store_true", help="Generate distribution plot")
    parser.add_argument("--create-sample", help="Create sample data file")
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_data(args.create_sample)
        sys.exit(0)
        
    # Create dashboard
    dashboard = GuardrailDashboard(args.data)
    
    if args.summary or not any([args.trends, args.export, args.plot_trends, args.plot_dist]):
        dashboard.print_summary()
        
    if args.trends:
        dashboard.print_trends()
        
    if args.export:
        dashboard.export_report(args.export, args.format)
        print(f"Report exported to: {args.export}")
        
    if args.plot_trends:
        output = args.export.replace(f".{args.format}", "_trends.png") if args.export else None
        dashboard.plot_trends(output)
        
    if args.plot_dist:
        output = args.export.replace(f".{args.format}", "_dist.png") if args.export else None
        dashboard.plot_distribution(output)
