#!/usr/bin/env bash
# =============================================
# WSL Network Monitoring Automation Script
# =============================================
# CLEANUP MODE: Debug-only feature.
# Scans ALL directories but ONLY removes corrupt/broken files:
#   - 0-byte .pcapng (failed captures)
#   - Malformed .json (invalid JSON)
#   - 0-byte .yaml/.yml (empty configs)
# NEVER removes development files (.py, .ps1, .sh, .md, etc.)
# =============================================

set -euo pipefail

INTERFACE="${1:-eth0}"
CAPTURE_FILTER="${2:-src host 192.168.1.0/24}"
COINBASE_FILTER="src host 10.0.0.5"
DEBUG_CLEANUP="${3:-}"
DATE_STAMP=$(date +%Y%m%d)
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Protected dev file extensions — NEVER removed
PROTECTED_EXT="py|ps1|sh|bat|cmd|md|txt|csv|html|css|js|ts|jsx|tsx|sql|r|ipynb|toml|ini|cfg|env|code-workspace|gitignore|gitattributes"

# WSL mount paths for E:\ directories
SSL_DIR="/mnt/e/SSL"
GRID_DIR="/mnt/e/grid"
COINBASE_DIR="/mnt/e/coinbase"
WELLNESS_DIR="/mnt/e/wellness_studio"

echo "[$TIMESTAMP] === WSL Network Monitoring ==="

# Step 1: Ensure directories exist
echo "[$TIMESTAMP] Step 1: Ensuring directories..."
mkdir -p "$SSL_DIR" "$GRID_DIR" "$COINBASE_DIR" "$WELLNESS_DIR"

# Step 2: Capture traffic
echo "[$TIMESTAMP] Step 2: Capturing traffic (2h duration)..."

echo "  [SSL] Capturing HTTPS/HTTP traffic..."
sudo tshark -i "$INTERFACE" -f "$CAPTURE_FILTER" \
  -w "$SSL_DIR/network_traffic_$DATE_STAMP.pcapng" \
  -a duration:7200 -q &
SSL_PID=$!

echo "  [Grid] Capturing SSH/DB traffic..."
sudo tshark -i "$INTERFACE" -f "tcp port 22 or tcp port 3306" \
  -w "$GRID_DIR/traffic_$DATE_STAMP.pcapng" \
  -a duration:7200 -q &
GRID_PID=$!

echo "  [Coinbase] Capturing API traffic..."
sudo tshark -i "$INTERFACE" -f "$COINBASE_FILTER" \
  -w "$COINBASE_DIR/monitoring_$DATE_STAMP.pcapng" \
  -a duration:7200 -q &
COINBASE_PID=$!

echo "  [Wellness] Capturing HTTP traffic..."
sudo tshark -i "$INTERFACE" -f "tcp port 80" \
  -w "$WELLNESS_DIR/activity_$DATE_STAMP.pcapng" \
  -a duration:7200 -q &
WELLNESS_PID=$!

echo "  Waiting for captures to complete (PIDs: $SSL_PID $GRID_PID $COINBASE_PID $WELLNESS_PID)..."
wait $SSL_PID $GRID_PID $COINBASE_PID $WELLNESS_PID 2>/dev/null || true

# Step 3: Parse traffic
echo "[$TIMESTAMP] Step 3: Parsing traffic..."

PARSE_SCRIPT="$SCRIPT_DIR/parse_traffic.py"

for entry in \
  "SSL|$SSL_DIR/network_traffic_$DATE_STAMP.pcapng|$SSL_DIR/parsed_ssl_$DATE_STAMP.json" \
  "Grid|$GRID_DIR/traffic_$DATE_STAMP.pcapng|$GRID_DIR/parsed_grid_$DATE_STAMP.json" \
  "Coinbase|$COINBASE_DIR/monitoring_$DATE_STAMP.pcapng|$COINBASE_DIR/parsed_coinbase_$DATE_STAMP.json" \
  "Wellness|$WELLNESS_DIR/activity_$DATE_STAMP.pcapng|$WELLNESS_DIR/parsed_wellness_$DATE_STAMP.json"
do
  IFS='|' read -r proto input output <<< "$entry"
  if [ -f "$input" ]; then
    echo "  [$proto] Parsing: $input"
    python3 "$PARSE_SCRIPT" "$input" --output "$output" --protocol "$proto" || \
      echo "  [$proto] WARNING: Parse failed"
  else
    echo "  [$proto] No capture file: $input"
  fi
done

# Step 4: Generate report
echo "[$TIMESTAMP] Step 4: Generating report..."

