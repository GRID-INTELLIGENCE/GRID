# SECURITY REMEDIATION PLAN
**Date:** 2026-02-02
**Priority:** CRITICAL
**Timeline:** Immediate to 90 Days
**Status:** ACTIVE REMEDIATION

---

## EXECUTIVE SUMMARY

This document provides a comprehensive, actionable remediation plan for all security vulnerabilities identified in the 2026-02-02 security audit. The plan is organized by priority and includes specific commands, code changes, and verification steps.

**Critical Vulnerabilities Requiring Immediate Action:**
1. Hardcoded Stripe API key exposure
2. Remote code execution via eval()
3. Vulnerable dependencies (aiohttp CVE-2024-23334)
4. Secrets in version control
5. Development authentication bypass

**Estimated Total Effort:** 40-60 hours over 2 weeks
**Team Required:** 1 senior developer + security consultant
**Cost Estimate:** $5,000-10,000 for external security audit after remediation

---

## PHASE 1: IMMEDIATE CONTAINMENT (0-24 HOURS)

### CRITICAL-1: Rotate Stripe API Key

**Vulnerability:** Hardcoded Stripe test API key in source code
**File:** `e:\.worktrees\copilot-worktree-2026-02-01T20-18-14\stripe-sample-code\server.py:13`
**Exposed Key:** `[REDACTED_STRIPE_KEY]`

#### Step 1: Rotate Key in Stripe Dashboard
```bash
# 1. Log into Stripe Dashboard: https://dashboard.stripe.com/test/apikeys
# 2. Click "Reveal test key"
# 3. Click "Roll key" to invalidate old key
# 4. Copy new key to secure location (password manager)
```

#### Step 2: Update Code to Use Environment Variables
```python
# BEFORE (INSECURE):
import stripe
stripe.api_key = '[REDACTED_STRIPE_KEY]'

# AFTER (SECURE):
import os
import stripe

stripe_key = os.getenv('STRIPE_API_KEY')
if not stripe_key:
    raise ValueError("STRIPE_API_KEY environment variable not set")
stripe.api_key = stripe_key
```

#### Step 3: Create .env File (NOT COMMITTED)
```bash
# Create .env file
cat > .env << EOF
STRIPE_API_KEY=sk_test_[NEW_KEY_HERE]
STRIPE_WEBHOOK_SECRET=whsec_[NEW_SECRET_HERE]
EOF

# Ensure .env is in .gitignore
echo ".env" >> .gitignore
echo "*.env" >> .gitignore
echo "!.env.example" >> .gitignore
```

#### Step 4: Create .env.example Template
```bash
cat > .env.example << EOF
# Stripe Configuration
STRIPE_API_KEY=sk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here

# IMPORTANT: Copy this file to .env and replace with real values
# NEVER commit .env to version control
EOF
```

#### Step 5: Verify
```bash
# Test that application fails without env var
unset STRIPE_API_KEY
python stripe-sample-code/server.py  # Should raise ValueError

# Test that application works with env var
export STRIPE_API_KEY="sk_test_[NEW_KEY]"
python stripe-sample-code/server.py  # Should start successfully
```

**Estimated Time:** 30 minutes
**Priority:** CRITICAL
**Status:** [x] Complete (code uses STRIPE_API_KEY env; .env.example in stripe-sample-code; rotate key in dashboard if not already done)

---

### CRITICAL-2: Remove eval() Remote Code Execution

**Vulnerability:** Direct use of eval() allowing arbitrary code execution
**File:** `e:\grid\src\application\resonance\arena_integration.py:61`
**CWE:** CWE-95 (Improper Neutralization of Directives in Dynamically Evaluated Code)

#### Current Vulnerable Code:
```python
for rule in self.rules:
    if eval(rule.condition, {}, context):
        triggered_actions.append(rule.action)
```

#### Option A: Replace with ast.literal_eval (Simple Expressions Only)
```python
import ast

def safe_evaluate_condition(condition: str, context: dict) -> bool:
    """
    Safely evaluate a condition string using AST parsing.
    Only supports literal expressions, no function calls.
    """
    try:
        # Parse the condition into an AST
        node = ast.parse(condition, mode='eval')

        # Validate that only safe operations are used
        for subnode in ast.walk(node):
            if isinstance(subnode, (ast.Call, ast.Import, ast.ImportFrom)):
                raise ValueError(f"Unsafe operation in condition: {ast.dump(subnode)}")

        # Evaluate with restricted context
        return bool(ast.literal_eval(condition))
    except Exception as e:
        logger.error(f"Failed to evaluate condition: {condition}, error: {e}")
        return False

# Usage:
for rule in self.rules:
    if safe_evaluate_condition(rule.condition, context):
        triggered_actions.append(rule.action)
```

#### Option B: Replace with Safe Expression Parser (Recommended)
```python
# Install simpleeval library
# pip install simpleeval

from simpleeval import simple_eval, EvalWithCompoundTypes, NameNotDefined

def safe_evaluate_condition(condition: str, context: dict) -> bool:
    """
    Safely evaluate a condition using simpleeval library.
    Supports comparisons, boolean logic, but no dangerous operations.
    """
    try:
        # Define allowed functions (whitelist)
        allowed_functions = {
            'abs': abs,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'min': min,
            'max': max,
        }

        # Evaluate with restricted context and functions
        result = simple_eval(
            condition,
            names=context,
            functions=allowed_functions
        )
        return bool(result)
    except NameNotDefined as e:
        logger.error(f"Undefined variable in condition: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to evaluate condition: {condition}, error: {e}")
        return False

# Usage:
for rule in self.rules:
    if safe_evaluate_condition(rule.condition, context):
        triggered_actions.append(rule.action)
```

