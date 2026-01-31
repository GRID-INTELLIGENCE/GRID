"""
Event-Driven Architecture System for Arena Modernization
======================================================

Transforms the dial-up-like synchronous architecture into an asynchronous,
event-driven system with proper separation of concerns and dynamic integration.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Callable, Union, TypeVar, Generic
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from collections import defaultdict
import weakref

import aiofiles
import aio_pika
from aio_pika import ExchangeType, Message, DeliveryMode
import redis.asyncio as redis

T = TypeVar('T')


class EventPriority(Enum):
    """Event priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EventStatus(Enum):
    """Event processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class Event:
    """Base event structure."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    source: str = ""
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None  # Event that caused this event
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 30.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create from dictionary."""
        data['priority'] = EventPriority(data['priority'])
        return cls(**data)


@dataclass
class EventResult:
    """Event processing result."""
    event_id: str
    status: EventStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    timestamp: float = field(default_factory=time.time)


class EventHandler(ABC, Generic[T]):
    """Abstract event handler."""
    
    @abstractmethod
    async def handle(self, event: Event) -> EventResult:
        """Handle an event."""
        pass
    
    @property
    @abstractmethod
    def event_types(self) -> List[str]:
        """List of event types this handler can process."""
        pass
    
    @property
    def name(self) -> str:
        """Handler name."""
        return self.__class__.__name__


class EventStore:
    """Event store for persistence and replay."""
    
    def __init__(self, storage_path: str = "events"):
        self.storage_path = storage_path
        self.events: Dict[str, Event] = {}
        self.results: Dict[str, EventResult] = {}
        self._lock = asyncio.Lock()
    
    async def store_event(self, event: Event) -> bool:
        """Store an event."""
        async with self._lock:
            self.events[event.id] = event
            await self._persist_event(event)
            return True
    
    async def store_result(self, result: EventResult) -> bool:
        """Store event result."""
        async with self._lock:
            self.results[result.event_id] = result
            await self._persist_result(result)
            return True
    
    async def get_event(self, event_id: str) -> Optional[Event]:
        """Get an event by ID."""
        return self.events.get(event_id)
    
    async def get_result(self, event_id: str) -> Optional[EventResult]:
        """Get event result by ID."""
        return self.results.get(event_id)
    
    async def get_events_by_type(self, event_type: str, limit: int = 100) -> List[Event]:
        """Get events by type."""
        events = [
            event for event in self.events.values()
            if event.type == event_type
        ]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
    
    async def get_events_by_source(self, source: str, limit: int = 100) -> List[Event]:
        """Get events by source."""
        events = [
            event for event in self.events.values()
            if event.source == source
        ]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
    
    async def replay_events(self, event_type: Optional[str] = None) -> List[Event]:
        """Replay events for recovery."""
        events = list(self.events.values())
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        events.sort(key=lambda e: e.timestamp)
        return events
    
    async def _persist_event(self, event: Event):
        """Persist event to disk."""
        try:
            filename = f"{self.storage_path}/events/{event.id}.json"
            async with aiofiles.open(filename, 'w') as f:
                await f.write(json.dumps(event.to_dict(), indent=2))
        except Exception as e:
            logging.error(f"Failed to persist event: {e}")
    
    async def _persist_result(self, result: EventResult):
        """Persist result to disk."""
        try:
            filename = f"{self.storage_path}/results/{result.event_id}.json"
            async with aiofiles.open(filename, 'w') as f:
                await f.write(json.dumps(asdict(result), indent=2))
        except Exception as e:
            logging.error(f"Failed to persist result: {e}")


class EventRouter:
    """Event router for dispatching events to handlers."""
    
    def __init__(self):
        self.handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self.global_handlers: List[EventHandler] = []
        self.middleware: List[Callable] = []
    
    def register_handler(self, handler: EventHandler):
        """Register an event handler."""
        for event_type in handler.event_types:
            self.handlers[event_type].append(handler)
        
        logging.info(f"Registered handler: {handler.name} for {handler.event_types}")
    
    def register_global_handler(self, handler: EventHandler):
        """Register a global handler for all events."""
        self.global_handlers.append(handler)
        logging.info(f"Registered global handler: {handler.name}")
    
    def add_middleware(self, middleware: Callable):
        """Add middleware for event processing."""
        self.middleware.append(middleware)
    
    async def route_event(self, event: Event) -> List[EventResult]:
        """Route event to appropriate handlers."""
        results = []
        
        # Apply middleware
        for middleware in self.middleware:
            event = await middleware(event)
        
        # Get handlers for this event type
        handlers = self.handlers.get(event.type, [])
        
        # Add global handlers
        handlers.extend(self.global_handlers)
        
        # Process event with all handlers
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._handle_with_error(handler, event))
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and convert to EventResult
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                final_results.append(EventResult(
                    event_id=event.id,
                    status=EventStatus.FAILED,
                    error=str(result)
                ))
            elif isinstance(result, EventResult):
                final_results.append(result)
        
        return final_results
    
    async def _handle_with_error(self, handler: EventHandler, event: Event) -> EventResult:
        """Handle event with error catching."""
        try:
            return await handler.handle(event)
        except Exception as e:
            logging.error(f"Handler {handler.name} failed for event {event.id}: {e}")
            return EventResult(
                event_id=event.id,
                status=EventStatus.FAILED,
                error=str(e)
            )


class EventBus:
    """
    Main event bus for the event-driven architecture.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        rabbitmq_url: str = "amqp://localhost:5672",
        storage_path: str = "events"
    ):
        self.redis_client: Optional[redis.Redis] = None
        self.rabbitmq_connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        
        self.event_store = EventStore(storage_path)
        self.event_router = EventRouter()
        
        self.redis_url = redis_url
        self.rabbitmq_url = rabbitmq_url
        
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.running = False
        
        # Metrics
        self.events_processed = 0
        self.events_failed = 0
        self.processing_times: List[float] = []
    
    async def start(self):
        """Start the event bus."""
        # Initialize Redis
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logging.info("Redis connected to event bus")
        except Exception as e:
            logging.error(f"Failed to connect to Redis: {e}")
        
        # Initialize RabbitMQ
        try:
            self.rabbitmq_connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.rabbitmq_connection.channel()
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                "arena_events",
                ExchangeType.TOPIC,
                durable=True
            )
            
            logging.info("RabbitMQ connected to event bus")
        except Exception as e:
            logging.error(f"Failed to connect to RabbitMQ: {e}")
        
        # Create storage directories
        import os
        os.makedirs(f"{self.event_store.storage_path}/events", exist_ok=True)
        os.makedirs(f"{self.event_store.storage_path}/results", exist_ok=True)
        
        self.running = True
        logging.info("Event bus started")
    
    async def stop(self):
        """Stop the event bus."""
        self.running = False
        
        if self.rabbitmq_connection:
            await self.rabbitmq_connection.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logging.info("Event bus stopped")
    
    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str = "unknown",
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: Optional[str] = None,
        routing_key: Optional[str] = None
    ) -> str:
        """Publish an event."""
        event = Event(
            type=event_type,
            source=source,
            data=data,
            priority=priority,
            correlation_id=correlation_id,
            metadata={"routing_key": routing_key or event_type}
        )
        
        # Store event
        await self.event_store.store_event(event)
        
        # Route to local handlers
        results = await self.event_router.route_event(event)
        
        # Store results
        for result in results:
            await self.event_store.store_result(result)
            if result.status == EventStatus.COMPLETED:
                self.events_processed += 1
            else:
                self.events_failed += 1
        
        # Publish to RabbitMQ
        if self.exchange:
            try:
                message = Message(
                    json.dumps(event.to_dict()).encode(),
                    content_type="application/json",
                    delivery_mode=DeliveryMode.PERSISTENT,
                    headers={"priority": event.priority.value}
                )
                
                routing_key = routing_key or event_type
                await self.exchange.publish(message, routing_key=routing_key)
                
                logging.debug(f"Published event {event.id} to RabbitMQ")
            except Exception as e:
                logging.error(f"Failed to publish to RabbitMQ: {e}")
        
        # Publish to Redis for real-time subscribers
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    f"events:{event_type}",
                    json.dumps(event.to_dict())
                )
            except Exception as e:
                logging.error(f"Failed to publish to Redis: {e}")
        
        return event.id
    
    async def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to events."""
        self.subscribers[event_type].append(handler)
        logging.info(f"Subscribed to {event_type}")
    
    async def subscribe_to_pattern(self, pattern: str, handler: Callable):
        """Subscribe to event patterns (Redis pub/sub)."""
        if self.redis_client:
            pubsub = self.redis_client.pubsub()
            await pubsub.psubscribe(f"events:{pattern}")
            
            async def listener():
                async for message in pubsub.listen():
                    if message['type'] == 'pmessage':
                        try:
                            event_data = json.loads(message['data'])
                            event = Event.from_dict(event_data)
                            await handler(event)
                        except Exception as e:
                            logging.error(f"Pattern subscriber error: {e}")
            
            asyncio.create_task(listener())
    
    def register_handler(self, handler: EventHandler):
        """Register an event handler."""
        self.event_router.register_handler(handler)
    
    def register_global_handler(self, handler: EventHandler):
        """Register a global handler."""
        self.event_router.register_global_handler(handler)
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics."""
        return {
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "success_rate": (
                self.events_processed / (self.events_processed + self.events_failed)
                if (self.events_processed + self.events_failed) > 0 else 0
            ),
            "average_processing_time": (
                sum(self.processing_times) / len(self.processing_times)
                if self.processing_times else 0
            ),
            "handlers_registered": len(self.event_router.handlers),
            "subscribers": len(self.subscribers)
        }


