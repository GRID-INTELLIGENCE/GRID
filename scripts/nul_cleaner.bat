@echo off
setlocal

REM Find Python executable in venv
set PYTHON_EXE=
if exist ".\.venv\Scripts\python.exe" (
    set PYTHON_EXE=.\.venv\Scripts\python.exe
) else if exist ".\.venv\Scripts\python3.exe" (
    set PYTHON_EXE=.\.venv\Scripts\python3.exe
) else (
    echo Python executable not found in .venv
    exit /b 1
)

REM Run the cleaner with all arguments
%PYTHON_EXE% scripts/nul_cleaner.py %*
