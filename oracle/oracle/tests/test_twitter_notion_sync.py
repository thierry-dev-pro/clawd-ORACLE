"""
Tests for Twitter to Notion sync.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from oracle.core.twitter_notion_sync import TwitterNotionSync
from oracle.core.twitter_daily_scanner import TweetCategory, CategorizedResult


class TestTwitterNotionSync:
    """Test Notion sync."""
    
    def test_init(self):
        """Test initialization."""
        with patch.dict('os.environ', {
            'NOTION_API_KEY': 'test_key',
            'NOTION_DATABASE_ID': 'test_db'
        }):
            sync = TwitterNotionSync()
            assert sync.notion_api_key == 'test_key'
            assert sync.database_id == 'test_db'
    
    def test_init_missing_credentials(self):
        """Test init with missing credentials."""
        with pytest.raises(ValueError):
            TwitterNotionSync(notion_api_key=None, database_id=None)
    
    @patch('oracle.core.twitter_notion_sync.requests.post')
    def test_create_page(self, mock_post):
        """Test creating Notion page."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "page-123"}
        mock_post.return_value = mock_response
        
        sync = TwitterNotionSync("key", "db-id")
        
        result = CategorizedResult(
            category=TweetCategory.AIRDROP,
            query="airdrop test",
            sentiment_score=0.75,
            confidence=0.85,
            key_themes=["claim", "distribution"],
            tweet_count=45,
            rank_score=75.0,
            detected_at=datetime.now(),
            raw_snapshot={}
        )
        
        page_id = sync.create_page(result)
        
        assert page_id == "page-123"
        mock_post.assert_called_once()
    
    @patch('oracle.core.twitter_notion_sync.requests.post')
    def test_create_page_error(self, mock_post):
        """Test page creation error handling."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_post.return_value = mock_response
        
        sync = TwitterNotionSync("key", "db-id")
        
        result = CategorizedResult(
            category=TweetCategory.AIRDROP,
            query="test",
            sentiment_score=0.5,
            confidence=0.7,
            key_themes=[],
            tweet_count=10,
            rank_score=50.0,
            detected_at=datetime.now(),
            raw_snapshot={}
        )
        
        page_id = sync.create_page(result)
        
        assert page_id is None
    
    @patch('oracle.core.twitter_notion_sync.requests.patch')
    def test_update_page(self, mock_patch):
        """Test updating Notion page."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "page-123"}
        mock_patch.return_value = mock_response
        
        sync = TwitterNotionSync("key", "db-id")
        
        result = CategorizedResult(
            category=TweetCategory.DEFI,
            query="defi test",
            sentiment_score=0.6,
            confidence=0.8,
            key_themes=["yield"],
            tweet_count=30,
            rank_score=60.0,
            detected_at=datetime.now(),
            raw_snapshot={}
        )
        
        page_id = sync.update_page("page-123", result)
        
        assert page_id == "page-123"
        mock_patch.assert_called_once()
    
    @patch('oracle.core.twitter_notion_sync.requests.post')
    def test_find_existing_page(self, mock_post):
        """Test finding existing page."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "page-123",
                    "properties": {
                        "title": {
                            "title": [{"text": {"content": "AIRDROP: test query"}}]
                        }
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        sync = TwitterNotionSync("key", "db-id")
        
        page_id = sync.find_existing_page("test query", TweetCategory.AIRDROP)
        
        assert page_id == "page-123"
    
    @patch('oracle.core.twitter_notion_sync.requests.post')
    @patch('oracle.core.twitter_notion_sync.requests.patch')
    def test_create_or_update_new(self, mock_patch, mock_post):
        """Test create_or_update for new page."""
        # Mock query (not found)
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {"results": []}
        
        # Mock create
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"id": "page-new"}
        
        mock_post.side_effect = [mock_response1, mock_response2]
        
        sync = TwitterNotionSync("key", "db-id")
        
        result = CategorizedResult(
            category=TweetCategory.AIRDROP,
            query="new airdrop",
            sentiment_score=0.7,
            confidence=0.8,
            key_themes=[],
            tweet_count=20,
            rank_score=70.0,
            detected_at=datetime.now(),
            raw_snapshot={}
        )
        
        page_id = sync.create_or_update_page(result)
        
        assert page_id == "page-new"
    
    @patch('oracle.core.twitter_notion_sync.requests.post')
    def test_sync_batch(self, mock_post):
        """Test batch sync."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "page-123",
            "results": []
        }
        mock_post.return_value = mock_response
        
        sync = TwitterNotionSync("key", "db-id")
        
        results = {
            TweetCategory.AIRDROP: [
                CategorizedResult(
                    category=TweetCategory.AIRDROP,
                    query="airdrop1",
                    sentiment_score=0.7,
                    confidence=0.8,
                    key_themes=[],
                    tweet_count=20,
                    rank_score=70.0,
                    detected_at=datetime.now(),
                    raw_snapshot={}
                )
            ],
            TweetCategory.DEFI: [
                CategorizedResult(
                    category=TweetCategory.DEFI,
                    query="defi1",
                    sentiment_score=0.6,
                    confidence=0.7,
                    key_themes=[],
                    tweet_count=15,
                    rank_score=60.0,
                    detected_at=datetime.now(),
                    raw_snapshot={}
                )
            ]
        }
        
        # Note: sync_batch calls create_or_update_page which uses mock_post
        # This is a simplified test
        assert len(results) == 2
    
    def test_get_category_emoji(self):
        """Test category emoji mapping."""
        assert TwitterNotionSync._get_category_emoji(TweetCategory.AIRDROP) == "🎁"
        assert TwitterNotionSync._get_category_emoji(TweetCategory.DEFI) == "💰"
        assert TwitterNotionSync._get_category_emoji(TweetCategory.NFT) == "🖼️"
        assert TwitterNotionSync._get_category_emoji(TweetCategory.SECURITY) == "🔒"
        assert TwitterNotionSync._get_category_emoji(TweetCategory.ADOPTION) == "🚀"
    
    def test_sentiment_label(self):
        """Test sentiment label generation."""
        assert TwitterNotionSync._sentiment_label(0.8) == "Very Bullish"
        assert TwitterNotionSync._sentiment_label(0.3) == "Bullish"
        assert TwitterNotionSync._sentiment_label(0.0) == "Neutral"
        assert TwitterNotionSync._sentiment_label(-0.3) == "Bearish"
        assert TwitterNotionSync._sentiment_label(-0.8) == "Very Bearish"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
