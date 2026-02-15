# Network Security System

## 🔒 Overview

This is a comprehensive network access control and monitoring system that enforces strict security policies across the entire codebase. By default, **ALL network access is DENIED** until explicitly whitelisted.

## 🎯 Key Features

- **Default Deny Policy**: All network requests are blocked by default
- **Comprehensive Monitoring**: Logs and tracks all network access attempts
- **Data Leak Prevention**: Scans outbound requests for sensitive data patterns
- **Real-time Dashboard**: Monitor blocked/allowed requests in real-time
- **Whitelist Management**: Gradually add trusted domains after verification
- **Emergency Kill Switch**: Instantly block all network access
- **Multiple Protocol Support**: HTTP/HTTPS, WebSockets, Raw Sockets, Databases
- **Library Patching**: Automatically intercepts requests, httpx, aiohttp, urllib, socket

## 📁 File Structure

```
security/
├── README.md                          # This file
├── network_access_control.yaml        # Main configuration file
├── network_interceptor.py             # Core security enforcement
├── monitor_network.py                 # Monitoring dashboard CLI
├── __init__.py                        # Python module initialization
└── logs/                              # Security logs directory
    ├── network_access.log             # Network request log
    ├── audit.log                      # Audit trail (JSON format)
    ├── metrics.json                   # Performance metrics
    └── security_report_*.json         # Generated reports
```

## 🚀 Quick Start

### 1. Enable Security (Automatic)

Simply import the security module in your main application entry point:

```python
# In your main.py or __init__.py
import security

# Security is now active - all network requests are blocked by default
```

### 2. Check Status

```bash
# View security status
python -c "import security; security.print_status()"

# Or use the monitoring dashboard
python security/monitor_network.py dashboard
```

### 3. Monitor Network Access

```bash
# Real-time dashboard (requires 'rich' package)
python security/monitor_network.py dashboard

# View blocked requests
python security/monitor_network.py blocked

# View statistics
python security/monitor_network.py stats

# View data leak attempts
python security/monitor_network.py leaks
```

### 4. Whitelist Trusted Domains

After analyzing blocked requests, whitelist trusted domains:

```bash
# Add domain to whitelist
python security/monitor_network.py add api.trusted-service.com "Verified payment gateway"

# View current whitelist
python security/monitor_network.py whitelist

# Remove from whitelist
python security/monitor_network.py remove api.trusted-service.com
```

## ⚙️ Configuration

### Main Configuration File: `network_access_control.yaml`

```yaml
# Global settings
global:
  network_enabled: false              # Master switch
  logging:
    enabled: true
    log_level: "DEBUG"

# Default policy
default_policy: "deny"                # deny | allow

# Emergency controls
emergency:
  kill_switch: false                  # Emergency shutdown
  localhost_only: true                # Only allow localhost

# Data leak prevention
data_leak_prevention:
  enabled: true
  scan_requests: true
  sensitive_patterns:
    - pattern: "api[_-]?key"
      action: "block"
    - pattern: "password"
      action: "block"
```

### Key Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `global.network_enabled` | Master network switch | `false` |
| `default_policy` | Allow or deny by default | `deny` |
| `emergency.kill_switch` | Emergency network shutdown | `false` |
| `emergency.localhost_only` | Only allow localhost connections | `true` |
| `data_leak_prevention.enabled` | Enable DLP scanning | `true` |

## 📊 Monitoring Commands

### Dashboard

```bash
python security/monitor_network.py dashboard
```

Shows:
- Total requests (allowed/blocked)
- Data leak detection count
- Recent blocked requests
- Top blocked domains and callers
- Current configuration

### View Blocked Requests

```bash
python security/monitor_network.py blocked
```

### View Allowed Requests

```bash
python security/monitor_network.py allowed
```

### Statistics

```bash
python security/monitor_network.py stats
```

### Whitelist Management

```bash
# Show whitelist
python security/monitor_network.py whitelist

# Add domain
python security/monitor_network.py add example.com "Verified service"

# Remove domain
python security/monitor_network.py remove example.com
```

### Network Control

```bash
# Enable global network access (still respects whitelist)
python security/monitor_network.py enable

# Disable all network access
python security/monitor_network.py disable

# Activate emergency kill switch
python security/monitor_network.py killswitch on

# Deactivate kill switch
python security/monitor_network.py killswitch off
```

