#!/usr/bin/env python3
"""
GRID Systems Integration Test Suite
Tests all three systems working together
"""

import json
import subprocess
import sys
from datetime import datetime


class GridIntegrationTests:
    def __init__(self):
        self.venv = ".venv\\Scripts\\python.exe"
        self.api_base = "http://localhost:8080"
        self.passed = 0
        self.failed = 0
        self.tests = []

    def print_header(self, title):
        """Print formatted header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")

    def print_test(self, name, status, details=""):
        """Print test result"""
        symbol = "✓" if status else "✗"
        print(f"  {symbol} {name}")
        if details:
            print(f"    {details}")
        if status:
            self.passed += 1
        else:
            self.failed += 1
        self.tests.append({"name": name, "status": status, "details": details})

    def run_command(self, cmd, timeout=10):
        """Run command and return result"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=timeout)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timeout"
        except Exception as e:
            return False, "", str(e)

    def test_skills_pipeline(self):
        """Test Skills Pipeline"""
        self.print_header("Skills Pipeline Tests")

        # Test 1: List skills
        success, output, _ = self.run_command(f"{self.venv} -m grid skills list")
        if success:
            try:
                data = json.loads(output)
                skills = data.get("skills", [])
                self.print_test("List skills", len(skills) > 0, f"Found {len(skills)} skills")
            except Exception:
                self.print_test("List skills", False, "Failed to parse output")
        else:
            self.print_test("List skills", False, "Command failed")

        # Test 2: context.refine
        args = json.dumps({"text": "I think we should do it because it is important.", "use_llm": False})
        cmd = f"{self.venv} -m grid skills run context.refine --args-json '{args}'"
        success, output, _ = self.run_command(cmd)
        if success:
            try:
                data = json.loads(output)
                self.print_test(
                    "context.refine", data.get("status") == "success", f"Output: {data.get('output', '')[:40]}"
                )
            except Exception:
                self.print_test("context.refine", False, "Failed to parse output")
        else:
            self.print_test("context.refine", False, "Command failed")

        # Test 3: transform.schema_map
        args = json.dumps(
            {"text": "Test framework", "target_schema": "resonance", "output_format": "json", "use_llm": False}
        )
        cmd = f"{self.venv} -m grid skills run transform.schema_map --args-json '{args}'"
        success, output, _ = self.run_command(cmd)
        if success:
            try:
                data = json.loads(output)
                self.print_test(
                    "transform.schema_map", data.get("status") == "success", f"Schema: {data.get('target_schema')}"
                )
            except Exception:
                self.print_test("transform.schema_map", False, "Failed to parse output")
        else:
            self.print_test("transform.schema_map", False, "Command failed")

        # Test 4: compress.articulate
        args = json.dumps(
            {
                "text": "This is a long text that needs to be compressed into a shorter version.",
                "max_chars": 50,
                "use_llm": False,
            }
        )
        cmd = f"{self.venv} -m grid skills run compress.articulate --args-json '{args}'"
        success, output, _ = self.run_command(cmd)
        if success:
            try:
                data = json.loads(output)
                chars = data.get("chars", 0)
                self.print_test(
                    "compress.articulate",
                    data.get("status") == "success" and chars <= 50,
                    f"Compressed to {chars} chars",
                )
            except Exception:
                self.print_test("compress.articulate", False, "Failed to parse output")
        else:
            self.print_test("compress.articulate", False, "Command failed")

    def test_rag_system(self):
        """Test RAG System"""
        self.print_header("RAG System Tests")

        # Test 1: Check Ollama
        success, _, _ = self.run_command("curl -s http://localhost:11434/api/tags")
        ollama_running = success
        self.print_test(
            "Ollama availability", ollama_running, "Ollama is " + ("running" if ollama_running else "not running")
        )

        # Test 2: Check RAG database
        import os

        rag_db_exists = os.path.isdir(".rag_db")
        self.print_test("RAG database directory", rag_db_exists, ".rag_db directory exists")

        # Test 3: RAG CLI available
        success, output, _ = self.run_command(f"{self.venv} -m tools.rag.cli --help")
        self.print_test("RAG CLI available", success, "RAG CLI is accessible")

        if ollama_running:
            # Test 4: Query RAG (if Ollama is running)
            success, output, _ = self.run_command(f'{self.venv} -m tools.rag.cli query "test" 2>&1', timeout=30)
            self.print_test("RAG query", success, "Query executed" if success else "Query failed")
        else:
            self.print_test("RAG query", False, "Skipped (Ollama not running)")

    def test_agentic_system(self):
        """Test Agentic System"""
        self.print_header("Agentic System Tests")

        # Test 1: API health
        success, output, _ = self.run_command("curl -s http://localhost:8080/health")
        if success:
            try:
                data = json.loads(output)
                self.print_test("API health", True, f"Status: {data.get('status')}")
            except Exception:
                self.print_test("API health", True, "API is responding")
        else:
            self.print_test("API health", False, "API not responding")
            return  # Skip remaining tests if API is down

        # Test 2: Create case
        payload = json.dumps({"raw_input": "Test case", "examples": ["test"], "scenarios": ["test"]})
        cmd = f"curl -s -X POST http://localhost:8080/api/v1/agentic/cases -H \"Content-Type: application/json\" -d '{payload}'"
        success, output, _ = self.run_command(cmd)
        case_id = None
        if success:
            try:
                data = json.loads(output)
                case_id = data.get("case_id")
                self.print_test("Create case", case_id is not None, f"Case ID: {case_id}")
            except Exception:
                self.print_test("Create case", False, "Failed to parse response")
        else:
            self.print_test("Create case", False, "Request failed")

        # Test 3: Get case status
        if case_id:
            cmd = f"curl -s http://localhost:8080/api/v1/agentic/cases/{case_id}"
            success, output, _ = self.run_command(cmd)
            if success:
                try:
                    data = json.loads(output)
                    self.print_test("Get case status", True, f"Status: {data.get('status')}")
                except Exception:
                    self.print_test("Get case status", False, "Failed to parse response")
            else:
                self.print_test("Get case status", False, "Request failed")
        else:
            self.print_test("Get case status", False, "Skipped (no case ID)")

        # Test 4: Get experience
        cmd = "curl -s http://localhost:8080/api/v1/agentic/experience"
        success, output, _ = self.run_command(cmd)
        if success:
            try:
                data = json.loads(output)
                total = data.get("total_cases", 0)
                success_rate = data.get("success_rate", 0)
                self.print_test("Get experience", True, f"Total: {total}, Success: {success_rate*100:.1f}%")
            except Exception:
                self.print_test("Get experience", False, "Failed to parse response")
        else:
            self.print_test("Get experience", False, "Request failed")

    def test_integration(self):
        """Test integration between systems"""
        self.print_header("Integration Tests")

        # Test 1: Skills → Schema → Compress pipeline
        text = "We should implement automated testing because it improves quality."

        # Refine
        args = json.dumps({"text": text, "use_llm": False})
        cmd = f"{self.venv} -m grid skills run context.refine --args-json '{args}'"
        success1, output1, _ = self.run_command(cmd)

        # Schema
        if success1:
            try:
                refined = json.loads(output1).get("output", text)
                args = json.dumps(
                    {"text": refined, "target_schema": "resonance", "output_format": "json", "use_llm": False}
                )
                cmd = f"{self.venv} -m grid skills run transform.schema_map --args-json '{args}'"
                success2, output2, _ = self.run_command(cmd)

                # Compress
                if success2:
                    args = json.dumps({"text": refined, "max_chars": 80, "use_llm": False})
                    cmd = f"{self.venv} -m grid skills run compress.articulate --args-json '{args}'"
                    success3, output3, _ = self.run_command(cmd)

                    self.print_test("Skills pipeline integration", success3, "Refine → Schema → Compress")
                else:
                    self.print_test("Skills pipeline integration", False, "Schema mapping failed")
            except Exception:
                self.print_test("Skills pipeline integration", False, "Parsing error")
        else:
            self.print_test("Skills pipeline integration", False, "Refine failed")

        # Test 2: Skills → Agentic case creation
        args = json.dumps({"text": text, "use_llm": False})
        cmd = f"{self.venv} -m grid skills run context.refine --args-json '{args}'"
        success, output, _ = self.run_command(cmd)

        if success:
            try:
                refined = json.loads(output).get("output", text)
                payload = json.dumps({"raw_input": refined, "examples": [], "scenarios": []})
                cmd = f"curl -s -X POST http://localhost:8080/api/v1/agentic/cases -H \"Content-Type: application/json\" -d '{payload}'"
                success, output, _ = self.run_command(cmd)

                if success:
                    data = json.loads(output)
                    case_id = data.get("case_id")
                    self.print_test("Skills → Agentic integration", case_id is not None, f"Created case {case_id}")
                else:
                    self.print_test("Skills → Agentic integration", False, "Case creation failed")
            except Exception:
                self.print_test("Skills → Agentic integration", False, "Parsing error")
        else:
            self.print_test("Skills → Agentic integration", False, "Skills execution failed")

    def run_all_tests(self):
        """Run all tests"""
        self.print_header("GRID Systems Integration Test Suite")
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        self.test_skills_pipeline()
        self.test_rag_system()
        self.test_agentic_system()
        self.test_integration()

        # Summary
        self.print_header("Test Summary")
        total = self.passed + self.failed
        print(f"  Passed: {self.passed}/{total}")
        print(f"  Failed: {self.failed}/{total}")
        print(f"  Success Rate: {self.passed/total*100:.1f}%" if total > 0 else "  No tests run")

        if self.failed == 0:
            print("\n  ✓ All systems operational!")
        else:
            print(f"\n  ⚠ {self.failed} test(s) failed - review above")

        return self.failed == 0


if __name__ == "__main__":
    tests = GridIntegrationTests()
    success = tests.run_all_tests()
    sys.exit(0 if success else 1)
