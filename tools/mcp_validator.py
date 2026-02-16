#!/usr/bin/env python
"""
GRID MCP Server Health Check & Configuration Validator
"""

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Any

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class MCPValidator:
    def __init__(self):
        self.error_count = 0
        self.warning_count = 0
        self.issues = []

    def validate_config(self, config_path: str) -> bool:
        logger.info(f"Validating: {config_path}")

        config_file = Path(config_path)
        if not config_file.exists():
            self.error(f"Config file not found: {config_path}")
            return False

        try:
            with open(config_file) as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            self.error(f"Invalid JSON: {e}")
            return False

        if "$schema" not in config:
            self.warning("Missing $schema field")

        servers = config.get("servers", config.get("mcpServers", []))
        if isinstance(servers, dict):
            for name, server_config in servers.items():
                if isinstance(server_config, dict):
                    server_config["name"] = name
                    self._validate_server(server_config, 0)
        elif isinstance(servers, list):
            for i, server in enumerate(servers):
                self._validate_server(server, i + 1)
        else:
            self.error(f"'servers' must be list or dict, got {type(servers)}")
            return False

        return self.error_count == 0

    def _validate_server(self, server: dict[str, Any], index: int):
        name = server.get("name", f"server_{index}")
        logger.info(f"Validating server: {name}")

        required = ["name", "command"]
        for field in required:
            if field not in server:
                self.error(f"Server '{name}' missing: {field}")

        command = server.get("command", "")
        if command:
            import shutil

            if not (Path(command).exists() or shutil.which(command)):
                self.error(f"Command not found: {command}")

        if "port" in server:
            port = server["port"]
            if not (1 <= port <= 65535):
                self.error(f"Invalid port {port}")

    async def check_server_health(self, host="localhost", ports=None) -> bool:
        if not HTTPX_AVAILABLE:
            return True
        if ports is None:
            ports = [8000, 8001, 8002, 8005]

        logger.info("Checking MCP server health...")
        async with httpx.AsyncClient(timeout=5.0) as client:
            for port in ports:
                try:
                    response = await client.get(f"http://{host}:{port}/health")
                    logger.info(f"Port {port}: {'OK' if response.status_code == 200 else 'FAIL'}")
                except Exception as e:
                    logger.info(f"Port {port}: ERROR: {e}")
        return True

    def check_ollama_models(self) -> bool:
        logger.info("Checking Ollama models...")
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                self.error("Ollama not responding")
                return False

            output = result.stdout
            models_ok = ["nomic-embed-text", "ministral"]
            for model in models_ok:
                if model in output:
                    logger.info(f"[OK] {model}")

            return True
        except Exception as e:
            self.error(f"Ollama error: {e}")
            return False

    def check_rag_db(self) -> bool:
        rag_db = Path(".rag_db/chroma.sqlite3")
        if rag_db.exists():
            logger.info(f"[OK] RAG DB exists ({rag_db.stat().st_size / (1024 * 1024):.1f} MB)")
            return True
        self.warning("RAG DB not found")
        return False

    def check_virtual_env(self) -> bool:
        venv_path = Path(".venv/Scripts/python.exe")
        if venv_path.exists():
            logger.info(f"[OK] Venv: {venv_path}")
            return True
        self.error("Venv not found")
        return False

    def error(self, message):
        self.error_count += 1
        self.issues.append(("ERROR", message))
        logger.error(f"[ERROR] {message}")

    def warning(self, message):
        self.warning_count += 1
        self.issues.append(("WARNING", message))
        logger.warning(f"[WARNING] {message}")

    def summary(self):
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Errors:   {self.error_count}")
        print(f"Warnings: {self.warning_count}")
        if self.issues:
            print("\nIssues:")
            for level, msg in self.issues:
                print(f"  [{level}] {msg}")
        print("=" * 60)
        if self.error_count == 0:
            print("[OK] All checks passed!")
        else:
            print(f"[ERROR] {self.error_count} error(s)")
        print("=" * 60)


async def main():
    validator = MCPValidator()
    print("=" * 60)
    print("GRID MCP Server Health Check & Configuration Validator")
    print("=" * 60)

    validator.validate_config(".cursor/mcp_config.json")
    validator.validate_config("mcp-setup/mcp_config.json")

    print("\nChecking environment...")
    validator.check_virtual_env()
    validator.check_ollama_models()
    validator.check_rag_db()

    validator.summary()
    exit(0 if validator.error_count == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
