#!/usr/bin/env python3
"""
Security Monitor - File System Analysis and Protection
Identifies and removes suspicious files, implements protection measures
"""

import os
import sys
import time
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Set


class SecurityMonitor:
    def __init__(self):
        self.blocklist: Set[str] = set()
        self.quarantine_path: Path = Path(tempfile.gettempdir()) / "quarantine"
        self.log_file: Path = Path(tempfile.gettempdir()) / "security_monitor.log"

        # Initialize blocklist with known suspicious patterns
        suspicious_names = [
            "nul",
            "con",
            "prn",
            "aux",
            "com1",
            "com2",
            "com3",
            "com4",
            "lpt1",
            "lpt2",
            "lpt3",
            "lpt4",
            "com0",
            "lpt0",
            "null",
            "nil",
            "undefined",
            "void",
            "eof",
            "..",
            ".",
            "...",
            "....",
            ".....",
        ]

        self.blocklist.update(name.lower() for name in suspicious_names)

        # Create quarantine directory
        self.quarantine_path.mkdir(exist_ok=True, mode=0o700)

    def log_action(self, action: str, path: str, reason: str):
        """Log security actions to file and console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {action}: {path} - {reason}\n"

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Failed to write to log: {e}")

        print(log_entry, end="")

    def is_suspicious(self, name: str) -> Tuple[bool, str]:
        """Check if a filename is suspicious"""
        lower_name = name.lower()

        # Check blocklist
        if lower_name in self.blocklist:
            return True, "Name matches security blocklist"

        # Check for suspicious patterns
        suspicious_patterns = ["nul", "null", "con", "prn", "aux"]
        for pattern in suspicious_patterns:
            if pattern in lower_name:
                return True, f"Contains reserved system name pattern: {pattern}"

        # Check for hidden/suspicious files
        if name.startswith(".") and name not in [".", ".."]:
            if len(name) > 3:
                return True, "Hidden file with suspicious extension"

        # Check for executable files in suspicious locations
        executable_exts = [".exe", ".bat", ".cmd", ".scr", ".vbs", ".js", ".ps1"]
        if any(name.lower().endswith(ext) for ext in executable_exts):
            return True, "Executable file in non-executable context"

        return False, ""

    def scan_directory(self, root: str) -> List[Dict]:
        """Scan directory for suspicious files"""
        suspicious_files = []

        # Skip system directories
        skip_dirs = {
            str(self.quarantine_path),
            "System Volume Information",
            "$RECYCLE.BIN",
            "__pycache__",
            ".git",
            "node_modules",
        }

        try:
            for root_path, dirs, files in os.walk(root):
                # Convert to Path for easier handling
                root_path = Path(root_path)

                # Skip directories in skip list
                dirs[:] = [
                    d
                    for d in dirs
                    if not any(skip in str(root_path / d) for skip in skip_dirs)
                ]

                for file_name in files:
                    file_path = root_path / file_name
                    is_suspicious, reason = self.is_suspicious(file_name)

                    if is_suspicious:
                        try:
                            stat_info = file_path.stat()
                            suspicious_files.append(
                                {
                                    "path": str(file_path),
                                    "size": stat_info.st_size,
                                    "mod_time": datetime.fromtimestamp(
                                        stat_info.st_mtime
                                    ),
                                    "is_suspicious": True,
                                    "reason": reason,
                                }
                            )
                        except Exception as e:
                            print(f"Error getting info for {file_path}: {e}")

        except Exception as e:
            print(f"Error scanning directory {root}: {e}")

        return suspicious_files

    def quarantine_file(self, file_path: str) -> bool:
        """Move file to quarantine"""
        try:
            path = Path(file_path)
            quarantine_name = f"{int(time.time() * 1000000)}_{path.name}"
            quarantine_file = self.quarantine_path / quarantine_name

            shutil.move(str(path), str(quarantine_file))

            self.log_action("QUARANTINED", file_path, f"Moved to {quarantine_file}")
            return True

        except Exception as e:
            self.log_action("QUARANTINE_FAILED", file_path, str(e))
            return False

    def remove_file(self, file_path: str) -> bool:
        """Permanently remove file"""
        try:
            os.remove(file_path)
            self.log_action("REMOVED", file_path, "Permanently deleted")
            return True

        except Exception as e:
            self.log_action("REMOVE_FAILED", file_path, str(e))
            return False

    def install_protection(self) -> bool:
        """Install protection measures"""
        try:
            # Create Python monitoring script
            monitor_script = '''#!/usr/bin/env python3
"""
Real-time security monitor
"""
import os
import time
import sys
from pathlib import Path

BLOCKLIST = {"nul", "con", "prn", "aux", "null", "nil", "undefined", "void"}

def monitor_directory(path="."):
    last_files = set()
    
    while True:
        try:
            current_files = set()
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower() in BLOCKLIST:
                        file_path = os.path.join(root, file)
                        print(f"SUSPICIOUS FILE DETECTED: {file_path}")
                        try:
                            os.remove(file_path)
                            print(f"BLOCKED and DELETED: {file_path}")
                        except Exception as e:
                            print(f"Failed to delete {file_path}: {e}")
                    current_files.add(file)
            
            time.sleep(2)  # Check every 2 seconds
            
        except KeyboardInterrupt:
            print("Monitoring stopped by user")
            break
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_directory()
'''

            monitor_path = Path(tempfile.gettempdir()) / "realtime_security_monitor.py"
            with open(monitor_path, "w", encoding="utf-8") as f:
                f.write(monitor_script)

            # Make executable
            os.chmod(monitor_path, 0o755)

            self.log_action(
                "PROTECTION", str(monitor_path), "Real-time monitor script installed"
            )

            # Create Windows batch script
            batch_script = """@echo off
