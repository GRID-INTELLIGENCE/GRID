import pytest

from application.resonance.stripe_billing import CostTier, StripeBilling


@pytest.mark.asyncio
async def test_calculate_overage_free_tier():
    """Test that overage is correctly calculated for the FREE tier."""
    # Free tier has 1000 events limit
    billing = StripeBilling(cost_tier=CostTier.FREE, meter_event_callback=lambda x: None)
    customer_id = "cus_test_free"

    # Record 1500 events (500 over limit)
    billing.record_meaningful_events(customer_id, 1500)

    invoice = await billing.get_upcoming_invoice(customer_id)

    assert invoice is not None
    assert invoice.customer_id == customer_id
    # Base price for FREE should be 0
    # Overage for 500 events at $0.01/event = $5.00
    assert invoice.amount_due == 5.0
    assert len(invoice.line_items) == 2
    assert invoice.line_items[0]["description"].lower() == "subscription base (free)"
    assert invoice.line_items[1]["description"] == "Resonance Events Overage"
    assert invoice.line_items[1]["quantity"] == 500
    assert invoice.line_items[1]["amount"] == 5.0


@pytest.mark.asyncio
async def test_calculate_overage_standard_tier():
    """Test that overage is correctly calculated for the STANDARD tier."""
    # Standard tier has 10000 events limit, $49.00 base
    billing = StripeBilling(cost_tier=CostTier.STANDARD, meter_event_callback=lambda x: None)
    customer_id = "cus_test_standard"

    # Record 12000 events (2000 over limit)
    billing.record_meaningful_events(customer_id, 12000)

    invoice = await billing.get_upcoming_invoice(customer_id)

    assert invoice is not None
    # Base price $49.00 + Overage for 2000 events at $0.01/event ($20.00) = $69.00
    assert invoice.amount_due == 69.0
    assert invoice.line_items[0]["amount"] == 49.0
    assert invoice.line_items[1]["amount"] == 20.0


@pytest.mark.asyncio
async def test_no_overage_premium_tier():
    """Test that no overage is charged if usage is below limit."""
    # Premium tier has 100000 events limit, $199.00 base
    billing = StripeBilling(cost_tier=CostTier.PREMIUM, meter_event_callback=lambda x: None)
    customer_id = "cus_test_premium"

    # Record 50000 events (well below 100000 limit)
    billing.record_meaningful_events(customer_id, 50000)

    invoice = await billing.get_upcoming_invoice(customer_id)

    assert invoice is not None
    assert invoice.amount_due == 199.0
    assert len(invoice.line_items) == 1
    assert invoice.line_items[0]["amount"] == 199.0


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_calculate_overage_free_tier())
    asyncio.run(test_calculate_overage_standard_tier())
    asyncio.run(test_no_overage_premium_tier())
