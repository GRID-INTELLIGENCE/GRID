#!/bin/bash

# GRID Project Migration to WSL Filesystem
# Automated migration with performance benchmarking and validation
#
# Usage: bash scripts/migrate_to_wsl.sh
#        bash scripts/migrate_to_wsl.sh --dry-run
#        bash scripts/migrate_to_wsl.sh --skip-benchmark

set -euo pipefail

# Configuration
WINDOWS_PROJECT_PATH="/mnt/e/grid"
WSL_PROJECT_PATH="$HOME/projects/grid"
BACKUP_PATH="$HOME/grid_backup_$(date +%Y%m%d_%H%M%S)"
BENCHMARK_DIR="$HOME/wsl_benchmarks"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Flags
DRY_RUN=false
SKIP_BENCHMARK=false
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-benchmark)
            SKIP_BENCHMARK=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help|-h)
            cat <<EOF
GRID Project Migration to WSL Filesystem

Usage: $0 [OPTIONS]

Options:
    --dry-run         Show what would be done without making changes
    --skip-benchmark  Skip performance benchmarking
    --force           Skip confirmation prompts
    --help            Show this help message

This script will:
  1. Benchmark current performance (Windows filesystem)
  2. Migrate project to WSL filesystem
  3. Verify migration integrity
  4. Benchmark new performance (WSL filesystem)
  5. Generate comparison report

Expected improvements:
  - Git operations: 5-6x faster
  - Test execution: 2.5-3x faster
  - File I/O: 4-5x faster
  - Linting: 4-5x faster

EOF
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Helper functions
print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE} $1${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "  $1"
}

check_dependencies() {
    print_step "Checking dependencies..."

    local missing=()

    for cmd in rsync git time du df; do
        if ! command -v $cmd &> /dev/null; then
            missing+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        print_error "Missing required commands: ${missing[*]}"
        print_info "Install with: sudo apt install ${missing[*]}"
        exit 1
    fi

    print_success "All dependencies available"
}

verify_source_exists() {
    print_step "Verifying source project..."

    if [ ! -d "$WINDOWS_PROJECT_PATH" ]; then
        print_error "Source project not found at: $WINDOWS_PROJECT_PATH"
        exit 1
    fi

    if [ ! -d "$WINDOWS_PROJECT_PATH/.git" ]; then
        print_warning "Git repository not found - this may not be the correct directory"
        if [ "$FORCE" = false ]; then
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi

    print_success "Source project found"
}

check_destination() {
    print_step "Checking destination..."

    if [ -d "$WSL_PROJECT_PATH" ]; then
        print_warning "Destination already exists: $WSL_PROJECT_PATH"

        if [ "$FORCE" = false ]; then
            read -p "Overwrite existing directory? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_info "Aborting migration"
                exit 1
            fi
        fi

        print_info "Creating backup at: $BACKUP_PATH"
        if [ "$DRY_RUN" = false ]; then
            mv "$WSL_PROJECT_PATH" "$BACKUP_PATH"
            print_success "Backup created"
        fi
    fi

    # Ensure parent directory exists
    mkdir -p "$(dirname "$WSL_PROJECT_PATH")"
    print_success "Destination ready"
}