# ============================================================================
# Example Event Handlers
# ============================================================================

class PortfolioUpdateHandler(EventHandler):
    """Handler for portfolio update events."""
    
    @property
    def event_types(self) -> List[str]:
        return ["portfolio.updated", "portfolio.created"]
    
    async def handle(self, event: Event) -> EventResult:
        """Handle portfolio update."""
        start_time = time.time()
        
        try:
            # Process portfolio update
            portfolio_data = event.data
            
            # Update analytics
            # Send notifications
            # Update caches
            
            processing_time = time.time() - start_time
            
            return EventResult(
                event_id=event.id,
                status=EventStatus.COMPLETED,
                result={"processed": True},
                processing_time=processing_time
            )
            
        except Exception as e:
            return EventResult(
                event_id=event.id,
                status=EventStatus.FAILED,
                error=str(e),
                processing_time=time.time() - start_time
            )


class TradingSignalHandler(EventHandler):
    """Handler for trading signal events."""
    
    @property
    def event_types(self) -> List[str]:
        return ["trading.signal.generated", "trading.signal.executed"]
    
    async def handle(self, event: Event) -> EventResult:
        """Handle trading signal."""
        start_time = time.time()
        
        try:
            signal_data = event.data
            
            # Validate signal
            # Check risk limits
            # Execute trade if approved
            
            processing_time = time.time() - start_time
            
            return EventResult(
                event_id=event.id,
                status=EventStatus.COMPLETED,
                result={"signal_processed": True},
                processing_time=processing_time
            )
            
        except Exception as e:
            return EventResult(
                event_id=event.id,
                status=EventStatus.FAILED,
                error=str(e),
                processing_time=time.time() - start_time
            )


# ============================================================================
# Example Usage
# ============================================================================

async def example_event_bus_setup():
    """Example setup of event bus."""
    event_bus = EventBus()
    await event_bus.start()
    
    # Register handlers
    event_bus.register_handler(PortfolioUpdateHandler())
    event_bus.register_handler(TradingSignalHandler())
    
    # Publish events
    await event_bus.publish(
        "portfolio.updated",
        {"user_id": "user123", "value": 25000.0},
        source="portfolio_service"
    )
    
    await event_bus.publish(
        "trading.signal.generated",
        {"symbol": "BTC", "signal": "BUY", "confidence": 0.85},
        source="trading_service",
        priority=EventPriority.HIGH
    )
    
    # Get metrics
    metrics = await event_bus.get_metrics()
    print(f"Event bus metrics: {metrics}")
    
    return event_bus


if __name__ == "__main__":
    async def main():
        event_bus = await example_event_bus_setup()
        
        try:
            # Keep running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await event_bus.stop()
    
    asyncio.run(main())
