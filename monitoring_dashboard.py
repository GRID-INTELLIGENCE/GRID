#!/usr/bin/env python3
"""
GRID Systems Monitoring Dashboard
Real-time monitoring of all three systems
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


class GridMonitoringDashboard:
    def __init__(self):
        self.venv = ".venv\\Scripts\\python.exe"
        self.api_base = "http://localhost:8080"
        self.metrics = {}

    def print_header(self, title):
        """Print formatted header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")

    def print_section(self, title):
        """Print formatted section"""
        print(f"\n{title}")
        print("-" * 60)

    def run_command(self, cmd, timeout=10):
        """Run command and return result"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=timeout)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Timeout"
        except Exception as e:
            return False, "", str(e)

    def get_api_metrics(self):
        """Get API server metrics"""
        self.print_section("API Server Status")

        # Health check
        success, output, _ = self.run_command('curl -s http://localhost:8080/health')
        if success:
            try:
                health = json.loads(output)
                print(f"  Status: {health.get('status', 'unknown')}")
                print("  ✓ API Server: RUNNING")
                self.metrics['api_health'] = 'running'
                return True
            except:
                print("  ✓ API Server: RESPONDING")
                self.metrics['api_health'] = 'running'
                return True
        else:
            print("  ✗ API Server: NOT RESPONDING")
            self.metrics['api_health'] = 'down'
            return False

    def get_agentic_metrics(self):
        """Get agentic system metrics"""
        self.print_section("Agentic System Metrics")

        success, output, _ = self.run_command('curl -s http://localhost:8080/api/v1/agentic/experience')
        if success:
            try:
                exp = json.loads(output)
                total_cases = exp.get('total_cases', 0)
                success_rate = exp.get('success_rate', 0)

                print(f"  Total Cases: {total_cases}")
                print(f"  Success Rate: {success_rate*100:.1f}%")

                categories = exp.get('category_distribution', {})
                if categories:
                    print("  Top Categories:")
                    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]:
                        print(f"    • {cat}: {count}")

                self.metrics['agentic_cases'] = total_cases
                self.metrics['agentic_success_rate'] = success_rate
                return True
            except:
                print("  ✗ Failed to parse experience data")
                return False
        else:
            print("  ✗ Could not fetch experience metrics")
            return False

    def get_rag_metrics(self):
        """Get RAG system metrics"""
        self.print_section("RAG System Metrics")

        # Check Ollama
        success, _, _ = self.run_command('curl -s http://localhost:11434/api/tags')
        if success:
            print("  Ollama Status: ✓ RUNNING")
            self.metrics['ollama_status'] = 'running'
        else:
            print("  Ollama Status: ✗ NOT RUNNING")
            self.metrics['ollama_status'] = 'down'

        # Check RAG database
        rag_db = Path(".rag_db")
        if rag_db.exists():
            # Count files in RAG database
            db_files = list(rag_db.rglob("*"))
            print(f"  RAG Database: ✓ EXISTS ({len(db_files)} files)")
            self.metrics['rag_db_files'] = len(db_files)
        else:
            print("  RAG Database: ✗ NOT FOUND")
            self.metrics['rag_db_files'] = 0

        # Check cache
        cache_dir = rag_db / "cache" if rag_db.exists() else None
        if cache_dir and cache_dir.exists():
            cache_files = list(cache_dir.glob("*"))
            print(f"  Cache: {len(cache_files)} entries")
            self.metrics['rag_cache_entries'] = len(cache_files)
        else:
            print("  Cache: Empty")
            self.metrics['rag_cache_entries'] = 0

    def get_skills_metrics(self):
        """Get skills pipeline metrics"""
        self.print_section("Skills Pipeline Status")

        success, output, _ = self.run_command(f'{self.venv} -m grid skills list')
        if success:
            try:
                data = json.loads(output)
                skills = data.get('skills', [])
                print(f"  Available Skills: {len(skills)}")

                key_skills = ['context.refine', 'transform.schema_map', 'compress.articulate']
                available = sum(1 for s in skills if s['id'] in key_skills)
                print(f"  Core Skills: {available}/{len(key_skills)}")

                self.metrics['total_skills'] = len(skills)
                self.metrics['core_skills_available'] = available
                return True
            except:
                print("  ✗ Failed to parse skills data")
                return False
        else:
            print("  ✗ Could not list skills")
            return False

    def get_case_references_metrics(self):
        """Get case references metrics"""
        self.print_section("Case References")

        case_refs = Path(".case_references")
        if case_refs.exists():
            ref_files = list(case_refs.glob("*.json"))
            print(f"  Total Cases: {len(ref_files)}")

            if ref_files:
                # Get latest case
                latest = max(ref_files, key=lambda p: p.stat().st_mtime)
                print(f"  Latest Case: {latest.name}")

            self.metrics['case_references'] = len(ref_files)
        else:
            print("  Case References: Not created yet")
            self.metrics['case_references'] = 0

    def get_system_health(self):
        """Get overall system health"""
        self.print_section("System Health Summary")

        health_checks = {
            'API Server': self.metrics.get('api_health') == 'running',
            'Agentic System': self.metrics.get('agentic_cases', 0) >= 0,
            'Skills Pipeline': self.metrics.get('core_skills_available', 0) > 0,
            'RAG Database': self.metrics.get('rag_db_files', 0) > 0,
        }

        passed = sum(1 for v in health_checks.values() if v)
        total = len(health_checks)

        for check, status in health_checks.items():
            symbol = "✓" if status else "✗"
            print(f"  {symbol} {check}")

        print(f"\n  Overall Health: {passed}/{total} systems operational")

        if passed == total:
            print("  Status: ✓ ALL SYSTEMS OPERATIONAL")
        elif passed >= total - 1:
            print("  Status: ⚠ MOSTLY OPERATIONAL")
        else:
            print("  Status: ✗ DEGRADED")

    def get_performance_metrics(self):
        """Get performance metrics"""
        self.print_section("Performance Metrics")

        # Test skill execution time
        args = json.dumps({"text": "test", "use_llm": False})
        cmd = f'{self.venv} -m grid skills run context.refine --args-json \'{args}\''

        start = time.time()
        success, _, _ = self.run_command(cmd)
        skill_time = (time.time() - start) * 1000

        if success:
            print(f"  Skill Execution: {skill_time:.0f}ms")
            self.metrics['skill_execution_ms'] = skill_time
        else:
            print("  Skill Execution: Failed")

        # API response time
        start = time.time()
        success, _, _ = self.run_command('curl -s http://localhost:8080/health')
        api_time = (time.time() - start) * 1000

        if success:
            print(f"  API Response: {api_time:.0f}ms")
            self.metrics['api_response_ms'] = api_time
        else:
            print("  API Response: Failed")

    def run_dashboard(self):
        """Run complete monitoring dashboard"""
        self.print_header("GRID Systems Monitoring Dashboard")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Collect metrics
        self.get_api_metrics()
        self.get_agentic_metrics()
        self.get_rag_metrics()
        self.get_skills_metrics()
        self.get_case_references_metrics()
        self.get_performance_metrics()
        self.get_system_health()

        # Recommendations
        self.print_section("Recommendations")

        if self.metrics.get('ollama_status') == 'down':
            print("  → Start Ollama: ollama serve")

        if self.metrics.get('rag_db_files', 0) == 0:
            print("  → Build RAG index: .venv\\Scripts\\python.exe -m tools.rag.cli index . --rebuild --curate")

        if self.metrics.get('core_skills_available', 0) < 3:
            print("  → Verify skills: .venv\\Scripts\\python.exe -m grid skills list")

        if self.metrics.get('api_health') != 'running':
            print("  → Start API server: .venv\\Scripts\\python.exe -m application.mothership.main")

        self.print_header("Dashboard Complete")
        print()

if __name__ == "__main__":
    dashboard = GridMonitoringDashboard()
    dashboard.run_dashboard()
