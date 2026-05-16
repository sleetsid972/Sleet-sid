# HEXAAxCHKR — Production Deployment Guide

## Architecture

```
┌──────────────┐     HTTP     ┌───────────────────────┐
│  Telegram    │◄────────────►│  bot.py  (Bot Machine) │
│  User        │              │  Telethon + SQLite      │
└──────────────┘              └──────────┬──────────────┘
                                         │ round-robin
                              ┌──────────▼──────────────┐
                              │   Health-aware LB        │
                              └──┬───────┬──────────┬───┘
                                 │       │          │
                           ┌─────▼──┐ ┌──▼─────┐ ┌─▼──────┐
                           │ VPS1   │ │ VPS2   │ │ VPS3   │
                           │ api.py │ │ api.py │ │ api.py │
                           │ :5000  │ │ :5000  │ │ :5000  │
                           └────────┘ └────────┘ └────────┘
```

## Files

| File | Purpose |
|------|---------|
| `api.py` | Quart async checkout API (deploy on each VPS) |
| `queries.py` | GraphQL query strings (imported by api.py) |
| `bot.py` | Telegram bot (deploy on Bot Machine) |
| `docker-compose.yml` | Docker config for VPS API deployment |
| `Dockerfile.api` | Docker image for the API |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

---

## 1. API Setup (repeat on each VPS)

### Option A — Docker (recommended)

```bash
# Clone / upload api.py, queries.py, docker-compose.yml, Dockerfile.api
cd /opt/checker-api

docker compose up -d

# Verify
curl http://localhost:5000/health
# {"status":"ok"}
```

### Option B — Direct Python

```bash
pip install quart hypercorn "curl_cffi>=0.7.0" aiohttp python-dotenv
python3 api.py
```

The API listens on `0.0.0.0:5000`. Open the port in your VPS firewall:

```bash
# UFW
ufw allow 5000/tcp
```

---

## 2. Bot Setup (Bot Machine)

### Install dependencies

```bash
pip install telethon aiofiles aiosqlite python-dotenv aiohttp
```

### Configure environment variables

```bash
cp .env.example .env
nano .env   # fill in real values
```

Required variables:

| Variable | Description |
|----------|-------------|
| `API_ID` | Telegram API ID (my.telegram.org) |
| `API_HASH` | Telegram API hash |
| `BOT_TOKEN` | Bot token from @BotFather |
| `ADMIN_IDS` | Comma-separated Telegram user IDs for admins |
| `PVT_CHANNEL_ID` | Negative integer ID of the private logs channel |
| `API_ENDPOINTS` | Comma-separated base URLs of the VPS APIs |
| `DB_FILE` | Path for SQLite credits database (default: `bot_data.db`) |

Example `.env`:

```dotenv
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
BOT_TOKEN=8200036561:AAGd...
ADMIN_IDS=7845916818
PVT_CHANNEL_ID=-1003866637848
API_ENDPOINTS=http://11.22.33.44:5000,http://55.66.77.88:5000,http://99.100.101.102:5000
DB_FILE=bot_data.db
```

### Run the bot

```bash
python3 bot.py
```

Or as a systemd service:

```ini
# /etc/systemd/system/hexabot.service
[Unit]
Description=HEXAAxCHKR Telegram Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/hexabot
EnvironmentFile=/opt/hexabot/.env
ExecStart=/usr/bin/python3 bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now hexabot
```

---

## 3. Proxy format

Proxies are stored in `proxy.txt` (one per line) in any of these formats:

```
ip:port
ip:port:username:password
http://username:password@ip:port
socks5://username:password@ip:port
```

---

## 4. API response format

The API always returns one of three outcomes:

| Status | Response | Meaning |
|--------|----------|---------|
| `true` | `"Charged"` | Card was successfully charged |
| `true` | `"Approved"` | Card is live (3DS, insufficient funds, etc.) |
| `false` | `"Dead"` | Card declined or site error |

Full response:

```json
{
  "Gateway": "Shopify Payments",
  "Price": 29.99,
  "Response": "Approved",
  "Status": true,
  "cc": "4111111111111111|01|2028|123"
}
```

---

## 5. Health check

Each VPS exposes `GET /health` → `{"status":"ok"}`.

The bot pings all endpoints every 30 seconds and automatically excludes unhealthy ones from rotation.

---

## 6. Migrating existing credits

If you were previously using `credits.json`, run this once on the Bot Machine to import credits into SQLite:

```python
import json, sqlite3, os

credits = json.load(open('credits.json'))
conn = sqlite3.connect('bot_data.db')
conn.execute('CREATE TABLE IF NOT EXISTS credits (user_id TEXT PRIMARY KEY, amount INTEGER NOT NULL DEFAULT 0)')
for uid, amount in credits.items():
    conn.execute('INSERT OR REPLACE INTO credits VALUES (?,?)', (uid, int(amount)))
conn.commit()
conn.close()
print(f"Migrated {len(credits)} users")
```
