# Data Loaders Usage Guide

## Overview
The `data_loaders` module provides standardized utilities for loading and saving user data and configuration files in JSON format.

## Features
- ✅ **Type-safe**: Full type hints for IDE support
- ✅ **Error handling**: Comprehensive exception handling with clear error messages
- ✅ **Logging**: Professional logging integration
- ✅ **Security**: Path traversal protection
- ✅ **Validation**: Input validation and data structure verification
- ✅ **Metadata**: Automatic metadata injection for traceability

---

## API Reference

### `load_user(user_id: str, data_store_path: Optional[str] = None) -> Dict[str, Any]`

Fetch user JSON from the data store.

**Parameters:**
- `user_id` (str): Unique identifier for the user
- `data_store_path` (Optional[str]): Path to data store directory (defaults to `./data/users/`)

**Returns:**
- `Dict[str, Any]`: User data dictionary with injected metadata

**Raises:**
- `FileNotFoundError`: If user file doesn't exist
- `json.JSONDecodeError`: If user file contains invalid JSON
- `ValueError`: If user_id is empty or invalid

**Example:**
```python
from src.grid.utils.data_loaders import load_user

# Load user with default data store path
user_data = load_user("user_12345")
print(f"User: {user_data['name']}")
print(f"Email: {user_data['email']}")

# Load user with custom data store path
user_data = load_user("user_12345", data_store_path="/custom/path/users")
```

**Metadata Fields:**
- `_loaded_from`: Absolute path to the source file
- `_user_id`: The user ID used to load the data

---

### `load_config(path: str) -> Dict[str, Any]`

Load configuration from a JSON file.

**Parameters:**
- `path` (str): Path to the configuration file (absolute or relative)

**Returns:**
- `Dict[str, Any]`: Configuration data dictionary with injected metadata

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `json.JSONDecodeError`: If config file contains invalid JSON
- `ValueError`: If path is empty or invalid

**Example:**
```python
from src.grid.utils.data_loaders import load_config

# Load configuration
config = load_config("config/production.json")
print(f"App: {config['app_name']}")
print(f"Environment: {config['environment']}")

# Access nested settings
db_host = config['database']['host']
api_port = config['api']['port']
```

**Metadata Fields:**
- `_loaded_from`: Absolute path to the source file
- `_file_name`: Name of the configuration file

---

### `save_user(user_id: str, user_data: Dict[str, Any], data_store_path: Optional[str] = None) -> Path`

Save user data to JSON file in the data store.

**Parameters:**
- `user_id` (str): Unique identifier for the user
- `user_data` (Dict[str, Any]): User data dictionary to save
- `data_store_path` (Optional[str]): Path to data store directory

**Returns:**
- `Path`: Path to the saved user file

**Raises:**
- `ValueError`: If user_id is empty or user_data is not a dictionary

**Example:**
```python
from src.grid.utils.data_loaders import save_user

# Create user data
new_user = {
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "role": "developer",
    "preferences": {
        "theme": "dark",
        "notifications": True
    }
}

# Save user
saved_path = save_user("user_67890", new_user)
print(f"User saved to: {saved_path}")
```

**Notes:**
- Automatically creates the data store directory if it doesn't exist
- Removes metadata fields (starting with `_`) before saving
- Uses UTF-8 encoding and pretty-prints JSON with 2-space indentation

---

### `save_config(path: str, config_data: Dict[str, Any]) -> Path`

Save configuration data to JSON file.

**Parameters:**
- `path` (str): Path where to save the configuration
- `config_data` (Dict[str, Any]): Configuration dictionary to save

**Returns:**
- `Path`: Path to the saved config file

**Raises:**
- `ValueError`: If path is empty or config_data is not a dictionary

**Example:**
```python
from src.grid.utils.data_loaders import save_config

# Create configuration
app_config = {
    "app_name": "Grid",
    "version": "1.0.0",
    "environment": "production",
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "grid_db"
    },
    "api": {
        "host": "0.0.0.0",
        "port": 8000,
        "prefix": "/api/v1"
    }
}

# Save configuration
saved_path = save_config("config/production.json", app_config)
print(f"Config saved to: {saved_path}")
```

**Notes:**
- Automatically creates parent directories if they don't exist
- Removes metadata fields (starting with `_`) before saving
- Uses UTF-8 encoding and pretty-prints JSON with 2-space indentation

---

## Complete Usage Examples

### Example 1: User Management System

```python
from src.grid.utils.data_loaders import load_user, save_user

def create_new_user(user_id: str, name: str, email: str, role: str):
    """Create a new user in the system"""
    user_data = {
        "name": name,
        "email": email,
        "role": role,
        "created_at": "2025-11-29T13:21:23+06:00",
        "active": True
    }

    save_user(user_id, user_data)
    print(f"✅ Created user: {name}")

def get_user_profile(user_id: str):
    """Retrieve user profile"""
    try:
        user = load_user(user_id)
        print(f"Name: {user['name']}")
        print(f"Email: {user['email']}")
        print(f"Role: {user['role']}")
        return user
    except FileNotFoundError:
        print(f"❌ User {user_id} not found")
        return None

# Usage
create_new_user("dev_001", "Alice Johnson", "alice@grid.dev", "developer")
profile = get_user_profile("dev_001")
```

### Example 2: Configuration Management

