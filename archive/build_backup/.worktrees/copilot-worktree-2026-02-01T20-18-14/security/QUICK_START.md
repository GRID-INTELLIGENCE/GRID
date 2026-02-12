# 🚀 Network Security System - QUICK START GUIDE

## ⚡ 5-Minute Setup

### Step 1: Install (30 seconds)

**Windows:**
```powershell
cd E:\
.\security\install.ps1
```

**Linux/Mac:**
```bash
cd /path/to/project
bash security/install.sh
```

**Manual:**
```bash
pip install pyyaml rich
```

---

### Step 2: Add Security to Your Code (1 minute)

Add this ONE line to your main application file:

```python
# At the top of your main.py, app.py, or __init__.py
import security

# That's it! All network access is now monitored and blocked by default
```

---

### Step 3: Run Your Application (30 seconds)

```bash
python main.py
# or
python your_application.py
```

**Expected Result**: Network requests will be BLOCKED and logged.

---

### Step 4: Monitor What's Blocked (2 minutes)

Open a **new terminal** and run:

```bash
python security/monitor_network.py dashboard
```

Or view blocked requests:

```bash
python security/monitor_network.py blocked
```

---

### Step 5: Whitelist Trusted Services (1 minute)

After reviewing blocked requests:

```bash
# Add trusted domain
python security/monitor_network.py add api.example.com "Description of why this is trusted"

# Enable network access for whitelisted domains
python security/monitor_network.py enable
```

---

## 🎯 Common Commands

```bash
# View real-time dashboard
python security/monitor_network.py dashboard

# See what's been blocked
python security/monitor_network.py blocked

# View statistics
python security/monitor_network.py stats

# Check for data leaks
python security/monitor_network.py leaks

# Show current whitelist
python security/monitor_network.py whitelist

# Add domain to whitelist
python security/monitor_network.py add <domain> "reason"

# Remove from whitelist
python security/monitor_network.py remove <domain>

# Enable network (respects whitelist)
python security/monitor_network.py enable

# Disable all network
python security/monitor_network.py disable

# Emergency shutdown
python security/monitor_network.py killswitch on
```

---

## 📋 Typical First-Day Workflow

### Morning: Setup
1. Run installation script
2. Add `import security` to your main file
3. Start your application

### During the Day: Monitor
4. Open monitoring dashboard (separate terminal)
5. Exercise all features of your application
6. Observe what gets blocked

### Evening: Analysis
7. Review blocked requests: `python security/monitor_network.py blocked`
8. For each blocked domain:
   - Verify it's legitimate
   - Check what data is being sent
   - Review the calling code
   - Decide if it's necessary

### End of Day: Whitelist
9. Add trusted domains:
   ```bash
   python security/monitor_network.py add api.stripe.com "Payment processing"
   python security/monitor_network.py add api.github.com "Repository access"
   ```
10. Enable network: `python security/monitor_network.py enable`
11. Test that everything works

---

## 🚨 Important Notes

### ⚠️ What to Expect:
- **ALL network requests are BLOCKED by default**
- This is INTENTIONAL for security
- You must manually whitelist each trusted service
- Data leak prevention is ACTIVE

### ✅ This is Normal:
- Seeing "NetworkAccessDenied" errors initially
- Many blocked requests on first run
- Need to whitelist localhost (if needed)

### ❌ Don't Do This:
- Don't whitelist domains without verification
- Don't disable security in production
- Don't ignore data leak alerts
- Don't skip the monitoring dashboard

---

## 🔍 What Gets Blocked?

Everything! Including:
- ✅ HTTP/HTTPS requests (requests, httpx, aiohttp, urllib)
- ✅ WebSocket connections
- ✅ Raw socket connections
- ✅ Database connections
- ✅ DNS queries

---

## 📊 Example Session

