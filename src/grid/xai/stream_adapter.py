"""
XAI Stream Adapter for GRID
Handles streaming XAI responses with chunking and progress tracking.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class StreamChunk:
    """Single chunk in a streaming XAI response."""

    chunk_id: str
    content: str
    sequence_number: int
    is_complete: bool = False
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StreamProgress:
    """Progress tracking for streaming responses."""

    total_chunks: int = 0
    processed_chunks: int = 0
    start_time: datetime = None
    estimated_completion: float = 0.0

    def get_completion_percentage(self) -> float:
        if self.total_chunks == 0:
            return 0.0
        return (self.processed_chunks / self.total_chunks) * 100.0

    def get_eta(self) -> str:
        if self.processed_chunks == 0 or self.estimated_completion == 0:
            return "Calculating..."

        elapsed = (datetime.now() - self.start_time).total_seconds()
        if elapsed == 0:
            return "Calculating..."

        chunks_per_second = self.processed_chunks / elapsed
        remaining_chunks = self.total_chunks - self.processed_chunks
        eta_seconds = remaining_chunks / chunks_per_second if chunks_per_second > 0 else 0

        if eta_seconds == 0:
            return "Complete"
        elif eta_seconds < 60:
            return f"{int(eta_seconds)}s"
        elif eta_seconds < 3600:
            return f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
        else:
            return f"{int(eta_seconds // 3600)}h {int((eta_seconds % 3600) // 60)}m"


class XAIStreamAdapter:
    """
    Adapter for handling streaming XAI responses in GRID.

    Provides chunking, progress tracking, and stream control
    while integrating with existing XAI explainer.
    """

    def __init__(self, chunk_size: int = 512, max_concurrent_streams: int = 5):
        self.chunk_size = chunk_size
        self.max_concurrent_streams = max_concurrent_streams
        self.active_streams: dict[str, StreamProgress] = {}
        self.chunk_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.is_paused = False
        self.pause_event = asyncio.Event()

    async def process_streaming_response(
        self,
        response_stream: Any,
        stream_id: str,
        explanation_generator: Callable | None = None,
        progress_callback: Callable | None = None,
    ) -> list[StreamChunk]:
        """
        Process a streaming XAI response into chunks.

        Args:
            response_stream: Raw XAI response stream
            stream_id: Unique identifier for this stream
            explanation_generator: Optional function to generate explanations
            progress_callback: Optional callback for progress updates

        Returns:
            List of processed chunks
        """
        chunks = []
        progress = StreamProgress(total_chunks=0, processed_chunks=0, start_time=datetime.now())

        try:
            async for chunk_data in response_stream:
                if self.is_paused:
                    await self.pause_event.wait()

                # Process chunk based on response format
                if hasattr(chunk_data, "content"):
                    chunk = StreamChunk(
                        chunk_id=f"{stream_id}_{len(chunks)}",
                        content=chunk_data.content,
                        sequence_number=len(chunks),
                        metadata=chunk_data.get("metadata", {}),
                    )
                elif hasattr(chunk_data, "text"):
                    chunk = StreamChunk(
                        chunk_id=f"{stream_id}_{len(chunks)}",
                        content=chunk_data.text,
                        sequence_number=len(chunks),
                        metadata={},
                    )
                else:
                    # Handle other response formats
                    chunk = StreamChunk(
                        chunk_id=f"{stream_id}_{len(chunks)}",
                        content=str(chunk_data),
                        sequence_number=len(chunks),
                        metadata={"type": "raw_response"},
                    )

                chunks.append(chunk)
                progress.processed_chunks += 1

                # Call progress callback if provided
                if progress_callback:
                    try:
                        await progress_callback(stream_id, progress)
                    except Exception as e:
                        logger.error(f"Progress callback error: {e}")

                # Call explanation generator if provided
                if explanation_generator:
                    try:
                        explanation = await explanation_generator(chunk, progress)
                        chunk.metadata["explanation"] = explanation
                    except Exception as e:
                        logger.error(f"Explanation generator error: {e}")

                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)

                # Check if stream is complete
                if hasattr(chunk_data, "done") and chunk_data.done:
                    chunk.is_complete = True
                    progress.estimated_completion = (datetime.now() - progress.start_time).total_seconds()
                    break

        except Exception as e:
            logger.error(f"Stream processing error: {e}")

        # Store progress for this stream
        self.active_streams[stream_id] = progress

        return chunks

    async def control_stream(self, stream_id: str, action: str) -> bool:
        """
        Control a streaming response (pause, resume, stop).

        Args:
            stream_id: Stream identifier
            action: Control action ('pause', 'resume', 'stop')

        Returns:
            Success status
        """
        if stream_id not in self.active_streams:
            return False

        if action == "pause":
            self.is_paused = True
            self.pause_event.clear()
            return True
        elif action == "resume":
            self.is_paused = False
            self.pause_event.set()
            return True
        elif action == "stop":
            # Mark stream as complete
            if stream_id in self.active_streams:
                self.active_streams[stream_id].processed_chunks = self.active_streams[stream_id].total_chunks
                del self.active_streams[stream_id]
            return True
        else:
            return False

    def get_stream_status(self, stream_id: str) -> StreamProgress | None:
        """
        Get current status of a streaming response.
        """
        return self.active_streams.get(stream_id)

    def get_all_stream_status(self) -> dict[str, StreamProgress]:
        """
        Get status of all active streams.
        """
        return self.active_streams.copy()

    async def cleanup_completed_streams(self):
        """
        Clean up completed streams from memory.
        """
        completed_streams = [
            stream_id
            for stream_id, progress in self.active_streams.items()
            if progress.processed_chunks >= progress.total_chunks
        ]

        for stream_id in completed_streams:
            del self.active_streams[stream_id]

        logger.info(f"Cleaned up {len(completed_streams)} completed streams")

    def get_performance_metrics(self) -> dict[str, Any]:
        """
        Get performance metrics for stream adapter.
        """
        active_count = len(self.active_streams)
        total_processed = sum(progress.processed_chunks for progress in self.active_streams.values())

        return {
            "active_streams": active_count,
            "total_chunks_processed": total_processed,
            "average_chunks_per_stream": total_processed / active_count if active_count > 0 else 0,
            "is_paused": self.is_paused,
            "max_concurrent_streams": self.max_concurrent_streams,
        }


# Integration with existing XAI explainer
try:
    from grid.xai.explainer import XAIExplainer

    class EnhancedXAIAdapter(XAIStreamAdapter):
        """
        Enhanced adapter that combines streaming capabilities with XAI explanations.
        """

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.explainer = XAIExplainer()

        async def process_with_explanation(
            self,
            response_stream: Any,
            stream_id: str,
            context: dict[str, Any] = None,
            progress_callback: Callable | None = None,
        ) -> dict[str, Any]:
            """
            Process streaming response with enhanced explanations.
            """
            chunks = await self.process_streaming_response(
                response_stream=response_stream,
                stream_id=stream_id,
                explanation_generator=self._generate_explanation,
                progress_callback=progress_callback,
            )

            # Generate comprehensive explanation
            final_explanation = await self.explainer.synthesize_explanation(
                decision_id=stream_id,
                context=context,
                detected_patterns=[],  # Could be extracted from response
                cognitive_state={},  # Could be derived from context
            )

            return {
                "stream_id": stream_id,
                "chunks": len(chunks),
                "explanation": final_explanation,
                "performance_metrics": self.get_performance_metrics(),
            }

        async def _generate_explanation(self, chunk: StreamChunk, progress: StreamProgress) -> dict[str, Any]:
            """
            Generate explanation for a specific chunk.
            """
            return await self.explainer.explain_case_execution(
                case_id=chunk.chunk_id,
                result={"content": chunk.content, "metadata": chunk.metadata},
                cognitive_state={
                    "load": progress.processed_chunks / progress.total_chunks,
                    "processing_mode": "streaming",
                },
            )

except ImportError:
    logger.warning("XAIExplainer not available, using fallback implementation")

    class EnhancedXAIAdapter(XAIStreamAdapter):
        """
        Fallback enhanced adapter without XAI explainer integration.
        """

        async def process_with_explanation(
            self,
            response_stream: Any,
            stream_id: str,
            context: dict[str, Any] = None,
            progress_callback: Callable | None = None,
        ) -> dict[str, Any]:
            """
            Process streaming response with fallback explanations.
            """
            chunks = await self.process_streaming_response(
                response_stream=response_stream,
                stream_id=stream_id,
                explanation_generator=None,  # No explanation generator
                progress_callback=progress_callback,
            )

            # Simple fallback explanation
            fallback_explanation = {
                "stream_id": stream_id,
                "chunks_processed": len(chunks),
                "status": "completed" if all(c.is_complete for c in chunks) else "in_progress",
                "cognitive_load": len(chunks) / 100.0,  # Simple load metric
            }

            return {
                "stream_id": stream_id,
                "chunks": len(chunks),
                "explanation": fallback_explanation,
                "performance_metrics": self.get_performance_metrics(),
            }
