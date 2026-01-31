"""Test script for billing service."""

import asyncio
import sys

sys.path.insert(0, 'src')

from application.mothership.services.billing import BillingService, SubscriptionTier


async def test_billing():
    print('=== Testing Billing Service ===')

    # Create billing service
    billing = BillingService()
    user_id = 'user_123'

    # Record some usage
    print('\nRecording usage...')
    await billing.record_usage(user_id, 'relationship_analysis', 50)
    await billing.record_usage(user_id, 'entity_extraction', 500)
    await billing.record_usage(user_id, 'relationship_analysis', 60)  # Total: 110
    await billing.record_usage(user_id, 'entity_extraction', 600)  # Total: 1100

    # Test FREE tier (100 relationship, 1000 entity limit)
    print('\n=== FREE Tier Billing Summary ===')
    summary = await billing.get_billing_summary(user_id, SubscriptionTier.FREE)
    print(f'Tier: {summary.tier.value}')
    print(f'Usage: {summary.usage}')
    print(f'Base cost: ${summary.base_cost_cents / 100:.2f}')
    print(f'Overages: {summary.overages.to_dict()}')
    print(f'Total due: ${summary.total_due_dollars:.2f}')

    # Test STARTER tier (1000 relationship, 10000 entity limit)
    print('\n=== STARTER Tier Billing Summary ===')
    summary2 = await billing.get_billing_summary(user_id, SubscriptionTier.STARTER)
    print(f'Tier: {summary2.tier.value}')
    print(f'Usage: {summary2.usage}')
    print(f'Base cost: ${summary2.base_cost_cents / 100:.2f}')
    print(f'Overages: {summary2.overages.to_dict()}')
    print(f'Total due: ${summary2.total_due_dollars:.2f}')

    # Test limit checking
    print('\n=== Limit Checking ===')
    exceeded, usage, limit = await billing.check_limit_exceeded(user_id, SubscriptionTier.FREE, 'relationship_analysis')
    print(f'FREE tier relationship analysis: {usage}/{limit} (exceeded: {exceeded})')

    exceeded2, usage2, limit2 = await billing.check_limit_exceeded(user_id, SubscriptionTier.STARTER, 'relationship_analysis')
    print(f'STARTER tier relationship analysis: {usage2}/{limit2} (exceeded: {exceeded2})')

    print('\n=== All Billing Tests Passed ===')


if __name__ == "__main__":
    asyncio.run(test_billing())
