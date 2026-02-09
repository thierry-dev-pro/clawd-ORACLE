"""
ORACLE Phase 4: Influencer Engagement Scorer
Scores influencers 0-100 based on:
- Engagement rate (likes, retweets, replies)
- Tweet frequency
- Sentiment trend
"""
import logging
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
import csv

logger = logging.getLogger(__name__)


@dataclass
class InfluencerScore:
    """Influencer ML score result"""
    username: str
    followers: int
    engagement_score: float  # 0-100
    sentiment_score: float   # -100 to +100
    composite_score: float   # 0-100
    airdrop_fit: float       # 0-100
    confidence: float        # 0-100
    tweets_analyzed: int


class InfluencerScorer:
    """ML scoring engine for influencers"""
    
    def __init__(self, engagement_weights: Dict = None):
        """
        Initialize scorer
        
        Args:
            engagement_weights: {likes, retweets, replies} weights
        """
        self.engagement_weights = engagement_weights or {
            "likes": 0.4,
            "retweets": 0.35,
            "replies": 0.25,
        }
        logger.info("✅ InfluencerScorer initialized")
    
    def score_engagement(
        self,
        likes: int,
        retweets: int,
        replies: int,
        followers: int,
        tweets_count: int
    ) -> float:
        """
        Calculate engagement score 0-100
        
        Formula:
        - Normalize by followers (engagement rate)
        - Weight by likes/retweets/replies
        - Cap at 100
        """
        if tweets_count == 0:
            return 0.0
        
        # Engagement rate per tweet
        total_engagement = likes + retweets + replies
        engagement_rate = (total_engagement / tweets_count) / max(followers, 1)
        
        # Weighted components
        like_rate = (likes / tweets_count) if tweets_count > 0 else 0
        rt_rate = (retweets / tweets_count) if tweets_count > 0 else 0
        reply_rate = (replies / tweets_count) if tweets_count > 0 else 0
        
        score = (
            like_rate * self.engagement_weights["likes"] +
            rt_rate * self.engagement_weights["retweets"] +
            reply_rate * self.engagement_weights["replies"]
        ) * 100
        
        return min(score, 100.0)
    
    def score_influencer(
        self,
        username: str,
        followers: int,
        tweets: List[Dict],
        sentiment_scores: Optional[List[float]] = None
    ) -> InfluencerScore:
        """
        Generate composite score for influencer
        
        Args:
            username: Twitter handle
            followers: Follower count
            tweets: List of tweet dicts with {likes, retweets, replies}
            sentiment_scores: Optional sentiment analysis results
        
        Returns:
            InfluencerScore object
        """
        if not tweets:
            return InfluencerScore(
                username=username,
                followers=followers,
                engagement_score=0.0,
                sentiment_score=0.0,
                composite_score=0.0,
                airdrop_fit=0.0,
                confidence=0.0,
                tweets_analyzed=0
            )
        
        # Aggregate metrics
        total_likes = sum(t.get("likes", 0) for t in tweets)
        total_retweets = sum(t.get("retweets", 0) for t in tweets)
        total_replies = sum(t.get("replies", 0) for t in tweets)
        
        # Engagement score
        engagement = self.score_engagement(
            total_likes, total_retweets, total_replies,
            followers, len(tweets)
        )
        
        # Sentiment score (if provided)
        sentiment = 0.0
        if sentiment_scores:
            sentiment = sum(sentiment_scores) / len(sentiment_scores) * 100
        
        # Composite: 60% engagement, 40% sentiment
        composite = (engagement * 0.6) + (sentiment * 0.4)
        
        # Airdrop fit: high engagement + positive sentiment = good airdrop target
        airdrop_fit = (engagement * 0.5) + (max(sentiment, 0) * 0.5)
        
        # Confidence based on tweet count
        confidence = min(len(tweets) / 50 * 100, 100.0)
        
        return InfluencerScore(
            username=username,
            followers=followers,
            engagement_score=engagement,
            sentiment_score=sentiment,
            composite_score=composite,
            airdrop_fit=airdrop_fit,
            confidence=confidence,
            tweets_analyzed=len(tweets)
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test scorer
    scorer = InfluencerScorer()
    test_tweets = [
        {"likes": 150, "retweets": 45, "replies": 23},
        {"likes": 200, "retweets": 60, "replies": 30},
        {"likes": 100, "retweets": 30, "replies": 15},
    ]
    
    result = scorer.score_influencer(
        "test_user",
        followers=10000,
        tweets=test_tweets,
        sentiment_scores=[0.75, 0.82, 0.68]
    )
    
    print(f"✅ Test score: {result}")
