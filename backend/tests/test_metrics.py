"""
Tests for Prometheus metrics endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_metrics_endpoint_exists():
    """Test that /metrics endpoint exists and responds."""
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_content_type():
    """Test that metrics endpoint returns prometheus format."""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Prometheus metrics should be plain text
    assert "text/plain" in response.headers.get("content-type", "")


def test_metrics_contains_app_metrics():
    """Test that custom app metrics are present."""
    response = client.get("/metrics")
    content = response.text
    
    # Check for starlette exporter metrics
    assert "http_requests_total" in content or "starlette" in content.lower()


def test_metrics_contains_python_info():
    """Test that Python runtime metrics are present."""
    response = client.get("/metrics")
    content = response.text
    
    # Standard Python metrics
    assert "python_info" in content
    assert "process_" in content  # Process metrics