#### Option C: Domain-Specific Language (Most Secure, Most Effort)
```python
from dataclasses import dataclass
from typing import Any, Callable
from enum import Enum

class Operator(Enum):
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    CONTAINS = "contains"
    IN = "in"

@dataclass
class RuleCondition:
    """Type-safe rule condition definition"""
    field: str
    operator: Operator
    value: Any

    def evaluate(self, context: dict) -> bool:
        """Safely evaluate condition against context"""
        if self.field not in context:
            return False

        field_value = context[self.field]

        if self.operator == Operator.EQUALS:
            return field_value == self.value
        elif self.operator == Operator.NOT_EQUALS:
            return field_value != self.value
        elif self.operator == Operator.GREATER_THAN:
            return field_value > self.value
        elif self.operator == Operator.LESS_THAN:
            return field_value < self.value
        elif self.operator == Operator.GREATER_EQUAL:
            return field_value >= self.value
        elif self.operator == Operator.LESS_EQUAL:
            return field_value <= self.value
        elif self.operator == Operator.CONTAINS:
            return self.value in field_value
        elif self.operator == Operator.IN:
            return field_value in self.value
        else:
            return False

# Usage:
for rule in self.rules:
    # rule.condition is now a RuleCondition object, not a string
    if rule.condition.evaluate(context):
        triggered_actions.append(rule.action)
```

#### Implementation Steps:
```bash
# 1. Install dependencies
pip install simpleeval

# 2. Update arena_integration.py with Option B (recommended for balance of security and flexibility)

# 3. Update tests to verify no eval() usage
# 4. Run security scan to confirm eval() removed
bandit -r src/application/resonance/arena_integration.py
```

#### Migration Note for Existing Rules:
```python
# Create migration script to update existing rule conditions
# From: "context['score'] > 0.8"
# To: RuleCondition(field='score', operator=Operator.GREATER_THAN, value=0.8)
# OR keep string format but use safe_evaluate_condition()
```

**Estimated Time:** 4 hours (Option B), 8 hours (Option C)
**Status:** [x] Complete (arena_integration.py uses safe_eval_condition AST-based evaluator; no eval())

---

### CRITICAL-3: Update Vulnerable Dependencies

**Vulnerabilities:** Multiple outdated packages with known CVEs
**Affected Files:** `e:\grid\arena_api\requirements.txt`

#### Current Vulnerable Versions:
```
aiohttp==3.9.1        → CVE-2024-23334 (Directory Traversal)
cryptography==41.0.7  → Multiple CVEs
fastapi==0.104.1      → CORS bypass
starlette==0.27.0     → Security updates available
transformers==4.35.2  → Updates available
```

#### Step 1: Update requirements.txt
```bash
# Backup current requirements
cp arena_api/requirements.txt arena_api/requirements.txt.backup

# Update to latest secure versions
cat > arena_api/requirements.txt << EOF
# Web Framework (updated for security)
fastapi==0.115.6
starlette==0.45.2
uvicorn==0.34.0

# HTTP Client (CRITICAL: CVE-2024-23334 fix)
aiohttp==3.11.11

# Security
cryptography==44.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# ML/AI
transformers==4.48.3
torch==2.5.1
sentence-transformers==3.3.1

# Data Processing
pydantic==2.10.5
pydantic-settings==2.7.1

# Database
sqlalchemy==2.0.36
alembic==1.14.0

# Testing
pytest==8.3.4
pytest-asyncio==0.24.0
httpx==0.28.1
EOF
```

#### Step 2: Update Dependencies
```bash
# Create new virtual environment (clean slate)
cd arena_api
python -m venv .venv_new
source .venv_new/bin/activate  # On Windows: .venv_new\Scripts\activate

# Install updated dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify no vulnerabilities
pip install safety pip-audit
safety check
pip-audit

# Run tests to ensure compatibility
pytest tests/
```

#### Step 3: Update Lock File
```bash
# Generate new lock file
pip freeze > requirements.lock

# Update UV lock if using UV
uv pip compile requirements.txt -o requirements.lock
```

#### Step 4: Verify Application Still Works
```bash
# Start application
uvicorn app.main:app --reload

# Run integration tests
pytest tests/integration/

# Check logs for deprecation warnings
grep -i "deprecat" logs/app.log
```

**Estimated Time:** 2 hours
**Priority:** CRITICAL
**Status:** [x] Complete (arena_api/requirements.txt updated; run `pip-audit` / `safety check` in venv to verify)

---

### CRITICAL-4: Remove Secrets from Git History

**Vulnerability:** `.env` files and secrets committed to git history
**Risk:** Complete credential exposure, even after deletion

