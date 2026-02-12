#!/usr/bin/env python3
"""
Log Collection and Preservation Script
Collects all security-related logs for forensic analysis and preserves them in a timestamped archive.
"""

import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path


class LogCollector:
    """Collects and preserves log files for forensic analysis."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.collection_dir = base_path / "logs" / f"log_collection_{self.timestamp}"
        self.archive_path = base_path / "logs" / f"logs_{self.timestamp}.zip"

    def collect_logs(self) -> list[Path]:
        """Collect all log files from known locations."""
        collected_files = []

        # Security logs
        security_logs = [
            self.base_path / "logs" / "audit.log",
            self.base_path / "logs" / "network_access.log",
            self.base_path / "logs" / "alerts.log",
        ]

        # MCP server logs
        mcp_base = Path("../../workspace/mcp/servers")
        if mcp_base.exists():
            for server_dir in mcp_base.iterdir():
                if server_dir.is_dir():
                    audit_log = server_dir / "audit.log"
                    if audit_log.exists():
                        security_logs.append(audit_log)

        # System logs (if accessible)
        system_logs = [
            Path("C:/Windows/System32/LogFiles/Firewall/pfirewall.log"),
            # Add other system logs as needed
        ]

        for log_path in security_logs + system_logs:
            if log_path.exists():
                collected_files.append(log_path)

        return collected_files

    def create_collection(self, files: list[Path]) -> Path:
        """Create a collection directory with copies of log files."""
        self.collection_dir.mkdir(parents=True, exist_ok=True)

        manifest = []
        manifest.append("# Log Collection Manifest")
        manifest.append(f"**Created:** {datetime.now().isoformat()}")
        manifest.append(f"**Collection ID:** {self.timestamp}")
        manifest.append("")

        for file_path in files:
            try:
                # Copy file to collection directory
                dest_path = self.collection_dir / file_path.name
                shutil.copy2(file_path, dest_path)

                # Add to manifest
                stat = file_path.stat()
                manifest.append(f"## {file_path.name}")
                manifest.append(f"- **Original Path:** {file_path}")
                manifest.append(f"- **Size:** {stat.st_size} bytes")
                manifest.append(f"- **Modified:** {datetime.fromtimestamp(stat.st_mtime).isoformat()}")
                manifest.append(f"- **Collected:** {datetime.now().isoformat()}")
                manifest.append("")

            except Exception as e:
                manifest.append(f"## {file_path.name} (COPY FAILED)")
                manifest.append(f"- **Error:** {str(e)}")
                manifest.append("")

        # Write manifest
        manifest_path = self.collection_dir / "MANIFEST.md"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write("\n".join(manifest))

        return self.collection_dir

    def create_archive(self, collection_dir: Path) -> Path:
        """Create a ZIP archive of the collection."""
        with zipfile.ZipFile(self.archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in collection_dir.rglob("*"):
                if file_path.is_file():
                    zipf.write(file_path, file_path.relative_to(collection_dir.parent))

        return self.archive_path

    def run_collection(self) -> dict:
        """Run the complete log collection process."""
        print(f"🔍 Starting log collection at {datetime.now().isoformat()}")

        # Collect files
        files = self.collect_logs()
        print(f"📁 Found {len(files)} log files to collect")

        if not files:
            print("⚠️  No log files found to collect")
            return {"success": False, "message": "No log files found", "collection_dir": None, "archive_path": None}

        # Create collection
        collection_dir = self.create_collection(files)
        print(f"📋 Created collection directory: {collection_dir}")

        # Create archive
        archive_path = self.create_archive(collection_dir)
        print(f"📦 Created archive: {archive_path}")

        print("✅ Log collection complete")

        return {
            "success": True,
            "collection_dir": collection_dir,
            "archive_path": archive_path,
            "files_collected": len(files),
            "timestamp": self.timestamp,
        }


def main():
    """Main function."""
    base_path = Path(__file__).parent
    collector = LogCollector(base_path)
    result = collector.run_collection()

    if result["success"]:
        print("\nCollection Summary:")
        print(f"- Files collected: {result['files_collected']}")
        print(f"- Collection directory: {result['collection_dir']}")
        print(f"- Archive: {result['archive_path']}")
        print(f"- Collection ID: {result['timestamp']}")
    else:
        print(f"❌ Collection failed: {result['message']}")


if __name__ == "__main__":
    main()
