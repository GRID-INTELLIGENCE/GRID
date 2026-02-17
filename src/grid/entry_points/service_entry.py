"""Service entry point with tracing and context."""

from typing import Any

from grid.organization.org_manager import OrganizationManager
from grid.tracing import TraceManager, TraceOrigin, get_trace_manager


class ServiceEntryPoint:
    """Optimized service entry point with tracing and context."""

    def __init__(
        self,
        trace_manager: TraceManager | None = None,
        org_manager: OrganizationManager | None = None,
    ):
        """Initialize service entry point.

        Args:
            trace_manager: Optional trace manager
            org_manager: Optional organization manager
        """
        self.trace_manager = trace_manager or get_trace_manager()
        self.org_manager = org_manager or OrganizationManager()

    def handle_service_call(
        self,
        service: str,
        method: str,
        params: dict[str, Any],
        user_id: str | None = None,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        """Handle a service call with full tracing.

        Args:
            service: Service name
            method: Method name
            params: Method parameters
            user_id: Optional user ID
            org_id: Optional organization ID

        Returns:
            Service result
        """
        action_name = f"{service}.{method}"

        # Create trace
        with self.trace_manager.trace_action(
            action_type="service_call",
            action_name=action_name,
            origin=TraceOrigin.INTERNAL_PIPELINE,
            user_id=user_id,
            org_id=org_id,
            input_data=params,
        ) as trace:
            # Check permissions
            if user_id and not self.org_manager.check_user_permission(user_id, action_name, org_id):
                trace.complete(success=False, error="Permission denied")
                return {"success": False, "error": "Permission denied"}

            # Record activity
            if user_id:
                self.org_manager.record_user_activity(user_id)

            # Process service call
            try:
                result = self._process_service_call(service, method, params, trace)
                trace.complete(success=True, output_data=result)
                return {"success": True, "data": result, "trace_id": trace.trace_id}
            except Exception as e:
                trace.complete(success=False, error=str(e))
                raise

    def _process_service_call(
        self,
        service: str,
        method: str,
        params: dict[str, Any],
        trace: Any,
    ) -> dict[str, Any]:
        """Process a service call.

        Args:
            service: Service name
            method: Method name
            params: Method parameters
            trace: Action trace

        Returns:
            Service result
        """
        # This would delegate to appropriate service
        # For now, return placeholder
        return {"service": service, "method": method, "processed": True}


def main() -> None:
    """Service entry point function."""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="GRID Service Entry Point")
    parser.add_argument("service", help="Service name")
    parser.add_argument("method", help="Method name")
    parser.add_argument("--params", type=json.loads, default={}, help="JSON parameters for the call")
    parser.add_argument("--user", help="User ID")
    parser.add_argument("--org", help="Organization ID")

    args = parser.parse_args()

    entry_point = ServiceEntryPoint()
    try:
        result = entry_point.handle_service_call(
            service=args.service,
            method=args.method,
            params=args.params,
            user_id=args.user,
            org_id=args.org,
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
