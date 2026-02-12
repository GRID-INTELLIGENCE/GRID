# Python Entrypoint Profile

Generated: 2026-02-01T22:07:18.990639+00:00

## Summary
- Total matches: 269
- Patterns: {'py_command': 26, 'python_command': 122, 'python_exe': 87, 'json_command': 28, 'py_launcher': 6}
- Extensions: {'.ps1': 182, '.bat': 12, '.py': 32, '.json': 43}

## Recent Files With Entrypoint Signals
- E:\scripts\profile_python_entrypoints.py (2026-02-02T04:07:02.847372)
- E:\config\python_entrypoint_blocklist.json (2026-02-02T04:06:41.021655)
- E:\scripts\organizational_cleanup.ps1 (2026-02-02T04:06:13.605081)
- E:\scripts\test_denylist.bat (2026-02-02T04:04:28.859154)
- E:\scripts\resolve_python.ps1 (2026-02-02T04:04:17.779226)
- E:\scripts\workspace_setup.ps1 (2026-02-02T04:02:19.341825)
- E:\scripts\validate_startup.ps1 (2026-02-02T04:00:02.133461)
- E:\scripts\setup_spawn_monitor_task.ps1 (2026-02-02T03:59:31.222609)
- E:\scripts\_archive\extend_denylist_4.ps1 (2026-02-02T03:39:28.041530)
- E:\config\server_denylist.json (2026-02-02T03:31:09.226540)
- E:\grid\mcp-setup\mcp_config.json (2026-02-02T03:11:16.557800)
- E:\grid\mcp-setup\mcp_config.backup.json (2026-02-02T02:42:38.123934)
- E:\wellness_studio\ai_safety\config\denylist_config.json (2026-02-02T02:41:26.270859)
- E:\grid\.vscode\settings.json (2026-02-01T21:25:01.200930)
- E:\grid\tests\test_integration.py (2026-02-01T21:25:00.676675)
- E:\grid\tests\performance\test_resonance_load.py (2026-02-01T21:24:58.070132)
- E:\grid\scripts\nul_cleaner.bat (2026-02-01T21:24:57.811827)
- E:\grid\scripts\agent_setup.ps1 (2026-02-01T21:24:57.809318)
- E:\grid\mcp-setup\server\rag-server-config.json (2026-02-01T21:24:57.775395)
- E:\grid\config\ignored\dotfolders\vscode\settings.json (2026-02-01T21:24:57.499116)
- E:\grid\scripts\local_ci_check.py (2026-02-01T20:54:37.267948)
- E:\grid\scripts\local_ci_check.ps1 (2026-02-01T20:45:32.505776)
- E:\grid\.vscode\tasks.json (2026-02-01T18:12:37.197532)
- E:\grid\scripts\mcp_tool_validator.py (2026-02-01T15:20:25.155059)
- E:\grid\scripts\setup_complete_systems.py (2026-02-01T15:20:25.129714)

## Tight Coupling Signals
- File association uses py.exe (Python Launcher).
- Scripts/configs that call `py` or `python` directly.
- JSON configs using `"command": "python"`.

## Recommended Blocklist Layer
```json
{
  "version": "1.0.0",
  "generated_at": "2026-02-01T22:07:18.989631+00:00",
  "allowed_python": "C:\\Users\\irfan\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
  "blocked_commands": [
    "py",
    "py.exe",
    "pyw",
    "pyw.exe"
  ],
  "blocked_paths": [
    "C:\\WINDOWS\\py.exe"
  ],
  "monitored_commands": [
    "python",
    "python.exe"
  ],
  "globs": [
    "*.ps1",
    "*.bat",
    "*.cmd",
    "*.py",
    "*.json",
    "*.yml",
    "*.yaml",
    "*.toml"
  ],
  "patterns": {
    "py_launcher": "(?i)\\bpy\\.exe\\b",
    "python_exe": "(?i)\\bpython\\.exe\\b",
    "py_command": "(?i)(?:^|[^\\w-])py(?:\\s|$)",
    "python_command": "(?i)(?:^|[^\\w-])python(?:\\s|$)",
    "json_command": "\\\"command\\\"\\s*:\\s*\\\"(python|py)\\\""
  }
}
```

