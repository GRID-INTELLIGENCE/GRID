#!/bin/bash
# Rollback Script: PDF Extraction with Metadata
# Rollback: Remove PDF metadata extraction, revert to simple text extraction

echo "Rolling back PDF extraction enhancements..."

# Backup current version
cp "wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py" "wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py.backup"

# Remove PDF metadata extraction from fetch_pdf function
sed -i '/# Extract metadata/,/# Extract metadata,/,/d' "wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py"

# Revert PDF extraction limit
sed -i 's/content\[:100000\]/content\[:20000\]/g' "wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py"

echo "Rollback complete. PDF extraction reverted to simple text extraction."
echo "Backup saved at: wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py.backup"
