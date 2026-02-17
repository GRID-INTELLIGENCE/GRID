# AI Safety Deployment Guide

## Deploying Server Denylist to Wellness Studio

This guide walks through deploying the Server Denylist System as an AI Safety seed component in the wellness_studio framework.

## Prerequisites

- Python 3.8+
- Access to `E:\wellness_studio\` directory
- Server Denylist System installed (from implementation)

## Deployment Steps

### Step 1: Initialize Wellness Studio AI Safety Structure

```bash
# Create AI safety directory structure
python scripts/init_safety_logging.py --target E:\wellness_studio\ai_safety\config_sanitization
```

This creates:
```
E:\wellness_studio\
└── ai_safety/
    └── config_sanitization/
        ├── logs/
        │   ├── enforcement/
        │   ├── violation/
        │   ├── safety_metrics/
        │   └── audit/
        └── monitoring/
```

### Step 2: Copy Denylist System Files

```bash
# Create denylist engine directory
mkdir E:\wellness_studio\ai_safety\config_sanitization\denylist_engine

# Copy configuration files
copy config\server_denylist_schema.json E:\wellness_studio\ai_safety\config_sanitization\denylist_engine\
copy config\server_denylist.json E:\wellness_studio\ai_safety\config_sanitization\denylist_engine\

# Copy scripts
copy scripts\server_denylist_manager.py E:\wellness_studio\ai_safety\config_sanitization\denylist_engine\
copy scripts\safety_aware_server_manager.py E:\wellness_studio\ai_safety\config_sanitization\denylist_engine\
copy scripts\apply_denylist_drive_wide.py E:\wellness_studio\ai_safety\config_sanitization\denylist_engine\
copy scripts\init_safety_logging.py E:\wellness_studio\ai_safety\config_sanitization\denylist_engine\

# Copy documentation
copy docs\AI_SAFETY_INTEGRATION.md E:\wellness_studio\ai_safety\config_sanitization\
copy docs\DENYLIST_QUICK_REFERENCE.md E:\wellness_studio\ai_safety\config_sanitization\
```

### Step 3: Configure Safety Logging

```bash
# Test safety logging
cd E:\wellness_studio\ai_safety\config_sanitization\denylist_engine

python safety_aware_server_manager.py \
  --config server_denylist.json \
  --safety-logs ../logs \
  --report
```

### Step 4: Generate Initial Safety Report

```bash
# Generate comprehensive safety report
python safety_aware_server_manager.py \
  --config server_denylist.json \
  --safety-logs ../logs \
  --report \
  --detect-violations \
  --save-metrics > safety_report_initial.txt
```

### Step 5: Apply to MCP Configurations

```bash
# Dry run first
python apply_denylist_drive_wide.py \
  --config server_denylist.json \
  --root E:\ \
  --dry-run

# Apply live
python apply_denylist_drive_wide.py \
  --config server_denylist.json \
  --root E:\
```

### Step 6: Set Up Monitoring

Create monitoring script at `E:\wellness_studio\ai_safety\config_sanitization\monitoring\monitor_safety.py`:

```python
#!/usr/bin/env python3
"""Continuous safety monitoring for server denylist"""

import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "denylist_engine"))

from safety_aware_server_manager import SafetyAwareServerManager

def monitor_loop(interval_seconds=300):
    """Monitor safety continuously"""
    
    manager = SafetyAwareServerManager(
        config_path="../denylist_engine/server_denylist.json",
        safety_log_dir="../logs"
    )
    
    print(f"Started safety monitoring (interval: {interval_seconds}s)")
    
    while True:
        try:
            print(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] Running safety check...")
            
            # Detect violations
            violations = manager.detect_violations()
            
            if violations:
                print(f"⚠ WARNING: {len(violations)} violations detected")
                for v in violations:
                    if v['severity'] == 'critical':
                        print(f"  CRITICAL: {v['server']} - {v['violation_type']}")
            else:
                print("✓ No violations detected")
            
            # Save metrics
            metrics = manager.save_safety_metrics()
            if metrics:
                print(f"  Denial rate: {metrics['denial_rate']:.1%}")
                print(f"  High risk count: {metrics['high_risk_count']}")
            
            time.sleep(interval_seconds)
            
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
            break
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            time.sleep(60)  # Wait before retry

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=300, 
                       help='Monitoring interval in seconds')
    args = parser.parse_args()
    
    monitor_loop(args.interval)
