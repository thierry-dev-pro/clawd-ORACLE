"""
Twitter Daily Scanner - Telegram Alerts (Optional).
Send top results to Telegram for daily review.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from .twitter_daily_scanner import TweetCategory, CategorizedResult

logger = logging.getLogger(__name__)


class TwitterTelegramAlerts:
    """Send Twitter scan results to Telegram."""
    
    def __init__(self, telegram_bot=None):
        """
        Initialize Telegram alerts.
        
        Args:
            telegram_bot: Optional TelegramBot instance
        """
        self.bot = telegram_bot
    
    def send_scan_summary(
        self,
        results: Dict[TweetCategory, List[CategorizedResult]],
        chat_id: Optional[str] = None,
        threshold_score: float = 60.0
    ) -> bool:
        """
        Send scan summary to Telegram.
        
        Args:
            results: Grouped scan results
            chat_id: Optional Telegram chat ID
            threshold_score: Only send results above this score
            
        Returns:
            True if sent successfully
        """
        if not self.bot:
            logger.warning("Telegram bot not configured")
            return False
        
        # Build message
        message = self._build_summary_message(results, threshold_score)
        
        if not message:
            logger.info("No results above threshold")
            return False
        
        try:
            self.bot.send_message(message, chat_id=chat_id)
            logger.info("Sent scan summary to Telegram")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_category_results(
        self,
        category: TweetCategory,
        results: List[CategorizedResult],
        chat_id: Optional[str] = None
    ) -> bool:
        """
        Send results for specific category.
        
        Args:
            category: Result category
            results: List of results
            chat_id: Optional chat ID
            
        Returns:
            True if sent successfully
        """
        if not self.bot or not results:
            return False
        
        message = self._build_category_message(category, results)
        
        try:
            self.bot.send_message(message, chat_id=chat_id)
            logger.info(f"Sent {category.value} results to Telegram")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_top_results(
        self,
        results: Dict[TweetCategory, List[CategorizedResult]],
        top_n: int = 5,
        chat_id: Optional[str] = None
    ) -> bool:
        """
        Send top N results across all categories.
        
        Args:
            results: Grouped results
            top_n: Number of top results to send
            chat_id: Optional chat ID
            
        Returns:
            True if sent successfully
        """
        if not self.bot:
            return False
        
        # Flatten and sort by rank score
        all_results = []
        for category_results in results.values():
            all_results.extend(category_results)
        
        all_results.sort(key=lambda r: r.rank_score, reverse=True)
        top_results = all_results[:top_n]
        
        if not top_results:
            return False
        
        message = self._build_top_results_message(top_results)
        
        try:
            self.bot.send_message(message, chat_id=chat_id)
            logger.info(f"Sent top {top_n} results to Telegram")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_high_confidence_alerts(
        self,
        results: Dict[TweetCategory, List[CategorizedResult]],
        min_confidence: float = 0.8,
        min_score: float = 70.0,
        chat_id: Optional[str] = None
    ) -> int:
        """
        Send alerts for high-confidence, high-score results.
        
        Args:
            results: Grouped results
            min_confidence: Minimum confidence threshold
            min_score: Minimum rank score threshold
            chat_id: Optional chat ID
            
        Returns:
            Number of alerts sent
        """
        if not self.bot:
            return 0
        
        alerts_sent = 0
        
        for category, category_results in results.items():
            for result in category_results:
                if (result.confidence >= min_confidence and 
                    result.rank_score >= min_score):
                    
                    message = self._build_alert_message(result)
                    
                    try:
                        self.bot.send_message(message, chat_id=chat_id)
                        alerts_sent += 1
                    except Exception as e:
                        logger.error(f"Failed to send alert: {e}")
        
        if alerts_sent > 0:
            logger.info(f"Sent {alerts_sent} high-confidence alerts to Telegram")
        
        return alerts_sent
    
    # Message builders
    
    def _build_summary_message(
        self,
        results: Dict[TweetCategory, List[CategorizedResult]],
        threshold_score: float
    ) -> str:
        """Build summary message."""
        emoji = "📊"
        message = f"{emoji} <b>Twitter Daily Scan Summary</b>\n"
        message += f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</i>\n\n"
        
        has_results = False
        
        for category, category_results in results.items():
            # Filter by threshold
            filtered = [r for r in category_results if r.rank_score >= threshold_score]
            
            if filtered:
                has_results = True
                cat_emoji = self._get_category_emoji(category)
                message += f"{cat_emoji} <b>{category.value.upper()}</b>\n"
                
                for i, result in enumerate(filtered[:3], 1):  # Top 3 per category
                    message += (
                        f"  {i}. {result.query}\n"
                        f"     📈 Score: {result.rank_score:.1f} | "
                        f"Confidence: {result.confidence:.0%}\n"
                    )
                
                message += "\n"
        
        if not has_results:
            return ""
        
        return message
    
    def _build_category_message(
        self,
        category: TweetCategory,
        results: List[CategorizedResult]
    ) -> str:
        """Build category-specific message."""
        emoji = self._get_category_emoji(category)
        message = f"{emoji} <b>{category.value.upper()} Results</b>\n\n"
        
        for i, result in enumerate(results[:5], 1):  # Top 5
            message += (
                f"{i}. <b>{result.query}</b>\n"
                f"   Sentiment: {result.sentiment_score:+.2f} | "
                f"Score: {result.rank_score:.1f}\n"
                f"   Themes: {', '.join(result.key_themes)}\n"
                f"   Tweets: {result.tweet_count}\n\n"
            )
        
        return message
    
    def _build_top_results_message(
        self,
        results: List[CategorizedResult]
    ) -> str:
        """Build top results message."""
        message = "🏆 <b>Top Results Today</b>\n\n"
        
        for i, result in enumerate(results, 1):
            emoji = self._get_category_emoji(result.category)
            message += (
                f"{i}. {emoji} <b>{result.query}</b>\n"
                f"   Category: {result.category.value}\n"
                f"   Score: {result.rank_score:.1f}/100\n\n"
            )
        
        return message
    
    def _build_alert_message(self, result: CategorizedResult) -> str:
        """Build alert message for single result."""
        emoji = self._get_category_emoji(result.category)
        sentiment_emoji = self._get_sentiment_emoji(result.sentiment_score)
        
        message = (
            f"🚨 <b>High-Confidence Alert</b>\n"
            f"{emoji} {result.category.value.upper()}\n\n"
            f"<b>{result.query}</b>\n"
            f"{sentiment_emoji} Sentiment: {result.sentiment_score:+.2f}\n"
            f"📊 Score: {result.rank_score:.1f}\n"
            f"✅ Confidence: {result.confidence:.0%}\n"
            f"💬 Tweets analyzed: {result.tweet_count}\n\n"
            f"<i>Key themes: {', '.join(result.key_themes)}</i>"
        )
        
        return message
    
    @staticmethod
    def _get_category_emoji(category: TweetCategory) -> str:
        """Get category emoji."""
        emojis = {
            TweetCategory.AIRDROP: "🎁",
            TweetCategory.DEFI: "💰",
            TweetCategory.NFT: "🖼️",
            TweetCategory.EXCHANGE: "💱",
            TweetCategory.WALLET: "🔑",
            TweetCategory.GOVERNANCE: "🗳️",
            TweetCategory.SECURITY: "🔒",
            TweetCategory.PRICE: "📊",
            TweetCategory.ADOPTION: "🚀",
            TweetCategory.REGULATION: "⚖️"
        }
        return emojis.get(category, "📌")
    
    @staticmethod
    def _get_sentiment_emoji(score: float) -> str:
        """Get sentiment emoji."""
        if score > 0.5:
            return "📈"  # Strong bullish
        elif score > 0.1:
            return "↗️"  # Slightly bullish
        elif score < -0.5:
            return "📉"  # Strong bearish
        elif score < -0.1:
            return "↘️"  # Slightly bearish
        else:
            return "➡️"  # Neutral


# Integration helper
def setup_telegram_alerts(job, telegram_bot=None) -> TwitterTelegramAlerts:
    """
    Setup Telegram alerts for daily job.
    
    Args:
        job: TwitterDailyJob instance
        telegram_bot: Optional TelegramBot instance
        
    Returns:
        TwitterTelegramAlerts instance
    """
    alerts = TwitterTelegramAlerts(telegram_bot)
    
    # Patch job to send alerts after scan
    original_run_scan = job.run_scan
    
    def run_scan_with_alerts():
        original_run_scan()
        
        # Get results from last scan
        if job.last_result_count > 0:
            try:
                # Send summary to Telegram
                results = job.scanner.scan_daily()
                top_results = job.scanner.get_top_by_category(results, top_n=3)
                
                alerts.send_scan_summary(top_results)
                
            except Exception as e:
                logger.error(f"Failed to send Telegram alerts: {e}")
    
    job.run_scan = run_scan_with_alerts
    
    return alerts
