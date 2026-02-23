#!/usr/bin/env bash
# GRID Post-11pm Contract Runner (WSL/Linux/macOS)
# Invokes Claude Code per Anthropic docs: worktree, Opus, append context, print mode.
# Usage: ./scripts/run_post_11pm_contract.sh [--dry-run] [--no-worktree]

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRID_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPORT_PATH="$GRID_ROOT/GRID_COMPREHENSIVE_REPORT_2026-02-23.md"
CONTRACT_PATH="$GRID_ROOT/.grid/post-11pm-contract.json"
ARTIFACTS_PATH="$GRID_ROOT/scripts/artifacts/session-terminal-outputs-2026-02-23.txt"
CONTEXT_FILE="$GRID_ROOT/scripts/post_11pm_context.txt"
ARTIFACTS_DIR="$GRID_ROOT/scripts/artifacts"
WORKTREE_NAME="post-11pm-20260223"
MODEL="${CLAUDE_MODEL:-opus}"

DRY_RUN=""
NO_WORKTREE=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --no-worktree) NO_WORKTREE=1 ;;
  esac
done

mkdir -p "$ARTIFACTS_DIR"
RUN_LOG="$ARTIFACTS_DIR/post_11pm_run_$(date +%Y%m%d_%H%M%S).log"
echo "GRID_ROOT=$GRID_ROOT" >> "$RUN_LOG"
echo "REPORT=$REPORT_PATH" >> "$RUN_LOG"
echo "CONTRACT=$CONTRACT_PATH" >> "$RUN_LOG"
echo "ARTIFACTS=$ARTIFACTS_PATH" >> "$RUN_LOG"

for f in "$CONTEXT_FILE" "$REPORT_PATH" "$CONTRACT_PATH"; do
  if [ ! -f "$f" ]; then
    echo "Missing: $f" >&2
    exit 1
  fi
done

if ! command -v claude &>/dev/null; then
  echo "Claude Code CLI not found. Install from https://docs.anthropic.com/en/docs/claude-code/getting-started" >&2
  echo "Paths logged to: $RUN_LOG"
  exit 1
fi

TASK_PROMPT="Execute the post-11pm contract. Read the report at GRID_COMPREHENSIVE_REPORT_2026-02-23.md and the contract at .grid/post-11pm-contract.json. Use terminal outputs at scripts/artifacts/session-terminal-outputs-2026-02-23.txt for reference. Follow actions in priority order: critical then high then medium then low. Preserve items in the contract preserve list. At the end output a short summary: what was done, what was skipped (and why), and any blocking issues."

if [ -n "$DRY_RUN" ]; then
  echo "Dry run. Would execute:"
  if [ -z "$NO_WORKTREE" ]; then
    echo "claude --worktree $WORKTREE_NAME --model $MODEL --append-system-prompt-file $CONTEXT_FILE -p \"...\""
  else
    echo "claude --model $MODEL --append-system-prompt-file $CONTEXT_FILE -p \"...\""
  fi
  echo "Paths logged to: $RUN_LOG"
  exit 0
fi

echo "Starting Claude Code (worktree=$([ -z "$NO_WORKTREE" ] && echo 'yes' || echo 'no'), model=$MODEL)..."
echo "Paths logged to: $RUN_LOG"
cd "$GRID_ROOT"
if [ -z "$NO_WORKTREE" ]; then
  claude --worktree "$WORKTREE_NAME" --model "$MODEL" --append-system-prompt-file "$CONTEXT_FILE" -p "$TASK_PROMPT"
else
  claude --model "$MODEL" --append-system-prompt-file "$CONTEXT_FILE" -p "$TASK_PROMPT"
fi
echo "EXIT=$?" >> "$RUN_LOG"
