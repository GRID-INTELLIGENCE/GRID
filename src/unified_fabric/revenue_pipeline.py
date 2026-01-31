"""
Revenue Pipeline
================
End-to-end safety-validated revenue flow with audit trail.

Connects:
- Coinbase portfolio actions → Revenue events
- Safety validation at every step
- Unified audit logging
"""
import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from . import Event, EventDomain, get_event_bus
from .audit import AuditEventType, get_audit_logger
from .coinbase_adapter import ActionType, PortfolioAction, SignalType, TradingSignal, get_coinbase_adapter
from .safety_bridge import SafetyContext, get_safety_bridge

logger = logging.getLogger(__name__)


class RevenueType(Enum):
    """Types of revenue"""
    TRADING_PROFIT = "trading_profit"
    DIVIDEND = "dividend"
    STAKING_REWARD = "staking_reward"
    REFERRAL = "referral"
    SUBSCRIPTION = "subscription"


class PipelineStage(Enum):
    """Pipeline stages"""
    SIGNAL_RECEIVED = "signal_received"
    SAFETY_VALIDATED = "safety_validated"
    ACTION_EXECUTED = "action_executed"
    REVENUE_RECORDED = "revenue_recorded"
    AUDIT_LOGGED = "audit_logged"
    COMPLETED = "completed"


@dataclass
class RevenueEvent:
    """Revenue event in pipeline"""
    revenue_type: RevenueType
    amount: float
    asset: str
    user_id: str
    source_action_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    event_id: str = field(default_factory=lambda: f"rev_{uuid.uuid4().hex[:12]}")


@dataclass
class PipelineResult:
    """Result of pipeline execution"""
    success: bool
    stages_completed: list[PipelineStage]
    revenue_amount: float = 0.0
    error: str | None = None
    event_id: str = ""
    total_time_ms: float = 0.0