```bash
# Terminal 1: Run your app
$ python main.py
[ERROR] NetworkAccessDenied: api.coinbase.com blocked

# Terminal 2: Check what was blocked
$ python security/monitor_network.py blocked
[2024-01-15 10:30:45] GET api.coinbase.com
  Reason: Not in whitelist

# Verify it's legitimate, then whitelist
$ python security/monitor_network.py add api.coinbase.com "Official Coinbase API - verified"
✅ Added api.coinbase.com to whitelist

# Enable network
$ python security/monitor_network.py enable
✅ Global network access ENABLED

# Back to Terminal 1 - try again
$ python main.py
[SUCCESS] Connected to api.coinbase.com ✅
```

---

## 🔧 Configuration File Location

```
E:\security\network_access_control.yaml
```

### Quick Settings:

```yaml
global:
  network_enabled: false    # Change to true after whitelisting

emergency:
  kill_switch: false        # Set to true for instant lockdown
  localhost_only: true      # Initially only allow localhost

default_policy: "deny"      # Keep as "deny" for security
```

---

## 💡 Pro Tips

### Tip 1: Use localhost for Testing
If you need to allow localhost during development:
```yaml
whitelist:
  rules:
    - domain: "localhost"
      description: "Local development"
    - domain: "127.0.0.1"
      description: "Local development"
```

### Tip 2: Watch the Dashboard Live
Keep the dashboard open while developing:
```bash
python security/monitor_network.py dashboard
```
Refresh automatically shows new blocked requests.

### Tip 3: Export Reports
Generate periodic security reports:
```python
import security
report = security.generate_security_report()
print(f"Report saved: {report}")
```

### Tip 4: Programmatic Control
Control security from Python:
```python
import security

# Check status
status = security.get_status()
print(f"Blocked: {status['metrics']['blocked_requests']}")

# Whitelist domain
security.whitelist_domain("api.example.com", "Verified service")

# Emergency lockdown
security.activate_kill_switch()
```

---

## 🆘 Troubleshooting

### Problem: "Cannot import security module"
**Solution:**
```bash
pip install pyyaml rich
```

### Problem: "Everything is blocked!"
**Solution:** This is correct! Review and whitelist:
```bash
python security/monitor_network.py blocked
python security/monitor_network.py add <domain>
```

### Problem: "Legitimate service keeps blocking"
**Solution:** Add to whitelist AND enable network:
```bash
python security/monitor_network.py add <domain> "reason"
python security/monitor_network.py enable
```

### Problem: "Too many false data leak alerts"
**Solution:** Edit `security/network_access_control.yaml`:
```yaml
data_leak_prevention:
  sensitive_patterns:
    # Comment out patterns causing false positives
```

---

## 📚 Full Documentation

For complete documentation, see:
- **Full Guide**: `security/README.md`
- **Implementation Summary**: `SECURITY_IMPLEMENTATION_SUMMARY.md`
- **Configuration**: `security/network_access_control.yaml`

---

## 🎯 Success Checklist

After your first day, you should have:
- [ ] Security system installed
- [ ] `import security` added to main file
- [ ] Application tested (some things blocked - that's good!)
- [ ] Monitoring dashboard viewed
- [ ] Blocked requests reviewed
- [ ] 3-5 trusted domains whitelisted
- [ ] Network enabled for whitelisted domains
- [ ] Application fully functional with security active

---

## 🔒 Security Status

Current configuration:
- ✅ **Default Policy**: DENY ALL
- ✅ **Network Enabled**: FALSE (nothing gets through)
- ✅ **Data Leak Prevention**: ACTIVE
- ✅ **Audit Logging**: ENABLED
- ✅ **Kill Switch**: READY

**You are protected by default. Gradually whitelist as needed.**

---

## 📞 Need Help?

1. Check logs: `security/logs/network_access.log`
2. View audit trail: `security/logs/audit.log`
3. Read full docs: `security/README.md`
4. Generate report: `python -c "import security; security.generate_security_report()"`

---

**Remember: If something is blocked, that means the security system is working! Review, verify, then whitelist.**

**Good luck! 🚀🔒**
