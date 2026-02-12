"""
Tests for Twitter daily scanner with categorization and ranking.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from oracle.core.twitter_daily_scanner import (
    TwitterDailyScanner,
    TweetCategory,
    CategoryClassifier,
    ResultRanker,
    CategorizedResult
)


class TestCategoryClassifier:
    """Test category classifier."""
    
    def test_init(self):
        """Test classifier initialization."""
        classifier = CategoryClassifier()
        assert len(classifier.CATEGORY_KEYWORDS) > 0
    
    def test_classify_airdrop(self):
        """Test airdrop classification."""
        classifier = CategoryClassifier()
        
        category, confidence = classifier.classify(
            "free airdrop distribution",
            ["claim", "eligibility", "whitelist"]
        )
        
        assert category == TweetCategory.AIRDROP
        assert confidence > 0.5
    
    def test_classify_defi(self):
        """Test DeFi classification."""
        classifier = CategoryClassifier()
        
        category, confidence = classifier.classify(
            "defi yield farming opportunity",
            ["liquidity pool", "aave", "compound"]
        )
        
        assert category == TweetCategory.DEFI
        assert confidence > 0.5
    
    def test_classify_nft(self):
        """Test NFT classification."""
        classifier = CategoryClassifier()
        
        category, confidence = classifier.classify(
            "nft collection mint",
            ["opensea", "collection", "pfp"]
        )
        
        assert category == TweetCategory.NFT
        assert confidence > 0.5
    
    def test_classify_security(self):
        """Test security classification."""
        classifier = CategoryClassifier()
        
        category, confidence = classifier.classify(
            "smart contract security audit",
            ["vulnerability", "audit", "fix"]
        )
        
        assert category == TweetCategory.SECURITY
        assert confidence > 0.5
    
    def test_get_category_for_query(self):
        """Test getting category from query alone."""
        classifier = CategoryClassifier()
        
        # Airdrop query
        cat = classifier.get_category_for_query("airdrop distribution")
        assert cat == TweetCategory.AIRDROP
        
        # DeFi query
        cat = classifier.get_category_for_query("defi protocol yield")
        assert cat == TweetCategory.DEFI


class TestResultRanker:
    """Test result ranking."""
    
    def test_calculate_rank_score_bullish(self):
        """Test ranking bullish sentiment."""
        score = ResultRanker.calculate_rank_score(
            sentiment_score=0.8,
            confidence=0.9,
            tweet_count=50
        )
        
        assert score > 60
        assert score <= 100
    
    def test_calculate_rank_score_bearish(self):
        """Test ranking bearish sentiment."""
        score = ResultRanker.calculate_rank_score(
            sentiment_score=-0.8,
            confidence=0.9,
            tweet_count=50
        )
        
        assert score < 50
    
    def test_calculate_rank_score_neutral(self):
        """Test ranking neutral sentiment."""
        score = ResultRanker.calculate_rank_score(
            sentiment_score=0.0,
            confidence=0.5,
            tweet_count=10
        )
        
        assert 20 < score < 50
    
    def test_rank_results(self):
        """Test ranking multiple results."""
        results = [
            CategorizedResult(
                category=TweetCategory.AIRDROP,
                query="airdrop1",
                sentiment_score=0.3,
                confidence=0.7,
                key_themes=["claim"],
                tweet_count=30,
                rank_score=40.0,
                detected_at=datetime.now(),
                raw_snapshot={}
            ),
            CategorizedResult(
                category=TweetCategory.AIRDROP,
                query="airdrop2",
                sentiment_score=0.8,
                confidence=0.9,
                key_themes=["distribution"],
                tweet_count=50,
                rank_score=80.0,
                detected_at=datetime.now(),
                raw_snapshot={}
            ),
            CategorizedResult(
                category=TweetCategory.DEFI,
                query="defi",
                sentiment_score=0.5,
                confidence=0.8,
                key_themes=["yield"],
                tweet_count=40,
                rank_score=60.0,
                detected_at=datetime.now(),
                raw_snapshot={}
            )
        ]
        
        ranked = ResultRanker.rank_results(results)
        
        # Should be sorted by rank_score descending
        assert ranked[0].rank_score == 80.0
        assert ranked[1].rank_score == 60.0
        assert ranked[2].rank_score == 40.0


class TestTwitterDailyScanner:
    """Test Twitter daily scanner."""
    
    @patch('oracle.core.twitter_daily_scanner.TwitterSentimentAnalyzer')
    def test_init(self, mock_analyzer):
        """Test scanner initialization."""
        scanner = TwitterDailyScanner()
        
        assert scanner.analyzer is not None
        assert scanner.classifier is not None
        assert scanner.ranker is not None
    
    @patch('oracle.core.twitter_daily_scanner.TwitterSentimentAnalyzer')
    def test_scan_daily(self, mock_analyzer):
        """Test daily scan execution."""
        # Setup mock
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        
        # Mock sentiment results
        from oracle.core.twitter_sentiment_analyzer import SentimentResult
        
        mock_analyzer_instance.analyze_multiple.return_value = {
            "airdrop query": SentimentResult(
                query="airdrop query",
                sentiment_score=0.7,
                sentiment_label="bullish",
                confidence=0.85,
                key_themes=["distribution", "claim"],
                tweet_count=45,
                analyzed_at=datetime.now(),
                raw_snapshot={}
            ),
            "defi query": SentimentResult(
                query="defi query",
                sentiment_score=0.5,
                sentiment_label="neutral",
                confidence=0.7,
                key_themes=["yield", "pool"],
                tweet_count=35,
                analyzed_at=datetime.now(),
                raw_snapshot={}
            )
        }
        
        scanner = TwitterDailyScanner()
        results = scanner.scan_daily(
            queries=["airdrop query", "defi query"]
        )
        
        # Check results
        assert len(results) > 0
        assert any(TweetCategory.AIRDROP in results 
                   or TweetCategory.DEFI in results)
    
    @patch('oracle.core.twitter_daily_scanner.TwitterSentimentAnalyzer')
    def test_get_top_by_category(self, mock_analyzer):
        """Test getting top results per category."""
        scanner = TwitterDailyScanner()
        
        by_category = {
            TweetCategory.AIRDROP: [
                CategorizedResult(
                    category=TweetCategory.AIRDROP,
                    query=f"airdrop{i}",
                    sentiment_score=0.5 + i*0.1,
                    confidence=0.7,
                    key_themes=["claim"],
                    tweet_count=30,
                    rank_score=50.0 + i*10,
                    detected_at=datetime.now(),
                    raw_snapshot={}
                )
                for i in range(5)
            ],
            TweetCategory.DEFI: [
                CategorizedResult(
                    category=TweetCategory.DEFI,
                    query=f"defi{i}",
                    sentiment_score=0.4,
                    confidence=0.6,
                    key_themes=["yield"],
                    tweet_count=25,
                    rank_score=40.0 + i*5,
                    detected_at=datetime.now(),
                    raw_snapshot={}
                )
                for i in range(3)
            ]
        }
        
        top = scanner.get_top_by_category(by_category, top_n=2)
        
        assert len(top[TweetCategory.AIRDROP]) == 2
        assert len(top[TweetCategory.DEFI]) == 2
    
    @patch('oracle.core.twitter_daily_scanner.TwitterSentimentAnalyzer')
    def test_format_for_notion(self, mock_analyzer):
        """Test formatting for Notion."""
        scanner = TwitterDailyScanner()
        
        results = {
            TweetCategory.AIRDROP: [
                CategorizedResult(
                    category=TweetCategory.AIRDROP,
                    query="airdrop test",
                    sentiment_score=0.7,
                    confidence=0.85,
                    key_themes=["claim", "distribution"],
                    tweet_count=45,
                    rank_score=70.0,
                    detected_at=datetime.now(),
                    raw_snapshot={}
                )
            ]
        }
        
        notion_data = scanner.format_for_notion(results)
        
        assert len(notion_data) == 1
        assert "airdrop test" in notion_data[0]["title"]
        assert notion_data[0]["category"] == "airdrop"
        assert notion_data[0]["sentiment"] == "🚀"  # Bullish emoji


class TestSentimentEmoji:
    """Test sentiment emoji generation."""
    
    @patch('oracle.core.twitter_daily_scanner.TwitterSentimentAnalyzer')
    def test_emoji_bullish(self, mock_analyzer):
        """Test bullish emoji."""
        scanner = TwitterDailyScanner()
        
        assert scanner._sentiment_emoji(0.8) == "🚀"
        assert scanner._sentiment_emoji(0.6) == "🚀"
    
    @patch('oracle.core.twitter_daily_scanner.TwitterSentimentAnalyzer')
    def test_emoji_slightly_bullish(self, mock_analyzer):
        """Test slightly bullish emoji."""
        scanner = TwitterDailyScanner()
        
        assert scanner._sentiment_emoji(0.3) == "📈"
    
    @patch('oracle.core.twitter_daily_scanner.TwitterSentimentAnalyzer')
    def test_emoji_neutral(self, mock_analyzer):
        """Test neutral emoji."""
        scanner = TwitterDailyScanner()
        
        assert scanner._sentiment_emoji(0.0) == "➡️"
        assert scanner._sentiment_emoji(0.05) == "➡️"
    
    @patch('oracle.core.twitter_daily_scanner.TwitterSentimentAnalyzer')
    def test_emoji_bearish(self, mock_analyzer):
        """Test bearish emoji."""
        scanner = TwitterDailyScanner()
        
        assert scanner._sentiment_emoji(-0.8) == "📉"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
