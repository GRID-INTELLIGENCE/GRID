

## Prerequisites

- Windows Subsystem for Linux (WSL2) enabled

## Quick Start

### Using PowerShell (Windows)
```powershell
# Build and start the application

# Run tests

# View status
```

### Using Bash (Linux/Mac)
```bash
# Make script executable

# Build and start the application

# Run tests
```



**Symptoms:**

**Solutions:**

   ```powershell

   # Or delete settings file:
   ```

2. **Reset WSL Backend:**
   ```powershell
   # Shutdown WSL
   wsl --shutdown


   ```


### Issue: WSL Distribution Errors

**Symptoms:**
- WSL commands fail

**Solutions:**

1. **Update WSL:**
   ```powershell
   wsl --update
   wsl --shutdown
   ```

   ```powershell
   # Check if vhdx exists

   # Try to import manually
   ```

3. **Enable WSL features:**
   ```powershell
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   ```

### Issue: Permission Denied

**Symptoms:**
- Access denied errors

**Solutions:**

1. **Run as Administrator:**
   ```powershell
   # Run PowerShell as Administrator
   Start-Process powershell -Verb runAs
   ```

   ```powershell
   ```

## Containerization Workflow

### Development

1. **Build container:**
   ```powershell
   ```

2. **Run tests in container:**
   ```powershell
   ```

3. **Start development server:**
   ```powershell
   ```

### Production

1. **Build production image:**
   ```powershell
   ```

   ```powershell
   ```

## Available Commands

- `build` - Build application container
- `start` - Start the application
- `stop` - Stop the application
- `test` - Run tests
- `test-coverage` - Run tests with coverage
- `logs` - View logs
- `clean` - Clean containers/images
- `reset` - Full reset
- `status` - Show status

## File Structure

```
└── Python/requirements.txt # Python dependencies
```

## Health Checks

The application includes health checks:
- HTTP endpoint: `GET /health`
- Database connectivity
- Service availability

## Volumes and Persistence

- Application code is volume-mounted for development
- Database uses named volumes in production
- Logs persist across container restarts

## Security Considerations

- Non-root user in containers
- Minimal base images (python:3.14-slim)
- No sensitive data in images
- Regular security updates

## Monitoring


## Support

If issues persist:
2. Verify WSL installation
3. Ensure sufficient resources (4GB+ RAM)
