"""AI Safety-specific tracing decorators and utilities."""

import hashlib
from collections.abc import Callable
from functools import wraps

from .action_trace import TraceOrigin
from .trace_manager import get_trace_manager


def hash_prompt(prompt: str, max_length: int = 1000) -> str:
    """Hash a prompt for security tracking without storing full content.

    Args:
        prompt: The prompt text to hash
        max_length: Maximum length to hash (truncate if longer)

    Returns:
        SHA256 hash of the prompt
    """
    if len(prompt) > max_length:
        prompt = prompt[:max_length]
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def trace_model_inference(model_name: str, prompt: str | None = None):
    """Decorator for model inference with safety tracking.

    Args:
        model_name: Name of the model being invoked
        prompt: Optional prompt text (will be hashed for security)

    Example:
        @trace_model_inference(model_name="gpt-4", prompt=user_prompt)
        def generate_response(prompt: str):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            trace_manager = get_trace_manager()
            prompt_hash = hash_prompt(prompt) if prompt else None

            with trace_manager.trace_action(
                action_type="model_inference",
                action_name=f"Generate with {model_name}",
                origin=TraceOrigin.MODEL_INFERENCE,
                metadata={
                    "model_used": model_name,
                    "prompt_hash": prompt_hash,
                },
            ) as trace:
                trace.model_used = model_name
                trace.prompt_hash = prompt_hash

                # Execute the function
                result = func(*args, **kwargs)

                # Update trace with result metadata if available
                if hasattr(result, "safety_score"):
                    trace.safety_score = result.safety_score
                if hasattr(result, "risk_level"):
                    trace.risk_level = result.risk_level

                return result

        return wrapper

    return decorator


def trace_safety_analysis(operation: str):
    """Decorator for safety analysis operations.

    Args:
        operation: Description of the safety analysis operation

    Example:
        @trace_safety_analysis(operation="Prompt security scan")
        def scan_prompt(prompt: str):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            trace_manager = get_trace_manager()

            with trace_manager.trace_action(
                action_type="safety_analysis",
                action_name=operation,
                origin=TraceOrigin.SAFETY_ANALYSIS,
                metadata={"operation": operation},
            ) as trace:
                result = func(*args, **kwargs)

                # Update trace with safety analysis results
                if isinstance(result, dict):
                    if "safety_score" in result:
                        trace.safety_score = result["safety_score"]
                    if "risk_level" in result:
                        trace.risk_level = result["risk_level"]
                    if "violations" in result:
                        trace.guardrail_violations.extend(result["violations"])
                    if "compliance_issues" in result:
                        trace.compliance_flags.extend(result["compliance_issues"])

                return result

        return wrapper

    return decorator


def trace_guardrail_check(rule_type: str, passed: bool = True):
    """Decorator for guardrail validation.

    Args:
        rule_type: Type of guardrail rule being checked
        passed: Whether the guardrail check passed

    Example:
        @trace_guardrail_check(rule_type="content_filter", passed=True)
        def check_content(content: str):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            trace_manager = get_trace_manager()

            with trace_manager.trace_action(
                action_type="guardrail_check",
                action_name=f"Guardrail: {rule_type}",
                origin=TraceOrigin.GUARDRAIL_VIOLATION if not passed else TraceOrigin.SAFETY_ANALYSIS,
                metadata={"rule_type": rule_type, "passed": passed},
            ) as trace:
                result = func(*args, **kwargs)

                # Record violation if check failed
                if not passed or (isinstance(result, bool) and not result):
                    trace.guardrail_violations.append(rule_type)
                    trace.risk_level = "high" if trace.risk_level != "high" else trace.risk_level

                return result

        return wrapper

    return decorator


def validate_response_safety(response: str, min_safety_score: float = 0.7) -> float:
    """Validate response safety and return a safety score.

    This is a placeholder implementation. In production, this would
    use actual safety validation models or rules.

    Args:
        response: The response text to validate
        min_safety_score: Minimum acceptable safety score

    Returns:
        Safety score between 0.0 and 1.0
    """
    # Placeholder: simple heuristic-based safety check
    # In production, this would use actual safety models

    safety_score = 1.0

    # Check for potentially unsafe content (simplified)
    unsafe_patterns = ["harmful", "dangerous", "illegal", "violence", "discrimination", "hate speech"]

    response_lower = response.lower()
    for pattern in unsafe_patterns:
        if pattern in response_lower:
            safety_score -= 0.2

    safety_score = max(0.0, min(1.0, safety_score))
    return safety_score