class RevenuePipeline:
    """
    End-to-end revenue pipeline with safety at every stage.
    
    Flow:
    1. Trading signal received
    2. Safety validation
    3. Portfolio action execution  
    4. Revenue calculation
    5. Audit logging
    6. Event broadcast
    """

    def __init__(self):
        self._safety_bridge = get_safety_bridge()
        self._coinbase_adapter = get_coinbase_adapter()
        self._audit_logger = get_audit_logger()
        self._event_bus = get_event_bus()
        self._revenue_handlers: list[Callable] = []
        self._initialized = False

    async def initialize(self):
        """Initialize the pipeline"""
        if self._initialized:
            return

        # Subscribe to revenue events
        self._event_bus.subscribe("coinbase.revenue.*", self._handle_revenue_event, domain="revenue")

        self._initialized = True
        logger.info("RevenuePipeline initialized")

    async def process_trading_opportunity(
        self,
        signal: TradingSignal,
        execute: bool = True
    ) -> PipelineResult:
        """
        Process a trading opportunity through the full pipeline.
        
        Args:
            signal: Trading signal
            execute: Whether to execute the trade
            
        Returns:
            PipelineResult with outcome
        """
        import time
        start = time.perf_counter()
        stages: list[PipelineStage] = []

        try:
            # Stage 1: Signal received
            stages.append(PipelineStage.SIGNAL_RECEIVED)

            # Stage 2: Safety validation
            report = await self._safety_bridge.validate(
                f"Trading: {signal.signal_type.value} {signal.asset}",
                SafetyContext(
                    project="coinbase",
                    domain="revenue_pipeline",
                    user_id=signal.user_id
                )
            )

            if report.should_block:
                return PipelineResult(
                    success=False,
                    stages_completed=stages,
                    error=f"Blocked at safety: {report.threat_level.value}"
                )

            stages.append(PipelineStage.SAFETY_VALIDATED)

            # Stage 3: Execute action if requested
            action_id = None
            if execute and signal.signal_type in [SignalType.ENTRY, SignalType.EXIT]:
                action = self._signal_to_action(signal)
                result = await self._coinbase_adapter.execute_action(action)

                if not result.success:
                    return PipelineResult(
                        success=False,
                        stages_completed=stages,
                        error=result.message
                    )

                action_id = result.action_id
                stages.append(PipelineStage.ACTION_EXECUTED)

            # Stage 4: Record revenue (simulate profit calculation)
            revenue = self._calculate_revenue(signal)

            if revenue > 0:
                event = RevenueEvent(
                    revenue_type=RevenueType.TRADING_PROFIT,
                    amount=revenue,
                    asset=signal.asset,
                    user_id=signal.user_id,
                    source_action_id=action_id
                )

                await self._record_revenue(event)
                stages.append(PipelineStage.REVENUE_RECORDED)

            # Stage 5: Audit log
            await self._audit_logger.log(
                event_type=AuditEventType.SYSTEM_EVENT,
                project_id="coinbase",
                domain="revenue_pipeline",
                action="pipeline_completed",
                status="success",
                user_id=signal.user_id,
                details={
                    "signal_type": signal.signal_type.value,
                    "asset": signal.asset,
                    "revenue": revenue,
                    "stages": len(stages)
                }
            )
            stages.append(PipelineStage.AUDIT_LOGGED)
            stages.append(PipelineStage.COMPLETED)

            elapsed = (time.perf_counter() - start) * 1000

            return PipelineResult(
                success=True,
                stages_completed=stages,
                revenue_amount=revenue,
                event_id=signal.signal_id,
                total_time_ms=elapsed
            )

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return PipelineResult(
                success=False,
                stages_completed=stages,
                error=str(e)
            )

    async def record_dividend(
        self,
        asset: str,
        amount: float,
        user_id: str
    ) -> str:
        """Record a dividend revenue event"""
        event = RevenueEvent(
            revenue_type=RevenueType.DIVIDEND,
            amount=amount,
            asset=asset,
            user_id=user_id
        )
        return await self._record_revenue(event)

    async def record_staking_reward(
        self,
        asset: str,
        amount: float,
        user_id: str
    ) -> str:
        """Record a staking reward"""
        event = RevenueEvent(
            revenue_type=RevenueType.STAKING_REWARD,
            amount=amount,
            asset=asset,
            user_id=user_id
        )
        return await self._record_revenue(event)

    def register_revenue_handler(
        self,
        handler: Callable[[RevenueEvent], Awaitable[None]]
    ):
        """Register a revenue event handler"""
        self._revenue_handlers.append(handler)

    async def _record_revenue(self, event: RevenueEvent) -> str:
        """Internal revenue recording"""
        # Log to audit
        request_id = await self._audit_logger.log(
            event_type=AuditEventType.SYSTEM_EVENT,
            project_id="coinbase",
            domain="revenue",
            action=f"revenue_{event.revenue_type.value}",
            status="success",
            user_id=event.user_id,
            details={
                "revenue_type": event.revenue_type.value,
                "amount": event.amount,
                "asset": event.asset,
                "event_id": event.event_id
            }
        )

        # Broadcast event
        bus_event = Event(
            event_type=f"coinbase.revenue.{event.revenue_type.value}",
            payload={
                "event_id": event.event_id,
                "revenue_type": event.revenue_type.value,
                "amount": event.amount,
                "asset": event.asset,
                "user_id": event.user_id
            },
            source_domain=EventDomain.COINBASE.value,
            target_domains=["all"]
        )
        await self._event_bus.publish(bus_event)

        # Notify handlers
        for handler in self._revenue_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Revenue handler error: {e}")

        logger.info(f"Revenue recorded: {event.revenue_type.value} ${event.amount} {event.asset} (Audit ID: {request_id})")

        return event.event_id

    def _signal_to_action(self, signal: TradingSignal) -> PortfolioAction:
        """Convert trading signal to portfolio action"""
        action_type = ActionType.BUY if signal.signal_type == SignalType.ENTRY else ActionType.SELL

        return PortfolioAction(
            action_type=action_type,
            asset=signal.asset,
            amount=signal.confidence * 100,  # Scale by confidence
            user_id=signal.user_id,
            metadata={"signal_id": signal.signal_id}
        )

    def _calculate_revenue(self, signal: TradingSignal) -> float:
        """Calculate simulated revenue from signal"""
        # Simplified revenue calculation
        if signal.signal_type in [SignalType.EXIT, SignalType.REBALANCE]:
            return signal.confidence * 50.0  # Simulated profit
        return 0.0

    async def _handle_revenue_event(self, event: Event):
        """Handle incoming revenue events"""
        logger.debug(f"Revenue event: {event.event_type}")


# Singleton instance
_revenue_pipeline: RevenuePipeline | None = None


def get_revenue_pipeline() -> RevenuePipeline:
    """Get the singleton revenue pipeline"""
    global _revenue_pipeline
    if _revenue_pipeline is None:
        _revenue_pipeline = RevenuePipeline()
    return _revenue_pipeline


async def init_revenue_pipeline() -> RevenuePipeline:
    """Initialize the revenue pipeline"""
    pipeline = get_revenue_pipeline()
    await pipeline.initialize()
    return pipeline
