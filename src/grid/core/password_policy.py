from typing import Any

from zxcvbn import zxcvbn

from .config import settings


def validate_password_strength(password: str, user_inputs: list[str] = None) -> dict[str, Any]:
    """
    Validate password strength using zxcvbn.

    Args:
        password: The password to check
        user_inputs: Optional list of strings related to the user (username, email, etc.)

    Returns:
        Dict containing score, warning, and suggestions.
    """
    if user_inputs is None:
        user_inputs = []

    result = zxcvbn(password, user_inputs=user_inputs)
    score = result["score"]
    feedback = result["feedback"]

    is_strong = score >= settings.PASSWORD_COMPLEXITY_SCORE
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        is_strong = False
        feedback["warning"] = f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long."

    return {
        "score": score,
        "is_strong": is_strong,
        "warning": feedback["warning"],
        "suggestions": feedback["suggestions"],
    }
