#!/usr/bin/env python3
"""
Live Network Monitoring for AI Safety Providers
Fetches provider sources and identifies safety gaps

DISABLED: This module is disabled in LOCAL_ONLY mode.
It fetches external URLs from AI providers which requires network access.
To re-enable, set WELLNESS_LOCAL_ONLY=false environment variable.
"""
import os
import sys

# LOCAL_ONLY GUARD: Prevent execution when network access is disabled
_LOCAL_ONLY = os.environ.get("WELLNESS_LOCAL_ONLY", "true").lower() == "true"
_DISABLE_NETWORK_MONITORING = os.environ.get("WELLNESS_DISABLE_NETWORK_MONITORING", "true").lower() == "true"

if _LOCAL_ONLY or _DISABLE_NETWORK_MONITORING:
    print("[DISABLED] live_network_monitor.py: Network monitoring disabled in LOCAL_ONLY mode")
    print("           Set WELLNESS_LOCAL_ONLY=false to enable external network fetching")
    if __name__ == "__main__":
        sys.exit(0)

import json
import urllib.request
from datetime import datetime
from typing import Dict, List, Any

PROVIDER_SOURCES = {
    "OpenAI": [
        "https://openai.com/safety/",
        "https://openai.com/safety/evaluations-hub/"
    ],
    "Anthropic": [
        "https://www.anthropic.com/safety",
        "https://www.anthropic.com/constitutional-ai"
    ],
    "Google": [
        "https://deepmind.google/safety/",
        "https://deepmind.google/technology/safety/"
    ],
    "xAI": [
        "https://x.ai/safety",
        "https://data.x.ai"
    ]
}

SAFETY_KEYWORDS = [
    "safety", "security", "alignment", "harm", "risk", "threat",
    "moderation", "filter", "guardrail", "policy", "protocol",
    "evaluation", "assessment", "monitoring", "audit"
]

def fetch_url(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Fetch URL and return metadata"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'AI-Safety-Monitor/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content = response.read().decode('utf-8', errors='ignore')
            return {
                "url": url,
                "status": response.status,
                "content_length": len(content),
                "success": True,
                "content": content[:5000]  # First 5KB for analysis
            }
    except Exception as e:
        return {
            "url": url,
            "status": 0,
            "error": str(e),
            "success": False
        }

def analyze_safety_gaps(content: str, provider: str, url: str) -> Dict[str, Any]:
    """Analyze content for safety gaps"""
    content_lower = content.lower()
    
    found_keywords = [kw for kw in SAFETY_KEYWORDS if kw in content_lower]
    
    gaps = []
    
    # Check for missing safety elements
    if "safety" not in content_lower:
        gaps.append("No explicit safety framework mentioned")
    if "evaluation" not in content_lower:
        gaps.append("No evaluation methodology documented")
    if "policy" not in content_lower:
        gaps.append("No safety policy defined")
    if "moderation" not in content_lower:
        gaps.append("No content moderation mentioned")
    if "guardrail" not in content_lower and "filter" not in content_lower:
        gaps.append("No guardrails or filters documented")
    
    return {
        "provider": provider,
        "url": url,
        "found_keywords": found_keywords,
        "gaps": gaps,
        "safety_score": max(0, 100 - len(gaps) * 10)
    }

def main():
    """Main monitoring function"""
    print(f"=== Live Network Monitoring - {datetime.utcnow().isoformat()} ===\n")
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "providers": {},
        "summary": {
            "total_providers": len(PROVIDER_SOURCES),
            "total_sources": 0,
            "successful_fetches": 0,
            "failed_fetches": 0,
            "total_gaps": 0
        }
    }
    
    for provider, urls in PROVIDER_SOURCES.items():
        print(f"\n📡 Monitoring {provider}...")
        provider_results = []
        
        for url in urls:
            print(f"  → Fetching: {url}")
            fetch_result = fetch_url(url)
            
            if fetch_result["success"]:
                print(f"    ✓ Status: {fetch_result['status']}, Size: {fetch_result['content_length']} bytes")
                safety_analysis = analyze_safety_gaps(
                    fetch_result["content"], 
                    provider, 
                    url
                )
                provider_results.append({
                    "fetch": fetch_result,
                    "safety_analysis": safety_analysis
                })
                results["summary"]["successful_fetches"] += 1
                results["summary"]["total_gaps"] += len(safety_analysis["gaps"])
            else:
                print(f"    ✗ Error: {fetch_result.get('error', 'Unknown')}")
                provider_results.append({
                    "fetch": fetch_result,
                    "safety_analysis": None
                })
                results["summary"]["failed_fetches"] += 1
            
            results["summary"]["total_sources"] += 1
        
        results["providers"][provider] = provider_results
    
    # Save results
    output_file = "wellness_studio/AI SAFETY/CORE_AUTOMATION/live_monitoring_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== Summary ===")
    print(f"Total Providers: {results['summary']['total_providers']}")
    print(f"Total Sources: {results['summary']['total_sources']}")
    print(f"Successful Fetches: {results['summary']['successful_fetches']}")
    print(f"Failed Fetches: {results['summary']['failed_fetches']}")
    print(f"Total Safety Gaps: {results['summary']['total_gaps']}")
    print(f"\nResults saved to: {output_file}")
    
    return results

if __name__ == "__main__":
    main()
