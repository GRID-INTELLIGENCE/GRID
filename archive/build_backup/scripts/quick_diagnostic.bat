@echo off
REM Quick WSL Mount Diagnostic
REM Run this to check if WSL can access E:\EUFLE

echo.
echo ════════════════════════════════════════════════════
echo    WSL Mount Diagnostic
echo ════════════════════════════════════════════════════
echo.

echo [1/5] Checking WSL installation...
wsl --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('wsl --version') do echo ✓ %%i
) else (
    echo ⚠ WSL might be version 1 or not fully installed
)
echo.

echo [2/5] Checking Windows E: drive...
if exist "E:\EUFLE" (
    echo ✓ E:\EUFLE found on Windows
) else (
    echo ✗ E:\EUFLE NOT found on Windows
    exit /b 1
)
echo.

echo [3/5] Checking if WSL can see E: drive as /mnt/e...
wsl test -d "/mnt/e" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ WSL can access /mnt/e
) else (
    echo ✗ WSL CANNOT access /mnt/e
    echo   This needs to be fixed
)
echo.

echo [4/5] Checking if WSL can see /mnt/e/EUFLE...
wsl test -d "/mnt/e/EUFLE" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ WSL can access /mnt/e/EUFLE
    echo.
    echo SUCCESS! Ready to run setup:
    echo   wsl bash /mnt/e/EUFLE/scripts/setup_llamacpp.sh
) else (
    echo ✗ WSL CANNOT access /mnt/e/EUFLE
    echo   Fix needed - see FIX_WSL_MOUNT.bat
)
echo.

echo [5/5] Checking setup script...
if exist "E:\EUFLE\scripts\setup_llamacpp.sh" (
    echo ✓ setup_llamacpp.sh exists
) else (
    echo ✗ setup_llamacpp.sh NOT found
)
echo.

echo ════════════════════════════════════════════════════
echo    DIAGNOSTIC COMPLETE
echo ════════════════════════════════════════════════════
echo.

pause
