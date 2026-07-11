from app.alerts.routing import get_routing
from app.models.models import AlertCategory


def test_cash_liquidity_routes_to_field_officer():
    routing = get_routing(AlertCategory.LIQUIDITY, None, None)
    assert routing["role"] == "Field Officer"
    assert "Field Officer" in routing["owner"]


def test_provider_liquidity_routes_to_field_officer():
    routing = get_routing(AlertCategory.LIQUIDITY, "bkash", "bKash")
    assert routing["role"] == "Field Officer"
    assert routing["owner_role"] == "field_officer"
    assert "bKash" in routing["action"]


def test_anomaly_routes_with_escalation_language():
    routing = get_routing(AlertCategory.ANOMALY, "nagad", "Nagad")
    assert routing["role"] == "Provider Operations"
    assert "Risk/Compliance" in routing["action"]
    assert routing["owner_role"] == "provider_ops"


def test_data_quality_routes_to_provider_operations():
    routing = get_routing(AlertCategory.DATA_QUALITY, "rocket", "Rocket")
    assert routing["role"] == "Provider Operations"
    assert "Rocket" in routing["owner"]


def test_provider_routing_never_crosses_providers():
    bkash_routing = get_routing(AlertCategory.LIQUIDITY, "bkash", "bKash")
    nagad_routing = get_routing(AlertCategory.LIQUIDITY, "nagad", "Nagad")
    assert bkash_routing["owner"] != nagad_routing["owner"]
    assert "Nagad" not in bkash_routing["owner"]
