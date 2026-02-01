"""Centralized retry policies for GRID operations.

Defines retry configuration policies per operation type, ensuring consistent
error recovery behavior across the system.

Policies are organized by domain (file I/O, network, database, LLM operations)
and provide sensible defaults while remaining overridable.
"""

from dataclasses import dataclass

__all__ = [
    "OperationPolicy",
    "FileIOPolicy",
    "NetworkPolicy",
    "DatabasePolicy",
    "LLMPolicy",
    "RAGPolicy",
    "SkillPolicy",
    "CommandPolicy",
    "get_policy_for_operation",
    "register_policy",
]


@dataclass
class OperationPolicy:
    """Base configuration for retry behavior on a specific operation type."""

    operation_type: str
    """Unique identifier for this operation type (e.g., 'file_write', 'api_call')."""

    max_attempts: int = 3
    """Maximum number of retry attempts."""

    backoff_factor: float = 2.0
    """Exponential backoff multiplier (delay = initial_delay * (backoff_factor ^ attempt))."""

    initial_delay: float = 1.0
    """Initial delay in seconds before first retry."""

    max_delay: float = 300.0
    """Maximum delay cap in seconds (prevents unbounded growth)."""

    timeout_seconds: float | None = None
    """Overall timeout for the entire operation (all attempts combined)."""

    retryable_exceptions: tuple[type[Exception], ...] = (Exception,)
    """Tuple of exception types that trigger retry. Default: all exceptions."""

    non_retryable_exceptions: tuple[type[Exception], ...] = ()
    """Tuple of exception types that should NOT be retried."""

    def should_retry_on(self, exc: Exception) -> bool:
        """Determine if the given exception should trigger a retry.

        Args:
            exc: The exception that occurred.

        Returns:
            True if the exception matches retry criteria, False otherwise.
        """
        # Never retry non-retryable exceptions
        if isinstance(exc, self.non_retryable_exceptions):
            return False

        # Retry if exception matches retryable types
        return isinstance(exc, self.retryable_exceptions)


# File I/O Operations
FileIOPolicy = OperationPolicy(
    operation_type="file_io",
    max_attempts=3,
    backoff_factor=2.0,
    initial_delay=0.1,
    max_delay=10.0,
    timeout_seconds=30.0,
    retryable_exceptions=(
        IOError,
        OSError,
        TimeoutError,
    ),
    non_retryable_exceptions=(
        PermissionError,
        FileNotFoundError,
        IsADirectoryError,
    ),
)
"""Retry policy for file I/O operations (read/write/delete).

- 3 attempts, fast backoff (0.1s → 0.2s → 0.4s)
- Retries on transient I/O errors
- Does not retry permission or file not found errors
"""

# Network Operations
NetworkPolicy = OperationPolicy(
    operation_type="network",
    max_attempts=4,
    backoff_factor=2.0,
    initial_delay=1.0,
    max_delay=60.0,
    timeout_seconds=120.0,
    retryable_exceptions=(
        ConnectionError,
        TimeoutError,
        OSError,
    ),
    non_retryable_exceptions=(
        ValueError,
        TypeError,
    ),
)
"""Retry policy for network operations (HTTP calls, socket connections).

- 4 attempts, moderate backoff (1s → 2s → 4s → 8s)
- Retries on connection and timeout errors
- Respects HTTP 429 (rate limit) via Retry-After header
"""

# Database Operations
DatabasePolicy = OperationPolicy(
    operation_type="database",
    max_attempts=3,
    backoff_factor=2.0,
    initial_delay=0.5,
    max_delay=30.0,
    timeout_seconds=60.0,
    retryable_exceptions=(
        TimeoutError,
        ConnectionError,
        OSError,
    ),
    non_retryable_exceptions=(
        ValueError,
        KeyError,
    ),
)
"""Retry policy for database operations (queries, transactions).

- 3 attempts, moderate backoff (0.5s → 1s → 2s)
- Retries on connection and timeout errors
- Does not retry data validation errors
"""

# LLM Model Operations
LLMPolicy = OperationPolicy(
    operation_type="llm",
    max_attempts=3,
    backoff_factor=2.0,
    initial_delay=2.0,
    max_delay=60.0,
    timeout_seconds=180.0,
    retryable_exceptions=(
        TimeoutError,
        ConnectionError,
        OSError,
    ),
    non_retryable_exceptions=(
        ValueError,
        TypeError,
        RuntimeError,
    ),
)
"""Retry policy for LLM model operations (inference, embeddings).

- 3 attempts, conservative backoff (2s → 4s → 8s)
- Retries on transient connection issues
- Does not retry model errors or invalid input
- Respects 180s timeout for long-running operations
"""

# RAG (Retrieval-Augmented Generation) Operations
RAGPolicy = OperationPolicy(
    operation_type="rag",
    max_attempts=3,
    backoff_factor=2.0,
    initial_delay=1.0,
    max_delay=30.0,
    timeout_seconds=120.0,
    retryable_exceptions=(
        TimeoutError,
        ConnectionError,
        OSError,
    ),
    non_retryable_exceptions=(
        ValueError,
        KeyError,
    ),
)
"""Retry policy for RAG operations (vectorization, retrieval, ranking).

- 3 attempts, moderate backoff (1s → 2s → 4s)
- Retries on transient vector store or embedding service issues
- Does not retry data or format errors
"""

# Skill Execution Operations
SkillPolicy = OperationPolicy(
    operation_type="skill",
    max_attempts=2,
    backoff_factor=2.0,
    initial_delay=1.0,
    max_delay=20.0,
    timeout_seconds=60.0,
    retryable_exceptions=(
        TimeoutError,
        ConnectionError,
    ),
    non_retryable_exceptions=(
        ValueError,
        TypeError,
        RuntimeError,
    ),
)
"""Retry policy for skill execution (domain transformations, utilities).

- 2 attempts, fast escalation (1s → 2s)
- Retries only on transient network issues
- Fails fast on input or execution errors
"""

# Command/CLI Operations
CommandPolicy = OperationPolicy(
    operation_type="command",
    max_attempts=1,
    backoff_factor=1.0,
    initial_delay=0.0,
    max_delay=0.0,
    timeout_seconds=300.0,
    retryable_exceptions=(),
    non_retryable_exceptions=(Exception,),
)
"""Retry policy for command/CLI operations.

- 1 attempt only (no retries)
- User-facing commands should fail fast rather than silently retry
- Commands can implement their own retry logic internally
"""

# Policy registry for lookup by operation type
_POLICY_REGISTRY: dict[str, OperationPolicy] = {
    "file_io": FileIOPolicy,
    "network": NetworkPolicy,
    "database": DatabasePolicy,
    "llm": LLMPolicy,
    "rag": RAGPolicy,
    "skill": SkillPolicy,
    "command": CommandPolicy,
}


def get_policy_for_operation(operation_type: str) -> OperationPolicy:
    """Retrieve the retry policy for the specified operation type.

    Args:
        operation_type: The operation type identifier (e.g., 'network', 'database').

    Returns:
        The OperationPolicy for the given type.

    Raises:
        ValueError: If the operation type is not registered.
    """
    if operation_type not in _POLICY_REGISTRY:
        available = ", ".join(sorted(_POLICY_REGISTRY.keys()))
        raise ValueError(f"Unknown operation type: {operation_type}. " f"Available types: {available}")
    return _POLICY_REGISTRY[operation_type]


def register_policy(policy: OperationPolicy) -> None:
    """Register a new or override an existing retry policy.

    Args:
        policy: The OperationPolicy to register.
    """
    _POLICY_REGISTRY[policy.operation_type] = policy