```

Run monitoring:
```bash
python monitoring\monitor_safety.py --interval 60
```

## Verification

### Check Installation

```bash
# Verify directory structure
tree E:\wellness_studio\ai_safety\config_sanitization

# Verify logs are being generated
dir E:\wellness_studio\ai_safety\config_sanitization\logs\enforcement

# Check metrics
type E:\wellness_studio\ai_safety\config_sanitization\logs\safety_metrics\*.json
```

### Test Safety Features

```bash
# Test server check with safety scoring
python denylist_engine\safety_aware_server_manager.py \
  --config denylist_engine\server_denylist.json \
  --safety-logs logs \
  --check grid-rag

# Test violation detection
python denylist_engine\safety_aware_server_manager.py \
  --config denylist_engine\server_denylist.json \
  --safety-logs logs \
  --detect-violations

# Generate full safety report
python denylist_engine\safety_aware_server_manager.py \
  --config denylist_engine\server_denylist.json \
  --safety-logs logs \
  --report
```

## Integration with Existing Systems

### Connect to GRID AI Safety Tracer

```python
# In your GRID application
from wellness_studio.ai_safety.config_sanitization.denylist_engine.safety_aware_server_manager import SafetyAwareServerManager

# Initialize with safety logging
manager = SafetyAwareServerManager(
    config_path="E:/wellness_studio/ai_safety/config_sanitization/denylist_engine/server_denylist.json",
    safety_log_dir="E:/wellness_studio/ai_safety/config_sanitization/logs"
)

# Use in your code
is_denied, reason = manager.is_denied('server-name')
```

### Add to CI/CD Pipeline

```yaml
# .github/workflows/safety_check.yml
name: AI Safety Check

on: [push, pull_request]

jobs:
  safety_check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Run Safety Checks
        run: |
          python wellness_studio/ai_safety/config_sanitization/denylist_engine/safety_aware_server_manager.py \
            --config wellness_studio/ai_safety/config_sanitization/denylist_engine/server_denylist.json \
            --detect-violations
      
      - name: Upload Safety Report
        uses: actions/upload-artifact@v2
        with:
          name: safety-report
          path: safety_report_*.txt
```

## Maintenance

### Daily Tasks
- Review violation logs
- Check safety metrics
- Monitor denial rates

### Weekly Tasks
- Analyze trends in safety scores
- Review false positives/negatives
- Update denylist rules as needed

### Monthly Tasks
- Comprehensive safety audit
- Rule optimization
- Documentation updates

### Quarterly Tasks
- System-wide safety assessment
- Compliance review
- Architecture review

## Troubleshooting

### Logs Not Being Generated
```bash
# Check permissions
icacls E:\wellness_studio\ai_safety\config_sanitization\logs

# Verify safety logger initialization
python -c "from init_safety_logging import init_safety_logging; init_safety_logging('E:/wellness_studio/ai_safety/config_sanitization')"
```

### High False Positive Rate
- Adjust rule thresholds in `server_denylist.json`
- Review `matchAttributes` criteria
- Analyze safety score calculations

### Performance Issues
- Reduce monitoring frequency
- Optimize rule evaluation
- Enable caching in manager

## Next Steps

1. ✅ Deploy to wellness_studio
2. ⏳ Configure monitoring dashboard
3. ⏳ Set up alerting system
4. ⏳ Integrate with SIEM
5. ⏳ Train team on safety workflows
6. ⏳ Establish review cadence
7. ⏳ Document incident response procedures

## Support

For issues or questions:
- Review `AI_SAFETY_INTEGRATION.md`
- Check `DENYLIST_QUICK_REFERENCE.md`
- Consult safety logs in `logs/audit/`

---

**Status**: Deployment Ready  
**Target**: E:\wellness_studio\ai_safety\config_sanitization  
**Priority**: Critical - AI Safety
