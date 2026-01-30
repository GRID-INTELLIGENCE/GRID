import sys
from pathlib import Path


def check_python_version():
    print(f"[*] Checking Python Version: {sys.version}")
    return True


def check_dependencies():
    print("[*] Checking critical dependencies...")
    libs = [
        ("pydantic", "Core Schemas"),
        ("chromadb", "RAG Database"),
        ("aiohttp", "Async Inference"),
        ("requests", "API Sync"),
    ]
    missing = []
    for lib, desc in libs:
        try:
            __import__(lib)
        except ImportError:
            missing.append(f"{lib} ({desc})")

    if missing:
        print(f"[-] ERROR: Missing dependencies: {', '.join(missing)}")
        return False
    print("[+] All critical dependencies are available.")
    return True


def check_inference_elasticity():
    print("[*] Checking Inference Elasticity (Tiered Providers)...")
    # Robustly find project root
    current = Path(__file__).resolve()
    project_root = current
    for _ in range(10):
        if (project_root / "src").exists():
            break
        project_root = project_root.parent

    sys.path.append(str(project_root))
    try:
        from src.grid.services.inference_harness import InferenceHarness

        harness = InferenceHarness()
        available = [t.value for t, p in harness.providers.items() if p.is_available()]
        print(f"[+] Active Providers: {', '.join(available)}")
        if "mock" in available and len(available) == 1:
            print("[-] WARNING: Only Mock provider available. Real inference will fail.")
            return False
        return True
    except Exception as e:
        print(f"[-] ERROR: Failed to initialize InferenceHarness: {e}")
        return False


def check_ollama():
    print("[*] Checking Ollama status...")
    try:
        import requests

        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.model_dump_json().get("models", [])]
            print(f"[+] Ollama reachable. Available models: {', '.join(models[:3])}...")
            return True
    except Exception:
        print("[-] WARNING: Ollama is not reachable on localhost:11434.")
    return False


def main():
    print("=== GRID System Health Check (v1.2) ===")
    results = [check_python_version(), check_dependencies(), check_ollama(), check_inference_elasticity()]

    if all(results):
        print("\n[SUCCESS] GRID environment is production-ready.")
        sys.exit(0)
    else:
        print("\n[FAILURE] GRID environment has issues.")
        sys.exit(1)


if __name__ == "__main__":
    main()
