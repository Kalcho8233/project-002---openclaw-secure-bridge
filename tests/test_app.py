import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("API_KEY", "test-secret")
    monkeypatch.setenv("NOTIFY_TARGET", "+359877656763")
    monkeypatch.setenv("NOTIFY_QUEUE_DIR", str(tmp_path / "notify-queue"))

    from app.config import get_settings
    from app.main import app

    get_settings.cache_clear()
    yield TestClient(app)
    get_settings.cache_clear()


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


def test_notify_sends_message_via_openclaw(client, monkeypatch):
    def fake_send(message: str):
        assert message == "Bridge says hi"
        return {
            "delivery": "sent",
            "target": "+359877656763",
            "transport": "openclaw-cli",
        }

    monkeypatch.setattr("app.main.send_notification", fake_send)

    response = client.post(
        "/api/notify",
        headers={"X-API-Key": "test-secret"},
        json={"message": "Bridge says hi"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "accepted": True,
        "delivery": "sent",
        "target": "+359877656763",
        "transport": "openclaw-cli",
    }


def test_notify_queues_message_when_delivery_is_unavailable(client, monkeypatch, tmp_path):
    queue_dir = tmp_path / "notify-queue"

    def fake_send(message: str):
        from app.notify import NotificationQueueResult

        return NotificationQueueResult(
            queue_id="queued-123",
            queue_path=queue_dir / "queued-123.json",
            reason="openclaw unavailable",
        )

    monkeypatch.setattr("app.main.send_notification", fake_send)

    response = client.post(
        "/api/notify",
        headers={"X-API-Key": "test-secret"},
        json={"message": "Queue this message"},
    )

    assert response.status_code == 202
    assert response.json() == {
        "accepted": True,
        "delivery": "queued",
        "queue_id": "queued-123",
        "queue_path": str(queue_dir / "queued-123.json"),
        "reason": "openclaw unavailable",
    }


def test_notify_rejects_blank_message(client):
    response = client.post(
        "/api/notify",
        headers={"X-API-Key": "test-secret"},
        json={"message": "   "},
    )

    assert response.status_code == 422
