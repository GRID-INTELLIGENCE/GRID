"""
Cascade Hooks for The Chase
"""

from collections.abc import Callable
from typing import Any


class OverwatchHooks:
    """Cascade Hooks for OVERWATCH"""

    def __init__(self) -> None:
        self.hooks: dict[str, list[Callable[..., Any]]] = {"pre_user_prompt": [], "post_cascade_response": []}

    def register_hook(self, event: str, callback: Callable[..., Any]) -> None:
        """Register hook for event"""
        if event in self.hooks:
            self.hooks[event].append(callback)

    def trigger_hook(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Trigger all hooks for a given event"""
        if event in self.hooks:
            for callback in self.hooks[event]:
                callback(*args, **kwargs)
