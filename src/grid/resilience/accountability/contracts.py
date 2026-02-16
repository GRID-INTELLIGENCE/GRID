"""Accountability contract schema for heavy enforcement.

Defines the contract schema for accountability enforcement, including:
- Endpoint contracts
- Data validation rules
- Performance SLAs
- Security requirements
- Compliance requirements
"""

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ContractSeverity(str, Enum):
    """Severity levels for contract violations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ViolationType(str, Enum):
    """Types of contract violations."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    DATA_VALIDATION = "data_validation"
    RATE_LIMIT = "rate_limit"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    IP_WHITELIST = "ip_whitelist"
    MISSING_CONTRACT = "missing_contract"
    ENDPOINT_DISABLED = "endpoint_disabled"


@dataclass
class ContractViolation:
    """Represents a single contract violation."""

    type: ViolationType
    severity: ContractSeverity
    message: str
    field: str
    actual_value: Any = None
    expected_value: Any = None
    penalty_points: int = 10
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Alias for backward compatibility
    @property
    def violation_type(self) -> ViolationType:
        """Alias for type property."""
        return self.type

    def to_dict(self) -> dict[str, Any]:
        """Convert violation to dictionary."""
        return {
            "type": self.type.value,
            "violation_type": self.type.value,  # Alias
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,
            "penalty_points": self.penalty_points,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class EnforcementResult:
    """Result of contract enforcement."""

    allowed: bool = True
    violations: list[ContractViolation] = field(default_factory=list)
    actions_taken: list[str] = field(default_factory=list)
    enforcement_mode: str = "monitor"
    endpoint_contract: Optional["EndpointContract"] = None
    endpoint_path: str = ""
    http_method: str = ""

    # Alias for backward compatibility
    @property
    def is_compliant(self) -> bool:
        """Alias for allowed property."""
        return self.allowed

    @property
    def total_penalty_points(self) -> int:
        """Calculate total penalty points from violations."""
        return sum(v.penalty_points for v in self.violations)

    def add_violation(self, violation: ContractViolation) -> None:
        """Add a violation to the result."""
        self.violations.append(violation)
        # Note: allowed may be set separately based on enforcement mode

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "allowed": self.allowed,
            "is_compliant": self.allowed,  # Alias
            "violation_count": len(self.violations),
            "total_penalty_points": self.total_penalty_points,
            "violations": [v.to_dict() for v in self.violations],
            "actions_taken": self.actions_taken,
            "enforcement_mode": self.enforcement_mode,
            "endpoint_path": self.endpoint_path,
            "http_method": self.http_method,
        }


class ContractManager:
    """Manager for loading and caching accountability contracts."""

    def __init__(self):
        self._contracts: dict[str, AccountabilityContract] = {}

    def register_contract(self, contract: "AccountabilityContract") -> None:
        """Register a contract."""
        self._contracts[contract.service_name] = contract

    def get_contract(self, service_name: str) -> Optional["AccountabilityContract"]:
        """Get a contract by service name."""
        return self._contracts.get(service_name)

    def get_all_contracts(self) -> dict[str, "AccountabilityContract"]:
        """Get all registered contracts."""
        return self._contracts.copy()

    def find_endpoint_contract(self, path: str, method: str) -> Optional["EndpointContract"]:
        """Find an endpoint contract across all registered contracts."""
        for contract in self._contracts.values():
            endpoint = contract.get_endpoint_contract(path, method)
            if endpoint:
                return endpoint
        return None


class DataValidationRule(BaseModel):
    """Data validation rule for request/response validation."""

    field: str = Field("", description="Field to validate (optional, derived from dict key)")
    type: str = Field("string", description="Expected type (string, number, boolean, object, array)")
    required: bool = Field(True, description="Whether the field is required")
    pattern: str | None = Field(None, description="Regex pattern for string validation")
    min_length: int | None = Field(None, description="Minimum length for strings/arrays")
    max_length: int | None = Field(None, description="Maximum length for strings/arrays")
    min_value: int | float | None = Field(None, description="Minimum value for numbers")
    max_value: int | float | None = Field(None, description="Maximum value for numbers")
    enum: list[Any] | None = Field(None, description="Allowed values")
    custom_validator: str | None = Field(
        None, description="Path to custom validation function (module.path:function_name)"
    )


