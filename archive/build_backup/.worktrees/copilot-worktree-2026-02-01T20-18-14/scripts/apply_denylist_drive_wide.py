#!/usr/bin/env python3
"""
Drive-Wide Denylist Application
Apply server denylist rules across entire drive
"""

import os
import json
from pathlib import Path
from typing import List, Dict
import argparse
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))
from server_denylist_manager import ServerDenylistManager


class DriveWideEnforcer:
    """Enforce denylist rules across entire drive"""

    def __init__(self, denylist_config: str, root_path: str):
        self.manager = ServerDenylistManager(denylist_config)
        self.root_path = Path(root_path)
        self.results = {
            'processed': [],
            'errors': [],
            'summary': {}
        }

    def find_mcp_configs(self, exclude_patterns: List[str] = None) -> List[Path]:
        """Find all MCP configuration files"""
        if exclude_patterns is None:
            exclude_patterns = [
                '**/node_modules/**',
                '**/.git/**',
                '**/venv/**',
                '**/__pycache__/**',
                '**/dist/**',
                '**/build/**'
            ]

        configs = []
        for pattern in ['**/mcp_config.json', '**/mcp-config.json', '**/.mcp.json']:
            for config_path in self.root_path.rglob(pattern):
                # Check exclusions
                should_exclude = False
                for exclude in exclude_patterns:
                    if config_path.match(exclude):
                        should_exclude = True
                        break
                
                if not should_exclude:
                    configs.append(config_path)

        return configs

    def backup_config(self, config_path: Path) -> Path:
        """Create backup of original config"""
        backup_path = config_path.parent / f"{config_path.stem}.backup{config_path.suffix}"
        
        if not backup_path.exists():
            with open(config_path, 'r') as src:
                with open(backup_path, 'w') as dst:
                    dst.write(src.read())
        
        return backup_path

    def apply_to_config(self, config_path: Path, dry_run: bool = False) -> Dict:
        """Apply denylist to single config"""
        result = {
            'path': str(config_path),
            'success': False,
            'denied_count': 0,
            'allowed_count': 0,
            'errors': []
        }

        try:
            # Backup original
            if not dry_run:
                backup_path = self.backup_config(config_path)
                result['backup'] = str(backup_path)

            # Load config
            with open(config_path, 'r') as f:
                mcp_config = json.load(f)

            # Process servers
            for server in mcp_config.get('servers', []):
                server_name = server.get('name')
                is_denied, reason = self.manager.is_denied(server_name)

                if is_denied:
                    result['denied_count'] += 1
                    if not dry_run:
                        server['enabled'] = False
                        server['_denylist_reason'] = reason
                        server['_denylist_applied'] = True
                else:
                    result['allowed_count'] += 1

            # Write updated config
            if not dry_run:
                with open(config_path, 'w') as f:
                    json.dump(mcp_config, f, indent=2)

            result['success'] = True

        except Exception as e:
            result['errors'].append(str(e))

        return result

    def apply_drive_wide(self, dry_run: bool = False, verbose: bool = False) -> Dict:
        """Apply denylist to all configs on drive"""
        print("=" * 80)
        print("DRIVE-WIDE DENYLIST ENFORCEMENT")
        print("=" * 80)
        print(f"Root Path: {self.root_path}")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print()

        # Find configs
        print("Scanning for MCP configurations...")
        configs = self.find_mcp_configs()
        print(f"Found {len(configs)} configuration(s)\n")

        if len(configs) == 0:
            print("No MCP configurations found.")
            return self.results

        # Process each config
        total_denied = 0
        total_allowed = 0

        for config_path in configs:
            print(f"Processing: {config_path.relative_to(self.root_path)}")
            
            result = self.apply_to_config(config_path, dry_run)
            
            if result['success']:
                total_denied += result['denied_count']
                total_allowed += result['allowed_count']
                
                print(f"  ✓ Success")
                print(f"    Denied: {result['denied_count']}")
                print(f"    Allowed: {result['allowed_count']}")
                
                if not dry_run and 'backup' in result:
                    print(f"    Backup: {Path(result['backup']).name}")
                
                self.results['processed'].append(result)
            else:
                print(f"  ✗ Failed")
                for error in result['errors']:
                    print(f"    Error: {error}")
                self.results['errors'].append(result)

            print()

        # Summary
        self.results['summary'] = {
            'total_configs': len(configs),
            'processed': len(self.results['processed']),
            'errors': len(self.results['errors']),
            'total_denied': total_denied,
            'total_allowed': total_allowed
        }

        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Configurations: {self.results['summary']['total_configs']}")
        print(f"Successfully Processed: {self.results['summary']['processed']}")
        print(f"Errors: {self.results['summary']['errors']}")
        print(f"Total Servers Denied: {total_denied}")
        print(f"Total Servers Allowed: {total_allowed}")
        print("=" * 80)

        return self.results

    def restore_backups(self):
        """Restore all backed up configurations"""
        print("Restoring backed up configurations...")
        
        restored = 0
        for result in self.results['processed']:
            if 'backup' in result:
                backup_path = Path(result['backup'])
                config_path = Path(result['path'])
                
                if backup_path.exists():
                    with open(backup_path, 'r') as src:
                        with open(config_path, 'w') as dst:
                            dst.write(src.read())
                    print(f"  ✓ Restored: {config_path.name}")
                    restored += 1

        print(f"\nRestored {restored} configuration(s)")


def main():
    parser = argparse.ArgumentParser(
        description="Apply server denylist rules across entire drive"
    )
    parser.add_argument(
        '--config',
        required=True,
        help='Path to denylist configuration'
    )
    parser.add_argument(
        '--root',
        default='E:\\',
        help='Root path to scan (default: E:\\)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate without making changes'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--restore',
        action='store_true',
        help='Restore backed up configurations'
    )

    args = parser.parse_args()

    enforcer = DriveWideEnforcer(args.config, args.root)

    if args.restore:
        enforcer.restore_backups()
    else:
        results = enforcer.apply_drive_wide(
            dry_run=args.dry_run,
            verbose=args.verbose
        )

        # Save results
        results_path = Path('config/denylist_drive_wide_results.json')
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: {results_path}")


if __name__ == '__main__':
    main()
