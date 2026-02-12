#!/usr/bin/env python3
"""
Live Network Monitoring for AI Safety Providers with JavaScript Rendering (v3)
Fetches provider sources and identifies safety gaps using headless browser

DISABLED: This module is disabled in LOCAL_ONLY mode.
It fetches external URLs from AI providers using Playwright browser automation.
To re-enable, set WELLNESS_LOCAL_ONLY=false environment variable.
"""
import os
import sys

# LOCAL_ONLY GUARD: Prevent execution when network access is disabled
_LOCAL_ONLY = os.environ.get("WELLNESS_LOCAL_ONLY", "true").lower() == "true"
_DISABLE_NETWORK_MONITORING = os.environ.get("WELLNESS_DISABLE_NETWORK_MONITORING", "true").lower() == "true"

if _LOCAL_ONLY or _DISABLE_NETWORK_MONITORING:
    print("[DISABLED] live_network_monitor_v3.py: Network monitoring disabled in LOCAL_ONLY mode")
    print("           Set WELLNESS_LOCAL_ONLY=false to enable external network fetching")
    if __name__ == "__main__":
        sys.exit(0)

import json
import urllib.request
import urllib.parse
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import time
import re

# Import innovative modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))
from gap_detection import SafetyGapDetector  # type: ignore
from trend_analytics import SafetyTrendAnalyzer  # type: ignore
from protocol_generator import SafetyProtocolGenerator  # type: ignore

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

# Direct API endpoints for structured data
API_ENDPOINTS = {
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

# Content cache
_content_cache = {}

def get_content_hash(content: str) -> str:
    """Generate hash for content"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def get_cached_content(url: str) -> Optional[str]:
    """Get cached content for URL"""
    return _content_cache.get(url)

def set_cached_content(url: str, content: str) -> None:
    """Cache content for URL"""
    _content_cache[url] = content

def is_content_cached(url: str) -> bool:
    """Check if content is cached"""
    return url in _content_cache

def utc_now() -> str:
    """Get current UTC timestamp"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def fetch_with_javascript_rendering(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Fetch URL with JavaScript rendering using Playwright"""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Set timeout and navigate
            page.set_default_timeout(timeout * 1000)
            page.goto(url, wait_until="networkidle")

            # Wait for content to load
            time.sleep(2)

            # Extract text content
            content = page.evaluate("() => document.body.innerText")

            browser.close()

            # Cache the content
            set_cached_content(url, content)

            return {
                "url": url,
                "status": 200,
                "content_length": len(content),
                "success": True,
                "content": content[:100000],  # First 100KB for analysis
                "method": "javascript_rendering",
                "cached": False
            }
    except ImportError:
        # Fallback to regular HTTP fetch if Playwright not available
        return fetch_url(url, timeout)
    except Exception as e:
        return {
            "url": url,
            "status": 0,
            "error": str(e),
            "success": False,
            "method": "javascript_rendering",
            "cached": False
        }

def fetch_url(url: str, timeout: int = 10, retries: int = 3) -> Dict[str, Any]:
    """Fetch URL and return metadata with retry logic and caching"""
    # Check cache first
    cached_content = get_cached_content(url)
    if cached_content:
        return {
            "url": url,
            "status": 200,
            "content_length": len(cached_content),
            "success": True,
            "content": cached_content[:100000],  # First 100KB for analysis
            "method": "http_fetch",
            "cached": True
        }

    # Fetch from network
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'AI-Safety-Monitor/1.0'})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read().decode('utf-8', errors='ignore')

                # Cache the content
                set_cached_content(url, content)

                return {
                    "url": url,
                    "status": response.status,
                    "content_length": len(content),
                    "success": True,
                    "content": content[:100000],  # First 100KB for analysis
                    "method": "http_fetch",
                    "cached": False
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
                "success": False,
                "method": "http_fetch",
                "cached": False
            }
    return {
        "url": url,
        "status": 0,
        "error": "Max retries exceeded",
        "success": False,
        "method": "http_fetch",
        "cached": False
    }

