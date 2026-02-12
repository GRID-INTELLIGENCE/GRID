"""
Safety Trend Analytics Module
Tracks safety scores over time and identifies trends
"""
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from collections import defaultdict

class SafetyTrendAnalyzer:
    """Analyzes safety score trends over time"""
    
    def __init__(self):
        self.history = []
        self.trends = {}
    
    def record_snapshot(self, results: Dict[str, Any]) -> None:
        """Record a snapshot of current safety state"""
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": results.get("summary", {}),
            "providers": {}
        }
        
        # Record provider-specific data
        for provider, provider_data in results.get("providers", {}).items():
            provider_scores = []
            for source_data in provider_data:
                if "safety_analysis" in source_data:
                    provider_scores.append(source_data["safety_analysis"].get("safety_score", 0))
            
            if provider_scores:
                snapshot["providers"][provider] = {
                    "average_score": sum(provider_scores) / len(provider_scores),
                    "gap_count": sum(len(source_data["safety_analysis"].get("gaps", [])) for source_data in provider_data if "safety_analysis" in source_data)
                }
        
        self.history.append(snapshot)
    
    def analyze_trends(self, window_size: int = 7) -> Dict[str, Any]:
        """Analyze trends over a time window"""
        if len(self.history) < window_size:
            return {"error": "Insufficient data for trend analysis"}
        
        recent_snapshots = self.history[-window_size:]
        
        trends = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "window_size": window_size,
            "overall_trend": "stable",
            "provider_trends": {}
        }
        
        # Analyze overall trend
        overall_scores = []
        for snapshot in recent_snapshots:
            avg_score = snapshot.get("summary", {}).get("average_safety_score", 0)
            overall_scores.append(avg_score)
        
        if len(overall_scores) >= 2:
            first_score = overall_scores[0]
            last_score = overall_scores[-1]
            change = last_score - first_score
            
            if change > 5:
                trends["overall_trend"] = "improving"
            elif change < -5:
                trends["overall_trend"] = "degrading"
            else:
                trends["overall_trend"] = "stable"
            
            trends["score_change"] = change
            trends["first_score"] = first_score
            trends["last_score"] = last_score
        
        # Analyze provider-specific trends
        for provider in ["OpenAI", "Anthropic", "Google", "xAI"]:
            provider_scores = []
            for snapshot in recent_snapshots:
                if provider in snapshot.get("providers", {}):
                    provider_scores.append(snapshot["providers"][provider].get("average_score", 0))
            
            if len(provider_scores) >= 2:
                first_score = provider_scores[0]
                last_score = provider_scores[-1]
                change = last_score - first_score
                
                if change > 5:
                    trends["provider_trends"][provider] = "improving"
                elif change < -5:
                    trends["provider_trends"][provider] = "degrading"
                else:
                    trends["provider_trends"][provider] = "stable"
        
        return trends
    
    def generate_trend_report(self) -> str:
        """Generate a trend analysis report"""
        trends = self.analyze_trends()
        
        report = f"# Safety Trend Analysis Report\n"
        report += f"Generated: {trends.get('timestamp', 'unknown')}\n\n"
        
        report += "## Overall Trend\n"
        report += f"Status: {trends.get('overall_trend', 'unknown').upper()}\n"
        if "score_change" in trends:
            report += f"Score Change: {trends['score_change']:+.1f} points\n"
            report += f"First Score: {trends['first_score']:.1f}/100\n"
            report += f"Last Score: {trends['last_score']:.1f}/100\n\n"
        
        report += "## Provider Trends\n"
        for provider, trend in trends.get("provider_trends", {}).items():
            report += f"- {provider}: {trend.upper()}\n"
        
        return report
    
    def get_historical_data(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical snapshot data"""
        return self.history[-limit:]
