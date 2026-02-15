# EUFLE Language Model Setup Guide

## Quick Start (Choose One)

### Option A: Ollama (Recommended - Fastest)

**1. Check if Ollama is installed:**
```powershell
ollama --version
```

**2. If installed, set environment variable:**
```powershell
# Temporary (this session only)
$env:EUFLE_DEFAULT_PROVIDER = "ollama"

# Permanent (all future sessions)
[Environment]::SetEnvironmentVariable("EUFLE_DEFAULT_PROVIDER", "ollama", "User")
```

**3. Start Ollama server (in separate terminal):**
```powershell
ollama serve
```

**4. Pull a model (if needed):**
```powershell
ollama pull mistral
```

**5. Test setup:**
```powershell
python verify_eufle_setup.py
```

**6. Run EUFLE:**
```powershell
python eufle.py --ask
```

---

### Option B: WSL + llama-cli (Advanced)

Requires WSL installed on Windows.

**1. Check WSL availability:**
```powershell
python E:\EUFLE\scripts\wsl_bridge.py check
```

**2. Build llama-cli in WSL:**
```powershell
wsl bash E:\EUFLE\scripts\setup_llamacpp.sh
```

**3. Set environment variables:**
```powershell
$env:EUFLE_DEFAULT_PROVIDER = "llamacpp"
$env:EUFLE_GGUF_MODEL = "$env:EUFLE_ROOT\EUFLE\hf-models\ministral-14b\consolidated.safetensors"
```

**4. Run EUFLE:**
```powershell
python eufle.py --ask
```

---

### Option C: Local HuggingFace Model (Already Setup)

Your `ministral-14b` model files are already in place at:
- `E:\EUFLE\hf-models\ministral-14b\`
- `tokenizer.json` ✓ (valid, 1.2M lines)
- `consolidated.safetensors` ✓ (present)
- `config.json` ✓ (present)

This works automatically without any special setup - it's the default fallback.

---

## Automated Setup Scripts

### PowerShell (Recommended)
```powershell
# Run with current session only
.\setup_ollama_eufle.ps1

# Or with permanent environment variables
.\setup_ollama_eufle.ps1 -Permanent

# Or with auto-start Ollama server
.\setup_ollama_eufle.ps1 -StartOllama
```

### Windows CMD
```cmd
setup_ollama_eufle.bat
```

### Verification
```powershell
python verify_eufle_setup.py
```

---

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `EUFLE_DEFAULT_PROVIDER` | Which backend to use | `ollama`, `llamacpp`, `auto` |
| `EUFLE_DEFAULT_MODEL` | Model identifier | `mistral:latest`, `ministral-14b` |
| `EUFLE_GGUF_MODEL` | Path to GGUF file | `E:\path\to\model.gguf` |
| `EUFLE_OLLAMA_MODEL` | Ollama model name | `mistral:latest` |

---

## Troubleshooting

### "Ollama not found"
1. Download from https://ollama.ai
2. Install and restart your terminal
3. Re-run setup script

### "Ollama server not responding"
1. Open new PowerShell window
2. Run: `ollama serve`
3. Keep this window open while using EUFLE

### "Model not found"
1. List available models: `ollama list`
2. Pull a model: `ollama pull mistral`
3. Or set default: `$env:EUFLE_DEFAULT_MODEL = "mistral:latest"`

### "Connection refused on localhost:11434"
- Make sure Ollama server is running: `ollama serve`
- Check firewall isn't blocking localhost

---

## File Locations

```
E:\EUFLE\
├── hf-models\ministral-14b\     ← HF model (always available)
├── models\                       ← GGUF models
├── scripts\
│   ├── wsl_bridge.py            ← WSL integration
│   └── setup_llamacpp.sh        ← llama-cli builder
├── studio\
│   └── unified_api.py           ← Provider selection logic
└── eufle.py                     ← Main CLI entry point
```

---

## Support

Check logs for detailed errors:
```powershell
Get-Content E:\EUFLE\logs\eufle_onboard_events.jsonl -Tail 20
```

For more info, see:
- `E:\EUFLE\README.md`
- `E:\EUFLE\docs\wsl_setup.md`
