#!/usr/bin/env python3
"""
GRID MCP Integration Tests

Comprehensive test suite for all MCP servers.
Tests server startup, basic functionality, and integration.

NOTE: These tests require external services (Ollama). They will skip
gracefully if services are unavailable.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Add GRID to path
grid_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(grid_root / "src"))

# ANSI color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def _ollama_reachable() -> bool:
    """Check if Ollama is reachable with a short timeout."""
    try:
        import httpx

        r = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


def _api_server_reachable() -> bool:
    """Check if API server is reachable with a short timeout."""
    try:
        import httpx

        r = httpx.get("http://localhost:8000/health", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


# Module-level skip: skip entire module if services are not running
_ollama_available = _ollama_reachable()
if not _ollama_available:
    pytest.skip("Ollama service not available at localhost:11434", allow_module_level=True)


def print_header(text: str):
    """Print formatted section header"""
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")


def print_test(text: str):
    """Print test name"""
    print(f"{YELLOW}Testing: {text}{RESET}", end=" ... ")


def print_success(text: str = "✓ PASSED"):
    """Print success message"""
    print(f"{GREEN}{text}{RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ FAILED: {text}{RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ WARNING: {text}{RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{BLUE}ℹ {text}{RESET}")


class MCPTestSuite:
    """MCP Integration Test Suite"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.grid_root = grid_root

    async def test_prerequisites(self) -> bool:
        """Test prerequisites are met"""
        print_header("Prerequisites Check")

        all_passed = True

        # Test Python version
        print_test("Python version (>=3.13)")
        version = sys.version_info
        if version.major == 3 and version.minor >= 13:
            print_success(f"✓ Python {version.major}.{version.minor}.{version.micro}")
            self.passed += 1
        else:
            print_error(f"Python {version.major}.{version.minor} < 3.13")
            self.failed += 1
            all_passed = False

        # Test MCP library
        print_test("MCP library")
        try:
            import importlib.util

            spec = importlib.util.find_spec("mcp")
            if spec is not None:
                print_success()
                self.passed += 1
            else:
                print_error("MCP not installed. Run: pip install mcp")
                self.failed += 1
                all_passed = False
        except Exception as e:
            print_error(f"Error checking MCP: {e}")
            self.failed += 1
            all_passed = False

        # Test Ollama connectivity
        print_test("Ollama service")
        try:
            import httpx

            response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
            if response.status_code == 200:
                print_success()
                self.passed += 1
            else:
                print_error(f"Ollama returned status {response.status_code}")
                self.failed += 1
                all_passed = False
        except Exception as e:
            print_error(f"Cannot connect to Ollama: {e}")
            print_info("Start Ollama with: ollama serve")
            self.failed += 1
            all_passed = False

        # Test required Ollama models
        print_test("Ollama models (ministral-3:3b)")
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            if "ministral" in result.stdout:
                print_success()
                self.passed += 1
            else:
                print_warning("ministral-3:3b not found")
                print_info("Pull with: ollama pull ministral-3:3b")
                self.warnings += 1
        except Exception as e:
            print_warning(f"Could not check models: {e}")
            self.warnings += 1

        # Test directory structure
        print_test("Project directory structure")
        required_dirs = [
            self.grid_root / "src" / "grid" / "mcp",
            self.grid_root / "mcp-setup" / "server",
        ]
        missing = [d for d in required_dirs if not d.exists()]
        if not missing:
            print_success()
            self.passed += 1
        else:
            print_error(f"Missing directories: {missing}")
            self.failed += 1
            all_passed = False

        # Test server files exist
        print_test("MCP server files")
        required_files = [
            self.grid_root / "src" / "grid" / "mcp" / "multi_git_server.py",
            self.grid_root / "src" / "grid" / "mcp" / "mastermind_server.py",
            self.grid_root / "mcp-setup" / "server" / "grid_rag_mcp_server.py",
        ]
        missing = [f for f in required_files if not f.exists()]
        if not missing:
            print_success()
            self.passed += 1
        else:
            print_error(f"Missing files: {missing}")
            self.failed += 1
            all_passed = False

        return all_passed

    async def test_server_startup(self, name: str, script_path: Path, env: dict[str, str]) -> bool:
        """Test that a server can start without errors"""
        print_test(f"{name} server startup")

        proc = None
        try:
            # Start server process
            full_env = os.environ.copy()
            full_env.update(env)

            proc = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=full_env,
                cwd=str(self.grid_root),
            )

            # Wait for startup
            await asyncio.sleep(2)

            # Check if still running
            if proc.poll() is None:
                # Still running, good
                print_success()
                self.passed += 1
                success = True
            else:
                # Exited early, bad
                stdout, stderr = proc.communicate(timeout=5)
                print_error(f"Server exited with code {proc.returncode}")
                if stderr:
                    print_info(f"Error: {stderr.decode()[:200]}")
                self.failed += 1
                success = False

            return success

        except Exception as e:
            print_error(str(e))
            self.failed += 1
            return False
        finally:
            # Cleanup: ensure process is terminated
            if proc is not None and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if terminate doesn't work
                    proc.kill()
                    proc.wait(timeout=2)
                except Exception:
                    # Last resort: kill without waiting
                    try:
                        proc.kill()
                    except Exception:
                        pass

    async def test_git_server(self) -> bool:
        """Test Git server"""
        print_header("Git Server Tests")

        script_path = self.grid_root / "src" / "grid" / "mcp" / "multi_git_server.py"
        env = {
            "GIT_MCP_REPOSITORIES": f"default:{self.grid_root}",
            "PYTHONPATH": f"{self.grid_root / 'src'};{self.grid_root}",
        }

        return await self.test_server_startup("Git", script_path, env)

    async def test_mastermind_server(self) -> bool:
        """Test Mastermind server"""
        print_header("Mastermind Server Tests")

        script_path = self.grid_root / "src" / "grid" / "mcp" / "mastermind_server.py"
        env = {
            "GRID_ROOT": str(self.grid_root),
            "GRID_KNOWLEDGE_BASE": str(self.grid_root / ".grid_knowledge"),
            "LOG_LEVEL": "INFO",
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "PYTHONPATH": f"{self.grid_root / 'src'};{self.grid_root}",
        }

        return await self.test_server_startup("Mastermind", script_path, env)

    async def test_rag_server(self) -> bool:
        """Test RAG server"""
        print_header("RAG Server Tests")

        script_path = self.grid_root / "mcp-setup" / "server" / "grid_rag_mcp_server.py"
        env = {
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "PYTHONPATH": f"{self.grid_root / 'src'};{self.grid_root}",
            "RAG_CACHE_ENABLED": "true",
            "RAG_EMBEDDING_MODEL": "BAAI/bge-small-en-v1.5",
            "RAG_EMBEDDING_PROVIDER": "huggingface",
            "RAG_LLM_MODE": "local",
            "RAG_LLM_MODEL_LOCAL": "ministral-3:3b",
            "RAG_VECTOR_STORE_PATH": str(self.grid_root / ".rag_db"),
            "RAG_VECTOR_STORE_PROVIDER": "chromadb",
        }

        return await self.test_server_startup("RAG", script_path, env)

    async def test_memory_structure(self) -> bool:
        """Test memory file structure"""
        print_header("Memory Server Tests")

        print_test("Memory file exists")
        memory_path = self.grid_root / "src" / "tools" / "agent_prompts" / ".case_memory" / "memory.json"

        if not memory_path.exists():
            print_warning("Memory file not found, creating...")
            memory_path.parent.mkdir(parents=True, exist_ok=True)
            default_memory = {"cases": [], "patterns": {}, "solutions": {}, "keywords": {}}
            memory_path.write_text(json.dumps(default_memory, indent=2))
            print_success("Created")
            self.warnings += 1
            return True

        try:
            with open(memory_path) as f:
                data = json.load(f)

            # Validate structure
            required_keys = ["cases", "patterns", "solutions", "keywords"]
            if all(key in data for key in required_keys):
                print_success()
                self.passed += 1
                return True
            else:
                print_error("Invalid structure, missing keys")
                self.failed += 1
                return False

        except Exception as e:
            print_error(f"Cannot read memory file: {e}")
            self.failed += 1
            return False

    async def test_rag_database(self) -> bool:
        """Test RAG database setup"""
        print_test("RAG database directory")
        rag_path = self.grid_root / ".rag_db"

        if not rag_path.exists():
            print_warning("RAG database not found, creating...")
            rag_path.mkdir(parents=True, exist_ok=True)
            print_success("Created")
            self.warnings += 1
        else:
            print_success("Exists")
            self.passed += 1

        return True

    async def test_knowledge_base(self) -> bool:
        """Test knowledge base setup"""
        print_test("Knowledge base directory")
        kb_path = self.grid_root / ".grid_knowledge"

        if not kb_path.exists():
            print_warning("Knowledge base not found, creating...")
            kb_path.mkdir(parents=True, exist_ok=True)
            print_success("Created")
            self.warnings += 1
        else:
            print_success("Exists")
            self.passed += 1

        return True

    async def run_all_tests(self):
        """Run all tests"""
        print_header("GRID MCP Integration Tests")
        print_info(f"Grid Root: {self.grid_root}")
        print_info(f"Python: {sys.executable}")

        # Prerequisites
        prereq_passed = await self.test_prerequisites()

        if not prereq_passed:
            print_error("\n⚠ Prerequisites not met. Please fix issues above before continuing.")
            return False

        # Server tests
        await self.test_git_server()
        await self.test_mastermind_server()
        await self.test_rag_server()

        # Configuration tests
        await self.test_memory_structure()
        await self.test_rag_database()
        await self.test_knowledge_base()

        # Summary
        self.print_summary()

        return self.failed == 0

    def print_summary(self):
        """Print test summary"""
        print_header("Test Summary")

        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"{GREEN}✓ Passed:{RESET}  {self.passed}")
        print(f"{RED}✗ Failed:{RESET}  {self.failed}")
        print(f"{YELLOW}⚠ Warnings:{RESET} {self.warnings}")
        print(f"{BLUE}Pass Rate:{RESET} {pass_rate:.1f}%")

        if self.failed == 0:
            print(f"\n{GREEN}{BOLD}All tests passed! ✓{RESET}")
            print(f"{GREEN}MCP servers are ready to use.{RESET}")
        else:
            print(f"\n{RED}{BOLD}Some tests failed.{RESET}")
            print(f"{RED}Please fix issues before using MCP servers.{RESET}")

        if self.warnings > 0:
            print(f"\n{YELLOW}Note: {self.warnings} warning(s) were fixed automatically.{RESET}")


async def main():
    """Main test entry point"""
    suite = MCPTestSuite()

    try:
        success = await suite.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Run tests
    asyncio.run(main())
