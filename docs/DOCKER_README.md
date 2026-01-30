# Docker Setup and Containerization Guide

This guide covers setting up Docker containerization for the Grid project, including troubleshooting common Docker Desktop issues.

## Prerequisites

- Docker Desktop installed
- Windows Subsystem for Linux (WSL2) enabled
- At least 4GB RAM allocated to Docker

## Quick Start

### Using PowerShell (Windows)
```powershell
# Build and start the application
.\docker.ps1 -Command build
.\docker.ps1 -Command start

# Run tests
.\docker.ps1 -Command test

# View status
.\docker.ps1 -Command status
```

### Using Bash (Linux/Mac)
```bash
# Make script executable
chmod +x docker.sh

# Build and start the application
./docker.sh build
./docker.sh start

# Run tests
./docker.sh test
```

## Troubleshooting Docker Desktop Issues

### Issue: Docker Desktop Unable to Start

**Symptoms:**
- Docker commands fail with "Docker Desktop is unable to start"
- WSL errors related to `docker-desktop` distro

**Solutions:**

1. **Reset Docker Desktop:**
   ```powershell
   # Stop Docker Desktop
   Stop-Process -Name "Docker Desktop" -Force

   # Reset to factory defaults (in Docker Desktop UI)
   # Or delete settings file:
   Remove-Item "$env:APPDATA\Docker\settings-store.json"
   ```

2. **Reset WSL Backend:**
   ```powershell
   # Shutdown WSL
   wsl --shutdown

   # Reset Docker Desktop WSL data
   Remove-Item "$env:LOCALAPPDATA\Docker\wsl\*" -Recurse -Force

   # Restart Docker Desktop
   ```

3. **Reinstall Docker Desktop:**
   - Uninstall Docker Desktop
   - Delete `%APPDATA%\Docker` and `%LOCALAPPDATA%\Docker`
   - Reinstall Docker Desktop

### Issue: WSL Distribution Errors

**Symptoms:**
- `ERROR_NOT_FOUND` when importing docker-desktop
- WSL commands fail

**Solutions:**

1. **Update WSL:**
   ```powershell
   wsl --update
   wsl --shutdown
   ```

2. **Manually register Docker distro:**
   ```powershell
   # Check if vhdx exists
   ls "$env:LOCALAPPDATA\Docker\wsl\main"

   # Try to import manually
   wsl --import docker-desktop "$env:LOCALAPPDATA\Docker\wsl\main" "$env:LOCALAPPDATA\Docker\wsl\main\ext4.vhdx"
   ```

3. **Enable WSL features:**
   ```powershell
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   ```

### Issue: Permission Denied

**Symptoms:**
- Cannot start/stop Docker services
- Access denied errors

**Solutions:**

1. **Run as Administrator:**
   ```powershell
   # Run PowerShell as Administrator
   Start-Process powershell -Verb runAs
   ```

2. **Reset Docker permissions:**
   ```powershell
   # Add user to docker-users group
   net localgroup docker-users $env:USERNAME /add
   ```

## Containerization Workflow

### Development

1. **Build container:**
   ```powershell
   .\docker.ps1 -Command build
   ```

2. **Run tests in container:**
   ```powershell
   .\docker.ps1 -Command test-coverage
   ```

3. **Start development server:**
   ```powershell
   .\docker.ps1 -Command start
   ```

### Production

1. **Build production image:**
   ```powershell
   docker build -t grid:prod --target prod .
   ```

2. **Run with docker-compose:**
   ```powershell
   docker-compose up -d
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
├── Dockerfile              # Main application container
├── Dockerfile.test         # Test container (existing)
├── docker-compose.yml      # Multi-service setup
├── docker.sh              # Bash management script
├── docker.ps1             # PowerShell management script
├── .dockerignore          # Docker build exclusions
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

- Container logs: `docker-compose logs`
- Health status: `docker ps`
- Resource usage: `docker stats`

## Support

If issues persist:
1. Check Docker Desktop logs
2. Verify WSL installation
3. Ensure sufficient resources (4GB+ RAM)
4. Try Docker Desktop factory reset
