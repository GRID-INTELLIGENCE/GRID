# Type Checker Quick Reference

## Common Type Errors & Fixes

### 1. ❌ Truthy Checks on Optional Types
```python
# BAD: Type checker doesn't know if it's None
if cache.redis_client:
    await cache.redis_client.ping()

# GOOD: Explicit None check
if cache.redis_client is not None:
    await cache.redis_client.ping()
```

### 2. ❌ None Cannot Be Assigned to Non-Optional
```python
# BAD: Parameter expects float, not None
def retry_policy(initial_wait: float = None):
    pass

# GOOD: Use union type for optional
def retry_policy(initial_wait: float | None = None):
    pass
```

### 3. ❌ Attribute Access on Optional
```python
# BAD: result could be None
return result.success

# GOOD: Guard with None check
if result is not None:
    return result.success
return False
```

### 4. ❌ Missing Module Imports
```python
# BAD: Module not installed
from openai import OpenAI

# GOOD: Conditional import with fallback
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore
```

### 5. ❌ Path vs String Mismatch
```python
# BAD: Expecting string, got Path
file_path: Path = Path("file.txt")
open(file_path + ".backup")  # ERROR

# GOOD: Convert to string
open(str(file_path) + ".backup")
```

---

## Running Type Checks

### Check All Files
```bash
pyright
```

### Check Specific File
```bash
pyright e:/app/main.py
```

### Watch Mode (IDE)
- VS Code: Install Pylance extension
- Command: `pyright --watch`

### Strict Mode
```bash
pyright --outputjson  # JSON format
```

---

## Configuration Files

### Root Level (`pyrightconfig.json`)
- Sets defaults for entire workspace
- Excludes non-essential directories
- Standard strictness

### Backend Level (`Apps/backend/pyrightconfig.json`)
- Strict mode for production code
- Test files use basic mode
- No warnings for legitimate patterns

---

## Suppressing Type Errors

### When Legitimate (Temporary)
```python
result = some_function()  # type: ignore
```

### When Expected (Documented)
```python
# pyright: ignore
from optional_package import something
```

### For Entire Section
```python
# pyright: off
legacy_code_that_wont_be_fixed()
# pyright: on
```

---

## Best Practices Going Forward

1. **Always use `|` for unions** (Python 3.10+)
   ```python
   # Good
   value: int | None = None
   
   # Old style (still works)
   value: Optional[int] = None
   ```

2. **Always check None explicitly**
   ```python
   if value is not None:
       use(value)
   ```

3. **Use type guards in complex logic**
   ```python
   def process(data: Dict[str, Any]) -> None:
       if "key" in data and isinstance(data["key"], str):
           print(data["key"].upper())
   ```

4. **Document optional dependencies**
   ```python
   """
   Requires: Optional[torch] - ML features
   Gracefully degrades without it
   """
   try:
       import torch
   except ImportError:
       torch = None
   ```

---

## IDE Integration

### VS Code (Recommended)
- Install: Pylance extension
- Settings → Pylance → Type Checking Mode: "strict"
- Shows errors inline

### PyCharm
- Settings → Editor → Inspections → Python
- Enable type checking inspections

### Vim/Neovim
```bash
pip install pyright
# Then configure with LSP
```

---

## Continuous Integration

Add to CI/CD pipeline:
```bash
# .github/workflows/typecheck.yml
- name: Type Check
  run: pyright --outputjson > typecheck.json
  
- name: Fail on Errors
  run: |
    if grep -q '"severity": "error"' typecheck.json; then
      exit 1
    fi
```

---

## Resources

- [Basedpyright Docs](https://docs.basedpyright.com/)
- [Python Typing PEP 484](https://peps.python.org/pep-0484/)
- [FastAPI Type Checking](https://fastapi.tiangolo.com/python-types/)
- [SQLAlchemy Type Stubs](https://docs.sqlalchemy.org/en/20/orm/declarative_config.html#orm-declarative-dataclass-tips)
