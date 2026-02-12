# WSL + llama-cli Setup - Complete Runbook

**Date:** January 18, 2026  
**Status:** Diagnostics created, ready for execution

---

## Quick Start - Immediate Actions

### For Windows Users (Choice of 2 paths):

#### 🚀 Path A: Ollama (Works Now - NO Setup Needed)
```powershell
$env:EUFLE_DEFAULT_PROVIDER = "ollama"
ollama serve                          # In separate terminal
python eufle.py --ask
```

#### 🔧 Path B: WSL + llama-cli (Needs setup)

**1. Check if setup is possible:**
```cmd
quick_diagnostic.bat
```
or
```powershell
powershell -ExecutionPolicy Bypass -File quick_diagnostic.ps1
```

**2. If TEST 4 shows "✓ YES":**
```powershell
wsl bash /mnt/e/EUFLE/scripts/setup_llamacpp.sh
```

**3. If TEST 4 shows "✗ NO":**
```cmd
FIX_WSL_MOUNT.bat
```
Then follow the instructions to fix the mount.

---

## Detailed Setup Steps

### Step 1: Check Current Status

Run the quick diagnostic:
```powershell
# PowerShell version (recommended)
powershell -ExecutionPolicy Bypass -File quick_diagnostic.ps1

# Or batch version
quick_diagnostic.bat
```

This will check:
- ✓ WSL installation
- ✓ Available distros
- ✓ Windows E: drive
- ✓ WSL /mnt/e mount
- ✓ Setup script existence

### Step 2: If /mnt/e/EUFLE is NOT accessible

**Run the fix:**
```cmd
FIX_WSL_MOUNT.bat
```

**Or manually:**

1. Open WSL terminal:
```powershell
wsl
```

2. Edit the config:
```bash
sudo nano /etc/wsl.conf
```

3. Add/ensure these lines exist:
```ini
[automount]
enabled = true
options = "metadata"
```

4. Save: `Ctrl+O` → `Enter` → `Ctrl+X`

5. Exit and restart WSL:
```bash
exit
```
```powershell
wsl --shutdown
# Then open WSL again
wsl
```

6. Verify:
```bash
ls -la /mnt/e/EUFLE/
```

Should show: `scripts/`, `eufle/`, `README.md`, etc.

### Step 3: Run the Setup

Once `/mnt/e/EUFLE` is accessible:

```bash
cd /mnt/e/EUFLE
bash scripts/setup_llamacpp.sh
```

Or from PowerShell:
```powershell
wsl bash /mnt/e/EUFLE/scripts/setup_llamacpp.sh
```

### Step 4: Configure Environment

After setup completes:
```powershell
# Get the EUFLE root directory dynamically
$eufleRoot = (Get-Item $PSScriptRoot -ErrorAction SilentlyContinue).Parent.FullName
if (-not (Test-Path "$eufleRoot\EUFLE")) {
    $eufleRoot = $PSScriptRoot
}

$env:EUFLE_ROOT = $eufleRoot
$env:EUFLE_DEFAULT_PROVIDER = "llamacpp"
$env:EUFLE_GGUF_MODEL = "$eufleRoot\EUFLE\hf-models\ministral-14b\consolidated.safetensors"

# Optional - make permanent
[Environment]::SetEnvironmentVariable("EUFLE_ROOT", $eufleRoot, "User")
[Environment]::SetEnvironmentVariable("EUFLE_DEFAULT_PROVIDER", "llamacpp", "User")
[Environment]::SetEnvironmentVariable("EUFLE_GGUF_MODEL", "$eufleRoot\EUFLE\hf-models\ministral-14b\consolidated.safetensors", "User")
```

### Step 5: Test

```powershell
python eufle.py --ask
```

---

## Available Diagnostic & Setup Scripts

### PowerShell Scripts

| Script | Purpose | Run With |
|--------|---------|----------|
| `quick_diagnostic.ps1` | Quick WSL status check | `powershell -ExecutionPolicy Bypass -File quick_diagnostic.ps1` |
| `setup_wsl_complete.ps1` | Full diagnostics + instructions | `powershell -ExecutionPolicy Bypass -File setup_wsl_complete.ps1` |
| `setup_ollama_eufle.ps1` | Ollama configuration | `.\setup_ollama_eufle.ps1 -Permanent` |

### Batch Scripts

| Script | Purpose | Run With |
|--------|---------|----------|
| `quick_diagnostic.bat` | Quick WSL status check | `quick_diagnostic.bat` |
| `FIX_WSL_MOUNT.bat` | WSL mount fix instructions | `FIX_WSL_MOUNT.bat` |

### Python Scripts

| Script | Purpose | Run With |
|--------|---------|----------|
| `verify_eufle_setup.py` | Full setup verification | `python verify_eufle_setup.py` |
| `EUFLE/scripts/setup_llamacpp.sh` | Build llama-cli (WSL) | `wsl bash /mnt/e/EUFLE/scripts/setup_llamacpp.sh` |

