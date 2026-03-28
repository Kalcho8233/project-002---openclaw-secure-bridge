from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings, get_settings


@dataclass(frozen=True)
class NotificationQueueResult:
    queue_id: str
    queue_path: Path
    reason: str


@dataclass(frozen=True)
class NotificationSentResult:
    target: str
    transport: str = "openclaw-cli"
    delivery: str = "sent"


def enqueue_notification(message: str, reason: str, settings: Settings | None = None) -> NotificationQueueResult:
    settings = settings or get_settings()
    queue_id = uuid.uuid4().hex
    queue_dir = Path(settings.notify_queue_dir)
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_path = queue_dir / f"{queue_id}.json"
    queue_path.write_text(
        json.dumps({"target": settings.notify_target, "message": message}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return NotificationQueueResult(queue_id=queue_id, queue_path=queue_path, reason=reason)


def send_notification(message: str, settings: Settings | None = None):
    settings = settings or get_settings()
    openclaw_path = shutil.which(settings.openclaw_command)
    if not openclaw_path:
        return enqueue_notification(message, reason="openclaw command unavailable", settings=settings)

    command = [
        openclaw_path,
        "message",
        "send",
        "--target",
        settings.notify_target,
        "--message",
        message,
        "--json",
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=settings.notify_timeout_seconds,
        check=False,
    )

    if completed.returncode != 0:
        reason = completed.stderr.strip() or completed.stdout.strip() or "openclaw send failed"
        return enqueue_notification(message, reason=reason, settings=settings)

    return NotificationSentResult(target=settings.notify_target)