```python
from src.grid.utils.data_loaders import load_config, save_config

def load_environment_config(env: str):
    """Load configuration for specific environment"""
    config_path = f"config/{env}.json"

    try:
        config = load_config(config_path)
        print(f"✅ Loaded {env} configuration")
        return config
    except FileNotFoundError:
        print(f"❌ Configuration for {env} not found")
        return None

def update_api_settings(env: str, new_port: int):
    """Update API port in configuration"""
    config = load_environment_config(env)

    if config:
        config['api']['port'] = new_port
        save_config(f"config/{env}.json", config)
        print(f"✅ Updated API port to {new_port}")

# Usage
prod_config = load_environment_config("production")
update_api_settings("production", 9000)
```

### Example 3: Data Migration

```python
from src.grid.utils.data_loaders import load_user, save_user
from pathlib import Path

def migrate_users(old_path: str, new_path: str):
    """Migrate users from old data store to new one"""
    old_dir = Path(old_path)
    migrated_count = 0

    for user_file in old_dir.glob("*.json"):
        user_id = user_file.stem

        try:
            # Load from old location
            user_data = load_user(user_id, data_store_path=old_path)

            # Save to new location
            save_user(user_id, user_data, data_store_path=new_path)

            migrated_count += 1
            print(f"✅ Migrated user: {user_id}")

        except Exception as e:
            print(f"❌ Failed to migrate {user_id}: {e}")

    print(f"\n📊 Migration complete: {migrated_count} users migrated")

# Usage
migrate_users("data/old_users", "data/users")
```

### Example 4: Error Handling

```python
from src.grid.utils.data_loaders import load_config
import json

def safe_load_config(path: str, default_config: dict = None):
    """Safely load configuration with fallback"""
    try:
        return load_config(path)

    except FileNotFoundError:
        print(f"⚠️  Config file not found: {path}")
        if default_config:
            print("Using default configuration")
            return default_config
        raise

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        print(f"   Error at position {e.pos}")
        raise

    except ValueError as e:
        print(f"❌ Configuration validation error: {e}")
        raise

# Usage with fallback
default = {
    "app_name": "Grid",
    "environment": "development"
}

config = safe_load_config("config/app.json", default_config=default)
```

---

## Best Practices

### 1. Always Use Try-Except for File Operations
```python
try:
    user = load_user("user_123")
except FileNotFoundError:
    # Handle missing user
    user = create_default_user("user_123")
except json.JSONDecodeError:
    # Handle corrupted data
    logger.error("User data corrupted")
    raise
```

### 2. Validate Data After Loading
```python
user = load_user("user_123")

# Validate required fields
required_fields = ["name", "email", "role"]
if not all(field in user for field in required_fields):
    raise ValueError("User data missing required fields")
```

### 3. Use Metadata for Debugging
```python
config = load_config("config/app.json")

# Log where config was loaded from
logger.info(f"Configuration loaded from: {config['_loaded_from']}")
logger.info(f"Configuration file: {config['_file_name']}")
```

### 4. Clean Data Before Saving
```python
# Remove temporary/computed fields before saving
user_data = {k: v for k, v in user.items() if not k.startswith("_temp")}
save_user("user_123", user_data)
```

### 5. Use Type Hints
```python
from typing import Dict, Any

def process_user_data(user_id: str) -> Dict[str, Any]:
    """Process user data with type safety"""
    user: Dict[str, Any] = load_user(user_id)
    # IDE will provide autocomplete and type checking
    return user
```

---

## Testing

Run the comprehensive test suite:

```bash
# Run all data loader tests
pytest tests/unit/test_data_loaders.py -v

# Run with coverage
pytest tests/unit/test_data_loaders.py --cov=src.grid.utils.data_loaders --cov-report=html

# Run specific test class
pytest tests/unit/test_data_loaders.py::TestLoadUser -v

# Run specific test
pytest tests/unit/test_data_loaders.py::TestLoadUser::test_load_user_success -v
```

---

## Security Considerations

### Path Traversal Protection
The module automatically sanitizes user IDs to prevent path traversal attacks:

```python
# This is safe - path traversal attempts are sanitized
user = load_user("../../etc/passwd")
# Actual file accessed: data/users/.._.._etc_passwd.json
```

### UTF-8 Encoding
All files are read and written with UTF-8 encoding to support international characters:

```python
user_data = {
    "name": "José García",
    "location": "São Paulo",
    "bio": "Développeur 开发者"
}
save_user("user_123", user_data)  # ✅ Works correctly
```

---

## Troubleshooting

### Issue: FileNotFoundError
**Cause**: User or config file doesn't exist
**Solution**: Check the file path and ensure the file exists

```python
from pathlib import Path

# Check if file exists before loading
user_file = Path("data/users/user_123.json")
if user_file.exists():
    user = load_user("user_123")
else:
    print("User file not found")
```

### Issue: JSONDecodeError
**Cause**: File contains invalid JSON
**Solution**: Validate JSON syntax

```bash
# Validate JSON file
python -m json.tool data/users/user_123.json
```

### Issue: ValueError (not a dict)
**Cause**: JSON file contains array instead of object
**Solution**: Ensure file contains a JSON object `{...}` not array `[...]`

---

## Changelog

### Version 1.0.0 (2025-11-29)
- ✅ Initial release
- ✅ `load_user()` function
- ✅ `load_config()` function
- ✅ `save_user()` function
- ✅ `save_config()` function
- ✅ Comprehensive error handling
- ✅ Path traversal protection
- ✅ Metadata injection
- ✅ Full test coverage
- ✅ Professional logging

---

## Contributing

When contributing to this module:

1. **Maintain backward compatibility**
2. **Add tests for new features**
3. **Update documentation**
4. **Follow type hint conventions**
5. **Preserve security features**

---

## License

Part of the GRID project. See main project LICENSE for details.
