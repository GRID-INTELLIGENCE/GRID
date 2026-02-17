"""
Enhanced Accountability Enforcer with claims/roles support.
"""

import logging
from collections import deque
from datetime import datetime, timezone, timedelta
from typing import Any

from .contract_loader import load_accountability_contract
from .contracts import (
    AccountabilityContract,
    ContractSeverity,
    ContractViolation,
    EnforcementResult,
    ViolationType,
)

logger = logging.getLogger(__name__)

_ERROR_RATE_WINDOW = timedelta(minutes=5)
_MAX_OUTCOMES_PER_ENDPOINT = 1000


class EnhancedAccountabilityEnforcer:
    """Enhanced accountability enforcer with RBAC and claims support."""

    def __init__(
        self,
        enforcement_mode: str = "monitor",  # monitor, enforce, disabled
        contract_path: str | None = None,
    ):
        """Initialize enhanced enforcer.

        Args:
            enforcement_mode: How to handle violations (monitor/enforce/disabled)
            contract_path: Path to contract file (optional)
        """
        self.enforcement_mode = enforcement_mode
        self.contract_path = contract_path
        self._contract: AccountabilityContract | None = None
        self._rbac_helper = None

        # Rate limiting store: {rate_key: [timestamps]}
        self._rate_limit_store: dict[str, list[datetime]] = {}
        # Error rate tracking: {endpoint_key: deque of (timestamp, is_success)}
        self._error_tracking: dict[str, deque[tuple[datetime, bool]]] = {}

        logger.info(f"Enhanced accountability enforcer initialized: mode={enforcement_mode}")

    def _get_contract(self) -> AccountabilityContract:
        """Get loaded contract, lazy loading if needed."""
        if self._contract is None:
            self._contract = load_accountability_contract()
        return self._contract

    def _get_rbac_helper(self):
        """Get RBAC helper for role/permission checking."""
        if self._rbac_helper is None:
            try:
                from application.mothership.security.rbac import ROLE_PERMISSIONS, Permission, Role

                self._rbac_helper = {
                    "ROLE_PERMISSIONS": ROLE_PERMISSIONS,
                    "Permission": Permission,
                    "Role": Role,
                }
            except ImportError:
                logger.warning("RBAC module not available, role checking disabled")
                self._rbac_helper = {}
        return self._rbac_helper

    def enforce_request(
        self,
        path: str,
        method: str,
        auth_context: dict[str, Any] | None = None,
        request_data: dict[str, Any] | None = None,
        client_ip: str | None = None,
    ) -> EnforcementResult:
        """Enforce accountability contract for a request.

        Args:
            path: Request path
            method: HTTP method
            auth_context: Authentication context with roles/permissions
            request_data: Request payload data
            client_ip: Client IP address

        Returns:
            EnforcementResult with violations and actions taken
        """
        contract = self._get_contract()
        violations = []
        actions_taken = []

        # Find matching endpoint contract
        endpoint_contract = contract.get_endpoint_contract(path, method)
        if not endpoint_contract:
            violations.append(
                ContractViolation(
                    type=ViolationType.SECURITY,
                    severity=ContractSeverity.MEDIUM,
                    message=f"No contract found for {method} {path}",
                    field="endpoint_contract",
                    actual_value=f"{method} {path}",
                    expected_value="defined_contract",
                    penalty_points=5,
                )
            )
            return EnforcementResult(
                allowed=self.enforcement_mode == "monitor",
                violations=violations,
                actions_taken=actions_taken,
                enforcement_mode=self.enforcement_mode,
            )

        # Check authentication requirements
        auth_violations = self._check_authentication_requirements(endpoint_contract, auth_context)
        violations.extend(auth_violations)

        # Check authorization (roles/permissions)
        authz_violations = self._check_authorization_requirements(endpoint_contract, auth_context)
        violations.extend(authz_violations)

        # Check IP whitelist
        ip_violations = self._check_ip_requirements(endpoint_contract, client_ip)
        violations.extend(ip_violations)

        # Check rate limiting
        rate_violations = self._check_rate_limiting(endpoint_contract, client_ip, path)
        violations.extend(rate_violations)

        # Check request validation
        if request_data:
            validation_violations = self._check_request_validation(endpoint_contract, request_data)
            violations.extend(validation_violations)

        # Determine if request should be allowed
        critical_violations = [v for v in violations if v.severity == ContractSeverity.CRITICAL]
        high_violations = [v for v in violations if v.severity == ContractSeverity.HIGH]

        if self.enforcement_mode == "enforce":
            # Block on critical or high severity violations
            allowed = len(critical_violations) == 0 and len(high_violations) == 0
            if not allowed:
                actions_taken.append(
                    f"Blocked due to {len(critical_violations)} critical and {len(high_violations)} high severity violations"
                )
        else:
            # Monitor mode - always allow but log violations
            allowed = True
            if violations:
                actions_taken.append(f"Logged {len(violations)} violations in monitor mode")

        return EnforcementResult(
            allowed=allowed,
            violations=violations,
            actions_taken=actions_taken,
            enforcement_mode=self.enforcement_mode,
            endpoint_contract=endpoint_contract,
        )

    def enforce_response(
        self,
        path: str,
        method: str,
        response_data: dict[str, Any] | None = None,
        response_status: int = 200,
        response_time_ms: float | None = None,
    ) -> EnforcementResult:
        """Enforce accountability contract for a response.

        Args:
            path: Request path
            method: HTTP method
            response_data: Response payload data
            response_status: HTTP status code
            response_time_ms: Response time in milliseconds

        Returns:
            EnforcementResult with violations and actions taken
        """
        contract = self._get_contract()
        violations = []
        actions_taken = []

        # Find matching endpoint contract
        endpoint_contract = contract.get_endpoint_contract(path, method)
        if not endpoint_contract:
            return EnforcementResult(
                allowed=True,  # Response violations don't block
                violations=[],
                actions_taken=[],
                enforcement_mode=self.enforcement_mode,
            )

        # Check response validation
        if response_data:
            validation_violations = self._check_response_validation(endpoint_contract, response_data)
            violations.extend(validation_violations)

        # Record outcome for error rate metrics before checking
        self._record_outcome(path, method, response_status)

        # Check performance SLA
        if response_time_ms:
            performance_violations = self._check_performance_sla(
                endpoint_contract, path, method, response_time_ms, response_status
            )
            violations.extend(performance_violations)

        # Response violations don't block but are logged
        if violations:
            actions_taken.append(f"Logged {len(violations)} response violations")

        return EnforcementResult(
            allowed=True,  # Responses are never blocked
            violations=violations,
            actions_taken=actions_taken,
            enforcement_mode=self.enforcement_mode,
            endpoint_contract=endpoint_contract,
        )

    def _check_authentication_requirements(
        self,
        endpoint_contract,
        auth_context: dict[str, Any] | None,
    ) -> list[ContractViolation]:
        """Check authentication requirements."""
        violations = []

        if endpoint_contract.security.authentication_required:
            if not auth_context or not auth_context.get("authenticated", False):
                violations.append(
                    ContractViolation(
                        type=ViolationType.SECURITY,
                        severity=ContractSeverity.HIGH,
                        message="Authentication required but not provided",
                        field="authentication",
                        actual_value="not_authenticated",
                        expected_value="authenticated",
                        penalty_points=25,
                    )
                )

        return violations

    def _check_authorization_requirements(
        self,
        endpoint_contract,
        auth_context: dict[str, Any] | None,
    ) -> list[ContractViolation]:
        """Check authorization (roles/permissions) requirements."""
        violations = []

        if not auth_context or not auth_context.get("authenticated", False):
            return violations  # Skip authz if not authenticated

        rbac = self._get_rbac_helper()
        if not rbac:
            return violations  # Skip if RBAC not available

        user_roles = auth_context.get("roles", [])
        user_permissions = auth_context.get("permissions", [])

        # Check required roles
        required_roles = endpoint_contract.security.required_roles
        if required_roles:
            missing_roles = []
            for role in required_roles:
                if role not in user_roles:
                    missing_roles.append(role)

            if missing_roles:
                violations.append(
                    ContractViolation(
                        type=ViolationType.SECURITY,
                        severity=ContractSeverity.HIGH,
                        message=f"Missing required roles: {missing_roles}",
                        field="authorization",
                        actual_value=user_roles,
                        expected_value=required_roles,
                        penalty_points=30,
                    )
                )

        # Check required permissions
        required_permissions = endpoint_contract.security.required_permissions
        if required_permissions:
            # Calculate user's effective permissions from roles
            effective_permissions = set()
            for role in user_roles:
                role_enum = rbac["Role"](role) if role in [r.value for r in rbac["Role"]] else None
                if role_enum and role_enum in rbac["ROLE_PERMISSIONS"]:
                    effective_permissions.update(rbac["ROLE_PERMISSIONS"][role_enum])

            # Add explicit permissions
            effective_permissions.update(user_permissions)

            missing_permissions = []
            for permission in required_permissions:
                if permission not in effective_permissions:
                    missing_permissions.append(permission)

            if missing_permissions:
                violations.append(
                    ContractViolation(
                        type=ViolationType.SECURITY,
                        severity=ContractSeverity.HIGH,
                        message=f"Missing required permissions: {missing_permissions}",
                        field="authorization",
                        actual_value=list(effective_permissions),
                        expected_value=required_permissions,
                        penalty_points=25,
                    )
                )

        return violations

    def _check_ip_requirements(
        self,
        endpoint_contract,
        client_ip: str | None,
    ) -> list[ContractViolation]:
        """Check IP whitelist requirements."""
        violations = []

        ip_whitelist = endpoint_contract.security.ip_whitelist
        if ip_whitelist and client_ip:
            # Simple IP check (could be enhanced with CIDR support)
            if client_ip not in ip_whitelist:
                violations.append(
                    ContractViolation(
                        type=ViolationType.SECURITY,
                        severity=ContractSeverity.MEDIUM,
                        message=f"Client IP {client_ip} not in whitelist",
                        field="ip_address",
                        actual_value=client_ip,
                        expected_value=ip_whitelist,
                        penalty_points=15,
                    )
                )

        return violations

    def _check_rate_limiting(
        self,
        endpoint_contract,
        client_ip: str | None,
        path: str,
    ) -> list[ContractViolation]:
        """Check rate limiting requirements."""
        violations = []

        rate_limit = endpoint_contract.security.rate_limit
        if not rate_limit or not client_ip:
            return violations

        current_time = datetime.now(timezone.utc)
        rate_key = f"rate:{client_ip}:{path}"

        # Clean old entries (older than 60 seconds)
        if rate_key in self._rate_limit_store:
            self._rate_limit_store[rate_key] = [
                ts for ts in self._rate_limit_store[rate_key] if (current_time - ts).total_seconds() < 60
            ]

        # Check current rate
        current_count = len(self._rate_limit_store.get(rate_key, []))
        if current_count >= rate_limit:
            violations.append(
                ContractViolation(
                    type=ViolationType.RATE_LIMIT,
                    severity=ContractSeverity.HIGH,
                    message=f"Rate limit exceeded: {current_count}/{rate_limit} requests per minute",
                    field="rate_limit",
                    actual_value=current_count,
                    expected_value=f"<{rate_limit}",
                    penalty_points=15,
                )
            )
            return violations

        # Record this request
        if rate_key not in self._rate_limit_store:
            self._rate_limit_store[rate_key] = []
        self._rate_limit_store[rate_key].append(current_time)

        return violations

    def _check_request_validation(
        self,
        endpoint_contract,
        request_data: dict[str, Any],
    ) -> list[ContractViolation]:
        """Check request data validation."""
        violations = []

        # Use parent contract for validation (validate_request is on AccountabilityContract)
        contract = self._get_contract()
        validation_errors = contract.validate_request(
            endpoint_contract.path, endpoint_contract.methods[0] if endpoint_contract.methods else "GET", request_data
        )

        for error in validation_errors:
            violations.append(
                ContractViolation(
                    type=ViolationType.DATA_VALIDATION,
                    severity=ContractSeverity.MEDIUM,
                    message=error.get("message", "Validation error"),
                    field=error.get("field", "unknown"),
                    actual_value=error.get("actual_value"),
                    expected_value=error.get("expected_value"),
                    penalty_points=10,
                )
            )

        return violations

    def _check_response_validation(
        self,
        endpoint_contract,
        response_data: dict[str, Any],
    ) -> list[ContractViolation]:
        """Check response data validation."""
        violations = []

        # Use parent contract for validation (validate_response is on AccountabilityContract)
        contract = self._get_contract()
        validation_errors = contract.validate_response(
            endpoint_contract.path, endpoint_contract.methods[0] if endpoint_contract.methods else "GET", response_data
        )

        for error in validation_errors:
            violations.append(
                ContractViolation(
                    type=ViolationType.DATA_VALIDATION,
                    severity=ContractSeverity.MEDIUM,
                    message=error.get("message", "Response validation error"),
                    field=error.get("field", "unknown"),
                    actual_value=error.get("actual_value"),
                    expected_value=error.get("expected_value"),
                    penalty_points=5,
                )
            )

        return violations

    def _endpoint_key(self, path: str, method: str) -> str:
        """Build endpoint key for metrics."""
        return f"{method}:{path}"

    def _record_outcome(self, path: str, method: str, response_status: int) -> None:
        """Record request outcome for error rate calculation."""
        key = self._endpoint_key(path, method)
        if key not in self._error_tracking:
            self._error_tracking[key] = deque(maxlen=_MAX_OUTCOMES_PER_ENDPOINT)
        is_success = 200 <= (response_status or 0) < 400
        now = datetime.now(timezone.utc)
        self._error_tracking[key].append((now, is_success))

    def _get_error_rate(self, path: str, method: str) -> float | None:
        """Get recent error rate for endpoint (0-1). Returns None if insufficient data."""
        key = self._endpoint_key(path, method)
        outcomes = self._error_tracking.get(key)
        if not outcomes or len(outcomes) < 10:
            return None
        cutoff = datetime.now(timezone.utc) - _ERROR_RATE_WINDOW
        recent = [(ts, ok) for ts, ok in outcomes if ts >= cutoff]
        if len(recent) < 10:
            return None
        errors = sum(1 for _, ok in recent if not ok)
        return errors / len(recent)

    def _check_performance_sla(
        self,
        endpoint_contract,
        path: str,
        method: str,
        response_time_ms: float,
        response_status: int,
    ) -> list[ContractViolation]:
        """Check performance SLA requirements."""
        violations = []

        performance = endpoint_contract.performance

        # Check latency
        if response_time_ms > performance.max_latency_ms:
            violations.append(
                ContractViolation(
                    type=ViolationType.PERFORMANCE,
                    severity=ContractSeverity.MEDIUM,
                    message=f"Response time {response_time_ms}ms exceeds SLA {performance.max_latency_ms}ms",
                    field="latency_ms",
                    actual_value=response_time_ms,
                    expected_value=f"≤{performance.max_latency_ms}",
                    penalty_points=15,
                )
            )

        # Check error rate with metrics
        error_rate = self._get_error_rate(path, method)
        if error_rate is not None and error_rate > performance.max_error_rate:
            violations.append(
                ContractViolation(
                    type=ViolationType.PERFORMANCE,
                    severity=ContractSeverity.MEDIUM,
                    message=f"Error rate {error_rate:.2%} exceeds SLA {performance.max_error_rate:.2%}",
                    field="error_rate",
                    actual_value=f"{error_rate:.2%}",
                    expected_value=f"≤{performance.max_error_rate:.2%}",
                    penalty_points=15,
                )
            )

        return violations


# Global enhanced enforcer instance
_global_enhanced_enforcer: EnhancedAccountabilityEnforcer | None = None


def get_enhanced_accountability_enforcer() -> EnhancedAccountabilityEnforcer:
    """Get global enhanced accountability enforcer instance."""
    global _global_enhanced_enforcer
    if _global_enhanced_enforcer is None:
        _global_enhanced_enforcer = EnhancedAccountabilityEnforcer()
    return _global_enhanced_enforcer


def set_enhanced_accountability_enforcer(enforcer: EnhancedAccountabilityEnforcer) -> None:
    """Set global enhanced accountability enforcer instance."""
    global _global_enhanced_enforcer
    _global_enhanced_enforcer = enforcer
