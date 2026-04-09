# Windows Security Hardening for Development Environment

**Status**: Ready to Apply
**Date**: [Date]
**Scope**: Local development security (Python, IDEs, local LLMs, local APIs)

---

## Overview

This security hardening package applies **targeted, persistent firewall rules** to:

✅ **Enable** development workflows on trusted (Private/Domain) networks
🔒 **Disable** development workflows on untrusted (Public) networks
🔐 **Isolate** local services (LLMs, APIs, databases) to localhost only

**Goal**: One-time configuration that provides persistent security with minimal ongoing effort.

---

## Quick Start (3 Steps)

### Step 1: Open PowerShell as Administrator

```powershell
# Right-click PowerShell icon → Run as administrator
# Or: Win+X, A
```

### Step 2: Run Hardening Script

```powershell
cd [path]\security-hardening
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
.\Apply-Security-Hardening.ps1
```

### Step 3: Verify It Worked

```powershell
.\Verify-Security-Hardening.ps1
```

✅ **Done!** Your development environment is now hardened.

---

## What Gets Configured

### Tier 1: Development Tools (Local Network Only)

- **Python.exe** - Allowed on Private/Domain profiles, blocked on Public
- **VS Code** - Allowed on Private/Domain profiles, blocked on Public
- **[IDE]** - Allowed on Private/Domain profiles, blocked on Public

### Tier 2: Local Services (Localhost Only - Absolute Isolation)

- **Local LLM (port [port])** - Embeddings and local model access
- **Development API (ports [port-range])** - FastAPI, Flask, etc.
- **RAG/Database (ports [port-range])** - ChromaDB, local data services

### Tier 3: Administrative Isolation (Block on Public)

- Python blocked from listening on Public networks
- VS Code blocked from listening on Public networks
- [IDE] blocked from listening on Public networks
- All dev ports blocked on Public networks

### Tier 4: Audit & Logging

- Firewall logging enabled for all profiles
- Log location: `[log-path]\pfirewall.log`

---

## File Structure

```
security-hardening/
├── README.md                          ← You are here
├── QUICK_REFERENCE.md                 ← Daily usage guide
├── WINDOWS_SECURITY_AUDIT.md          ← Full audit details
├── TROUBLESHOOTING.md                 ← Problem solving
├── Apply-Security-Hardening.ps1       ← Main installation script
└── Verify-Security-Hardening.ps1      ← Verification script
```

---

## Documentation Map

| Need                        | Go To                                        |
| --------------------------- | -------------------------------------------- |
| **First time setup**        | Start here (README.md) then run scripts      |
| **Daily usage guide**       | `QUICK_REFERENCE.md`                         |
| **Understand architecture** | `SECURITY_AUDIT.md` (detailed audit) |
| **Something not working**   | `TROUBLESHOOTING.md`                         |
| **Common commands**         | `QUICK_REFERENCE.md` → "Common Commands"     |
| **Roll back changes**       | `QUICK_REFERENCE.md` → "Rollback"            |

---

## Security Policy Summary

### On Private/Domain Networks (Home/Office/Trusted VPN)

```
✅ Python can connect and listen locally
✅ VS Code can debug and use extensions
✅ [IDE] AI assistant can operate
✅ Local LLM available at localhost:[port]
✅ API servers on localhost:[port-range] work
✅ Full development productivity
```

### On Public Networks (Coffee Shop/Airport/Untrusted WiFi)

```
🚫 Python cannot listen on network (blocked)
🚫 VS Code cannot listen on network (blocked)
🚫 [IDE] cannot listen on network (blocked)
🚫 Dev ports not accessible (blocked)
✅ Web browsing still works
✅ Maximum security
```

---

## Why This Approach?

### Problem Your Current Setup Has

- Python.exe globally blocked (even on localhost)
- VS Code blocked everywhere
- [IDE] blocked everywhere
- Local LLM has no firewall rule
- Local APIs have no firewall rule
- Dev environment non-functional

### Solution This Provides

- **Network-aware**: Separate rules for trusted vs. untrusted networks
- **Service-aware**: Localhost-only services absolutely cannot expose externally
- **Tool-aware**: Development tools work locally, blocked publicly
- **Persistent**: Rules survive reboot and system updates
- **Reversible**: Can rollback in seconds if needed
- **Auditable**: All changes logged and documented

---

## Architecture Diagram

```
╔════════════════════════════════════════════════════════════╗
║            Development Environment                         ║
╠════════════════════════════════════════════════════════════╣
║                 Firewall Configuration                     ║
║  ┌──────────────────────────────────────────────────────┐  ║
║  │         Private/Domain Network Profile              │  ║
║  │  ✅ Python (LocalSubnet)                            │  ║
║  │  ✅ VS Code (LocalSubnet)                           │  ║
║  │  ✅ [IDE] (LocalSubnet)                             │  ║
║  │  ✅ Development API (localhost:[port-range])         │  ║
║  │  ✅ Local LLM (localhost:[port])                    │  ║
║  │  ✅ RAG Services (localhost:[port-range])            │  ║
║  └──────────────────────────────────────────────────────┘  ║
║                             ▲                               ║
║                    (when connected to                       ║
║                     home/office/VPN)                        ║
║                                                              ║
║  ┌──────────────────────────────────────────────────────┐  ║
║  │            Public Network Profile                   │  ║
║  │  🚫 Python (BLOCKED)                                │  ║
║  │  🚫 VS Code (BLOCKED)                               │  ║
║  │  🚫 [IDE] (BLOCKED)                                 │  ║
║  │  🚫 Development Ports (BLOCKED)                     │  ║
║  │  ✅ Web Browsing (ALLOWED)                          │  ║
║  └──────────────────────────────────────────────────────┘  ║
║                             ▲                               ║
║                    (when connected to                       ║
║                  coffee shop/airport WiFi)                  ║
╚════════════════════════════════════════════════════════════╝

           Localhost Isolation (All Profiles)
           ════════════════════════════════
    🔐 127.0.0.1 & ::1 ONLY - Zero Internet Exposure
    ✅ Local LLM ([port])
    ✅ Development API ([port-range])
    ✅ RAG/Database ([port-range])
```

