# Quick Start: Using the Fixed Development Environment

## 1. Initial Setup (One-Time)

### Start Docker Desktop
```powershell
# Open Docker Desktop application (required for PostgreSQL, GitHub MCP, SonarQube)
# Or from terminal:
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Wait 2-3 minutes for Docker to fully initialize
# Verify: docker ps (should work without errors)
```

### Install Pylance VS Code Extension
```powershell
# From PowerShell in VS Code, OR
code --install-extension ms-python.vscode-pylance

# Reload VS Code when prompted
```

### Validate Startup Configuration
```powershell
cd E:\
.\validate_startup.ps1

# Output should show:
# ✓ Python Language Server: Pylance (enabled)
# ✓ MCP Servers configured: 4
# ✓ Terminal Shell Integration: Enabled
# ✓ Type Checking Mode: strict
```

## 2. Daily Development Workflow

### Start Backend API Server
```powershell
# Terminal 1: Backend Server
cd E:\Apps\backend
python main.py

# Or with auto-reload for development:
uvicorn main:app --reload

# You should see:
# ✓ MCP servers: 2-4/4 initialized successfully
# ✓ Terminal shells: 2-3/3 initialized successfully
```

### Check System Health
```powershell
# In PowerShell or WSL
curl http://localhost:8000/health | ConvertFrom-Json | ConvertTo-Json

# Or with jq (WSL):
curl http://localhost:8000/health | jq
```

### Start Frontend Development
```powershell
# Terminal 2: Frontend Development
cd E:\Apps
npm install  # One-time
npm run dev  # Starts on http://localhost:3000
```

## 3. Using PowerShell (Primary Terminal)

PowerShell is configured as the default terminal for:
- Running commands
- Building/testing
- File management
- Python execution

```powershell
# Standard PowerShell workflow
python main.py
npm run dev
npm test
git status
```

## 4. Using WSL (Advanced Unix Tasks)

WSL is available for advanced Unix commands:
```powershell
# Switch to WSL from PowerShell
wsl

# Now you have full Unix environment
grep "pattern" file.txt
cat /etc/os-release
find . -name "*.pyc" -delete

# Return to PowerShell
exit
```

## 5. Monitoring MCP Server Status

### Check Health Endpoint
```powershell
# In PowerShell
$health = Invoke-WebRequest http://localhost:8000/health -UseBasicParsing | ConvertFrom-Json
$health | ConvertTo-Json -Depth 10

# Expected output:
# {
#   "status": "healthy",
#   "mcp_servers": {
#     "sqlite": { "status": "healthy", ... },
#     "postgresql": { "status": "docker_required", ... },  # If Docker not running
#     "github": { "status": "healthy", ... },
#     "sonarqube": { "status": "docker_required", ... }
#   },
#   "mcp_healthy_count": 2,
#   "mcp_total_count": 4
# }
```

### Understand Status Values
- **healthy** - Server initialized successfully and ready
- **docker_required** - Server needs Docker (not a failure, Docker just not running)
- **initializing** - Server is starting up (check again in a few seconds)
- **timeout** - Server initialization exceeded 60-second timeout
- **error** - Server initialization failed (check logs)
- **unhealthy** - Server was healthy but is no longer responding

## 6. Common Scenarios

