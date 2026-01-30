"""GRID custom exception hierarchy."""


class GridError(Exception):
    """Base exception for all GRID errors."""

    pass


class DataSaveError(GridError):
    """Error raised when data cannot be saved."""

    pass


class ConfigurationError(GridError):
    """Error raised for configuration issues."""

    pass


class ValidationError(GridError):
    """Error raised for validation failures."""

    pass


class ProcessingError(GridError):
    """Error raised during processing pipeline failures."""

    pass


class AgenticSystemError(GridError):
    """Base exception for agentic system errors."""

    pass


class SkillStoreError(AgenticSystemError):
    """Raised when skill store operations fail."""

    pass
