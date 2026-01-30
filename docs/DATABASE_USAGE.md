# Database Usage Guide - Agentic System

## Overview

The Agentic System uses Databricks for persistent storage of cases, events, and learning data. This guide covers database setup, usage, and best practices.

## Database Schema

### AgenticCase Table

The `agentic_cases` table stores all case information:

```sql
CREATE TABLE agentic_cases (
    case_id VARCHAR(255) PRIMARY KEY,
    raw_input TEXT NOT NULL,
    user_id VARCHAR(255),
    category VARCHAR(100),
    priority VARCHAR(50) DEFAULT 'medium',
    confidence FLOAT,
    structured_data JSON,
    labels JSON,
    keywords JSON,
    entities JSON,
    relationships JSON,
    reference_file_path VARCHAR(500),
    status VARCHAR(50) DEFAULT 'created',
    agent_role VARCHAR(100),
    task VARCHAR(100),
    outcome VARCHAR(50),
    solution TEXT,
    agent_experience JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time_seconds FLOAT
);
```

## Setup

### 1. Databricks Configuration

Configure Databricks in `application/mothership/config.py`:

```python
database:
  use_databricks: true
  url: "databricks://token:your-token@your-hostname.cloud.databricks.com:443/default"
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
```

### 2. Environment Variables

```bash
# Databricks credentials
export DATABRICKS_SERVER_HOSTNAME="your-hostname.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
export DATABRICKS_ACCESS_TOKEN="your-token"

# Or use .env file
DATABRICKS_SERVER_HOSTNAME=your-hostname.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_ACCESS_TOKEN=your-token
```

### 3. Initialize Database

```python
from application.mothership.db.models_agentic import AgenticCase
from application.mothership.db.models_base import Base
from application.mothership.db.engine import get_async_engine

# Create tables
engine = get_async_engine()
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

## Usage

### Creating Cases

```python
from application.mothership.repositories.agentic import AgenticRepository
from application.mothership.db.engine import get_async_sessionmaker

async def create_case_example():
    sessionmaker = get_async_sessionmaker()
    async with sessionmaker() as session:
        repository = AgenticRepository(session)

        case = await repository.create_case(
            case_id="CASE-001",
            raw_input="Add contract testing to CI",
            user_id="user123"
        )

        print(f"Created case: {case.case_id}")
```

### Querying Cases

```python
# Get case by ID
case = await repository.get_case("CASE-001")

# List cases with filters
cases = await repository.list_cases(
    status="completed",
    category="testing",
    limit=20,
    offset=0
)

# Find similar cases
similar = await repository.find_similar_cases(
    category="testing",
    keywords=["test", "ci"],
    limit=10
)
```

### Updating Cases

```python
# Update case status
updated = await repository.update_case_status(
    case_id="CASE-001",
    status="completed",
    outcome="success",
    solution="Solution applied",
    agent_experience={"time_taken": "2 hours"}
)
```

### Getting Experience Metrics

```python
# Get aggregated experience
experience = await repository.get_agent_experience()

print(f"Total cases: {experience['total_cases']}")
print(f"Success rate: {experience['success_rate']:.1%}")
print(f"Category distribution: {experience['category_distribution']}")
```

## Best Practices

### 1. Connection Management

**Always use async context managers:**

```python
# Good: Proper connection management
async with sessionmaker() as session:
    repository = AgenticRepository(session)
    case = await repository.get_case("CASE-001")

# Bad: Manual session management
session = sessionmaker()
case = await repository.get_case("CASE-001")
# Missing: session.close()
```

### 2. Transaction Management

**Use transactions for multiple operations:**

```python
async with sessionmaker() as session:
    async with session.begin():
        repository = AgenticRepository(session)

        # Multiple operations in one transaction
        case = await repository.create_case(...)
        await repository.update_case_status(...)
        # All or nothing
```

### 3. Query Optimization

**Use indexes and limits:**

```python
# Good: Indexed query with limit
cases = await repository.list_cases(
    category="testing",
    limit=20  # Always limit results
)

# Bad: Unbounded query
cases = await repository.list_cases()  # Could return thousands
```

### 4. Error Handling

**Handle database errors gracefully:**

```python
from sqlalchemy.exc import SQLAlchemyError

try:
    case = await repository.get_case("CASE-001")
except SQLAlchemyError as e:
    logger.error(f"Database error: {e}")
    # Handle error appropriately
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### 5. Connection Pooling

**Configure appropriate pool sizes:**

```python
# In config.py
database:
  pool_size: 10        # Base pool size
  max_overflow: 20      # Additional connections
  pool_timeout: 30      # Timeout in seconds
```

