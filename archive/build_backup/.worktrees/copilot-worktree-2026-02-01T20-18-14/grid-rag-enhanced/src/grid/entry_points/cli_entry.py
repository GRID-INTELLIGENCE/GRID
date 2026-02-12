"""CLI entry point with tracing and context."""

from typing import Any

from grid.organization.org_manager import OrganizationManager
from grid.tracing import TraceManager, TraceOrigin, get_trace_manager


class CLIEntryPoint:
    """Optimized CLI entry point with tracing and context."""

    def __init__(
        self,
        trace_manager: TraceManager | None = None,
        org_manager: OrganizationManager | None = None,
    ):
        """Initialize CLI entry point.

        Args:
            trace_manager: Optional trace manager
            org_manager: Optional organization manager
        """
        self.trace_manager = trace_manager or get_trace_manager()
        self.org_manager = org_manager or OrganizationManager()

    def handle_command(
        self,
        command: str,
        args: dict[str, Any],
        user_id: str | None = None,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        """Handle a CLI command with full tracing.

        Args:
            command: Command name
            args: Command arguments
            user_id: Optional user ID
            org_id: Optional organization ID

        Returns:
            Command result
        """
        # Create trace
        with self.trace_manager.trace_action(
            action_type="cli_command",
            action_name=command,
            origin=TraceOrigin.USER_INPUT,
            user_id=user_id,
            org_id=org_id,
            input_data=args,
        ) as trace:
            # Check permissions
            if user_id and not self.org_manager.check_user_permission(user_id, command, org_id):
                trace.complete(success=False, error="Permission denied")
                return {"success": False, "error": "Permission denied"}

            # Record activity
            if user_id:
                self.org_manager.record_user_activity(user_id)

            # Process command
            try:
                result = self._process_command(command, args, trace)
                trace.complete(success=True, output_data=result)
                return {"success": True, "data": result, "trace_id": trace.trace_id}
            except Exception as e:
                trace.complete(success=False, error=str(e))
                raise

    def _process_command(
        self,
        command: str,
        args: dict[str, Any],
        trace: Any,
    ) -> dict[str, Any]:
        """Process a command.

        Args:
            command: Command name
            args: Command arguments
            trace: Action trace

        Returns:
            Command result
        """
        # This would delegate to appropriate service
        # For now, return placeholder
        return {"command": command, "processed": True}


def main() -> None:
    """CLI entry point function."""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="GRID CLI Entry Point")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("--args", type=json.loads, default={}, help="JSON arguments for the command")
    parser.add_argument("--user", help="User ID")
    parser.add_argument("--org", help="Organization ID")

    args = parser.parse_args()

    entry_point = CLIEntryPoint()
    try:
        result = entry_point.handle_command(
            command=args.command,
            args=args.args,
            user_id=args.user,
            org_id=args.org,
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
