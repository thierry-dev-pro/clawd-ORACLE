# 🔮 ORACLE: AI-Powered Crypto Intelligence & Personal Brand Automation

![License](https://img.shields.io/badge/license-proprietary-red)
![Phase](https://img.shields.io/badge/phase-3%20%E2%9C%85-green)
![Security](https://img.shields.io/badge/security-Grade%20A-blue)
![Tests](https://img.shields.io/badge/tests-115%2B-brightgreen)

Plateforme automatisée pour la gestion de présence crypto, monitoring Twitter, synchronisation Notion et réponses IA intelligentes via Telegram.

## 🎯 Objectifs

- ✅ **Backup**: Code sécurisé et versionné
- ✅ **Versioning**: Historique complet + rollback possible
- ✅ **Collaboration**: Partage facile avec autres devs
- ✅ **Déploiement**: Infrastructure cloud-ready

---

## 📦 Architecture

### Phase 1: Infrastructure ✅
- **FastAPI** framework (async, modern)
- **Telegram Bot** webhook (real-time)
- **AI Handler** (multi-model: Haiku/Sonnet/Opus)
- **PostgreSQL** + **Redis** backend
- **OWASP Compliant** security

### Phase 2: Intelligence ✅
- **Twitter Scraper** (RSS + Nitter, free)
- **Airdrop Tracker** (automated detection)
- **Auto-responses** (9+ keyword patterns)
- **Background Scheduler** (APScheduler)
- **Admin API** (11 endpoints)
- **115+ Tests** (high coverage)

### Phase 3: Notion Sync ✅
- **Notion Integration** (REST API v1)
- **26 Twitter Handles** tracked
- **Hourly Sync** (configurable)
- **Category Tracking** (20 categories)
- **Database Schema** (automated)

---

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.9+
# PostgreSQL 14+
# Redis 7.0+
```

### Installation

```bash
# 1. Clone repository
git clone https://github.com/thierry-dev-pro/clawd-ORACLE.git
cd clawd-ORACLE

# 2. Setup Python environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# 3. Install dependencies
cd oracle
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys:
# - TELEGRAM_TOKEN
# - ANTHROPIC_API_KEY
# - DATABASE_URL
# - REDIS_URL
# - NOTION_API_KEY (Phase 3)
# - NOTION_DATABASE_ID (Phase 3)

# 5. Initialize database
python -m core.database

# 6. Run application
uvicorn main:app --reload
```

---

## 📋 Configuration

### Environment Variables

```bash
# Telegram
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook/telegram

# AI Models (Anthropic Claude)
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-haiku-20241022

# Database
DATABASE_URL=postgresql://user:pass@localhost/oracle
REDIS_URL=redis://localhost:6379/0

# Notion (Phase 3)
NOTION_API_KEY=ntn_...
NOTION_DATABASE_ID=...

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false
```

### Phase 3 Configuration
```bash
# .env.phase3
NOTION_API_KEY=ntn_YOUR_API_KEY
NOTION_DATABASE_ID=YOUR_DATABASE_ID
PHASE3_ENABLED=true
PHASE3_SYNC_INTERVAL=3600  # seconds
```
⚠️ Never commit actual API keys! Use `.env` files + `.gitignore`

---

## 📊 API Endpoints

### Health & Status
```
GET /                    # Root health check
GET /health              # Detailed health
GET /status              # ORACLE status
GET /api/phase3/status   # Phase 3 sync status
```

### Telegram
```
POST /webhook/telegram   # Webhook handler
```

### Phase 2: Intelligence
```
GET  /api/tweets                         # Get tweets
POST /api/tweets/scrape                  # Trigger scraper
GET  /api/airdrops                       # Get airdrops
POST /api/airdrops/check                 # Check new airdrops
POST /api/airdrops/{id}/claim            # Mark as claimed
GET  /api/scheduler/status               # Scheduler status
POST /api/scheduler/start                # Start scheduler
POST /api/scheduler/stop                 # Stop scheduler
```

### Phase 3: Notion Sync
```
POST /api/phase3/sync/now                # Trigger sync immediately
POST /api/phase3/sync/start              # Start hourly scheduler
POST /api/phase3/sync/stop               # Stop scheduler
```

---

## 🧪 Testing

```bash
cd oracle

# Run all tests
pytest

# Run with coverage
pytest --cov=core tests/

# Run specific test file
pytest tests/test_twitter_scraper.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_auto_responses.py::TestAutoResponses::test_pattern_matching
```

### Test Coverage
- ✅ Twitter Scraper (integration, mocking)
- ✅ Airdrop Tracker (detection, notifications)
- ✅ Scheduler (job management, timing)
- ✅ Auto-responses (patterns, matching)
- ✅ Security (injection, validation)
- ✅ Database (models, queries)

---

## 🔄 Workflow

### Message Flow
```
Telegram User
    ↓
    [Telegram Webhook]
    ↓
    [AI Handler: Classify message type]
    ↓
    [Auto-responses: Check patterns]
    ↓
    [AI Models: Generate response (Haiku/Sonnet)]
    ↓
    [Database: Log message + response]
    ↓
    [Telegram: Send response back]
```

### Background Jobs (Phase 2)
```
APScheduler
    ↓
    [Twitter Scraper: Hourly (free RSS + Nitter)]
    ↓
    [Airdrop Tracker: Every 2 hours]
    ↓
    [Database: Store tweets + airdrops]
    ↓
    [Notifications: Alert on new airdrops]
```

### Notion Sync (Phase 3)
```
APScheduler (Hourly)
    ↓
    [Load twitter_handles_phase3.json]
    ↓
    [NotionSyncHandler: Create/Update pages]
    ↓
    [Notion API: Store in database]
    ↓
    [Logging: Record sync stats]
```

---

## 📁 Project Structure

```
oracle/
├── core/                          # Main application modules
│   ├── ai_handler.py             # AI response generation
│   ├── telegram_bot.py           # Telegram webhook handler
│   ├── auto_responses.py         # Pattern matching
│   ├── twitter_scraper.py        # Twitter monitoring
│   ├── airdrop_tracker.py        # Airdrop detection
│   ├── scheduler.py              # Background jobs
│   ├── notion_sync.py            # Notion integration (Phase 3)
│   ├── phase3_scheduler.py       # Phase 3 scheduler
│   ├── database.py               # Database setup
│   ├── models.py                 # SQLAlchemy models
│   ├── config.py                 # Configuration
│   └── admin_api.py              # Admin endpoints
├── tests/                         # Test suite (115+ tests)
│   ├── test_ai_handler.py
│   ├── test_twitter_scraper.py
│   ├── test_airdrop_tracker.py
│   ├── test_auto_responses.py
│   ├── test_scheduler.py
│   └── conftest.py
├── data/                          # Data files
│   └── twitter_handles_phase3.json
├── logs/                          # Application logs
├── docs/                          # Documentation
├── scripts/                       # Utility scripts
│   ├── setup_notion_db.py        # Notion DB setup
│   └── test_phase3_sync.py       # Phase 3 tests
├── main.py                        # FastAPI application
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
├── .env.phase3                    # Phase 3 config
├── docker-compose.yml             # Docker setup
├── pytest.ini                     # Test config
└── README.md                      # This file
```

---

## 💰 Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| Anthropic API | ~€25/mo | Multi-model (Haiku/Sonnet/Opus) |
| PostgreSQL | ~€15/mo | Small RDS instance |
| Redis | ~€5/mo | Cache layer |
| Telegram Bot | Free | Webhook mode |
| Twitter Data | Free | RSS + Nitter (no paid API) |
| Notion API | Free | 1000 calls/min included |
| **Total** | **~€45/mo** | Optimized |

---

## 🔐 Security

- ✅ **OWASP Top 10** compliance
- ✅ **Input validation** on all endpoints
- ✅ **Rate limiting** (Telegram webhook)
- ✅ **Secret management** (.env isolation)
- ✅ **SQL injection** prevention (SQLAlchemy ORM)
- ✅ **CSRF protection** (webhook tokens)
- ✅ **Logging** (audit trail)

### Grade: **A**

---

## 📈 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs
```bash
# Application logs
tail -f oracle.log

# Phase 3 sync logs
tail -f logs/phase3_sync.log

# Test logs
pytest -v --tb=short
```

### Metrics
- Message throughput
- API response time
- Database query latency
- Memory usage
- Error rates

---

## 🚢 Deployment

### Docker

```bash
# Build image
docker build -t oracle:latest .

# Run container
docker run -d \
  --name oracle \
  --env-file .env \
  -p 8000:8000 \
  -v ./logs:/app/logs \
  oracle:latest
```

### Docker Compose

```bash
docker-compose up -d
```

### Cloud Deployment

- **Heroku**: `git push heroku main`
- **AWS EC2**: Deploy with Systemd + Nginx
- **GCP Cloud Run**: Containerized FastAPI
- **Azure Container Instances**: Docker image

---

## 📝 Versioning

### Semantic Versioning
- `v1.0.0` - Phase 1 Complete
- `v2.0.0` - Phase 2 Complete (Twitter + Airdrop)
- `v3.0.0` - Phase 3 Complete (Notion Sync)

### Release Process
1. Update version in `main.py`
2. Create git tag: `git tag v3.0.0`
3. Push tag: `git push origin v3.0.0`
4. GitHub Actions auto-deploys

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/amazing-feature`
2. Commit changes: `git commit -m 'Add amazing feature'`
3. Push to branch: `git push origin feature/amazing-feature`
4. Open Pull Request

### Code Standards
- PEP 8 compliance
- Type hints on all functions
- Docstrings (Google style)
- 80% test coverage minimum

---

## 📚 Documentation

- [PHASE3_INIT.md](oracle/PHASE3_INIT.md) - Phase 3 setup guide
- [PHASE3_MAIN_INTEGRATION.md](oracle/PHASE3_MAIN_INTEGRATION.md) - Main.py integration
- [PHASE2_COMPLETE.md](oracle/PHASE2_COMPLETE.md) - Phase 2 specs
- [DEPLOYMENT.md](oracle/DEPLOYMENT.md) - Production deployment

---

## 🐛 Issues & Support

- **Report bugs**: GitHub Issues
- **Feature requests**: Discussions
- **Documentation**: Wiki
- **Security issues**: Contact directly (no public disclosure)

---

## 📄 License

Proprietary - All rights reserved

---

## 🎉 Status

| Phase | Status | Date |
|-------|--------|------|
| Phase 1: Infrastructure | ✅ Complete | Jan 31, 2026 |
| Phase 2: Intelligence | ✅ Complete | Feb 2, 2026 |
| Phase 3: Notion Sync | ✅ Complete | Feb 6, 2026 |
| **Production Ready** | **✅ YES** | **Feb 6, 2026** |

---

**Last Updated**: Feb 6, 2026  
**Repository**: https://github.com/thierry-dev-pro/clawd-ORACLE  
**Maintainer**: @thierry-dev-pro
