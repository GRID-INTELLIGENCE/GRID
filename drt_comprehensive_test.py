#!/usr/bin/env python3
"""
Comprehensive DRT Monitoring Test Suite
"""

import sys
import logging
from datetime import datetime

# Add src to path
sys.path.append('src')

from grid.resilience.drt_monitor import check_drt_violation, get_drt_status, get_endpoint_drt_summary

def run_comprehensive_tests():
    """Run comprehensive DRT monitoring tests."""
    
    # Set up detailed logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    print('=== DRT Comprehensive Test Suite ===')
    print('Starting comprehensive DRT monitoring tests...')
    print(f'Timestamp: {datetime.now().isoformat()}')
    print()

    # Test 1: Baseline system status
    print('1. BASELINE SYSTEM STATUS')
    print('-' * 30)
    baseline_status = get_drt_status()
    for key, value in baseline_status.items():
        print(f'{key}: {value}')

    # Test 2: Normal legitimate traffic patterns
    print('\n2. NORMAL TRAFFIC PATTERNS')
    print('-' * 30)
    normal_requests = [
        ('/api/v1/users/profile', 'GET', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
        ('/api/v1/dashboard', 'GET', '192.168.1.101', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'),
        ('/api/v1/data/list', 'GET', '192.168.1.102', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'),
        ('/api/v1/auth/logout', 'POST', '192.168.1.103', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
    ]

    normal_results = []
    for i, (endpoint, method, ip, ua) in enumerate(normal_requests, 1):
        result = check_drt_violation(endpoint, method, ip, ua)
        normal_results.append(result)
        print(f'Normal {i}: {method} {endpoint} from {ip}')
        print(f'  Similar attacks: {result["similar_attacks_detected"]}')
        print(f'  Escalated: {result["escalation_applied"]}')

    # Test 3: Suspicious attack patterns
    print('\n3. SUSPICIOUS ATTACK PATTERNS')
    print('-' * 30)
    attack_requests = [
        ('/api/v1/auth/login', 'POST', 'brute_force_ip', 'python-requests/2.28.1'),
        ('/api/v1/data/query', 'POST', 'malicious_ip', 'curl/7.68.0'),
        ('/api/v1/upload', 'POST', 'malware_ip', 'python-requests/2.28.1'),
        ('/api/v1/admin/config', 'PUT', 'admin_ip', 'curl/7.68.0'),
    ]

    attack_results = []
    for i, (endpoint, method, ip, ua) in enumerate(attack_requests, 1):
        result = check_drt_violation(endpoint, method, ip, ua)
        attack_results.append(result)
        print(f'Attack {i}: {method} {endpoint} from {ip}')
        print(f'  Similar attacks: {result["similar_attacks_detected"]}')
        print(f'  Escalated: {result["escalation_applied"]}')
        if result.get('escalation_config'):
            attack_type = result['escalation_config']['attack_type']
            similarity = result['escalation_config']['similarity_score']
            threat = result['escalation_config']['threat_level']
            print(f'  Attack Type: {attack_type}, Similarity: {similarity:.3f}, Threat: {threat}')

    # Test 4: Endpoint behavior analysis
    print('\n4. ENDPOINT BEHAVIOR ANALYSIS')
    print('-' * 30)
    test_endpoints = ['/api/v1/auth/login', '/api/v1/data/query', '/api/v1/users/profile']
    for endpoint in test_endpoints:
        summary = get_endpoint_drt_summary(endpoint)
        print(f'Endpoint: {endpoint}')
        print(f'  Behavior count: {summary["behavior_count"]}')
        print(f'  Escalated: {summary["escalated"]}')
        if summary.get('method_distribution'):
            print(f'  Methods: {summary["method_distribution"]}')

    # Test 5: Final system status
    print('\n5. FINAL SYSTEM STATUS')
    print('-' * 30)
    final_status = get_drt_status()
    for key, value in final_status.items():
        print(f'{key}: {value}')

    print('\n=== Test Summary ===')
    print(f'Normal requests processed: {len(normal_results)}')
    print(f'Attack requests processed: {len(attack_results)}')
    escalated_count = sum(1 for r in attack_results if r['escalation_applied'])
    print(f'Attacks escalated: {escalated_count}')
    print(f'Escalation rate: {escalated_count/len(attack_results)*100:.1f}%')

    return {
        'normal_results': normal_results,
        'attack_results': attack_results,
        'baseline_status': baseline_status,
        'final_status': final_status
    }

if __name__ == '__main__':
    run_comprehensive_tests()
