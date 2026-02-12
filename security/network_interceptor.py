"""
Network Access Control Interceptor
===================================
Centralized network access control layer that intercepts ALL network requests
and enforces security policies defined in network_access_control.yaml

This module monkey-patches common network libraries to enforce access control.
"""

import functools
import json
import logging
import os
import re
import socket
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Tuple
from urllib.parse import urlparse

import yaml

# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class NetworkAccessDenied(Exception):
    """Raised when network access is denied by security policy."""

    pass


class DataLeakDetected(Exception):
    """Raised when potential data leak is detected."""

    pass


class NetworkAccessControl:
    """Centralized network access control enforcement."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.config_path = Path(__file__).parent / "network_access_control.yaml"
        self.config = self._load_config()
        self.blocked_requests: list[dict] = []
        self.allowed_requests: list[dict] = []
        self.metrics = {
            "total_requests": 0,
            "blocked_requests": 0,
            "allowed_requests": 0,
            "data_leaks_detected": 0,
            "started_at": datetime.utcnow().isoformat(),
        }

        # Create logs directory
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)

        # Setup file handlers
        self._setup_file_logging()

        self._initialized = True
        logger.info("Network Access Control initialized - ALL ACCESS DENIED BY DEFAULT")

    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        try:
            if not self.config_path.exists():
                logger.error(f"Config file not found: {self.config_path}")
                return self._get_default_config()

            with open(self.config_path) as f:
                config = yaml.safe_load(f)

            logger.info(f"Loaded config from {self.config_path}")
            logger.info(f"Mode: {config.get('mode', 'strict')}, Default Policy: {config.get('default_policy', 'deny')}")

            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """Get default deny-all configuration."""
        return {
            "mode": "strict",
            "default_policy": "deny",
            "global": {
                "network_enabled": False,
                "logging": {
                    "enabled": True,
                    "log_level": "DEBUG",
                    "log_blocked_requests": True,
                    "log_allowed_requests": True,
                },
            },
        }

    def _setup_file_logging(self):
        """Setup file logging handlers."""
        log_dir = Path(__file__).parent / "logs"

        # Network access log
        network_log = log_dir / "network_access.log"
        fh = logging.FileHandler(network_log)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Audit log
        self.audit_log = log_dir / "audit.log"

    def _log_audit(self, event_type: str, details: dict):
        """Log audit event to file."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
        }

        try:
            with open(self.audit_log, "a") as f:
                f.write(json.dumps(audit_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def _check_data_leak(self, url: str, data: Any = None, headers: dict | None = None) -> bool:
        """Check for potential data leaks in request."""
        dlp_config = self.config.get("data_leak_prevention", {})

        if not dlp_config.get("enabled", True):
            return False

        sensitive_patterns = dlp_config.get("sensitive_patterns", [])

        # Check URL
        for pattern_config in sensitive_patterns:
            pattern = pattern_config.get("pattern", "")
            if re.search(pattern, url, re.IGNORECASE):
                logger.critical(f"DATA LEAK DETECTED in URL: Pattern '{pattern}' found")
                self.metrics["data_leaks_detected"] += 1
                return True

        # Check headers
        if headers:
            headers_str = json.dumps(headers)
            for pattern_config in sensitive_patterns:
                pattern = pattern_config.get("pattern", "")
                if re.search(pattern, headers_str, re.IGNORECASE):
                    logger.critical(f"DATA LEAK DETECTED in headers: Pattern '{pattern}' found")
                    self.metrics["data_leaks_detected"] += 1
                    return True

        # Check data/body
        if data:
            data_str = str(data)
            for pattern_config in sensitive_patterns:
                pattern = pattern_config.get("pattern", "")
                if re.search(pattern, data_str, re.IGNORECASE):
                    logger.critical(f"DATA LEAK DETECTED in body: Pattern '{pattern}' found")
                    self.metrics["data_leaks_detected"] += 1
                    return True

        return False

    def check_request(
        self,
        url: str,
        method: str = "GET",
        data: Any = None,
        headers: dict[str, Any] | None = None,
        caller: str = "unknown",
    ) -> tuple[bool, str]:
        """
        Check if a network request should be allowed.

        Returns:
            Tuple[bool, str]: (is_allowed, reason)
        """
        self.metrics["total_requests"] += 1

        parsed = urlparse(url)
        domain = parsed.netloc
        scheme = parsed.scheme

        request_info = {
            "url": url,
            "method": method,
            "domain": domain,
            "scheme": scheme,
            "caller": caller,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Check emergency kill switch
        emergency = self.config.get("emergency", {})
        if emergency.get("kill_switch", False):
            reason = "EMERGENCY KILL SWITCH ACTIVE - ALL NETWORK ACCESS DISABLED"
            logger.critical(f"🚨 {reason}")
            self._log_blocked_request(request_info, reason)
            return False, reason

        # Check if network is globally enabled
        global_config = self.config.get("global", {})
        if not global_config.get("network_enabled", False):
            reason = "Global network access is DISABLED"
            logger.warning(f"🚫 BLOCKED: {method} {url} - {reason}")
            self._log_blocked_request(request_info, reason)
            return False, reason

        # Check localhost-only mode
        if emergency.get("localhost_only", True):
            if domain not in ["localhost", "127.0.0.1", "::1", ""]:
                reason = "Only localhost access allowed (emergency mode)"
                logger.warning(f"🚫 BLOCKED: {method} {url} - {reason}")
                self._log_blocked_request(request_info, reason)
                return False, reason

        # Check for data leaks
        if self._check_data_leak(url, data, headers):
            reason = "Potential DATA LEAK detected"
            logger.critical(f"🚨 BLOCKED: {method} {url} - {reason}")
            self._log_blocked_request(request_info, reason)
            self._log_audit("DATA_LEAK_BLOCKED", request_info)
            return False, reason

        # Check whitelist
        if self._check_whitelist(url):
            reason = "URL in whitelist"
            logger.info(f"✅ ALLOWED: {method} {url} - {reason}")
            self._log_allowed_request(request_info, reason)
            return True, reason

        # Check blacklist
        if self._check_blacklist(url):
            reason = "URL in blacklist"
            logger.warning(f"🚫 BLOCKED: {method} {url} - {reason}")
            self._log_blocked_request(request_info, reason)
            return False, reason

        # Default policy
        default_policy = self.config.get("default_policy", "deny")
        if default_policy == "deny":
            reason = "Default policy is DENY - not in whitelist"
            logger.warning(f"🚫 BLOCKED: {method} {url} - {reason}")
            self._log_blocked_request(request_info, reason)
            return False, reason
        else:
            reason = "Default policy is ALLOW"
            logger.info(f"✅ ALLOWED: {method} {url} - {reason}")
            self._log_allowed_request(request_info, reason)
            return True, reason

    def _check_whitelist(self, url: str) -> bool:
        """Check if URL is in whitelist."""
        whitelist = self.config.get("whitelist", {}).get("rules", [])
        parsed = urlparse(url)

        for rule in whitelist:
            rule_domain = rule.get("domain", "")
            if self._domain_matches(parsed.netloc, rule_domain):
                return True

        return False

    def _check_blacklist(self, url: str) -> bool:
        """Check if URL is in blacklist."""
        blacklist = self.config.get("blacklist", {}).get("rules", [])
        parsed = urlparse(url)

        for rule in blacklist:
            rule_domain = rule.get("domain", "")
            if self._domain_matches(parsed.netloc, rule_domain):
                return True

        return False

    def _domain_matches(self, domain: str, pattern: str) -> bool:
        """Check if domain matches pattern (supports wildcards)."""
        pattern = pattern.replace(".", r"\.")
        pattern = pattern.replace("*", ".*")
        return bool(re.match(f"^{pattern}$", domain))

    def _log_blocked_request(self, request_info: dict, reason: str):
        """Log blocked request."""
        self.metrics["blocked_requests"] += 1
        request_info["reason"] = reason
        request_info["status"] = "BLOCKED"
        self.blocked_requests.append(request_info)

        self._log_audit("REQUEST_BLOCKED", request_info)

        # Alert if threshold reached
        alert_threshold = self.config.get("global", {}).get("alerts", {}).get("alert_threshold", 10)
        if self.metrics["blocked_requests"] % alert_threshold == 0:
            logger.critical(f"🚨 ALERT: {self.metrics['blocked_requests']} requests blocked!")

    def _log_allowed_request(self, request_info: dict, reason: str):
        """Log allowed request."""
        self.metrics["allowed_requests"] += 1
        request_info["reason"] = reason
        request_info["status"] = "ALLOWED"
        self.allowed_requests.append(request_info)

        self._log_audit("REQUEST_ALLOWED", request_info)

    def get_metrics(self) -> dict:
        """Get current metrics."""
        return {
            **self.metrics,
            "uptime_seconds": (datetime.utcnow() - datetime.fromisoformat(self.metrics["started_at"])).total_seconds(),
        }

    def get_blocked_requests(self, limit: int = 100) -> list[dict]:
        """Get list of blocked requests."""
        return self.blocked_requests[-limit:]

    def get_allowed_requests(self, limit: int = 100) -> list[dict]:
        """Get list of allowed requests."""
        return self.allowed_requests[-limit:]

    def save_report(self, filepath: str | None = None):
        """Save security report to file."""
        if filepath is None:
            filepath = str(Path(__file__).parent / "logs" / f"security_report_{int(time.time())}.json")

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": self.get_metrics(),
            "blocked_requests": self.get_blocked_requests(),
            "allowed_requests": self.get_allowed_requests(),
            "config_summary": {
                "mode": self.config.get("mode"),
                "default_policy": self.config.get("default_policy"),
                "network_enabled": self.config.get("global", {}).get("network_enabled"),
                "kill_switch": self.config.get("emergency", {}).get("kill_switch"),
            },
        }

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Security report saved to {filepath}")
        return filepath


# Global instance
nac = NetworkAccessControl()


def enforce_network_policy(func: Callable) -> Callable:
    """Decorator to enforce network policy on functions."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract URL from args/kwargs
        url = None
        if args and isinstance(args[0], str):
            url = args[0]
        elif "url" in kwargs:
            url = kwargs["url"]

        if url:
            method = kwargs.get("method", "GET")
            data = kwargs.get("data") or kwargs.get("json")
            headers = kwargs.get("headers")

            allowed, reason = nac.check_request(
                url=url,
                method=method,
                data=data,
                headers=headers,
                caller=func.__module__ + "." + func.__name__,
            )

            if not allowed:
                raise NetworkAccessDenied(f"Network access denied: {reason}\nURL: {url}")

        return func(*args, **kwargs)

    return wrapper


def patch_requests_library():
    """Monkey-patch requests library to enforce access control."""
    try:
        import requests

        # Save original methods
        _original_request = requests.request
        _original_get = requests.get
        _original_post = requests.post
        _original_put = requests.put
        _original_delete = requests.delete
        _original_patch = requests.patch
        _original_head = requests.head
        _original_options = requests.options

        # Wrap with access control
        requests.request = enforce_network_policy(_original_request)
        requests.get = enforce_network_policy(_original_get)
        requests.post = enforce_network_policy(_original_post)
        requests.put = enforce_network_policy(_original_put)
        requests.delete = enforce_network_policy(_original_delete)
        requests.patch = enforce_network_policy(_original_patch)
        requests.head = enforce_network_policy(_original_head)
        requests.options = enforce_network_policy(_original_options)

        logger.info("✅ Patched requests library with access control")

    except ImportError:
        logger.debug("requests library not available, skipping patch")


def patch_httpx_library():
    """Monkey-patch httpx library to enforce access control."""
    try:
        import httpx

        # Save original Client class
        _OriginalClient = httpx.Client
        _OriginalAsyncClient = httpx.AsyncClient

        class PatchedClient(_OriginalClient):
            @enforce_network_policy
            def request(self, *args, **kwargs):
                return super().request(*args, **kwargs)

        class PatchedAsyncClient(_OriginalAsyncClient):
            @enforce_network_policy
            async def request(self, *args, **kwargs):
                return await super().request(*args, **kwargs)

        httpx.Client = PatchedClient
        httpx.AsyncClient = PatchedAsyncClient

        logger.info("✅ Patched httpx library with access control")

    except ImportError:
        logger.debug("httpx library not available, skipping patch")


def patch_aiohttp_library():
    """Monkey-patch aiohttp library to enforce access control."""
    try:
        import aiohttp

        _OriginalClientSession = aiohttp.ClientSession

        class PatchedClientSession(_OriginalClientSession):
            @enforce_network_policy
            async def request(self, *args, **kwargs):
                return await super().request(*args, **kwargs)

        aiohttp.ClientSession = PatchedClientSession

        logger.info("✅ Patched aiohttp library with access control")

    except ImportError:
        logger.debug("aiohttp library not available, skipping patch")


def patch_urllib():
    """Monkey-patch urllib to enforce access control."""
    try:
        import urllib.request

        _original_urlopen = urllib.request.urlopen

        @functools.wraps(_original_urlopen)
        def patched_urlopen(url, *args, **kwargs):
            url_str = str(url)
            allowed, reason = nac.check_request(url_str, method="GET", caller="urllib.request.urlopen")

            if not allowed:
                raise NetworkAccessDenied(f"Network access denied: {reason}\nURL: {url_str}")

            return _original_urlopen(url, *args, **kwargs)

        urllib.request.urlopen = patched_urlopen

        logger.info("✅ Patched urllib with access control")

    except Exception as e:
        logger.error(f"Failed to patch urllib: {e}")


def patch_socket():
    """Monkey-patch socket to enforce access control."""
    try:
        _original_socket_connect = socket.socket.connect

        def patched_connect(self, address):
            host = address[0] if isinstance(address, tuple) else str(address)
            port = address[1] if isinstance(address, tuple) and len(address) > 1 else "unknown"

            url = f"socket://{host}:{port}"
            allowed, reason = nac.check_request(url, method="CONNECT", caller="socket.connect")

            if not allowed:
                raise NetworkAccessDenied(f"Socket connection denied: {reason}\nAddress: {address}")

            return _original_socket_connect(self, address)

        socket.socket.connect = patched_connect

        logger.info("✅ Patched socket with access control")

    except Exception as e:
        logger.error(f"Failed to patch socket: {e}")


def apply_all_patches():
    """Apply all network access control patches."""
    logger.info("=" * 80)
    logger.info("🔒 APPLYING NETWORK ACCESS CONTROL PATCHES")
    logger.info("=" * 80)
    logger.info("⚠️  ALL NETWORK ACCESS IS DENIED BY DEFAULT")
    logger.info("⚠️  Review blocked requests and whitelist trusted clients")
    logger.info("=" * 80)

    patch_requests_library()
    patch_httpx_library()
    patch_aiohttp_library()
    patch_urllib()
    patch_socket()

    logger.info("=" * 80)
    logger.info("✅ Network access control patches applied successfully")
    logger.info("📊 Metrics endpoint available via: nac.get_metrics()")
    logger.info("📋 Blocked requests available via: nac.get_blocked_requests()")
    logger.info(f"📁 Audit logs: {nac.audit_log}")
    logger.info("=" * 80)


# Auto-apply patches on import.
# Network security can only be disabled in explicit development mode
# (requires BOTH env vars to prevent accidental or malicious bypass).
_disable_requested = os.environ.get("DISABLE_NETWORK_SECURITY") == "true"
_is_dev_env = os.environ.get("GRID_ENV", "production").lower() in ("development", "dev", "test")

if _disable_requested and not _is_dev_env:
    logger.critical(
        "DISABLE_NETWORK_SECURITY rejected — GRID_ENV is not 'development' or 'test'. "
        "Network security remains ACTIVE. Set GRID_ENV=development to allow bypass."
    )
    apply_all_patches()
elif _disable_requested and _is_dev_env:
    logger.critical(
        "NETWORK SECURITY DISABLED — GRID_ENV=%s, DISABLE_NETWORK_SECURITY=true. "
        "This MUST NOT be used in production.",
        os.environ.get("GRID_ENV"),
    )
else:
    apply_all_patches()


__all__ = [
    "NetworkAccessControl",
    "NetworkAccessDenied",
    "DataLeakDetected",
    "nac",
    "enforce_network_policy",
    "apply_all_patches",
]