class PerformanceSLA(BaseModel):
    """Performance SLA requirements for an endpoint."""

    max_latency_ms: int = Field(1000, description="Maximum allowed latency in milliseconds")
    max_error_rate: float = Field(0.01, description="Maximum allowed error rate (0-1)")
    min_throughput_rps: int = Field(10, description="Minimum required requests per second")
    timeout_ms: int = Field(30000, description="Request timeout in milliseconds")


class SecurityRequirement(BaseModel):
    """Security requirements for an endpoint."""

    authentication_required: bool = Field(True, description="Authentication required")
    required_roles: list[str] = Field(default_factory=list, description="Required roles for access")
    required_permissions: list[str] = Field(default_factory=list, description="Required permissions")
    ip_whitelist: list[str] | None = Field(None, description="Allowed IP addresses/CIDR ranges")
    rate_limit: int | None = Field(None, description="Max requests per minute per client")
    request_signing_required: bool = Field(False, description="Require request signing")
    response_encryption_required: bool = Field(False, description="Require response encryption")


class ComplianceRequirement(BaseModel):
    """Compliance requirements for an endpoint."""

    gdpr: bool = Field(False, description="GDPR compliance required")
    hipaa: bool = Field(False, description="HIPAA compliance required")
    pci_dss: bool = Field(False, description="PCI DSS compliance required")
    data_retention_days: int = Field(90, description="Required data retention period in days")
    audit_logging: bool = Field(True, description="Audit logging required")
    data_classification: str = Field(
        "public", description="Data classification level (public, internal, confidential, restricted)"
    )


class EndpointContract(BaseModel):
    """Contract defining requirements for a specific API endpoint."""

    path: str = Field(..., description="Endpoint path (can include wildcards)")
    methods: list[str] = Field(["GET"], description="HTTP methods this contract applies to")
    description: str = Field(..., description="Description of the endpoint's purpose")
    request_validation: dict[str, DataValidationRule] = Field(
        default_factory=dict, description="Request validation rules"
    )
    response_validation: dict[str, DataValidationRule] = Field(
        default_factory=dict, description="Response validation rules"
    )
    performance: PerformanceSLA = Field(default_factory=PerformanceSLA, description="Performance requirements")
    security: SecurityRequirement = Field(default_factory=SecurityRequirement, description="Security requirements")
    compliance: ComplianceRequirement = Field(
        default_factory=ComplianceRequirement, description="Compliance requirements"
    )
    enabled: bool = Field(True, description="Whether this contract is actively enforced")
    severity: ContractSeverity = Field(ContractSeverity.MEDIUM, description="Default severity for violations")
    penalty_points: int = Field(10, description="Penalty points for violations")
    auto_remediation: bool = Field(False, description="Enable automatic remediation")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When this contract was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When this contract was last updated"
    )

    @field_validator("methods")
    @classmethod
    def validate_http_method(cls, v: list[str]) -> list[str]:
        valid_methods = {
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "PATCH",
            "HEAD",
            "OPTIONS",
            "WEBSOCKET",
            "WS",
        }
        validated = []
        for method in v:
            if method.upper() not in valid_methods:
                raise ValueError(f"Invalid HTTP method: {method}")
            validated.append(method.upper())
        return validated

    @model_validator(mode="before")
    @classmethod
    def update_timestamp(cls, values: dict[str, Any]) -> dict[str, Any]:
        values["updated_at"] = datetime.now(UTC)
        return values


class ServiceLevelObjective(BaseModel):
    """Service Level Objective for accountability."""

    name: str = Field(..., description="Name of the SLO")
    description: str = Field(..., description="Description of the SLO")
    measurement: str = Field(..., description="What to measure (e.g., 'latency', 'error_rate')")
    threshold: float = Field(..., description="Threshold value")
    threshold_type: Literal["lt", "lte", "gt", "gte", "eq", "neq"] = Field(
        "lte", description="Comparison operator for threshold"
    )
    window: str = Field("1h", description="Time window for evaluation (e.g., '5m', '1h', '1d')")
    severity: ContractSeverity = Field(ContractSeverity.MEDIUM, description="Severity if SLO is violated")
    penalty_points: int = Field(5, description="Penalty points if SLO is violated")


