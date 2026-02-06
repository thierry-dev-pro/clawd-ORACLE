# ORACLE Phase 2: Twitter Scraper + Airdrop Tracker

## Overview

Phase 2 implements **minimal-cost** crypto intelligence gathering via:
1. **Twitter Scraper** - Automated tweets collection on crypto topics
2. **Airdrop Tracker** - Automated detection of airdrop opportunities
3. **Background Scheduler** - Cost-optimized task execution

### Design Principles

✅ **No Paid APIs** - Uses only free sources (RSS, web scraping, public feeds)  
✅ **Rate Limited** - 5-10 tweets/hour max, 2-3 airdrop checks/day  
✅ **Cost Minimized** - Estimated cost: <$0.10/month  
✅ **Production Ready** - Full error handling, logging, rate limiting  
✅ **User Integrated** - Auto-responses, webhooks, notifications  

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    ORACLE                           │
├─────────────────────────────────────────────────────┤
│                  Scheduler Core                      │
│  (Background tasks, rate limiting, error recovery)  │
├────────────────────────────────────────────────────┤
│  Twitter Scraper      │    Airdrop Tracker         │
│  (RSS + Web)          │    (News + Explorers)      │
├────────────────────────────────────────────────────┤
│          Database (SQLite/PostgreSQL)              │
│  (tweets, airdrops tables)                         │
├────────────────────────────────────────────────────┤
│  API Endpoints  │  Auto-Responses  │  Webhooks    │
└────────────────────────────────────────────────────┘
```

---

## Modules

### 1. Twitter Scraper (`core/twitter_scraper.py`)

**Purpose**: Automatically collect relevant crypto tweets from free sources

**Sources**:
- RSS feeds (Coindesk, Bloomberg, CoinBase, TechCrunch)
- Nitter web scraping (alternative Twitter frontend, no auth required)
- Direct blockchain project RSS feeds

**Rate Limit**: 5-10 tweets/hour

**Tracked Keywords**:
```
bitcoin: btc, bitcoin, blockchain
ethereum: eth, ethereum, evm, defi
crypto: crypto, cryptocurrency, token, altcoin
defi: defi, decentralized finance, yield farming
nft: nft, nfts, collectible
```

**Key Classes**:

```python
# Tweet data model
@dataclass
class Tweet:
    id: str
    author: str
    content: str
    url: str
    posted_at: datetime
    source: str  # "rss", "web_scrape"
    keywords: List[str]
    likes: int = 0
    retweets: int = 0

# Main scraper
class TwitterScraper:
    async def scrape_rss_feeds() -> List[Tweet]
    async def scrape_nitter(query: str) -> List[Tweet]
    async def scrape_all_sources() -> List[Tweet]

# Database operations
class TwitterScraperDB:
    @staticmethod
    def save_tweets(db, tweets) -> int
    @staticmethod
    def get_recent_tweets(db, limit=10) -> List[Dict]
    @staticmethod
    def search_tweets(db, keyword, limit=10) -> List[Dict]
    @staticmethod
    def cleanup_old_tweets(db, days=7) -> int
```

**Usage Example**:

```python
from core.twitter_scraper import twitter_scraper, TwitterScraperDB
from core.database import SessionLocal

# Scrape
tweets = await twitter_scraper.scrape_all_sources()

# Save to DB
db = SessionLocal()
count = TwitterScraperDB.save_tweets(db, tweets)
print(f"Saved {count} tweets")
```

---

### 2. Airdrop Tracker (`core/airdrop_tracker.py`)

**Purpose**: Discover and track active cryptocurrency airdrop opportunities

**Sources**:
- Crypto news RSS feeds (Coindesk, CoinBase)
- Blockchain official channels (Ethereum, Polygon, Arbitrum)
- Community announcements

**Rate Limit**: 2-3 checks/day (8-hour intervals)

**Detected Airdrop Types**:
- Testnet rewards
- Community programs
- Retroactive airdrops
- Trading rewards
- Staking rewards

**Key Classes**:

```python
# Airdrop data model
@dataclass
class Airdrop:
    id: str
    project_name: str
    token_symbol: str
    description: str
    url: str
    status: str  # "active", "pending", "closed", "claimed"
    estimated_value: float = None
    requirements: List[str] = None
    ends_at: datetime = None

