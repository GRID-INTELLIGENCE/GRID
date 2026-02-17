"""
Dynamic Gateway Module
=====================

Transforms static broadband dial-up architecture into dynamic, responsive system.
"""

from .dynamic_router import DynamicRouter, RequestPriority, SafetyScore, get_dynamic_router

__all__ = ["DynamicRouter", "get_dynamic_router", "SafetyScore", "RequestPriority"]