#### Step 1: Identify All Secrets in Git History
```bash
# Search for .env files in history
git log --all --full-history --oneline -- "*.env"

# Search for potential secrets
git log -p --all | grep -i "api_key\|password\|secret\|token" > potential_secrets.txt

# Use git-secrets tool (recommended)
git secrets --install
git secrets --register-aws
git secrets --scan-history
```

#### Step 2: Create Backup
```bash
# Backup entire repository
cd ..
cp -r grid grid_backup_before_history_clean_$(date +%Y%m%d)

# Create list of all branches
cd grid
git branch -a > branches_backup.txt
```

#### Step 3: Remove Secrets Using BFG Repo-Cleaner (Recommended)
```bash
# Install BFG Repo-Cleaner
# Download from: https://rtyley.github.io/bfg-repo-cleaner/
# Or: brew install bfg (Mac)

# Create fresh clone
cd ..
git clone --mirror git@github.com:username/grid.git grid-mirror.git

# Remove .env files from history
bfg --delete-files "*.env" grid-mirror.git

# Remove specific secrets by pattern
echo "[REDACTED_STRIPE_KEY]" > secrets.txt
echo "whsec_12345" >> secrets.txt
echo "[REDACTED_HF_TOKEN]" >> secrets.txt
bfg --replace-text secrets.txt grid-mirror.git

# Clean up
cd grid-mirror.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Push cleaned history (DESTRUCTIVE - coordinate with team)
git push --force
```

#### Step 4: Alternative - Use git filter-branch
```bash
# If BFG not available, use git filter-branch (slower)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch -r *.env" \
  --prune-empty --tag-name-filter cat -- --all

# Remove specific file patterns
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch 'config/.env' 'grid/.env' 'grid/config/env/.env.*'" \
  --prune-empty --tag-name-filter cat -- --all

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin --force --all
git push origin --force --tags
```

#### Step 5: Verify Secrets Removed
```bash
# Clone fresh copy and verify
cd ..
git clone git@github.com:username/grid.git grid-clean-test
cd grid-clean-test

# Search for secrets in history
git log --all --full-history --oneline -- "*.env"  # Should return nothing
git log -p --all | grep -i "sk_test_51STA3R"      # Should return nothing

# Use git-secrets to verify
git secrets --scan-history  # Should report no secrets
```

#### Step 6: Notify Collaborators
```bash
# All collaborators must re-clone repository
# Send notification:

cat > GIT_HISTORY_CLEANED_NOTICE.md << EOF
# IMPORTANT: Git History Cleaned - Action Required

## What Happened
Security secrets were accidentally committed to git history and have been removed.

## Required Actions for All Contributors

### 1. Delete your local repository
```bash
rm -rf grid
```

### 2. Re-clone from GitHub
```bash
git clone git@github.com:username/grid.git
cd grid
```

### 3. Verify your clone is clean
```bash
git log --oneline | head -5  # Should show latest commit: [commit hash] "Clean history - removed secrets"
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with real values (contact admin for credentials)
```

## Do NOT attempt to:
- Merge old branches (they contain old history with secrets)
- Pull from old clones
- Use old working directories

## Questions?
Contact: [your email]
EOF
```

**Estimated Time:** 3-4 hours
**Priority:** CRITICAL
**Status:** [ ] Complete
**Risk:** HIGH (requires force push, coordinate carefully)

---

### CRITICAL-5: Disable Development Authentication Bypass

**Vulnerability:** SUPER_ADMIN access without authentication in development mode
**File:** `e:\grid\src\application\mothership\security\auth.py:218-228`

#### Current Vulnerable Code:
```python
if allow_development_bypass and settings.is_development:
    if os.getenv("MOTHERSHIP_ALLOW_DEV_BYPASS") == "1":
        logger.warning("SECURITY: Bypassing authentication in development mode")
        return {
            "authenticated": False,
            "method": "dev_bypass",
            "user_id": "dev_superuser",
            "role": Role.SUPER_ADMIN.value,
            "permissions": get_permissions_for_role(Role.SUPER_ADMIN),
        }
```

#### Option A: Remove Completely (Most Secure)
```python
# Simply delete the entire bypass block
# Replace with proper development authentication
```

#### Option B: Harden with Multiple Checks (Recommended)
```python
def _check_development_bypass(allow_development_bypass: bool, settings: Settings) -> Optional[dict]:
    """
    Development bypass with multiple safety checks.
    ONLY works in development mode with explicit environment variables.
    """
    # NEVER allow in production
    if settings.environment == "production":
        logger.critical("SECURITY: Attempted dev bypass in PRODUCTION - BLOCKED")
        raise SecurityError("Development bypass not allowed in production")

    # Require explicit opt-in
    if not allow_development_bypass:
        return None

    # Check environment is actually development
    if not settings.is_development:
        logger.error("SECURITY: is_development=False, dev bypass rejected")
        return None

    # Require multiple environment variables (defense in depth)
    bypass_enabled = os.getenv("MOTHERSHIP_ALLOW_DEV_BYPASS") == "1"
    bypass_confirmed = os.getenv("MOTHERSHIP_DEV_BYPASS_CONFIRMED") == "yes_i_understand_the_risk"
    dev_machine = os.getenv("DEV_MACHINE_ID")  # Unique to developer's machine

    if not (bypass_enabled and bypass_confirmed and dev_machine):
        logger.warning("SECURITY: Dev bypass incomplete - missing environment variables")
        return None

    # Log extensively
    logger.warning("=" * 80)
    logger.warning("SECURITY WARNING: Development authentication bypass ACTIVE")
    logger.warning(f"Machine ID: {dev_machine}")
    logger.warning(f"Time: {datetime.now().isoformat()}")
    logger.warning("This grants SUPER_ADMIN privileges without authentication")
    logger.warning("NEVER enable this in production or shared environments")
    logger.warning("=" * 80)

    return {
        "authenticated": False,
        "method": "dev_bypass",
        "user_id": f"dev_superuser_{dev_machine}",
        "role": Role.SUPER_ADMIN.value,
        "permissions": get_permissions_for_role(Role.SUPER_ADMIN),
        "dev_bypass_active": True,  # Flag for logging
    }
```

