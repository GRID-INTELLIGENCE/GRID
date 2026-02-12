#!/bin/bash
# Rollback Script: Content Caching
# Rollback: Remove content caching functionality

echo "Rolling back content caching functionality..."

# Backup current version
cp "wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py" "wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py.backup"

# Remove caching functions
sed -i '/# Content cache/,/def is_content_cached/,/d' "wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py"

# Remove cache checks from fetch functions
sed -i '/# Check cache first/,/# Cache the content/,/d' "wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py"
sed -i '/# Cache the content/,/set_cached_content(url, content)/,/d' "wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py"

echo "Rollback complete. Content caching functionality removed."
echo "Backup saved at: wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py.backup"
