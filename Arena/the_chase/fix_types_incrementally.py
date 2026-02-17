#!/usr/bin/env python3
"""
Incremental Type Fix Script for Arena/The Chase
===============================================
Applies type annotations incrementally and verifies with mypy.

Usage:
    python fix_types_incrementally.py --stage 1
    python fix_types_incrementally.py --all
    python fix_types_incrementally.py --check
"""

import argparse
import subprocess
import sys
from pathlib import Path


# File paths
BASE_DIR = Path(__file__).parent
FILES = {
    "hooks": BASE_DIR / "python/src/the_chase/overwatch/hooks.py",
    "arena_mode": BASE_DIR / "python/src/the_chase/overwatch/arena_mode.py",
    "core": BASE_DIR / "python/src/the_chase/overwatch/core.py",
    "compressor": BASE_DIR / "python/src/the_chase/hardgate/compressor.py",
    "lumen": BASE_DIR / "python/src/the_chase/hardgate/lumen.py",
    "audit": BASE_DIR / "python/src/the_chase/overwatch/audit.py",
    "cache": BASE_DIR / "python/src/the_chase/core/cache.py",
    "resonance_demo": BASE_DIR / "resonance_chase_demo.py",
}


def run_mypy(files: list[Path] | None = None) -> tuple[int, str]:
    """Run mypy on specified files or all files."""
    if files is None:
        files = list(FILES.values())

    cmd = ["python", "-m", "mypy", "--show-error-codes", "--no-error-summary"]
    cmd.extend(str(f) for f in files)

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def check_current_state() -> None:
    """Check current mypy status for all files."""
    print("=" * 60)
    print("CURRENT MYPY STATUS")
    print("=" * 60)

    returncode, output = run_mypy()
    print(f"Exit code: {returncode}")
    print(output)

    if returncode == 0:
        print("\n✅ All files pass mypy!")
    else:
        print(f"\n❌ {output.count('error:')} errors found")


def fix_hooks() -> bool:
    """Fix hooks.py - Callable type annotations."""
    print("\n" + "=" * 60)
    print("STAGE 1: Fixing hooks.py")
    print("=" * 60)

    file_path = FILES["hooks"]
    content = file_path.read_text()

    # Check if already fixed
    if "Callable[..., Any]" in content:
        print("✓ hooks.py already has Callable type annotations")
        return True

    # Fix: Add Callable type arguments
    old_code = 'self.hooks: dict[str, list[Callable]] = {"pre_user_prompt": [], "post_cascade_response": []}'
    new_code = 'self.hooks: dict[str, list[Callable[..., Any]]] = {"pre_user_prompt": [], "post_cascade_response": []}'

    if old_code in content:
        content = content.replace(old_code, new_code)
        file_path.write_text(content)
        print("✓ Fixed hooks.py")
        return True

    print("✗ hooks.py already has different code or is already fixed")
    return False


def fix_arena_mode() -> bool:
    """Fix arena_mode.py - Return type annotation."""
    print("\n" + "=" * 60)
    print("STAGE 1: Fixing arena_mode.py")
    print("=" * 60)

    file_path = FILES["arena_mode"]
    content = file_path.read_text()

    # Check if already fixed
    if 'def _execute_with_model(self, prompt: str, model: str) -> str:' in content:
        print("✓ arena_mode.py already has return type annotation")
        return True

    # Fix: Add return type annotation
    old_code = "def _execute_with_model(self, prompt: str, model: str):"
    new_code = "def _execute_with_model(self, prompt: str, model: str) -> str:"

    if old_code in content:
        content = content.replace(old_code, new_code)
        file_path.write_text(content)
        print("✓ Fixed arena_mode.py")
        return True

    print("✗ arena_mode.py already has different code or is already fixed")
    return False