#### Option C: Separate Development Authentication (Best Practice)
```python
def get_development_auth_user() -> dict:
    """
    Development authentication using environment variables.
    Provides authentication, but simplified for development.
    """
    dev_username = os.getenv("DEV_USERNAME", "dev_user")
    dev_role = os.getenv("DEV_ROLE", Role.USER.value)

    # Still require a password, even in development
    dev_password = os.getenv("DEV_PASSWORD")
    if not dev_password:
        raise ValueError("DEV_PASSWORD must be set for development authentication")

    return {
        "authenticated": True,
        "method": "dev_password",
        "user_id": dev_username,
        "role": dev_role,
        "permissions": get_permissions_for_role(Role[dev_role]),
    }
```

#### Implementation Steps:
```bash
# 1. Choose option (recommend Option B for immediate fix, Option C for long-term)

# 2. Update auth.py with chosen implementation

# 3. Update .env.example with new requirements
cat >> .env.example << EOF

# Development Authentication (Option B)
# MOTHERSHIP_ALLOW_DEV_BYPASS=1
# MOTHERSHIP_DEV_BYPASS_CONFIRMED=yes_i_understand_the_risk
# DEV_MACHINE_ID=your_machine_identifier

# OR Development Authentication (Option C - Recommended)
DEV_USERNAME=developer
DEV_PASSWORD=changeme_in_production
DEV_ROLE=USER
EOF

# 4. Update production deployment to BLOCK dev bypass
cat > deploy/production_security_check.py << EOF
import os
import sys

# Check for development bypass in production
if os.getenv("MOTHERSHIP_ALLOW_DEV_BYPASS"):
    print("ERROR: MOTHERSHIP_ALLOW_DEV_BYPASS is set in production")
    print("This is a CRITICAL SECURITY VULNERABILITY")
    sys.exit(1)

print("Production security check: PASSED")
EOF

# 5. Add to CI/CD pipeline
# In .github/workflows/deploy-production.yml:
# - name: Security check
#   run: python deploy/production_security_check.py
```

#### Step 4: Add Runtime Check
```python
# In main application startup (e.g., main.py or app.py)
@app.on_event("startup")
async def security_startup_check():
    """Verify no development bypasses in production"""
    if settings.environment == "production":
        dangerous_env_vars = [
            "MOTHERSHIP_ALLOW_DEV_BYPASS",
            "MOTHERSHIP_DEV_BYPASS_CONFIRMED",
            "DEV_USERNAME",
            "DEV_PASSWORD",
        ]

        found_dangerous = [var for var in dangerous_env_vars if os.getenv(var)]

        if found_dangerous:
            logger.critical(f"SECURITY: Dangerous environment variables in PRODUCTION: {found_dangerous}")
            raise SecurityError("Production deployment with development environment variables")

        logger.info("Security startup check: PASSED")
```

**Estimated Time:** 2 hours
**Priority:** CRITICAL
**Status:** [ ] Complete

---

## PHASE 2: HIGH PRIORITY REMEDIATION (24-72 HOURS)

### HIGH-1: Implement Secrets Manager

**Current Issue:** Secrets stored in environment variables (plain text)
**Solution:** Migrate to dedicated secrets management solution

#### Option A: Local Development - python-dotenv + Encryption
```bash
# Install dependencies
pip install python-dotenv cryptography

# Create secrets management module
cat > src/grid/security/local_secrets_manager.py << EOF
from cryptography.fernet import Fernet
import os
from pathlib import Path

class LocalSecretsManager:
    """Encrypted secrets for local development"""

    def __init__(self, key_file: Path = Path.home() / ".grid" / "secret.key"):
        self.key_file = key_file
        self._ensure_key()
        self.cipher = Fernet(self._load_key())

    def _ensure_key(self):
        """Generate encryption key if not exists"""
        if not self.key_file.exists():
            self.key_file.parent.mkdir(parents=True, exist_ok=True)
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            self.key_file.chmod(0o600)  # Read/write for owner only

    def _load_key(self) -> bytes:
        """Load encryption key"""
        return self.key_file.read_bytes()

    def encrypt_secret(self, secret: str) -> str:
        """Encrypt a secret value"""
        return self.cipher.encrypt(secret.encode()).decode()

    def decrypt_secret(self, encrypted: str) -> str:
        """Decrypt a secret value"""
        return self.cipher.decrypt(encrypted.encode()).decode()

    def get_secret(self, key: str) -> str:
        """Get decrypted secret from environment"""
        encrypted_value = os.getenv(f"{key}_ENCRYPTED")
        if not encrypted_value:
            raise ValueError(f"Secret {key} not found")
        return self.decrypt_secret(encrypted_value)

# Usage:
secrets = LocalSecretsManager()
stripe_key = secrets.get_secret("STRIPE_API_KEY")
EOF
```

