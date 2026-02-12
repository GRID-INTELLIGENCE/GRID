"""Coinbase - Crypto-focused project with GRID agentic system."""

__version__ = "0.1.0"

# Define __all__ first
__all__ = []

# Core components
# Runtime behavior module
from . import runtimebehavior
from .agent_executor import AgentExecutor, ExecutionResult
from .agentic_system import AgenticSystem, SystemConfig
from .cognitive_engine import (
    CognitiveEngine,
    CognitiveLoad,
    CognitiveState,
    InteractionEvent,
)

# Databricks integration
from .databricks_config import (
    DatabricksClient,
    DatabricksConfig,
)
from .error_recovery import (
    ErrorCategory,
    ErrorClassifier,
    RecoveryEngine,
)
from .events import (
    CaseCompletedEvent,
    CaseExecutedEvent,
    EventBus,
)
from .learning_coordinator import LearningCoordinator, SkillStats
from .skill_generator import SkillGenerator, SkillMetadata

# Crypto skills
from .skills import (
    CryptoSkill,
    CryptoSkillsRegistry,
    SkillType,
    crypto_skills_registry,
)
from .tracer import (
    DecisionType,
    ExecutionBehavior,
    ExecutionOutcome,
    RuntimeBehaviorTracer,
)
from .version_scoring import VersionMetrics, VersionScorer

# Crypto investment platform (new)
try:
    from .app import CoinbaseApp, CoinbaseConfig, create_app

    __all__.extend(["CoinbaseApp", "CoinbaseConfig", "create_app"])
except ImportError:
    pass

# Now extend with all other exports
__all__.extend(
    [
        # Tracer
        "RuntimeBehaviorTracer",
        "ExecutionBehavior",
        "ExecutionOutcome",
        "DecisionType",
        # Events
        "EventBus",
        "CaseCompletedEvent",
        "CaseExecutedEvent",
        # Error recovery
        "RecoveryEngine",
        "ErrorClassifier",
        "ErrorCategory",
        # Skill generation
        "SkillGenerator",
        "SkillMetadata",
        # Learning
        "LearningCoordinator",
        "SkillStats",
        # Agent executor
        "AgentExecutor",
        "ExecutionResult",
        # Agentic system
        "AgenticSystem",
        "SystemConfig",
        # Version scoring
        "VersionScorer",
        "VersionMetrics",
        # Cognitive engine
        "CognitiveEngine",
        "CognitiveState",
        "CognitiveLoad",
        "InteractionEvent",
        # Crypto skills
        "CryptoSkillsRegistry",
        "CryptoSkill",
        "SkillType",
        "crypto_skills_registry",
        # Runtime behavior
        "runtimebehavior",
        # Databricks
        "DatabricksConfig",
        "DatabricksClient",
    ]
)
