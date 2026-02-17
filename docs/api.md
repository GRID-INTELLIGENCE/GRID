# API Documentation

## Overview

The Python Framework provides a RESTful API built with FastAPI. The API follows REST conventions and includes automatic documentation, validation, and authentication.

## Application Initialization

The application is initialized using the **Builder Pattern** (`src/core/builder.py`), which ensures a clean separation between configuration and construction.

```python
from src.core.builder import GridAppBuilder
from src.core.config import Settings

app = (
    GridAppBuilder()
    .with_settings(Settings())
    .with_router(router)
    .build()
)
```

## Base URL

```
Development: http://localhost:8000
Production:  https://api.yourdomain.com
```

## Authentication

The API uses JWT (JSON Web Token) authentication:

### Authentication Flow

1. **Bootstrap (first run only)**: When the database has no users, create the first admin via `POST /users/bootstrap`.
2. **Login**: Send credentials to `POST /users/login`.
3. **Token Response**: Receive an access token and refresh token.
4. **Authenticated Requests**: Include `Authorization: Bearer <access_token>` header for protected endpoints.
5. **Refresh**: When the access token expires, call `POST /users/refresh` with the `refresh_token` to obtain a new access token.

### Token Types

- **Access Token**: Short-lived (30 minutes by default)
- **Refresh Token**: Long-lived (7 days by default)

### Example Authentication

```bash
# 1) Bootstrap first admin user (only when DB has no users)
curl -X POST http://localhost:8000/users/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "email": "admin@example.com", "password": "StrongPassword123!"}'

# 2) Login
curl -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "StrongPassword123!"}'

# 3) Use access token
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/users/

# 4) Refresh access token
curl -X POST http://localhost:8000/users/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

### OpenAI Responses Proxy

Authenticated users can proxy requests to the OpenAI Responses API via:

```http
POST /users/ai/respond
```

**Headers:**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request body:**

```json
{
  "prompt": "Say hello in one short sentence.",
  "model": "gpt-4.1-mini"
}
```

The endpoint forwards the request to `https://api.openai.com/v1/responses` using the `OPENAI_API_KEY` environment variable and returns the raw JSON response from OpenAI.

## API Endpoints

### NER (Named Entity Recognition) Endpoints

The NER system provides cross-domain entity extraction, pattern recognition, and scenario-based analysis capabilities.

#### Ingest Event

```http
POST /ner/events/ingest
```

**Request Body:**
```json
{
  "source": "twitter",
  "text": "Acme Corp raised $10M in funding to expand into Europe",
  "timestamp": "2025-01-15T10:00:00Z",
  "metadata": {
    "url": "https://example.com/article"
  }
}
```

**Response:**
```json
{
  "event_id": "uuid",
  "entities": [
    {
      "id": "entity-uuid",
      "type": "ORG",
      "text": "Acme Corp",
      "confidence": 0.9
    },
    {
      "id": "entity-uuid-2",
      "type": "MONEY",
      "text": "$10M",
      "confidence": 0.95
    },
    {
      "id": "entity-uuid-3",
      "type": "LOCATION",
      "text": "Europe",
      "confidence": 0.85
    }
  ],
  "relationships": 2
}
```

#### Get Entities

```http
GET /ner/entities?entity_type=ORG&date_from=2025-01-01&text_contains=Acme&limit=100
```

**Query Parameters:**
- `entity_type` (optional): Filter by entity type (ORG, PERSON, PRODUCT, LOCATION, MONEY, DATE, LAW, EVENT)
- `date_from` (optional): Filter by date from (ISO 8601)
- `date_to` (optional): Filter by date to (ISO 8601)
- `text_contains` (optional): Filter by text contains
- `limit` (optional): Maximum number of results (default: 100)

**Response:**
```json
[
  {
    "id": "entity-uuid",
    "type": "ORG",
    "text": "Acme Corp",
    "normalized_text": "acme corp",
    "confidence": 0.9,
    "event_id": "event-uuid"
  }
]
```

#### Get Events

```http
GET /ner/events?source=twitter&processed=true&limit=100
```

**Query Parameters:**
- `source` (optional): Filter by source
- `processed` (optional): Filter by processed status (true/false)
- `limit` (optional): Maximum number of results (default: 100)

**Response:**
```json
[
  {
    "id": "event-uuid",
    "source": "twitter",
    "timestamp": "2025-01-15T10:00:00Z",
    "raw_text": "Acme Corp raised $10M",
    "processed": true,
    "entities": [...]
  }
]
```

#### Analyze Scenario

```http
POST /ner/scenarios/analyze
```

**Request Body:**
```json
{
  "name": "Competitor Intelligence Q1 2025",
  "description": "Analyze competitor activity in Q1 2025",
  "configuration": {
    "time_window_hours": 2160,
    "sources": ["twitter", "news"],
    "keywords": ["funding", "acquisition", "launch"]
  }
}
```

**Response:**
```json
{
  "id": "scenario-uuid",
  "name": "Competitor Intelligence Q1 2025",
  "status": "completed",
  "result": {
    "obvious_players": [...],
    "hidden_players": [...],
    "competitive_landscape": {...}
  },
  "created_at": "2025-01-15T10:00:00Z",
  "completed_at": "2025-01-15T10:05:00Z"
}
```