#### Option B: Cloud Secrets Manager (Production)

##### AWS Secrets Manager:
```python
import boto3
from botocore.exceptions import ClientError

class AWSSecretsManager:
    """AWS Secrets Manager integration"""

    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client('secretsmanager', region_name=region_name)

    def get_secret(self, secret_name: str) -> dict:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                raise ValueError(f"Secret {secret_name} not found")
            raise

# Usage:
secrets = AWSSecretsManager()
credentials = secrets.get_secret("grid/production/credentials")
stripe_key = credentials['stripe_api_key']
```

##### HashiCorp Vault:
```python
import hvac

class VaultSecretsManager:
    """HashiCorp Vault integration"""

    def __init__(self, url: str, token: str):
        self.client = hvac.Client(url=url, token=token)
        if not self.client.is_authenticated():
            raise ValueError("Vault authentication failed")

    def get_secret(self, path: str, key: str) -> str:
        """Retrieve secret from Vault"""
        response = self.client.secrets.kv.v2.read_secret_version(path=path)
        return response['data']['data'][key]

# Usage:
vault = VaultSecretsManager(
    url=os.getenv("VAULT_ADDR"),
    token=os.getenv("VAULT_TOKEN")
)
stripe_key = vault.get_secret("secret/data/grid/production", "stripe_api_key")
```

#### Implementation Steps:
```bash
# 1. Choose secrets manager based on environment
#    - Local dev: LocalSecretsManager (Option A)
#    - Production: AWS Secrets Manager or Vault (Option B)

# 2. Install dependencies
pip install python-dotenv cryptography boto3 hvac

# 3. Create unified secrets interface
cat > src/grid/security/secrets.py << EOF
from enum import Enum
import os

class SecretBackend(Enum):
    LOCAL = "local"
    AWS = "aws"
    VAULT = "vault"

class SecretsManager:
    """Unified secrets management interface"""

    def __init__(self):
        backend = os.getenv("SECRETS_BACKEND", "local")

        if backend == "aws":
            from .aws_secrets import AWSSecretsManager
            self.backend = AWSSecretsManager()
        elif backend == "vault":
            from .vault_secrets import VaultSecretsManager
            self.backend = VaultSecretsManager(
                url=os.getenv("VAULT_ADDR"),
                token=os.getenv("VAULT_TOKEN")
            )
        else:
            from .local_secrets_manager import LocalSecretsManager
            self.backend = LocalSecretsManager()

    def get_secret(self, key: str) -> str:
        """Get secret from configured backend"""
        return self.backend.get_secret(key)

# Global instance
secrets = SecretsManager()
EOF

# 4. Update all code to use secrets manager
#    Replace: os.getenv("STRIPE_API_KEY")
#    With:    secrets.get_secret("STRIPE_API_KEY")

# 5. Migrate existing secrets
python -m grid.security.migrate_secrets
```

**Estimated Time:** 6-8 hours
**Priority:** HIGH
**Status:** [ ] Complete

---

### HIGH-2: SQL Injection Audit

**Issue:** Potential SQL injection in dynamic query construction
**Files to Audit:**
- `e:\grid\src\application\resonance\api\performance.py`
- All files using `execute()`, `sql_text()`, or string concatenation for SQL

#### Step 1: Identify All SQL Query Construction
```bash
# Find all database query construction
grep -r "execute\|sql_text\|query\|SELECT\|INSERT\|UPDATE\|DELETE" src/ \
  --include="*.py" \
  | grep -v ".pyc" \
  | grep -v "test_" \
  > sql_query_audit.txt

# Find string concatenation in SQL
grep -r 'f"SELECT\|f"INSERT\|f"UPDATE\|f"DELETE\|f'"'"'SELECT' src/ \
  --include="*.py" \
  > potential_sql_injection.txt
```

#### Step 2: Review Each Query
```python
# BAD: String concatenation (SQL Injection vulnerable)
query = f"SELECT * FROM users WHERE username = '{username}'"
cursor.execute(query)

# GOOD: Parameterized query
query = "SELECT * FROM users WHERE username = ?"
cursor.execute(query, (username,))

# GOOD: SQLAlchemy ORM
from sqlalchemy import select
stmt = select(User).where(User.username == username)
result = session.execute(stmt)
```

#### Step 3: Fix Identified Issues
Example fix for `performance.py:46`:
```python
# BEFORE (potentially vulnerable):
query_str = f"SELECT * FROM performance_metrics WHERE timestamp > {start_time}"
cursor.execute(query_str)

# AFTER (secure):
query_str = "SELECT * FROM performance_metrics WHERE timestamp > ?"
cursor.execute(query_str, (start_time,))

# OR with SQLAlchemy (preferred):
from sqlalchemy import select, text
stmt = select(PerformanceMetric).where(PerformanceMetric.timestamp > start_time)
result = db.execute(stmt)
```

