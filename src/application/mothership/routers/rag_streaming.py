"""FastAPI router for streaming RAG endpoints."""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from tools.rag.conversational_rag import ConversationalRAGEngine, create_conversational_rag_engine
from tools.rag.config import RAGConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])

# Global RAG engine instance
_rag_engine: Optional[ConversationalRAGEngine] = None


def get_rag_engine() -> ConversationalRAGEngine:
    """Get or create the global RAG engine."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = create_conversational_rag_engine()
    return _rag_engine


# Pydantic models for streaming API

class RAGQueryRequest(BaseModel):
    """Request model for RAG queries."""
    
    query: str = Field(..., description="The query to search")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    top_k: Optional[int] = Field(None, description="Number of documents to retrieve")
    temperature: float = Field(0.7, description="LLM temperature")
    enable_conversation: bool = Field(True, description="Enable conversation context")
    enable_multi_hop: Optional[bool] = Field(None, description="Enable multi-hop reasoning")


class RAGQueryStreamResponse(BaseModel):
    """Streaming response model for RAG queries."""
    
    type: str = Field(..., description="Response type")
    data: Dict[str, Any] = Field(..., description="Response data")


class RAGSessionCreateRequest(BaseModel):
    """Request to create a new RAG session."""
    
    session_id: str = Field(..., description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Session metadata")


class RAGSessionResponse(BaseModel):
    """Response for session operations."""
    
    session_id: str = Field(..., description="Session identifier")
    metadata: Dict[str, Any] = Field(..., description="Session metadata")
    turn_count: int = Field(..., description="Number of turns in session")
    created_at: str = Field(..., description="Session creation timestamp")


@dataclass
class StreamChunk:
    """Single chunk in streaming response."""
    
    type: str
    data: Dict[str, Any]
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({"type": self.type, "data": self.data}, ensure_ascii=False)


# Streaming endpoint for RAG queries
@router.post("/query/stream")
async def query_rag_stream(request: RAGQueryRequest) -> StreamingResponse:
    """Stream RAG query results with real-time updates.
    
    Streams different stages of the RAG process:
    1. Retrieval started
    2. Documents retrieved
    3. Reasoning performed (if multi-hop)
    4. Answer generation
    5. Final result
    """
    engine = get_rag_engine()
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response chunks."""
        
        # Stage 1: Query analysis and retrieval start
        yield StreamChunk(
            type="analysis_started",
            data={
                "query": request.query,
                "session_id": request.session_id,
                "timestamp": asyncio.get_event_loop().time()
            }
        ).to_json() + "\n"
        
        # Stage 2: Retrieval process
        yield StreamChunk(
            type="retrieval_started",
            data={"query": request.query}
        ).to_json() + "\n"
        
        # Stage 3: Simulate retrieval progress
        for progress in range(0, 101, 20):
            yield StreamChunk(
                type="retrieval_progress",
                data={"progress": progress, "status": f"Retrieving documents... {progress}%"}
            ).to_json() + "\n"
            await asyncio.sleep(0.1)  # Simulate work
        
        # Stage 4: Execute query
        try:
            result = await engine.query(
                query_text=request.query,
                top_k=request.top_k,
                temperature=request.temperature,
                session_id=request.session_id,
                use_conversation=request.enable_conversation,
                enable_multi_hop=request.enable_multi_hop
            )
            
            # Stage 5: Documents retrieved
            yield StreamChunk(
                type="documents_retrieved",
                data={
                    "count": len(result.get("sources", [])),
                    "sources_preview": [
                        {
                            "path": source.get("metadata", {}).get("path", "Unknown"),
                            "confidence": source.get("confidence", 0.0)
                        }
                        for source in result.get("sources", [])[:3]
                    ]
                }
            ).to_json() + "\n"
            
            # Stage 6: Answer generation
            if result.get("multi_hop_used", False):
                yield StreamChunk(
                    type="multi_hop_completed",
                    data={
                        "hops": result.get("hops_performed", 1),
                        "follow_up_queries": result.get("follow_up_queries", [])
                    }
                ).to_json() + "\n"
            
            # Stage 7: Stream answer
            answer = result.get("answer", "")
            for i, chunk in enumerate(chunk_text(answer, chunk_size=50)):
                yield StreamChunk(
                    type="answer_chunk",
                    data={
                        "chunk": chunk,
                        "chunk_number": i + 1,
                        "total_chunks": (len(answer) // 50) + 1,
                        "progress": min(100, int((i + 1) / ((len(answer) // 50) + 1) * 100))
                    }
                ).to_json() + "\n"
                await asyncio.sleep(0.05)  # Simulate streaming
            
            # Stage 8: Final result
            yield StreamChunk(
                type="complete",
                data={
                    "answer": result.get("answer", ""),
                    "sources": result.get("sources", []),
                    "conversation_metadata": result.get("conversation_metadata", {}),
                    "multi_hop_used": result.get("multi_hop_used", False)
                }
            ).to_json() + "\n"
            
        except Exception as e:
            yield StreamChunk(
                type="error",
                data={"error": str(e), "query": request.query}
            ).to_json() + "\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="application/x-ndjson",
        headers={
            "Transfer-Encoding": "chunked",
            "X-Content-Type-Options": "nosniff",
        }
    )


@router.post("/query/batch")
async def query_rag_batch(requests: List[RAGQueryRequest]) -> Dict[str, Any]:
    """Execute multiple RAG queries in batch with progress streaming."""
    engine = get_rag_engine()
    
    async def batch_process() -> AsyncGenerator[str, None]:
        """Process batch queries with progress streaming."""
        
        total_queries = len(requests)
        
        yield StreamChunk(
            type="batch_started",
            data={"total_queries": total_queries}
        ).to_json() + "\n"
        
        results = []
        for i, request in enumerate(requests):
            # Progress update
            yield StreamChunk(
                type="query_progress",
                data={
                    "current": i + 1,
                    "total": total_queries,
                    "progress": int((i + 1) / total_queries * 100),
                    "query": request.query
                }
            ).to_json() + "\n"
            
            # Execute query
            try:
                result = await engine.query(
                    query_text=request.query,
                    top_k=request.top_k,
                    temperature=request.temperature,
                    session_id=request.session_id,
                    use_conversation=request.enable_conversation,
                    enable_multi_hop=request.enable_multi_hop
                )
                
                results.append({
                    "query": request.query,
                    **result
                })
                
            except Exception as e:
                results.append({
                    "query": request.query,
                    "error": str(e)
                })
            
            yield StreamChunk(
                type="query_completed",
                data={
                    "index": i,
                    "query": request.query,
                    "success": "error" not in results[-1]
                }
            ).to_json() + "\n"
        
        # Final batch result
        yield StreamChunk(
            type="batch_completed",
            data={
                "total_queries": total_queries,
                "successful_queries": sum(1 for r in results if "error" not in r),
                "failed_queries": sum(1 for r in results if "error" in r),
                "results": results
            }
        ).to_json() + "\n"
    
    return StreamingResponse(
        batch_process(),
        media_type="application/x-ndjson",
        headers={
            "Transfer-Encoding": "chunked",
            "X-Content-Type-Options": "nosniff",
        }
    )


@router.post("/sessions")
async def create_rag_session(request: RAGSessionCreateRequest) -> RAGSessionResponse:
    """Create a new RAG conversation session."""
    engine = get_rag_engine()
    
    try:
        session_id = engine.create_session(request.session_id, request.metadata)
        session_info = engine.get_session_info(session_id)
        
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session"
            )
        
        return RAGSessionResponse(
            session_id=session_info["session_id"],
            metadata=session_info["metadata"],
            turn_count=session_info["turn_count"],
            created_at=session_info["created_at"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/sessions/{session_id}")
async def get_rag_session(session_id: str) -> RAGSessionResponse:
    """Get information about a RAG session."""
    engine = get_rag_engine()
    
    session_info = engine.get_session_info(session_id)
    
    if not session_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return RAGSessionResponse(
        session_id=session_info["session_id"],
        metadata=session_info["metadata"],
        turn_count=session_info["turn_count"],
        created_at=session_info["created_at"]
    )


@router.delete("/sessions/{session_id}")
async def delete_rag_session(session_id: str) -> Dict[str, Any]:
    """Delete a RAG session."""
    engine = get_rag_engine()
    
    success = engine.delete_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return {"status": "success", "message": f"Session {session_id} deleted"}


@router.get("/stats")
async def get_rag_stats() -> Dict[str, Any]:
    """Get RAG system statistics."""
    engine = get_rag_engine()
    
    conversation_stats = engine.get_conversation_stats()
    
    return {
        "conversation_stats": conversation_stats,
        "engine_info": {
            "type": "ConversationalRAGEngine",
            "conversation_enabled": engine.config.conversation_enabled,
            "multi_hop_enabled": engine.config.multi_hop_enabled,
            "memory_size": engine.config.conversation_memory_size
        }
    }


# Utility functions

def chunk_text(text: str, chunk_size: int = 50) -> List[str]:
    """Split text into chunks for streaming."""
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i+chunk_size])
    return chunks


# WebSocket endpoint for real-time collaboration
@router.websocket("/ws/{session_id}")
async def rag_websocket_endpoint(websocket, session_id: str):
    """WebSocket endpoint for real-time RAG collaboration."""
    await websocket.accept()
    engine = get_rag_engine()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "query":
                # Handle query through WebSocket
                query = message.get("query", "")
                
                if not query:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "error": "No query provided"
                    }))
                    continue
                
                # Execute query
                result = await engine.query(
                    query_text=query,
                    session_id=session_id,
                    use_conversation=True
                )
                
                # Send response
                await websocket.send_text(json.dumps({
                    "type": "result",
                    "query": query,
                    "answer": result.get("answer", ""),
                    "sources_count": len(result.get("sources", [])),
                    "session_id": session_id
                }))
                
            elif message.get("type") == "session_info":
                # Provide session information
                session_info = engine.get_session_info(session_id)
                await websocket.send_text(json.dumps({
                    "type": "session_info",
                    "session_id": session_id,
                    "info": session_info or {}
                }))
                
            elif message.get("type") == "close":
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": str(e)
        }))
    finally:
        await websocket.close()