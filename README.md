# OpenClaw Secure Bridge

Minimal FastAPI backend for OpenClaw/MCP-style integrations where you want a small authenticated webhook layer without n8n.

## Features

- `GET /health` → `{"status": "ok"}`
- `POST /api/webhook` with `X-API-Key`
- `POST /api/notify` with `X-API-Key`
- Validates request bodies before accepting them
- Sends WhatsApp notifications through the local `openclaw` CLI when available
- Falls back to a safe local queue when direct delivery is unavailable
- Keeps secrets out of git via `.env` + `.gitignore`

## Project layout

- `app/main.py` — FastAPI app and routes
- `app/config.py` — environment-backed settings
- `app/notify.py` — OpenClaw CLI delivery + queue fallback
- `tests/test_app.py` — pytest coverage for health/auth/validation/notify behavior
- `deploy/openclaw-secure-bridge.service` — systemd unit template used in production
- `.env.example` — safe example config

## Requirements

- Python 3.12+
- `pip`
- `openclaw` CLI available on the host if you want direct message delivery

## Install

```bash
cd /root/Coding_Projects/Test_Projects/openclaw-secure-bridge
python3 -m pip install --break-system-packages -r requirements.txt
cp .env.example .env
```

Edit `.env` and set a real secret:

```env
API_KEY=use-a-long-random-secret
HOST=127.0.0.1
PORT=18080
NOTIFY_TARGET=+359877656763
NOTIFY_QUEUE_DIR=./var/notify-queue
NOTIFY_TIMEOUT_SECONDS=15
OPENCLAW_COMMAND=openclaw
```

## Run locally

```bash
cd /root/Coding_Projects/Test_Projects/openclaw-secure-bridge
export $(grep -v '^#' .env | xargs)
python3 -m uvicorn app.main:app --host "$HOST" --port "$PORT"
```

## Test

```bash
cd /root/Coding_Projects/Test_Projects/openclaw-secure-bridge
pytest -q
```

## Endpoints

### `GET /health`

Returns:

```json
{"status":"ok"}
```

### `POST /api/webhook`

```bash
curl -X POST http://127.0.0.1:18080/api/webhook \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-secret' \
  -d '{"source":"openclaw","payload":{"event":"ping"}}'
```

Expected response:

```json
{"accepted":true,"source":"openclaw"}
```

### `POST /api/notify`

```bash
curl -X POST http://127.0.0.1:18080/api/notify \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-secret' \
  -d '{"message":"Bridge says hi"}'
```

Direct-send success response:

```json
{"accepted":true,"delivery":"sent","target":"+359877656763","transport":"openclaw-cli"}
```

Queue fallback response:

```json
{
  "accepted": true,
  "delivery": "queued",
  "queue_id": "...",
  "queue_path": "./var/notify-queue/<id>.json",
  "reason": "openclaw command unavailable"
}
```

Queued file payload:

```json
{"target":"+359877656763","message":"Bridge says hi"}
```

## Production deployment notes

### systemd service

The repo includes a ready unit file at `deploy/openclaw-secure-bridge.service`.

Install it with:

```bash
sudo cp deploy/openclaw-secure-bridge.service /etc/systemd/system/openclaw-secure-bridge.service
sudo systemctl daemon-reload
sudo systemctl enable --now openclaw-secure-bridge.service
```

### Caddy reverse proxy

Caddy is **not installed** on this VPS right now.

If you install it later, use a site block like:

```caddy
bridge.example.com {
    reverse_proxy 127.0.0.1:18080
    encode gzip
    header {
        -Server
    }
}
```

### Hardening suggestions

- Keep Uvicorn bound to `127.0.0.1` and expose it only through a reverse proxy if remote access is needed.
- Generate a strong `API_KEY` and store it only in `.env` or a secret manager.
- The direct notify path depends on a local OpenClaw channel that can actually deliver WhatsApp messages.
- If local delivery is unavailable, monitor `var/notify-queue/` and process queued notifications with a trusted local worker.

## Notes

This service intentionally keeps logic minimal so it can act as a safe bridge layer before downstream automation or tool execution.
