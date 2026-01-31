"""
Coinbase Integration Adapter
============================
Integrates Coinbase portfolio and trading with unified fabric.

Features:
- Safety-validated portfolio actions
- Event-driven trading signals
- Revenue pipeline auditing
"""
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from . import Event, EventDomain, get_event_bus
from .audit import AuditEventType, get_audit_logger
from .safety_bridge import SafetyContext, get_safety_bridge

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Coinbase action types"""
    BUY = "buy"
    SELL = "sell"
    REBALANCE = "rebalance"
    STAKE = "stake"
    UNSTAKE = "unstake"
    WITHDRAW = "withdraw"
    DEPOSIT = "deposit"


class SignalType(Enum):
    """Trading signal types"""
    ENTRY = "entry"
    EXIT = "exit"
    HOLD = "hold"
    REBALANCE = "rebalance"
    ALERT = "alert"


@dataclass
class PortfolioAction:
    """Portfolio action request"""
    action_type: ActionType
    asset: str
    amount: float
    user_id: str
    price: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    action_id: str = field(default_factory=lambda: f"act_{datetime.now(UTC).timestamp():.0f}")


@dataclass
class TradingSignal:
    """Trading signal"""
    signal_type: SignalType
    asset: str
    confidence: float
    reasoning: str
    user_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    signal_id: str = field(default_factory=lambda: f"sig_{datetime.now(UTC).timestamp():.0f}")


@dataclass
class ActionResult:
    """Result of a portfolio action"""
    success: bool
    action_id: str
    message: str
    blocked_by_safety: bool = False
    safety_reason: str | None = None
    execution_time_ms: float = 0.0


class CoinbaseIntegrationAdapter:
    """
    Adapter for integrating Coinbase with unified fabric.
    
    Connects:
    - Portfolio actions → Safety validation → Event bus
    - Trading signals → Safety validation → Revenue pipeline
    - Revenue events → Audit trail
    """

    def __init__(self):
        self._safety_bridge = get_safety_bridge()
        self._event_bus = get_event_bus()
        self._audit_logger = get_audit_logger()
        self._action_handlers: dict[ActionType, Callable] = {}
        self._signal_handlers: list[Callable] = []
        self._initialized = False

    async def initialize(self):
        """Initialize the adapter"""
        if self._initialized:
            return

        # Subscribe to relevant events
        self._event_bus.subscribe("coinbase.action.*", self._handle_action_event, domain="coinbase")
        self._event_bus.subscribe("coinbase.signal.*", self._handle_signal_event, domain="coinbase")

        self._initialized = True
        logger.info("CoinbaseIntegrationAdapter initialized")

    async def execute_action(
        self,
        action: PortfolioAction
    ) -> ActionResult:
        """
        Execute a portfolio action with safety validation.
        
        Args:
            action: Portfolio action to execute
            
        Returns:
            ActionResult with success/failure status
        """
        start_time = datetime.now(UTC)

        # Safety validation first
        report = await self._safety_bridge.validate_coinbase_action(
            {
                "type": action.action_type.value,
                "asset": action.asset,
                "amount": action.amount,
                "price": action.price
            },
            action.user_id
        )

        if report.should_block:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                message="Action blocked by safety",
                blocked_by_safety=True,
                safety_reason=report.violations[0].description if report.violations else "Safety violation"
            )

        # Execute the action
        try:
            result = await self._execute_internal(action)

            # Log to audit
            await self._audit_action(action, result)

            # Broadcast event
            await self._broadcast_action_event(action, result)

            elapsed = (datetime.now(UTC) - start_time).total_seconds() * 1000
            result.execution_time_ms = elapsed

            return result

        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return ActionResult(
                success=False,
                action_id=action.action_id,
                message=f"Execution failed: {str(e)}"
            )

    async def process_signal(
        self,
        signal: TradingSignal
    ) -> bool:
        """
        Process a trading signal with safety validation.
        
        Args:
            signal: Trading signal to process
            
        Returns:
            True if signal was processed successfully
        """
        # Safety validation
        report = await self._safety_bridge.validate(
            f"Trading signal: {signal.signal_type.value} {signal.asset} confidence={signal.confidence}",
            SafetyContext(
                project="coinbase",
                domain="trading",
                user_id=signal.user_id,
                metadata={"signal_id": signal.signal_id}
            )
        )

        if report.should_block:
            logger.warning(f"Signal blocked by safety: {signal.signal_id}")
            return False

        # Dispatch to signal handlers
        for handler in self._signal_handlers:
            try:
                await handler(signal)
            except Exception as e:
                logger.error(f"Signal handler error: {e}")

        # Broadcast event
        await self._broadcast_signal_event(signal)

        return True

    async def create_revenue_event(
        self,
        revenue_type: str,
        amount: float,
        asset: str,
        user_id: str,
        metadata: dict | None = None
    ) -> str:
        """
        Create a safety-validated revenue event.
        
        Args:
            revenue_type: Type of revenue (dividend, staking, trading)
            amount: Revenue amount
            asset: Asset symbol
            user_id: User identifier
            metadata: Additional metadata
            
        Returns:
            Revenue event ID
        """
        # Validate revenue event
        report = await self._safety_bridge.validate_revenue_event(
            {
                "type": revenue_type,
                "amount": amount,
                "asset": asset,
                "user_id": user_id,
                **(metadata or {})
            },
            user_id
        )

        if report.should_block:
            raise ValueError(f"Revenue event blocked: {report.violations}")

        # Log to audit
        request_id = await self._audit_logger.log(
            event_type=AuditEventType.SYSTEM_EVENT,
            project_id="coinbase",
            domain="revenue",
            action=f"revenue_{revenue_type}",
            status="success",
            user_id=user_id,
            details={
                "revenue_type": revenue_type,
                "amount": amount,
                "asset": asset,
                **(metadata or {})
            }
        )

        # Broadcast event
        event = Event(
            event_type=f"coinbase.revenue.{revenue_type}",
            payload={
                "revenue_type": revenue_type,
                "amount": amount,
                "asset": asset,
                "user_id": user_id,
                "request_id": request_id
            },
            source_domain=EventDomain.COINBASE.value,
            target_domains=["all"]
        )
        await self._event_bus.publish(event)

        logger.info(f"Revenue event created: {revenue_type} ${amount} {asset}")

        return request_id

    def register_action_handler(
        self,
        action_type: ActionType,
        handler: Callable[[PortfolioAction], Awaitable[ActionResult]]
    ):
        """Register a handler for specific action type"""
        self._action_handlers[action_type] = handler

    def register_signal_handler(
        self,
        handler: Callable[[TradingSignal], Awaitable[None]]
    ):
        """Register a trading signal handler"""
        self._signal_handlers.append(handler)

    async def _execute_internal(
        self,
        action: PortfolioAction
    ) -> ActionResult:
        """Execute action internally"""
        # Check for custom handler
        if action.action_type in self._action_handlers:
            return await self._action_handlers[action.action_type](action)

        # Default mock execution
        logger.info(f"Executing {action.action_type.value}: {action.amount} {action.asset}")

        return ActionResult(
            success=True,
            action_id=action.action_id,
            message=f"{action.action_type.value.upper()} {action.amount} {action.asset} executed"
        )

    async def _audit_action(
        self,
        action: PortfolioAction,
        result: ActionResult
    ):
        """Log action to audit trail"""
        await self._audit_logger.log_portfolio_action(
            action=action.action_type.value,
            portfolio_id=action.user_id,
            user_id=action.user_id,
            success=result.success,
            details={
                "asset": action.asset,
                "amount": action.amount,
                "action_id": action.action_id,
                "message": result.message
            }
        )

    async def _broadcast_action_event(
        self,
        action: PortfolioAction,
        result: ActionResult
    ):
        """Broadcast action event"""
        event = Event(
            event_type=f"coinbase.action.{action.action_type.value}",
            payload={
                "action_id": action.action_id,
                "action_type": action.action_type.value,
                "asset": action.asset,
                "amount": action.amount,
                "success": result.success,
                "user_id": action.user_id
            },
            source_domain=EventDomain.COINBASE.value,
            target_domains=["all"]
        )
        await self._event_bus.publish(event)

    async def _broadcast_signal_event(
        self,
        signal: TradingSignal
    ):
        """Broadcast signal event"""
        event = Event(
            event_type=f"coinbase.signal.{signal.signal_type.value}",
            payload={
                "signal_id": signal.signal_id,
                "signal_type": signal.signal_type.value,
                "asset": signal.asset,
                "confidence": signal.confidence,
                "reasoning": signal.reasoning
            },
            source_domain=EventDomain.COINBASE.value,
            target_domains=["all"]
        )
        await self._event_bus.publish(event)

    async def _handle_action_event(self, event: Event):
        """Handle incoming action events"""
        logger.debug(f"Received action event: {event.event_type}")

    async def _handle_signal_event(self, event: Event):
        """Handle incoming signal events"""
        logger.debug(f"Received signal event: {event.event_type}")


# Singleton instance
_coinbase_adapter: CoinbaseIntegrationAdapter | None = None


def get_coinbase_adapter() -> CoinbaseIntegrationAdapter:
    """Get the singleton Coinbase adapter"""
    global _coinbase_adapter
    if _coinbase_adapter is None:
        _coinbase_adapter = CoinbaseIntegrationAdapter()
    return _coinbase_adapter


async def init_coinbase_adapter() -> CoinbaseIntegrationAdapter:
    """Initialize the Coinbase adapter"""
    adapter = get_coinbase_adapter()
    await adapter.initialize()
    return adapter
