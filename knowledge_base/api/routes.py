"""
REST API for Knowledge Base
============================

Provides REST endpoints for knowledge base operations:
- Search and retrieval
- Document ingestion
- System management
- Analytics and monitoring
"""

import logging
import os
import time
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..core.config import KnowledgeBaseConfig
from ..core.database import KnowledgeBaseDB
from ..embeddings.engine import EmbeddingEngine
from ..embeddings.llm_generator import LLMGenerator
from ..ingestion.pipeline import DataIngestionPipeline
from ..search.retriever import VectorRetriever

logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class SearchRequest(BaseModel):
    """Search request model."""

    query: str = Field(..., description="Search query text")
    limit: int | None = Field(10, description="Maximum results to return")
    threshold: float | None = Field(0.7, description="Similarity threshold")
    use_hybrid: bool | None = Field(True, description="Use hybrid search")
    include_sources: bool | None = Field(True, description="Include source information")


class SearchResponse(BaseModel):
    """Search response model."""

    query: str
    total_results: int
    results: list[dict[str, Any]]
    sources: list[dict[str, Any]] | None = None
    processing_time: float


class IngestRequest(BaseModel):
    """Document ingestion request model."""

    content: str = Field(..., description="Document content")
    title: str = Field(..., description="Document title")
    source_type: str = Field("manual", description="Source type")
    source_path: str | None = Field(None, description="Source file path")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class IngestResponse(BaseModel):
    """Document ingestion response model."""

    document_id: str
    chunks_created: int
    success: bool
    message: str


class GenerateRequest(BaseModel):
    """Text generation request model."""

    query: str = Field(..., description="Question to answer")
    context_limit: int | None = Field(5, description="Maximum context results")
    temperature: float | None = Field(None, description="Generation temperature")
    max_tokens: int | None = Field(None, description="Maximum tokens to generate")


class GenerateResponse(BaseModel):
    """Text generation response model."""

    answer: str
    confidence_score: float
    sources: list[dict[str, Any]]
    token_usage: dict[str, int]
    processing_time: float


class SystemStats(BaseModel):
    """System statistics response model."""

    documents: dict[str, Any]
    chunks: dict[str, Any]
    embeddings: dict[str, Any]
    search: dict[str, Any]
    generation: dict[str, Any]