REM Security Monitor for Windows
:monitor
timeout /t 5 >nul 2>&1
if exist "nul" (
    echo SUSPICIOUS FILE DETECTED: nul >> %TEMP%\\security_alerts.log
    del /f /q "nul" 2>nul
    echo BLOCKED and DELETED: nul >> %TEMP%\\security_alerts.log
)
if exist "con" (
    echo SUSPICIOUS FILE DETECTED: con >> %TEMP%\\security_alerts.log
    del /f /q "con" 2>nul
    echo BLOCKED and DELETED: con >> %TEMP%\\security_alerts.log
)
if exist "prn" (
    echo SUSPICIOUS FILE DETECTED: prn >> %TEMP%\\security_alerts.log
    del /f /q "prn" 2>nul
    echo BLOCKED and DELETED: prn >> %TEMP%\\security_alerts.log
)
goto monitor
"""

            batch_path = Path(tempfile.gettempdir()) / "security_monitor.bat"
            with open(batch_path, "w", encoding="utf-8") as f:
                f.write(batch_script)

            self.log_action(
                "PROTECTION",
                str(batch_path),
                "Windows batch protection script installed",
            )

            return True

        except Exception as e:
            print(f"Failed to install protection: {e}")
            return False


def main():
    print("🔒 SECURITY MONITOR - File System Analysis and Protection")
    print("=" * 60)

    # Initialize security monitor
    sm = SecurityMonitor()

    # Get directory to scan
    root = "."
    if len(sys.argv) > 1:
        root = sys.argv[1]

    root_path = Path(root).resolve()
    print(f"🔍 Scanning directory: {root_path}")
    print()

    # Scan for suspicious files
    suspicious_files = sm.scan_directory(str(root_path))

    if not suspicious_files:
        print("✅ No suspicious files found")
    else:
        print(f"🚨 Found {len(suspicious_files)} suspicious files:")
        print()

        for i, file_info in enumerate(suspicious_files, 1):
            print(f"{i}. {file_info['path']}")
            print(f"   Size: {file_info['size']} bytes")
            print(f"   Modified: {file_info['mod_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Reason: {file_info['reason']}")
            print()

        # Ask for action
        print("Choose action:")
        print("1. Quarantine suspicious files")
        print("2. Permanently remove suspicious files")
        print("3. Only remove 'nul' files")
        print("4. Skip removal")

        try:
            choice = input("Enter choice (1-4): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n⏭️  Skipping file removal")
            choice = "4"

        if choice == "1":
            print("\n🔒 Quarantining suspicious files...")
            for file_info in suspicious_files:
                sm.quarantine_file(file_info["path"])

        elif choice == "2":
            print("\n🗑️  Removing suspicious files...")
            for file_info in suspicious_files:
                sm.remove_file(file_info["path"])

        elif choice == "3":
            print("\n🎯 Removing only 'nul' files...")
            for file_info in suspicious_files:
                if Path(file_info["path"]).name.lower() == "nul":
                    sm.remove_file(file_info["path"])

        elif choice == "4":
            print("\n⏭️  Skipping file removal")

        else:
            print("\n❌ Invalid choice")

    # Install protection measures
    print("\n🛡️ Installing protection measures...")
    sm.install_protection()

    print("\n✅ Security analysis complete!")
    print(f"📋 Log file: {sm.log_file}")
    print(f"🔒 Quarantine directory: {sm.quarantine_path}")
    print("\n🛡️ Protection measures installed:")
    print("   - Real-time file monitoring script")
    print("   - Windows batch protection script")
    print("   - Automatic suspicious file deletion")
    print(f"\n🔄 To start real-time monitoring, run:")
    print(f"   python {Path(tempfile.gettempdir()) / 'realtime_security_monitor.py'}")

    # Immediately remove the 'nul' file if it exists
    nul_file = Path("nul")
    if nul_file.exists():
        print(f"\n🎯 Immediately removing 'nul' file found at: {nul_file}")
        sm.remove_file(str(nul_file))


if __name__ == "__main__":
    import tempfile

    main()
