from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.config import Settings, get_settings

app = FastAPI(title="OpenClaw Secure Bridge")


class WebhookRequest(BaseModel):
    source: str
    payload: dict


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
