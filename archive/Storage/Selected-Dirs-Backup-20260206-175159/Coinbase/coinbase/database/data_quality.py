"""
Data Quality Checks
====================
Validates portfolio position consistency and data integrity.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class QualityCheckType(Enum):
    """Types of data quality checks."""

    NOT_NULL = "not_null"
    RANGE = "range"
    CONSISTENCY = "consistency"
    REFERENCE = "reference"
    TIMESTAMP = "timestamp"
    FORMAT = "format"


class QualityCheckSeverity(Enum):
    """Severity levels for quality issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class QualityIssue:
    """Data quality issue found."""

    check_type: QualityCheckType
    severity: QualityCheckSeverity
    field_name: str
    value: Any
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class QualityCheckResult:
    """Result of quality check."""

    passed: bool
    issues: list[QualityIssue]
    check_name: str
    timestamp: datetime = field(default_factory=datetime.now)


class PortfolioDataQualityChecker:
    """
    Validates portfolio position consistency and data integrity.

    Checks for:
    - Not null constraints
    - Value ranges
    - Consistency between fields
    - Referential integrity
    - Timestamp validity
    - Format validation
    """

    def __init__(self) -> None:
        self.issues: list[QualityIssue] = []
        self.logger = logging.getLogger(__name__)

    def check_position(self, position: dict[str, Any]) -> QualityCheckResult:
        """
        Check quality of a single portfolio position.

        Args:
            position: Portfolio position data

        Returns:
            QualityCheckResult with all issues
        """
        self.issues = []

        # Run all checks
        self._check_not_null(position)
        self._check_quantity_range(position)
        self._check_price_range(position)
        self._check_value_consistency(position)
        self._check_gain_loss_consistency(position)
        self._check_timestamp_validity(position)
        self._check_symbol_format(position)

        passed = len(self.issues) == 0

        return QualityCheckResult(
            passed=passed, issues=self.issues, check_name="position_quality_check"
        )

    def check_positions_batch(self, positions: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Check quality of multiple positions.

        Args:
            positions: List of portfolio positions

        Returns:
            Summary of quality check results
        """
        results: dict[str, Any] = {
            "total_positions": len(positions),
            "passed": 0,
            "failed": 0,
            "total_issues": 0,
            "issues_by_severity": {},
            "issues_by_field": {},
            "all_issues": [],
        }

        for i, position in enumerate(positions):
            result = self.check_position(position)

            if result.passed:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["total_issues"] += len(result.issues)

                # Count by severity
                for issue in result.issues:
                    severity = issue.severity.value
                    results["issues_by_severity"][severity] = results["issues_by_severity"].get(severity, 0) + 1

                    # Count by field
                    if issue.field_name not in results["issues_by_field"]:
                        results["issues_by_field"][issue.field_name] = 0
                    results["issues_by_field"][issue.field_name] += 1

                    # Add to all issues
                    results["all_issues"].append(
                        {
                            "position_index": i,
                            "check_type": issue.check_type.value,
                            "severity": severity,
                            "field_name": issue.field_name,
                            "message": issue.message,
                            "timestamp": issue.timestamp.isoformat(),
                        }
                    )

        return results

    def _check_not_null(self, position: dict[str, Any]) -> None:
        """Check that required fields are not null."""
        required_fields = [
            "symbol",
            "quantity",
            "purchase_price",
            "current_price",
            "purchase_value",
            "current_value",
        ]

        for field in required_fields:
            if field not in position or position[field] is None:
                self.issues.append(
                    QualityIssue(
                        check_type=QualityCheckType.NOT_NULL,
                        severity=QualityCheckSeverity.ERROR,
                        field_name=field,
                        value=position.get(field),
                        message=f"Required field '{field}' is null or missing",
                    )
                )

    def _check_quantity_range(self, position: dict[str, Any]) -> None:
        """Check that quantity is within valid range."""
        if "quantity" not in position:
            return

        quantity = position["quantity"]

        if quantity is None:
            return

        if quantity < 0:
            self.issues.append(
                QualityIssue(
                    check_type=QualityCheckType.RANGE,
                    severity=QualityCheckSeverity.ERROR,
                    field_name="quantity",
                    value=quantity,
                    message=f"Quantity cannot be negative: {quantity}",
                )
            )

        if quantity > 1e9:
            self.issues.append(
                QualityIssue(
                    check_type=QualityCheckType.RANGE,
                    severity=QualityCheckSeverity.WARNING,
                    field_name="quantity",
                    value=quantity,
                    message=f"Suspiciously large quantity: {quantity}",
                )
            )

    def _check_price_range(self, position: dict[str, Any]) -> None:
        """Check that prices are within valid range."""
        price_fields = ["purchase_price", "current_price"]

        for field in price_fields:
            if field not in position:
                continue

            price = position[field]

            if price is None:
                continue

            if price < 0:
                self.issues.append(
                    QualityIssue(
                        check_type=QualityCheckType.RANGE,
                        severity=QualityCheckSeverity.ERROR,
                        field_name=field,
                        value=price,
                        message=f"{field} cannot be negative: {price}",
                    )
                )

            if price > 1e9:
                self.issues.append(
                    QualityIssue(
                        check_type=QualityCheckType.RANGE,
                        severity=QualityCheckSeverity.WARNING,
                        field_name=field,
                        value=price,
                        message=f"Suspiciously large {field}: {price}",
                    )
                )

    def _check_value_consistency(self, position: dict[str, Any]) -> None:
        """Check consistency between quantity, price, and value."""
        required = [
            "quantity",
            "purchase_price",
            "purchase_value",
            "current_price",
            "current_value",
        ]

        if not all(field in position for field in required):
            return

        quantity = position["quantity"]
        purchase_price = position["purchase_price"]
        purchase_value = position["purchase_value"]
        current_price = position["current_price"]
        current_value = position["current_value"]

        # Check purchase value consistency (allow 5% tolerance)
        expected_purchase_value = quantity * purchase_price
        if purchase_value > 0:
            purchase_diff = abs(purchase_value - expected_purchase_value) / expected_purchase_value
            if purchase_diff > 0.05:
                self.issues.append(
                    QualityIssue(
                        check_type=QualityCheckType.CONSISTENCY,
                        severity=QualityCheckSeverity.WARNING,
                        field_name="purchase_value",
                        value=purchase_value,
                        message=f"Purchase value inconsistency: expected {expected_purchase_value:.2f}, got {purchase_value:.2f}",
                    )
                )

        # Check current value consistency (allow 5% tolerance)
        expected_current_value = quantity * current_price
        if current_value > 0:
            current_diff = abs(current_value - expected_current_value) / expected_current_value
            if current_diff > 0.05:
                self.issues.append(
                    QualityIssue(
                        check_type=QualityCheckType.CONSISTENCY,
                        severity=QualityCheckSeverity.WARNING,
                        field_name="current_value",
                        value=current_value,
                        message=f"Current value inconsistency: expected {expected_current_value:.2f}, got {current_value:.2f}",
                    )
                )

    def _check_gain_loss_consistency(self, position: dict[str, Any]) -> None:
        """Check gain/loss calculation consistency."""
        required = ["purchase_value", "current_value", "total_gain_loss", "gain_loss_percentage"]

        if not all(field in position for field in required):
            return

        purchase_value = position["purchase_value"]
        current_value = position["current_value"]
        total_gain_loss = position["total_gain_loss"]
        gain_loss_percentage = position["gain_loss_percentage"]

        if purchase_value == 0:
            return

        # Check total gain/loss
        expected_gain_loss = current_value - purchase_value
        if abs(total_gain_loss - expected_gain_loss) > 1.0:  # Allow $1 tolerance
            self.issues.append(
                QualityIssue(
                    check_type=QualityCheckType.CONSISTENCY,
                    severity=QualityCheckSeverity.WARNING,
                    field_name="total_gain_loss",
                    value=total_gain_loss,
                    message=f"Gain/loss inconsistency: expected {expected_gain_loss:.2f}, got {total_gain_loss:.2f}",
                )
            )

        # Check gain/loss percentage
        expected_percentage = (total_gain_loss / purchase_value) * 100
        if abs(gain_loss_percentage - expected_percentage) > 1.0:  # Allow 1% tolerance
            self.issues.append(
                QualityIssue(
                    check_type=QualityCheckType.CONSISTENCY,
                    severity=QualityCheckSeverity.WARNING,
                    field_name="gain_loss_percentage",
                    value=gain_loss_percentage,
                    message=f"Gain/loss percentage inconsistency: expected {expected_percentage:.2f}%, got {gain_loss_percentage:.2f}%",
                )
            )

    def _check_timestamp_validity(self, position: dict[str, Any]) -> None:
        """Check timestamp validity."""
        timestamp_fields = ["purchase_date", "created_at", "updated_at"]

        for field in timestamp_fields:
            if field not in position:
                continue

            timestamp = position[field]

            if timestamp is None:
                continue

            # Check if timestamp is not in the future
            if isinstance(timestamp, datetime):
                if timestamp > datetime.now():
                    self.issues.append(
                        QualityIssue(
                            check_type=QualityCheckType.TIMESTAMP,
                            severity=QualityCheckSeverity.ERROR,
                            field_name=field,
                            value=timestamp,
                            message=f"{field} is in the future: {timestamp}",
                        )
                    )
            elif isinstance(timestamp, str):
                try:
                    parsed = datetime.fromisoformat(timestamp)
                    if parsed > datetime.now():
                        self.issues.append(
                            QualityIssue(
                                check_type=QualityCheckType.TIMESTAMP,
                                severity=QualityCheckSeverity.ERROR,
                                field_name=field,
                                value=timestamp,
                                message=f"{field} is in the future: {timestamp}",
                            )
                        )
                except ValueError:
                    self.issues.append(
                        QualityIssue(
                            check_type=QualityCheckType.FORMAT,
                            severity=QualityCheckSeverity.WARNING,
                            field_name=field,
                            value=timestamp,
                            message=f"Invalid timestamp format: {timestamp}",
                        )
                    )

    def _check_symbol_format(self, position: dict[str, Any]) -> None:
        """Check symbol format."""
        if "symbol" not in position:
            return

        symbol = position["symbol"]

        if symbol is None:
            return

        # Symbol should be uppercase letters and numbers only
        if not symbol.replace(".", "").isalnum():
            self.issues.append(
                QualityIssue(
                    check_type=QualityCheckType.FORMAT,
                    severity=QualityCheckSeverity.WARNING,
                    field_name="symbol",
                    value=symbol,
                    message=f"Invalid symbol format: {symbol}",
                )
            )


def get_data_quality_checker() -> PortfolioDataQualityChecker:
    """
    Get singleton instance of PortfolioDataQualityChecker.

    Returns:
        PortfolioDataQualityChecker instance
    """
    return PortfolioDataQualityChecker()


# Example usage
def example_usage() -> None:
    """Example usage of data quality checker."""
    checker = get_data_quality_checker()

    # Valid position
    valid_position = {
        "symbol": "AAPL",
        "quantity": 100,
        "purchase_price": 150.0,
        "current_price": 175.0,
        "purchase_value": 15000.0,
        "current_value": 17500.0,
        "total_gain_loss": 2500.0,
        "gain_loss_percentage": 16.67,
        "purchase_date": "2024-01-15",
    }

    result = checker.check_position(valid_position)
    print(f"Valid position check: {'PASSED' if result.passed else 'FAILED'}")

    # Invalid position
    invalid_position = {
        "symbol": "AAPL",
        "quantity": -100,  # Invalid: negative
        "purchase_price": 150.0,
        "current_price": 175.0,
        "purchase_value": 15000.0,
        "current_value": 17500.0,
        "total_gain_loss": 2500.0,
        "gain_loss_percentage": 16.67,
        "purchase_date": "2024-01-15",
    }

    result = checker.check_position(invalid_position)
    print(f"Invalid position check: {'PASSED' if result.passed else 'FAILED'}")

    if not result.passed:
        print(f"Issues found: {len(result.issues)}")
        for issue in result.issues:
            print(f"  - {issue.severity.value.upper()}: {issue.message}")


if __name__ == "__main__":
    example_usage()