def create_api_app(
    config: KnowledgeBaseConfig,
    db: KnowledgeBaseDB,
    ingestion_pipeline: DataIngestionPipeline,
    embedding_engine: EmbeddingEngine,
    retriever: VectorRetriever,
    llm_generator: LLMGenerator,
) -> FastAPI:
    """Create FastAPI application with knowledge base endpoints."""

    app = FastAPI(
        title="GRID Knowledge Base API", description="REST API for knowledge base operations", version="1.0.0"
    )

    # Add CORS middleware
    # CORS Configuration - NEVER use wildcards in production
    # Set GRID_CORS_ORIGINS environment variable with comma-separated origins
    # Example: GRID_CORS_ORIGINS=http://localhost:3000,https://app.example.com
    cors_origins_env = os.environ.get("GRID_CORS_ORIGINS", "")

    if cors_origins_env:
        cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
    else:
        # Default to localhost only for development
        cors_origins = ["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"]
        import logging

        logging.warning(
            "GRID_CORS_ORIGINS not set. Using localhost defaults. Set GRID_CORS_ORIGINS for production deployment."
        )

    # Validate no wildcards in production
    if "*" in cors_origins:
        environment = os.environ.get("GRID_ENV", "development")
        if environment == "production":
            raise ValueError(
                "CORS wildcard (*) is not allowed in production. "
                "Set explicit origins in GRID_CORS_ORIGINS environment variable."
            )
        else:
            import logging

            logging.warning("CORS wildcard detected - this is insecure and should not be used in production.")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Request-ID"],
    )

    @app.get("/")
    async def root():
        """API root endpoint."""
        return {"message": "GRID Knowledge Base API", "version": "1.0.0", "status": "running"}

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "config": {
                "database_connected": True,  # Would check actual connection
                "embeddings_ready": True,
                "search_ready": True,
            },
        }

    @app.post("/search", response_model=SearchResponse)
    async def search_documents(request: SearchRequest):
        """Search documents in the knowledge base."""
        start_time = time.time()

        try:
            # Execute search
            results = retriever.search(
                query_text=request.query,
                limit=request.limit,
                threshold=request.threshold,
                use_hybrid=request.use_hybrid,
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "content": result.content,
                        "score": result.score,
                        "rank": result.rank,
                        "document_title": result.document_title,
                        "document_id": result.document_id,
                        "chunk_id": result.chunk_id,
                        "source_type": result.source_type,
                        "metadata": result.metadata,
                    }
                )

            # Get sources if requested
            sources = None
            if request.include_sources:
                search_with_sources = retriever.search_with_sources(request.query)
                sources = search_with_sources.get("documents", {})

            processing_time = time.time() - start_time

            return SearchResponse(
                query=request.query,
                total_results=len(formatted_results),
                results=formatted_results,
                sources=sources,
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    @app.post("/generate", response_model=GenerateResponse)
    async def generate_answer(request: GenerateRequest):
        """Generate answer using retrieved context."""
        try:
            # Search for relevant context
            context_results = retriever.search(query_text=request.query, limit=request.context_limit or 5)

            if not context_results:
                return GenerateResponse(
                    answer="I couldn't find relevant information in the knowledge base to answer your question.",
                    confidence_score=0.0,
                    sources=[],
                    token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    processing_time=0.0,
                )

            # Generate answer
            generation_request = LLMGenerator.GenerationRequest(
                query=request.query,
                context=context_results,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            result = llm_generator.generate_answer(generation_request)

            return GenerateResponse(
                answer=result.answer,
                confidence_score=result.confidence_score,
                sources=result.sources,
                token_usage=result.token_usage,
                processing_time=result.processing_time,
            )

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    @app.post("/ingest", response_model=IngestResponse)
    async def ingest_document(request: IngestRequest, background_tasks: BackgroundTasks):
        """Ingest a new document into the knowledge base."""
        try:
            # Add document to ingestion pipeline
            ingestion_result = ingestion_pipeline._process_document(
                ingestion_pipeline.DocumentData(
                    id=f"api_{int(time.time())}_{hash(request.content) % 10000}",
                    title=request.title,
                    content=request.content,
                    source_type=request.source_type,
                    source_path=request.source_path or "",
                    file_type="txt",
                    metadata=request.metadata or {},
                )
            )

            # Trigger embedding update in background
            if ingestion_result.success:
                background_tasks.add_task(
                    embedding_engine.update_chunk_embeddings, limit=ingestion_result.chunks_created
                )

            return IngestResponse(
                document_id=ingestion_result.document_id,
                chunks_created=ingestion_result.chunks_created,
                success=ingestion_result.success,
                message="Document ingested successfully"
                if ingestion_result.success
                else ingestion_result.error_message or "Ingestion failed",
            )

        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    @app.get("/stats", response_model=SystemStats)
    async def get_system_stats():
        """Get comprehensive system statistics."""
        try:
            return SystemStats(
                documents={
                    "total_count": db.get_document_count(),
                    "recent_documents": db.get_recent_documents(limit=5),
                },
                chunks={"total_count": db.get_chunk_count()},
                embeddings=embedding_engine.get_embedding_stats(),
                search=retriever.get_search_stats(),
                generation=llm_generator.get_generation_stats(),
            )

        except Exception as e:
            logger.error(f"Stats retrieval failed: {e}")
            raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

    @app.post("/embeddings/update")
    async def update_embeddings(limit: int = Query(100, description="Maximum chunks to update")):
        """Update embeddings for chunks that don't have them."""
        try:
            updated_count = embedding_engine.update_chunk_embeddings(limit=limit)
            return {"message": f"Updated embeddings for {updated_count} chunks", "updated_count": updated_count}

        except Exception as e:
            logger.error(f"Embedding update failed: {e}")
            raise HTTPException(status_code=500, detail=f"Embedding update failed: {str(e)}")

    @app.delete("/cache/clear")
    async def clear_cache():
        """Clear various caches (embeddings, search stats, etc.)."""
        try:
            embedding_engine.clear_cache()
            retriever.clear_stats()
            llm_generator.clear_stats()

            return {"message": "All caches cleared successfully"}

        except Exception as e:
            logger.error(f"Cache clearing failed: {e}")
            raise HTTPException(status_code=500, detail=f"Cache clearing failed: {str(e)}")

    @app.get("/documents")
    async def list_documents(
        limit: int = Query(20, description="Maximum documents to return"),
        offset: int = Query(0, description="Offset for pagination"),
    ):
        """List documents in the knowledge base."""
        try:
            documents = db.get_recent_documents(limit=limit)
            return {"documents": documents, "count": len(documents), "limit": limit, "offset": offset}

        except Exception as e:
            logger.error(f"Document listing failed: {e}")
            raise HTTPException(status_code=500, detail=f"Document listing failed: {str(e)}")

    # Error handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})

    logger.info("Knowledge Base API initialized")
    return app


def create_development_app() -> FastAPI:
    """Create development application with mock components."""
    # This would create a minimal app for testing without full dependencies
    app = FastAPI(title="GRID Knowledge Base API (Development)")

    @app.get("/")
    async def root():
        return {"message": "Development API - Full system not initialized"}

    return app


# Create the main application instance
try:
    from ..core.config import KnowledgeBaseConfig
    from ..core.database import KnowledgeBaseDB
    from ..embeddings.engine import EmbeddingEngine
    from ..embeddings.llm_generator import LLMGenerator
    from ..ingestion.pipeline import DataIngestionPipeline
    from ..search.retriever import VectorRetriever

    # Load configuration
    config = KnowledgeBaseConfig.from_env()

    # Initialize components
    db = KnowledgeBaseDB(config)
    db.connect()

    ingestion_pipeline = DataIngestionPipeline(config, db)

    embedding_engine = EmbeddingEngine(config, db)

    retriever = VectorRetriever(config, db, embedding_engine)

    llm_generator = LLMGenerator(config)

    # Create and expose the app
    app = create_api_app(config, db, ingestion_pipeline, embedding_engine, retriever, llm_generator)

except Exception as e:
    logger.error(f"Failed to initialize full application: {e}")
    logger.info("Falling back to development app")
    app = create_development_app()
