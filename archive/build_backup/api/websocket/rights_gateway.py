"""Real-time WebSocket handler for rights-preserving request-response patterns.

Provides WebSocket endpoints for:
- Real-time request streaming with rights validation
- Live boundary enforcement notifications
- Monitoring dashboard data feed
- Audit log streaming
"""

from __future__ import annotations

import asyncio
import json
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Callable, Optional
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.websockets import WebSocketState

from api.schema.rights_boundary import (
    BoundaryAction,
    BoundaryDecision,
    HumanRightsImpact,
    HumanRightCategory,
    MonitoringMetrics,
    RequestType,
    RightsPreservingRequest,
    RiskLevel,
    WebSocketMessage,
)


class RightsPreservingWebSocketManager:
    """Manages WebSocket connections with rights-preserving boundary enforcement."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.connection_metadata: dict[str, dict[str, Any]] = {}
        self.message_handlers: dict[str, Callable] = {}
        self._shutdown_event = asyncio.Event()
        
    async def connect(self, websocket: WebSocket, client_id: str, metadata: dict[str, Any] | None = None) -> None:
        """Accept a new WebSocket connection with rights validation."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = metadata or {
            "connected_at": datetime.utcnow().isoformat(),
            "client_ip": getattr(websocket.client, "host", "unknown"),
            "connection_id": str(uuid4())[:8],
        }
        
        # Send welcome message with rights notice
        welcome = WebSocketMessage(
            correlation_id=str(uuid4())[:12],
            message_type="welcome",
            payload={
                "message": "Connected to GRID Sovereign Rights-Preserving Gateway",
                "client_id": client_id,
                "rights_notice": (
                    "This system enforces human rights protections. "
                    "All requests are analyzed for potential rights violations. "
                    "Prohibited research domains are automatically blocked."
                ),
                "prohibited_domains": self._get_prohibited_domains(),
                "version": "1.0.0",
            },
            status="connected",
        )
        await self._send_message(client_id, welcome)
        
    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_metadata:
            del self.connection_metadata[client_id]
            
    async def broadcast(self, message: WebSocketMessage) -> None:
        """Broadcast a message to all connected clients."""
        disconnected = []
        for client_id, websocket in self.active_connections.items():
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message.dict())
            except Exception:
                disconnected.append(client_id)
                
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
            
    async def send_to_client(self, client_id: str, message: WebSocketMessage) -> bool:
        """Send a message to a specific client."""
        return await self._send_message(client_id, message)
        
    async def _send_message(self, client_id: str, message: WebSocketMessage) -> bool:
        """Internal method to send message with error handling."""
        if client_id not in self.active_connections:
            return False
            
        websocket = self.active_connections[client_id]
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(message.dict())
                return True
        except Exception:
            self.disconnect(client_id)
            
        return False
        
    def _get_prohibited_domains(self) -> list[str]:
        """Get list of prohibited research domains."""
        return [
            "surveillance_technology",
            "discriminatory_profiling",
            "autonomous_weapons",
            "forced_behavior_modification",
            "exploitative_data_collection",
            "coercive_psychological_manipulation",
            "non_consensual_biometric_tracking",
            "social_credit_scoring",
            "predictive_policing_without_oversight",
            "algorithmic_discrimination_enforcement",
        ]
        
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register a handler for a specific message type."""
        self.message_handlers[message_type] = handler
        
    async def handle_message(self, client_id: str, raw_message: dict[str, Any]) -> WebSocketMessage | None:
        """Handle an incoming WebSocket message with rights validation."""
        start_time = time.time()
        
        try:
            # Parse message
            msg_type = raw_message.get("message_type", "unknown")
            correlation_id = raw_message.get("correlation_id", str(uuid4())[:12])
            payload = raw_message.get("payload", {})
            
            # Create base response
            response = WebSocketMessage(
                correlation_id=correlation_id,
                message_type=f"{msg_type}_response",
                status="processing",
            )
            
            # Rights validation on request content
            content = payload.get("content", "")
            request_type = payload.get("request_type", "unknown")
            
            # Check for prohibited content
            rights_check = await self._validate_human_rights(content, request_type)
            response.rights_validated = True
            
            if rights_check.risk_level == RiskLevel.VIOLATION:
                response.rights_violations = rights_check.potential_harms
                response.status = "blocked"
                response.payload = {
                    "error": "Request blocked due to human rights violation",
                    "violation_details": rights_check.dict(),
                    "action_taken": "deny",
                }
                response.processing_time_ms = int((time.time() - start_time) * 1000)
                return response
            
            if rights_check.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                response.rights_violations = rights_check.potential_harms
                response.requires_acknowledgment = True
                response.payload["rights_warning"] = rights_check.review_reason
            
            # Route to appropriate handler
            handler = self.message_handlers.get(msg_type)
            if handler:
                try:
                    result = await handler(payload, rights_check)
                    response.payload.update(result)
                    response.status = "completed"
                except Exception as e:
                    response.status = "error"
                    response.payload["error"] = str(e)
            else:
                response.status = "unknown_type"
                response.payload["error"] = f"No handler for message type: {msg_type}"
            
            response.processing_time_ms = int((time.time() - start_time) * 1000)
            return response
            
        except Exception as e:
            return WebSocketMessage(
                correlation_id=str(uuid4())[:12],
                message_type="error",
                status="error",
                payload={"error": f"Message handling failed: {str(e)}"},
            )
    
    async def _validate_human_rights(
        self, content: str, request_type: str
    ) -> HumanRightsImpact:
        """Validate content against human rights guardrails."""
        impact = HumanRightsImpact(risk_level=RiskLevel.NONE)
        content_lower = content.lower() if content else ""
        
        # Check prohibited patterns
        prohibited_patterns = {
            "surveillance_technology": [
                "mass surveillance", "warrantless tracking", "covert monitoring",
                "spy on", "track without consent", "surveillance capitalism"
            ],
            "discriminatory_profiling": [
                "racial profiling", "ethnic targeting", "discriminatory algorithm",
                "biased scoring", "minority exclusion"
            ],
            "autonomous_weapons": [
                "lethal autonomous", "killer robot", "weaponized ai",
                "automated targeting", "drone strike ai"
            ],
            "forced_behavior_modification": [
                "coercive nudging", "forced compliance", "behavioral control",
                "manipulative persuasion", "coercive tracking"
            ],
            "exploitative_data_collection": [
                "data harvesting", "exploitative tracking", "predatory collection",
                "non-consensual data", "privacy violation"
            ],
            "coercive_psychological_manipulation": [
                "psychological manipulation", "coercive control", "mental coercion",
                "emotional exploitation", "gaslighting at scale"
            ],
            "non_consensual_biometric_tracking": [
                "facial recognition tracking", "biometric surveillance",
                "emotion tracking without consent", "non-consensual face scan"
            ],
            "social_credit_scoring": [
                "social credit", "citizen score", "behavioral scoring system",
                "trustworthiness ranking", "social ranking"
            ],
            "predictive_policing_without_oversight": [
                "predictive policing", "crime prediction", "algorithmic policing",
                "pre-crime detection", "predictive incarceration"
            ],
            "algorithmic_discrimination_enforcement": [
                "algorithmic bias enforcement", "automated discrimination",
                "discriminatory ai deployment", "unfair algorithmic decision"
            ],
        }
        
        detected_domains = []
        for domain, patterns in prohibited_patterns.items():
            for pattern in patterns:
                if pattern in content_lower:
                    detected_domains.append(domain)
                    impact.rights_categories.append(HumanRightCategory.RIGHT_TO_PRIVACY)
                    impact.potential_harms.append(f"Prohibited domain: {domain}")
                    break
        
        if detected_domains:
            impact.risk_level = RiskLevel.VIOLATION
            impact.mitigation_required = True
            impact.requires_human_review = True
            impact.review_reason = f"Prohibited research domains detected: {', '.join(detected_domains)}"
        
        # Check for high-risk content requiring review
        high_risk_keywords = [
            "vulnerable population", "children data", "mental health tracking",
            "political manipulation", "election interference", "health data monetization"
        ]
        
        high_risk_detected = [kw for kw in high_risk_keywords if kw in content_lower]
        if high_risk_detected and impact.risk_level != RiskLevel.VIOLATION:
            impact.risk_level = RiskLevel.HIGH
            impact.requires_human_review = True
            impact.review_reason = f"High-risk keywords detected: {', '.join(high_risk_detected)}"
            impact.potential_harms.extend(high_risk_detected)
        
        return impact


class WebSocketEndpoint:
    """WebSocket endpoint factory for rights-preserving real-time communication."""
    
    def __init__(self, manager: RightsPreservingWebSocketManager):
        self.manager = manager
        
    async def handle_websocket(self, websocket: WebSocket, client_id: str) -> None:
        """Main WebSocket handler with rights enforcement."""
        await self.manager.connect(websocket, client_id)
        
        try:
            while True:
                # Receive message
                raw_data = await websocket.receive_text()
                
                try:
                    data = json.loads(raw_data)
                except json.JSONDecodeError:
                    error_msg = WebSocketMessage(
                        correlation_id=str(uuid4())[:12],
                        message_type="error",
                        status="error",
                        payload={"error": "Invalid JSON format"},
                    )
                    await self.manager.send_to_client(client_id, error_msg)
                    continue
                
                # Handle message with rights validation
                response = await self.manager.handle_message(client_id, data)
                if response:
                    await self.manager.send_to_client(client_id, response)
                    
        except WebSocketDisconnect:
            self.manager.disconnect(client_id)
        except Exception as e:
            # Log error and disconnect
            error_msg = WebSocketMessage(
                correlation_id=str(uuid4())[:12],
                message_type="error",
                status="error",
                payload={"error": f"Connection error: {str(e)}"},
            )
            await self.manager.send_to_client(client_id, error_msg)
            self.manager.disconnect(client_id)


# Global manager instance
websocket_manager = RightsPreservingWebSocketManager()
websocket_endpoint = WebSocketEndpoint(websocket_manager)

__all__ = [
    "RightsPreservingWebSocketManager",
    "WebSocketEndpoint",
    "websocket_manager",
    "websocket_endpoint",
]
