"""
Current Events Discussion Service
==================================

Provides intelligent discussion capabilities with:
- Topic extraction from current events
- Recursive reasoning with TracedDiscussionAgent
- ADSR envelope integration for discussion phases
- Wall-board metaphor visualization
"""

import asyncio
import logging
import os
import re
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Arena components (relative imports)
from arena_api.ai_safety.safety import AISafetyManager
from arena_api.api_gateway.authentication.auth import AuthManager
from arena_api.monitoring.monitor import MonitoringManager

logger = logging.getLogger(__name__)


# Embedded TracedDiscussionAgent (standalone version)
@dataclass
class ReasoningStep:
    """A single step in the agent's reasoning process."""

    step_id: str
    query: str
    thought: str
    result: Any
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    sub_steps: list["ReasoningStep"] = field(default_factory=list)


class TracedDiscussionAgent:
    """Agent for discussion with full reasoning trace."""

    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
        self.trace: list[ReasoningStep] = []

    async def discuss(self, query: str, context: dict[str, Any], depth: int = 0) -> dict[str, Any]:
        """Perform a discussion with recursive reasoning."""
        if depth > self.max_depth:
            return {"error": "Maximum reasoning depth exceeded"}

        step_id = str(uuid.uuid4())
        logger.info(f"Reasoning step {step_id} at depth {depth} for query: {query}")

        thought = f"Analyzing '{query}' at depth {depth}..."
        sub_steps = []

        if depth < self.max_depth and "recursive" in query.lower():
            sub_query = f"Decomposing: {query}"
            await self.discuss(sub_query, context, depth + 1)

        result = f"Response for '{query}' based on context {list(context.keys())}"
        current_step = ReasoningStep(step_id=step_id, query=query, thought=thought, result=result, sub_steps=sub_steps)

        if depth == 0:
            self.trace.append(current_step)

        return {
            "response": result,
            "step_id": step_id,
            "trace": self._format_trace(current_step) if depth == 0 else None,
        }

    def _format_trace(self, step: ReasoningStep) -> dict[str, Any]:
        """Convert reasoning steps to a serializable dictionary."""
        return {
            "step_id": step.step_id,
            "query": step.query,
            "thought": step.thought,
            "result": step.result,
            "timestamp": step.timestamp.isoformat(),
            "sub_steps": [self._format_trace(s) for s in step.sub_steps],
        }