class AccountabilityContract(BaseModel):
    """Complete accountability contract for a service."""

    service_name: str = Field(..., description="Name of the service")
    version: str = Field("1.0.0", description="Contract version")
    description: str = Field(..., description="Description of the service and contract")
    endpoints: list[EndpointContract] = Field(default_factory=list, description="List of endpoint contracts")
    slos: list[ServiceLevelObjective] = Field(default_factory=list, description="Service Level Objectives")
    default_security: SecurityRequirement = Field(
        default_factory=SecurityRequirement, description="Default security requirements"
    )
    default_compliance: ComplianceRequirement = Field(
        default_factory=ComplianceRequirement, description="Default compliance requirements"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When this contract was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When this contract was last updated"
    )

    def get_endpoint_contract(self, path: str, method: str) -> EndpointContract | None:
        """Find the most specific contract for the given path and method."""
        method = method.upper()

        # First try exact match
        for contract in self.endpoints:
            if contract.path == path and method in contract.methods:
                return contract

        # Then try wildcard match (e.g., /api/*)
        path_parts = path.strip("/").split("/")

        for contract in self.endpoints:
            if "*" in contract.path and method in contract.methods:
                contract_parts = contract.path.strip("/").split("/")
                if len(path_parts) != len(contract_parts):
                    continue

                match = True
                for p, cp in zip(path_parts, contract_parts):
                    if cp == "*":
                        continue
                    if p != cp:
                        match = False
                        break

                if match:
                    return contract

        return None

    def validate_request(self, path: str, method: str, request_data: dict) -> list[dict]:
        """Validate a request against the contract."""
        contract = self.get_endpoint_contract(path, method)
        if not contract:
            return [{"error": "no_matching_contract", "message": f"No contract found for {method} {path}"}]

        return self._validate_data(contract.request_validation, request_data)

    def validate_response(self, path: str, method: str, response_data: dict) -> list[dict]:
        """Validate a response against the contract."""
        contract = self.get_endpoint_contract(path, method)
        if not contract:
            return []

        return self._validate_data(contract.response_validation, response_data)

    def _validate_data(self, rules: dict[str, DataValidationRule], data: dict) -> list[dict]:
        """Validate data against validation rules."""
        errors = []

        for field, rule in rules.items():
            if field not in data:
                if rule.required:
                    errors.append(
                        {
                            "field": field,
                            "error": "missing_required_field",
                            "message": f"Required field '{field}' is missing",
                        }
                    )
                continue

            value = data[field]

            # Type checking
            expected_type = rule.type.lower()
            type_ok = False

            if expected_type == "string":
                type_ok = isinstance(value, str)
            elif expected_type == "number":
                type_ok = isinstance(value, (int, float))
            elif expected_type == "boolean":
                type_ok = isinstance(value, bool)
            elif expected_type == "object":
                type_ok = isinstance(value, dict)
            elif expected_type == "array":
                type_ok = isinstance(value, list)

            if not type_ok:
                errors.append(
                    {
                        "field": field,
                        "error": "invalid_type",
                        "message": f"Field '{field}' must be of type {expected_type}, got {type(value).__name__}",
                    }
                )
                continue

            # Additional validations
            if expected_type == "string":
                if rule.min_length is not None and len(value) < rule.min_length:
                    errors.append(
                        {
                            "field": field,
                            "error": "min_length",
                            "message": f"Field '{field}' must be at least {rule.min_length} characters",
                        }
                    )

                if rule.max_length is not None and len(value) > rule.max_length:
                    errors.append(
                        {
                            "field": field,
                            "error": "max_length",
                            "message": f"Field '{field}' must be at most {rule.max_length} characters",
                        }
                    )

                if rule.pattern and not re.match(rule.pattern, value):
                    errors.append(
                        {
                            "field": field,
                            "error": "pattern_mismatch",
                            "message": f"Field '{field}' does not match required pattern",
                        }
                    )

            elif expected_type in ("int", "float", "number"):
                if rule.min_value is not None and value < rule.min_value:
                    errors.append(
                        {
                            "field": field,
                            "error": "min_value",
                            "message": f"Field '{field}' must be at least {rule.min_value}",
                        }
                    )

                if rule.max_value is not None and value > rule.max_value:
                    errors.append(
                        {
                            "field": field,
                            "error": "max_value",
                            "message": f"Field '{field}' must be at most {rule.max_value}",
                        }
                    )

            if rule.enum and value not in rule.enum:
                errors.append(
                    {
                        "field": field,
                        "error": "invalid_enum_value",
                        "message": f"Field '{field}' must be one of {rule.enum}",
                    }
                )

            # TODO: Add support for custom validators

        return errors
