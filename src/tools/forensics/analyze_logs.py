#!/usr/bin/env python3
"""
Log Analysis Tool for Forensic Investigation
============================================
Parses audit logs and MCP server logs for unauthorized access attempts.
Reuses existing forensic_log_analyzer for comprehensive analysis.
"""

import sys
import os
from pathlib import Path

# Add security module to path
sys.path.append('e:/grid/security')

def main():
    """Main analysis function."""
    print("🔍 Starting comprehensive log analysis...")

    # Import the existing forensic analyzer
    try:
        # If your actual class name in forensic_log_analyzer.py is different, update this import accordingly.
        from forensic_log_analyzer import LogAnalyzer
    except ImportError as e:
        print(f"❌ Error importing forensic_log_analyzer: {e}")
        print("Please ensure forensic_log_analyzer.py is available in security/")
        sys.exit(1)

    # Validate that LogAnalyzer exists in the module, else raise informative error
    if not hasattr(sys.modules.get('forensic_log_analyzer'), 'LogAnalyzer'):
        print("❌ 'LogAnalyzer' class not found in forensic_log_analyzer.py.")
        print("Check the definition in security/forensic_log_analyzer.py.")
        sys.exit(1)

    analyzer = LogAnalyzer()
    print("📊 Analyzing network access logs...")
    network_report = analyzer.analyze_network_logs()
    print("Network Analysis:")
    print(network_report)

    # Analyze audit logs
    print("\n📋 Analyzing audit logs...")
    audit_report = analyzer.analyze_audit_logs()
    print("Audit Analysis:")
    print(audit_report)

    # Generate combined report
    print("\n📄 Generating forensic report...")
    report = analyzer.generate_report()
    print("Forensic Report:")
    print(report)

    # Save report
    report_path = Path('e:/grid/security/logs/forensic_analysis_report.md')
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n✅ Report saved to: {report_path}")

    # Additional MCP-specific analysis
    print("\n🔧 Analyzing MCP server logs...")

    mcp_logs = [
        'e:/grid/work/GRID/workspace/mcp/servers/filesystem/audit.log',
        'e:/grid/work/GRID/workspace/mcp/servers/playwright/audit.log'
    ]

    for log_path in mcp_logs:
        if os.path.exists(log_path):
            print(f"📝 Checking MCP log: {log_path}")
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Count security events
            denied_count = 0
            access_count = 0
            error_count = 0

            for line in lines[-100:]:  # Last 100 entries
                if 'AUTHZ_ACCESS_DENIED' in line:
                    denied_count += 1
                elif 'DATA_ACCESS' in line:
                    access_count += 1
                elif 'error' in line.lower():
                    error_count += 1

            print(f"   Access Denied: {denied_count}")
            print(f"   Data Access: {access_count}")
            print(f"   Errors: {error_count}")
        else:
            print(f"⚠️  MCP log not found: {log_path}")

    print("\n✅ Log analysis complete.")


if __name__ == "__main__":
    main()
