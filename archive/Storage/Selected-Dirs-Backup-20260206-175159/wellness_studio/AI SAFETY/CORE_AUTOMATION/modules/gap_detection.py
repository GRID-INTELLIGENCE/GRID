"""
Real-Time Safety Gap Detection Module
Detects new safety gaps and sends alerts via API endpoints
"""
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import hashlib

# Gap detection thresholds
GAP_SEVERITY_LEVELS = {
    "critical": 8,  # 8+ gaps
    "high": 5,      # 5-7 gaps
    "medium": 3,    # 3-4 gaps
    "low": 1        # 1-2 gaps
}

class SafetyGapDetector:
    """Detects safety gaps and generates alerts"""
    
    def __init__(self):
        self.previous_gaps = {}
        self.alert_history = []
    
    def detect_new_gaps(self, current_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect new safety gaps compared to previous run"""
        new_gaps = []
        
        for provider, provider_data in current_results.get("providers", {}).items():
            for source_data in provider_data:
                if "safety_analysis" not in source_data:
                    continue
                
                current_gaps = source_data["safety_analysis"].get("gaps", [])
                url = source_data["fetch"].get("url", "")
                
                # Generate unique key for this source
                gap_key = hashlib.md5(f"{provider}_{url}".encode()).hexdigest()
                
                # Get previous gaps
                previous_gaps = self.previous_gaps.get(gap_key, [])
                
                # Detect new gaps
                for gap in current_gaps:
                    if gap not in previous_gaps:
                        new_gaps.append({
                            "provider": provider,
                            "url": url,
                            "gap": gap,
                            "severity": self._calculate_severity(current_gaps),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                
                # Update previous gaps
                self.previous_gaps[gap_key] = current_gaps
        
        return new_gaps
    
    def _calculate_severity(self, gaps: List[str]) -> str:
        """Calculate severity level based on gap count"""
        gap_count = len(gaps)
        
        if gap_count >= GAP_SEVERITY_LEVELS["critical"]:
            return "critical"
        elif gap_count >= GAP_SEVERITY_LEVELS["high"]:
            return "high"
        elif gap_count >= GAP_SEVERITY_LEVELS["medium"]:
            return "medium"
        else:
            return "low"
    
    def generate_alert(self, gap_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate alert for a safety gap"""
        return {
            "alert_id": hashlib.md5(f"{gap_info['provider']}_{gap_info['gap']}_{gap_info['timestamp']}".encode()).hexdigest(),
            "provider": gap_info["provider"],
            "url": gap_info["url"],
            "gap": gap_info["gap"],
            "severity": gap_info["severity"],
            "timestamp": gap_info["timestamp"],
            "status": "detected",
            "action_required": gap_info["severity"] in ["critical", "high"]
        }
    
    def send_alert(self, alert: Dict[str, Any], endpoint: Optional[str] = None) -> bool:
        """Send alert via API endpoint"""
        try:
            if endpoint:
                import urllib.request
                import json
                
                data = json.dumps(alert).encode('utf-8')
                req = urllib.request.Request(
                    endpoint,
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        self.alert_history.append(alert)
                        return True
                    return False
            else:
                # Store alert locally if no endpoint
                self.alert_history.append(alert)
                return True
        except Exception as e:
            print(f"Failed to send alert: {e}")
            return False
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent alert history"""
        return self.alert_history[-limit:]
