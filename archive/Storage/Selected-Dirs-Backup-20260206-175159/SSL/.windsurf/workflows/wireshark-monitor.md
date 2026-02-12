---
description: Run Wireshark-based network monitoring workflow with WSL capture, parsing, and E:\ directory routing
---

# Wireshark Network Monitoring Workflow

## Prerequisites
- WSL installed with `tshark` (`sudo apt install tshark`)
- Python 3 in WSL with `pyshark` (`pip install pyshark`)
- `sudo` access in WSL (tshark requires root for packet capture)
- Network interface identified (run `ip a` in WSL to find yours, default: `eth0`)

## Cleanup Policy (Debug Feature)
Cleanup is a **debugging feature** that scans ALL directories but ONLY removes corrupt/broken files:
- 0-byte `.pcapng` files (failed/incomplete captures)
- Malformed `.json` files (invalid JSON)
- 0-byte `.yaml`/`.yml` files (empty configs)

**NEVER removed:** `.py`, `.ps1`, `.sh`, `.md`, `.txt`, and all other development files.
Must be explicitly activated with `-DebugCleanup` flag.

## Steps

1. Ensure target directories exist:
```powershell
New-Item -ItemType Directory -Path 'E:\SSL' -Force
New-Item -ItemType Directory -Path 'E:\grid' -Force
New-Item -ItemType Directory -Path 'E:\coinbase' -Force
New-Item -ItemType Directory -Path 'E:\wellness_studio' -Force
```

2. Run the full automation from PowerShell (capture uses sudo tshark):
```powershell
E:\SSL\wireshark-monitor\scripts\route_wsl_traffic.ps1
```

3. Or run individual steps:
```powershell
# Capture only
E:\SSL\wireshark-monitor\scripts\route_wsl_traffic.ps1 -SkipParse -SkipCleanup

# Parse only (after capture completes)
E:\SSL\wireshark-monitor\scripts\route_wsl_traffic.ps1 -SkipCapture -SkipCleanup

# Debug cleanup: scan all dirs for corrupt files only
E:\SSL\wireshark-monitor\scripts\route_wsl_traffic.ps1 -SkipCapture -SkipParse -DebugCleanup
```

4. Or run via WSL bash:
```bash
chmod +x /mnt/e/SSL/wireshark-monitor/scripts/automate_workflow.sh
# Normal run (no cleanup)
/mnt/e/SSL/wireshark-monitor/scripts/automate_workflow.sh eth0
# With debug cleanup
/mnt/e/SSL/wireshark-monitor/scripts/automate_workflow.sh eth0 "src host 192.168.1.0/24" debug-cleanup
```

5. Check results:
```powershell
Get-ChildItem E:\SSL\* -Filter "*.json"
Get-ChildItem E:\SSL\* -Filter "*.md"
```

## Configuration
Edit `E:\SSL\wireshark-monitor\config\routing_schema.yaml` to customize:
- Network interface
- Capture filters per directory
- Corrupt file detection rules
