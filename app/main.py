from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, StringConstraints

from app.config import Settings, get_settings
from app.notify import NotificationQueueResult, NotificationSentResult, send_notification

app = FastAPI(title="OpenClaw Secure Bridge")


class WebhookRequest(BaseModel):
    source: str
    payload: dict


class NotifyRequest(BaseModel):
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/webhook")
def webhook(
    body: WebhookRequest,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> dict[str, str | bool]:
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {"accepted": True, "source": body.source}


@app.post("/api/notify")
def notify(
    body: NotifyRequest,
    response: Response,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> dict[str, str | bool]:
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = send_notification(body.message)

    if isinstance(result, NotificationQueueResult):
        response.status_code = 202
        return {
            "accepted": True,
            "delivery": "queued",
            "queue_id": result.queue_id,
            "queue_path": str(result.queue_path),
            "reason": result.reason,
        }

    if isinstance(result, NotificationSentResult):
        return {
            "accepted": True,
            "delivery": result.delivery,
            "target": result.target,
            "transport": result.transport,
        }

    if isinstance(result, dict):
        return {"accepted": True, **result}

    return {"accepted": True, "delivery": "unknown"}
