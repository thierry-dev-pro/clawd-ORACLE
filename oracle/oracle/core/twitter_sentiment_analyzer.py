"""
Twitter Sentiment Analyzer using Camofox for undetectable scraping.
Analyzes crypto market sentiment from Twitter/X searches.
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from urllib.parse import urlencode

import anthropic

from .camofox_client import CamofoxClient, CamofoxError

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """Sentiment analysis result."""
    query: str
    sentiment_score: float  # -1.0 (bearish) to +1.0 (bullish)
    sentiment_label: str  # "bearish", "neutral", "bullish"
    confidence: float  # 0.0 to 1.0
    key_themes: List[str]
    tweet_count: int
    analyzed_at: datetime
    raw_snapshot: Dict


class TwitterSentimentAnalyzer:
    """Analyze crypto sentiment from Twitter using Camofox snapshots."""
    
    def __init__(
        self,
        camofox_url: str = "http://localhost:9377",
        claude_model: str = "claude-sonnet-4-5-20250929"
    ):
        """
        Initialize sentiment analyzer.
        
        Args:
            camofox_url: Camofox service URL
            claude_model: Claude model for analysis
        """
        self.camofox = CamofoxClient(base_url=camofox_url)
        self.claude_client = anthropic.Anthropic()
        self.claude_model = claude_model
    
    def analyze_sentiment(
        self,
        query: str,
        max_tweets: int = 50,
        proxy: Optional[str] = None
    ) -> SentimentResult:
        """
        Analyze sentiment for a crypto query.
        
        Args:
            query: Search query (e.g., "bitcoin", "ethereum bull run")
            max_tweets: Maximum tweets to analyze
            proxy: Optional proxy URL
            
        Returns:
            SentimentResult with scores and themes
        """
        logger.info(f"Analyzing sentiment for: {query}")
        
        # Create browser tab
        url = f"https://twitter.com/search?q={urlencode({'q': query})}&f=live"
        
        try:
            tab_id = self.camofox.create_tab(
                user_id="oracle",
                session_key=f"twitter-sentiment-{query}",
                url=url,
                proxy=proxy
            )
            
            # Get snapshot
            snapshot = self.camofox.get_snapshot(tab_id, "oracle")
            
            # Extract tweet content
            tweets = self._extract_tweets_from_snapshot(snapshot)
            
            # Truncate to max_tweets
            tweets = tweets[:max_tweets]
            
            # Analyze with Claude
            sentiment = self._analyze_with_claude(query, tweets)
            
            # Store result
            result = SentimentResult(
                query=query,
                sentiment_score=sentiment["score"],
                sentiment_label=sentiment["label"],
                confidence=sentiment["confidence"],
                key_themes=sentiment["themes"],
                tweet_count=len(tweets),
                analyzed_at=datetime.now(),
                raw_snapshot=snapshot
            )
            
            logger.info(
                f"Sentiment: {sentiment['label']} "
                f"(score={sentiment['score']:.2f}, confidence={sentiment['confidence']:.2f})"
            )
            
            return result
            
        finally:
            self.camofox.close_tab(tab_id)
    
    def _extract_tweets_from_snapshot(self, snapshot: Dict) -> List[str]:
        """
        Extract tweet text from snapshot.
        
        Args:
            snapshot: Camofox snapshot
            
        Returns:
            List of tweet texts
        """
        tweets = []
        
        for elem in snapshot.get("elements", []):
            # Twitter uses article tags for tweets
            if elem.get("tag") == "article":
                text = elem.get("text", "").strip()
                if text and len(text) > 10:  # Filter out noise
                    tweets.append(text)
            
            # Also check for tweet-like divs
            elif "tweet" in elem.get("className", "").lower():
                text = elem.get("text", "").strip()
                if text and len(text) > 10:
                    tweets.append(text)
        
        return tweets
    
    def _analyze_with_claude(self, query: str, tweets: List[str]) -> Dict:
        """
        Analyze sentiment using Claude API.
        
        Args:
            query: Original search query
            tweets: List of tweet texts
            
        Returns:
            Dict with score, label, confidence, themes
        """
        if not tweets:
            return {
                "score": 0.0,
                "label": "neutral",
                "confidence": 0.0,
                "themes": []
            }
        
        # Prepare prompt
        tweets_text = "\n".join([f"- {tweet}" for tweet in tweets[:30]])  # Limit for tokens
        
        prompt = f"""Analyze the sentiment of these tweets about "{query}":

{tweets_text}

Provide a JSON response with:
1. "sentiment_score": float from -1.0 (bearish) to +1.0 (bullish)
2. "sentiment_label": "bearish", "neutral", or "bullish"
3. "confidence": float from 0.0 to 1.0
4. "key_themes": list of main topics discussed

Keep it concise. Return only valid JSON."""
        
        try:
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse response
            response_text = response.content[0].text
            
            # Try to extract JSON
            try:
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                # Try to extract JSON from markdown blocks
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0]
                    result = json.loads(json_str)
                    return result
                elif "{" in response_text:
                    json_str = response_text[response_text.index("{"):response_text.rindex("}")+1]
                    result = json.loads(json_str)
                    return result
                else:
                    raise ValueError("Could not parse Claude response")
                    
        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            return {
                "score": 0.0,
                "label": "neutral",
                "confidence": 0.0,
                "themes": []
            }
    
    def analyze_multiple(
        self,
        queries: List[str],
        max_tweets_per_query: int = 50
    ) -> Dict[str, SentimentResult]:
        """
        Analyze sentiment for multiple queries.
        
        Args:
            queries: List of search queries
            max_tweets_per_query: Max tweets per query
            
        Returns:
            Dict mapping query to SentimentResult
        """
        results = {}
        
        for query in queries:
            try:
                result = self.analyze_sentiment(query, max_tweets_per_query)
                results[query] = result
            except Exception as e:
                logger.error(f"Failed to analyze '{query}': {e}")
                results[query] = None
        
        return results
    
    def get_summary(self, results: Dict[str, SentimentResult]) -> Dict:
        """
        Generate summary of sentiment analysis.
        
        Args:
            results: Dict from analyze_multiple
            
        Returns:
            Summary dict with aggregate sentiment
        """
        valid_results = [r for r in results.values() if r is not None]
        
        if not valid_results:
            return {
                "overall_sentiment": "neutral",
                "average_score": 0.0,
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0
            }
        
        scores = [r.sentiment_score for r in valid_results]
        labels = [r.sentiment_label for r in valid_results]
        
        return {
            "overall_sentiment": "bullish" if sum(scores) > 0 else "bearish" if sum(scores) < 0 else "neutral",
            "average_score": sum(scores) / len(scores),
            "bullish_count": labels.count("bullish"),
            "bearish_count": labels.count("bearish"),
            "neutral_count": labels.count("neutral")
        }


# Example usage
def demo_sentiment_analysis():
    """Demo sentiment analysis."""
    analyzer = TwitterSentimentAnalyzer()
    
    queries = [
        "bitcoin price prediction",
        "ethereum bull run",
        "crypto market crash"
    ]
    
    results = analyzer.analyze_multiple(queries)
    summary = analyzer.get_summary(results)
    
    print(f"Overall Sentiment: {summary['overall_sentiment']}")
    print(f"Average Score: {summary['average_score']:.2f}")
    print(f"Bullish: {summary['bullish_count']}, Bearish: {summary['bearish_count']}, Neutral: {summary['neutral_count']}")
    
    return results
