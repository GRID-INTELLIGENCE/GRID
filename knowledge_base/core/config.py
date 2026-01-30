"""
Knowledge Base Configuration
============================

Centralized configuration management for the GRID Knowledge Base system.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration for vector storage."""
    host: str = "dbc-9747ff30-23c5.cloud.databricks.com"
    http_path: str = "/sql/1.0/warehouses/b23086e70499319a"
    token: Optional[str] = None
    connection_timeout: int = 30
    pool_size: int = 5
    max_overflow: int = 10


@dataclass
class EmbeddingConfig:
    """Vector embedding configuration."""
    model: str = "text-embedding-3-large"
    provider: str = "openai"
    dimensions: int = 3072
    api_key: Optional[str] = None
    batch_size: int = 100
    max_tokens: int = 8191


@dataclass
class SearchConfig:
    """Search and retrieval configuration."""
    top_k: int = 10
    similarity_threshold: float = 0.7
    use_hybrid_search: bool = True
    rerank_results: bool = True
    max_context_length: int = 4000


@dataclass
class LLMConfig:
    """LLM configuration for generation."""
    model: str = "gpt-4-turbo-preview"
    provider: str = "openai"
    api_key: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 1000
    streaming: bool = True


@dataclass
class SecurityConfig:
    """Security and access control configuration."""
    enable_auth: bool = True
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # per minute


@dataclass
class MonitoringConfig:
    """Monitoring and analytics configuration."""
    enable_metrics: bool = True
    enable_logging: bool = True
    log_level: str = "INFO"
    metrics_port: int = 9090
    enable_tracing: bool = True


@dataclass
class KnowledgeBaseConfig:
    """Main configuration class for the Knowledge Base system."""

    # Core settings
    name: str = "GRID Knowledge Base"
    version: str = "1.0.0"
    debug: bool = False

    # Component configs
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    embeddings: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    # Paths
    data_dir: Path = field(default_factory=lambda: Path("data"))
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_ATLAS_API", ""))
    cache_dir: Path = field(default_factory=lambda: Path("cache"))
    logs_dir: Path = field(default_factory=lambda: Path("logs"))

    @classmethod
    def from_env(cls) -> 'KnowledgeBaseConfig':
        """Create configuration from environment variables."""
        config = cls()

        # Database
        config.database.host = os.getenv("DATABRICKS_HOST", config.database.host)
        config.database.http_path = os.getenv("DATABRICKS_HTTP_PATH", config.database.http_path)
        config.database.token = os.getenv("DATABRICKS_TOKEN")

        # Embeddings
        config.embeddings.api_key = os.getenv("OPENAI_ATLAS_API")

        # LLM
        config.llm.api_key = os.getenv("OPENAI_ATLAS_API")

        # Security
        config.security.jwt_secret = os.getenv("JWT_SECRET")

        # Monitoring
        config.monitoring.log_level = os.getenv("LOG_LEVEL", config.monitoring.log_level)

        return config

    def validate(self) -> None:
        """Validate configuration completeness."""
        errors = []

        if not self.database.token:
            errors.append("DATABRICKS_TOKEN is required")

        if not self.embeddings.api_key:
            errors.append("OPENAI_ATLAS_API is required for embeddings")

        if not self.llm.api_key:
            errors.append("OPENAI_ATLAS_API is required for LLM")

        if self.security.enable_auth and not self.security.jwt_secret:
            errors.append("JWT_SECRET is required when auth is enabled")

        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "debug": self.debug,
            "database": {
                "host": self.database.host,
                "http_path": self.database.http_path,
                "connection_timeout": self.database.connection_timeout,
                "pool_size": self.database.pool_size,
                "max_overflow": self.database.max_overflow
            },
            "embeddings": {
                "model": self.embeddings.model,
                "provider": self.embeddings.provider,
                "dimensions": self.embeddings.dimensions,
                "batch_size": self.embeddings.batch_size,
                "max_tokens": self.embeddings.max_tokens
            },
            "search": {
                "top_k": self.search.top_k,
                "similarity_threshold": self.search.similarity_threshold,
                "use_hybrid_search": self.search.use_hybrid_search,
                "rerank_results": self.search.rerank_results,
                "max_context_length": self.search.max_context_length
            },
            "llm": {
                "model": self.llm.model,
                "provider": self.llm.provider,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "streaming": self.llm.streaming
            },
            "security": {
                "enable_auth": self.security.enable_auth,
                "jwt_algorithm": self.security.jwt_algorithm,
                "jwt_expiration": self.security.jwt_expiration,
                "rate_limit_requests": self.security.rate_limit_requests,
                "rate_limit_window": self.security.rate_limit_window
            },
            "monitoring": {
                "enable_metrics": self.monitoring.enable_metrics,
                "enable_logging": self.monitoring.enable_logging,
                "log_level": self.monitoring.log_level,
                "metrics_port": self.monitoring.metrics_port,
                "enable_tracing": self.monitoring.enable_tracing
            }
        }
