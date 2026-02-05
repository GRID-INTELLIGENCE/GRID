"""
Response generation for parasitic requests.

Creates deterministic null responses that look valid but contain
only sentinels (null, 0, empty lists) while preserving
type signatures and injecting parasite metadata.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from .models import ParasiteContext
from .config import ParasiteGuardConfig

logger = logging.getLogger(__name__)


class FractalNullFacade:
    """
    Recursively replaces all values with null sentinels while
    preserving type signatures.

    "Fractal" because it applies the null transformation at all
    nesting levels of the response structure.
    """

    NULL_SENTINEL = None

    def __init__(self, config: ParasiteGuardConfig):
        self.config = config

    def build_null_response(self, schema: Any, parasite_context: ParasiteContext) -> Dict[str, Any]:
        """
        Build a fractal null response based on schema.

        Args:
            schema: Pydantic model or dict representing expected response
            parasite_context: Context for metadata injection

        Returns:
            Dictionary with all fields nulled and parasite metadata
        """
        base_payload = self._build_null_object(schema)

        # Inject hidden parasite metadata
        base_payload["_parasite_meta"] = {
            "id": str(parasite_context.id),
            "component": parasite_context.component,
            "pattern": parasite_context.pattern,
            "detected_by": parasite_context.rule,
            "severity": parasite_context.severity.name,
            "timestamp": parasite_context.start_ts.isoformat(),
        }

        return base_payload

    def _build_null_object(self, schema: Any) -> Dict[str, Any]:
        """
        Recursively walk schema and build null object.

        Handles:
        - Pydantic BaseModel subclasses
        - TypedDict
        - Dict[str, Any]
        - Lists/Sequences
        - Nested structures
        """
        # Pydantic BaseModel
        if hasattr(schema, "__fields__"):
            result = {}
            for field_name, field_info in schema.__fields__.items():
                result[field_name] = self._null_for_type(field_info.type_)
            return result

        # Plain dict
        elif isinstance(schema, dict):
            return {k: self._null_for_type(v) for k, v in schema.items()}

        # Unknown schema, return empty dict
        else:
            return {}

    def _null_for_type(self, typ: Any) -> Any:
        """
        Map a Python/type hint to the null sentinel.

        Handles:
        - Primitives (str, int, float, bool)
        - Containers (list, dict, set, tuple)
        - Optional types
        - Union types
        - Custom classes
        """
        # Check for Optional/Union
        origin = getattr(typ, "__origin__", None)

        # Optional[T] or Union[T, None]
        if origin is Union:
            args = getattr(typ, "__args__", [])
            if type(None) in args:
                return self.NULL_SENTINEL
            # Union without None, pick first type
            return self._null_for_type(args[0]) if args else self.NULL_SENTINEL

        # Direct NoneType
        elif typ is type(None):
            return self.NULL_SENTINEL

        # Containers
        elif origin is list or origin is List:
            return []

        elif origin is dict or origin is Dict:
            return {}

        elif origin is set or origin is frozenset:
            return set()

        elif origin is tuple:
            args = getattr(typ, "__args__", [])
            return tuple(self._null_for_type(arg) if arg is not ... else self.NULL_SENTINEL for arg in args)

        # Primitives
        elif typ in (str, int, float, bool, bytes):
            return self.NULL_SENTINEL

        # Datetime types
        elif typ in (datetime,):
            return None

        # Pydantic models
        elif hasattr(typ, "__fields__"):
            return self._build_null_object(typ)

        # Unknown type, use sentinel
        else:
            return self.NULL_SENTINEL


class DummyResponseGenerator:
    """
    Generates deterministic null responses for parasitic requests.

    Workflow:
    1. Infer expected response schema from endpoint
    2. Build fractal null object preserving type signatures
    3. Inject hidden parasite metadata
    4. Return ASGI-compatible response
    """

    def __init__(self, config: ParasiteGuardConfig):
        self.config = config
        self.facade = FractalNullFacade(config)

    async def make(self, context: ParasiteContext, request: Any) -> Any:
        """
        Generate a dummy response for the parasite.

        Args:
            context: ParasiteContext from detection
            request: ASGI request object

        Returns:
            FastAPI/Starlette Response object
        """
        # 1. Infer schema from endpoint
        schema = self._infer_schema(request)

        # 2. Build fractal null payload
        payload = self.facade.build_null_response(schema, context)

        # 3. Log generation
        if self.config.log_structured:
            logger.info(
                "Generated parasite dummy response",
                extra={
                    "parasite_id": str(context.id),
                    "component": context.component,
                    "pattern": context.pattern,
                    "schema_type": self._get_schema_name(schema),
                },
            )

        # 4. Return response
        return self._create_response(payload)

    def _infer_schema(self, request: Any) -> Any:
        """
        Heuristic to infer response schema from endpoint.

        Tries:
        1. Endpoint response_model (FastAPI)
        2. Return annotation
        3. Fallback to dict
        """
        # Get endpoint from scope
        endpoint = getattr(request, "scope", {}).get("endpoint")

        if endpoint:
            # Try FastAPI response_model
            response_model = getattr(endpoint, "response_model", None)
            if response_model:
                return response_model

            # Try return annotation
            return_annotation = getattr(endpoint, "__annotations__", {}).get("return")
            if return_annotation:
                return return_annotation

        # Fallback
        return dict

    def _get_schema_name(self, schema: Any) -> str:
        """Get human-readable schema name for logging."""
        if hasattr(schema, "__name__"):
            return schema.__name__
        elif hasattr(schema, "_name"):
            return schema._name
        else:
            return str(schema)

    def _create_response(self, payload: Dict[str, Any]) -> Any:
        """
        Create ASGI response object.

        Returns FastAPI JSONResponse.
        """
        from fastapi.responses import JSONResponse

        return JSONResponse(
            content=payload,
            status_code=200,
            media_type="application/json",
        )
