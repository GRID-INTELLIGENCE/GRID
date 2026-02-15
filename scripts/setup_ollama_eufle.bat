@echo off
REM EUFLE + Ollama Setup (Windows CMD)
REM This script sets up EUFLE to use Ollama as the language model provider

setlocal enabledelayedexpansion

echo.
echo ================================
echo EUFLE + Ollama Setup Script
echo ================================
echo.

REM Step 1: Check Ollama installation
echo [1/3] Checking Ollama installation...
ollama --version >nul 2>&1

if errorlevel 1 (
    echo X Ollama not installed or not in PATH
    echo.
    echo To install Ollama:
    echo   1. Download from https://ollama.ai
    echo   2. Install and restart CMD
    echo   3. Run: ollama pull mistral
    echo   4. Then re-run this script
    echo.
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('ollama --version') do set OLLAMA_VER=%%i
    echo. Ollama found: !OLLAMA_VER!
)

REM Step 2: Set temporary environment variable
echo.
echo [2/3] Setting EUFLE_DEFAULT_PROVIDER environment variable...
set EUFLE_DEFAULT_PROVIDER=ollama
echo. Environment variable set for this session

REM Step 3: Inform about permanent setup
echo.
echo [3/3] Permanent setup (optional)...
echo. To set permanently for all sessions, use setx:
echo.
echo   setx EUFLE_DEFAULT_PROVIDER ollama
echo.
echo. Then restart CMD/PowerShell
echo.

REM Verification
echo ================================
echo Setup Complete!
echo ================================
echo.
echo Next steps:
echo   1. Start Ollama server: ollama serve (in another window)
echo   2. Verify with: ollama list
echo   3. Test EUFLE: python eufle.py --ask
echo.
echo Current environment variable:
echo   EUFLE_DEFAULT_PROVIDER=!EUFLE_DEFAULT_PROVIDER!
echo.

endlocal
