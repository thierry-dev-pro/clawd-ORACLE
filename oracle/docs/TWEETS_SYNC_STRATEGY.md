# 📡 ORACLE Phase 4: Tweets Sync Strategy

## Current Status

✅ **DB Connected**: PostgreSQL running  
⏳ **Table Empty**: `tweets` table not yet populated  
✅ **ML Pipeline**: Ready (using mock data for testing)

## Issue Identified

**Twitter Scraper Phase 2** collects tweets via:
- RSS feeds (public, free)
- Nitter scraping (lightweight)
- No direct Twitter API v2 (blocked by paid tier)

**But**: Tweets aren't persisted to `tweets` table in DB yet.

## Solution: Connect Scraper → DB

### 1. Fix: Save tweets to DB
The `TwitterScraper` class in `/core/twitter_scraper.py` collects tweets but doesn't save them.

**Action**: Add persistence:
```python
# In core/twitter_scraper.py
from sqlalchemy.orm import Session
from core.models import TweetModel

async def save_tweets(self, tweets: List[Tweet], db: Session):
    """Save tweets to DB"""
    for tweet in tweets:
        db_tweet = TweetModel(
            external_id=tweet.id,
            author=tweet.author,
            content=tweet.content,
            url=tweet.url,
            posted_at=tweet.posted_at,
            source=tweet.source,
            likes=tweet.likes,
            retweets=tweet.retweets,
            replies=tweet.replies,
            keywords=tweet.keywords,
        )
        db.add(db_tweet)
    db.commit()
```

### 2. Activate scraper scheduler
The `phase3_scheduler.py` should run Twitter scraper every N hours.

**Verify**:
```bash
cd oracle
grep -r "twitter_scraper" core/phase3_scheduler.py
```

### 3. Export to CSV for ML
Once DB populated, use:
```bash
python3 ml_engine/export_tweets.py
```

This exports all tweets to `data/tweets_history.csv`.

## Current Workaround: Mock Data

**For immediate ML testing**, using `mock_tweets.py`:
```bash
python3 ml_engine/mock_tweets.py
# → data/tweets_mock.csv (400 test tweets)
```

Then score:
```bash
python3 ml_engine/influencer_scorer.py < data/tweets_mock.csv
```

## Integration Timeline

| Phase | Task | Status |
|-------|------|--------|
| 2 | Twitter scraper collects tweets | ✅ Code ready |
| 2 | Save tweets to DB | ⏳ Need patch |
| 2 | Run scheduler | ⏳ Verify active |
| 4 | Export tweets CSV | ✅ Script ready |
| 4 | Score influencers | ✅ Working |
| 4 | Push results to Notion | 🔄 Next |

## Files

| File | Purpose | Status |
|------|---------|--------|
| `core/twitter_scraper.py` | Collects tweets | ✅ Exists |
| `ml_engine/export_tweets.py` | Export to CSV | ✅ Ready |
| `ml_engine/mock_tweets.py` | Test data | ✅ Ready |
| `data/tweets_mock.csv` | 400 mock tweets | ✅ Generated |
| `data/tweets_history.csv` | Real tweets | ⏳ Awaiting DB |

## Next Steps

1. **Option A (Quick)**: Use mock data, continue scoring + Notion integration
2. **Option B (Complete)**: Fix Phase 2 scraper persistence → populate DB → export real tweets

**Recommend**: Option A now, Option B in Phase 4b (Week 2)

---

**Decision**: 🎯 Continue with mock data for now, Notion integration next
