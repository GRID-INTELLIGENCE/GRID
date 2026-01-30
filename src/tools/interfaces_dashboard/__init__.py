"""Interfaces dashboard package for local prototype."""

from .collector import DashboardCollector
from .dashboard import run_dashboard

__all__ = ["DashboardCollector", "run_dashboard"]