#### Get Scenario

```http
GET /ner/scenarios/{scenario_id}
```

**Response:**
```json
{
  "id": "scenario-uuid",
  "name": "Competitor Intelligence Q1 2025",
  "status": "completed",
  "result": {...},
  "created_at": "2025-01-15T10:00:00Z",
  "completed_at": "2025-01-15T10:05:00Z"
}
```

#### Test Rules

```http
POST /ner/rules/test?event_id={event_id}
```

**Response:**
```json
[
  {
    "id": "alert-uuid",
    "rule_id": "rule-uuid",
    "event_id": "event-uuid",
    "alert_type": "competitor",
    "alert_text": "Competitor activity detected: Acme Corp",
    "severity": "medium",
    "status": "active",
    "timestamp": "2025-01-15T10:00:00Z"
  }
]
```

#### Get Alerts

```http
GET /ner/alerts?alert_type=competitor&severity=high&status=active&limit=100
```

**Query Parameters:**
- `alert_type` (optional): Filter by alert type
- `severity` (optional): Filter by severity (low, medium, high)
- `status` (optional): Filter by status (active, acknowledged, resolved)
- `limit` (optional): Maximum number of results (default: 100)

**Response:**
```json
[
  {
    "id": "alert-uuid",
    "rule_id": "rule-uuid",
    "event_id": "event-uuid",
    "alert_type": "competitor",
    "alert_text": "Competitor activity detected: Acme Corp",
    "severity": "high",
    "status": "active",
    "timestamp": "2025-01-15T10:00:00Z"
  }
]
```

#### Get Patterns

```http
GET /ner/patterns?entity_id={entity_id}&pattern_code=CAUSE_EFFECT&limit=100
```

**Query Parameters:**
- `entity_id` (optional): Filter by entity ID
- `pattern_code` (optional): Filter by pattern code (CAUSE_EFFECT, SPATIAL_RELATIONSHIPS, etc.)
- `limit` (optional): Maximum number of results (default: 100)

**Response:**
```json
[
  {
    "id": "pattern-uuid",
    "entity_id": "entity-uuid",
    "pattern_code": "CAUSE_EFFECT",
    "confidence": 0.8,
    "context": "Entity has 3 outgoing causal relationships"
  }
]
```

#### Get Relationships

```http
GET /ner/relationships?entity_id={entity_id}&relationship_type=partnership&include_judgment=false&limit=100
```

**Query Parameters:**
- `entity_id` (optional): Filter by entity ID (source or target)
- `relationship_type` (optional): Filter by relationship type
- `include_judgment` (optional, default=false): Include judgment fields in response
- `limit` (optional): Maximum number of results (default: 100)

**Response:**
```json
[
  {
    "source_entity": "Acme Corp",
    "target_entity": "Tech Ventures",
    "relationship_type": "partnership",
    "confidence": 0.85
  }
]
```

#### Analyze Relationship

```http
POST /ner/relationships/analyze
```

**Request Body:**
```json
{
  "relationship_id": "uuid",
  "include_history": false
}
```

**Response:**
```json
{
  "polarity_score": -0.65,
  "polarity_label": "adversarial",
  "confidence": 0.85,
  "explanation": "Rapidly deteriorating relationship with escalating conflicts, trust broken, defensive and angry interactions, high risk of termination.",
  "top_evidence": [
    {
      "type": "history",
      "description": "8 conflicts in 10 interactions, all recent",
      "weight": 0.35
    }
  ],
  "contextual_features": {
    "relationship_history": {
      "interaction_count": 10,
      "cooperation_count": 2,
      "conflict_count": 8,
      "trajectory": "declining"
    },
    "emotional_state": "angry",
    "risk_level": "high"
  },
  "judged_at": "2025-01-15T10:30:00Z",
  "judgment_version": "1.0"
}
```

#### Get Relationship Judgment

```http
GET /ner/relationships/{relationship_id}/judgment
```

**Response:** Same format as POST /ner/relationships/analyze

#### Batch Analyze Relationships

```http
POST /ner/relationships/batch-analyze
```

**Request Body:**
```json
{
  "relationship_ids": ["uuid1", "uuid2", ...],
  "include_history": false
}
```

**Response:** List of relationship judgments (same format as single analyze)

### Health Endpoints

#### Get Health Status

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

#### Get Detailed Health Status

```http
GET /health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "checks": {
    "database": "healthy"
  }
}
```

### User Management Endpoints

#### Get All Users

```http
GET /users?skip=0&limit=100
```

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_active": true
  }
]
```

#### Get User by ID

```http
GET /users/{user_id}
```

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_active": true
}
```

#### Create User

```http
POST /users
```

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "id": 2,
  "username": "newuser",
  "email": "newuser@example.com",
  "is_active": true
}
```

#### Update User

```http
PUT /users/{user_id}
```

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "username": "updateduser",
  "email": "updated@example.com",
  "password": "newpassword"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "updateduser",
  "email": "updated@example.com",
  "is_active": true
}
```

