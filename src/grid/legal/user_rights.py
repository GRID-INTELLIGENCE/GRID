"""User rights protection module.

Manages user-right requests (access, erasure, portability, etc.),
tracks their lifecycle, and raises wellbeing flags when user safety
or dignity is at risk.  Integrates with the boundary engine's
consent and refusal mechanisms.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from .models import (
    PolicySeverity,
    UserRightRequest,
    UserRightRequestStatus,
    UserRightType,
    WellbeingFlag,
)

logger = logging.getLogger(__name__)

# Maximum days before an unresolved request triggers escalation.
_ESCALATION_THRESHOLD_DAYS = 30


class UserRightsManager:
    """Tracks and enforces user-right requests and wellbeing flags."""

    def __init__(self) -> None:
        self._requests: dict[str, UserRightRequest] = {}
        self._wellbeing_flags: dict[str, WellbeingFlag] = {}

    # -- Right request lifecycle ---------------------------------------------

    async def submit_request(
        self,
        user_id: str,
        right_type: UserRightType,
        description: str = "",
        priority: PolicySeverity = PolicySeverity.MEDIUM,
        metadata: dict[str, Any] | None = None,
    ) -> UserRightRequest:
        """Submit a new user-right request.

        Immediately acknowledges the request and stores it for processing.
        """
        request = UserRightRequest(
            user_id=user_id,
            right_type=right_type,
            description=description,
            priority=priority,
            status=UserRightRequestStatus.ACKNOWLEDGED,
            acknowledged_at=datetime.now(UTC),
            metadata=metadata or {},
        )
        self._requests[request.request_id] = request
        logger.info(
            "user_right_request_submitted",
            extra={
                "request_id": request.request_id,
                "user_id": user_id,
                "right_type": right_type.value,
                "priority": priority.value,
            },
        )
        return request

    async def fulfill_request(
        self,
        request_id: str,
        resolution_summary: str,
    ) -> UserRightRequest | None:
        """Mark a request as fulfilled."""
        request = self._requests.get(request_id)
        if request is None:
            logger.warning("fulfill_unknown_request", extra={"request_id": request_id})
            return None

        request.status = UserRightRequestStatus.FULFILLED
        request.resolved_at = datetime.now(UTC)
        request.resolution_summary = resolution_summary
        logger.info(
            "user_right_request_fulfilled",
            extra={"request_id": request_id, "user_id": request.user_id},
        )
        return request

    async def deny_request(
        self,
        request_id: str,
        reason: str,
    ) -> UserRightRequest | None:
        """Deny a request with a documented reason."""
        request = self._requests.get(request_id)
        if request is None:
            return None

        request.status = UserRightRequestStatus.DENIED
        request.resolved_at = datetime.now(UTC)
        request.resolution_summary = reason
        logger.info(
            "user_right_request_denied",
            extra={"request_id": request_id, "reason": reason},
        )
        return request

    async def escalate_request(self, request_id: str, reason: str = "") -> UserRightRequest | None:
        """Escalate a request that cannot be handled at this level."""
        request = self._requests.get(request_id)
        if request is None:
            return None

        request.status = UserRightRequestStatus.ESCALATED
        request.metadata["escalation_reason"] = reason
        logger.info(
            "user_right_request_escalated",
            extra={"request_id": request_id, "reason": reason},
        )
        return request

    def get_request(self, request_id: str) -> UserRightRequest | None:
        return self._requests.get(request_id)

    def get_pending_requests(self, user_id: str | None = None) -> list[UserRightRequest]:
        """Return all non-terminal requests, optionally filtered by user."""
        terminal = {UserRightRequestStatus.FULFILLED, UserRightRequestStatus.DENIED}
        results: list[UserRightRequest] = []
        for r in self._requests.values():
            if r.status in terminal:
                continue
            if user_id and r.user_id != user_id:
                continue
            results.append(r)
        return results

    def get_overdue_requests(self) -> list[UserRightRequest]:
        """Return requests that have exceeded the escalation threshold."""
        now = datetime.now(UTC)
        overdue: list[UserRightRequest] = []
        terminal = {UserRightRequestStatus.FULFILLED, UserRightRequestStatus.DENIED}
        for r in self._requests.values():
            if r.status in terminal:
                continue
            age_days = (now - r.submitted_at).days
            if age_days >= _ESCALATION_THRESHOLD_DAYS:
                overdue.append(r)
        return overdue

    # -- Wellbeing flags -----------------------------------------------------

    async def raise_wellbeing_flag(
        self,
        user_id: str,
        concern: str,
        severity: PolicySeverity,
        source: str,
        mitigations: list[str] | None = None,
    ) -> WellbeingFlag:
        """Raise a wellbeing concern for a user.

        This triggers safety-domain events and notifies the boundary engine.
        """
        flag = WellbeingFlag(
            user_id=user_id,
            concern=concern,
            severity=severity,
            source=source,
            mitigations=mitigations or [],
        )
        self._wellbeing_flags[flag.flag_id] = flag
        logger.warning(
            "wellbeing_flag_raised",
            extra={
                "flag_id": flag.flag_id,
                "user_id": user_id,
                "concern": concern,
                "severity": severity.value,
            },
        )
        return flag

    async def resolve_wellbeing_flag(self, flag_id: str) -> WellbeingFlag | None:
        flag = self._wellbeing_flags.get(flag_id)
        if flag is None:
            return None
        flag.resolved = True
        logger.info("wellbeing_flag_resolved", extra={"flag_id": flag_id})
        return flag

    def get_active_wellbeing_flags(self, user_id: str | None = None) -> list[WellbeingFlag]:
        flags: list[WellbeingFlag] = []
        for f in self._wellbeing_flags.values():
            if f.resolved:
                continue
            if user_id and f.user_id != user_id:
                continue
            flags.append(f)
        return flags

    # -- Bulk checks ---------------------------------------------------------

    async def check_wellbeing(self, user_id: str, context: dict[str, Any]) -> list[WellbeingFlag]:
        """Run heuristic wellbeing checks and return any new flags.

        Checks for high interaction density, excessive hours, and
        cognitive load signals that may harm user wellbeing.
        """
        new_flags: list[WellbeingFlag] = []

        interaction_density = context.get("interaction_density_score", 0.0)
        if isinstance(interaction_density, (int, float)) and interaction_density > 0.85:
            flag = await self.raise_wellbeing_flag(
                user_id=user_id,
                concern="Unusually high interaction density detected — potential overwork",
                severity=PolicySeverity.HIGH,
                source="legal_agent.user_rights",
                mitigations=["Suggest break", "Reduce task frequency"],
            )
            new_flags.append(flag)

        cognitive_load = context.get("cognitive_load_level", "low")
        if cognitive_load in ("high", "critical"):
            flag = await self.raise_wellbeing_flag(
                user_id=user_id,
                concern=f"Cognitive load at '{cognitive_load}' level — risk of decision fatigue",
                severity=PolicySeverity.HIGH if cognitive_load == "critical" else PolicySeverity.MEDIUM,
                source="legal_agent.user_rights",
                mitigations=["Simplify task queue", "Provide decision scaffolding"],
            )
            new_flags.append(flag)

        hours_active = context.get("hours_active_today", 0)
        if isinstance(hours_active, (int, float)) and hours_active > 10:
            flag = await self.raise_wellbeing_flag(
                user_id=user_id,
                concern=f"User active for {hours_active}h today — extended session risk",
                severity=PolicySeverity.MEDIUM,
                source="legal_agent.user_rights",
                mitigations=["Encourage rest", "Limit non-critical tasks"],
            )
            new_flags.append(flag)

        return new_flags