def fix_core() -> bool:
    """Fix core.py - Parameter and return type annotations."""
    print("\n" + "=" * 60)
    print("STAGE 1: Fixing core.py")
    print("=" * 60)

    file_path = FILES["core"]
    content = file_path.read_text()

    # Check if already fixed
    if 'def monitor_action(self, action: dict[str, Any]) -> dict[str, Any]:' in content:
        print("✓ core.py already has proper type annotations")
        return True

    # Fix: Add type annotations
    old_code = "def monitor_action(self, action: dict) -> dict:"
    new_code = "def monitor_action(self, action: dict[str, Any]) -> dict[str, Any]:"

    if old_code in content:
        content = content.replace(old_code, new_code)
        file_path.write_text(content)
        print("✓ Fixed core.py")
        return True

    print("✗ core.py already has different code or is already fixed")
    return False


def fix_compressor() -> bool:
    """Fix compressor.py - Dict/list type arguments."""
    print("\n" + "=" * 60)
    print("STAGE 2: Fixing compressor.py")
    print("=" * 60)

    file_path = FILES["compressor"]
    content = file_path.read_text()

    changes_made = False

    # Fix 1: Add type args to _storage
    if "self._storage: dict[str, dict] = {}" in content:
        content = content.replace(
            "self._storage: dict[str, dict] = {}",
            "self._storage: dict[str, dict[str, Any]] = {}"
        )
        changes_made = True

    # Fix 2: Add type args to _violation_log
    if "self._violation_log: list[dict] = []" in content:
        content = content.replace(
            "self._violation_log: list[dict] = []",
            "self._violation_log: list[dict[str, Any]] = []"
        )
        changes_made = True

    # Fix 3: Add type annotation to storage dict assignment
    if 'self._storage[key] = {"count": 0, "window_start": current_time}' in content:
        content = content.replace(
            'self._storage[key] = {"count": 0, "window_start": current_time}',
            'self._storage[key]: dict[str, Any] = {"count": 0, "window_start": current_time}'
        )
        changes_made = True

    if changes_made:
        file_path.write_text(content)
        print("✓ Fixed compressor.py")
        return True

    print("✗ compressor.py already has different code or is already fixed")
    return False


def fix_lumen() -> bool:
    """Fix lumen.py - List element type annotation."""
    print("\n" + "=" * 60)
    print("STAGE 2: Fixing lumen.py")
    print("=" * 60)

    file_path = FILES["lumen"]
    content = file_path.read_text()

    # Check if already fixed
    if "entities: list[PIIEntity] = []" in content:
        print("✓ lumen.py already has list element type annotation")
        return True

    # Fix: Add type annotation to entities list
    old_code = "entities = []"
    new_code = "entities: list[PIIEntity] = []"

    if old_code in content:
        content = content.replace(old_code, new_code)
        file_path.write_text(content)
        print("✓ Fixed lumen.py")
        return True

    print("✗ lumen.py already has different code or is already fixed")
    return False


def fix_audit() -> bool:
    """Fix audit.py - Dict type arguments."""
    print("\n" + "=" * 60)
    print("STAGE 2: Fixing audit.py")
    print("=" * 60)

    file_path = FILES["audit"]
    content = file_path.read_text()

    # Check if already fixed
    if 'details: dict[str, Any] | None = None' in content:
        print("✓ audit.py already has dict type arguments")
        return True

    # Fix: Add type args to details parameter
    old_code = "details: dict | None = None"
    new_code = "details: dict[str, Any] | None = None"

    if old_code in content:
        content = content.replace(old_code, new_code)
        file_path.write_text(content)
        print("✓ Fixed audit.py")
        return True

    print("✗ audit.py already has different code or is already fixed")
    return False