## 🔌 Programmatic API

### Python API

```python
import security

# Check current status
status = security.get_status()
print(f"Network enabled: {status['network_enabled']}")
print(f"Blocked: {status['metrics']['blocked_requests']}")

# Enable/disable network
security.enable_network()
security.disable_network()

# Emergency controls
security.activate_kill_switch()
security.deactivate_kill_switch()

# Whitelist management
security.whitelist_domain("api.example.com", "Verified API")

# Get request logs
blocked = security.get_blocked_requests(limit=50)
allowed = security.get_allowed_requests(limit=50)

# Generate security report
report_path = security.generate_security_report()
```

### Access Control in Code

```python
from security import enforce_network_policy, NetworkAccessDenied

@enforce_network_policy
def make_api_call(url):
    """This function is protected by security policy."""
    import requests
    return requests.get(url)

try:
    response = make_api_call("https://api.example.com")
except NetworkAccessDenied as e:
    print(f"Access denied: {e}")
```

## 🚨 Data Leak Prevention

The system automatically scans all outbound requests for sensitive data:

### Detected Patterns

- API keys (`api_key`, `apikey`, etc.)
- Passwords
- Secrets and tokens
- Bearer tokens
- Credit card numbers (16 digits)
- SSN patterns
- Authentication headers

### File Extensions Blocked

- `.env` files
- `.key`, `.pem`, `.p12`, `.pfx` (certificates)
- `.crt`, `.csr` (certificate files)

### Response to Data Leaks

When a potential data leak is detected:
1. Request is immediately blocked
2. Critical alert is logged
3. Entry added to audit log
4. Data leak counter incremented

View detected leaks:

```bash
python security/monitor_network.py leaks
```

## 📋 Workflow: Adding Trusted Clients

### Step 1: Run Your Application

```bash
# Start your application with security enabled
python main.py
```

All network requests will be blocked and logged.

### Step 2: Monitor Blocked Requests

```bash
python security/monitor_network.py dashboard
```

Review blocked requests and identify legitimate services.

### Step 3: Analyze and Verify

For each blocked domain:
1. Verify the domain is legitimate
2. Check what data is being sent
3. Ensure it's necessary for functionality
4. Review the calling code

### Step 4: Whitelist Trusted Domains

```bash
# After verification, whitelist the domain
python security/monitor_network.py add api.stripe.com "Payment processing"
python security/monitor_network.py add api.github.com "Repository access"
```

### Step 5: Enable Network (Optional)

If you've whitelisted your trusted services:

```bash
python security/monitor_network.py enable
```

This enables network but still enforces the whitelist.

### Step 6: Continuous Monitoring

```bash
# Regularly check for new blocked requests
python security/monitor_network.py blocked

# Review statistics
python security/monitor_network.py stats

# Generate periodic reports
python -c "import security; security.generate_security_report()"
```

## 🛡️ Security Modes

### Strict Mode (Default)

```yaml
mode: "strict"
default_policy: "deny"
global:
  network_enabled: false
emergency:
  localhost_only: true
```

- Everything blocked by default
- Only whitelisted domains allowed
- Localhost connections only (initially)
- Data leak prevention active

### Audit Mode

```yaml
mode: "audit"
default_policy: "allow"
global:
  network_enabled: true
```

- Requests allowed but logged
- Use for transition period
- Identifies all network dependencies
- Still blocks data leaks

### Permissive Mode

```yaml
mode: "permissive"
default_policy: "allow"
data_leak_prevention:
  enabled: false
```

- Most permissive mode
- Only blocks known malicious domains
- Reduced data leak prevention

## 🔧 Integration with Existing Code

### Option 1: Global Import (Recommended)

Add to your main entry point:

```python
# main.py or __init__.py
import security  # Apply security patches globally
```

### Option 2: Selective Protection

Protect specific functions:

```python
from security import enforce_network_policy

@enforce_network_policy
def fetch_user_data(user_id):
    # Network access controlled here
    pass
```

### Option 3: Manual Control

```python
from security import nac, NetworkAccessDenied

def make_request(url):
    allowed, reason = nac.check_request(url, method="GET")
    if not allowed:
        raise NetworkAccessDenied(reason)
    
    # Proceed with request
    import requests
    return requests.get(url)
```

