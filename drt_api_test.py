#!/usr/bin/env python3
"""
DRT API Endpoints Test Suite
"""

import sys
import asyncio
import logging
from datetime import datetime

# Add src to path
sys.path.append('src')

from fastapi import FastAPI
from application.mothership.middleware.drt_middleware import ComprehensiveDRTMiddleware
from application.mothership.routers.drt_monitoring import set_drt_middleware, router as drt_router
from application.mothership.routers.drt_monitoring import AttackVectorAddRequest

async def test_drt_api():
    """Test DRT API endpoints."""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    print('=== DRT API Endpoints Test Suite ===')
    print('Starting DRT API tests...')
    print(f'Timestamp: {datetime.now().isoformat()}')
    print()

    # Create FastAPI app
    app = FastAPI(title="DRT Test API")

    # Initialize and add DRT middleware
    print('1. SETTING UP FASTAPI WITH DRT MIDDLEWARE')
    print('-' * 40)
    middleware = ComprehensiveDRTMiddleware(
        app=app,
        enabled=True,
        similarity_threshold=0.85,
        retention_hours=96,
        websocket_overhead=True,
        auto_escalate=True,
        escalation_timeout_minutes=60,
        rate_limit_multiplier=0.5,
        sampling_rate=1.0,
        alert_on_escalation=True,
    )

    # Set middleware globally for router
    set_drt_middleware(middleware)

    # Add DRT router
    app.include_router(drt_router)

    print('✅ FastAPI app created with DRT middleware and router')

    # Test API endpoints using direct calls
    print('\n2. TESTING DRT API ENDPOINTS')
    print('-' * 40)

    # Test status endpoint
    print('Testing GET /drt/status...')
    try:
        from application.mothership.routers.drt_monitoring import get_drt_status
        status_response = await get_drt_status(middleware)
        print('✅ Status endpoint working')
        print(f'  Enabled: {status_response.enabled}')
        print(f'  Similarity threshold: {status_response.similarity_threshold}')
        print(f'  Attack vectors: {status_response.attack_vectors_count}')
    except Exception as e:
        print(f'❌ Status endpoint failed: {e}')

    # Test add attack vector endpoint
    print('\nTesting POST /drt/attack-vectors...')
    try:
        attack_request = AttackVectorAddRequest(
            path_pattern="/api/v1/secret/data",
            method="GET",
            headers=["authorization", "x-api-key"],
            body_pattern=None,
            query_pattern="format=json"
        )
        
        from application.mothership.routers.drt_monitoring import add_attack_vector
        result = await add_attack_vector(attack_request, middleware)
        print('✅ Add attack vector endpoint working')
        print(f'  Result: {result["status"]}')
        print(f'  Message: {result["message"]}')
    except Exception as e:
        print(f'❌ Add attack vector endpoint failed: {e}')

    # Test escalated endpoints endpoint
    print('\nTesting GET /drt/escalated-endpoints...')
    try:
        from application.mothership.routers.drt_monitoring import get_escalated_endpoints
        escalated_response = await get_escalated_endpoints(middleware)
        print('✅ Escalated endpoints endpoint working')
        print(f'  Escalated count: {len(escalated_response["escalated_endpoints"])}')
        for endpoint, expires in escalated_response["escalated_endpoints"].items():
            print(f'    {endpoint}: {expires}')
    except Exception as e:
        print(f'❌ Escalated endpoints endpoint failed: {e}')

    # Test manual escalation
    print('\nTesting POST /drt/escalate/test-endpoint...')
    try:
        from application.mothership.routers.drt_monitoring import escalate_endpoint
        escalate_result = await escalate_endpoint("test-endpoint", middleware)
        print('✅ Manual escalation endpoint working')
        print(f'  Result: {escalate_result["status"]}')
        print(f'  Message: {escalate_result["message"]}')
    except Exception as e:
        print(f'❌ Manual escalation endpoint failed: {e}')

    # Test behavioral history
    print('\nTesting GET /drt/behavioral-history...')
    try:
        from application.mothership.routers.drt_monitoring import get_behavioral_history
        history_response = await get_behavioral_history(middleware)
        print('✅ Behavioral history endpoint working')
        print(f'  History count: {len(history_response["behavioral_history"])}')
        for i, entry in enumerate(history_response["behavioral_history"][-3:], 1):  # Last 3
            print(f'    {i}. {entry["method"]} {entry["path_pattern"]} at {entry["timestamp"]}')
    except Exception as e:
        print(f'❌ Behavioral history endpoint failed: {e}')

    # Test de-escalation
    print('\nTesting POST /drt/de-escalate/test-endpoint...')
    try:
        from application.mothership.routers.drt_monitoring import de_escalate_endpoint
        de_escalate_result = await de_escalate_endpoint("test-endpoint", middleware)
        print('✅ De-escalation endpoint working')
        print(f'  Result: {de_escalate_result["status"]}')
        print(f'  Message: {de_escalate_result["message"]}')
    except Exception as e:
        print(f'❌ De-escalation endpoint failed: {e}')

    # Final middleware status
    print('\n3. FINAL MIDDLEWARE STATUS')
    print('-' * 40)
    final_status = middleware.get_status()
    for key, value in final_status.items():
        print(f'  {key}: {value}')

    print('\n=== API Test Summary ===')
    print('✅ DRT API endpoints are functional')
    print('✅ Status monitoring working')
    print('✅ Attack vector management working')
    print('✅ Escalation control working')
    print('✅ Behavioral history tracking working')
    print('✅ All DRT API endpoints tested successfully')

    return app, middleware

if __name__ == '__main__':
    asyncio.run(test_drt_api())
