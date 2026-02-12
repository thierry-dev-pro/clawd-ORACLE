#!/usr/bin/env python3
"""
Demo - Simulate Twitter scan and show what would appear in Notion.
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent / "oracle"))

from oracle.core.twitter_daily_scanner import (
    TwitterDailyScanner,
    TweetCategory,
    CategorizedResult
)
from datetime import datetime

print("=" * 80)
print("TWITTER DAILY SCAN - NOTION PREVIEW")
print("=" * 80)
print()

# Simulate scan results (what would be stored in Notion)
simulated_results = {
    TweetCategory.AIRDROP: [
        CategorizedResult(
            category=TweetCategory.AIRDROP,
            query="airdrop crypto distribution 2024",
            sentiment_score=0.78,
            confidence=0.87,
            key_themes=["claim", "eligibility", "distribution", "whitelist"],
            tweet_count=48,
            rank_score=78.5,
            detected_at=datetime.now(),
            raw_snapshot={}
        ),
        CategorizedResult(
            category=TweetCategory.AIRDROP,
            query="free tokens allocation eligible",
            sentiment_score=0.72,
            confidence=0.82,
            key_themes=["free", "allocation", "snapshot", "reward"],
            tweet_count=42,
            rank_score=72.3,
            detected_at=datetime.now(),
            raw_snapshot={}
        ),
        CategorizedResult(
            category=TweetCategory.AIRDROP,
            query="token claim process guide",
            sentiment_score=0.65,
            confidence=0.75,
            key_themes=["claim", "process", "guide", "how-to"],
            tweet_count=35,
            rank_score=65.8,
            detected_at=datetime.now(),
            raw_snapshot={}
        ),
    ],
    TweetCategory.DEFI: [
        CategorizedResult(
            category=TweetCategory.DEFI,
            query="defi yield farming opportunity 2024",
            sentiment_score=0.62,
            confidence=0.80,
            key_themes=["yield", "farming", "liquidity", "aave", "compound"],
            tweet_count=38,
            rank_score=62.1,
            detected_at=datetime.now(),
            raw_snapshot={}
        ),
        CategorizedResult(
            category=TweetCategory.DEFI,
            query="new defi protocol launch",
            sentiment_score=0.58,
            confidence=0.76,
            key_themes=["protocol", "launch", "new", "dex"],
            tweet_count=32,
            rank_score=58.3,
            detected_at=datetime.now(),
            raw_snapshot={}
        ),
        CategorizedResult(
            category=TweetCategory.DEFI,
            query="liquidity pool mining airdrop",
            sentiment_score=0.54,
            confidence=0.70,
            key_themes=["liquidity", "mining", "pool"],
            tweet_count=28,
            rank_score=54.6,
            detected_at=datetime.now(),
            raw_snapshot={}
        ),
    ],
    TweetCategory.ADOPTION: [
        CategorizedResult(
            category=TweetCategory.ADOPTION,
            query="bitcoin institutional adoption news",
            sentiment_score=0.85,
            confidence=0.92,
            key_themes=["institutional", "adoption", "mainstream", "news"],
            tweet_count=52,
            rank_score=85.5,
            detected_at=datetime.now(),
            raw_snapshot={}
        ),
        CategorizedResult(
            category=TweetCategory.ADOPTION,
            query="crypto mainstream integration real world use",
            sentiment_score=0.78,
            confidence=0.88,
            key_themes=["mainstream", "integration", "real-world", "utility"],
            tweet_count=45,
            rank_score=78.2,
            detected_at=datetime.now(),
            raw_snapshot={}
        ),
        CategorizedResult(
            category=TweetCategory.ADOPTION,
            query="blockchain enterprise partnership announcement",
            sentiment_score=0.71,
            confidence=0.83,
            key_themes=["enterprise", "partnership", "blockchain"],
            tweet_count=38,
            rank_score=71.0,
            detected_at=datetime.now(),
            raw_snapshot={}
        ),
    ],
    TweetCategory.SECURITY: [
        CategorizedResult(
            category=TweetCategory.SECURITY,
            query="smart contract security audit completed",
            sentiment_score=0.45,
            confidence=0.72,
            key_themes=["audit", "security", "smart-contract", "verified"],
            tweet_count=28,
            rank_score=50.2,
            detected_at=datetime.now(),
            raw_snapshot={}
        ),
        CategorizedResult(
            category=TweetCategory.SECURITY,
            query="vulnerability fix update security patch",
            sentiment_score=0.35,
            confidence=0.68,
            key_themes=["vulnerability", "fix", "patch"],
            tweet_count=22,
            rank_score=45.1,
            detected_at=datetime.now(),
            raw_snapshot={}
        ),
    ],
    TweetCategory.NFT: [
        CategorizedResult(
            category=TweetCategory.NFT,
            query="nft collection mint drop announcement",
            sentiment_score=0.68,
            confidence=0.79,
            key_themes=["collection", "mint", "drop", "announcement"],
            tweet_count=40,
            rank_score=68.3,
            detected_at=datetime.now(),
            raw_snapshot={}
        ),
    ],
}

# Format for Notion display
scanner = TwitterDailyScanner()
notion_data = scanner.format_for_notion(simulated_results)

print(f"📊 SCAN RESULTS: {len(notion_data)} pages à créer dans Notion")
print()
print("─" * 80)
print()

# Display by category
for category, results in simulated_results.items():
    emoji = scanner._sentiment_emoji(results[0].sentiment_score)
    print(f"{emoji} {category.value.upper()}")
    print()
    
    for i, result in enumerate(results, 1):
        sentiment_emoji = scanner._sentiment_emoji(result.sentiment_score)
        print(f"  {i}. {result.query}")
        print(f"     {sentiment_emoji} Sentiment: {result.sentiment_score:+.2f} | "
              f"Score: {result.rank_score:.1f}/100 | "
              f"Confidence: {result.confidence:.0%}")
        print(f"     Tweets: {result.tweet_count} | "
              f"Themes: {', '.join(result.key_themes[:3])}")
        print()

print("─" * 80)
print()

# Show table view (what you'll see in Notion)
print("📋 NOTION TABLE VIEW:")
print()
print(f"{'Title':<40} {'Category':<12} {'Sentiment':<10} {'Score':<6} {'Confidence':<12} {'Rank':<6}")
print("─" * 86)

for result in notion_data:
    title = result['title'][:38]
    category = result['category'].upper()[:10]
    sentiment = result['sentiment']
    score = f"{result['sentiment_score']:.2f}"
    confidence = f"{result['confidence']:.0%}"
    rank = f"{result['rank_score']:.1f}"
    
    print(f"{title:<40} {category:<12} {sentiment:<10} {score:<6} {confidence:<12} {rank:<6}")

print()
print("─" * 80)
print()

# Summary
print("📊 SUMMARY:")
print(f"  Total results: {len(notion_data)}")
print(f"  Categories: {len(simulated_results)}")
for cat, results in simulated_results.items():
    print(f"    • {cat.value.upper()}: {len(results)} results")

print()
print("✅ These results would be created in your Notion database:")
print("   - Pages named: 🎁 airdrop distribution, 💰 defi yield farming, etc.")
print("   - All properties filled: Sentiment, Score, Confidence, Rank, Tweets, Themes")
print("   - Last Updated: Current timestamp")
print()
print("=" * 80)
