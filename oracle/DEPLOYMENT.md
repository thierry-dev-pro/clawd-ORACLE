# Phase 2 Deployment Guide

## Pre-Deployment Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created
- [ ] All requirements installed
- [ ] Database configured
- [ ] Environment variables set
- [ ] Tests passing
- [ ] API endpoints verified

---

## Installation Steps

### 1. Install Dependencies

```bash
cd /Users/clawdbot/clawd/oracle

# Create virtual environment (optional)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
# Create tables (automatic on first startup)
python -c "from core.database import init_db; init_db(); print('✅ Database initialized')"
```

### 3. Configure Environment

Create `.env` file in oracle root directory:

```bash
# Telegram
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook/telegram

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key_here

# Database
DATABASE_URL=sqlite:///./oracle.db
# Or PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/oracle

# API Server
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
ENVIRONMENT=production

# Logging
LOG_LEVEL=INFO

# Phase 2: Scheduler Configuration
SCHEDULER_ENABLED=true
TWITTER_SCRAPER_INTERVAL=3600      # 1 hour
AIRDROP_TRACKER_INTERVAL=28800     # 8 hours
CLEANUP_INTERVAL=86400             # 24 hours

# Phase 2: Scraper Configuration
TWITTER_SCRAPER_LIMIT=10
AIRDROP_TRACKER_LIMIT=20
REQUEST_TIMEOUT=10

# Feature Flags
ENABLE_TWITTER_SCRAPER=true
ENABLE_AIRDROP_TRACKER=true
ENABLE_AUTO_CLEANUP=true
```

### 4. Run Tests

```bash
# Phase 2 tests
pytest tests/test_twitter_scraper.py tests/test_airdrop_tracker.py tests/test_scheduler.py -v

# Expected output:
# ==================== 30 passed in 2.45s ====================
```

### 5. Start Application

```bash
# Development mode
python -m core.main_robust

# Production mode (with gunicorn)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker core.main_robust:app --bind 0.0.0.0:8000
```

Expected startup output:

```
🚀 Starting ORACLE...
✅ Database initialized
✅ Phase 2 scheduler initialized (Twitter Scraper + Airdrop Tracker)
✅ Health checks registered
✅ Rate limiter initialized
✅ Security layers initialized
✅ Monitoring initialized
🔮 ORACLE is ONLINE and ready
```

---

## Verification

### 1. Check Health Status

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
    "status": "healthy",
    "version": "0.3.0-hardened",
    "timestamp": "2024-01-15T10:35:00Z"
}
```

### 2. Check Scheduler Status

```bash
curl http://localhost:8000/api/scheduler/status
```

Expected response:
```json
{
    "status": {
        "running": true,
        "tasks": {
            "twitter_scraper": {
                "enabled": true,
                "interval": 3600,
                "run_count": 0,
                "error_count": 0
            },
            "airdrop_tracker": {
                "enabled": true,
                "interval": 28800,
                "run_count": 0,
                "error_count": 0
            },
            "cleanup_task": {
                "enabled": true,
                "interval": 86400,
                "run_count": 0,
                "error_count": 0
            }
        }
    }
}
```

### 3. Manual Trigger Tests

```bash
# Trigger Twitter scraper
curl -X POST http://localhost:8000/api/tweets/scrape

# Trigger Airdrop tracker
curl -X POST http://localhost:8000/api/airdrops/check

# Both should return:
# {
#     "status": "completed",
#     "tweets_found": 0,  # or actual count
#     "timestamp": "..."
# }
```

### 4. Get Tweets/Airdrops

```bash
# Get recent tweets
curl http://localhost:8000/api/tweets?limit=5

# Get active airdrops
curl http://localhost:8000/api/airdrops?limit=10
```

---

## Docker Deployment

### Using Docker

```bash
# Build image
docker build -t oracle:0.3.0 .

# Run container
docker run -d \
  --name oracle \
  -p 8000:8000 \
  -e TELEGRAM_TOKEN=your_token \
  -e ANTHROPIC_API_KEY=your_key \
  -e DATABASE_URL=sqlite:///./oracle.db \
  -v oracle_data:/app/data \
  oracle:0.3.0
```

### Using Docker Compose

```bash
# Create docker-compose.yml (see Docker section in PHASE2_README.md)

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f oracle

# Stop services
docker-compose down
```

---

## Systemd Service (Linux)

### Create Service File

Create `/etc/systemd/system/oracle.service`:

```ini
[Unit]
Description=ORACLE - AI Crypto Intelligence
After=network.target

[Service]
Type=simple
User=oracle
WorkingDirectory=/path/to/oracle
Environment="PATH=/path/to/oracle/venv/bin"
Environment="TELEGRAM_TOKEN=your_token"
Environment="ANTHROPIC_API_KEY=your_key"
ExecStart=/path/to/oracle/venv/bin/python -m core.main_robust
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable oracle

# Start service
sudo systemctl start oracle

# Check status
sudo systemctl status oracle

