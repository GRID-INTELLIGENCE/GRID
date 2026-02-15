@echo off
REM Test Server Denylist Manager
cd /d %~dp0..

echo ================================================================================
echo Testing Server Denylist Manager
echo ================================================================================
echo.

set "PYTHON_EXE=C:\Users\irfan\AppData\Local\Programs\Python\Python313\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

echo [1] Generating Denylist Report...
%PYTHON_EXE% scripts\server_denylist_manager.py --config config\server_denylist.json --report
echo.

echo [2] Checking individual servers...
%PYTHON_EXE% scripts\server_denylist_manager.py --config config\server_denylist.json --check grid-rag
echo.
%PYTHON_EXE% scripts\server_denylist_manager.py --config config\server_denylist.json --check memory
echo.

echo [3] Applying denylist to MCP configuration...
%PYTHON_EXE% scripts\server_denylist_manager.py --config config\server_denylist.json --mcp-config grid-rag-enhanced\mcp-setup\mcp_config.json --output grid-rag-enhanced\mcp-setup\mcp_config.denied.json
echo.

echo ================================================================================
echo Test Complete
echo ================================================================================
pause
