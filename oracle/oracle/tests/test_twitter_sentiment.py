"""
Tests for Twitter sentiment analyzer integration.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch

from oracle.core.twitter_sentiment_analyzer import (
    TwitterSentimentAnalyzer,
    SentimentResult
)


class TestTwitterSentimentAnalyzer:
    """Test sentiment analyzer."""
    
    @patch('oracle.core.twitter_sentiment_analyzer.CamofoxClient')
    @patch('oracle.core.twitter_sentiment_analyzer.anthropic.Anthropic')
    def test_init(self, mock_claude, mock_camofox):
        """Test analyzer initialization."""
        analyzer = TwitterSentimentAnalyzer()
        
        assert analyzer.camofox is not None
        assert analyzer.claude_client is not None
        assert analyzer.claude_model == "claude-sonnet-4-5-20250929"
    
    @patch('oracle.core.twitter_sentiment_analyzer.CamofoxClient')
    @patch('oracle.core.twitter_sentiment_analyzer.anthropic.Anthropic')
    def test_extract_tweets_from_snapshot(self, mock_claude, mock_camofox):
        """Test tweet extraction."""
        analyzer = TwitterSentimentAnalyzer()
        
        snapshot = {
            "tabId": "tab-123",
            "elements": [
                {
                    "tag": "article",
                    "text": "Bitcoin price up 5%",
                    "className": "tweet"
                },
                {
                    "tag": "article",
                    "text": "Ethereum breaking new highs",
                    "className": "tweet"
                },
                {
                    "tag": "div",
                    "text": "Short text",  # Should be filtered
                }
            ]
        }
        
        tweets = analyzer._extract_tweets_from_snapshot(snapshot)
        
        assert len(tweets) == 2
        assert "Bitcoin" in tweets[0]
        assert "Ethereum" in tweets[1]
    
    @patch('oracle.core.twitter_sentiment_analyzer.CamofoxClient')
    @patch('oracle.core.twitter_sentiment_analyzer.anthropic.Anthropic')
    def test_analyze_with_claude(self, mock_claude, mock_camofox):
        """Test Claude sentiment analysis."""
        # Mock Claude response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "sentiment_score": 0.75,
            "sentiment_label": "bullish",
            "confidence": 0.85,
            "key_themes": ["price_increase", "adoption"]
        })
        
        mock_claude_instance = Mock()
        mock_claude_instance.messages.create.return_value = mock_response
        mock_claude.return_value = mock_claude_instance
        
        analyzer = TwitterSentimentAnalyzer()
        
        tweets = ["Bitcoin up 50%", "Ethereum adoption increasing"]
        result = analyzer._analyze_with_claude("bitcoin", tweets)
        
        assert result["sentiment_score"] == 0.75
        assert result["sentiment_label"] == "bullish"
        assert result["confidence"] == 0.85
        assert len(result["key_themes"]) == 2
    
    @patch('oracle.core.twitter_sentiment_analyzer.CamofoxClient')
    @patch('oracle.core.twitter_sentiment_analyzer.anthropic.Anthropic')
    def test_analyze_sentiment(self, mock_claude, mock_camofox):
        """Test full sentiment analysis flow."""
        # Mock Camofox
        mock_camofox_instance = Mock()
        mock_camofox_instance.create_tab.return_value = "tab-123"
        mock_camofox_instance.get_snapshot.return_value = {
            "tabId": "tab-123",
            "elements": [
                {
                    "tag": "article",
                    "text": "Bitcoin surging 10% today",
                    "className": "tweet"
                }
            ]
        }
        mock_camofox.return_value = mock_camofox_instance
        
        # Mock Claude
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "sentiment_score": 0.8,
            "sentiment_label": "bullish",
            "confidence": 0.9,
            "key_themes": ["price_increase"]
        })
        
        mock_claude_instance = Mock()
        mock_claude_instance.messages.create.return_value = mock_response
        mock_claude.return_value = mock_claude_instance
        
        analyzer = TwitterSentimentAnalyzer()
        result = analyzer.analyze_sentiment("bitcoin")
        
        assert isinstance(result, SentimentResult)
        assert result.query == "bitcoin"
        assert result.sentiment_label == "bullish"
        assert result.sentiment_score == 0.8
        assert result.confidence == 0.9
        assert result.tweet_count == 1
        
        # Verify cleanup
        mock_camofox_instance.close_tab.assert_called_once_with("tab-123")
    
    @patch('oracle.core.twitter_sentiment_analyzer.CamofoxClient')
    @patch('oracle.core.twitter_sentiment_analyzer.anthropic.Anthropic')
    def test_analyze_multiple(self, mock_claude, mock_camofox):
        """Test analyzing multiple queries."""
        mock_camofox_instance = Mock()
        mock_camofox_instance.create_tab.return_value = "tab-123"
        mock_camofox_instance.get_snapshot.return_value = {
            "tabId": "tab-123",
            "elements": [
                {"tag": "article", "text": "Sample tweet", "className": "tweet"}
            ]
        }
        mock_camofox.return_value = mock_camofox_instance
        
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "sentiment_score": 0.5,
            "sentiment_label": "neutral",
            "confidence": 0.7,
            "key_themes": []
        })
        
        mock_claude_instance = Mock()
        mock_claude_instance.messages.create.return_value = mock_response
        mock_claude.return_value = mock_claude_instance
        
        analyzer = TwitterSentimentAnalyzer()
        results = analyzer.analyze_multiple(["bitcoin", "ethereum"])
        
        assert len(results) == 2
        assert "bitcoin" in results
        assert "ethereum" in results
        assert all(r is not None for r in results.values())
    
    @patch('oracle.core.twitter_sentiment_analyzer.CamofoxClient')
    @patch('oracle.core.twitter_sentiment_analyzer.anthropic.Anthropic')
    def test_get_summary(self, mock_claude, mock_camofox):
        """Test generating sentiment summary."""
        results = {
            "bitcoin": SentimentResult(
                query="bitcoin",
                sentiment_score=0.7,
                sentiment_label="bullish",
                confidence=0.8,
                key_themes=["price_increase"],
                tweet_count=25,
                analyzed_at=datetime.now(),
                raw_snapshot={}
            ),
            "ethereum": SentimentResult(
                query="ethereum",
                sentiment_score=-0.5,
                sentiment_label="bearish",
                confidence=0.75,
                key_themes=["price_decrease"],
                tweet_count=20,
                analyzed_at=datetime.now(),
                raw_snapshot={}
            ),
            "ripple": SentimentResult(
                query="ripple",
                sentiment_score=0.1,
                sentiment_label="neutral",
                confidence=0.6,
                key_themes=[],
                tweet_count=15,
                analyzed_at=datetime.now(),
                raw_snapshot={}
            )
        }
        
        analyzer = TwitterSentimentAnalyzer()
        summary = analyzer.get_summary(results)
        
        assert "overall_sentiment" in summary
        assert summary["bullish_count"] == 1
        assert summary["bearish_count"] == 1
        assert summary["neutral_count"] == 1
        assert summary["average_score"] == pytest.approx(0.1, abs=0.01)


class TestSentimentIntegration:
    """Integration tests for sentiment analyzer."""
    
    @patch('oracle.core.twitter_sentiment_analyzer.CamofoxClient')
    @patch('oracle.core.twitter_sentiment_analyzer.anthropic.Anthropic')
    def test_full_sentiment_pipeline(self, mock_claude, mock_camofox):
        """Test complete sentiment analysis pipeline."""
        # Setup mocks
        mock_camofox_instance = Mock()
        mock_camofox_instance.create_tab.return_value = "tab-123"
        mock_camofox_instance.get_snapshot.return_value = {
            "tabId": "tab-123",
            "elements": [
                {"tag": "article", "text": "Bitcoin bull market continues", "className": "tweet"},
                {"tag": "article", "text": "Ethereum adoption accelerating", "className": "tweet"},
                {"tag": "article", "text": "Crypto regulation improving", "className": "tweet"},
            ]
        }
        mock_camofox.return_value = mock_camofox_instance
        
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "sentiment_score": 0.85,
            "sentiment_label": "bullish",
            "confidence": 0.95,
            "key_themes": ["bull_market", "adoption", "regulation"]
        })
        
        mock_claude_instance = Mock()
        mock_claude_instance.messages.create.return_value = mock_response
        mock_claude.return_value = mock_claude_instance
        
        analyzer = TwitterSentimentAnalyzer()
        result = analyzer.analyze_sentiment("crypto bull market")
        
        # Verify result quality
        assert result.sentiment_score == 0.85
        assert result.sentiment_label == "bullish"
        assert result.tweet_count == 3
        assert len(result.key_themes) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
