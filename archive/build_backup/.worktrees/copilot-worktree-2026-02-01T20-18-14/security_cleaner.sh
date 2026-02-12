#!/bin/bash
# Security Cleaner - Immediate threat removal and protection

echo "🔒 SECURITY CLEANER - File System Analysis and Protection"
echo "========================================================="

# Find and immediately remove suspicious files
echo "🚨 Scanning for immediate threats..."

# Current directory
CURRENT_DIR=$(pwd)
echo "🔍 Scanning directory: $CURRENT_DIR"

# Known dangerous filenames (Windows reserved names)
DANGEROUS_FILES=("nul" "con" "prn" "aux" "com1" "com2" "com3" "com4" "lpt1" "lpt2" "lpt3" "lpt4")

# Counter for removed files
REMOVED_COUNT=0

# Function to remove file safely
remove_threat() {
    local file_path="$1"
    if [ -f "$file_path" ]; then
        echo "🗑️  REMOVING THREAT: $file_path"
        rm -f "$file_path"
        if [ $? -eq 0 ]; then
            echo "✅ Successfully removed: $file_path"
            ((REMOVED_COUNT++))
            echo "$(date '+%Y-%m-%d %H:%M:%S') - REMOVED: $file_path" >> /tmp/security_cleaner.log
        else
            echo "❌ Failed to remove: $file_path"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - FAILED: $file_path" >> /tmp/security_cleaner.log
        fi
    fi
}

# Scan current directory for threats
for dangerous in "${DANGEROUS_FILES[@]}"; do
    remove_threat "$CURRENT_DIR/$dangerous"
done

# Recursive scan for additional threats
echo "🔍 Performing recursive scan..."
find "$CURRENT_DIR" -type f \( -iname "nul" -o -iname "con" -o -iname "prn" -o -iname "aux" \) 2>/dev/null | while read file; do
    remove_threat "$file"
done

# Specific check for the 'nul' file mentioned
if [ -f "nul" ]; then
    echo "🎯 TARGET FILE 'nul' DETECTED - REMOVING IMMEDIATELY"
    remove_threat "nul"
fi

echo ""
echo "📊 SUMMARY:"
echo "   Files removed: $REMOVED_COUNT"
echo "   Log file: /tmp/security_cleaner.log"

# Create ongoing protection script
echo "🛡️ Installing protection measures..."

# Create Windows batch protection
cat > "/tmp/security_monitor.bat" << 'EOF'
@echo off
REM Security Monitor - Continuous Protection
:monitor
timeout /t 3 >nul 2>&1
if exist "nul" (
    echo [$(date /t) $(time /t)] SUSPICIOUS: nul detected and deleted >> %TEMP%\security_alerts.log
    del /f /q "nul" 2>nul
)
if exist "con" (
    echo [$(date /t) $(time /t)] SUSPICIOUS: con detected and deleted >> %TEMP%\security_alerts.log
    del /f /q "con" 2>nul
)
if exist "prn" (
    echo [$(date /t) $(time /t)] SUSPICIOUS: prn detected and deleted >> %TEMP%\security_alerts.log
    del /f /q "prn" 2>nul
)
if exist "aux" (
    echo [$(date /t) $(time /t)] SUSPICIOUS: aux detected and deleted >> %TEMP%\security_alerts.log
    del /f /q "aux" 2>nul
)
goto monitor
EOF

# Create Unix/Linux protection script
cat > "/tmp/security_monitor.sh" << 'EOF'
#!/bin/bash
# Security Monitor - Continuous Protection for Unix/Linux

MONITOR_DIR="."
ALERT_LOG="/tmp/security_alerts.log"
DANGEROUS_FILES=("nul" "con" "prn" "aux" "null" "nil" "undefined" "void")

monitor_loop() {
    while true; do
        for dangerous in "${DANGEROUS_FILES[@]}"; do
            if [ -f "$MONITOR_DIR/$dangerous" ]; then
                echo "[$(date)] SUSPICIOUS: $dangerous detected and deleted" >> "$ALERT_LOG"
                rm -f "$MONITOR_DIR/$dangerous" 2>/dev/null
            fi
        done
        sleep 2
    done
}

echo "Starting security monitor for directory: $MONITOR_DIR"
monitor_loop
EOF

chmod +x "/tmp/security_monitor.sh"

echo "✅ Protection scripts created:"
echo "   Windows: /tmp/security_monitor.bat"
echo "   Unix/Linux: /tmp/security_monitor.sh"

# Create immediate one-time cleanup
echo ""
echo "🔄 Running immediate cleanup..."

# Final verification
FINAL_CHECK=0
for dangerous in "${DANGEROUS_FILES[@]}"; do
    if [ -f "$CURRENT_DIR/$dangerous" ]; then
        echo "⚠️  STILL EXISTS: $CURRENT_DIR/$dangerous"
        ((FINAL_CHECK++))
    fi
done

if [ $FINAL_CHECK -eq 0 ]; then
    echo "✅ All threats eliminated!"
else
    echo "⚠️  $FINAL_CHECK threats may still exist"
fi

echo ""
echo "📋 NEXT STEPS:"
echo "1. Review log: cat /tmp/security_cleaner.log"
echo "2. Start continuous monitoring:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    echo "   Run: /tmp/security_monitor.bat"
else
    echo "   Run: /tmp/security_monitor.sh"
fi
echo "3. Monitor alerts: tail -f /tmp/security_alerts.log"

echo ""
echo "🔒 Security cleaning complete!"