def fix_cache() -> bool:
    """Fix cache.py - Remove unnecessary isinstance checks and add type args."""
    print("\n" + "=" * 60)
    print("STAGE 3: Fixing cache.py")
    print("=" * 60)

    file_path = FILES["cache"]
    content = file_path.read_text()

    changes_made = False

    # Fix 1: Remove unnecessary isinstance checks (lines 230-231)
    # The types are already validated by the enum constructors
    old_check_1 = "reward_level if isinstance(reward_level, RewardLevel) else RewardLevel(reward_level)"
    new_check_1 = "RewardLevel(reward_level) if isinstance(reward_level, str) else reward_level"

    if old_check_1 in content:
        content = content.replace(old_check_1, new_check_1)
        changes_made = True

    old_check_2 = "penalty_level if isinstance(penalty_level, PenaltyLevel) else PenaltyLevel(penalty_level)"
    new_check_2 = "PenaltyLevel(penalty_level) if isinstance(penalty_level, str) else penalty_level"

    if old_check_2 in content:
        content = content.replace(old_check_2, new_check_2)
        changes_made = True

    # Fix 2: Add type annotation to entry dict (line 238)
    if 'entry: dict[str, Any] = {"value": value, "meta": meta}' not in content:
        old_entry = 'entry = {"value": value, "meta": meta}'
        new_entry = 'entry: dict[str, Any] = {"value": value, "meta": meta}'
        if old_entry in content:
            content = content.replace(old_entry, new_entry)
            changes_made = True

    if changes_made:
        file_path.write_text(content)
        print("✓ Fixed cache.py")
        return True

    print("✗ cache.py already has different code or is already fixed")
    return False


def fix_resonance_demo() -> bool:
    """Fix resonance_chase_demo.py - Add type annotations for asyncio loop."""
    print("\n" + "=" * 60)
    print("STAGE 4: Fixing resonance_chase_demo.py")
    print("=" * 60)

    file_path = FILES["resonance_demo"]
    content = file_path.read_text()

    # Check if already fixed
    if "def start_loop(loop: asyncio.AbstractEventLoop) -> None:" in content:
        print("✓ resonance_chase_demo.py already has type annotations")
        return True

    # Fix: Add type annotation to start_loop function
    old_code = "def start_loop(loop):"
    new_code = "def start_loop(loop: asyncio.AbstractEventLoop) -> None:"

    if old_code in content:
        content = content.replace(old_code, new_code)
        file_path.write_text(content)
        print("✓ Fixed resonance_chase_demo.py")
        return True

    print("✗ resonance_chase_demo.py already has different code or is already fixed")
    return False


def run_stage(stage: int) -> None:
    """Run a specific stage of fixes."""
    print(f"\n{'=' * 60}")
    print(f"RUNNING STAGE {stage}")
    print("=" * 60)

    if stage == 1:
        # Simple type args first (5 min)
        fix_hooks()
        fix_arena_mode()
        fix_core()
    elif stage == 2:
        # Dict/list type args (10 min)
        fix_compressor()
        fix_lumen()
        fix_audit()
    elif stage == 3:
        # More complex partial types (15 min)
        fix_cache()
    elif stage == 4:
        # Unknown types requiring Protocol (20 min)
        fix_resonance_demo()
    else:
        print(f"Invalid stage: {stage}")
        return

    # Check mypy after stage
    print("\n" + "=" * 60)
    print(f"MYPY CHECK AFTER STAGE {stage}")
    print("=" * 60)
    _, output = run_mypy()
    print(output)


def run_all_stages() -> None:
    """Run all stages sequentially."""
    print("\n" + "=" * 60)
    print("RUNNING ALL STAGES")
    print("=" * 60)

    for stage in range(1, 5):
        run_stage(stage)
        print("\n" + "-" * 60)

    # Final check
    print("\n" + "=" * 60)
    print("FINAL MYPY CHECK")
    print("=" * 60)
    returncode, output = run_mypy()
    print(output)

    if returncode == 0:
        print("\n✅ All fixes applied successfully!")
    else:
        print(f"\n❌ {output.count('error:')} errors remaining")


def main():
    parser = argparse.ArgumentParser(
        description="Incremental type fix script for Arena/The Chase"
    )
    parser.add_argument(
        "--stage",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run specific stage (1-4)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all stages"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check current mypy status without fixing"
    )

    args = parser.parse_args()

    if args.check:
        check_current_state()
    elif args.stage:
        run_stage(args.stage)
    elif args.all:
        run_all_stages()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