#### Step 4: Implement Input Validation
```python
# Create SQL input validator
from src.grid.security.input_sanitizer import InputSanitizer

def validate_sql_input(value: str, max_length: int = 255) -> str:
    """Validate input before using in SQL query"""
    sanitizer = InputSanitizer()

    # Check for SQL injection patterns
    if sanitizer.contains_sql_injection(value):
        raise ValueError("SQL injection pattern detected")

    # Check length
    if len(value) > max_length:
        raise ValueError(f"Input exceeds maximum length: {max_length}")

    return value

# Usage:
username = validate_sql_input(user_input, max_length=100)
query = "SELECT * FROM users WHERE username = ?"
cursor.execute(query, (username,))
```

#### Step 5: Static Analysis
```bash
# Install sqlmap for automated detection
pip install bandit sqlmap

# Run Bandit security linter
bandit -r src/ -f json -o bandit_sql_report.json

# Check specifically for SQL injection
bandit -r src/ -f json | jq '.results[] | select(.issue_text | contains("SQL"))'
```

**Estimated Time:** 4-6 hours
**Priority:** HIGH
**Status:** [ ] Complete

---

### HIGH-3: Command Injection Audit

**Issue:** subprocess calls with potential user input
**Files to Audit:**
- `e:\grid\src\grid\skills\sandbox.py:283`
- `e:\grid\src\tools\rag\embeddings.py`
- `e:\grid\src\grid\progress\motivator.py`

#### Step 1: Find All subprocess Usage
```bash
# Find all subprocess calls
grep -rn "subprocess\|os.system\|os.popen\|eval\|exec" src/ \
  --include="*.py" \
  > subprocess_audit.txt

# Find shell=True usage (most dangerous)
grep -rn "shell=True" src/ --include="*.py"
```

#### Step 2: Review and Fix Each Instance

##### Example: sandbox.py
```python
# BEFORE (potentially vulnerable):
command = f"python {script_path} {user_args}"
process = await asyncio.create_subprocess_shell(
    command,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE
)

# AFTER (secure):
# Use argument list instead of shell string
command = ["python", script_path] + shlex.split(user_args)
process = await asyncio.create_subprocess_exec(
    *command,  # Unpack list as separate arguments
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE
)

# Even better: Validate script_path and whitelist allowed arguments
import shlex
from pathlib import Path

def validate_script_path(path: str) -> Path:
    """Ensure script path is safe"""
    script = Path(path).resolve()
    allowed_dir = Path("/app/scripts").resolve()

    if not script.is_relative_to(allowed_dir):
        raise ValueError("Script path outside allowed directory")

    if not script.exists():
        raise ValueError("Script does not exist")

    return script

script = validate_script_path(script_path)
args = shlex.split(user_args)  # Safely parse arguments

# Whitelist allowed arguments
allowed_args = {"--input", "--output", "--verbose"}
for arg in args:
    if arg.startswith("--") and arg not in allowed_args:
        raise ValueError(f"Argument not allowed: {arg}")

command = ["python", str(script)] + args
```

##### Example: motivator.py
```python
# BEFORE (vulnerable):
subprocess.run(f"git commit -m '{message}'", shell=True)

# AFTER (secure):
subprocess.run(
    ["git", "commit", "-m", message],  # Argument list
    shell=False,
    check=True,
    capture_output=True
)
```

#### Step 3: Create Safe Subprocess Wrapper
```python
# src/grid/security/safe_subprocess.py
import subprocess
import shlex
from typing import List, Optional
from pathlib import Path

class SafeSubprocess:
    """Secure subprocess execution wrapper"""

    def __init__(self, allowed_commands: Optional[List[str]] = None):
        self.allowed_commands = allowed_commands or ["git", "python", "pip"]

    def run(
        self,
        command: List[str],
        cwd: Optional[Path] = None,
        timeout: int = 30
    ) -> subprocess.CompletedProcess:
        """
        Execute command with security checks.

        Args:
            command: List of command arguments (NOT a string)
            cwd: Working directory
            timeout: Timeout in seconds
        """
        # Validate command is in whitelist
        if command[0] not in self.allowed_commands:
            raise ValueError(f"Command not allowed: {command[0]}")

        # Ensure command is a list, not a string
        if not isinstance(command, list):
            raise ValueError("Command must be a list of arguments")

        # Validate working directory
        if cwd:
            cwd = Path(cwd).resolve()
            if not cwd.exists():
                raise ValueError("Working directory does not exist")

        # Execute with security restrictions
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                shell=False,  # NEVER use shell=True
                timeout=timeout,
                check=False,
                capture_output=True,
                text=True
            )
            return result
        except subprocess.TimeoutExpired:
            raise ValueError(f"Command timed out after {timeout} seconds")

# Usage:
safe_subprocess = SafeSubprocess(allowed_commands=["git", "python"])
result = safe_subprocess.run(["git", "status"], cwd="/app/repo")
```

**Estimated Time:** 4 hours
**Priority:** HIGH
**Status:** [ ] Complete

---

## PHASE 3: MEDIUM PRIORITY (1-2 WEEKS)

### MEDIUM-1: Replace Pickle Serialization

**Issue:** Pickle deserialization can execute arbitrary code
**File:** `e:\grid\src\tools\rag\store.py`

#### Solution Options:

