# 🔮 ORACLE Telegram Bot - Real Webhook Setup Guide

> Complete implementation of Telegram Bot with real webhook support (no polling)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Local Testing](#local-testing)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)
8. [Commands Reference](#commands-reference)

---

## Overview

This guide covers the **real webhook implementation** for the ORACLE Telegram Bot. Unlike polling mode (which constantly asks Telegram for updates), webhooks are **event-driven** and much more efficient.

### Key Features ✨

- ✅ **Real webhook** - Event-driven, no polling overhead
- ✅ **Auto-response** - Messages replied to instantly
- ✅ **Database logging** - All interactions saved
- ✅ **Smart handlers** - Commands, messages, and edge cases
- ✅ **Production-ready** - Proper error handling & logging
- ✅ **Easy setup** - One command to configure

---

## Architecture

### Components

```
┌─────────────────────────────────────────┐
│     Telegram Bot (User Interface)        │
└────────────────┬────────────────────────┘
                 │
                 ↓ (Webhook HTTP POST)
         ┌───────────────────────┐
         │   FastAPI Server      │
         │  /webhook/telegram    │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────────────┐
         │                               │
         ↓                               ↓
    ┌──────────────┐          ┌──────────────────┐
    │ Telegram Bot │          │   PostgreSQL     │
    │   Handler    │          │   Database       │
    │  (telegram_  │          │                  │
    │   bot.py)    │          │  • Users         │
    └──────┬───────┘          │  • Messages      │
           │                  │  • System Logs   │
           ↓                  │  • Tasks         │
    ┌──────────────┐          └──────────────────┘
    │ AI Handler   │
    │  (Optional)  │
    └──────────────┘
```

### File Structure

```
oracle/
├── telegram_bot_setup.py       # Setup/config script ⭐ NEW
├── main.py                      # FastAPI app (updated)
├── core/
│   ├── telegram_bot.py         # Webhook handler ⭐ UPDATED
│   ├── config.py               # Config (unchanged)
│   ├── models.py               # DB models (unchanged)
│   ├── database.py             # DB setup (unchanged)
│   └── ...
└── TELEGRAM_WEBHOOK_SETUP.md   # This file ⭐ NEW
```

---

## Prerequisites

### 1. **Telegram Bot Token**

Create a bot with [@BotFather](https://t.me/botfather) on Telegram:

```
1. Message @BotFather
2. /newbot
3. Follow instructions
4. Copy the token: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```

### 2. **Python 3.9+**

```bash
python --version  # Should be 3.9 or higher
```

### 3. **Dependencies Installed**

```bash
cd /Users/clawdbot/clawd/oracle
pip install -r requirements.txt
```

### 4. **Environment Variables**

Update `.env` file:

```env
TELEGRAM_TOKEN=your_bot_token_here
ANTHROPIC_API_KEY=sk-ant-your-key-here
DATABASE_URL=postgresql://oracle:oracle_dev@localhost:5432/oracle
ENVIRONMENT=development
DEBUG=false
```

### 5. **Database Ready**

PostgreSQL must be running:

```bash
# Check if running
psql -l | grep oracle

# Or start if needed
brew services start postgresql
```

---

## Installation

### Step 1: Update Core Files

```bash
cd /Users/clawdbot/clawd/oracle

# The files are already in place:
# - telegram_bot_setup.py (NEW)
# - core/telegram_bot.py (UPDATED)
# - main.py (UPDATED)
```

### Step 2: Install/Update Requirements

```bash
# Install all dependencies
pip install -r requirements.txt

# Or update if needed
pip install --upgrade -r requirements.txt
```

### Step 3: Initialize Database

```bash
python -c "from core.database import init_db; init_db(); print('✅ Database initialized')"
```

---

## Local Testing

### Test 1: Start FastAPI Server

```bash
# Terminal 1: Start the server
python main.py

# Expected output:
# INFO:     Started server process [12345]
# INFO:     Uvicorn running on http://0.0.0.0:8000
# 🔮 ORACLE is now ONLINE
```

### Test 2: Check Health Endpoints

```bash
# Terminal 2: Check health
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "oracle": "online",
#   "telegram": "connected",
#   "ai_engine": "ready",
#   "database": "connected"
# }
```

### Test 3: Webhook Status (Polling Mode)

For local testing, you can check status without setting webhook:

```bash
# Check current webhook status
python telegram_bot_setup.py status

# Output shows whether webhook is active or in polling mode
```

### Test 4: Manual Message Processing (Simulation)

```bash
# Simulate a Telegram update
curl -X POST http://localhost:8000/webhook/telegram \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 123456,
    "message": {
      "message_id": 1,
      "date": 1234567890,
      "chat": {
        "id": 987654321,
        "type": "private",
        "username": "testuser"
      },
      "from": {
        "id": 987654321,
        "is_bot": false,
        "first_name": "Test",
        "username": "testuser"
      },
      "text": "/start"
    }
  }'

# Expected response:
# {"ok": true}

# Check database
psql oracle -c "SELECT * FROM messages LIMIT 5;"
```

### Test 5: Check Database Entries

```bash
# Connect to database
psql oracle

# See users registered
SELECT * FROM users;

# See messages logged
SELECT * FROM messages LIMIT 10;

# See system logs
SELECT * FROM system_logs LIMIT 10;
```

---

## Production Deployment

### Step 1: Get Public URL

Your FastAPI server needs a **public, HTTPS URL** accessible from Telegram servers.

Options:

#### Option A: Self-Hosted Server
```bash
# Server with public IP and domain
https://your-domain.com

# Make sure:
# - SSL/TLS certificate is valid
# - Port 443 (HTTPS) is open
# - Firewall allows Telegram IPs
```

#### Option B: Cloud Provider
- AWS EC2 + Route53
- DigitalOcean
- Heroku (deprecated but still works)
- Google Cloud Run
- Azure App Service

#### Option C: Ngrok (Development Only)
```bash
# Download ngrok: https://ngrok.com

# Start tunnel to local server
ngrok http 8000

# Get public URL (e.g., https://abc123.ngrok.io)
# ⚠️ This URL changes every time - not for production!
```

### Step 2: Deploy ORACLE

```bash
# 1. Upload files to server
scp -r /Users/clawdbot/clawd/oracle user@server:/app/oracle

# 2. Connect to server
ssh user@server

# 3. Install dependencies
cd /app/oracle
pip install -r requirements.txt

# 4. Update .env with production values
nano .env
# Set: ENVIRONMENT=production
# Set: DEBUG=false
# Set: DATABASE_URL=your_production_db

# 5. Initialize database
python -c "from core.database import init_db; init_db()"
```

### Step 3: Start Server with Systemd

Create `/etc/systemd/system/oracle.service`:

```ini
[Unit]
Description=ORACLE Telegram Bot
After=network.target postgresql.service

[Service]
Type=notify
User=oracle
WorkingDirectory=/app/oracle
Environment="PATH=/app/oracle/venv/bin"
ExecStart=/app/oracle/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=oracle

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable oracle
sudo systemctl start oracle
sudo systemctl status oracle
```

### Step 4: Setup Webhook

```bash
# Set webhook to your production URL
python telegram_bot_setup.py setup https://your-domain.com/webhook/telegram

# Expected output:
# ✅ Bot Connected
# ✅ Webhook Active
#    URL: https://your-domain.com/webhook/telegram
```

### Step 5: Verify Webhook

```bash
# Check webhook status
python telegram_bot_setup.py status

# Should show:
# ✅ Webhook Active
# Pending updates: 0
# Last error: None
```

### Step 6: Test End-to-End

1. Open Telegram
2. Find your bot (@your_bot_name)
3. Send `/start`
4. Bot responds with welcome message
5. Send `/help` to see commands
6. Check logs: `tail -f /var/log/syslog | grep oracle`

---

## Troubleshooting

### Webhook Not Receiving Updates

**Problem:** No messages are being received

**Solutions:**

```bash
# 1. Check webhook status
python telegram_bot_setup.py status

# 2. Verify URL is accessible
curl -I https://your-domain.com/webhook/telegram
# Should return 405 (POST required) or similar

# 3. Check firewall
sudo ufw allow 443  # HTTPS
sudo iptables -L | grep 443

# 4. Check SSL certificate
openssl s_client -connect your-domain.com:443

# 5. Re-register webhook
python telegram_bot_setup.py delete
python telegram_bot_setup.py setup https://your-domain.com/webhook/telegram

# 6. Check pending updates
python telegram_bot_setup.py status
# Look for "Pending updates" count
```

### Bot Not Responding

**Problem:** Bot receives message but doesn't reply

**Solutions:**

```bash
# 1. Check server is running
curl http://localhost:8000/health

# 2. Check logs
tail -f /var/log/syslog | grep oracle
# or if running locally:
# Check terminal output

# 3. Verify database connection
psql oracle -c "SELECT COUNT(*) FROM users;"

# 4. Check if message was saved
psql oracle -c "SELECT * FROM messages ORDER BY created_at DESC LIMIT 1;"

# 5. Restart service
sudo systemctl restart oracle
```

### Database Connection Error

**Problem:** `psycopg2.OperationalError: could not connect to server`

**Solutions:**

```bash
# 1. Check PostgreSQL is running
psql -l

# 2. Verify DATABASE_URL in .env
grep DATABASE_URL .env

# 3. Test connection
psql postgresql://oracle:oracle_dev@localhost:5432/oracle

# 4. Check credentials
# Default: user=oracle, pass=oracle_dev, db=oracle

# 5. If new database needed:
createuser oracle
createdb -O oracle oracle
# Then set password in postgres
psql -c "ALTER USER oracle WITH PASSWORD 'oracle_dev';"
```

### TELEGRAM_TOKEN Not Set

**Problem:** `ValueError: TELEGRAM_TOKEN not set in .env`

**Solutions:**

```bash
# 1. Verify .env file exists
ls -la .env

# 2. Check TELEGRAM_TOKEN is set
grep TELEGRAM_TOKEN .env

# 3. Token should look like: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# 4. Update .env if needed
echo "TELEGRAM_TOKEN=your_real_token" >> .env

# 5. Don't commit token to git!
# Add to .gitignore:
echo ".env" >> .gitignore
```

### SSL Certificate Error

**Problem:** `ssl.SSLError: certificate verify failed`

**Solutions:**

```bash
# 1. Verify certificate is valid
openssl x509 -in /path/to/cert -text -noout | grep -i "not"

# 2. Use Let's Encrypt (free)
sudo apt-get install certbot
sudo certbot certonly --standalone -d your-domain.com

# 3. Configure web server to use certificate
# For nginx:
server {
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
}

# 4. Renew certificate (automated with certbot)
sudo certbot renew --dry-run
```

---

## Commands Reference

### Setup Script

```bash
# Show status
python telegram_bot_setup.py status

# Setup webhook
python telegram_bot_setup.py setup https://your-domain.com/webhook/telegram

# Delete webhook (revert to polling)
python telegram_bot_setup.py delete

# Keep existing webhook when setting new one
python telegram_bot_setup.py setup https://your-domain.com/webhook/telegram --keep-existing
```

### Telegram Bot Commands

Users can send these commands to the bot:

```
/start       - Welcome & intro
/help        - Full command list
/status      - System status
/alpha [desc] - Log alpha discovery
/pause       - Pause automation
/resume      - Resume automation
```

### API Endpoints

```bash
# Health checks
GET  /                    # Basic health
GET  /health             # Detailed health
GET  /status             # System status

# Webhook
POST /webhook/telegram   # ⭐ Main webhook endpoint

# Database queries
GET  /api/users          # List users
GET  /api/messages       # List messages
GET  /api/logs           # List logs

# Admin
GET  /api/ai-handler/stats
POST /api/process-messages
GET  /config             # (debug only)
```

---

## Deployment Checklist

- [ ] Telegram bot created with @BotFather
- [ ] Token stored in `.env` (not committed to git)
- [ ] PostgreSQL database created and running
- [ ] All requirements installed
- [ ] Local tests pass (`/health` endpoint works)
- [ ] Public HTTPS URL obtained
- [ ] SSL certificate is valid
- [ ] Firewall allows port 443
- [ ] Server deployed with `main.py` running
- [ ] Webhook configured: `python telegram_bot_setup.py setup <url>`
- [ ] Webhook verified as active
- [ ] Test message from @BotFather received
- [ ] Logs show successful message processing

---

## Performance Considerations

### Webhook Efficiency

| Metric | Polling | Webhook |
|--------|---------|---------|
| Updates/sec | Check every 30s | Instant delivery |
| Response time | 30+ seconds | <1 second |
| CPU usage | Continuous polling | Event-driven |
| Network bandwidth | High | Low |
| Server load | High (✗) | Low (✓) |

### Scaling

For high volume (>100 msg/sec):

1. **Add message queue** (Redis/RabbitMQ)
2. **Process messages async** (Celery workers)
3. **Database connection pooling** (PgBouncer)
4. **Load balancer** (nginx)
5. **Multiple ORACLE instances**

Example with Celery:

```python
# In telegram_bot.py
from celery import Celery

celery_app = Celery('oracle')

@celery_app.task
def process_message_async(message_id):
    # Process in background
    handler.process_update(...)
```

---

## Logging & Monitoring

### Database Logs

```sql
-- See all interactions
SELECT timestamp, level, component, message 
FROM system_logs 
ORDER BY timestamp DESC 
LIMIT 50;

-- Count by component
SELECT component, COUNT(*) 
FROM system_logs 
GROUP BY component;

-- Error logs only
SELECT * FROM system_logs 
WHERE level = 'ERROR' 
ORDER BY timestamp DESC;
```

### System Logs (File/Journalctl)

```bash
# If running with systemd
sudo journalctl -u oracle -f
sudo journalctl -u oracle --since "1 hour ago"

# Or tail main.py output if running directly
tail -f oracle.log
```

---

## Support & Help

### Resources

- **Telegram Bot API**: https://core.telegram.org/bots/api
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **PostgreSQL**: https://www.postgresql.org/docs

### Getting Help

```bash
# Check ORACLE status
curl http://localhost:8000/status | jq

# View recent logs
tail -100 /var/log/syslog | grep oracle

# Test webhook endpoint
curl -X POST http://localhost:8000/webhook/telegram \
  -H "Content-Type: application/json" \
  -d '{"update_id": 1, "message": {"text": "test"}}'

# Debug mode (show more details)
DEBUG=true python main.py
```

---

## Summary

✅ **Webhook Implementation Complete**

- Real webhook (not polling)
- Auto-response via Telegram Bot API
- Full database logging
- All commands working
- Production-ready

**To Deploy:**

```bash
# 1. Get public HTTPS URL
# 2. Update DATABASE_URL and TELEGRAM_TOKEN in .env
# 3. Start server: python main.py
# 4. Setup webhook: python telegram_bot_setup.py setup <url>
# 5. Test: Send /start to bot
# Done! 🚀
```

---

**Last Updated:** 2025-02-03
**Status:** ✅ Production Ready
**Tested On:** macOS 13+, Python 3.9+, PostgreSQL 12+