# Main tracker
class AirdropTracker:
    async def scrape_crypto_news_feeds() -> List[Airdrop]
    async def scrape_blockchain_explorers() -> List[Airdrop]
    async def check_all_sources() -> List[Airdrop]

# Database operations
class AirdropTrackerDB:
    @staticmethod
    def save_airdrops(db, airdrops) -> int
    @staticmethod
    def get_active_airdrops(db, limit=20) -> List[Dict]
    @staticmethod
    def get_airdrops_for_user(db, user_id, limit=10) -> List[Dict]
    @staticmethod
    def mark_claimed(db, airdrop_id) -> bool
    @staticmethod
    def cleanup_expired(db) -> int
```

**Usage Example**:

```python
from core.airdrop_tracker import airdrop_tracker, AirdropTrackerDB

# Check for airdrops
airdrops = await airdrop_tracker.check_all_sources()

# Save to DB
db = SessionLocal()
count = AirdropTrackerDB.save_airdrops(db, airdrops)
print(f"Found {count} new airdrops")

# Get active for user
user_airdrops = AirdropTrackerDB.get_airdrops_for_user(db, user_id=123)
```

---

### 3. Scheduler (`core/scheduler.py`)

**Purpose**: Background task management with intelligent scheduling

**Default Tasks**:
1. **twitter_scraper** - Every 1 hour (5-10 tweets max)
2. **airdrop_tracker** - Every 8 hours (max 3/day)
3. **cleanup_task** - Every 24 hours (delete old data)

**Key Classes**:

```python
class ScheduledTask:
    def __init__(name, func, interval_seconds, enabled=True)
    async def run()
    def should_run() -> bool
    
    # Properties
    last_run: datetime
    next_run: datetime
    run_count: int
    error_count: int

class Scheduler:
    def add_task(task: ScheduledTask) -> bool
    def remove_task(task_name: str) -> bool
    def enable_task(task_name: str) -> bool
    def disable_task(task_name: str) -> bool
    def start() -> bool
    def stop() -> bool
    def get_status() -> dict
```

**Usage Example**:

```python
from core.scheduler import scheduler, initialize_scheduler

# Auto-initialize on startup
initialize_scheduler()

# Or manual management
scheduler.start()
scheduler.get_status()
scheduler.disable_task("twitter_scraper")
scheduler.stop()
```

---

## Database Schema

### New Tables

#### `tweets` Table
```sql
CREATE TABLE tweets (
    id INTEGER PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE,
    author VARCHAR(255),
    content TEXT,
    url VARCHAR(500) UNIQUE,
    posted_at DATETIME,
    source VARCHAR(50),  -- "rss", "web_scrape"
    likes INTEGER,
    retweets INTEGER,
    replies INTEGER,
    keywords JSON,  -- ["bitcoin", "ethereum"]
    indexed_at DATETIME,
    created_at DATETIME
);

-- Indices
CREATE INDEX idx_tweets_posted_at ON tweets(posted_at);
CREATE INDEX idx_tweets_keywords ON tweets(keywords);
```

#### `airdrops` Table
```sql
CREATE TABLE airdrops (
    id INTEGER PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE,
    project_name VARCHAR(255),
    token_symbol VARCHAR(50),
    description TEXT,
    url VARCHAR(500),
    status VARCHAR(50),  -- "active", "pending", "closed", "claimed"
    estimated_value FLOAT,
    requirements JSON,  -- ["kyc", "hold_tokens"]
    ends_at DATETIME,
    source VARCHAR(100),
    discovered_at DATETIME,
    updated_at DATETIME,
    created_at DATETIME
);