benchmark_current_performance() {
    if [ "$SKIP_BENCHMARK" = true ]; then
        print_warning "Skipping performance benchmark (--skip-benchmark)"
        return
    fi

    print_step "Benchmarking current performance (Windows filesystem)..."

    mkdir -p "$BENCHMARK_DIR"
    local benchmark_file="$BENCHMARK_DIR/before_migration.txt"

    echo "Performance Benchmark - Before Migration" > "$benchmark_file"
    echo "Date: $(date)" >> "$benchmark_file"
    echo "Location: $WINDOWS_PROJECT_PATH" >> "$benchmark_file"
    echo "" >> "$benchmark_file"

    cd "$WINDOWS_PROJECT_PATH" || exit 1

    # Git status benchmark
    print_info "Measuring git status performance..."
    echo "=== Git Status ===" >> "$benchmark_file"
    { time git status > /dev/null 2>&1; } 2>&1 | grep real >> "$benchmark_file"

    # File I/O benchmark
    print_info "Measuring file I/O performance..."
    echo "" >> "$benchmark_file"
    echo "=== File I/O (100MB write) ===" >> "$benchmark_file"
    { time dd if=/dev/zero of=testfile bs=1M count=100 2>&1; } 2>&1 | grep copied >> "$benchmark_file"
    rm -f testfile

    # Directory traversal
    print_info "Measuring directory traversal..."
    echo "" >> "$benchmark_file"
    echo "=== Directory Traversal ===" >> "$benchmark_file"
    { time find . -name "*.py" | wc -l > /dev/null 2>&1; } 2>&1 | grep real >> "$benchmark_file"

    # Python import benchmark
    if command -v python3 &> /dev/null && [ -f ".venv/bin/python" ]; then
        print_info "Measuring Python import performance..."
        echo "" >> "$benchmark_file"
        echo "=== Python Import ===" >> "$benchmark_file"
        { time .venv/bin/python -c "import sys" 2>&1; } 2>&1 | grep real >> "$benchmark_file"
    fi

    print_success "Benchmark saved to: $benchmark_file"
    cat "$benchmark_file"
}

migrate_project() {
    print_step "Migrating project to WSL filesystem..."

    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN: Would execute:"
        print_info "  rsync -avhP --exclude='.venv' --exclude='node_modules' --exclude='__pycache__' \\"
        print_info "        '$WINDOWS_PROJECT_PATH/' '$WSL_PROJECT_PATH/'"
        return
    fi

    local rsync_excludes=(
        "--exclude=.venv"
        "--exclude=node_modules"
        "--exclude=__pycache__"
        "--exclude=.pytest_cache"
        "--exclude=.ruff_cache"
        "--exclude=.mypy_cache"
        "--exclude=*.pyc"
        "--exclude=.git/objects/pack/*.pack"
        "--exclude=dist"
        "--exclude=build"
        "--exclude=*.egg-info"
    )

    # Use rsync for efficient copy with progress
    print_info "This may take several minutes depending on project size..."

    if rsync -avhP "${rsync_excludes[@]}" "$WINDOWS_PROJECT_PATH/" "$WSL_PROJECT_PATH/"; then
        print_success "Project migrated successfully"
    else
        print_error "Migration failed"
        exit 1
    fi
}

verify_migration() {
    print_step "Verifying migration integrity..."

    # Check critical directories
    local critical_dirs=("src" "tests" "docs" "scripts")
    local all_good=true

    for dir in "${critical_dirs[@]}"; do
        if [ -d "$WSL_PROJECT_PATH/$dir" ]; then
            print_success "Found: $dir/"
        else
            print_error "Missing: $dir/"
            all_good=false
        fi
    done

    # Check Git repository
    if [ -d "$WSL_PROJECT_PATH/.git" ]; then
        print_success "Git repository migrated"

        # Verify Git status
        cd "$WSL_PROJECT_PATH"
        if git status > /dev/null 2>&1; then
            print_success "Git repository is functional"
        else
            print_warning "Git repository may have issues"
        fi
    else
        print_error "Git repository not found"
        all_good=false
    fi

    if [ "$all_good" = true ]; then
        print_success "Migration verification passed"
    else
        print_error "Migration verification failed"
        exit 1
    fi
}

rebuild_venv() {
    print_step "Rebuilding virtual environment..."

    cd "$WSL_PROJECT_PATH"

    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN: Would rebuild .venv in WSL"
        return
    fi

    # Remove old venv if exists
    if [ -d ".venv" ]; then
        print_info "Removing old virtual environment..."
        rm -rf .venv
    fi

    # Create new venv
    print_info "Creating new virtual environment..."
    python3 -m venv .venv

    # Activate and install dependencies
    print_info "Installing dependencies..."
    source .venv/bin/activate

    if [ -f "requirements.txt" ]; then
        pip install --upgrade pip setuptools wheel
        pip install -r requirements.txt
    fi

    if command -v uv &> /dev/null; then
        print_info "Using uv for dependency sync..."
        uv sync
    fi

    print_success "Virtual environment ready"
}

