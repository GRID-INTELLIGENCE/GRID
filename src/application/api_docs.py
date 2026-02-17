"""
API Documentation Generator for GRID.

Generates comprehensive OpenAPI/Swagger documentation from FastAPI applications.
Includes interactive Swagger UI, ReDoc, and exportable HTML documentation.

Usage:
    from application.api_docs import setup_api_docs, export_openapi_spec

    app = FastAPI()
    setup_api_docs(
        app,
        title="GRID API",
        version="2.2.0",
        description="Enterprise AI framework with local-first RAG"
    )

    # Export to file
    export_openapi_spec(app, "docs/openapi.json")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse


def setup_api_docs(
    app: FastAPI,
    title: str = "GRID API",
    version: str = "2.2.0",
    description: str | None = None,
    terms_of_service: str | None = None,
    contact: dict[str, str] | None = None,
    license_info: dict[str, str] | None = None,
    servers: list[dict[str, str]] | None = None,
    tags_metadata: list[dict[str, Any]] | None = None,
) -> None:
    """
    Setup comprehensive API documentation for FastAPI application.

    Args:
        app: FastAPI application instance
        title: API title
        version: API version
        description: Detailed description
        terms_of_service: Terms of service URL
        contact: Contact information
        license_info: License information
        servers: List of servers
        tags_metadata: Metadata for API tags
    """

    # Default description if not provided
    if description is None:
        description = """
## GRID - Geometric Resonance Intelligence Driver

Enterprise-grade AI framework with:
- **Local-First RAG**: ChromaDB + Ollama (zero cloud dependencies)
- **Event-Driven Architecture**: Unified Fabric async pub/sub
- **Cognitive Decision Support**: Bounded rationality framework
- **Production Security**: JWT auth, token revocation, path validation
- **Agentic System**: Receptionist-Lawyer-Client workflow
- **26+ Intelligent Skills**: Auto-discovery with 0.1ms SLA

### Authentication

All authenticated endpoints require a Bearer token:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.grid.example.com/api/v1/users/me
```

### Rate Limiting

- **Free Tier**: 100 requests/hour
- **Basic Tier**: 1,000 requests/hour
- **Professional Tier**: 10,000 requests/hour
- **Enterprise Tier**: Unlimited

### Error Codes

- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid or missing token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error
- `503` - Service Unavailable

### Versioning

API versioning via URL path: `/api/v1/`, `/api/v2/`, etc.

Breaking changes will increment the major version number.
"""

    # Default contact
    if contact is None:
        contact = {
            "name": "GRID Support",
            "url": "https://github.com/yourusername/grid",
            "email": "irfankabir02@gmail.com",
        }

    # Default license
    if license_info is None:
        license_info = {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        }

    # Default servers
    if servers is None:
        servers = [
            {"url": "http://localhost:8080", "description": "Development server"},
            {"url": "https://api.grid.example.com", "description": "Production server"},
        ]

    # Default tags metadata
    if tags_metadata is None:
        tags_metadata = [
            {
                "name": "Authentication",
                "description": "User authentication and authorization",
            },
            {
                "name": "Users",
                "description": "User management operations",
            },
            {
                "name": "Billing",
                "description": "Subscription and billing management",
            },
            {
                "name": "RAG",
                "description": "Retrieval-Augmented Generation queries",
            },
            {
                "name": "Skills",
                "description": "Intelligent skill execution",
            },
            {
                "name": "Agentic",
                "description": "Agentic system case management",
            },
            {
                "name": "Events",
                "description": "Event bus operations",
            },
            {
                "name": "Health",
                "description": "Health check and monitoring",
            },
        ]

    # Custom OpenAPI schema generator
    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=title,
            version=version,
            description=description,
            routes=app.routes,
            servers=servers,
            terms_of_service=terms_of_service,
            contact=contact,
            license_info=license_info,
            tags=tags_metadata,
        )

        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your JWT token",
            }
        }

        # Add global security requirement
        openapi_schema["security"] = [{"BearerAuth": []}]

        # Add custom extensions
        openapi_schema["x-logo"] = {
            "url": "https://example.com/logo.png",
            "altText": "GRID Logo",
        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore

    # Enable ReDoc
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html() -> HTMLResponse:
        """Serve ReDoc documentation."""
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{title} - ReDoc</title>
                <meta charset="utf-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                    }}
                </style>
            </head>
            <body>
                <redoc spec-url="/openapi.json"></redoc>
                <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
            </body>
            </html>
            """
        )


def export_openapi_spec(app: FastAPI, output_path: str | Path) -> None:
    """
    Export OpenAPI specification to JSON file.

    Args:
        app: FastAPI application instance
        output_path: Path to save JSON file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate OpenAPI schema
    openapi_schema = app.openapi()

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)


def export_html_docs(app: FastAPI, output_path: str | Path) -> None:
    """
    Export standalone HTML documentation.

    Args:
        app: FastAPI application instance
        output_path: Path to save HTML file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get OpenAPI schema
    openapi_schema = app.openapi()
    schema_json = json.dumps(openapi_schema, indent=2, ensure_ascii=False)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{openapi_schema.get("info", {}).get("title", "API Documentation")}</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <style>
            body {{
                margin: 0;
                padding: 0;
            }}
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {{
                const spec = {schema_json};

                window.ui = SwaggerUIBundle({{
                    spec: spec,
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout"
                }});
            }};
        </script>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)


def add_example_responses(
    app: FastAPI,
    endpoint: str,
    method: str,
    status_code: int,
    examples: dict[str, Any],
) -> None:
    """
    Add example responses to OpenAPI schema.

    Args:
        app: FastAPI application
        endpoint: Endpoint path
        method: HTTP method (get, post, etc.)
        status_code: HTTP status code
        examples: Dictionary of examples
    """
    openapi_schema = app.openapi()

    # Navigate to the specific endpoint
    if endpoint in openapi_schema.get("paths", {}):
        endpoint_schema = openapi_schema["paths"][endpoint]
        if method in endpoint_schema:
            method_schema = endpoint_schema[method]
            if "responses" not in method_schema:
                method_schema["responses"] = {}
            if str(status_code) not in method_schema["responses"]:
                method_schema["responses"][str(status_code)] = {}

            # Add examples
            method_schema["responses"][str(status_code)]["content"] = {"application/json": {"examples": examples}}

    # Update schema
    app.openapi_schema = openapi_schema
