import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import yaml
import os

from .contracts import (
    AccountabilityContract,
    ContractSeverity,
    EndpointContract,
    ServiceLevelObjective,
)

logger = logging.getLogger(__name__)


class ContractEnforcementResult:
    """Result of enforcing a contract on a request/response."""

    def __init__(self):
        self.violations: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {}
        self.penalty_points: int = 0
        self.is_compliant: bool = True

    def add_violation(
        self,
        field: str,
        error: str,
        message: str,
        severity: ContractSeverity = ContractSeverity.MEDIUM,
        penalty_points: int = 1,
    ) -> None:
        """Add a contract violation."""
        self.violations.append(
            {
                "field": field,
                "error": error,
                "message": message,
                "severity": severity,
                "penalty_points": penalty_points,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        self.penalty_points += penalty_points
        self.is_compliant = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "is_compliant": self.is_compliant,
            "violation_count": len(self.violations),
            "penalty_points": self.penalty_points,
            "violations": self.violations,
            "metrics": self.metrics,
        }


class AccountabilityEnforcer:
    """Enforces accountability contracts on API requests and responses."""

    def __init__(self, contract_path: str = None):
        self.contracts: Dict[str, AccountabilityContract] = {}
        self.contract_path = contract_path or "config/accountability/contracts.yaml"
        self.load_contracts()

        # Track metrics for SLO evaluation
        self.metrics_store: Dict[str, List[Tuple[datetime, float]]] = {}

    def load_contracts(self) -> None:
        """Load contracts from YAML configuration."""
        try:
            if not os.path.exists(self.contract_path):
                # Fallback to absolute path check if relative fails
                abs_path = os.path.join(os.getcwd(), self.contract_path)
                if os.path.exists(abs_path):
                    self.contract_path = abs_path
                else:
                    logger.warning(f"Contract file not found: {self.contract_path}")
                    return

            with open(self.contract_path, "r") as f:
                contract_data = yaml.safe_load(f)

            # Convert YAML to Pydantic models
            contract = AccountabilityContract(**contract_data)
            self.contracts[contract.service_name] = contract
            logger.info(f"Loaded accountability contract for {contract.service_name}")

        except Exception as e:
            logger.error(f"Failed to load accountability contracts: {e}")
            # Don't raise, just log error to allow app to start

    def get_contract_for_endpoint(self, path: str, method: str) -> Optional[EndpointContract]:
        """Get the contract for a specific endpoint."""
        for contract in self.contracts.values():
            endpoint_contract = contract.get_endpoint_contract(path, method)
            if endpoint_contract:
                return endpoint_contract
        return None

    def enforce_request(
        self,
        path: str,
        method: str,
        headers: Dict[str, str],
        body: Dict[str, Any],
        client_ip: str = None,
    ) -> ContractEnforcementResult:
        """Enforce contract on an incoming request."""
        result = ContractEnforcementResult()
        method = method.upper()

        # Find matching contract
        contract = self.get_contract_for_endpoint(path, method)
        if not contract:
            # Check if we should log missing contracts
            # result.add_violation(...)
            return result

        # Check if endpoint is enabled
        if not contract.enabled:
            result.add_violation(
                "endpoint",
                "endpoint_disabled",
                f"Endpoint {method} {path} is disabled by policy",
                ContractSeverity.HIGH,
                10,
            )
            return result

        # Validate authentication
        auth_required = contract.security.authentication_required
        if auth_required:
            if "Authorization" not in headers and "authorization" not in headers:
                result.add_violation(
                    "headers.Authorization",
                    "missing_authentication",
                    "Authentication required",
                    ContractSeverity.HIGH,
                    20,
                )

        # Check rate limiting (simplified example)
        rate_limit = contract.security.rate_limit
        if rate_limit:
            client_id = headers.get("X-Client-ID", client_ip or "unknown")
            rate_key = f"rate:{client_id}:{path}"
            current_time = datetime.utcnow()

            # Clean up old entries
            if rate_key in self.metrics_store:
                self.metrics_store[rate_key] = [
                    (ts, count)
                    for ts, count in self.metrics_store[rate_key]
                    if current_time - ts < timedelta(minutes=1)
                ]

            # Get current rate
            current_rate = sum(
                count for ts, count in self.metrics_store.get(rate_key, []) if current_time - ts < timedelta(seconds=60)
            )

            if current_rate >= rate_limit:
                result.add_violation(
                    "rate_limit",
                    "rate_limit_exceeded",
                    f"Rate limit exceeded: {current_rate}/{rate_limit} requests per minute",
                    ContractSeverity.HIGH,
                    15,
                )

            # Record this request
            if rate_key not in self.metrics_store:
                self.metrics_store[rate_key] = []
            self.metrics_store[rate_key].append((current_time, 1))

        # Validate Request Body
        if body:
            # We need to access the parent AccountabilityContract to call validate_request
            # But here we only have EndpointContract.
            # We need to change how we get the contract or pass the validation logic.
            # The AccountabilityContract has the validate_request method in the file I read.

            # Let's find the parent contract
            parent_contract = None
            for c in self.contracts.values():
                if contract in c.endpoints:
                    parent_contract = c
                    break

            if parent_contract:
                errors = parent_contract.validate_request(path, method, body)
                for error in errors:
                    result.add_violation(
                        error.get("field", "unknown"),
                        error.get("error", "validation_error"),
                        error.get("message", "Validation failed"),
                        contract.severity,
                        contract.penalty_points,
                    )

        return result

    def enforce_response(
        self,
        path: str,
        method: str,
        status_code: int,
        headers: Dict[str, str],
        body: Dict[str, Any],
    ) -> ContractEnforcementResult:
        """Enforce contract on an outgoing response."""
        result = ContractEnforcementResult()
        method = method.upper()

        # Find matching contract
        contract = self.get_contract_for_endpoint(path, method)
        if not contract:
            return result  # No contract, nothing to enforce

        # Validate response status code
        if status_code >= 500:
            result.add_violation(
                "status_code",
                "server_error",
                f"Endpoint returned server error status: {status_code}",
                ContractSeverity.HIGH,
                10,
            )
        elif status_code >= 400:
            # Client errors might be expected, but track them
            pass

        # Record performance metrics
        if hasattr(result, "request_start_time"):
            latency_ms = (datetime.utcnow() - result.request_start_time).total_seconds() * 1000
            result.metrics["latency_ms"] = latency_ms

            max_latency = contract.performance.max_latency_ms
            if max_latency and latency_ms > max_latency:
                result.add_violation(
                    "performance",
                    "latency_exceeded",
                    f"Response latency {latency_ms:.2f}ms exceeds maximum allowed {max_latency}ms",
                    ContractSeverity.MEDIUM,
                    5,
                )

        return result


# Singleton instance
enforcer = AccountabilityEnforcer()