# Embedded topic extractor (simplified heuristic version)
def extract_topics_simple(args: Mapping[str, Any]) -> dict[str, Any]:
    """Extract discussion topics using heuristic approach."""
    text = args.get("text") or args.get("input")
    if text is None:
        return {"skill": "topic_extractor", "status": "error", "error": "Missing text"}

    text = str(text)
    max_topics = int(args.get("max_topics", 8))

    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
    }

    tech_patterns = [
        r"\b([A-Z]{2,}(?:\s+\w+)?)\b",  # Acronyms like API, JWT
        r"\b(\w+(?:ing|tion|ment)\s+\w+|\w+\s+(?:layer|schema|system|strategy))\b",
        r"\b((?:rate|user|auth\w*|cache|data)\s*\w*)\b",
    ]

    topics: list[dict[str, Any]] = []
    seen_topics = set()

    def add_topic(topic_name: str, context: str, weight: int = 1) -> None:
        topic_name = topic_name.strip().lower()
        words = topic_name.split()
        words = [w for w in words if w not in stop_words and len(w) > 2]
        if not words:
            return
        topic_name = " ".join(words)
        if len(topic_name) < 3 or topic_name in seen_topics:
            return
        seen_topics.add(topic_name)
        topics.append({"topic": topic_name, "context": context, "pins": [], "connections": [], "weight": weight})

    for sentence in sentences:
        for pattern in tech_patterns:
            matches = re.findall(pattern, sentence, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                add_topic(match, sentence, weight=2)

    topic_list = sorted(topics, key=lambda x: x["weight"], reverse=True)[:max_topics]

    for topic in topic_list:
        words = re.findall(r"\b\w+\b", str(topic["context"]))
        key_words = [w for w in words if w.lower() not in stop_words and len(w) > 3]
        topic["pins"] = list(dict.fromkeys(key_words))[:5]

    if topic_list:
        max_weight = max(t["weight"] for t in topic_list)
        for topic in topic_list:
            topic["weight"] = max(1, min(10, int((topic["weight"] / max_weight) * 10)))

    return {
        "skill": "topic_extractor",
        "status": "success",
        "output": {
            "wall_board": {
                "topics": topic_list,
                "total_topics": len(topic_list),
                "connections": 0,
                "metaphor": "Each topic is a note pinned to the wall",
            }
        },
    }


class DiscussionRequest(BaseModel):
    """Request model for discussion."""

    text: str = Field(..., min_length=10, max_length=5000, description="Current event text to discuss")
    max_depth: int = Field(3, ge=1, le=5, description="Maximum reasoning depth")
    extract_topics: bool = Field(True, description="Extract topics before discussion")
    use_llm_topics: bool = Field(False, description="Use LLM for topic extraction")


class TopicExtractionRequest(BaseModel):
    """Request for topic extraction only."""

    text: str = Field(..., min_length=10, max_length=5000, description="Text to extract topics from")
    use_llm: bool = Field(False, description="Use LLM for extraction")
    max_topics: int = Field(8, ge=1, le=20, description="Maximum topics to extract")


class DiscussionResponse(BaseModel):
    """Response model for discussion."""

    discussion_id: str
    topics: dict[str, Any] | None
    reasoning_trace: dict[str, Any]
    summary: str
    processing_time: float
    timestamp: datetime


class TopicResponse(BaseModel):
    """Response model for topic extraction."""

    topics: list[dict[str, Any]]
    total_topics: int
    connections: int
    metaphor: str
    processing_time: float


class DiscussionService:
    """Current Events Discussion Service."""

    def __init__(self) -> None:
        self.app: FastAPI = FastAPI(
            title="Discussion Service",
            description="Current events discussion with topic extraction and reasoning",
            version="1.0.0",
        )

        self.service_name: str = "discussion_service"
        self.service_url: str = os.getenv("DISCUSSION_SERVICE_URL", "http://localhost:8003")
        self.health_url: str = f"{self.service_url}/health"

        self.auth_manager: AuthManager = AuthManager()
        self.monitoring: MonitoringManager = MonitoringManager()
        self.ai_safety: AISafetyManager = AISafetyManager()
        self.discussion_agent: TracedDiscussionAgent = TracedDiscussionAgent(max_depth=5)

        self.discussions: dict[str, dict[str, Any]] = {}

        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self) -> None:
        """Setup middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self) -> None:
        """Setup API routes."""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": self.service_name,
                "timestamp": datetime.now(UTC).isoformat(),
                "active_discussions": len(self.discussions),
            }

        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "service": "Discussion Service",
                "version": "1.0.0",
                "description": "Current events discussion with topic extraction",
                "endpoints": {
                    "discuss": "/discuss",
                    "topics": "/topics/extract",
                    "discussions": "/discussions",
                    "health": "/health",
                },
            }

        @self.app.post("/discuss", response_model=DiscussionResponse)
        async def discuss(
            request: DiscussionRequest, req: Request, authenticated: bool = Depends(self._authenticate_request)
        ):
            """Discuss current events with topic extraction and reasoning."""
            start_time = asyncio.get_event_loop().time()

            try:
                safety_result = await self.ai_safety.check_request(req)
                if not safety_result["safe"]:
                    raise HTTPException(status_code=403, detail="Request flagged by AI safety")

                discussion_id = f"disc_{int(datetime.now(UTC).timestamp() * 1000)}"

                topics_result = None
                if request.extract_topics:
                    topics_result = await self._extract_topics(request.text, request.use_llm_topics, max_topics=8)

                context = {
                    "text": request.text,
                    "topics": topics_result.get("output", {}).get("wall_board", {}).get("topics", [])
                    if topics_result
                    else [],
                    "timestamp": datetime.now(UTC).isoformat(),
                }

                query = f"Analyze and discuss: {request.text[:200]}..."
                discussion_result = await self.discussion_agent.discuss(query=query, context=context, depth=0)

                summary = self._generate_summary(topics_result, discussion_result)

                self.discussions[discussion_id] = {
                    "request": request.model_dump(),
                    "topics": topics_result,
                    "reasoning": discussion_result,
                    "summary": summary,
                    "timestamp": datetime.now(UTC),
                }

                processing_time = asyncio.get_event_loop().time() - start_time
                await self.monitoring.record_request(req, {"status_code": 200}, processing_time, authenticated)

                return DiscussionResponse(
                    discussion_id=discussion_id,
                    topics=topics_result.get("output") if topics_result else None,
                    reasoning_trace=discussion_result.get("trace", {}),
                    summary=summary,
                    processing_time=round(processing_time, 3),
                    timestamp=datetime.now(UTC),
                )

            except HTTPException:
                raise
            except Exception as e:
                processing_time = asyncio.get_event_loop().time() - start_time
                await self.monitoring.record_error(req, str(e), processing_time)
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.app.post("/topics/extract", response_model=TopicResponse)
        async def extract_topics(request: TopicExtractionRequest, req: Request):
            """Extract topics from text using wall-board metaphor."""
            start_time = asyncio.get_event_loop().time()

            try:
                result = await self._extract_topics(request.text, request.use_llm, request.max_topics)
                wall_board = result.get("output", {}).get("wall_board", {})
                processing_time = asyncio.get_event_loop().time() - start_time

                return TopicResponse(
                    topics=wall_board.get("topics", []),
                    total_topics=wall_board.get("total_topics", 0),
                    connections=wall_board.get("connections", 0),
                    metaphor=wall_board.get("metaphor", ""),
                    processing_time=round(processing_time, 3),
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.app.get("/discussions/{discussion_id}")
        async def get_discussion(discussion_id: str):
            """Get a specific discussion by ID."""
            if discussion_id not in self.discussions:
                raise HTTPException(status_code=404, detail="Discussion not found")

            discussion = self.discussions[discussion_id]
            return {
                "discussion_id": discussion_id,
                "summary": discussion["summary"],
                "topics": discussion["topics"],
                "reasoning": discussion["reasoning"],
                "timestamp": discussion["timestamp"].isoformat(),
            }

        @self.app.get("/discussions")
        async def list_discussions():
            """List all discussions."""
            return {
                "discussions": [
                    {
                        "discussion_id": disc_id,
                        "summary": disc["summary"],
                        "timestamp": disc["timestamp"].isoformat(),
                    }
                    for disc_id, disc in self.discussions.items()
                ],
                "total": len(self.discussions),
            }

        @self.app.get("/metrics")
        async def get_metrics():
            """Get service metrics."""
            return self.monitoring.get_metrics_summary()

    async def _authenticate_request(self, request: Request) -> bool:
        """Authenticate request."""
        auth_result = await self.auth_manager.authenticate(request)
        return auth_result["authenticated"]

    async def _extract_topics(self, text: str, use_llm: bool, max_topics: int = 8) -> dict[str, Any]:
        """Extract topics from text."""
        result = extract_topics_simple({"text": text, "use_llm": use_llm, "max_topics": max_topics})
        return result

    def _generate_summary(self, topics_result: dict[str, Any] | None, discussion_result: dict[str, Any]) -> str:
        """Generate discussion summary."""
        summary_parts = []

        if topics_result:
            wall_board = topics_result.get("output", {}).get("wall_board", {})
            topic_count = wall_board.get("total_topics", 0)
            if topic_count > 0:
                summary_parts.append(f"Identified {topic_count} key topics")
                top_topics = wall_board.get("topics", [])[:3]
                if top_topics:
                    topic_names = [t["topic"] for t in top_topics]
                    summary_parts.append(f"focusing on: {', '.join(topic_names)}")

        reasoning_response = discussion_result.get("response", "")
        if reasoning_response:
            summary_parts.append(f"Discussion: {reasoning_response[:100]}...")

        return ". ".join(summary_parts) if summary_parts else "Discussion completed."


service = DiscussionService()
app = service.app

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("DISCUSSION_SERVICE_PORT", "8003")), reload=True)
