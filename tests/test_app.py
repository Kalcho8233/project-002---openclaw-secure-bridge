import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-secret")

    from app.main import app

    return TestClient(app)


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_webhook_accepts_valid_request_with_api_key(client):
    response = client.post(
        "/api/webhook",
        headers={"X-API-Key": "test-secret"},
        json={"source": "openclaw", "payload": {"message": "ping"}},
    )

    assert response.status_code == 200
    assert response.json() == {"accepted": True, "source": "openclaw"}


def test_webhook_rejects_missing_api_key(client):
    response = client.post(
        "/api/webhook",
        json={"source": "openclaw", "payload": {"message": "ping"}},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_webhook_rejects_invalid_api_key(client):
    response = client.post(
        "/api/webhook",
        headers={"X-API-Key": "wrong-key"},
        json={"source": "openclaw", "payload": {"message": "ping"}},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_webhook_rejects_invalid_body(client):
    response = client.post(
        "/api/webhook",
        headers={"X-API-Key": "test-secret"},
        json={"source": "openclaw", "payload": "not-an-object"},
    )

    assert response.status_code == 422
