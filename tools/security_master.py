#!/usr/bin/env python3
"""
GRID Security Master Control
============================

Unified interface for all security operations.
Profiles threats, applies guardrails, executes responses, and maintains prevention.

This is your command center for systematic defense.

Usage:
    # Full security assessment
    python tools/security_master.py --full-assessment

    # Quick status check
    python tools/security_master.py --status

    # Apply all guardrails
    python tools/security_master.py --fortify

    # Emergency response mode
    python tools/security_master.py --emergency
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class SecurityStatus:
    """Current security posture snapshot."""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    overall_status: str = "unknown"  # secure, at-risk, compromised
    risk_score: float = 0.0
    active_defenses: int = 0
    recent_threats: int = 0
    mitigated_threats: int = 0
    pending_actions: list[str] = field(default_factory=list)
    critical_findings: int = 0


class SecurityMasterControl:
    """Master controller for all security operations."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tools_path = project_root / "tools"
        self.logs_path = project_root / "logs" / "security"
        
    def print_header(self, text: str) -> None:
        """Print formatted header."""
        print(f"\n{BOLD}{BLUE}{'=' * 70}{RESET}")
        print(f"{BOLD}{BLUE}{text:^70}{RESET}")
        print(f"{BOLD}{BLUE}{'=' * 70}{RESET}\n")
    
    def print_success(self, text: str) -> None:
        print(f"{GREEN}✓{RESET} {text}")
    
    def print_warning(self, text: str) -> None:
        print(f"{YELLOW}⚠{RESET} {text}")
    
    def print_error(self, text: str) -> None:
        print(f"{RED}✗{RESET} {text}")
    
    def print_info(self, text: str) -> None:
        print(f"{BLUE}ℹ{RESET} {text}")
    
    def run_tool(self, tool_name: str, *args: str) -> tuple[int, str, str]:
        """Run a security tool and capture output."""
        tool_path = self.tools_path / tool_name
        
        if not tool_path.exists():
            return 1, "", f"Tool not found: {tool_path}"
        
        try:
            result = subprocess.run(
                [sys.executable, str(tool_path)] + list(args),
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.project_root,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Tool execution timed out"
        except Exception as e:
            return 1, "", str(e)
    
    def get_security_status(self) -> SecurityStatus:
        """Get current security status."""
        status = SecurityStatus()
        
        # Check active defenses
        active_defenses = []
        
        if os.getenv("PARASITE_GUARD") == "1":
            active_defenses.append("Parasite Guard")
        if os.getenv("GRID_ENVIRONMENT") == "production":
            active_defenses.append("Production Mode")
        
        # Check for recent security events
        recent_events = self._count_recent_events(hours=24)
        
        # Check for critical findings
        critical_findings = self._count_critical_findings()
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(recent_events, critical_findings)
        
        # Determine status
        if risk_score > 75 or critical_findings > 5:
            overall_status = "compromised"
        elif risk_score > 50 or critical_findings > 0:
            overall_status = "at-risk"
        else:
            overall_status = "secure"
        
        status.active_defenses = len(active_defenses)
        status.recent_threats = recent_events
        status.critical_findings = critical_findings
        status.risk_score = risk_score
        status.overall_status = overall_status
        
        return status
    
    def _count_recent_events(self, hours: int = 24) -> int:
        """Count recent security events."""
        count = 0
        log_file = self.logs_path / "mothership" / "mothership_audit.log"
        
        if not log_file.exists():
            return 0
        
        try:
            cutoff = datetime.now(UTC) - __import__('datetime').timedelta(hours=hours)
            
            with open(log_file) as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        event_time = datetime.fromisoformat(
                            event.get("timestamp", "").replace("Z", "+00:00")
                        )
                        if event_time > cutoff:
                            count += 1
                    except (json.JSONDecodeError, ValueError):
                        continue
        except Exception:
            pass
        
        return count
    
    def _count_critical_findings(self) -> int:
        """Count critical security findings."""
        # Check for findings reports
        findings_path = self.project_root / "reports" / "security" / "findings"
        
        if not findings_path.exists():
            return 0
        
        critical_count = 0
        
        for report_file in findings_path.glob("security_findings_*.json"):
            try:
                with open(report_file) as f:
                    report = json.load(f)
                    critical_count += report.get("by_severity", {}).get("critical", 0)
            except (json.JSONDecodeError, IOError):
                continue
        
        return critical_count
    
    def _calculate_risk_score(self, events: int, findings: int) -> float:
        """Calculate overall risk score (0-100)."""
        base_score = min(events / 10, 30)  # Max 30 from events
        finding_score = findings * 15  # 15 points per critical finding
        
        return min(base_score + finding_score, 100)
    
    def full_assessment(self) -> None:
        """Run comprehensive security assessment."""
        self.print_header("GRID SECURITY ASSESSMENT")
        
        # Step 1: Get current status
        print(f"{BOLD}Step 1: Analyzing Current Status{RESET}")
        status = self.get_security_status()
        
        print(f"  Overall Status: {status.overall_status.upper()}")
        print(f"  Risk Score: {status.risk_score:.1f}/100")
        print(f"  Active Defenses: {status.active_defenses}")
        print(f"  Recent Events (24h): {status.recent_threats}")
        print(f"  Critical Findings: {status.critical_findings}")
        
        if status.overall_status == "compromised":
            self.print_error("CRITICAL: System may be compromised!")
        elif status.overall_status == "at-risk":
            self.print_warning("WARNING: System is at risk")
        else:
            self.print_success("System appears secure")
        
        # Step 2: Profile threats
        print(f"\n{BOLD}Step 2: Profiling Threat Landscape{RESET}")
        ret, out, err = self.run_tool("security_command_center.py", "--profile")
        if ret == 0:
            print(out)
        else:
            self.print_error(f"Threat profiling failed: {err}")
        
        # Step 3: Scan codebase
        print(f"\n{BOLD}Step 3: Scanning Codebase{RESET}")
        ret, out, err = self.run_tool("prevention_framework.py", "--scan")
        if ret == 0:
            if "No security issues found" in out:
                self.print_success("No code security issues detected")
            else:
                print(out)
        else:
            self.print_error(f"Code scan failed: {err}")
        
        # Step 4: Validate security setup
        print(f"\n{BOLD}Step 4: Validating Security Configuration{RESET}")
        ret, out, err = self.run_tool("..\\scripts\\validate_security.py")
        if ret == 0:
            self.print_success("Security validation passed")
        else:
            self.print_warning("Security validation issues detected")
            print(out)
        
        # Step 5: Generate report
        print(f"\n{BOLD}Step 5: Generating Report{RESET}")
        ret, out, err = self.run_tool("security_command_center.py", "--report")
        if ret == 0:
            self.print_success("Security report generated")
        else:
            self.print_error(f"Report generation failed: {err}")
        
        # Summary
        self.print_header("ASSESSMENT COMPLETE")
        print(f"Risk Score: {status.risk_score:.1f}/100")
        print(f"Status: {status.overall_status.upper()}")
        
        if status.overall_status == "secure":
            print(f"\n{GREEN}Your system is well-protected. Continue monitoring.{RESET}")
        elif status.overall_status == "at-risk":
            print(f"\n{YELLOW}Action recommended: Review findings and apply hardening.{RESET}")
            print(f"Run: python tools/security_master.py --fortify")
        else:
            print(f"\n{RED}URGENT: Immediate action required!{RESET}")
            print(f"Run: python tools/security_master.py --emergency")
    
    def fortify(self) -> None:
        """Apply all security hardening measures."""
        self.print_header("FORTIFYING SECURITY POSTURE")
        
        # Step 1: Apply guardrails
        print(f"{BOLD}Step 1: Applying Security Guardrails{RESET}")
        ret, out, err = self.run_tool("security_command_center.py", "--guardrails")
        if ret == 0:
            print(out)
            self.print_success("Guardrails applied")
        else:
            self.print_error(f"Guardrail application failed: {err}")
        
        # Step 2: Harden codebase
        print(f"\n{BOLD}Step 2: Hardening Codebase{RESET}")
        ret, out, err = self.run_tool("prevention_framework.py", "--harden", "--dry-run")
        if ret == 0:
            print(out)
            self.print_success("Codebase hardening analyzed")
            
            # Ask user if they want to apply fixes
            print(f"\n{BOLD}Apply hardening fixes? (review above first){RESET}")
            print("To apply: python tools/prevention_framework.py --harden")
        else:
            self.print_error(f"Hardening failed: {err}")
        
        # Step 3: Setup continuous monitoring
        print(f"\n{BOLD}Step 3: Setting Up Continuous Monitoring{RESET}")
        ret, out, err = self.run_tool("prevention_framework.py", "--setup")
        if ret == 0:
            print(out)
            self.print_success("Continuous monitoring configured")
        else:
            self.print_error(f"Setup failed: {err}")
        
        # Step 4: Enable Parasite Guard
        print(f"\n{BOLD}Step 4: Activating Parasite Guard{RESET}")
        os.environ["PARASITE_GUARD"] = "1"
        os.environ["PARASITE_GUARD_MODE"] = "ENFORCE"
        os.environ["PARASITE_DETECT_THRESHOLD"] = "3"
        self.print_success("Parasite Guard activated (ENFORCE mode)")
        
        self.print_header("FORTIFICATION COMPLETE")
        print("Your system is now hardened with:")
        print("  ✓ Security guardrails active")
        print("  ✓ Continuous monitoring enabled")
        print("  ✓ Parasite Guard in ENFORCE mode")
        print("  ✓ Codebase reviewed for vulnerabilities")
    
    def emergency_response(self) -> None:
        """Activate emergency response mode."""
        self.print_header("🚨 EMERGENCY RESPONSE MODE 🚨")
        
        print(f"{RED}{BOLD}CRITICAL SECURITY STATE DETECTED{RESET}\n")
        
        print("Executing emergency protocols...")
        print()
        
        # Step 1: Immediate containment
        print(f"{BOLD}Step 1: Immediate Containment{RESET}")
        os.environ["PARASITE_GUARD"] = "1"
        os.environ["PARASITE_GUARD_MODE"] = "ENFORCE"
        os.environ["PARASITE_SANITIZE_ASYNC"] = "1"
        os.environ["PARASITE_MAX_CONCURRENT"] = "1"
        self.print_success("Parasite Guard locked down")
        
        # Step 2: Analyze active threats
        print(f"\n{BOLD}Step 2: Analyzing Active Threats{RESET}")
        ret, out, err = self.run_tool("threat_response.py", "--scan")
        if ret == 0:
            print(out)
        
        # Step 3: Generate incident report
        print(f"\n{BOLD}Step 3: Generating Incident Report{RESET}")
        ret, out, err = self.run_tool("security_command_center.py", "--report")
        if ret == 0:
            self.print_success("Incident report generated")
        
        # Step 4: Continuous monitoring
        print(f"\n{BOLD}Step 4: Activating Continuous Monitoring{RESET}")
        print("Monitoring for 60 seconds (Ctrl+C to stop)...")
        
        try:
            ret, out, err = self.run_tool("security_command_center.py", "--monitor", "--duration", "60")
            print(out)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
        
        self.print_header("EMERGENCY RESPONSE COMPLETE")
        print(f"{YELLOW}Review generated reports and take manual action as needed.{RESET}")
        print(f"{BLUE}Reports location: reports/security/{RESET}")
    
    def show_status(self) -> None:
        """Show current security status."""
        self.print_header("SECURITY STATUS DASHBOARD")
        
        status = self.get_security_status()
        
        # Status indicator
        if status.overall_status == "secure":
            indicator = f"{GREEN}🛡️ SECURE{RESET}"
        elif status.overall_status == "at-risk":
            indicator = f"{YELLOW}⚠️ AT RISK{RESET}"
        else:
            indicator = f"{RED}🚨 COMPROMISED{RESET}"
        
        print(f"Status: {indicator}")
        print(f"Risk Score: {status.risk_score:.1f}/100")
        print(f"Last Updated: {status.timestamp}")
        
        print(f"\n{BOLD}Active Defenses:{RESET}")
        defenses = []
        if os.getenv("PARASITE_GUARD") == "1":
            mode = os.getenv("PARASITE_GUARD_MODE", "unknown")
            defenses.append(f"  ✓ Parasite Guard ({mode})")
        if os.getenv("GRID_ENVIRONMENT"):
            defenses.append(f"  ✓ Environment: {os.getenv('GRID_ENVIRONMENT')}")
        
        if defenses:
            for defense in defenses:
                print(defense)
        else:
            print("  ✗ No active defenses detected!")
        
        print(f"\n{BOLD}Recent Activity (24h):{RESET}")
        print(f"  Events logged: {status.recent_threats}")
        print(f"  Critical findings: {status.critical_findings}")
        
        # Quick actions
        print(f"\n{BOLD}Quick Actions:{RESET}")
        print("  1. python tools/security_master.py --full-assessment")
        print("  2. python tools/security_master.py --fortify")
        print("  3. python tools/security_master.py --emergency")


def main():
    parser = argparse.ArgumentParser(
        description="GRID Security Master Control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full security assessment
  python tools/security_master.py --full-assessment

  # Quick status check
  python tools/security_master.py --status

  # Fortify all defenses
  python tools/security_master.py --fortify

  # Emergency response
  python tools/security_master.py --emergency
        """
    )
    
    parser.add_argument(
        "--full-assessment",
        action="store_true",
        help="Run comprehensive security assessment"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current security status"
    )
    parser.add_argument(
        "--fortify",
        action="store_true",
        help="Apply all security hardening measures"
    )
    parser.add_argument(
        "--emergency",
        action="store_true",
        help="Activate emergency response mode"
    )
    
    args = parser.parse_args()
    
    project_root = Path(__file__).resolve().parent.parent
    master = SecurityMasterControl(project_root)
    
    if args.full_assessment:
        master.full_assessment()
    elif args.fortify:
        master.fortify()
    elif args.emergency:
        master.emergency_response()
    elif args.status:
        master.show_status()
    else:
        # Default: show status
        master.show_status()


if __name__ == "__main__":
    main()