### 6. Prepared Statements

**Use parameterized queries (SQLAlchemy does this automatically):**

```python
# Good: Parameterized (SQLAlchemy default)
case = await repository.get_case(case_id)  # Safe from SQL injection

# Bad: String concatenation (never do this)
# query = f"SELECT * FROM cases WHERE id = '{case_id}'"  # SQL injection risk
```

## Security Best Practices

### 1. Credential Management

**Never hardcode credentials:**

```python
# Good: Environment variables
token = os.getenv("DATABRICKS_ACCESS_TOKEN")

# Bad: Hardcoded
token = "dapi1234567890abcdef"  # Never do this
```

### 2. Access Control

**Use least privilege principle:**

- Create separate database users for different services
- Grant only necessary permissions
- Use read-only users for queries

### 3. Data Encryption

**Ensure encrypted connections:**

```python
# Databricks uses TLS by default
url = "databricks://token:token@hostname:443/default"  # Port 443 = HTTPS
```

### 4. Input Validation

**Validate all inputs before database operations:**

```python
from pydantic import BaseModel, validator

class CaseCreateRequest(BaseModel):
    raw_input: str

    @validator('raw_input')
    def validate_input(cls, v):
        if len(v) > 10000:
            raise ValueError("Input too long")
        if not v.strip():
            raise ValueError("Input cannot be empty")
        return v.strip()
```

### 5. SQL Injection Prevention

**SQLAlchemy automatically prevents SQL injection, but be cautious:**

```python
# Good: SQLAlchemy ORM (safe)
case = await session.get(AgenticCase, case_id)

# Good: Parameterized queries (safe)
result = await session.execute(
    select(AgenticCase).where(AgenticCase.case_id == case_id)
)

# Bad: Raw SQL with string formatting (dangerous)
# result = await session.execute(f"SELECT * FROM cases WHERE id = '{case_id}'")
```

## Performance Optimization

### 1. Indexing

**Create indexes on frequently queried fields:**

```sql
CREATE INDEX idx_case_status ON agentic_cases(status);
CREATE INDEX idx_case_category ON agentic_cases(category);
CREATE INDEX idx_case_created_at ON agentic_cases(created_at);
CREATE INDEX idx_case_user_id ON agentic_cases(user_id);
```

### 2. Query Optimization

**Use select_related for joins:**

```python
# Good: Eager loading
from sqlalchemy.orm import selectinload

query = select(AgenticCase).options(
    selectinload(AgenticCase.related_cases)
)
```

### 3. Batch Operations

**Batch inserts and updates:**

```python
# Good: Batch insert
cases = [AgenticCase(...) for _ in range(100)]
session.add_all(cases)
await session.commit()

# Bad: Individual inserts
for case_data in cases_data:
    case = AgenticCase(**case_data)
    session.add(case)
    await session.commit()  # Too many commits
```

### 4. Connection Pooling

**Monitor and tune pool size:**

```python
# Check pool status
pool = engine.pool
print(f"Pool size: {pool.size()}")
print(f"Checked out: {pool.checkedout()}")
print(f"Overflow: {pool.overflow()}")
```

## Monitoring

### 1. Query Logging

**Enable query logging for debugging:**

```python
# In config.py
database:
  echo: true  # Log all SQL queries
```

### 2. Performance Metrics

**Track query performance:**

```python
import time

start = time.perf_counter()
case = await repository.get_case("CASE-001")
duration = time.perf_counter() - start

if duration > 1.0:
    logger.warning(f"Slow query: {duration:.3f}s")
```

### 3. Connection Monitoring

**Monitor connection pool:**

```python
# Check for connection leaks
pool = engine.pool
if pool.checkedout() > pool.size() * 0.8:
    logger.warning("High connection usage")
```

## Troubleshooting

### Connection Issues

**Check connectivity:**

```python
try:
    async with sessionmaker() as session:
        await session.execute(text("SELECT 1"))
        print("Connection successful")
except Exception as e:
    print(f"Connection failed: {e}")
```

### Timeout Issues

**Increase timeout for long queries:**

```python
# In config.py
database:
  pool_timeout: 60  # Increase timeout
```

### Memory Issues

**Limit result sets:**

```python
# Always use limits
cases = await repository.list_cases(limit=100)  # Not unlimited
```

## References

- **Repository**: `application/mothership/repositories/agentic.py`
- **Models**: `application/mothership/db/models_agentic.py`
- **Engine**: `application/mothership/db/engine.py`
- **Config**: `application/mothership/config.py`
