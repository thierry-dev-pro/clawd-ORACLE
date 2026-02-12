"""
Twitter Daily Scanner - Scan crypto tweets once per day with categorization.
Fetches tweets, categorizes by topic (DeFi, Airdrop, etc.), ranks, and pushes to Notion.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .twitter_sentiment_analyzer import TwitterSentimentAnalyzer, SentimentResult
from .camofox_anti_detection import AntiDetectionPool

logger = logging.getLogger(__name__)


class TweetCategory(str, Enum):
    """Tweet categories for crypto market."""
    AIRDROP = "airdrop"
    DEFI = "defi"
    NFT = "nft"
    EXCHANGE = "exchange"
    WALLET = "wallet"
    GOVERNANCE = "governance"
    SECURITY = "security"
    PRICE = "price"
    ADOPTION = "adoption"
    REGULATION = "regulation"


@dataclass
class CategorizedResult:
    """Categorized and ranked tweet result."""
    category: TweetCategory
    query: str
    sentiment_score: float
    confidence: float
    key_themes: List[str]
    tweet_count: int
    rank_score: float  # Combined score for ranking
    detected_at: datetime
    raw_snapshot: Dict


class CategoryClassifier:
    """Classify tweets into predefined categories."""
    
    CATEGORY_KEYWORDS = {
        TweetCategory.AIRDROP: [
            "airdrop", "claim", "free tokens", "distribute", "allocation",
            "eligibility", "whitelist", "snapshot", "reward distribution"
        ],
        TweetCategory.DEFI: [
            "defi", "decentralized finance", "yield farming", "liquidity pool",
            "swap", "lending protocol", "borrowing", "dex", "amm",
            "compound", "aave", "curve", "uniswap"
        ],
        TweetCategory.NFT: [
            "nft", "non-fungible", "nfts", "digital asset", "collectible",
            "opensea", "blur", "mint", "mint nft", "collection",
            "art", "metaverse", "pfp"
        ],
        TweetCategory.EXCHANGE: [
            "exchange", "coinbase", "kraken", "binance", "gate.io",
            "trading", "listing", "delisting", "ceex"
        ],
        TweetCategory.WALLET: [
            "wallet", "hardware wallet", "ledger", "trezor", "metamask",
            "custodial", "self-custody", "secure", "seed phrase"
        ],
        TweetCategory.GOVERNANCE: [
            "governance", "dao", "vote", "proposal", "voting",
            "snapshot vote", "governance token", "decentralized governance"
        ],
        TweetCategory.SECURITY: [
            "hack", "exploit", "vulnerability", "breach", "scam",
            "security audit", "rug pull", "malware", "phishing",
            "smart contract audit"
        ],
        TweetCategory.PRICE: [
            "price", "pump", "dump", "bullish", "bearish", "rally",
            "atl", "ath", "resistance", "support", "technical analysis",
            "chart analysis"
        ],
        TweetCategory.ADOPTION: [
            "adoption", "mainstream", "integration", "partnership",
            "enterprise", "institutional", "mainstream adoption",
            "real world use case", "utility"
        ],
        TweetCategory.REGULATION: [
            "regulation", "sec", "regulatory", "compliance", "license",
            "legal", "legislation", "cbdc", "government",
            "policy", "enforce"
        ]
    }
    
    def classify(self, query: str, themes: List[str]) -> Tuple[TweetCategory, float]:
        """
        Classify query/themes into category.
        
        Args:
            query: Original search query
            themes: Key themes from sentiment analysis
            
        Returns:
            Tuple of (category, confidence)
        """
        query_lower = query.lower()
        themes_lower = [t.lower() for t in themes]
        combined = f"{query_lower} {' '.join(themes_lower)}"
        
        scores = {}
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in combined)
            scores[category] = matches
        
        # Get category with highest score
        best_category = max(scores, key=scores.get)
        max_score = scores[best_category]
        
        # Calculate confidence (0.0-1.0)
        confidence = min(max_score / len(self.CATEGORY_KEYWORDS[best_category]), 1.0)
        
        return best_category, confidence
    
    def get_category_for_query(self, query: str) -> TweetCategory:
        """Get primary category for query string."""
        query_lower = query.lower()
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                return category
        
        return TweetCategory.PRICE  # Default


class ResultRanker:
    """Rank categorized results by quality score."""
    
    @staticmethod
    def calculate_rank_score(
        sentiment_score: float,
        confidence: float,
        tweet_count: int,
        category_rarity: float = 1.0
    ) -> float:
        """
        Calculate overall rank score.
        
        Args:
            sentiment_score: -1.0 to +1.0
            confidence: 0.0 to 1.0
            tweet_count: Number of tweets analyzed
            category_rarity: How rare/valuable is this category (1.0 = normal)
            
        Returns:
            Rank score (0.0-100.0)
        """
        # Normalize sentiment (-1 to 1 → 0 to 1)
        sentiment_normalized = (sentiment_score + 1) / 2
        
        # Tweet count factor (more = better, but diminishing returns)
        tweet_factor = min(tweet_count / 100, 1.0)
        
        # Combine with weights
        score = (
            sentiment_normalized * 40 +
            confidence * 30 +
            tweet_factor * 20 +
            category_rarity * 10
        )
        
        return min(score, 100.0)
    
    @staticmethod
    def rank_results(results: List[CategorizedResult]) -> List[CategorizedResult]:
        """
        Rank results by score.
        
        Args:
            results: List of categorized results
            
        Returns:
            Sorted list (highest score first)
        """
        return sorted(results, key=lambda r: r.rank_score, reverse=True)


class TwitterDailyScanner:
    """Scan Twitter daily with categorization and ranking."""
    
    # Queries to scan daily
    DEFAULT_QUERIES = [
        # Airdrops
        "airdrop crypto new",
        "free tokens distribution 2024",
        "token claim eligible",
        
        # DeFi
        "defi opportunity yield farming",
        "new defi protocol launch",
        "liquidity pool mining",
        
        # NFTs
        "nft drop announcement",
        "new nft collection mint",
        "nft floor price",
        
        # Trading
        "crypto bullish signal",
        "altcoin pump 2024",
        "technical analysis bitcoin",
        
        # Security
        "smart contract audit completed",
        "security vulnerability fixed",
        
        # Adoption
        "bitcoin institutional adoption",
        "crypto mainstream news",
        "blockchain real world use"
    ]
    
    def __init__(
        self,
        camofox_url: str = "http://localhost:9377",
        proxy_list: Optional[List[str]] = None
    ):
        """
        Initialize daily scanner.
        
        Args:
            camofox_url: Camofox service URL
            proxy_list: Optional proxy list
        """
        self.analyzer = TwitterSentimentAnalyzer(camofox_url)
        self.classifier = CategoryClassifier()
        self.ranker = ResultRanker()
        
        # Optional: use anti-detection pool
        self.pool = AntiDetectionPool(
            pool_size=5,
            camofox_url=camofox_url,
            proxy_list=proxy_list,
            rotation_interval_minutes=60
        ) if proxy_list else None
    
    def scan_daily(
        self,
        queries: Optional[List[str]] = None,
        max_tweets_per_query: int = 50
    ) -> Dict[TweetCategory, List[CategorizedResult]]:
        """
        Scan Twitter with predefined or custom queries.
        
        Args:
            queries: Optional custom query list (default: DEFAULT_QUERIES)
            max_tweets_per_query: Max tweets per query
            
        Returns:
            Dict mapping category to results
        """
        queries = queries or self.DEFAULT_QUERIES
        
        logger.info(f"Starting daily Twitter scan ({len(queries)} queries)")
        
        # Analyze all queries
        sentiment_results = self.analyzer.analyze_multiple(
            queries,
            max_tweets_per_query
        )
        
        # Categorize and rank
        categorized = self._categorize_results(sentiment_results)
        ranked = self.ranker.rank_results(categorized)
        
        # Group by category
        by_category = self._group_by_category(ranked)
        
        logger.info(
            f"Scan complete: {len(categorized)} results, "
            f"{len(by_category)} categories"
        )
        
        return by_category
    
    def _categorize_results(
        self,
        sentiment_results: Dict[str, SentimentResult]
    ) -> List[CategorizedResult]:
        """
        Categorize sentiment results.
        
        Args:
            sentiment_results: Dict from analyzer
            
        Returns:
            List of categorized results
        """
        categorized = []
        
        for query, result in sentiment_results.items():
            if result is None:
                continue
            
            # Classify
            category, confidence = self.classifier.classify(
                query,
                result.key_themes
            )
            
            # Calculate rank score
            rank_score = self.ranker.calculate_rank_score(
                result.sentiment_score,
                result.confidence,
                result.tweet_count
            )
            
            # Create categorized result
            cat_result = CategorizedResult(
                category=category,
                query=query,
                sentiment_score=result.sentiment_score,
                confidence=result.confidence,
                key_themes=result.key_themes,
                tweet_count=result.tweet_count,
                rank_score=rank_score,
                detected_at=result.analyzed_at,
                raw_snapshot=result.raw_snapshot
            )
            
            categorized.append(cat_result)
        
        return categorized
    
    def _group_by_category(
        self,
        results: List[CategorizedResult]
    ) -> Dict[TweetCategory, List[CategorizedResult]]:
        """
        Group results by category.
        
        Args:
            results: List of results (should be ranked)
            
        Returns:
            Dict mapping category to results
        """
        grouped = {}
        
        for result in results:
            if result.category not in grouped:
                grouped[result.category] = []
            
            grouped[result.category].append(result)
        
        return grouped
    
    def get_top_by_category(
        self,
        by_category: Dict[TweetCategory, List[CategorizedResult]],
        top_n: int = 3
    ) -> Dict[TweetCategory, List[CategorizedResult]]:
        """
        Get top N results per category.
        
        Args:
            by_category: Results grouped by category
            top_n: Number of top results per category
            
        Returns:
            Dict with top results per category
        """
        return {
            category: results[:top_n]
            for category, results in by_category.items()
        }
    
    def format_for_notion(
        self,
        results: Dict[TweetCategory, List[CategorizedResult]]
    ) -> List[Dict]:
        """
        Format results for Notion database.
        
        Args:
            results: Grouped and ranked results
            
        Returns:
            List of Notion-compatible dicts
        """
        notion_items = []
        
        for category, category_results in results.items():
            for result in category_results:
                item = {
                    "title": f"{category.value.upper()}: {result.query}",
                    "category": category.value,
                    "query": result.query,
                    "sentiment": self._sentiment_emoji(result.sentiment_score),
                    "sentiment_score": round(result.sentiment_score, 2),
                    "confidence": round(result.confidence, 2),
                    "rank_score": round(result.rank_score, 1),
                    "themes": ", ".join(result.key_themes),
                    "tweet_count": result.tweet_count,
                    "detected_at": result.detected_at.isoformat(),
                    "status": "Active"
                }
                notion_items.append(item)
        
        return notion_items
    
    @staticmethod
    def _sentiment_emoji(score: float) -> str:
        """Get emoji for sentiment score."""
        if score > 0.5:
            return "🚀"  # Bullish
        elif score > 0.1:
            return "📈"  # Slightly bullish
        elif score < -0.5:
            return "📉"  # Bearish
        elif score < -0.1:
            return "⚠️"  # Slightly bearish
        else:
            return "➡️"  # Neutral
    
    def close(self) -> None:
        """Close pool and cleanup."""
        if self.pool:
            self.pool.release_all()


# Example usage
def demo_daily_scan():
    """Demo daily Twitter scan."""
    scanner = TwitterDailyScanner()
    
    # Custom queries
    queries = [
        "airdrop crypto distribution",
        "defi yield farming opportunity",
        "bitcoin bullish signal"
    ]
    
    # Scan
    results = scanner.scan_daily(queries)
    
    # Get top results
    top_results = scanner.get_top_by_category(results, top_n=3)
    
    # Format for Notion
    notion_data = scanner.format_for_notion(top_results)
    
    print(f"Found {len(notion_data)} top results:")
    for item in notion_data:
        print(f"  {item['title']} ({item['sentiment']} {item['rank_score']:.1f})")
    
    return results
