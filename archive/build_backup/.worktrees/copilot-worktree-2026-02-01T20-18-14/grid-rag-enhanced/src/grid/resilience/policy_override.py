"""Policy override mechanism for runtime configuration.

Allows retry policies to be overridden via environment variables and config files,
enabling runtime tuning without code changes.
"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from grid.resilience.policies import OperationPolicy, register_policy

logger = logging.getLogger(__name__)

__all__ = ["load_policy_overrides", "apply_env_policy_overrides"]


def load_policy_overrides(config_path: str | Path = "config/retry_policies.yaml") -> int:
    """Load retry policy overrides from YAML configuration file.

    Configuration file format:
    ```yaml
    network:
      max_attempts: 5
      backoff_factor: 1.5
      initial_delay: 2.0
      timeout_seconds: 180

    llm:
      max_attempts: 3
      backoff_factor: 3.0
      initial_delay: 5.0
    ```

    Args:
        config_path: Path to retry policy YAML configuration file.

    Returns:
        Number of policies loaded/updated.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config file has invalid format.
    """
    config_path = Path(config_path)

    if not config_path.exists():
        logger.warning(f"Policy override config not found: {config_path}")
        return 0

    try:
        with open(config_path) as f:
            overrides = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {config_path}: {e}") from e
    except OSError as e:
        raise FileNotFoundError(f"Cannot read {config_path}: {e}") from e

    if not isinstance(overrides, dict):
        raise ValueError(f"Expected dict at root of {config_path}, got {type(overrides)}")

    count = 0
    for operation_type, overrides_dict in overrides.items():
        if not isinstance(overrides_dict, dict):
            logger.warning(f"Skipping {operation_type}: expected dict, got {type(overrides_dict)}")
            continue

        try:
            # Get the existing policy or create a new one
            from grid.resilience.policies import get_policy_for_operation

            try:
                base_policy = get_policy_for_operation(operation_type)
                # Create new policy with overrides
                kwargs = {
                    "operation_type": base_policy.operation_type,
                    "max_attempts": overrides_dict.get("max_attempts", base_policy.max_attempts),
                    "backoff_factor": overrides_dict.get("backoff_factor", base_policy.backoff_factor),
                    "initial_delay": overrides_dict.get("initial_delay", base_policy.initial_delay),
                    "max_delay": overrides_dict.get("max_delay", base_policy.max_delay),
                    "timeout_seconds": overrides_dict.get(
                        "timeout_seconds", base_policy.timeout_seconds
                    ),
                    "retryable_exceptions": base_policy.retryable_exceptions,
                    "non_retryable_exceptions": base_policy.non_retryable_exceptions,
                }
            except ValueError:
                # New operation type not in registry
                kwargs = {
                    "operation_type": operation_type,
                    "max_attempts": overrides_dict.get("max_attempts", 3),
                    "backoff_factor": overrides_dict.get("backoff_factor", 2.0),
                    "initial_delay": overrides_dict.get("initial_delay", 1.0),
                    "max_delay": overrides_dict.get("max_delay", 300.0),
                    "timeout_seconds": overrides_dict.get("timeout_seconds", None),
                }

            new_policy = OperationPolicy(**kwargs)
            register_policy(new_policy)
            logger.info(
                f"Loaded policy override for {operation_type}: "
                f"{new_policy.max_attempts} attempts, "
                f"{new_policy.backoff_factor}x backoff"
            )
            count += 1
        except Exception as e:
            logger.error(f"Failed to load policy override for {operation_type}: {e}")

    return count


def apply_env_policy_overrides() -> int:
    """Apply retry policy overrides from environment variables.

    Expects environment variables in the format:
    - GRID_POLICY_{OPERATION_TYPE}_MAX_ATTEMPTS=5
    - GRID_POLICY_{OPERATION_TYPE}_BACKOFF_FACTOR=1.5
    - GRID_POLICY_{OPERATION_TYPE}_INITIAL_DELAY=2.0
    - GRID_POLICY_{OPERATION_TYPE}_MAX_DELAY=60.0
    - GRID_POLICY_{OPERATION_TYPE}_TIMEOUT_SECONDS=180

    Example:
    ```
    GRID_POLICY_NETWORK_MAX_ATTEMPTS=5
    GRID_POLICY_NETWORK_BACKOFF_FACTOR=1.5
    GRID_POLICY_LLM_TIMEOUT_SECONDS=300
    ```

    Returns:
        Number of policies loaded/updated.
    """
    from grid.resilience.policies import get_policy_for_operation

    overrides_by_operation: dict[str, dict[str, Any]] = {}

    # Collect all GRID_POLICY_* environment variables
    for env_var, value in os.environ.items():
        if not env_var.startswith("GRID_POLICY_"):
            continue

        # Parse format: GRID_POLICY_{OPERATION_TYPE}_{PARAM}
        parts = env_var[len("GRID_POLICY_") :].split("_")
        if len(parts) < 2:
            logger.warning(f"Invalid policy env var format: {env_var}")
            continue

        # Extract operation type (all but last part) and parameter (last part)
        param = parts[-1].lower()
        operation_type = "_".join(parts[:-1]).lower()

        if operation_type not in overrides_by_operation:
            overrides_by_operation[operation_type] = {}

        # Parse value to appropriate type
        try:
            if param in ("max_attempts",):
                overrides_by_operation[operation_type][param] = int(value)
            elif param in ("backoff_factor", "initial_delay", "max_delay", "timeout_seconds"):
                overrides_by_operation[operation_type][param] = float(value)
            else:
                logger.warning(f"Unknown policy parameter: {param}")
        except ValueError:
            logger.error(f"Cannot parse {env_var}={value} as number")

    # Apply overrides
    count = 0
    for operation_type, overrides_dict in overrides_by_operation.items():
        try:
            try:
                base_policy = get_policy_for_operation(operation_type)
                kwargs = {
                    "operation_type": base_policy.operation_type,
                    "max_attempts": overrides_dict.get("max_attempts", base_policy.max_attempts),
                    "backoff_factor": overrides_dict.get("backoff_factor", base_policy.backoff_factor),
                    "initial_delay": overrides_dict.get("initial_delay", base_policy.initial_delay),
                    "max_delay": overrides_dict.get("max_delay", base_policy.max_delay),
                    "timeout_seconds": overrides_dict.get(
                        "timeout_seconds", base_policy.timeout_seconds
                    ),
                    "retryable_exceptions": base_policy.retryable_exceptions,
                    "non_retryable_exceptions": base_policy.non_retryable_exceptions,
                }
            except ValueError:
                kwargs = {
                    "operation_type": operation_type,
                    "max_attempts": overrides_dict.get("max_attempts", 3),
                    "backoff_factor": overrides_dict.get("backoff_factor", 2.0),
                    "initial_delay": overrides_dict.get("initial_delay", 1.0),
                    "max_delay": overrides_dict.get("max_delay", 300.0),
                    "timeout_seconds": overrides_dict.get("timeout_seconds", None),
                }

            new_policy = OperationPolicy(**kwargs)
            register_policy(new_policy)
            logger.info(
                f"Applied env policy override for {operation_type}: "
                f"max_attempts={new_policy.max_attempts}, "
                f"backoff_factor={new_policy.backoff_factor}"
            )
            count += 1
        except Exception as e:
            logger.error(f"Failed to apply env override for {operation_type}: {e}")

    return count
