#!/usr/bin/env python3
"""Dashboard server for interfaces metrics."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from grid.interfaces.config import DashboardConfig, get_config
from tools.interfaces_dashboard.collector import DashboardCollector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for dashboard."""

    def __init__(self, collector: DashboardCollector, template: str, refresh_interval: int, *args, **kwargs):
        """Initialize dashboard handler.

        Args:
            collector: Dashboard collector instance
            template: HTML template string
            refresh_interval: Auto-refresh interval in seconds
            *args: Positional arguments for BaseHTTPRequestHandler
            **kwargs: Keyword arguments for BaseHTTPRequestHandler
        """
        self.collector = collector
        self.template = template
        self.refresh_interval = refresh_interval
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

            # Inject refresh interval into template
            # Replace the default value in the interval assignment
            template = self.template.replace(
                "const interval = 30; // Server will replace this value",
                f"const interval = {self.refresh_interval}; // Auto-refresh every {self.refresh_interval} seconds",
            )
            self.wfile.write(template.encode("utf-8"))
            return

        if path == "/api/metrics":
            hours = int(query_params.get("hours", [24])[0])

            try:
                metrics = self.collector.get_all_metrics(hours=hours)
                json_data = json.dumps(metrics, default=str)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json_data.encode("utf-8"))
                return
            except Exception as e:
                logger.error(f"Error fetching metrics: {e}", exc_info=True)
                error_response = json.dumps({"error": str(e)})
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(error_response.encode("utf-8"))
                return

        # 404 for other paths
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Not Found")

    def log_message(self, format: str, *args: tuple) -> None:
        """Override log message to use logger."""
        logger.info(format % args)


def run_dashboard(
    config: DashboardConfig | None = None,
    host: str | None = None,
    port: int | None = None,
) -> None:
    """Run dashboard server.

    Args:
        config: Dashboard configuration (default: from environment)
        host: Server host (default: from config)
        port: Server port (default: from config)
    """
    if config is None:
        config = get_config()

    host = host or config.prototype_host
    port = port or config.prototype_port

    # Load HTML template
    template_file = Path(__file__).parent / "templates" / "dashboard.html"
    if not template_file.exists():
        logger.error(f"Template file not found: {template_file}")
        sys.exit(1)

    with open(template_file) as f:
        template = f.read()

    # Create collector
    collector = DashboardCollector(config)

    # Create handler class with collector
    def handler_factory(*args, **kwargs):
        return DashboardHandler(collector, template, config.refresh_interval_seconds, *args, **kwargs)

    # Create server
    server = HTTPServer((host, port), handler_factory)

    logger.info(f"Starting dashboard server on http://{host}:{port}")
    logger.info(f"Dashboard will auto-refresh every {config.refresh_interval_seconds} seconds")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down dashboard server")
        server.shutdown()
        collector.close()


def validate_db_path(db_path: str) -> str:
    """Validate database path is within allowed bounds."""
    path = Path(db_path).resolve()

    # Restrict to known safe directories
    allowed_dirs = [Path.cwd(), Path.home() / ".grid", Path("/tmp/grid"), Path("E:/grid")]

    if not any(path.is_relative_to(allowed_dir.resolve()) for allowed_dir in allowed_dirs):
        raise ValueError(f"Database path not allowed: {db_path}")

    return str(path)


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success)
    """
    parser = argparse.ArgumentParser(description="Run interfaces metrics dashboard")
    parser.add_argument("--host", type=str, default=None, help="Server host (default: from config)")
    parser.add_argument("--port", type=int, default=None, help="Server port (default: from config)")
    parser.add_argument("--db-path", type=str, default=None, help="Database path (default: from config)")

    args = parser.parse_args()

    config = get_config()

    if args.db_path:
        validated_db_path = validate_db_path(args.db_path)
        config.prototype_db_path = validated_db_path

    try:
        run_dashboard(config, host=args.host, port=args.port)
        return 0
    except Exception as e:
        logger.error(f"Dashboard failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
