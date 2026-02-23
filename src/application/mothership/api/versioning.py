"""
API Versioning and Deprecation Strategy.

Provides centralized management of API versions, deprecation status,
and headers for unified versioning across all services.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from fastapi import Response


class ApiVersion(StrEnum):
    """Supported API versions."""

    V1 = "v1"
    V2 = "v2"
    EXPERIMENTAL = "experimental"


class VersionStatus(StrEnum):
    """Status of an API version."""

    STABLE = "stable"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"
    EXPERIMENTAL = "experimental"


class VersionMetadata:
    """Metadata for an API version."""

    def __init__(
        self,
        version: ApiVersion,
        status: VersionStatus = VersionStatus.STABLE,
        deprecated_at: datetime | None = None,
        sunset_at: datetime | None = None,
        migration_guide_url: str | None = None,
    ) -> None:
        self.version = version
        self.status = status
        self.deprecated_at = deprecated_at
        self.sunset_at = sunset_at
        self.migration_guide_url = migration_guide_url

    def inject_headers(self, response: Response) -> None:
        """Inject versioning and deprecation headers into response."""
        response.headers["X-API-Version"] = self.version.value
        response.headers["X-API-Status"] = self.status.value

        if self.deprecated_at:
            response.headers["Deprecation"] = f"@{int(self.deprecated_at.timestamp())}"
            if self.migration_guide_url:
                response.headers["Link"] = f'<{self.migration_guide_url}>; rel="deprecation-guide"'

        if self.sunset_at:
            response.headers["Sunset"] = self.sunset_at.strftime("%a, %d %b %Y %H:%M:%S GMT")


# Unified registry of version metadata
VERSION_REGISTRY: dict[ApiVersion, VersionMetadata] = {
    ApiVersion.V1: VersionMetadata(
        version=ApiVersion.V1,
        status=VersionStatus.STABLE,
    ),
    ApiVersion.V2: VersionMetadata(
        version=ApiVersion.V2,
        status=VersionStatus.EXPERIMENTAL,
        migration_guide_url="https://docs.grid.example.com/api/v2-migration",
    ),
}


def get_version_metadata(version: str | ApiVersion) -> VersionMetadata | None:
    """Get metadata for a specific API version."""
    if isinstance(version, str):
        try:
            version = ApiVersion(version.lower())
        except ValueError:
            return None
    return VERSION_REGISTRY.get(version)