# View logs
sudo journalctl -u oracle -f
```

---

## Nginx Reverse Proxy

### Configure Nginx

```nginx
upstream oracle {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Proxy to ORACLE
    location / {
        proxy_pass http://oracle;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Webhook endpoint
    location /webhook/telegram {
        proxy_pass http://oracle/webhook/telegram;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Monitoring Setup

### Prometheus Metrics

```bash
# Scrape endpoint
curl http://localhost:8000/api/metrics/prometheus
```

Add to Prometheus config:

```yaml
scrape_configs:
  - job_name: 'oracle'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/metrics/prometheus'
    scrape_interval: 15s
```

### Health Check Endpoint

```bash
# For load balancer health checks
curl http://localhost:8000/health
```

### Alerting Rules

```yaml
# Prometheus alert rules
groups:
  - name: oracle
    rules:
      - alert: SchedulerDown
        expr: up{job="oracle"} == 0
        for: 5m
        annotations:
          summary: "ORACLE Scheduler is down"

      - alert: HighErrorRate
        expr: rate(oracle_errors_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "ORACLE error rate is high"

      - alert: TaskFailed
        expr: oracle_task_errors_total > 5
        for: 5m
        annotations:
          summary: "ORACLE task error count too high"
```

---

## Performance Tuning

### Database Optimization

```sql
-- Create indices for faster queries
CREATE INDEX idx_tweets_posted_at ON tweets(posted_at);
CREATE INDEX idx_tweets_keywords ON tweets(keywords);
CREATE INDEX idx_airdrops_status ON airdrops(status);
CREATE INDEX idx_airdrops_ends_at ON airdrops(ends_at);
CREATE INDEX idx_airdrops_project ON airdrops(project_name);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM tweets WHERE keywords @> '["bitcoin"]';
```

### Application Tuning

```python
# In core/config.py
class Settings:
    # Connection pooling
    DATABASE_POOL_SIZE = 10
    DATABASE_MAX_OVERFLOW = 20
    
    # Caching
    CACHE_TTL = 3600  # 1 hour
    ENABLE_CACHE = True
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_PERIOD = 60  # seconds
```

---

## Backup & Recovery

### Database Backup

```bash
# SQLite
cp oracle.db oracle.db.backup

# PostgreSQL
pg_dump oracle > oracle_backup.sql
```

### Restore Database

```bash
# SQLite
cp oracle.db.backup oracle.db

# PostgreSQL
psql oracle < oracle_backup.sql
```

### Automated Backups

```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backups/oracle"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp /path/to/oracle.db $BACKUP_DIR/oracle_$TIMESTAMP.db

# Keep last 7 days only
find $BACKUP_DIR -name "oracle_*.db" -mtime +7 -delete

echo "Backup completed: oracle_$TIMESTAMP.db"
```

Add to crontab:
```bash
0 2 * * * /path/to/backup.sh
```

---

## Security Considerations

### Environment Variables

```bash
# Never commit .env file
echo ".env" >> .gitignore

# Use secrets management in production
# AWS Secrets Manager, HashiCorp Vault, etc.
```

### API Security

```python
# CORS configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Rate limiting
from core.security import rate_limiter
# Already configured in main.py
```

### Database Security

```bash
# Use strong credentials
# PostgreSQL: change default password
# Create limited-privilege user for app
```

---

## Troubleshooting Deployment

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
python -m core.main_robust --port 8001
```

### Database Connection Error

```bash
# Check database is accessible
python -c "from core.database import SessionLocal; db = SessionLocal(); print('✅ DB OK')"

# Check credentials in DATABASE_URL
# Verify database exists (SQLite) or is running (PostgreSQL)
```

### Scheduler Not Starting

```bash
# Check logs
tail -f logs/oracle.log | grep scheduler

# Verify dependencies
pip list | grep feedparser beautifulsoup

# Check initialization
GET /api/scheduler/status
```

### Out of Memory

```bash
# Check memory usage
ps aux | grep oracle

# Reduce cache size
CACHE_TTL=600  # Reduce from 3600

# Reduce worker count
# In gunicorn: -w 2 (instead of 4)
```

---

## Upgrade Procedure

### Backup First

```bash
cp oracle.db oracle.db.backup
```

### Update Code

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Run Migrations

```bash
# Database schema updates
python -c "from core.database import init_db; init_db()"
```

### Restart Service

```bash
# Systemd
sudo systemctl restart oracle

# Docker
docker-compose down && docker-compose up -d

# Manual
# Stop old process, start new one
```

### Verify

```bash
curl http://localhost:8000/health
```

---

## Support Resources

### Documentation
- Main: `PHASE2.md`
- Integration: `PHASE2_README.md`
- This file: `DEPLOYMENT.md`
- API Docs: `http://localhost:8000/api/docs`

### Logs
- Application: `logs/oracle.log`
- Systemd: `journalctl -u oracle`
- Docker: `docker-compose logs -f`

### Health Endpoints
- Health: `GET /health`
- Metrics: `GET /api/metrics`
- Logs: `GET /api/logs`
- Scheduler: `GET /api/scheduler/status`

---

## Version Information

- **Phase**: 2 (Twitter Scraper + Airdrop Tracker)
- **Version**: 0.3.0
- **Status**: ✅ Production Ready
- **Last Updated**: January 2024

---

**Questions?** Check the logs with `GET /api/logs` or review PHASE2_README.md
