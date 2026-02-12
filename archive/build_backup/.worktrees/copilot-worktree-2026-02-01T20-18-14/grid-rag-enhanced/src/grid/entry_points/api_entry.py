"""API entry point with tracing and context."""

from typing import Any

from fastapi import Request

from grid.organization.org_manager import OrganizationManager
from grid.tracing import TraceManager, TraceOrigin, get_trace_manager


class APIEntryPoint:
    """Optimized API entry point with tracing and context."""

    def __init__(
        self,
        trace_manager: TraceManager | None = None,
        org_manager: OrganizationManager | None = None,
    ):
        """Initialize API entry point.

        Args:
            trace_manager: Optional trace manager
            org_manager: Optional organization manager
        """
        self.trace_manager = trace_manager or get_trace_manager()
        self.org_manager = org_manager or OrganizationManager()

    async def handle_request(
        self,
        request: Request,
        operation: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle an API request with full tracing.

        Args:
            request: FastAPI request
            operation: Operation name
            data: Request data

        Returns:
            Response data
        """
        # Extract context
        user_id = getattr(request.state, "user_id", None)
        org_id = getattr(request.state, "org_id", None)
        session_id = getattr(request.state, "session_id", None)
        request_id = request.headers.get("X-Request-ID") or getattr(request.state, "request_id", None)

        # Create trace
        with self.trace_manager.trace_action(
            action_type="api_request",
            action_name=operation,
            origin=TraceOrigin.API_REQUEST,
            user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            request_id=request_id,
            input_data=data,
        ) as trace:
            # Check permissions
            if user_id and not self.org_manager.check_user_permission(user_id, operation, org_id):
                trace.complete(success=False, error="Permission denied")
                return {"success": False, "error": "Permission denied"}

            # Record activity
            if user_id:
                self.org_manager.record_user_activity(user_id)

            # Process operation
            try:
                result = await self._process_operation(operation, data, trace)
                trace.complete(success=True, output_data=result)
                return {"success": True, "data": result, "trace_id": trace.trace_id}
            except Exception as e:
                trace.complete(success=False, error=str(e))
                raise

    async def _process_operation(
        self,
        operation: str,
        data: dict[str, Any],
        trace: Any,
    ) -> dict[str, Any]:
        """Process an operation.

        Args:
            operation: Operation name
            data: Operation data
            trace: Action trace

        Returns:
            Operation result
        """
        # This would delegate to appropriate service
        # For now, return placeholder
        return {"operation": operation, "processed": True}


def main() -> None:
    """API entry point function (placeholder for CLI execution)."""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="GRID API Entry Point Wrapper")
    parser.add_argument("operation", help="Operation to execute")
    parser.add_argument("--data", type=json.loads, default={}, help="JSON data for the operation")

    args = parser.parse_args()

    # Note: handle_request requires a FastAPI Request object.
    # This main() is a skeletal wrapper.
    print(f"Executing API operation: {args.operation}", file=sys.stderr)
    print(json.dumps({"success": True, "note": "API entry point requires FastAPI context"}, indent=2))
