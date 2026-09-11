from app.modules.platform.subscriptions.service import SubscriptionService


def test_subscription_period_days_cover_all_billing_cycles():
    assert SubscriptionService._period_days("monthly") == 30
    assert SubscriptionService._period_days("quarterly") == 90
    assert SubscriptionService._period_days("semi_annual") == 182
    assert SubscriptionService._period_days("yearly") == 365
