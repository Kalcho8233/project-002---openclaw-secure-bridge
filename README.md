# OpenClaw Secure Bridge

Minimal FastAPI backend for OpenClaw/MCP-style integrations where you want a small authenticated webhook layer without n8n.

## Features

- `GET /health` → `{"status": "ok"}`
- `POST /api/webhook` with `X-API-Key` header
- Validates body shape: `{"source": "string", "payload": {}}`
- Rejects missing/invalid API keys with `401 Unauthorized`
- Keeps secrets out of git via `.env` + `.gitignore`

## Project layout

- `app/main.py` — FastAPI app and routes
- `app/config.py` — environment-backed settings
- `tests/test_app.py` — pytest coverage for health/auth/validation
- `.env.example` — safe example config

## Requirements

- Python 3.12+
- `pip`

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
PORT=8000
```

## Run locally

```bash
cd /root/Coding_Projects/Test_Projects/openclaw-secure-bridge
export $(grep -v '^#' .env | xargs)
uvicorn app.main:app --host "$HOST" --port "$PORT"
```

Or explicitly:

```bash
API_KEY='your-secret' uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Test

```bash
cd /root/Coding_Projects/Test_Projects/openclaw-secure-bridge
pytest -q
```

## Example request

```bash
curl -X POST http://127.0.0.1:8000/api/webhook \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-secret' \
  -d '{"source":"openclaw","payload":{"event":"ping"}}'
```

Expected response:

```json
{"accepted":true,"source":"openclaw"}
```

## Production deployment notes

### systemd service

Example unit file:

```ini
[Unit]
Description=OpenClaw Secure Bridge
After=network.target

[Service]
User=root
WorkingDirectory=/root/Coding_Projects/Test_Projects/openclaw-secure-bridge
EnvironmentFile=/root/Coding_Projects/Test_Projects/openclaw-secure-bridge/.env
ExecStart=/usr/local/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

If `uvicorn` resolves elsewhere on your machine, replace `/usr/local/bin/uvicorn` with `which uvicorn`.

### Caddy reverse proxy

Example Caddyfile snippet:

```caddy
bridge.example.com {
    reverse_proxy 127.0.0.1:8000
    encode gzip
    header {
        -Server
    }
}
```

### Hardening suggestions

- Bind Uvicorn to `127.0.0.1` and expose it only through Caddy.
- Generate a strong `API_KEY` and keep it only in `.env` or your secret manager.
- Terminate TLS at Caddy.
- Consider request logging and IP allowlisting if the caller set is small.
- Run under a dedicated service user instead of `root` in production.

## Notes

This service intentionally keeps logic minimal so it can act as a safe bridge layer before downstream automation or tool execution.
