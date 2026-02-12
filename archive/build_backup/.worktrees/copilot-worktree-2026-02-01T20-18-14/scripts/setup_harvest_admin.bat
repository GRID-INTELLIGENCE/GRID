@echo off
powershell.exe -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File E:\setup_daily_harvest.ps1' -Verb RunAs"
