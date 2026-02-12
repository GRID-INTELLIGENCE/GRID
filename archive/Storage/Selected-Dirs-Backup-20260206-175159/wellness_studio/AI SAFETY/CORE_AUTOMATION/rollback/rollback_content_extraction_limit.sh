#!/bin/bash
# Rollback Script: Content Extraction Limit Increase
# Rollback: Decrease content extraction limit from 100KB back to 20KB

echo "Rolling back content extraction limit from 100KB to 20KB..."

# Backup current version
cp "wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py" "wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py.backup"

# Revert content extraction limit
sed -i 's/content\[:100000\]/content\[:20000\]/g' "wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py"

# Revert PDF extraction limit
sed -i 's/content\[:100000\]/content\[:20000\]/g' "wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py"

echo "Rollback complete. Content extraction limit reverted to 20KB."
echo "Backup saved at: wellness_studio/AI SAFETY/CORE_AUTOMATION/live_network_monitor_v3.py.backup"
