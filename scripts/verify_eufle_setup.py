#!/usr/bin/env python3
"""
EUFLE Setup Verification Script

Checks:
1. Ollama installation and availability
2. Environment variables
3. Model availability
4. HF model files
"""

import os
import subprocess
import sys
from pathlib import Path


def check_ollama():
    """Check if Ollama is installed and accessible."""
    print("\n[1/5] Checking Ollama installation...")
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"  ✓ {result.stdout.strip()}")
            return True
        else:
            print("  ✗ Ollama not found")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"  ✗ Error: {e}")
        return False


def check_ollama_server():
    """Check if Ollama server is running."""
    print("\n[2/5] Checking Ollama server (localhost:11434)...")
    try:
        import urllib.request

        response = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        if response.status == 200:
            print("  ✓ Ollama server is running")
            return True
    except Exception:
        print("  ⚠ Ollama server not responding")
        print("    Start with: ollama serve")
        return False


def check_environment():
    """Check environment variables."""
    print("\n[3/5] Checking environment variables...")

    provider = os.getenv("EUFLE_DEFAULT_PROVIDER", "not set")
    model = os.getenv("EUFLE_DEFAULT_MODEL", "not set")

    print(f"  EUFLE_DEFAULT_PROVIDER = {provider}")
    print(f"  EUFLE_DEFAULT_MODEL = {model}")

    if provider.lower() in ["ollama", "auto"]:
        print("  ✓ Provider configured for Ollama")
        return True
    else:
        print("  ⚠ Provider not set to Ollama")
        return False


def check_hf_models():
    """Check HuggingFace model files."""
    print("\n[4/5] Checking HuggingFace model files...")

    # Get EUFLE root from environment or use current script location
    eufle_root = os.getenv("EUFLE_ROOT", str(Path(__file__).parent))
    model_path = Path(eufle_root) / "EUFLE" / "hf-models" / "ministral-14b"
    required_files = {
        "tokenizer.json": "tokenizer",
        "config.json": "config",
        "consolidated.safetensors": "model weights",
    }

    all_exist = True
    for filename, description in required_files.items():
        filepath = model_path / filename
        exists = filepath.exists()
        status = "✓" if exists else "✗"

        # For tokenizer.json, also check it's not empty
        if filename == "tokenizer.json" and exists:
            size = filepath.stat().st_size
            if size > 1000:
                print(f"  {status} {description} ({filename}) - {size:,} bytes")
            else:
                print(f"  ✗ {description} ({filename}) - EMPTY or too small ({size} bytes)")
                all_exist = False
        else:
            print(f"  {status} {description} ({filename})")
            if not exists:
                all_exist = False

    return all_exist


def check_eufle_repo():
    """Check EUFLE repository structure."""
    print("\n[5/5] Checking EUFLE repository...")

    required_paths = {
        "E:/EUFLE": "EUFLE root",
        "E:/EUFLE/eufle": "eufle package",
        "E:/EUFLE/studio": "studio module",
        "E:/EUFLE/eufle.py": "CLI entry point",
    }

    all_exist = True
    for path, description in required_paths.items():
        exists = Path(path).exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {description}")
        if not exists:
            all_exist = False

    return all_exist


def main():
    """Run all checks."""
    print("=" * 50)
    print("EUFLE + Ollama Setup Verification")
    print("=" * 50)

    results = {
        "Ollama installed": check_ollama(),
        "Ollama server running": check_ollama_server(),
        "Environment variables": check_environment(),
        "HF model files": check_hf_models(),
        "EUFLE repository": check_eufle_repo(),
    }

    print("\n" + "=" * 50)
    print("Verification Summary")
    print("=" * 50)

    for check, passed in results.items():
        status = "✓" if passed else "⚠"
        print(f"  {status} {check}")

    if all(results.values()):
        print("\n✓ All checks passed! Ready to use EUFLE with Ollama.")
        print("\nNext: python eufle.py --ask")
        return 0
    else:
        print("\n⚠ Some checks failed. See details above.")
        print("\nCommon fixes:")
        print("  1. Set environment: $env:EUFLE_DEFAULT_PROVIDER = 'ollama'")
        print("  2. Start Ollama: ollama serve")
        print("  3. Pull a model: ollama pull mistral")
        return 1


if __name__ == "__main__":
    sys.exit(main())
