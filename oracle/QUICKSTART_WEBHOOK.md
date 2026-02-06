# 🚀 ORACLE Telegram Bot - Webhook Quick Start

> Get ORACLE running with real Telegram webhook in 5 minutes

---

## ⚡ 5-Minute Setup

### Step 1: Prerequisites (2 min)

```bash
# Clone repo
cd /Users/clawdbot/clawd/oracle

# Install dependencies
pip install -r requirements.txt

# Copy and edit .env
cp .env.example .env
# Edit .env and add:
# - TELEGRAM_TOKEN (from @BotFather)
# - DATABASE_URL (your PostgreSQL)
```

### Step 2: Start Server (1 min)

```bash
# Initialize database
python3 -c "from core.database import init_db; init_db(); print('✅ DB ready')"

# Start FastAPI server
python3 main.py

# Expected output:
# INFO:     Started server process
# 🔮 ORACLE is now ONLINE
# 📡 Webhook mode: Ready to receive updates
```

### Step 3: Configure Webhook (1 min)

```bash
# In new terminal:
python3 telegram_bot_setup.py setup https://your-domain.com/webhook/telegram

# Expected output:
# ✅ Connected to bot
# ✅ Webhook set to: https://your-domain.com/webhook/telegram
# ✅ Webhook verified successfully!
```

### Step 4: Test (1 min)

```bash
# Test with local simulation
python3 test_webhook.py

# Or send /start to bot on Telegram
# Expected: Instant response ✨
```

---

## 📊 Local Testing Without Real Bot

```bash
# Simulate webhook (no Telegram account needed)
python3 test_webhook.py

# Output:
# 🧪 Testing ORACLE Telegram Webhook Handler
# 
# 📝 Test 1: /start command
# Result: start - True
# Response: 🔮 Welcome to ORACLE...
# 
# ✅ All tests completed!
```

---

## 🔧 Core Commands

```bash
# Check webhook status
python3 telegram_bot_setup.py status

# Delete webhook (revert to polling)
python3 telegram_bot_setup.py delete

# View health
curl http://localhost:8000/health | jq

# Check users in database
psql oracle -c "SELECT * FROM users;"
```

---

## 🐛 Troubleshooting

### "TELEGRAM_TOKEN not set"

```bash
# Check .env
grep TELEGRAM_TOKEN .env

# Should show: TELEGRAM_TOKEN=123456:ABC-DEF...
# If not, edit .env and add real token from @BotFather
```

### "Cannot connect to bot"

```bash
# Verify token is correct
# Get real token from @BotFather on Telegram
# Set in .env: TELEGRAM_TOKEN=your_real_token

# Test connection
curl https://api.telegram.org/bot[YOUR_TOKEN]/getMe
```

### "Database connection error"

```bash
# Check PostgreSQL is running
psql -l | grep oracle

# If not, start PostgreSQL
brew services start postgresql

# Initialize database
python3 -c "from core.database import init_db; init_db()"
```

### "Webhook URL not accessible"

```bash
# Your domain must be:
# ✅ Public (accessible from internet)
# ✅ HTTPS (not HTTP)
# ✅ Valid SSL certificate
# ✅ Port 443 open

# Test accessibility
curl -I https://your-domain.com/webhook/telegram
# Should return 405 Method Not Allowed (that's OK, POST is required)
```

---

## 📋 Deployment Checklist

- [ ] Token from @BotFather
- [ ] .env file configured
- [ ] PostgreSQL running
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database initialized
- [ ] FastAPI server running (`python3 main.py`)
- [ ] Public HTTPS URL ready
- [ ] Webhook setup: `python3 telegram_bot_setup.py setup <url>`
- [ ] Status check: `python3 telegram_bot_setup.py status`
- [ ] Send /start to bot on Telegram
- [ ] ✅ Live! 🎉

---

## 📁 What Was Added

```
oracle/
├── telegram_bot_setup.py          # ⭐ Setup script
├── test_webhook.py                 # ⭐ Test suite
├── TELEGRAM_WEBHOOK_SETUP.md       # Complete guide
├── TELEGRAM_WEBHOOK_IMPLEMENTATION_REPORT.md  # Full report
├── QUICKSTART_WEBHOOK.md           # This file
│
└── core/
    └── telegram_bot.py             # ⭐ Updated webhook handler
```

---

## 🎯 What Works Now

✅ `/start` - Welcome message
✅ `/help` - Command list
✅ `/status` - System status
✅ `/alpha [desc]` - Log alpha
✅ `/pause` - Pause automation
✅ `/resume` - Resume automation
✅ Regular messages - Message processing
✅ Database logging - All interactions saved
✅ Instant responses - <1 second delivery

---

## 🔗 Quick Links

- **Setup Guide:** [TELEGRAM_WEBHOOK_SETUP.md](./TELEGRAM_WEBHOOK_SETUP.md)
- **Full Report:** [TELEGRAM_WEBHOOK_IMPLEMENTATION_REPORT.md](./TELEGRAM_WEBHOOK_IMPLEMENTATION_REPORT.md)
- **Test Script:** `python3 test_webhook.py`
- **Telegram Bot API:** https://core.telegram.org/bots/api

---

## 💡 Tips

### Development

```bash
# Run with debug logging
DEBUG=true python3 main.py

# Watch logs
tail -f oracle.log

# Check recent messages
psql oracle -c "SELECT * FROM messages ORDER BY created_at DESC LIMIT 10;"
```

### Production

```bash
# Keep server running with systemd
sudo systemctl start oracle
sudo systemctl status oracle

# Monitor with journalctl
sudo journalctl -u oracle -f

# Check webhook status regularly
python3 telegram_bot_setup.py status
```

---

## ❓ FAQ

**Q: Do I need Telegram Desktop?**
A: No, the bot works with any Telegram client (mobile, web, etc.)

**Q: Can I test without real bot?**
A: Yes! Use `python3 test_webhook.py` for local testing

**Q: What if webhook URL changes?**
A: Re-run setup script: `python3 telegram_bot_setup.py setup <new_url>`

**Q: How do I see all interactions?**
A: `psql oracle -c "SELECT * FROM system_logs;"`

**Q: What if bot stops responding?**
A: Check: logs, database connection, webhook status

---

## 📞 Need Help?

```bash
# Check system health
curl http://localhost:8000/health | jq

# View all logs
tail -100 oracle.log

# Test webhook endpoint
curl -X POST http://localhost:8000/webhook/telegram \
  -H "Content-Type: application/json" \
  -d '{"update_id":1,"message":{"text":"/help","from":{"id":123,"first_name":"Test"}}}'
```

---

**Ready to deploy?** Follow the steps above and you'll have ORACLE running with real Telegram webhook in ~5 minutes! 🚀

For detailed information, see [TELEGRAM_WEBHOOK_SETUP.md](./TELEGRAM_WEBHOOK_SETUP.md)
