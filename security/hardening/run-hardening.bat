@echo off
REM Simple launcher for security hardening scripts
REM Right-click this file and select "Run as administrator"

setlocal enabledelayedexpansion

cls
echo.
echo ================================================================
echo Windows Security Hardening - Configuration Launcher
echo ================================================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires Administrator privileges
    echo.
    echo Please right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

echo.
echo What would you like to do?
echo.
echo 1. Apply security hardening (recommended)
echo 2. Verify hardening is applied
echo 3. Rollback all changes
echo 4. View security audit details
echo 5. View troubleshooting guide
echo 6. Exit
echo.

set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" (
    cls
    echo.
    echo Applying security hardening...
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -Command "& '!CD!\Apply-Security-Hardening.ps1'"
    echo.
    pause
) else if "%choice%"=="2" (
    cls
    echo.
    echo Verifying security hardening...
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -Command "& '!CD!\Verify-Security-Hardening.ps1'"
    echo.
    pause
) else if "%choice%"=="3" (
    cls
    echo.
    echo WARNING: This will remove all security hardening rules
    echo.
    set /p confirm="Are you sure? Type 'yes' to confirm: "
    if /i "!confirm!"=="yes" (
        echo.
        echo Rolling back changes...
        echo.
        powershell -NoProfile -ExecutionPolicy Bypass -Command "& '!CD!\Apply-Security-Hardening.ps1' -Rollback"
    ) else (
        echo Rollback cancelled
    )
    echo.
    pause
) else if "%choice%"=="4" (
    cls
    more "!CD!\WINDOWS_SECURITY_AUDIT.md"
    pause
) else if "%choice%"=="5" (
    cls
    more "!CD!\TROUBLESHOOTING.md"
    pause
) else (
    echo Exiting...
    exit /b 0
)

goto :eof