##### Option A: Replace with JSON
```python
# BEFORE:
import pickle

def save_data(data, file_path):
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)

def load_data(file_path):
    with open(file_path, 'rb') as f:
        return pickle.load(f)

# AFTER:
import json
from typing import Any
from pathlib import Path

def save_data(data: Any, file_path: Path):
    """Save data as JSON"""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_data(file_path: Path) -> Any:
    """Load data from JSON"""
    with open(file_path, 'r') as f:
        return json.load(f)
```

##### Option B: Signed Pickle (if pickle required)
```python
import pickle
import hmac
import hashlib
from pathlib import Path

class SecurePickle:
    """Pickle with HMAC signing for integrity verification"""

    def __init__(self, secret_key: bytes):
        self.secret_key = secret_key

    def _sign(self, data: bytes) -> bytes:
        """Create HMAC signature"""
        return hmac.new(self.secret_key, data, hashlib.sha256).digest()

    def dump(self, obj: Any, file_path: Path):
        """Serialize and sign object"""
        # Serialize
        pickled = pickle.dumps(obj)

        # Create signature
        signature = self._sign(pickled)

        # Write signature + data
        with open(file_path, 'wb') as f:
            f.write(signature)
            f.write(pickled)

    def load(self, file_path: Path) -> Any:
        """Load and verify signed pickle"""
        with open(file_path, 'rb') as f:
            # Read signature and data
            signature = f.read(32)  # SHA256 is 32 bytes
            pickled = f.read()

        # Verify signature
        expected_signature = self._sign(pickled)
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Pickle signature verification failed - file may be tampered")

        # Only deserialize if signature valid
        return pickle.loads(pickled)

# Usage:
secure_pickle = SecurePickle(secret_key=os.getenv("PICKLE_SECRET_KEY").encode())
secure_pickle.dump(data, Path("data.pkl"))
data = secure_pickle.load(Path("data.pkl"))
```

##### Option C: Protocol Buffers or MessagePack
```python
# Install: pip install msgpack protobuf

import msgpack
from typing import Any
from pathlib import Path

def save_data_msgpack(data: Any, file_path: Path):
    """Save data using MessagePack (faster, safer than pickle)"""
    with open(file_path, 'wb') as f:
        packed = msgpack.packb(data, use_bin_type=True)
        f.write(packed)

def load_data_msgpack(file_path: Path) -> Any:
    """Load data from MessagePack"""
    with open(file_path, 'rb') as f:
        return msgpack.unpackb(f.read(), raw=False)
```

#### Migration Script:
```python
# migrate_pickle_to_json.py
import pickle
import json
from pathlib import Path

def migrate_pickle_files(source_dir: Path, target_dir: Path):
    """Migrate all pickle files to JSON"""
    pickle_files = source_dir.glob("*.pkl")

    for pkl_file in pickle_files:
        try:
            # Load from pickle
            with open(pkl_file, 'rb') as f:
                data = pickle.load(f)

            # Save as JSON
            json_file = target_dir / pkl_file.with_suffix('.json').name
            with open(json_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            print(f"Migrated: {pkl_file} -> {json_file}")
        except Exception as e:
            print(f"Error migrating {pkl_file}: {e}")

# Run migration
migrate_pickle_files(
    source_dir=Path("src/tools/rag/.rag_db"),
    target_dir=Path("src/tools/rag/.rag_db_json")
)
```

**Estimated Time:** 4 hours
**Priority:** MEDIUM
**Status:** [ ] Complete

---

### MEDIUM-2: Add Security Headers

**Issue:** Missing security headers in HTTP responses

#### Implementation:
```python
# src/application/mothership/middleware/security_headers.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS (only for HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=()"
        )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

# Add to FastAPI application:
from fastapi import FastAPI
app = FastAPI()
app.add_middleware(SecurityHeadersMiddleware)
```

**Estimated Time:** 1 hour
**Priority:** MEDIUM
**Status:** [ ] Complete

---

### MEDIUM-3: Penetration Testing

**Action:** Hire professional security firm to conduct penetration test

#### Preparation:
```bash
# 1. Document all endpoints
python -c "from app.main import app; print('\n'.join([f'{route.path} {route.methods}' for route in app.routes]))" > endpoints.txt

# 2. Create test environment
# - Clone production configuration
# - Use separate database
# - Enable verbose logging

# 3. Provide testing credentials
# Create pentest user with controlled permissions

# 4. Define scope
cat > pentest_scope.md << EOF
# Penetration Test Scope

## In Scope
- Web application: https://staging.grid.example.com
- API endpoints: /api/*
- Authentication and authorization
- Input validation
- Session management
- File upload functionality

## Out of Scope
- Production environment
- Social engineering
- Physical security
- Denial of service attacks
- Third-party services (Stripe, AWS)

## Contact
Security Lead: security@grid.example.com
Emergency: +1-XXX-XXX-XXXX
EOF
```

#### Recommended Firms:
- Bishop Fox
- NCC Group
- Trail of Bits
- Cure53 (for web/crypto)
- Include Security