def fetch_pdf(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Fetch PDF and extract text with metadata"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'AI-Safety-Monitor/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content = response.read()

            # Try to extract text from metadata
            try:
                from pypdf import PdfReader  # type: ignore
                from io import BytesIO

                pdf_file = BytesIO(content)
                pdf_reader = PdfReader(pdf_file)

                # Extract metadata
                metadata = pdf_reader.metadata

                # Extract table of contents if available
                toc = pdf_reader.outline if hasattr(pdf_reader, 'outline') else None

                # Extract full text content
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"

                # Build metadata summary
                metadata_summary = {
                    "title": metadata.get('/Title', 'Unknown') if metadata else 'Unknown',
                    "author": metadata.get('/Author', 'Unknown') if metadata else 'Unknown',
                    "subject": metadata.get('/Subject', 'Unknown') if metadata else 'Unknown',
                    "creator": metadata.get('/Creator', 'Unknown') if metadata else 'Unknown',
                    "pages": len(pdf_reader.pages)
                }

                # Cache the content
                set_cached_content(url, text)

                return {
                    "url": url,
                    "status": response.status,
                    "content_length": len(content),
                    "success": True,
                    "content": text[:100000],  # First 100KB for analysis
                    "metadata": metadata_summary,
                    "method": "pdf_extraction",
                    "cached": False
                }
            except ImportError:
                # Fallback: return raw content
                text_content = content[:100000].decode('utf-8', errors='ignore')
                set_cached_content(url, text_content)

                return {
                    "url": url,
                    "status": response.status,
                    "content_length": len(content),
                    "success": True,
                    "content": text_content,
                    "method": "pdf_raw",
                    "cached": False
                }
    except Exception as e:
        return {
            "url": url,
            "status": 0,
            "error": str(e),
            "success": False,
            "method": "pdf_extraction",
            "cached": False
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
    print(f"=== Live Network Monitoring with JavaScript Rendering - {utc_now()} ===\n")

    results = {
        "timestamp": utc_now(),
        "providers": {},
        "summary": {
            "total_providers": len(PROVIDER_SOURCES),
            "total_sources": 0,
            "successful_fetches": 0,
            "failed_fetches": 0,
            "total_gaps": 0,
            "average_safety_score": 0,
            "methods_used": []
        }
    }

    gap_detector = SafetyGapDetector()
    trend_analyzer = SafetyTrendAnalyzer()
    protocol_generator = SafetyProtocolGenerator()

    total_safety_score = 0
    scored_sources = 0
    methods_used = set()

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
                        "success": False,
                        "method": "validation"
                    },
                    "safety_analysis": None
                })
                results["summary"]["total_sources"] += 1
                results["summary"]["failed_fetches"] += 1
                continue

            print(f"  → Fetching: {url}")

            # Determine fetch method based on URL
            if url.endswith('.pdf'):
                fetch_result = fetch_pdf(url)
            elif provider in API_ENDPOINTS and url in API_ENDPOINTS[provider]:
                # Try JavaScript rendering for known API endpoints
                fetch_result = fetch_with_javascript_rendering(url)
            else:
                # Try JavaScript rendering first, fallback to HTTP
                fetch_result = fetch_with_javascript_rendering(url)
                if not fetch_result["success"]:
                    fetch_result = fetch_url(url)

            if fetch_result["success"]:
                method = fetch_result.get("method", "unknown")
                methods_used.add(method)
                print(f"    ✓ Status: {fetch_result['status']}, Size: {fetch_result['content_length']} bytes, Method: {method}")
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

    results["summary"]["methods_used"] = list(methods_used)

    # Record snapshot for trend analysis
    trend_analyzer.record_snapshot(results)

    # Detect new gaps and generate alerts
    new_gaps = gap_detector.detect_new_gaps(results)
    if new_gaps:
        print(f"\n🚨 Detected {len(new_gaps)} new safety gaps")
        for gap in new_gaps:
            alert = gap_detector.generate_alert(gap)
            print(f"  - {gap['provider']}: {gap['gap']} (Severity: {gap['severity']})")
            gap_detector.send_alert(alert)

    # Analyze trends
    trends = trend_analyzer.analyze_trends()
    if "error" in trends:
        trend_status = "INSUFFICIENT DATA"
        print(f"\n📊 Trend Analysis: {trends['error']}")
    else:
        trend_status = trends.get("overall_trend", "unknown").upper()
        print(f"\n📊 Trend Analysis: {trend_status}")
        if "score_change" in trends:
            print(f"   Score Change: {trends['score_change']:+.1f} points")

    # Generate protocols for providers with high gap counts
    for provider, provider_data in results["providers"].items():
        total_gaps = sum(
            len(source_data["safety_analysis"].get("gaps", []))
            for source_data in provider_data
            if "safety_analysis" in source_data
        )
        if total_gaps >= 5:
            # Calculate provider-specific safety score
            provider_scores = [
                source_data["safety_analysis"].get("safety_score", 0)
                for source_data in provider_data
                if "safety_analysis" in source_data
            ]
            provider_avg_score = round(sum(provider_scores) / len(provider_scores)) if provider_scores else results["summary"]["average_safety_score"]

            print(f"\n📝 Generating safety protocol for {provider}...")
            protocol = protocol_generator.generate_protocol(
                provider,
                [gap for source_data in provider_data
                 for gap in source_data["safety_analysis"].get("gaps", [])
                 if "safety_analysis" in source_data],
                provider_avg_score
            )
            print(f"   Generated: {protocol['protocol_id']}")
            print(f"   Severity: {protocol['severity'].upper()}")
            print(f"   Recommendations: {len(protocol['recommendations'])}")

    # Save results
    output_file = "wellness_studio/AI SAFETY/CORE_AUTOMATION/live_monitoring_results_v3.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n=== Summary ===")
    print(f"Total Providers: {results['summary']['total_providers']}")
    print(f"Total Sources: {results['summary']['total_sources']}")
    print(f"Successful Fetches: {results['summary']['successful_fetches']}")
    print(f"Failed Fetches: {results['summary']['failed_fetches']}")
    print(f"Total Safety Gaps: {results['summary']['total_gaps']}")
    print(f"Average Safety Score: {results['summary']['average_safety_score']}/100")
    print(f"Methods Used: {', '.join(results['summary']['methods_used'])}")
    print(f"\nInnovative Features:")
    print(f"- Real-Time Gap Detection: {len(new_gaps)} gaps detected")
    print(f"- Trend Analytics: {trend_status}")
    print(f"- Protocol Generation: Enabled")
    print(f"\nResults saved to: {output_file}")

    return results

if __name__ == "__main__":
    main()