-- Indices
CREATE INDEX idx_airdrops_status ON airdrops(status);
CREATE INDEX idx_airdrops_ends_at ON airdrops(ends_at);
CREATE INDEX idx_airdrops_project ON airdrops(project_name);
```

---

## API Endpoints

### Twitter Scraper Endpoints

#### `GET /api/tweets`
Get recent tweets from database

**Query Parameters**:
- `limit` (int, default=10): Max tweets
- `keyword` (str, optional): Filter by keyword

**Response**:
```json
{
    "count": 5,
    "tweets": [
        {
            "id": 1,
            "author": "@bitcoinnews",
            "content": "Bitcoin reaches new high...",
            "url": "https://...",
            "posted_at": "2024-01-15T10:30:00Z",
            "source": "rss",
            "keywords": ["bitcoin"]
        }
    ],
    "timestamp": "2024-01-15T10:35:00Z"
}
```

#### `POST /api/tweets/scrape`
Manually trigger Twitter scraper (normally automatic)

**Response**:
```json
{
    "status": "completed",
    "tweets_found": 8,
    "tweets_saved": 7,
    "timestamp": "2024-01-15T10:35:00Z"
}
```

---

### Airdrop Tracker Endpoints

#### `GET /api/airdrops`
Get active airdrops

**Query Parameters**:
- `limit` (int, default=20): Max results
- `user_id` (int, optional): Filter for specific user

**Response**:
```json
{
    "count": 3,
    "airdrops": [
        {
            "id": 1,
            "project_name": "Ethereum",
            "token_symbol": "ETH",
            "description": "Early participant rewards...",
            "url": "https://...",
            "status": "active",
            "estimated_value": 150.50,
            "requirements": ["kyc", "hold_eth"],
            "ends_at": "2024-02-15T00:00:00Z",
            "source": "ethereum_explorer"
        }
    ],
    "timestamp": "2024-01-15T10:35:00Z"
}
```

#### `POST /api/airdrops/check`
Manually trigger airdrop tracker (normally automatic)

**Response**:
```json
{
    "status": "completed",
    "airdrops_found": 5,
    "airdrops_saved": 4,
    "airdrops_expired": 2,
    "timestamp": "2024-01-15T10:35:00Z"
}
```

#### `POST /api/airdrops/{airdrop_id}/claim`
Mark airdrop as claimed by user

**Response**:
```json
{
    "status": "claimed",
    "airdrop_id": 1,
    "timestamp": "2024-01-15T10:35:00Z"
}
```

---

### Scheduler Endpoints

#### `GET /api/scheduler/status`
Get scheduler status and task details

**Response**:
```json
{
    "status": {
        "running": true,
        "tasks": {
            "twitter_scraper": {
                "enabled": true,
                "interval": 3600,
                "last_run": "2024-01-15T10:00:00Z",
                "next_run": "2024-01-15T11:00:00Z",
                "run_count": 24,
                "error_count": 0,
                "last_error": null
            },
            "airdrop_tracker": {
                "enabled": true,
                "interval": 28800,
                "last_run": "2024-01-15T08:00:00Z",
                "next_run": "2024-01-15T16:00:00Z",
                "run_count": 3,
                "error_count": 0,
                "last_error": null
            }
        }
    },
    "timestamp": "2024-01-15T10:35:00Z"
}
```

#### `POST /api/scheduler/start`
Start scheduler

#### `POST /api/scheduler/stop`
Stop scheduler

#### `POST /api/scheduler/task/{task_name}/enable`
Enable a specific task

#### `POST /api/scheduler/task/{task_name}/disable`
Disable a specific task

---

## Integration with Auto-Responses

Phase 2 integrates with auto-responses to handle airdrop-related queries:

```python
# In auto_responses.py patterns
ResponsePattern(
    pattern_id="crypto_airdrop",
    regex=r"(airdrop|free.*token|claim.*reward)",
    message_type=MessageType.QUESTION,
    description="Airdrop inquiries",
    response_template="""🎁 Looking for airdrops?
I found {count} active airdrops for you:
{airdrops_list}""",
    priority=ResponsePriority.HIGH,
    keywords=["airdrop", "claim", "free"],
    requires_context=True
)
```

**Integration Flow**:
1. User asks about airdrops
2. Auto-responder detects pattern
3. Fetches active airdrops from DB
4. Sends personalized response with links
5. Logs interaction for stats

---

## Configuration

### Environment Variables

```bash
# Scheduler config
SCHEDULER_ENABLED=true
TWITTER_SCRAPER_INTERVAL=3600      # 1 hour
AIRDROP_TRACKER_INTERVAL=28800     # 8 hours
CLEANUP_INTERVAL=86400             # 24 hours

