#!/usr/bin/env python3
"""
GRID Daily Routine Automation
Runs morning health checks, priority queries, and experience summaries
"""

import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path

class GridDailyRoutine:
    def __init__(self):
        self.venv = ".venv\\Scripts\\python.exe"
        self.api_base = "http://localhost:8080"
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def print_header(self, title):
        """Print formatted header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def print_section(self, title):
        """Print formatted section"""
        print(f"\n{title}")
        print("-" * 60)
    
    def run_command(self, cmd, description=""):
        """Run command and return success status"""
        if description:
            print(f"  {description}...", end=" ", flush=True)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=10)
            if result.returncode == 0:
                if description:
                    print("✓")
                return True, result.stdout
            else:
                if description:
                    print("✗")
                return False, result.stderr
        except subprocess.TimeoutExpired:
            if description:
                print("✗ (timeout)")
            return False, "Command timeout"
        except Exception as e:
            if description:
                print(f"✗ ({e})")
            return False, str(e)
    
    def check_api_health(self):
        """Check API server health"""
        self.print_section("1. API Server Health")
        success, output = self.run_command(
            'curl -s http://localhost:8080/health',
            "Checking API health"
        )
        if success:
            try:
                health = json.loads(output)
                print(f"  Status: {health.get('status', 'unknown')}")
                return True
            except:
                print(f"  Response: {output[:100]}")
                return True
        else:
            print(f"  ✗ API server not responding")
            return False
    
    def get_experience_summary(self):
        """Get agentic system experience summary"""
        self.print_section("2. Agentic System Experience")
        success, output = self.run_command(
            'curl -s http://localhost:8080/api/v1/agentic/experience',
            "Fetching experience summary"
        )
        if success:
            try:
                exp = json.loads(output)
                print(f"  Total Cases: {exp.get('total_cases', 0)}")
                print(f"  Success Rate: {exp.get('success_rate', 0)*100:.1f}%")
                
                categories = exp.get('category_distribution', {})
                if categories:
                    print(f"  Top Categories:")
                    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]:
                        print(f"    - {cat}: {count}")
                return True
            except:
                print(f"  Response: {output[:200]}")
                return False
        else:
            print(f"  ✗ Could not fetch experience")
            return False
    
    def query_rag_priorities(self):
        """Query RAG for today's priorities"""
        self.print_section("3. RAG Knowledge Query")
        
        # Check if Ollama is running
        success, _ = self.run_command(
            'curl -s http://localhost:11434/api/tags',
            "Checking Ollama availability"
        )
        
        if not success:
            print("  ⚠ Ollama not running - skipping RAG query")
            print("  Start Ollama to enable: ollama serve")
            return False
        
        print("  ✓ Ollama is available")
        
        # Try to query RAG
        success, output = self.run_command(
            f'{self.venv} -m tools.rag.cli query "today priorities focus" 2>&1',
            "Querying RAG for priorities"
        )
        
        if success:
            # Extract relevant parts from output
            lines = output.split('\n')
            results = [l for l in lines if l.strip() and not l.startswith('2026')]
            if results:
                print("  Results:")
                for line in results[:5]:
                    if line.strip():
                        print(f"    {line.strip()[:70]}")
            return True
        else:
            print("  ⚠ RAG query failed (index may not be built)")
            print("  Build index: .venv\\Scripts\\python.exe -m tools.rag.cli index . --rebuild --curate")
            return False
    
    def check_skills_availability(self):
        """Verify skills are available"""
        self.print_section("4. Skills Pipeline Status")
        success, output = self.run_command(
            f'{self.venv} -m grid skills list 2>&1',
            "Checking available skills"
        )
        
        if success:
            try:
                data = json.loads(output)
                skills = data.get('skills', [])
                print(f"  Available Skills: {len(skills)}")
                print(f"  Key Skills:")
                key_skills = ['context.refine', 'transform.schema_map', 'compress.articulate']
                for skill in key_skills:
                    found = any(s['id'] == skill for s in skills)
                    status = "✓" if found else "✗"
                    print(f"    {status} {skill}")
                return True
            except:
                print(f"  Response: {output[:100]}")
                return False
        else:
            print(f"  ✗ Could not list skills")
            return False
    
    def generate_report(self):
        """Generate daily report"""
        self.print_section("5. Daily Report")
        
        report = {
            "timestamp": self.timestamp,
            "checks": {
                "api_health": "pending",
                "experience": "pending",
                "rag_available": "pending",
                "skills_available": "pending"
            }
        }
        
        # Run all checks
        report["checks"]["api_health"] = "pass" if self.check_api_health() else "fail"
        report["checks"]["experience"] = "pass" if self.get_experience_summary() else "fail"
        report["checks"]["rag_available"] = "pass" if self.query_rag_priorities() else "fail"
        report["checks"]["skills_available"] = "pass" if self.check_skills_availability() else "fail"
        
        # Summary
        self.print_section("Summary")
        passed = sum(1 for v in report["checks"].values() if v == "pass")
        total = len(report["checks"])
        print(f"  Checks Passed: {passed}/{total}")
        print(f"  Status: {'✓ All systems operational' if passed == total else '⚠ Some systems need attention'}")
        
        return report
    
    def run(self):
        """Run complete daily routine"""
        self.print_header("GRID Daily Routine")
        print(f"  Time: {self.timestamp}")
        
        report = self.generate_report()
        
        self.print_header("Daily Routine Complete")
        print(f"\nNext Steps:")
        print(f"  1. Review priorities above")
        print(f"  2. Create agentic cases for today's tasks")
        print(f"  3. Use skills pipeline for text processing")
        print(f"  4. Query RAG for knowledge lookup")
        print(f"\nDocumentation:")
        print(f"  - Integration Guide: INTEGRATION_GUIDE.md")
        print(f"  - Quick Reference: QUICK_REFERENCE.md")
        print(f"  - API Docs: http://localhost:8080/docs")
        print()
        
        return report

if __name__ == "__main__":
    routine = GridDailyRoutine()
    report = routine.run()
    sys.exit(0)
