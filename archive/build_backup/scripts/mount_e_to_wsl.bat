@echo off
REM Mount E: drive to WSL
REM This script configures .wslconfig to enable E: drive mounting

setlocal enabledelayedexpansion

echo.
echo ====== WSL E: Drive Mount Setup ======
echo.

REM Check if WSL is installed
echo Checking WSL installation...
wsl --list --verbose >nul 2>&1
if errorlevel 1 (
    echo Error: WSL not found or not installed
    pause
    exit /b 1
)
echo [OK] WSL detected

REM Create .wslconfig in user home directory
set WSLCONFIG=%USERPROFILE%\.wslconfig

echo.
echo Creating WSL configuration at %WSLCONFIG%...

REM Backup existing config if it exists
if exist "%WSLCONFIG%" (
    echo Backing up existing .wslconfig...
    copy "%WSLCONFIG%" "%WSLCONFIG%.backup" >nul
)

REM Write new config
(
    echo [interop]
    echo appendWindowsPath = true
    echo.
    echo [automount]
    echo enabled = true
    echo root = /mnt
    echo options = "metadata,umask=22,fmask=11"
    echo.
    echo [wsl2]
    echo memory = 4GB
    echo processors = 4
    echo swap = 2GB
    echo localhostForwarding = true
) > "%WSLCONFIG%"

echo [OK] .wslconfig created

REM Verify E: drive exists
echo.
if exist "E:\" (
    echo [OK] E: drive found
) else (
    echo [WARNING] E: drive not found
)

REM Shutdown WSL to apply changes
echo.
echo Restarting WSL to apply changes...
wsl --shutdown
timeout /t 3 /nobreak

REM Verify mount
echo.
echo Verifying mount in WSL...
wsl ls -la /mnt/e/ >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Mount verification failed
    wsl ls -la /mnt/e/ 2>&1
) else (
    echo [OK] E: drive successfully mounted at /mnt/e/
    echo.
    echo Contents of /mnt/e/:
    wsl ls -lh /mnt/e/
)

echo.
echo ====== Setup Complete ======
echo.
echo E: drive is now accessible at /mnt/e/ in WSL
echo You can access files with: wsl ls /mnt/e/
echo.
pause
