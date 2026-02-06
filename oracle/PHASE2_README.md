# Phase 2 Integration Guide: Twitter Scraper + Airdrop Tracker

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**New dependencies**:
- `feedparser` - RSS feed parsing
- `beautifulsoup4` - Web scraping
- `httpx` - Async HTTP client
- `pytest` - Testing framework

### 2. Database Migration

```bash
# The database schema is automatically created on startup
# Tables added: tweets, airdrops

python -c "from core.database import init_db; init_db()"
```

### 3. Start the Application

```bash
python -m core.main_robust
```

The scheduler will automatically initialize with Phase 2 tasks:
- ✅ Twitter Scraper (every 1 hour)
- ✅ Airdrop Tracker (every 8 hours)
- ✅ Auto Cleanup (every 24 hours)

---

## API Testing

### Test Twitter Scraper

```bash
# Get recent tweets
curl http://localhost:8000/api/tweets?limit=5

# Scrape tweets (manual trigger)
curl -X POST http://localhost:8000/api/tweets/scrape

# Search tweets by keyword
curl http://localhost:8000/api/tweets?keyword=bitcoin&limit=10
```

### Test Airdrop Tracker

```bash
# Get active airdrops
curl http://localhost:8000/api/airdrops?limit=10

# Check for new airdrops (manual trigger)
curl -X POST http://localhost:8000/api/airdrops/check

# Get airdrops for specific user
curl http://localhost:8000/api/airdrops?user_id=123&limit=10

# Mark airdrop as claimed
curl -X POST http://localhost:8000/api/airdrops/1/claim
```

### Test Scheduler

```bash
# Get scheduler status
curl http://localhost:8000/api/scheduler/status

# Start scheduler
curl -X POST http://localhost:8000/api/scheduler/start

# Stop scheduler
curl -X POST http://localhost:8000/api/scheduler/stop

# Enable task
curl -X POST http://localhost:8000/api/scheduler/task/twitter_scraper/enable

# Disable task
curl -X POST http://localhost:8000/api/scheduler/task/airdrop_tracker/disable
```

---

## Running Tests

### Run All Phase 2 Tests

```bash
pytest tests/test_twitter_scraper.py tests/test_airdrop_tracker.py tests/test_scheduler.py -v
```

### Run Specific Test Suite

```bash
# Twitter Scraper tests
pytest tests/test_twitter_scraper.py -v -s

# Airdrop Tracker tests
pytest tests/test_airdrop_tracker.py -v -s

# Scheduler tests
pytest tests/test_scheduler.py -v -s
```

### With Coverage Report

```bash
pytest tests/ --cov=core --cov-report=html
```

---

## Configuration

### Environment Variables

Create `.env` file with Phase 2 settings:

```bash
# Scheduler intervals (in seconds)
TWITTER_SCRAPER_INTERVAL=3600      # 1 hour
AIRDROP_TRACKER_INTERVAL=28800     # 8 hours (3 checks/day)
CLEANUP_INTERVAL=86400             # 24 hours

# Scraper limits
TWITTER_SCRAPER_LIMIT=10           # Max tweets per run
AIRDROP_TRACKER_LIMIT=20           # Max airdrops per run

# HTTP settings
REQUEST_TIMEOUT=10                 # Seconds

# Feature flags
ENABLE_TWITTER_SCRAPER=true
ENABLE_AIRDROP_TRACKER=true
ENABLE_AUTO_CLEANUP=true

# Logging
LOG_LEVEL=INFO                     # DEBUG, INFO, WARNING, ERROR
```

---

## Integration with Existing Features

### 1. Auto-Responses

Phase 2 integrates with auto-responses for airdrop queries:

```python
# Example: User asks about airdrops
User: "Are there any airdrops available?"

# Auto-responder detects airdrop pattern
# Fetches from DB
# Sends personalized response with active airdrops
Bot: "🎁 I found 3 active airdrops for you: ..."
```

### 2. Webhook Integration

Tweets and airdrops can trigger webhooks:

```python
# In webhook processor
if "airdrop" in message.text.lower():
    # Suggest relevant airdrops
    airdrops = AirdropTrackerDB.get_active_airdrops(db)
    return suggest_relevant_airdrops(user_id, airdrops)

if "bitcoin" in message.text.lower():
    # Provide relevant tweets
    tweets = TwitterScraperDB.search_tweets(db, "bitcoin")
    return formatted_tweet_suggestions(tweets)
```

### 3. User Notifications

Premium users get notifications:

```python
# Notify premium users of new high-value airdrops
def notify_premium_users(airdrop):
    if airdrop.estimated_value > 100:
        send_notification_to_premium_users(
            f"🎁 New airdrop: {airdrop.project_name} (${airdrop.estimated_value})"
        )
```

---

## Monitoring & Troubleshooting

### Check Scheduler Status

```python
from core.scheduler import scheduler

status = scheduler.get_status()
print(status)
# Output:
# {
#     'running': True,
#     'tasks': {
#         'twitter_scraper': {
#             'enabled': True,
#             'run_count': 24,
#             'error_count': 0,
#             'last_run': '2024-01-15T10:00:00Z',
#             'next_run': '2024-01-15T11:00:00Z'
#         },
#         ...
#     }
# }
```

### View Logs

