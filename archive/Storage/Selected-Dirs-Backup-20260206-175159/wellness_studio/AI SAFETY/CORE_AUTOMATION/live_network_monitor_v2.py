#!/usr/bin/env python3
"""
Live Network Monitoring for AI Safety Providers (v2)
Fetches provider sources and identifies safety gaps with retry logic

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
    print("[DISABLED] live_network_monitor_v2.py: Network monitoring disabled in LOCAL_ONLY mode")
    print("           Set WELLNESS_LOCAL_ONLY=false to enable external network fetching")
    if __name__ == "__main__":
        sys.exit(0)

import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import time

# Updated provider URLs with verified working URLs
PROVIDER_SOURCES = {
    "OpenAI": [
        "https://openai.com/safety/",
        "https://openai.com/safety/evaluations-hub/"
    ],
    "Anthropic": [
        "https://trust.anthropic.com/",
        "https://www.anthropic.com/transparency/platform-security"
    ],
    "Google": [
        "https://deepmind.google/responsibility-and-safety/",
        "https://deepmind.google/about/responsibility-safety/"
    ],
    "xAI": [
        "https://x.ai/safety",
        "https://data.x.ai/2025-08-20-xai-risk-management-framework.pdf"
    ]
}

# API endpoints for direct data access
API_ENDPOINTS = {
    "OpenAI": [],
    "Anthropic": [],
    "Google": [],
    "xAI": [
        "https://data.x.ai/2025-08-20-xai-risk-management-framework.pdf"
    ]
}

SAFETY_KEYWORDS = [
    "safety", "security", "alignment", "harm", "risk", "threat",
    "moderation", "filter", "guardrail", "policy", "protocol",
    "evaluation", "assessment", "monitoring", "audit",
    "constitutional", "responsible", "scaling", "preparedness"
]

def utc_now() -> str:
    """Get current UTC timestamp"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def fetch_url(url: str, timeout: int = 10, retries: int = 3) -> Dict[str, Any]:
    """Fetch URL and return metadata with retry logic"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'AI-Safety-Monitor/1.0'})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read().decode('utf-8', errors='ignore')
                return {
                    "url": url,
                    "status": response.status,
                    "content_length": len(content),
                    "success": True,
                    "content": content[:10000]  # First 10KB for analysis
                }
        except Exception as e:
            if attempt < retries - 1:
                # Exponential backoff
                wait_time = (2 ** attempt) * 1
                time.sleep(wait_time)
                continue
            return {
                "url": url,
                "status": 0,
                "error": str(e),
                "success": False
            }
    return {
        "url": url,
        "status": 0,
        "error": "Max retries exceeded",
        "success": False
    }

def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def extract_text_from_html(html: str) -> str:
    """Extract text content from HTML, focusing on main content areas"""
    import re

    # Remove script and style tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Extract text from common content containers
    content_patterns = [
        r'<main[^>]*>(.*?)</main>',
        r'<article[^>]*>(.*?)</article>',
        r'<section[^>]*>(.*?)</section>',
        r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
    ]

    extracted_texts = []
    for pattern in content_patterns:
        matches = re.findall(pattern, html, flags=re.DOTALL | re.IGNORECASE)
        extracted_texts.extend(matches)

    if extracted_texts:
        # Remove all HTML tags
        text = ' '.join(extracted_texts)
        text = re.sub(r'<[^>]+>', ' ', text)
        return text.strip()

    # Fallback: extract all text
    text = re.sub(r'<[^>]+>', ' ', html)
    return text.strip()

def analyze_safety_gaps(content: str, provider: str, url: str) -> Dict[str, Any]:
    """Analyze content for safety gaps with improved analysis"""
    content_lower = content.lower()

    # Extract text from HTML if present
    if '<' in content and '>' in content:
        content = extract_text_from_html(content)
        content_lower = content.lower()

    found_keywords = [kw for kw in SAFETY_KEYWORDS if kw in content_lower]

    gaps = []

    # Check for missing safety elements with provider-specific checks
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

    # Provider-specific checks
    if provider == "OpenAI":
        if "preparedness" not in content_lower:
            gaps.append("No Preparedness Framework mentioned")
        if "evaluations" not in content_lower:
            gaps.append("No Safety Evaluations Hub mentioned")
    elif provider == "Anthropic":
        if "constitutional" not in content_lower:
            gaps.append("No Constitutional AI mentioned")
        if "scaling" not in content_lower:
            gaps.append("No Responsible Scaling Policy mentioned")
    elif provider == "Google":
        if "frontier" not in content_lower:
            gaps.append("No Frontier Safety Framework mentioned")
        if "ai principles" not in content_lower:
            gaps.append("No AI Principles mentioned")
    elif provider == "xAI":
        if "risk" not in content_lower:
            gaps.append("No Risk Management Framework mentioned")
        if "grok" not in content_lower:
            gaps.append("No Grok safety mentioned")

    # Calculate safety score
    base_score = 100
    penalty_per_gap = 8
    safety_score = max(0, base_score - (len(gaps) * penalty_per_gap))

    return {
        "provider": provider,
        "url": url,
        "found_keywords": found_keywords,
        "gaps": gaps,
        "safety_score": safety_score
    }

def main():
    """Main monitoring function"""
    print(f"=== Live Network Monitoring - {utc_now()} ===\n")

    results = {
        "timestamp": utc_now(),
        "providers": {},
        "summary": {
            "total_providers": len(PROVIDER_SOURCES),
            "total_sources": 0,
            "successful_fetches": 0,
            "failed_fetches": 0,
            "total_gaps": 0,
            "average_safety_score": 0
        }
    }

    total_safety_score = 0
    scored_sources = 0

    for provider, urls in PROVIDER_SOURCES.items():
        print(f"\n📡 Monitoring {provider}...")
        provider_results = []

        for url in urls:
            # Validate URL before fetching
            if not validate_url(url):
                print(f"  ✗ Invalid URL: {url}")
                provider_results.append({
                    "fetch": {
                        "url": url,
                        "status": 0,
                        "error": "Invalid URL format",
                        "success": False
                    },
                    "safety_analysis": None
                })
                results["summary"]["total_sources"] += 1
                results["summary"]["failed_fetches"] += 1
                continue

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
                total_safety_score += safety_analysis["safety_score"]
                scored_sources += 1
            else:
                print(f"    ✗ Error: {fetch_result.get('error', 'Unknown')}")
                provider_results.append({
                    "fetch": fetch_result,
                    "safety_analysis": None
                })
                results["summary"]["failed_fetches"] += 1

            results["summary"]["total_sources"] += 1

        results["providers"][provider] = provider_results

    # Calculate average safety score
    if scored_sources > 0:
        results["summary"]["average_safety_score"] = round(total_safety_score / scored_sources, 1)

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
    print(f"Average Safety Score: {results['summary']['average_safety_score']}/100")
    print(f"\nResults saved to: {output_file}")

    return results

if __name__ == "__main__":
    main()
