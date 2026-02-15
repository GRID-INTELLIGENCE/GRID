# WSL Mount Issue - Quick Fix Guide

## Problem
WSL cannot access Windows E: drive at path `/mnt/e/EUFLE`

## Root Cause
WSL auto-mounting of Windows drives is disabled or misconfigured.

---

## ⚡ Quick Fix (5 minutes)

### Step 1: Run Diagnostic
```powershell
.\wsl_diagnostic.ps1
```
This will tell you exactly what's missing.

### Step 2: Enable WSL Drive Mounting

**In WSL terminal, run:**
```bash
sudo nano /etc/wsl.conf
```

**Add these lines (if not already there):**
```ini
[automount]
enabled = true
options = "metadata"
```

**Save:** `Ctrl+O` → `Enter` → `Ctrl+X`

### Step 3: Restart WSL
```powershell
wsl --shutdown
```

Then open WSL terminal again.

### Step 4: Verify Fix
```bash
ls /mnt/e/EUFLE/
```

Should show: `scripts/`, `eufle/`, `README.md`, etc.

---

## Alternative: Check Current Config

If you want to see the current WSL config without editing:

```bash
cat /etc/wsl.conf
```

---

## If Still Not Working

### Check mount status in WSL:
```bash
mount | grep /mnt
```

Should show something like:
```
/dev/sdc on /mnt/e type drvfs (rw,relatime,metadata,umask=22,fmask=11)
```

### Force remount Windows drives:
```bash
sudo mount -t drvfs E: /mnt/e -o metadata
```

### Or try uppercase path:
```bash
ls /mnt/E/EUFLE
```
(Some systems use uppercase drive letters)

---

## Once Fixed, Run Setup

```bash
cd /mnt/e/EUFLE
bash scripts/setup_llamacpp.sh
```

---

## Files Available

- `wsl_diagnostic.ps1` → Run this first (PowerShell)
- `EUFLE/scripts/wsl_diagnostic.sh` → Run in WSL for detailed diagnostics
- `EUFLE/scripts/setup_llamacpp.sh` → Actual setup script (run after fixing mount)

---

## Need More Help?

Check WSL docs: https://docs.microsoft.com/en-us/windows/wsl/
Or: `wsl --help`
