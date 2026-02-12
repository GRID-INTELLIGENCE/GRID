@echo off
REM Fix WSL Mount Issues - Run in WSL terminal

echo.
echo ════════════════════════════════════════════════════
echo    WSL Mount Fix - Instructions
echo ════════════════════════════════════════════════════
echo.

echo STEP 1: Open WSL terminal
echo   Type in PowerShell: wsl
echo.

echo STEP 2: Edit /etc/wsl.conf
echo   Run: sudo nano /etc/wsl.conf
echo.

echo STEP 3: Add these lines:
echo   [automount]
echo   enabled = true
echo   options = "metadata"
echo.

echo STEP 4: Save the file
echo   Press: Ctrl+O
echo   Press: Enter
echo   Press: Ctrl+X
echo.

echo STEP 5: Exit WSL and restart
echo   Type: exit
echo   Then in PowerShell: wsl --shutdown
echo.

echo STEP 6: Reopen WSL and verify
echo   Type in PowerShell: wsl
echo   Run: ls /mnt/e/EUFLE
echo   Should see files and directories
echo.

echo STEP 7: Run setup
echo   Run: bash /mnt/e/EUFLE/scripts/setup_llamacpp.sh
echo.

echo ════════════════════════════════════════════════════
echo.

pause