benchmark_new_performance() {
    if [ "$SKIP_BENCHMARK" = true ]; then
        print_warning "Skipping performance benchmark (--skip-benchmark)"
        return
    fi

    print_step "Benchmarking new performance (WSL filesystem)..."

    mkdir -p "$BENCHMARK_DIR"
    local benchmark_file="$BENCHMARK_DIR/after_migration.txt"

    echo "Performance Benchmark - After Migration" > "$benchmark_file"
    echo "Date: $(date)" >> "$benchmark_file"
    echo "Location: $WSL_PROJECT_PATH" >> "$benchmark_file"
    echo "" >> "$benchmark_file"

    cd "$WSL_PROJECT_PATH" || exit 1

    # Git status benchmark
    print_info "Measuring git status performance..."
    echo "=== Git Status ===" >> "$benchmark_file"
    { time git status > /dev/null 2>&1; } 2>&1 | grep real >> "$benchmark_file"

    # File I/O benchmark
    print_info "Measuring file I/O performance..."
    echo "" >> "$benchmark_file"
    echo "=== File I/O (100MB write) ===" >> "$benchmark_file"
    { time dd if=/dev/zero of=testfile bs=1M count=100 2>&1; } 2>&1 | grep copied >> "$benchmark_file"
    rm -f testfile

    # Directory traversal
    print_info "Measuring directory traversal..."
    echo "" >> "$benchmark_file"
    echo "=== Directory Traversal ===" >> "$benchmark_file"
    { time find . -name "*.py" | wc -l > /dev/null 2>&1; } 2>&1 | grep real >> "$benchmark_file"

    # Python import benchmark
    if [ -f ".venv/bin/python" ]; then
        print_info "Measuring Python import performance..."
        echo "" >> "$benchmark_file"
        echo "=== Python Import ===" >> "$benchmark_file"
        { time .venv/bin/python -c "import sys" 2>&1; } 2>&1 | grep real >> "$benchmark_file"
    fi

    print_success "Benchmark saved to: $benchmark_file"
    cat "$benchmark_file"
}