#### Delete User

```http
DELETE /users/{user_id}
```

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

## Data Models

### User Model

```json
{
  "id": "integer",
  "username": "string (max 50 characters)",
  "email": "string (max 100 characters)",
  "is_active": "boolean",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

### CreateUserRequest Model

```json
{
  "username": "string (required, max 50 characters)",
  "email": "string (required, max 100 characters, valid email)",
  "password": "string (required, min 8 characters)"
}
```

## Error Handling

### Error Response Format

All errors return a consistent format:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

### Common Error Types

#### Validation Error (422)

```json
{
  "error": "ValidationError",
  "message": "Invalid request data",
  "details": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### Authentication Error (401)

```json
{
  "error": "AuthenticationError",
  "message": "Could not validate credentials",
  "error_code": "INVALID_TOKEN"
}
```

#### Authorization Error (403)

```json
{
  "error": "AuthorizationError",
  "message": "Insufficient permissions",
  "error_code": "PERMISSION_DENIED"
}
```

#### Not Found Error (404)

```json
{
  "error": "NotFoundError",
  "message": "User not found",
  "error_code": "USER_NOT_FOUND"
}
```

#### Conflict Error (409)

```json
{
  "error": "ConflictError",
  "message": "User with this username or email already exists",
  "error_code": "USER_EXISTS"
}
```

#### Rate Limit Error (429)

```json
{
  "error": "RateLimitError",
  "message": "Rate limit exceeded",
  "error_code": "TOO_MANY_REQUESTS"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Default Limit**: 100 requests per minute per IP
- **Authenticated Users**: Higher limits based on user role
- **Headers**: Rate limit information included in response headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Pagination

List endpoints support pagination using query parameters:

- `skip`: Number of items to skip (default: 0)
- `limit`: Maximum number of items to return (default: 100, max: 1000)

**Example:**
```http
GET /users?skip=20&limit=10
```

**Response Headers:**
```http
X-Total-Count: 150
X-Page-Count: 15
```

## Filtering and Sorting

### Filtering

List endpoints support filtering using query parameters:

```http
GET /users?is_active=true&email_contains=example.com
```

### Sorting

Sort results using the `sort` parameter:

```http
GET /users?sort=username:asc
GET /users?sort=created_at:desc
```

## Request Headers

### Standard Headers

- `Content-Type: application/json` (for POST/PUT requests)
- `Authorization: Bearer <token>` (for authenticated endpoints)

### Optional Headers

- `X-Request-ID`: Unique request identifier (generated automatically)
- `Accept-Language`: Preferred response language

### Response Headers

- `X-Request-ID`: Request identifier
- `X-Process-Time`: Request processing time in seconds
- `X-RateLimit-*`: Rate limiting information

## CORS

The API supports Cross-Origin Resource Sharing (CORS):

- **Allowed Origins**: Configured via `API__CORS_ORIGINS` setting
- **Allowed Methods**: GET, POST, PUT, DELETE, OPTIONS
- **Allowed Headers**: Content-Type, Authorization
- **Credentials**: Supported

## Webhooks

The framework supports webhook notifications for events:

### Webhook Events

- `user.created`: New user created
- `user.updated`: User updated
- `user.deleted`: User deleted

### Webhook Configuration

Configure webhooks via environment variables:

```bash
WEBHOOK__URL=https://your-webhook-endpoint.com
WEBHOOK__SECRET=your-webhook-secret
WEBHOOK__EVENTS=user.created,user.updated
```

## API Versioning

The API supports versioning through URL paths:

- **Current Version**: v1 (default)
- **Future Versions**: v2, v3, etc.

**Example:**
```http
GET /v1/users
```

## OpenAPI Documentation

Interactive API documentation is available:

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

## SDK and Client Libraries

### Python Client

```python
from python_framework_client import FrameworkClient

client = FrameworkClient(base_url="http://localhost:8000")
client.set_token("your-access-token")

users = client.users.list()
user = client.users.get(1)
```

### JavaScript Client

```javascript
import { FrameworkClient } from 'python-framework-client';

const client = new FrameworkClient('http://localhost:8000');
client.setToken('your-access-token');

const users = await client.users.list();
const user = await client.users.get(1);
```

## Testing the API

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Get users (with token)
curl -H "Authorization: Bearer <token>" http://localhost:8000/users/

# Create user
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"username": "test", "email": "test@example.com", "password": "password"}'
```

### Using Postman

Import the OpenAPI specification into Postman:

1. Go to `/openapi.json` in your browser
2. Copy the JSON
3. In Postman: Import > Raw text > Paste JSON
4. The API collection will be created automatically

## Best Practices

### Authentication

- Always use HTTPS in production
- Store tokens securely on the client
- Implement token refresh logic
- Handle token expiration gracefully

### Error Handling

- Check HTTP status codes before processing response
- Parse error messages from response body
- Implement retry logic for transient errors
- Log errors for debugging

### Performance

- Use pagination for large datasets
- Implement caching for frequently accessed data
- Compress request/response payloads
- Use connection pooling

### Security

- Validate all input data
- Sanitize user inputs
- Implement proper access controls
- Log security events
