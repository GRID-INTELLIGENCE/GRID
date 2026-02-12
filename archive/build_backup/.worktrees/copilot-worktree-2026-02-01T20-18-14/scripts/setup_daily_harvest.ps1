# Setup Daily Harvest Task - Windows Native
$taskName = "DailyHarvestRoutine"
$scriptPath = "E:\daily_harvest.ps1"

# Create task action
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File '$scriptPath'"

# Create daily trigger - Default to 9am, can be overridden here
$trigger = New-ScheduledTaskTrigger -Daily -At 9am

# Create task settings - Robust for various power states
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries

# Register or update the task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -User "$env:USERNAME" -RunLevel Highest

Write-Host "Scheduled task '$taskName' created/updated to run daily at 9am."
Write-Host "To test immediately: powershell -ExecutionPolicy Bypass -File '$scriptPath'"