## Sample Matches (Top 50)
- E:\grid\scripts\agent_setup.ps1:15 [py_command] python -m pytest tests/security/test_path_traversal.py -v
- E:\grid\scripts\agent_setup.ps1:15 [python_command] python -m pytest tests/security/test_path_traversal.py -v
- E:\grid\scripts\categorize_working_tree.ps1:105 [python_command] $report += "3. Python code ($($categories['python_code'].Count)):"
- E:\grid\scripts\ci_simulate.ps1:28 [py_command] uv run pytest tests/security/test_path_traversal.py -v
- E:\grid\scripts\cli_helpers.ps1:48 [python_command] # Python Wrappers (Avoid PATH issues)
- E:\grid\scripts\cli_helpers.ps1:54 [python_command] Safe pip wrapper using python -m
- E:\grid\scripts\cli_helpers.ps1:58 [python_command] python -m pip $args
- E:\grid\scripts\cli_helpers.ps1:76 [python_command] $cmd = "python -m pytest $Path"
- E:\grid\scripts\cli_helpers.ps1:96 [python_command] python -m alembic $args
- E:\grid\scripts\cli_helpers.ps1:123 [python_command] $cmd = "python -m uvicorn application.mothership.main:app --port $Port"
- E:\grid\scripts\cli_helpers.ps1:140 [py_command] python scripts/instrumentation_metrics.py
- E:\grid\scripts\cli_helpers.ps1:140 [python_command] python scripts/instrumentation_metrics.py
- E:\grid\scripts\cli_helpers.ps1:158 [python_command] # Python
- E:\grid\scripts\cli_helpers.ps1:160 [python_command] $pythonVersion = python --version 2>&1
- E:\grid\scripts\cli_helpers.ps1:161 [python_command] $pythonPath = (where.exe python 2>$null | Select-Object -First 1)
- E:\grid\scripts\cli_helpers.ps1:201 [python_command] $importTest = python -c "from application.mothership.main import create_app; print('OK')" 2>&1
- E:\grid\scripts\deploy-simple.ps1:36 [python_command] python -c "from grid.mcp.enhanced_rag_server import EnhancedRAGMCPServer"
- E:\grid\scripts\deploy-simple.ps1:37 [python_command] python -c "from tools.rag.conversational_rag import create_conversational_rag_engine"
- E:\grid\scripts\deploy-simple.ps1:38 [python_command] python -c "from src.application.mothership.rag_handlers import register_rag_handlers; register_rag_handlers()"
- E:\grid\scripts\deploy-simple.ps1:46 [python_exe] .venv\Scripts\python.exe -m grid.mcp.enhanced_rag_server
- E:\grid\scripts\deploy-simple.ps1:52 [python_exe] .venv\Scripts\python.exe workspace\mcp\servers\memory\server.py
- E:\grid\scripts\deploy-simple.ps1:52 [py_command] .venv\Scripts\python.exe workspace\mcp\servers\memory\server.py
- E:\grid\scripts\deploy-simple.ps1:58 [python_exe] .venv\Scripts\python.exe workspace\mcp\servers\agentic\server.py
- E:\grid\scripts\deploy-simple.ps1:58 [py_command] .venv\Scripts\python.exe workspace\mcp\servers\agentic\server.py
- E:\grid\scripts\deploy.ps1:63 [python_command] python -c "from grid.mcp.enhanced_rag_server import EnhancedRAGMCPServer"
- E:\grid\scripts\deploy.ps1:64 [python_command] python -c "from tools.rag.conversational_rag import create_conversational_rag_engine"
- E:\grid\scripts\deploy.ps1:65 [python_command] python -c "from src.application.mothership.rag_handlers import register_rag_handlers; register_rag_handlers()"
- E:\grid\scripts\deploy.ps1:74 [python_exe] .venv\Scripts\python.exe -m grid.mcp.enhanced_rag_server
- E:\grid\scripts\deploy.ps1:81 [python_exe] .venv\Scripts\python.exe workspace\mcp\servers\memory\server.py
- E:\grid\scripts\deploy.ps1:81 [py_command] .venv\Scripts\python.exe workspace\mcp\servers\memory\server.py
- E:\grid\scripts\deploy.ps1:88 [python_exe] .venv\Scripts\python.exe workspace\mcp\servers\agentic\server.py
- E:\grid\scripts\deploy.ps1:88 [py_command] .venv\Scripts\python.exe workspace\mcp\servers\agentic\server.py
- E:\grid\scripts\deploy.ps1:94 [python_exe] taskkill /F /IM python.exe /FI "WINDOWTITLE eq grid-rag-enhanced*" 2>nul
- E:\grid\scripts\deploy.ps1:95 [python_exe] taskkill /F /IM python.exe /FI "WINDOWTITLE eq memory-mcp*" 2>nul
- E:\grid\scripts\deploy.ps1:96 [python_exe] taskkill /F /IM python.exe /FI "WINDOWTITLE eq grid-agentic*" 2>nul
- E:\grid\scripts\local_ci_check.ps1:86 [python_exe] & "e:\grid\.venv\Scripts\python.exe" -c "import sys; print(f'Python: {sys.version}'); import pytest, pydantic, fastapi, numpy; print('All imports OK'); sys.exit(0)"
- E:\grid\scripts\local_ci_check.ps1:91 [python_exe] & "e:\grid\.venv\Scripts\python.exe" -m ruff check src/ tests/ --select=E, F, W
- E:\grid\scripts\local_ci_check.ps1:96 [python_exe] & "e:\grid\.venv\Scripts\python.exe" -m black --check src/ tests/ --quiet
- E:\grid\scripts\local_ci_check.ps1:101 [python_exe] & "e:\grid\.venv\Scripts\python.exe" -m pytest tests/unit/ -v --tb=short -x --maxfail=3
- E:\grid\scripts\local_ci_check.ps1:106 [python_exe] & "e:\grid\.venv\Scripts\python.exe" -m pytest tests/unit/test_input_sanitizer.py -v --tb=short
- E:\grid\scripts\local_ci_check.ps1:106 [py_command] & "e:\grid\.venv\Scripts\python.exe" -m pytest tests/unit/test_input_sanitizer.py -v --tb=short
- E:\grid\scripts\local_ci_check.ps1:111 [python_exe] & "e:\grid\.venv\Scripts\python.exe" -m mypy src/grid --ignore-missing-imports --no-strict-optional
- E:\grid\scripts\organize_commits.ps1:148 [python_command] Message = "refactor: update Python code"
- E:\grid\scripts\run_python.ps1:1 [python_command] # Python runner script that bypasses the broken venv
- E:\grid\scripts\run_python.ps1:8 [python_command] # Try to find system Python
- E:\grid\scripts\run_python.ps1:11 [python_command] # Check common Python locations
- E:\grid\scripts\run_python.ps1:16 [python_exe] "C:\Python313\python.exe",
- E:\grid\scripts\run_python.ps1:17 [python_exe] "C:\Python312\python.exe",
- E:\grid\scripts\run_python.ps1:18 [python_exe] "C:\Python311\python.exe",
- E:\grid\scripts\run_python.ps1:19 [python_exe] "C:\Program Files\Python313\python.exe",
