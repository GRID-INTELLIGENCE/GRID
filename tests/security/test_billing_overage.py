import pytest
from unittest.mock import MagicMock
from application.mothership.services.billing_service import (
    BillingService,
    SubscriptionTier,
    OverageCharges,
)


@pytest.fixture
def billing_service():
    """Create a billing service with mock settings for testing."""
    mock_settings = MagicMock()
    # Mock settings with small limits for easy testing
    mock_settings.free_tier_relationship_analyses = 10
    mock_settings.free_tier_entity_extractions = 50
    mock_settings.starter_tier_relationship_analyses = 100
    mock_settings.starter_tier_entity_extractions = 1000
    
    # Pricing
    mock_settings.starter_monthly_price = 5000
    mock_settings.relationship_analysis_overage_cents = 10
    mock_settings.entity_extraction_overage_cents = 5
    mock_settings.billing_cycle_days = 30
    
    return BillingService(settings=mock_settings)


class TestOverageCalculation:
    """Test overage calculation logic."""

    def test_no_overage_within_limits(self, billing_service):
        """Test no charges when within tier limits."""
        charges = billing_service.calculate_overage(
            tier=SubscriptionTier.STARTER,
            relationship_analysis_usage=10,
            entity_extraction_usage=50,
        )
        
        assert charges.relationship_analysis_count == 0
        assert charges.entity_extraction_count == 0
        assert charges.total_overage_cents == 0

    def test_overage_relationship_analysis(self, billing_service):
        """Test overage calculation for relationship analyses."""
        # Free tier has 10 relationship analyses
        charges = billing_service.calculate_overage(
            tier=SubscriptionTier.FREE,
            relationship_analysis_usage=15,  # 5 over limit
            entity_extraction_usage=0,
        )
        
        assert charges.relationship_analysis_count == 5
        assert charges.relationship_analysis_cost_cents > 0

    def test_overage_entity_extraction(self, billing_service):
        """Test overage calculation for entity extractions."""
        # Free tier has 50 entity extractions
        charges = billing_service.calculate_overage(
            tier=SubscriptionTier.FREE,
            relationship_analysis_usage=0,
            entity_extraction_usage=75,  # 25 over limit
        )
        
        assert charges.entity_extraction_count == 25
        assert charges.entity_extraction_cost_cents > 0

    def test_combined_overage(self, billing_service):
        """Test combined overage for both resource types."""
        charges = billing_service.calculate_overage(
            tier=SubscriptionTier.FREE,
            relationship_analysis_usage=20,
            entity_extraction_usage=100,
        )
        
        assert charges.relationship_analysis_count > 0
        assert charges.entity_extraction_count > 0
        assert charges.total_overage_cents == (
            charges.relationship_analysis_cost_cents + charges.entity_extraction_cost_cents
        )
        assert charges.total_overage_dollars == charges.total_overage_cents / 100


class TestBillingSummary:
    """Test billing summary generation."""

    @pytest.mark.asyncio
    async def test_billing_summary_generation(self, billing_service):
        """Test generating a billing summary."""
        user_id = "test-user-billing"
        
        # Record some usage
        await billing_service.record_usage(user_id, "relationship_analysis", 5)
        await billing_service.record_usage(user_id, "entity_extraction", 20)
        
        summary = await billing_service.get_billing_summary(user_id, SubscriptionTier.STARTER)
        
        assert summary.tier == SubscriptionTier.STARTER
        assert summary.usage["relationship_analyses"] == 5
        assert summary.usage["entity_extractions"] == 20

    @pytest.mark.asyncio
    async def test_limit_exceeded_check(self, billing_service):
        """Test checking if limit is exceeded."""
        user_id = "limit-test-user"
        
        # Record usage near limit
        await billing_service.record_usage(user_id, "relationship_analysis", 10)
        
        exceeded, current, limit = await billing_service.check_limit_exceeded(
            user_id, SubscriptionTier.FREE, "relationship_analysis"
        )
        
        assert current == 10
        # Free tier limit is 10, so should be at limit
        assert exceeded is True
