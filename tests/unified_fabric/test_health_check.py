"""
Tests for Unified Fabric - Health Checks
"""
from unified_fabric.health_check import get_health_status

def test_get_health_status():
    status = get_health_status()
    
    assert "status" in status
    assert "event_bus" in status
    assert "safety_bridge" in status
    assert "audit_logger" in status
    
    # Audit logger should have baseline fields
    audit = status["audit_logger"]
    assert "log_dir" in audit
    assert "buffer_size" in audit
    assert "buffered_entries" in audit

    # Overall status should be string
    assert isinstance(status["status"], str)
