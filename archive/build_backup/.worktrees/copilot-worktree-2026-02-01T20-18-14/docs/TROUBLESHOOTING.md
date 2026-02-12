# Troubleshooting Guide

Common issues and solutions for workspace utilities.

## Common Issues

### Issue: workspace_utils import fails

**Symptoms**:
```
ModuleNotFoundError: No module named 'workspace_utils'
```

**Solutions**:
1. Verify workspace_utils is in Python path:
   ```powershell
   code e:\.vscode\settings.json
   # Check that "./workspace_utils" is in python.analysis.extraPaths
   ```

2. Add workspace_utils to Python path manually:
   ```python
   import sys
   sys.path.insert(0, 'e:\\workspace_utils')
   ```

3. Verify workspace_utils directory exists:
   ```powershell
   dir e:\workspace_utils
   ```

### Issue: Root path does not exist

**Symptoms**:
```
ValidationError: Root path does not exist: <path>
```

**Solutions**:
1. Check that the path exists:
   ```powershell
   Test-Path <path>
   ```

2. Verify it's a directory, not a file:
   ```powershell
   Get-Item <path> | Select-Object -ExpandProperty PSIsContainer
   ```

3. Check file permissions:
   ```powershell
   Get-Acl <path>
   ```

### Issue: Output directory not writable

**Symptoms**:
```
ValidationError: Output directory is not writable: <path>
```

**Solutions**:
1. Check write permissions:
   ```powershell
   $acl = Get-Acl <path>
   $acl | Format-List
   ```

2. Create output directory if it doesn't exist:
   ```powershell
   New-Item -ItemType Directory -Path <path> -Force
   ```

3. Run with administrator privileges if needed

### Issue: Analysis fails with permission errors

**Symptoms**:
```
PermissionError: [WinError 5] Access is denied
```

**Solutions**:
1. Check file permissions:
   ```powershell
   Get-Acl <file_path> | Format-List
   ```

2. Run Python with appropriate permissions

3. Exclude problematic directories:
   ```bash
   workspace-utils analyze --root <path> --out <output> --exclude "System Volume Information,$RECYCLE.BIN"
   ```

### Issue: Project comparison fails

**Symptoms**:
```
ComparisonError: Invalid comparison inputs: Analysis directory is missing required files
```

**Solutions**:
1. Ensure both analysis directories contain required files:
   - `candidates.json`
   - `module_graph.json`
   - `file_metrics/` directory

2. Re-run analysis on both projects:
   ```bash
   workspace-utils analyze --root <project1> --out <output1>
   workspace-utils analyze --root <project2> --out <output2>
   ```

3. Verify analysis outputs are valid JSON:
   ```powershell
   Get-Content <output>\candidates.json | ConvertFrom-Json
   ```

### Issue: EUFLE verification fails

**Symptoms**:
```
⚠ Some checks failed
```

**Solutions**:

1. **Ollama not installed**:
   ```powershell
   # Check if Ollama is installed
   ollama --version
   # If not, install from https://ollama.ai
   ```

2. **Ollama server not running**:
   ```bash
   # Start Ollama server
   ollama serve
   ```

3. **Environment variables not set**:
   ```powershell
   # Set environment variables
   $env:EUFLE_DEFAULT_PROVIDER = "ollama"
   $env:EUFLE_DEFAULT_MODEL = "mistral"
   ```

4. **EUFLE root not found**:
   ```powershell
   # Set EUFLE_ROOT environment variable
   $env:EUFLE_ROOT = "e:\EUFLE"
   ```

### Issue: VS Code tasks don't work

**Symptoms**:
- Task fails to run
- "npm script not found" error

**Solutions**:
1. Verify tasks.json exists:
   ```powershell
   Test-Path e:\EUFLE\.vscode\tasks.json
   ```

2. Check npm scripts in package.json:
   ```powershell
   cd e:\EUFLE\dashboard
   npm run
   ```

3. Install dependencies if needed:
   ```powershell
   npm install
   ```

4. Verify working directory:
   - Tasks should use `"path": "dashboard"` in tasks.json
   - Ensure you're in the EUFLE workspace root

### Issue: VS Code debugging doesn't work

**Symptoms**:
- Debugger doesn't attach
- Chrome DevTools not opening

**Solutions**:
1. Verify launch.json exists:
   ```powershell
   Test-Path e:\EUFLE\.vscode\launch.json
   ```

2. Check dev server is running:
   - Should be accessible at http://localhost:5173
   - Verify Vite is using default port

3. Verify Chrome installation:
   - Chrome must be installed
   - Check Chrome path in launch.json

4. Test manual attachment:
   - Start dev server manually
   - Use "Attach to Chrome" configuration

### Issue: OpenCode wrapper fails

**Symptoms**:
```
OpenCode CLI not found at <path>
```

**Solutions**:
1. Verify OpenCode path:
   ```bash
   wsl ls -la /mnt/c/Users/irfan/opencode
   ```

2. Check Bun installation:
   ```bash
   wsl ~/.bun/bin/bun --version
   ```

3. **Note**: OpenCode has known runtime issues. Use alternatives:
   - Use Claude Code directly in Cascade (recommended)
   - Use Anthropic/OpenAI Python SDKs

### Issue: JSON output not generated

**Symptoms**:
- No JSON files in output directory
- Only text output

**Solutions**:
1. Check Cascade integration settings:
   ```python
   from workspace_utils.config import config
   print(config.should_output_json())  # Should be True
   ```

2. Verify config file:
   ```powershell
   Get-Content e:\workspace_utils_config.json
   ```

3. Enable JSON output explicitly:
   ```python
   config.set("cascade_integration.json_output", True)
   config.save()
   ```

### Issue: Tests fail

**Symptoms**:
```
pytest: command not found
```

**Solutions**:
1. Install pytest:
   ```powershell
   pip install pytest pytest-cov
   ```

2. Run tests from workspace root:
   ```powershell
   cd e:\workspace_utils
   python -m pytest tests/
   ```

3. Check test dependencies:
   - Ensure all required packages are installed
   - Check pytest.ini configuration

## Debugging Tips

### Enable verbose output

```bash
# Add --verbose flag
workspace-utils analyze --root <path> --out <output> --verbose
```

### Check configuration

```bash
# View current configuration
workspace-utils config --show
```

### Test individual components

```python
# Test repository analyzer
from workspace_utils import RepositoryAnalyzer
analyzer = RepositoryAnalyzer("test_path", "output_path")
# Check for errors
```

### View error details

All utilities output detailed error messages with suggestions. Read the full error message for specific guidance.

## Getting Help

1. Check this troubleshooting guide
2. Review error messages (they include suggestions)
3. Verify configuration files
4. Test with minimal examples
5. Check known issues in `WORKSPACE_UTILITIES_STATUS.md`

## Common Patterns

### Testing with small repository

```bash
# Create test repo
mkdir test_repo
cd test_repo
echo "print('hello')" > test.py

# Analyze
workspace-utils analyze --root . --out ../test_output
```

### Checking JSON output

```powershell
# Validate JSON files
Get-Content output\candidates.json | ConvertFrom-Json
```

### Validating configuration

```python
from workspace_utils.config import config
print(config.get_output_dir())
print(config.get_excluded_dirs())
```
