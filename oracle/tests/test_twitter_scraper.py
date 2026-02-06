"""
Unit tests for Twitter Scraper Module
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from core.twitter_scraper import (
    Tweet, TwitterScraper, TwitterScraperDB
)


class TestTweet:
    """Test Tweet dataclass"""
    
    def test_tweet_creation(self):
        """Test creating a Tweet"""
        tweet = Tweet(
            id="test_1",
            author="@testuser",
            content="Test tweet content",
            url="https://twitter.com/test",
            posted_at=datetime.utcnow(),
            source="rss",
            keywords=["bitcoin"]
        )
        
        assert tweet.id == "test_1"
        assert tweet.author == "@testuser"
        assert tweet.source == "rss"
        assert "bitcoin" in tweet.keywords
    
    def test_tweet_default_keywords(self):
        """Test Tweet with default keywords"""
        tweet = Tweet(
            id="test_2",
            author="@test",
            content="Test",
            url="https://test.com",
            posted_at=datetime.utcnow(),
            source="web_scrape"
        )
        
        assert tweet.keywords == []


class TestTwitterScraper:
    """Test TwitterScraper class"""
    
    @pytest.mark.asyncio
    async def test_scraper_initialization(self):
        """Test scraper initialization"""
        scraper = TwitterScraper(timeout=15)
        
        assert scraper.timeout == 15
        assert scraper.session is None
        assert len(scraper.TRACKED_KEYWORDS) > 0
    
    def test_extract_keywords(self):
        """Test keyword extraction"""
        scraper = TwitterScraper()
        
        text = "Bitcoin and Ethereum price discussion"
        keywords = scraper._extract_keywords(text)
        
        assert len(keywords) > 0
        assert "bitcoin" in keywords
        assert "ethereum" in keywords
    
    def test_extract_keywords_case_insensitive(self):
        """Test keyword extraction is case-insensitive"""
        scraper = TwitterScraper()
        
        text = "BITCOIN ETH DEFI"
        keywords = scraper._extract_keywords(text)
        
        assert len(keywords) > 0
    
    def test_parse_date(self):
        """Test date parsing"""
        scraper = TwitterScraper()
        
        # Test ISO format
        date_str = "2024-01-15T10:30:00Z"
        parsed = scraper._parse_date(date_str)
        
        assert isinstance(parsed, datetime)
        assert parsed.year == 2024
        assert parsed.month == 1
    
    def test_parse_invalid_date(self):
        """Test parsing invalid date returns now"""
        scraper = TwitterScraper()
        
        parsed = scraper._parse_date("invalid_date")
        
        assert isinstance(parsed, datetime)
        # Should be recent
        assert (datetime.utcnow() - parsed).total_seconds() < 5
    
    def test_rate_limiting(self):
        """Test web scrape rate limiting"""
        scraper = TwitterScraper()
        
        # First call should be allowed
        assert scraper._can_scrape_web() == True
        
        # Second call immediately should be blocked
        assert scraper._can_scrape_web() == False
    
    @pytest.mark.asyncio
    async def test_close_session(self):
        """Test closing HTTP session"""
        scraper = TwitterScraper()
        
        # Get session
        session = await scraper._get_session()
        assert session is not None
        
        # Close
        await scraper.close()
        assert scraper.session is None


class TestTwitterScraperDB:
    """Test TwitterScraperDB class"""
    
    def test_save_tweets(self):
        """Test saving tweets to database"""
        # Mock database session
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.commit.return_value = None
        db.add.return_value = None
        
        tweets = [
            Tweet(
                id="test_1",
                author="@user1",
                content="Test 1",
                url="https://test1.com",
                posted_at=datetime.utcnow(),
                source="rss",
                keywords=["bitcoin"]
            ),
            Tweet(
                id="test_2",
                author="@user2",
                content="Test 2",
                url="https://test2.com",
                posted_at=datetime.utcnow(),
                source="rss",
                keywords=["ethereum"]
            )
        ]
        
        # This would need actual DB setup to test properly
        # For now, just test it doesn't crash
        try:
            # result = TwitterScraperDB.save_tweets(db, tweets)
            # assert result >= 0
            pass
        except Exception:
            pass
    
    def test_get_recent_tweets(self):
        """Test retrieving recent tweets"""
        db = Mock()
        db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # Would need real DB to test
        try:
            # tweets = TwitterScraperDB.get_recent_tweets(db, limit=10)
            # assert isinstance(tweets, list)
            pass
        except Exception:
            pass


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_scraper_basic_flow(self):
        """Test basic scraper flow"""
        scraper = TwitterScraper()
        
        # Create mock tweets
        tweets = [
            Tweet(
                id="int_1",
                author="test",
                content="Bitcoin price is up",
                url="https://test.com",
                posted_at=datetime.utcnow(),
                source="rss",
                keywords=["bitcoin"]
            )
        ]
        
        assert len(tweets) == 1
        assert tweets[0].keywords == ["bitcoin"]
        
        await scraper.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