generate_comparison_report() {
    if [ "$SKIP_BENCHMARK" = true ]; then
        return
    fi

    print_step "Generating performance comparison report..."

    local report_file="$BENCHMARK_DIR/comparison_report.md"
    local before_file="$BENCHMARK_DIR/before_migration.txt"
    local after_file="$BENCHMARK_DIR/after_migration.txt"

    if [ ! -f "$before_file" ] || [ ! -f "$after_file" ]; then
        print_warning "Benchmark files not found - skipping comparison"
        return
    fi

    cat > "$report_file" <<EOF
# GRID WSL Migration Performance Report

**Date**: $(date)
**Migration**: Windows Filesystem → WSL Filesystem

---

## Performance Comparison

### Before Migration (Windows Filesystem)

\`\`\`
$(cat "$before_file")
\`\`\`

### After Migration (WSL Filesystem)

\`\`\`
$(cat "$after_file")
\`\`\`

---

## Summary

The project has been successfully migrated from Windows filesystem to WSL native filesystem.

### Next Steps

1. **Update IDE settings** to point to new location:
   - Path: \`\\\\wsl\$\\Ubuntu\\home\\$(whoami)\\projects\\grid\`

2. **Update environment variables**:
   \`\`\`bash
   export GRID_ROOT="$WSL_PROJECT_PATH"
   export PYTHONPATH="$WSL_PROJECT_PATH/src"
   \`\`\`

3. **Verify Git configuration**:
   \`\`\`bash
   cd $WSL_PROJECT_PATH
   git config --list | grep user
   \`\`\`

4. **Run tests** to verify everything works:
   \`\`\`bash
   cd $WSL_PROJECT_PATH
   source .venv/bin/activate
   pytest tests/unit -x -q
   \`\`\`

---

## Cleanup

The original project remains at: \`$WINDOWS_PROJECT_PATH\`

**To remove the old copy** (after verifying everything works):
\`\`\`bash
rm -rf $WINDOWS_PROJECT_PATH
\`\`\`

**Backup location**: \`$BACKUP_PATH\` (if existed before)

---

*Generated by: scripts/migrate_to_wsl.sh*
EOF

    print_success "Report saved to: $report_file"

    # Display summary
    echo ""
    echo -e "${BOLD}${MAGENTA}Performance Improvement Summary:${NC}"
    echo ""

    # Try to extract and compare times (simplified)
    local before_git=$(grep -A1 "Git Status" "$before_file" | grep real | awk '{print $2}' || echo "N/A")
    local after_git=$(grep -A1 "Git Status" "$after_file" | grep real | awk '{print $2}' || echo "N/A")

    echo -e "  Git Status:  ${YELLOW}$before_git${NC} → ${GREEN}$after_git${NC}"

    # Open report in default text editor
    if command -v code &> /dev/null; then
        code "$report_file"
    elif command -v nano &> /dev/null; then
        echo ""
        read -p "Open report in nano? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            nano "$report_file"
        fi
    fi
}

update_git_config() {
    print_step "Optimizing Git configuration..."

    cd "$WSL_PROJECT_PATH"

    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN: Would configure Git for performance"
        return
    fi

    git config core.filemode false
    git config core.compression 0
    git config core.untrackedCache true
    git config core.fsmonitor true
    git config feature.manyFiles true
    git config index.threads true
    git config index.version 4
    git config pack.threads 0
    git config fetch.parallel 8

    print_success "Git configured for optimal performance"
}

display_summary() {
    print_header "Migration Complete!"

    echo -e "${GREEN}✓ Project successfully migrated to WSL filesystem${NC}"
    echo ""
    echo -e "${BOLD}New Location:${NC} $WSL_PROJECT_PATH"
    echo ""
    echo -e "${BOLD}Access from Windows:${NC}"
    echo -e "  \\\\wsl\$\\Ubuntu\\home\\$(whoami)\\projects\\grid"
    echo ""

    if [ -d "$BACKUP_PATH" ]; then
        echo -e "${BOLD}Backup:${NC} $BACKUP_PATH"
        echo ""
    fi

    echo -e "${BOLD}${CYAN}Next Steps:${NC}"
    echo ""
    echo "  1. Update your IDE to open the new WSL location"
    echo "  2. Update environment variables (GRID_ROOT, PYTHONPATH)"
    echo "  3. Run tests to verify: cd $WSL_PROJECT_PATH && pytest -x"
    echo "  4. Review comparison report: $BENCHMARK_DIR/comparison_report.md"
    echo ""
    echo -e "${YELLOW}Old Windows copy:${NC} $WINDOWS_PROJECT_PATH (safe to delete after verification)"
    echo ""
}

# Main execution
main() {
    print_header "GRID Project Migration to WSL Filesystem"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}DRY RUN MODE - No changes will be made${NC}"
        echo ""
    fi

    # Pre-flight checks
    check_dependencies
    verify_source_exists
    check_destination

    # Calculate and display sizes
    print_step "Analyzing project size..."
    local total_size=$(du -sh "$WINDOWS_PROJECT_PATH" 2>/dev/null | awk '{print $1}')
    print_info "Project size: $total_size"

    # Estimate time
    local estimate="2-5 minutes"
    if [[ "$total_size" =~ G ]]; then
        estimate="5-15 minutes"
    fi
    print_info "Estimated migration time: $estimate"

    # Confirmation
    if [ "$FORCE" = false ] && [ "$DRY_RUN" = false ]; then
        echo ""
        read -p "Proceed with migration? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Migration cancelled"
            exit 0
        fi
    fi

    # Benchmark before
    if [ "$DRY_RUN" = false ]; then
        benchmark_current_performance
    fi

    # Migrate
    migrate_project

    if [ "$DRY_RUN" = false ]; then
        # Verify
        verify_migration

        # Rebuild venv
        rebuild_venv

        # Optimize Git
        update_git_config

        # Benchmark after
        benchmark_new_performance

        # Generate report
        generate_comparison_report

        # Summary
        display_summary
    else
        print_info "DRY RUN: Migration steps completed (no changes made)"
    fi
}

# Run main function
main

exit 0
