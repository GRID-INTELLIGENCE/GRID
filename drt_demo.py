#!/usr/bin/env python3
"""
DRT Monitoring Demonstration Script
Shows how the DRT (Don't Repeat Themselves) behavioral monitoring system works
"""

import asyncio
import json
import time
from datetime import datetime

from grid.resilience.drt_monitor import (
    DRTMonitor,
    BehavioralFingerprint,
    check_drt_violation,
    get_drt_status,
    get_endpoint_drt_summary
)

def demonstrate_attack_patterns():
    """Demonstrate attack pattern detection."""
    print("🔍 DRT Monitoring Demonstration")
    print("=" * 50)

    # Initialize DRT monitor
    drt = DRTMonitor(similarity_threshold=0.7, retention_hours=24)

    print("📊 Testing Behavioral Pattern Analysis")
    print("-" * 40)

    # Test normal behavior
    print("\n1. Normal API calls:")
    normal_endpoints = [
        ("/api/v1/users", "GET", "192.168.1.10", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
        ("/api/v1/data", "POST", "192.168.1.11", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"),
        ("/api/v1/search", "GET", "192.168.1.12", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"),
    ]

    for endpoint, method, ip, ua in normal_endpoints:
        result = drt.monitor_endpoint(endpoint, method, ip, ua)
        print(f"   {endpoint} ({method}): Normal behavior detected")

    # Test attack-like behavior (SQL injection attempt)
    print("\n2. SQL Injection attempt:")
    sql_injection = drt.monitor_endpoint(
        "/api/v1/data/query",
        "POST",
        "10.0.0.5",
        "python-requests/2.25.1"
    )

    if sql_injection.get("escalation_applied"):
        print("   🚨 ATTACK PATTERN DETECTED!")
        print(f"   Attack Type: {sql_injection['escalation_config']['attack_type']}")
        print(f"   Similarity Score: {sql_injection['escalation_config']['similarity_score']:.3f}")
        print(f"   Threat Level: {sql_injection['escalation_config']['threat_level']}")
        print("   ✅ Protections Escalated")
    else:
        print("   Pattern not recognized (may need more data)")

    # Test directory traversal attempt
    print("\n3. Directory Traversal attempt:")
    dir_traversal = drt.monitor_endpoint(
        "/api/v1/files/../../../etc/passwd",
        "GET",
        "203.0.113.1",
        "curl/7.68.0"
    )

    if dir_traversal.get("escalation_applied"):
        print("   🚨 ATTACK PATTERN DETECTED!")
        print(f"   Attack Type: {dir_traversal['escalation_config']['attack_type']}")
        print(f"   Similarity Score: {dir_traversal['escalation_config']['similarity_score']:.3f}")
        print(f"   Threat Level: {dir_traversal['escalation_config']['threat_level']}")
        print("   ✅ Protections Escalated")
    else:
        print("   Pattern not recognized (may need more data)")

    # Test brute force login attempts
    print("\n4. Brute Force Login attempts:")
    login_attempts = [
        ("/api/v1/auth/login", "POST", "185.220.101.1", "python-requests/2.28.1"),
        ("/api/v1/auth/login", "POST", "185.220.101.2", "python-requests/2.28.1"),
        ("/api/v1/auth/login", "POST", "185.220.101.3", "python-requests/2.28.1"),
    ]

    escalation_triggered = False
    for endpoint, method, ip, ua in login_attempts:
        result = drt.monitor_endpoint(endpoint, method, ip, ua)
        if result.get("escalation_applied"):
            escalation_triggered = True
            print("   🚨 BRUTE FORCE PATTERN DETECTED!")
            print(f"   Attack Type: {result['escalation_config']['attack_type']}")
            print(f"   Similarity Score: {result['escalation_config']['similarity_score']:.3f}")
            print(f"   Threat Level: {result['escalation_config']['threat_level']}")
            print("   ✅ Login Protections Escalated")
            break

    if not escalation_triggered:
        print("   Multiple login attempts detected but pattern not yet escalated")

    print("\n📈 System Status Report")
    print("-" * 40)

    status = drt.get_system_drt_status()
    print(f"Total monitored endpoints: {status['total_monitored_endpoints']}")
    print(f"Escalated endpoints: {status['escalated_endpoints']}")
    print(f"Escalation Rate: {status['escalation_rate']:.3f}")
    print(f"Known attack vectors: {status['known_attack_vectors']}")
    print(f"Retention period: {status['retention_hours']} hours")
    print(f"Similarity Threshold: {status['similarity_threshold']:.3f}")

    print("\n🔒 Escalated Endpoint Details")
    print("-" * 40)

    for endpoint in drt.behavioral_history.keys():
        if drt.escalation_engine.is_endpoint_escalated(endpoint):
            config = drt.escalation_engine.get_endpoint_escalation(endpoint)
            summary = drt.get_endpoint_behavior_summary(endpoint)

            print(f"\nEndpoint: {endpoint}")
            print(f"  Behavior Count: {summary['behavior_count']}")
            print(f"  Escalation Time: {config['escalation_time']}")
            print(f"  Attack Type: {config['attack_type']}")
            print(f"  Similarity Score: {config['similarity_score']:.3f}")
            print(f"  Threat Level: {config['threat_level']}")

            if config.get('architectural_hardening'):
                arch = config['architectural_hardening']
                print("  Architectural Hardening:")
                print(f"    - Rate Limit Multiplier: {arch['rate_limiting_multiplier']}")
                print(f"    - Circuit Breaker: {arch['circuit_breaker_enabled']}")
                print(f"    - Isolation Level: {arch['isolation_level']}")

            if config.get('websocket_overhead'):
                ws = config['websocket_overhead']
                print("  WebSocket Overhead:")
                print(f"    - Overhead ID: {ws['overhead_id']}")
                print(f"    - Heartbeat Frequency: {ws['heartbeat_frequency']}s")
                print(f"    - Message Encryption: {ws['message_encryption']}")

def demonstrate_fingerprint_similarity():
    """Demonstrate fingerprint similarity calculations."""
    print("\n🔬 Behavioral Fingerprint Analysis")
    print("=" * 50)

    # Create similar fingerprints
    fp1 = BehavioralFingerprint("/api/v1/data", "POST", "192.168.1.100", "python-requests")
    fp2 = BehavioralFingerprint("/api/v1/data", "POST", "192.168.1.101", "python-requests")
    fp3 = BehavioralFingerprint("/api/v1/search", "GET", "192.168.1.100", "curl")

    print("Fingerprint 1 (POST /api/v1/data from python-requests):")
    print(f"  Vector: {fp1.to_vector()}")
    print("Fingerprint 2 (POST /api/v1/data from python-requests, different IP):")
    print(f"  Vector: {fp2.to_vector()}")
    print("Fingerprint 3 (GET /api/v1/search from curl):")
    print(f"  Vector: {fp3.to_vector()}")

    sim_12 = fp1.calculate_similarity(fp2)
    sim_13 = fp1.calculate_similarity(fp3)
    sim_23 = fp2.calculate_similarity(fp3)

    print("\nSimilarity Scores:")
    print(f"  Fingerprint 1 vs. Fingerprint 2: {sim_12:.3f}")
    print(f"  Fingerprint 1 vs. Fingerprint 3: {sim_13:.3f}")
    print(f"  Fingerprint 2 vs. Fingerprint 3: {sim_23:.3f}")

def main():
    """Main demonstration function."""
    print("🚀 DRT (Don't Repeat Themselves) Monitoring System")
    print("Behavioral Pattern Analysis & Dynamic Protection Escalation")
    print("=" * 70)

    try:
        # Run demonstrations
        demonstrate_attack_patterns()
        demonstrate_fingerprint_similarity()

        print("\n✅ DRT Monitoring Demonstration Complete")
        print("=" * 70)
        print("Key Features Demonstrated:")
        print("• Behavioral fingerprinting of endpoint interactions")
        print("• Similarity-based attack pattern detection")
        print("• Dynamic protection escalation")
        print("• Architectural hardening measures")
        print("• Unique WebSocket overhead application")
        print("• Comprehensive monitoring and reporting")

    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