# Scraper config
TWITTER_SCRAPER_LIMIT=10           # Max tweets per run
AIRDROP_TRACKER_LIMIT=20           # Max airdrops per run
REQUEST_TIMEOUT=10                 # HTTP timeout (seconds)

# Feature flags
ENABLE_TWITTER_SCRAPER=true
ENABLE_AIRDROP_TRACKER=true
ENABLE_AUTO_CLEANUP=true
```

---

## Testing

### Run Tests

```bash
# Twitter Scraper tests
pytest tests/test_twitter_scraper.py -v

# Airdrop Tracker tests
pytest tests/test_airdrop_tracker.py -v

# Scheduler tests
pytest tests/test_scheduler.py -v

# All Phase 2 tests
pytest tests/test_twitter_scraper.py tests/test_airdrop_tracker.py tests/test_scheduler.py -v
```

### Test Coverage

- ✅ Data model creation and validation
- ✅ Keyword extraction and filtering
- ✅ Rate limiting logic
- ✅ Database operations (save, retrieve, cleanup)
- ✅ Task scheduling and execution
- ✅ Error handling and recovery
- ✅ Integration workflows

---

## Deployment Checklist

- [ ] Database tables created (`tweets`, `airdrops`)
- [ ] Requirements installed (`feedparser`, `beautifulsoup4`, `httpx`)
- [ ] Environment variables configured
- [ ] Scheduler initialized in `main.py` startup
- [ ] API endpoints tested
- [ ] Rate limiting verified
- [ ] Auto-responses integrated
- [ ] Error logging configured
- [ ] Monitoring/alerts setup
- [ ] Documentation reviewed

---

## Cost Analysis

| Component | Source | Cost |
|-----------|--------|------|
| RSS Feeds | Coindesk, Bloomberg | Free |
| Web Scraping | Nitter, Explorers | Free |
| HTTP Requests | ~50/day | <$0.01 |
| Database | SQLite or small DB | Free-$5 |
| Compute | Background tasks | Negligible |
| **Total/Month** | - | **<$0.50** |

---

## Performance Optimization

### Rate Limiting Strategy
- **Tweets**: 10 per hour (600 per day max)
- **Airdrops**: 3 per day (24-72 hour interval)
- **Cleanup**: 1 per day

### Database Optimization
- Automatic cleanup of tweets older than 7 days
- Index on `posted_at`, `keywords`, `status`, `ends_at`
- Efficient JSON queries for filtering

### Async Operations
- Non-blocking HTTP requests
- Parallel feed parsing
- Background task execution

---

## Troubleshooting

### Common Issues

#### 1. "No tweets scraped"
```
Check:
- RSS feeds are accessible
- Network connectivity
- Rate limiting not exceeded
- Keywords configured correctly
```

#### 2. "Scheduler not running"
```
Check:
- initialize_scheduler() called in startup
- No exceptions during initialization
- Check /api/scheduler/status
```

#### 3. "Database errors"
```
Check:
- Tables created (init_db())
- Database connection valid
- Disk space available
```

### Debug Mode

```python
# Enable verbose logging
from core.logging_config import setup_logging
setup_logging("DEBUG")

# Check scheduler status
GET /api/scheduler/status

# Check recent logs
GET /api/logs?level=ERROR
```

---

## Future Enhancements

### Phase 3 Potential Features
- [ ] Twitter API v2 integration (premium)
- [ ] Discord server monitoring
- [ ] Custom webhook subscriptions
- [ ] Machine learning for airdrop scoring
- [ ] User portfolio tracking
- [ ] Push notifications
- [ ] Airdrop eligibility calculator
- [ ] Historical trend analysis

---

## Support & Documentation

- **Code**: `core/twitter_scraper.py`, `core/airdrop_tracker.py`, `core/scheduler.py`
- **Tests**: `tests/test_twitter_scraper.py`, `tests/test_airdrop_tracker.py`, `tests/test_scheduler.py`
- **API Docs**: `/api/docs` (Swagger)
- **Logs**: `logs/` directory

---

**Last Updated**: January 2024  
**Status**: ✅ Production Ready  
**Version**: 0.3.0 (Phase 2 Complete)