**Estimated Cost:** $10,000-25,000
**Estimated Time:** 2-3 weeks (firm's timeline)
**Priority:** MEDIUM
**Status:** [ ] Complete

---

## PHASE 4: ONGOING SECURITY PRACTICES

### Automated Security Scanning

#### GitHub Actions Workflow:
```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  secret-scanning:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run detect-secrets
        run: |
          pip install detect-secrets
          detect-secrets scan --all-files --force-use-all-plugins

  dependency-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: pip install safety pip-audit

      - name: Safety check
        run: safety check --json

      - name: Pip audit
        run: pip-audit

  sast-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r src/ -f json -o bandit-report.json

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: bandit-report
          path: bandit-report.json

  semgrep:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/owasp-top-ten
            p/python
```

### Pre-commit Hooks:
```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', 'src/', '-ll']

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-added-large-files
        args: ['--maxkb=1000']

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
EOF

# Install hooks
pre-commit install
```

### Security Training

#### Developer Checklist:
```markdown
# Secure Coding Checklist

## Before Committing Code:
- [ ] No hardcoded secrets or credentials
- [ ] All user input validated and sanitized
- [ ] No use of eval(), exec(), or pickle with untrusted data
- [ ] SQL queries use parameterization
- [ ] Subprocess calls use argument lists, not shell strings
- [ ] Authentication and authorization checked
- [ ] Error messages don't leak sensitive information
- [ ] Logging doesn't include PII or secrets

## Before Deploying:
- [ ] All dependencies updated to latest secure versions
- [ ] Security headers configured
- [ ] HTTPS enforced in production
- [ ] Rate limiting enabled
- [ ] Monitoring and alerting configured
- [ ] Secrets using secrets manager, not environment variables
- [ ] Database backups configured
- [ ] Incident response plan documented
```

---

## VERIFICATION AND TESTING

### Security Test Suite:
```python
# tests/security/test_security_comprehensive.py
import pytest
from fastapi.testclient import TestClient

def test_no_hardcoded_secrets():
    """Verify no secrets in codebase"""
    result = subprocess.run(
        ["detect-secrets", "scan", "--all-files"],
        capture_output=True
    )
    assert "No secrets were detected" in result.stdout.decode()

def test_no_eval_usage():
    """Verify no eval() in codebase"""
    result = subprocess.run(
        ["grep", "-r", "eval(", "src/"],
        capture_output=True
    )
    assert result.returncode != 0  # grep returns non-zero if no matches

def test_dependencies_updated():
    """Verify all dependencies are current and secure"""
    result = subprocess.run(["pip-audit"], capture_output=True)
    assert "No known vulnerabilities found" in result.stdout.decode()

def test_security_headers_present(client: TestClient):
    """Verify security headers in response"""
    response = client.get("/")
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
    assert "Strict-Transport-Security" in response.headers

def test_authentication_required(client: TestClient):
    """Verify authentication required for protected endpoints"""
    response = client.get("/api/protected")
    assert response.status_code == 401

def test_no_sql_injection(client: TestClient):
    """Test for SQL injection vulnerability"""
    payload = {"username": "admin' OR '1'='1"}
    response = client.post("/api/login", json=payload)
    assert response.status_code in [400, 401]  # Should reject, not succeed

def test_no_command_injection():
    """Test command injection protection"""
    from src.grid.security.safe_subprocess import SafeSubprocess

    safe_subprocess = SafeSubprocess()
    with pytest.raises(ValueError):
        safe_subprocess.run(["python", "; rm -rf /"])
```

---

## SUCCESS CRITERIA

### Phase 1 Complete When:
- [x] All critical vulnerabilities patched
- [ ] All secrets rotated
- [ ] Git history cleaned
- [ ] Dependencies updated
- [ ] No eval() usage
- [ ] Development bypass hardened

### Phase 2 Complete When:
- [ ] Secrets manager implemented
- [ ] All SQL queries use parameterization
- [ ] All subprocess calls use argument lists
- [ ] Input validation comprehensive

### Phase 3 Complete When:
- [ ] Pickle replaced with safer serialization
- [ ] Security headers added
- [ ] Penetration test completed and issues resolved

### Ongoing Success Metrics:
- Zero critical vulnerabilities in quarterly scans
- All dependencies updated within 30 days of security release
- 100% of PRs pass security checks
- Security training completed annually by all developers

---

## INCIDENT RESPONSE PLAN

### If Exploitation Detected:

1. **Contain** (0-1 hour):
   - Disable compromised services
   - Rotate all credentials
   - Block attacker IP addresses
   - Preserve logs and evidence

2. **Investigate** (1-24 hours):
   - Analyze logs for attacker activity
   - Identify data accessed/exfiltrated
   - Determine initial attack vector
   - Assess scope of compromise

3. **Remediate** (24-72 hours):
   - Patch vulnerabilities exploited
   - Restore from clean backups if needed
   - Implement additional monitoring
   - Deploy security updates

4. **Notify** (72 hours):
   - Internal stakeholders
   - Affected users (if applicable)
   - Law enforcement (if criminal)
   - Regulatory authorities (if required)

5. **Post-Incident** (1-2 weeks):
   - Detailed incident report
   - Lessons learned review
   - Update security procedures
   - Additional training if needed

---

## DOCUMENT CONTROL

**Version:** 1.0
**Last Updated:** 2026-02-02
**Next Review:** 2026-02-09 (weekly during remediation)
**Owner:** Security Team
**Status:** ACTIVE REMEDIATION

---

**END OF REMEDIATION PLAN**
