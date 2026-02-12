"""
Custom exception classes for workspace utilities.
"""


class WorkspaceUtilsError(Exception):
    """Base exception for workspace utilities."""
    pass


class ConfigurationError(WorkspaceUtilsError):
    """Raised when configuration is invalid or missing."""
    pass


class ValidationError(WorkspaceUtilsError):
    """Raised when input validation fails."""
    pass


class AnalysisError(WorkspaceUtilsError):
    """Raised when repository analysis fails."""
    pass


class ComparisonError(WorkspaceUtilsError):
    """Raised when project comparison fails."""
    pass


class VerificationError(WorkspaceUtilsError):
    """Raised when EUFLE verification fails."""
    pass


class OutputError(WorkspaceUtilsError):
    """Raised when output generation fails."""
    pass