## 🚨 Emergency Procedures

### Complete Network Lockdown

```bash
# Activate kill switch
python security/monitor_network.py killswitch on
```

Or programmatically:

```python
import security
security.activate_kill_switch()
```

### Suspected Data Breach

1. Activate kill switch immediately
2. Review data leak logs
3. Check audit trail
4. Generate security report

```bash
python security/monitor_network.py killswitch on
python security/monitor_network.py leaks
python -c "import security; security.generate_security_report()"
```

### Disable Security (Testing Only)

```bash
# Temporarily disable (NOT for production)
export DISABLE_NETWORK_SECURITY=true
python main.py
```

Or in code:

```python
import os
os.environ['DISABLE_NETWORK_SECURITY'] = 'true'
import security  # Security will be disabled
```

## 📈 Performance Impact

- **Overhead**: ~1-5ms per request (negligible)
- **Memory**: ~10-50MB (depends on log size)
- **CPU**: Minimal (regex pattern matching)

### Optimization Tips

1. Regularly rotate logs (clear old entries)
2. Limit audit log retention
3. Use whitelist to reduce checks
4. Disable verbose logging in production

## 🔍 Troubleshooting

### Issue: All requests blocked unexpectedly

**Solution**: Check configuration:

```bash
python -c "import security; security.print_status()"
```

Ensure `network_enabled: true` if you want to allow whitelisted domains.

### Issue: Legitimate service blocked

**Solution**: Add to whitelist:

```bash
python security/monitor_network.py add <domain> "Description"
```

### Issue: Cannot import security module

**Solution**: Install dependencies:

```bash
pip install pyyaml rich
```

### Issue: Logs growing too large

**Solution**: Rotate logs:

```bash
# Archive old logs
cd security/logs
tar -czf archive_$(date +%Y%m%d).tar.gz *.log
rm *.log
```

### Issue: False positive data leak detection

**Solution**: Adjust patterns in `network_access_control.yaml`:

```yaml
data_leak_prevention:
  sensitive_patterns:
    # Comment out overly aggressive patterns
    # - pattern: "token"
```

## 📚 Examples

### Example 1: Coinbase API Integration

```python
# 1. Start with security enabled
import security

# 2. Try to use Coinbase API - will be blocked
from coinbase.features.fact_check import FactChecker
checker = FactChecker()
# NetworkAccessDenied: api.coinbase.com blocked

# 3. Check what was blocked
python security/monitor_network.py blocked
# Shows: api.coinbase.com, api.coingecko.com, api.binance.com

# 4. Verify and whitelist
python security/monitor_network.py add api.coinbase.com "Official Coinbase API"
python security/monitor_network.py add api.coingecko.com "Price data"

# 5. Enable network
python security/monitor_network.py enable

# 6. Now API calls work
checker.verify_price("BTC", 50000)  # ✅ Works
```

### Example 2: WebSocket Monitoring

```python
import security
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # WebSocket connections are monitored
    await websocket.accept()
    # Security logs the connection
    
# Configure WebSocket policy
# Edit network_access_control.yaml:
# websockets:
#   inbound:
#     enabled: true
#     allowed_origins: ["https://trusted-frontend.com"]
```

### Example 3: Database Connection Security

```python
import security

# Database connections are also controlled
from sqlalchemy import create_engine

# Blocked by default
# engine = create_engine("postgresql://localhost/db")

# Whitelist database host
security.whitelist_domain("localhost:5432", "Local PostgreSQL")

# Or in config:
# databases:
#   postgresql:
#     enabled: true
#     allowed_hosts: ["localhost", "db.production.com"]
```

## 🤝 Contributing

To add support for new libraries:

1. Add patch function in `network_interceptor.py`
2. Follow existing pattern (save original, wrap with decorator)
3. Call patch function in `apply_all_patches()`
4. Update configuration YAML with new section
5. Test thoroughly

## 📄 License

This security system is part of the GRID project.

## 🆘 Support

For issues or questions:
1. Check logs: `security/logs/network_access.log`
2. Review configuration: `security/network_access_control.yaml`
3. Generate report: `python -c "import security; security.generate_security_report()"`

---

**Remember**: Security is not a one-time setup. Continuously monitor, analyze, and adjust your policies based on observed behavior.