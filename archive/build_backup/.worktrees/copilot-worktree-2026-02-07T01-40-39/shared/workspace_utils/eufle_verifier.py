"""
EUFLE Verification Module

Migrated from verify_eufle_setup.py - provides EUFLE setup verification
with JSON output for Cascade integration.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .config import config
from .exceptions import VerificationError


class EUFLEVerifier:
    """EUFLE setup verification with Cascade-friendly JSON output."""

    def __init__(self):
        try:
            self.eufle_root = Path(os.getenv("EUFLE_ROOT", config.get_workspace_root() / "projects" / "EUFLE"))
            if not self.eufle_root.exists() and not os.getenv("EUFLE_ROOT"):
                # Only warn if EUFLE_ROOT wasn't explicitly set
                pass  # Will be caught in check_eufle_repo()
        except (OSError, ValueError) as e:
            raise VerificationError(
                f"Invalid EUFLE root path: {self.eufle_root}\n"
                f"Error: {str(e)}\n"
                f"Please set EUFLE_ROOT environment variable or verify workspace structure."
            ) from e
        self.results: Dict[str, bool] = {}
        self.details: Dict[str, any] = {}

    def check_ollama(self) -> bool:
        """Check if Ollama is installed and accessible."""
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.details["ollama_version"] = result.stdout.strip()
                return True
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def check_ollama_server(self) -> bool:
        """Check if Ollama server is running."""
        try:
            import urllib.request
            response = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
            if response.status == 200:
                self.details["ollama_server"] = "running"
                return True
            return False
        except Exception:
            self.details["ollama_server"] = "not_responding"
            return False

    def check_environment(self) -> bool:
        """Check environment variables."""
        provider = os.getenv("EUFLE_DEFAULT_PROVIDER", "not set")
        model = os.getenv("EUFLE_DEFAULT_MODEL", "not set")
        
        self.details["eufle_provider"] = provider
        self.details["eufle_model"] = model
        
        return provider.lower() in ["ollama", "auto"]

    def check_hf_models(self) -> bool:
        """Check HuggingFace model files."""
        model_path = self.eufle_root / "hf-models" / "ministral-14b"
        required_files = {
            "tokenizer.json": "tokenizer",
            "config.json": "config",
            "consolidated.safetensors": "model weights"
        }
        
        file_status = {}
        all_exist = True
        
        for filename, description in required_files.items():
            filepath = model_path / filename
            exists = filepath.exists()
            file_status[filename] = {
                "exists": exists,
                "description": description
            }
            
            if filename == "tokenizer.json" and exists:
                size = filepath.stat().st_size
                file_status[filename]["size"] = size
                if size <= 1000:
                    all_exist = False
            
            if not exists:
                all_exist = False
        
        self.details["hf_model_files"] = file_status
        return all_exist

    def check_eufle_repo(self) -> bool:
        """Check EUFLE repository structure."""
        required_paths = {
            str(self.eufle_root): "EUFLE root",
            str(self.eufle_root / "studio"): "studio module",
            str(self.eufle_root / "eufle.py"): "CLI entry point"
        }
        
        path_status = {}
        all_exist = True
        
        for path, description in required_paths.items():
            exists = Path(path).exists()
            path_status[path] = {
                "exists": exists,
                "description": description
            }
            if not exists:
                all_exist = False
        
        self.details["eufle_repo_paths"] = path_status
        return all_exist

    def run_all_checks(self) -> Dict:
        """Run all checks and return results (JSON for Cascade)."""
        print("=" * 50)
        print("EUFLE + Ollama Setup Verification")
        print("=" * 50)
        
        self.results = {
            "Ollama installed": self.check_ollama(),
            "Ollama server running": self.check_ollama_server(),
            "Environment variables": self.check_environment(),
            "HF model files": self.check_hf_models(),
            "EUFLE repository": self.check_eufle_repo(),
        }
        
        print("\n" + "=" * 50)
        print("Verification Summary")
        print("=" * 50)
        
        for check, passed in self.results.items():
            status = "✓" if passed else "⚠"
            print(f"  {status} {check}")
        
        all_passed = all(self.results.values())
        
        if all_passed:
            print("\n✓ All checks passed! Ready to use EUFLE with Ollama.")
            print("\nNext: python eufle.py --ask")
        else:
            print("\n⚠ Some checks failed. See details above.")
            print("\nCommon fixes:")
            print("  1. Set environment: $env:EUFLE_DEFAULT_PROVIDER = 'ollama'")
            print("  2. Start Ollama: ollama serve")
            print("  3. Pull a model: ollama pull mistral")
        
        # Return JSON-compatible report
        return {
            "timestamp": datetime.now().isoformat(),
            "all_checks_passed": all_passed,
            "results": self.results,
            "details": self.details,
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on failed checks."""
        recommendations = []
        
        if not self.results.get("Ollama installed", False):
            recommendations.append("Install Ollama from https://ollama.ai")
        
        if not self.results.get("Ollama server running", False):
            recommendations.append("Start Ollama server: ollama serve")
        
        if not self.results.get("Environment variables", False):
            recommendations.append("Set EUFLE_DEFAULT_PROVIDER environment variable to 'ollama'")
        
        if not self.results.get("HF model files", False):
            recommendations.append("Download required HuggingFace model files")
        
        if not self.results.get("EUFLE repository", False):
            recommendations.append("Verify EUFLE repository structure and paths")
        
        return recommendations


def main():
    """Main entry point."""
    verifier = EUFLEVerifier()
    result = verifier.run_all_checks()
    
    # Output JSON for Cascade if enabled
    if config.should_output_json():
        output_file = config.get_output_dir() / "eufle_verification.json"
        import json
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nJSON report saved to: {output_file}")
    
    sys.exit(0 if result["all_checks_passed"] else 1)


if __name__ == "__main__":
    main()