---

## Three Configuration Options Summary

### Option 1: Ollama ✅ (Ready Now)
- **Status:** Can use immediately
- **Setup time:** 2 minutes
- **Command:** `python eufle.py --ask`
- **Complexity:** Easiest

### Option 2: WSL + llama-cli ⚙️ (Needs Setup)
- **Status:** Infrastructure ready, mount may need fix
- **Setup time:** 10-15 minutes (including fix if needed)
- **Command:** `wsl bash /mnt/e/EUFLE/scripts/setup_llamacpp.sh`
- **Complexity:** Medium

### Option 3: Local HF Model ✅ (Already Works)
- **Status:** Automatic, no setup
- **Setup time:** 0 minutes
- **Command:** `python eufle.py --ask` (automatic fallback)
- **Complexity:** None

---

## Troubleshooting

### "WSL not installed"
**Solution:** `wsl --install` then restart Windows

### "/mnt/e/EUFLE not accessible"
**Solution:** Run `FIX_WSL_MOUNT.bat` or follow manual fix in Step 2 above

### "setup_llamacpp.sh not found"
**Solution:** Check path: `ls /mnt/e/EUFLE/scripts/` in WSL

### "Script runs but takes very long"
**Solution:** Normal - building GGUF binary takes 5-10 minutes
- Keep terminal open and wait
- Check logs: `tail -f build.log` (if available)

### "Build fails with errors"
**Solution:** 
1. Check WSL has 4GB+ RAM: `wsl --list --verbose`
2. Update WSL: `wsl --update`
3. Run `wsl --shutdown` and try again

---

## File Locations Reference

```
$env:EUFLE_ROOT                  ← Root directory (auto-detected)
├── quick_diagnostic.ps1         ← Quick diagnostic (PowerShell)
├── quick_diagnostic.bat         ← Quick diagnostic (Batch)
├── setup_wsl_complete.ps1       ← Full setup script
├── setup_ollama_eufle.ps1       ← Ollama setup
├── setup_ollama_eufle.bat       ← Ollama setup (CMD)
├── FIX_WSL_MOUNT.bat            ← Mount fix instructions
├── verify_eufle_setup.py        ← Verification tool
├── EUFLE_SETUP_GUIDE.md         ← Full setup guide
├── WSL_MOUNT_FIX.md             ← Mount fix details
├── QUICK_REFERENCE.md           ← Quick reference card
└── EUFLE\
    ├── eufle.py                 ← Main CLI
    ├── scripts\
    │   ├── setup_llamacpp.sh    ← Build llama-cli
    │   ├── wsl_bridge.py        ← WSL integration
    │   ├── wsl_diagnostic.sh    ← WSL diagnostics
    │   └── ...
    ├── hf-models\
    │   └── ministral-14b\
    │       ├── tokenizer.json   ✓ Valid
    │       ├── consolidated.safetensors
    │       └── config.json
    └── studio\
        └── unified_api.py       ← Provider selection
```

---

## Environment Variables

### For Ollama:
```powershell
$env:EUFLE_DEFAULT_PROVIDER = "ollama"
```

### For WSL + llama-cli:
```powershell
$eufleRoot = $env:EUFLE_ROOT  # Set via step 4 above
$env:EUFLE_DEFAULT_PROVIDER = "llamacpp"
$env:EUFLE_GGUF_MODEL = "$eufleRoot\EUFLE\hf-models\ministral-14b\consolidated.safetensors"
```

### Optional - HF Model:
```powershell
$env:EUFLE_DEFAULT_PROVIDER = "auto"  # Auto-fallback
```

---

## Next Actions (In Order)

1. ✅ **Run diagnostic:**
   ```
   quick_diagnostic.bat
   ```

2. 📋 **Check the TEST 4 result**

3. ✅ **If TEST 4 = YES:**
   ```
   wsl bash /mnt/e/EUFLE/scripts/setup_llamacpp.sh
   ```

4. ⚙️ **If TEST 4 = NO:**
   ```
   FIX_WSL_MOUNT.bat
   ← Follow instructions
   ← Try again
   ```

5. 🚀 **After setup completes:**
   ```powershell
   $env:EUFLE_DEFAULT_PROVIDER = "llamacpp"
   python eufle.py --ask
   ```

---

## Support & Documentation

- Full setup guide: `EUFLE_SETUP_GUIDE.md`
- Mount fix guide: `WSL_MOUNT_FIX.md`
- Quick reference: `QUICK_REFERENCE.md`
- EUFLE docs: `$env:EUFLE_ROOT\EUFLE\README.md`
- WSL docs: `$env:EUFLE_ROOT\EUFLE\docs\wsl_setup.md`

---

**Status:** All setup infrastructure is ready. Execute diagnostics to proceed.
