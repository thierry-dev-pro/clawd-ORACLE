"""
Twitter Scraper Module - Récupère tweets sans API payante
Utilise: RSS feeds, web scraping minimal, sources publiques
Limite: 5-10 tweets/heure (coûts minimaux)
"""
import logging
import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import httpx
from bs4 import BeautifulSoup
import feedparser
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class Tweet:
    """Représentation d'un tweet"""
    id: str
    author: str
    content: str
    url: str
    posted_at: datetime
    source: str  # "rss", "web_scrape", "api"
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


class TwitterScraper:
    """Scraper de tweets minimal - Sources gratuites"""
    
    # Feeds RSS publiques pour crypto news
    RSS_FEEDS = {
        "bitcoin_news": "https://feeds.bloomberg.com/markets/bitcoin.rss",
        "crypto_news": "https://feeds.coindesk.com/api/v1/rss/?category=all",
        "ethereum": "https://feed.ethereum.org/",
        "cryptocurrency": "https://feeds.techcrunch.com/category/cryptocurrency/feed/",
    }
    
    # Sources web à scraper
    WEB_SOURCES = {
        "twitter_search_bitcoin": "https://nitter.net/search?q=bitcoin&f=tweets&since:",
        "twitter_search_ethereum": "https://nitter.net/search?q=ethereum&f=tweets&since:",
    }
    
    # Keywords de suivi
    TRACKED_KEYWORDS = {
        "bitcoin": ["btc", "bitcoin", "blockchain"],
        "ethereum": ["eth", "ethereum", "evm", "defi"],
        "crypto": ["crypto", "cryptocurrency", "token", "altcoin"],
        "defi": ["defi", "decentralized finance", "yield farming"],
        "nft": ["nft", "nfts", "collectible"],
    }
    
    def __init__(self, timeout: int = 10):
        """
        Initialize scraper
        
        Args:
            timeout: Timeout HTTP en secondes
        """
        self.timeout = timeout
        self.session = None
        self.last_scrape = {}
        logger.info("✅ TwitterScraper initialized")
    
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session"""
        if self.session is None:
            self.session = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
        return self.session
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def scrape_rss_feeds(self) -> List[Tweet]:
        """
        Scrape RSS feeds pour tweets/news crypto
        
        Returns:
            List of tweets
        """
        tweets = []
        
        for feed_name, feed_url in self.RSS_FEEDS.items():
            try:
                logger.info(f"📡 Scraping RSS feed: {feed_name}")
                
                # Parse feed
                feed = feedparser.parse(feed_url)
                
                if feed.bozo:
                    logger.warning(f"⚠️ Feed parsing warning for {feed_name}")
                
                # Limite: prendre les 3-5 derniers articles
                for entry in feed.entries[:5]:
                    try:
                        tweet = Tweet(
                            id=entry.get('id', entry.get('link', '')),
                            author=entry.get('author', 'Unknown'),
                            content=entry.get('title', '') + "\n" + entry.get('summary', ''),
                            url=entry.get('link', ''),
                            posted_at=self._parse_date(entry.get('published', '')),
                            source="rss",
                            keywords=self._extract_keywords(entry.get('title', ''))
                        )
                        
                        # Filtre: au moins un keyword trouvé
                        if tweet.keywords:
                            tweets.append(tweet)
                            logger.info(f"✅ RSS tweet found: {tweet.author}")
                    
                    except Exception as e:
                        logger.warning(f"Error parsing entry: {e}")
                        continue
            
            except Exception as e:
                logger.error(f"❌ Error scraping RSS {feed_name}: {e}")
                continue
        
        logger.info(f"📊 Collected {len(tweets)} tweets from RSS feeds")
        return tweets
    
    async def scrape_nitter(self, query: str, limit: int = 5) -> List[Tweet]:
        """
        Scrape Nitter (instance libre de Twitter)
        Nitter: https://github.com/zedeus/nitter - instance publique libre
        
        Args:
            query: Search query
            limit: Max tweets
        
        Returns:
            List of tweets
        """
        tweets = []
        
        try:
            session = await self._get_session()
            
            # Utilise instance publique de Nitter
            nitter_instance = "https://nitter.net"
            search_url = f"{nitter_instance}/search?q={query}&f=tweets&since:1d"
            
            logger.info(f"🔍 Scraping Nitter: {query}")
            
            response = await session.get(search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find tweets
            tweet_elements = soup.find_all('div', class_='tweet')[:limit]
            
            for elem in tweet_elements:
                try:
                    # Extract fields
                    author_elem = elem.find('a', class_='username')
                    content_elem = elem.find('div', class_='tweet-text')
                    date_elem = elem.find('span', class_='tweet-date')
                    
                    if not all([author_elem, content_elem]):
                        continue
                    
                    author = author_elem.text if author_elem else "Unknown"
                    content = content_elem.text if content_elem else ""
                    posted_at = self._parse_date(date_elem.get('title', '') if date_elem else '')
                    
                    tweet = Tweet(
                        id=f"nitter_{query}_{len(tweets)}",
                        author=author,
                        content=content,
                        url=f"{nitter_instance}{author_elem.get('href', '')}",
                        posted_at=posted_at,
                        source="web_scrape",
                        keywords=self._extract_keywords(content)
                    )
                    
                    if tweet.keywords:
                        tweets.append(tweet)
                        logger.info(f"✅ Nitter tweet: {author}")
                
                except Exception as e:
                    logger.warning(f"Error parsing tweet element: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"❌ Error scraping Nitter: {e}")
        
        logger.info(f"📊 Collected {len(tweets)} tweets from Nitter")
        return tweets
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract relevant keywords from text
        
        Args:
            text: Text to analyze
        
        Returns:
            List of matched keywords
        """
        keywords = []
        text_lower = text.lower()
        
        for category, terms in self.TRACKED_KEYWORDS.items():
            for term in terms:
                if term in text_lower:
                    keywords.append(category)
                    break
        
        return keywords
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string to datetime
        
        Args:
            date_str: Date string
        
        Returns:
            Datetime object or now()
        """
        try:
            # Essaie formats courants
            for fmt in [
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S",
                "%d %b %Y",
                "%a, %d %b %Y %H:%M:%S",
            ]:
                try:
                    return datetime.strptime(date_str.split('+')[0].split('Z')[0][:19], fmt[:19])
                except:
                    continue
        except:
            pass
        
        return datetime.utcnow()
    
    async def scrape_all_sources(self) -> List[Tweet]:
        """
        Scrape all sources pour tweets
        Rate limit: max 10 tweets/heure
        
        Returns:
            List of tweets
        """
        try:
            tweets = []
            
            # RSS feeds (toujours OK)
            rss_tweets = await self.scrape_rss_feeds()
            tweets.extend(rss_tweets)
            
            # Nitter scraping (avec rate limiting)
            if self._can_scrape_web():
                for query in ["bitcoin", "ethereum", "crypto"]:
                    nitter_tweets = await self.scrape_nitter(query, limit=3)
                    tweets.extend(nitter_tweets)
            
            # Déduplique par URL/ID
            unique_tweets = {}
            for tweet in tweets:
                key = tweet.id or tweet.url
                if key not in unique_tweets:
                    unique_tweets[key] = tweet
            
            tweets = list(unique_tweets.values())
            
            # Limite finale: 10 tweets max
            tweets = tweets[:10]
            
            logger.info(f"🎯 Total tweets scraped: {len(tweets)}")
            return tweets
        
        except Exception as e:
            logger.error(f"❌ Error in scrape_all_sources: {e}")
            return []
    
    def _can_scrape_web(self) -> bool:
        """
        Check rate limiting for web scraping
        Max 5-10 tweets/heure = max 1 scrape all/10-12 minutes
        
        Returns:
            True if can scrape, False if rate limited
        """
        now = datetime.utcnow()
        last_web_scrape = self.last_scrape.get('web_scrape', datetime.utcnow() - timedelta(hours=1))
        
        can_scrape = (now - last_web_scrape).total_seconds() > 600  # 10 minutes
        
        if can_scrape:
            self.last_scrape['web_scrape'] = now
        
        return can_scrape


class TwitterScraperDB:
    """Database operations pour tweets"""
    
    @staticmethod
    def save_tweets(db: Session, tweets: List[Tweet]) -> int:
        """
        Save tweets to database
        
        Args:
            db: Database session
            tweets: Tweets to save
        
        Returns:
            Number of tweets saved
        """
        from core.models import TweetModel
        
        count = 0
        try:
            for tweet in tweets:
                # Check if already exists
                existing = db.query(TweetModel).filter(
                    TweetModel.url == tweet.url
                ).first()
                
                if existing:
                    logger.debug(f"Tweet already exists: {tweet.url}")
                    continue
                
                # Save new tweet
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
                    indexed_at=datetime.utcnow()
                )
                db.add(db_tweet)
                count += 1
            
            db.commit()
            logger.info(f"✅ Saved {count} tweets to database")
            return count
        
        except Exception as e:
            logger.error(f"❌ Error saving tweets: {e}")
            db.rollback()
            return 0
    
    @staticmethod
    def get_recent_tweets(db: Session, limit: int = 10) -> List[Dict]:
        """
        Get recent tweets from database
        
        Args:
            db: Database session
            limit: Max tweets
        
        Returns:
            List of tweets
        """
        from core.models import TweetModel
        
        try:
            tweets = db.query(TweetModel).order_by(
                TweetModel.posted_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": t.id,
                    "author": t.author,
                    "content": t.content[:200],
                    "url": t.url,
                    "posted_at": t.posted_at.isoformat(),
                    "source": t.source,
                    "likes": t.likes,
                    "keywords": t.keywords
                }
                for t in tweets
            ]
        
        except Exception as e:
            logger.error(f"❌ Error fetching tweets: {e}")
            return []
    
    @staticmethod
    def search_tweets(db: Session, keyword: str, limit: int = 10) -> List[Dict]:
        """
        Search tweets by keyword
        
        Args:
            db: Database session
            keyword: Keyword to search
            limit: Max results
        
        Returns:
            List of matching tweets
        """
        from core.models import TweetModel
        
        try:
            tweets = db.query(TweetModel).filter(
                TweetModel.keywords.contains([keyword.lower()])
            ).order_by(
                TweetModel.posted_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": t.id,
                    "author": t.author,
                    "content": t.content[:200],
                    "url": t.url,
                    "posted_at": t.posted_at.isoformat(),
                    "keywords": t.keywords
                }
                for t in tweets
            ]
        
        except Exception as e:
            logger.error(f"❌ Error searching tweets: {e}")
            return []
    
    @staticmethod
    def cleanup_old_tweets(db: Session, days: int = 7) -> int:
        """
        Delete old tweets (older than X days)
        
        Args:
            db: Database session
            days: Keep tweets from last N days
        
        Returns:
            Number of deleted tweets
        """
        from core.models import TweetModel
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            deleted = db.query(TweetModel).filter(
                TweetModel.posted_at < cutoff_date
            ).delete()
            
            db.commit()
            logger.info(f"✅ Cleaned up {deleted} old tweets")
            return deleted
        
        except Exception as e:
            logger.error(f"❌ Error cleaning tweets: {e}")
            db.rollback()
            return 0


# Global instance
twitter_scraper = TwitterScraper()
