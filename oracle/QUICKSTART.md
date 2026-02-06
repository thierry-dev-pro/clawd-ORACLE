# ⚡ ORACLE Quick Start (5 min)

## Local Development (Fastest)

### 1. Clone & Setup (2 min)
```bash
cd oracle
cp .env.example .env

# Edit .env with your tokens:
# - TELEGRAM_TOKEN (from @BotFather)
# - ANTHROPIC_API_KEY (from Anthropic console)
```

### 2. Start Services (1 min)
```bash
# PostgreSQL + Redis
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 3. Install & Run (1 min)
```bash
pip install -r requirements.txt
python main.py
```

### 4. Test Bot (1 min)
Open Telegram → send to your bot:
```
/status
```

Should get: `✅ ORACLE Status` with system info.

## Railway Deployment (Fastest to Production)

### 1. Push to GitHub (1 min)
```bash
git add .
git commit -m "Init ORACLE"
git push origin main
```

### 2. Create Railway Project (2 min)
- Go to railway.app
- "Create" → "Deploy from GitHub"
- Select `oracle` repo
- Railway auto-detects Python app

### 3. Add Services (2 min)
- Add PostgreSQL database
- Add Redis cache
- Set environment variables (see DEPLOYMENT.md)

### 4. Deploy (3 min)
- Railway auto-builds and deploys
- Check dashboard → Deployments tab
- Should be green ✅

### 5. Get Domain (1 min)
- Railway dashboard → Networking
- Copy domain (e.g., `oracle-prod.railway.app`)

### 6. Test
```bash
curl https://oracle-prod.railway.app/health
```

## Telegram Bot Commands

After setup, your bot responds to:

```
/start      → Introduction
/status     → System status
/post       → Generate & post content
/alpha      → Alpha discovery workflow
/email      → Email summary
/report     → Daily/weekly reports
/help       → Command list
```

## Troubleshooting

**Bot not responding?**
```bash
# Check TELEGRAM_TOKEN in .env
# Verify bot is online: @BotFather → /mybots
```

**API errors?**
```bash
# Check logs
docker-compose logs -f  # Local
railway logs            # Railway
```

**Database connection failed?**
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

## Next: Week 2

After local/production setup works:
- ✅ API responding → /health returns 200
- ✅ Bot responding → /status works
- ✅ DB connected → no connection errors

**Ready to add:**
1. Twitter scraper (Nitter)
2. Notion integration
3. Email automation

👉 See DEPLOYMENT.md for full guide.