```bash
# Recent errors
curl http://localhost:8000/api/logs?level=ERROR&limit=20

# All logs with scheduler component
curl http://localhost:8000/api/logs?limit=50

# Check specific log file
tail -f logs/oracle.log | grep "scheduler\|scraper\|airdrop"
```

### Debug Mode

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
export LOG_LEVEL=DEBUG
python -m core.main_robust
```

### Common Issues

#### 1. Scheduler Not Starting

```
Error: "Scheduler initialization partially failed"

Solution:
- Check if dependencies installed: pip install feedparser beautifulsoup4 httpx
- Check logs for specific errors
- Verify DATABASE_URL is valid
```

#### 2. No Tweets Found

```
Reason: RSS feeds may be temporarily unavailable

Solution:
- Check network connectivity
- Verify RSS feed URLs are accessible
- Try manual scrape: POST /api/tweets/scrape
- Check logs for HTTP errors
```

#### 3. Rate Limiting Issues

```
Issue: "Not enough time since last web scrape"

Solution:
- Adjust intervals in .env
- Check last_run time in scheduler status
- Remember: web scraping is limited to prevent overload
```

---

## Performance Metrics

### Expected Performance

| Metric | Value |
|--------|-------|
| Tweets per hour | 5-10 |
| Airdrop checks per day | 2-3 |
| Database cleanup | Daily |
| API response time | <500ms |
| Memory footprint | ~50MB |
| CPU usage | <5% (idle) |

### Optimization Tips

1. **Adjust intervals** if experiencing resource issues
2. **Reduce cleanup frequency** if storage is not a concern
3. **Disable web scraping** if only using RSS feeds
4. **Use database indices** for faster queries

---

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

CMD ["python", "-m", "core.main_robust"]
```

### Docker Compose

```yaml
version: '3.9'
services:
  oracle:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./oracle.db
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ENABLE_TWITTER_SCRAPER=true
      - ENABLE_AIRDROP_TRACKER=true
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

---

## API Documentation

### Swagger UI

Visit: `http://localhost:8000/api/docs`

Shows all endpoints with:
- Parameters
- Request/Response schemas
- Try-it-out interface

### ReDoc

Visit: `http://localhost:8000/api/redoc`

Alternative documentation interface

---

## Development

### Adding New Scraper Source

```python
# In core/twitter_scraper.py
class TwitterScraper:
    async def scrape_custom_source(self) -> List[Tweet]:
        """Add custom source"""
        tweets = []
        
        # Your scraping logic here
        
        return tweets
    
    async def scrape_all_sources(self) -> List[Tweet]:
        tweets = []
        tweets.extend(await self.scrape_rss_feeds())
        tweets.extend(await self.scrape_nitter(...))
        tweets.extend(await self.scrape_custom_source())  # Add here
        return tweets
```

### Adding Custom Scheduled Task

```python
# In core/scheduler.py
async def custom_task():
    """Custom background task"""
    logger.info("Running custom task")
    # Your logic here
    return {"status": "completed"}

# In main.py startup
from core.scheduler import scheduler, ScheduledTask
task = ScheduledTask(
    name="custom_task",
    func=custom_task,
    interval_seconds=3600
)
scheduler.add_task(task)
```

---

## FAQ

**Q: Why no Twitter API v2?**  
A: API v2 requires paid subscription (~$100+/month). RSS and web scraping are free alternatives that work well for basic use cases.

**Q: What if RSS feeds go down?**  
A: Fallback to web scraping, or use alternative feeds. The system handles HTTP errors gracefully.

**Q: Can I increase scraper frequency?**  
A: Yes, adjust `TWITTER_SCRAPER_INTERVAL` and `AIRDROP_TRACKER_INTERVAL` in `.env`.

**Q: Does Phase 2 support webhooks?**  
A: Yes! Integrate tweets/airdrops into webhook processor to send suggestions.

**Q: How much storage do I need?**  
A: ~10MB per 100,000 tweets. Auto-cleanup removes old tweets after 7 days.

---

## Roadmap

### Phase 2 (Current)
- ✅ Twitter Scraper (RSS + Web)
- ✅ Airdrop Tracker (News + Explorers)
- ✅ Background Scheduler
- ✅ API Endpoints
- ✅ Auto-response Integration

### Phase 3 (Planned)
- [ ] Twitter API v2 (premium tier)
- [ ] Discord monitoring
- [ ] Portfolio tracking
- [ ] ML-based airdrop scoring
- [ ] Push notifications
- [ ] Custom webhooks

---

## Support

### Documentation
- Main docs: `PHASE2.md`
- Code comments: Inline documentation
- API docs: `http://localhost:8000/api/docs`

### Issues
- Check logs: `GET /api/logs`
- Check scheduler: `GET /api/scheduler/status`
- Check health: `GET /health`

### Contact
- Issues: Create GitHub issue
- Discussions: Check DISCUSSIONS.md
- Logs: `logs/` directory

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.3.0 | Jan 2024 | ✅ Phase 2 Release |
| 0.2.0 | Dec 2023 | Phase 1 Complete |
| 0.1.0 | Nov 2023 | Initial Release |

---

**Status**: ✅ Production Ready  
**Last Updated**: January 2024  
**Maintainer**: ORACLE Development Team
