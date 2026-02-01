"""
Cascade Hooks for The Chase
"""

from collections.abc import Callable


class OverwatchHooks:
    """Cascade Hooks for OVERWATCH"""

    def __init__(self):
        self.hooks = {"pre_user_prompt": [], "post_cascade_response": []}

    def register_hook(self, event: str, callback: Callable):
        """Register hook for event"""
        if event in self.hooks:
            self.hooks[event].append(callback)

    def trigger_hook(self, event: str, *args, **kwargs):
        """Trigger all hooks for a given event"""
        if event in self.hooks:
            for callback in self.hooks[event]:
                callback(*args, **kwargs)