---

## Before You Apply

### Checklist

- [ ] You have Administrator privileges
- [ ] You're on Windows 10/11
- [ ] PowerShell 5.1+ is installed
- [ ] You have a backup of important files (recommended)
- [ ] You understand this creates persistent firewall rules

### What This WON'T Do

- ❌ Change Windows Defender antivirus settings
- ❌ Modify VPN configuration
- ❌ Change password policies
- ❌ Install new software
- ❌ Modify system files outside firewall

### What This WILL Do

- ✅ Add 10 firewall rules
- ✅ Enable firewall logging
- ✅ Create persistent rule backups
- ✅ Allow development tools to function on trusted networks
- ✅ Block development tools on untrusted networks

---

## After Application

### Verify Everything Works

```powershell
# Run verification
.\Verify-Security-Hardening.ps1

# You should see: ✓ All checks passed!
```

### Test Your Workflow

1. **Start VS Code** - Should work normally
2. **Run Python scripts** - Should work normally
3. **Start [IDE]** - Should work normally
4. **Start Local LLM** - Should listen on localhost:[port]
5. **Start API server** - Should listen on localhost:[port-range]

### Optional: Test on Public Network

1. Switch to Public network profile: `Set-NetConnectionProfile -Name "Network" -NetworkCategory Public`
2. Try to run Python → Should fail (expected)
3. Try to start VS Code → Should fail (expected)
4. Switch back to Private: `Set-NetConnectionProfile -Name "Network" -NetworkCategory Private`

---

## Common Questions

**Q: Do I need to run this again?**
A: No. Rules are persistent. They survive reboots and Windows updates.

**Q: Can I undo this?**
A: Yes. Run: `.\Apply-Security-Hardening.ps1 -Rollback`

**Q: What if I need to work on a Public network?**
A: Use a VPN to connect back to a trusted network, or temporarily disable rules (see Troubleshooting).

**Q: Will this affect web browsing?**
A: No. Web browsing is unaffected by these rules.

**Q: What about other applications?**
A: These rules only affect Python, VS Code, [IDE], and local service ports. Other apps are unchanged.

**Q: Is this secure?**
A: Yes. This hardening actually makes your system MORE secure by:

- Preventing accidental exposure on public networks
- Isolating local services to localhost only
- Enabling security audit logging
- Using whitelist approach (explicit allow, not implicit)

---

## Troubleshooting

### Issue: Script Won't Run

```powershell
# Fix: Allow scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Then retry:
.\Apply-Security-Hardening.ps1
```

### Issue: Tools Still Don't Work

```powershell
# Run verification to diagnose:
.\Verify-Security-Hardening.ps1

# See detailed help:
cat .\TROUBLESHOOTING.md
```

### Issue: Need to Rollback

```powershell
.\Apply-Security-Hardening.ps1 -Rollback
```

**For detailed troubleshooting**: See `TROUBLESHOOTING.md`

---

## Support Resources

- 📖 **Full Audit Details**: `WINDOWS_SECURITY_AUDIT.md`
- 🔧 **Common Commands**: `QUICK_REFERENCE.md`
- 🐛 **Problem Solving**: `TROUBLESHOOTING.md`
- 📋 **Daily Reference**: `QUICK_REFERENCE.md`

---

## Next Steps

1. ✅ **Read this README** (you are here)
2. 🚀 **Run the installation script** - `.\Apply-Security-Hardening.ps1`
3. ✔️ **Verify it worked** - `.\Verify-Security-Hardening.ps1`
4. 📚 **Bookmark QUICK_REFERENCE.md** for daily usage
5. 🔒 **You're done!** Your environment is now hardened

---

## Version History

| Version | Date         | Changes                   |
| ------- | ------------ | ------------------------- |
| 1.0     | Jan 26, 2026 | Initial hardening package |

---

## License & Usage

This security hardening package is provided as-is for development environment protection. Use as-is or modify for your security requirements.

---

<!-- Sanitized via Mufliato | mode=veil | audience=user | source_hash=hardening-v1-2026 | date=2026-04-09 -->

## Appendix: Hardening Script Template

```powershell
# Template configuration for security hardening
# Copy and adapt to your environment

param(
    [switch]$Rollback
)

# Configuration - adjust for your environment
$Config = @{
    DevTools = @(
        @{ Name = "Python"; Path = "python.exe"; Action = "AllowLocalSubnet" }
        @{ Name = "VSCode"; Path = "Code.exe"; Action = "AllowLocalSubnet" }
        # Add your tools here
    )
    LocalServices = @(
        @{ Name = "API"; Port = "[port-range]"; Action = "LocalhostOnly" }
        @{ Name = "Database"; Port = "[port-range]"; Action = "LocalhostOnly" }
        # Add your services here
    )
}

# Implementation follows standard firewall rule creation pattern
```

> **Note**: This is a template configuration. Replace `[port-range]` and other placeholders with your actual service ports during deployment.

---

## Questions?

Check these in order:

1. `QUICK_REFERENCE.md` - Common commands and FAQ
2. `TROUBLESHOOTING.md` - Detailed problem solving
3. `WINDOWS_SECURITY_AUDIT.md` - Full technical details
