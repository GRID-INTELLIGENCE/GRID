# VS Code Setup Guide

Setup and troubleshooting guide for VS Code configurations in the EUFLE dashboard project.

## Configuration Files

### Tasks Configuration
- **Location**: `EUFLE/.vscode/tasks.json`
- **Purpose**: Provides one-click commands for dashboard development
- **Tasks Available**:
  - Dashboard: Dev Server
  - Dashboard: Build
  - Dashboard: Lint
  - Dashboard: Preview

### Launch Configuration
- **Location**: `EUFLE/.vscode/launch.json`
- **Purpose**: Debugging configurations for React app
- **Configurations Available**:
  - Dashboard: Debug React App
  - Dashboard: Attach to Chrome

## Setup Instructions

### 1. Prerequisites

```powershell
# Verify Node.js is installed
node --version

# Verify npm is installed
npm --version

# Navigate to dashboard directory
cd e:\EUFLE\dashboard

# Install dependencies
npm install
```

### 2. Verify Tasks Configuration

```powershell
# Check tasks.json exists
Test-Path e:\EUFLE\.vscode\tasks.json

# Open in VS Code
code e:\EUFLE\.vscode\tasks.json
```

### 3. Test Tasks

1. Open VS Code in EUFLE workspace:
   ```powershell
   code e:\EUFLE
   ```

2. Open Command Palette (Ctrl+Shift+P)

3. Run "Tasks: Run Task"

4. Select "Dashboard: Dev Server"

5. Verify Vite dev server starts at http://localhost:5173

### 4. Test Launch Configuration

1. Open VS Code in EUFLE workspace

2. Go to Run and Debug panel (Ctrl+Shift+D)

3. Select "Dashboard: Debug React App"

4. Press F5 or click "Start Debugging"

5. Verify:
   - Dev server starts automatically
   - Chrome opens with DevTools
   - Debugger attaches to React app

## Troubleshooting

### Issue: Task not found

**Solution**:
1. Verify tasks.json location is correct
2. Ensure you're in the EUFLE workspace (not just dashboard folder)
3. Reload VS Code window (Ctrl+Shift+P → "Developer: Reload Window")

### Issue: npm script not found

**Solution**:
1. Check package.json scripts:
   ```powershell
   cd e:\EUFLE\dashboard
   Get-Content package.json | Select-String -Pattern "scripts" -Context 0,10
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

### Issue: Dev server doesn't start

**Solution**:
1. Check if port 5173 is already in use:
   ```powershell
   netstat -ano | findstr :5173
   ```

2. Manually start dev server to see errors:
   ```powershell
   cd e:\EUFLE\dashboard
   npm run dev
   ```

### Issue: Debugger doesn't attach

**Solution**:
1. Verify Chrome is installed

2. Check launch.json configuration:
   - URL should be http://localhost:5173
   - webRoot should point to dashboard directory

3. Ensure dev server is running before debugging:
   - Use preLaunchTask or start manually

4. Try "Attach to Chrome" configuration if auto-launch fails

### Issue: Source maps not working

**Solution**:
1. Verify sourceMapPathOverrides in launch.json

2. Check vite.config.ts for source map settings:
   ```typescript
   build: {
     sourcemap: true
   }
   ```

3. Rebuild with source maps:
   ```powershell
   npm run build
   ```

## Validation Checklist

### Tasks Validation

- [ ] Dashboard: Dev Server starts Vite dev server
- [ ] Dashboard: Build compiles TypeScript successfully
- [ ] Dashboard: Lint runs ESLint without errors
- [ ] Dashboard: Preview starts preview server

### Launch Validation

- [ ] Dashboard: Debug React App starts dev server
- [ ] Dashboard: Debug React App opens Chrome with DevTools
- [ ] Dashboard: Debug React App attaches debugger
- [ ] Dashboard: Attach to Chrome works with running server
- [ ] Breakpoints hit correctly
- [ ] Variables visible in debugger
- [ ] Source maps resolve correctly

## Configuration Details

### Tasks.json Structure

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Dashboard: Dev Server",
      "type": "npm",
      "script": "dev",
      "path": "dashboard",
      "group": { "kind": "build", "isDefault": true },
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    }
  ]
}
```

### Launch.json Structure

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Dashboard: Debug React App",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:5173",
      "webRoot": "${workspaceFolder}/dashboard",
      "preLaunchTask": "Dashboard: Dev Server"
    }
  ]
}
```

## Best Practices

1. **Always use tasks for npm scripts**: Don't run npm commands manually in terminal
2. **Use debug configuration**: Always use launch configuration for debugging, not manual Chrome DevTools
3. **Check preLaunchTask**: Ensure preLaunchTask is set for auto-starting dev server
4. **Verify working directory**: Tasks should specify `"path": "dashboard"` to run from correct directory

## Cascade Integration

VS Code tasks and launch configurations enable Cascade to:
- Track development workflow
- Understand debugging sessions
- Provide context-aware assistance
- Automate repetitive tasks

All configurations are designed to work seamlessly with Cascade's terminal tracking and browser integration.

## Additional Resources

- [VS Code Tasks Documentation](https://code.visualstudio.com/docs/editor/tasks)
- [VS Code Debugging Documentation](https://code.visualstudio.com/docs/editor/debugging)
- [React Debugging Guide](https://react.dev/learn/react-developer-tools)