REPORT="$SSL_DIR/network_report_$DATE_STAMP.md"
{
  echo "# Network Activity Report"
  echo "**Generated:** $TIMESTAMP"
  echo ""
  echo "---"
  echo ""
  echo "## Captured Files"

  for dir in "$SSL_DIR" "$GRID_DIR" "$COINBASE_DIR" "$WELLNESS_DIR"; do
    pcap_count=$(find "$dir" -maxdepth 1 -name "*$DATE_STAMP.pcapng" 2>/dev/null | wc -l)
    echo "- **$dir**: $pcap_count capture(s) today"
  done

  echo ""
  echo "## Parsed Results"

  for dir in "$SSL_DIR" "$GRID_DIR" "$COINBASE_DIR" "$WELLNESS_DIR"; do
    json_files=$(find "$dir" -maxdepth 1 -name "*parsed*$DATE_STAMP.json" 2>/dev/null)
    if [ -n "$json_files" ]; then
      for jf in $json_files; do
        echo ""
        echo "### $(basename "$jf")"
        echo '```json'
        cat "$jf" 2>/dev/null || echo "(could not read)"
        echo '```'
      done
    fi
  done

  echo ""
  echo "---"
  echo ""
  echo "## Debug Cleanup Policy"
  echo "Cleanup is a **debugging feature** that scans all directories."
  echo "It ONLY removes corrupt/broken files:"
  echo "- 0-byte .pcapng files (failed captures)"
  echo "- Malformed .json files (invalid JSON)"
  echo "- 0-byte .yaml/.yml files (empty configs)"
  echo ""
  echo "**NEVER removed:** .py, .ps1, .sh, .md, .txt, and all other dev files."
  echo "Pass 'debug-cleanup' as 3rd argument to activate."
} > "$REPORT"

echo "  Report saved → $REPORT"

# =============================================
# Step 5: Debug Cleanup (corrupt files only)
# =============================================
# DEBUGGING FEATURE: Scans ALL directories but ONLY
# removes corrupt/broken files. Dev files are NEVER touched.
# Activated by passing 'debug-cleanup' as 3rd argument.
# =============================================
if [ "$DEBUG_CLEANUP" = "debug-cleanup" ]; then
  echo "[$TIMESTAMP] Step 5: Debug Cleanup (corrupt files only)..."
  echo "  [MODE] Scanning all directories for corrupt/broken files"
  echo "  [SAFE] Development files are NEVER removed"

  TOTAL_REMOVED=0
  TOTAL_CORRUPT=0

  for scan_dir in "$SSL_DIR" "$GRID_DIR" "$COINBASE_DIR" "$WELLNESS_DIR"; do
    [ -d "$scan_dir" ] || continue
    echo ""
    echo "  Scanning: $scan_dir"
    DIR_REMOVED=0

    for file in "$scan_dir"/*; do
      [ -f "$file" ] || continue
      filename=$(basename "$file")
      ext="${filename##*.}"

      # SAFETY: Skip all protected development file types
      if echo "$ext" | grep -qiE "^($PROTECTED_EXT)$"; then
        continue
      fi

      IS_CORRUPT=false
      REASON=""

      # Check 1: 0-byte .pcapng (failed captures)
      if [ "$ext" = "pcapng" ] && [ ! -s "$file" ]; then
        IS_CORRUPT=true
        REASON="0-byte capture (failed/incomplete)"
      fi

      # Check 2: Malformed .json
      if [ "$ext" = "json" ]; then
        if [ ! -s "$file" ]; then
          IS_CORRUPT=true
          REASON="0-byte JSON (empty)"
        elif ! python3 -c "import json; json.load(open('$file'))" 2>/dev/null; then
          IS_CORRUPT=true
          REASON="Malformed JSON (parse error)"
        fi
      fi

      # Check 3: 0-byte .yaml/.yml (empty configs)
      if ([ "$ext" = "yaml" ] || [ "$ext" = "yml" ]) && [ ! -s "$file" ]; then
        IS_CORRUPT=true
        REASON="0-byte config (empty)"
      fi

      if [ "$IS_CORRUPT" = true ]; then
        ((TOTAL_CORRUPT++)) || true
        rm -f "$file" && {
          echo "    REMOVED: $filename [$REASON]"
          ((DIR_REMOVED++)) || true
          ((TOTAL_REMOVED++)) || true
        } || echo "    FAILED:  $filename"
      fi
    done

    if [ "$DIR_REMOVED" -eq 0 ]; then
      echo "    No corrupt files found"
    fi
  done

  echo ""
  echo "  [SUMMARY] Scanned 4 directories"
  echo "  [SUMMARY] Found $TOTAL_CORRUPT corrupt file(s), removed $TOTAL_REMOVED"
  echo "  [SAFE] All development files preserved"
else
  echo "[$TIMESTAMP] Step 5: Cleanup skipped (pass 'debug-cleanup' as 3rd arg to enable)"
  echo "  Debug cleanup scans for corrupt files only (0-byte captures, bad JSON, empty configs)"
  echo "  Development files (.py, .ps1, .sh, .md, etc.) are NEVER removed"
fi

echo ""
echo "[$TIMESTAMP] Done."
