# EUFLE Setup - Quick Reference Card

## One-Minute Setup (Choose One Path)

### 🚀 Path 1: Ollama (Fastest - RECOMMENDED)
```powershell
# 1. Set environment variable
$env:EUFLE_DEFAULT_PROVIDER = "ollama"

# 2. Start Ollama (new terminal)
ollama serve

# 3. Test it
python verify_eufle_setup.py
```

### 🔧 Path 2: WSL + llama-cli
```powershell
# 1. Check WSL
python E:\EUFLE\scripts\wsl_bridge.py check

# 2. Build llama-cli
wsl bash E:\EUFLE\scripts\setup_llamacpp.sh

# 3. Set variables
$env:EUFLE_DEFAULT_PROVIDER = "llamacpp"
$env:EUFLE_GGUF_MODEL = "$env:EUFLE_ROOT\EUFLE\hf-models\ministral-14b\consolidated.safetensors"
```

### 💾 Path 3: Local Model (Already Works)
```powershell
# No setup needed! Default fallback to:
# E:\EUFLE\hf-models\ministral-14b\
```

---

## Automated Setup

```powershell
# Run this to auto-setup Ollama + set env variables
.\setup_ollama_eufle.ps1 -Permanent
```

---

## Verify Everything Works

```powershell
python verify_eufle_setup.py
```

Expected output: ✓ All checks passed!

---

## Run EUFLE

```powershell
python eufle.py --ask
```

---

## Environment Variable Locations

**Temporary (current session):**
```powershell
$env:EUFLE_DEFAULT_PROVIDER = "ollama"
```

**Permanent (all future sessions):**
```powershell
# PowerShell (recommended)
[Environment]::SetEnvironmentVariable("EUFLE_DEFAULT_PROVIDER", "ollama", "User")

# Or Windows (requires restart)
setx EUFLE_DEFAULT_PROVIDER ollama

# Or Settings > Environment Variables (GUI)
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Ollama not found" | Download from https://ollama.ai, install, restart terminal |
| "Server not responding" | Run `ollama serve` in separate terminal |
| "Model not found" | Run `ollama pull mistral` |
| "Connection refused" | Check Ollama server is running + firewall allows localhost:11434 |

---

## Files Created

- `setup_ollama_eufle.ps1` → Automated setup script
- `setup_ollama_eufle.bat` → CMD version
- `verify_eufle_setup.py` → Verification tool
- `EUFLE_SETUP_GUIDE.md` → Complete documentation
- `IMPLEMENTATION_SUMMARY.md` → Full implementation details
- `QUICK_REFERENCE.md` → This file

---

## Support

View setup guide: `EUFLE_SETUP_GUIDE.md`  
Check implementation: `IMPLEMENTATION_SUMMARY.md`  
View EUFLE docs: `E:\EUFLE\README.md`  
WSL setup: `E:\EUFLE\docs\wsl_setup.md`