### Scenario: Docker Not Running
**Expected Behavior:**
- PostgreSQL MCP server shows `docker_required` status
- GitHub MCP server shows `healthy` (doesn't need Docker)
- SonarQube MCP server shows `docker_required`
- System still runs normally with degraded MCP functionality

**Fix:**
```powershell
# Start Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
# Wait 2-3 minutes, then restart backend server
```

### Scenario: Language Server Errors
**Symptoms:** Yellow/red squiggles in Python files, type checking errors

**Causes:**
1. Pylance not installed → `code --install-extension ms-python.vscode-pylance`
2. Language server disabled → Check `python.languageServer` in settings.json
3. Too many type errors → Run `python -m pylint` to check for issues

**Resolution:**
```powershell
# Reload VS Code
Ctrl+Shift+P -> "Developer: Reload Window"

# Or restart Python language server
Ctrl+Shift+P -> "Python: Restart Language Server"
```

### Scenario: Terminal Integration Not Working
**Symptoms:** Shell integration test fails, custom args causing issues

**Resolution:**
```powershell
# Verify PowerShell is available
powershell -NoProfile -Command 'Get-Host'

# Reset terminal in VS Code
Ctrl+Shift+P -> "Terminal: Kill the Active Terminal"
Ctrl+Shift+` -> "Create new terminal"

# Verify shell integration
$PSVersionTable.PSVersion
```

### Scenario: MCP Server Initialization Hangs
**Symptoms:** "loading already in progress" message

**Root Cause:** Mutex is preventing concurrent loads (this is expected and correct)

**Resolution:**
```powershell
# Wait for current initialization to complete (max 60 seconds per server)
# If truly stuck:
Stop-Process -Name python -Force  # Kill backend server
# Wait 5 seconds
python main.py  # Restart

# Check for mutex issues in logs
# (No further action usually needed - mutex prevents bad states)
```

## 7. Debugging Tips

### View Backend Logs
```powershell
# Terminal where backend is running
# Look for:
# - "MCP servers: X/4 initialized successfully"
# - "Terminal shells: X/3 initialized successfully"
# - Any [ERROR] messages indicating failures
```

### Check Specific Server Status
```python
# In Python REPL or script
import asyncio
from services.mcp_server_manager import get_mcp_server_manager

async def check_server():
    manager = await get_mcp_server_manager()
    sqlite_status = await manager.get_server_status("sqlite")
    print(f"SQLite: {sqlite_status.status.value}")
    print(f"Error: {sqlite_status.error_message}")

asyncio.run(check_server())
```

### Enable Verbose Pyright Output
```jsonc
// In .vscode/settings.json
"python.analysis.logLevel": "Trace",  // Very verbose
// or
"python.analysis.logLevel": "Information",  // Standard
```

## 8. Next Steps

1. **Quick Validation**
   ```powershell
   cd E:\
   .\validate_startup.ps1
   ```

2. **Start Development**
   ```powershell
   # Terminal 1: Backend
   cd E:\Apps\backend
   python main.py
   
   # Terminal 2: Frontend  
   cd E:\Apps
   npm run dev
   ```

3. **Monitor Health**
   ```powershell
   curl http://localhost:8000/health | ConvertFrom-Json
   ```

4. **Begin Coding**
   - Open VS Code
   - Start coding in PowerShell primary terminal
   - Use WSL for advanced Unix tasks
   - Language server will validate code in real-time

## 9. Key Improvements Made

✓ **Language Server**: Now enabled and strict type checking catches errors early  
✓ **MCP Servers**: Properly configured with Docker detection and graceful degradation  
✓ **Terminal Shells**: PowerShell primary, WSL for Unix tasks, with retry logic  
✓ **Concurrent Loading**: Thread-safe mutex prevents race conditions  
✓ **Health Monitoring**: `/health` endpoint shows system status anytime  
✓ **Startup Validation**: `validate_startup.ps1` script checks all configurations  

## 10. Support

If you encounter issues:

1. **Check Logs**: Look for [ERROR] or [WARNING] messages in backend terminal
2. **Run Validation**: `.\validate_startup.ps1` to diagnose issues
3. **Health Endpoint**: `curl http://localhost:8000/health` to see component status
4. **Restart Components**: Stop and restart backend/frontend as needed
5. **Review Documentation**: See `IMPLEMENTATION_COMPLETE_FIXES.md` for detailed architecture

---

**Summary**: Your development environment now has proper type checking, MCP server management, terminal integration, and concurrent loading protection. PowerShell is primary (Windows workflow), WSL available for advanced tasks.
