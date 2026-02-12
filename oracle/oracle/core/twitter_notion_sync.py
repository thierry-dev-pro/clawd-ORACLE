"""
Twitter to Notion Sync - Push daily scanner results to Notion database.
Creates/updates Notion pages with categorized Twitter analysis results.
"""

import logging
import os
from typing import Dict, List, Optional
from datetime import datetime
import requests

from .twitter_daily_scanner import TweetCategory, CategorizedResult

logger = logging.getLogger(__name__)


class TwitterNotionSync:
    """Sync Twitter daily scan results to Notion."""
    
    def __init__(
        self,
        notion_api_key: Optional[str] = None,
        database_id: Optional[str] = None
    ):
        """
        Initialize Notion sync.
        
        Args:
            notion_api_key: Notion API key (from env: NOTION_API_KEY)
            database_id: Notion database ID (from env: NOTION_DATABASE_ID)
        """
        self.notion_api_key = notion_api_key or os.getenv("NOTION_API_KEY")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        
        if not self.notion_api_key or not self.database_id:
            raise ValueError("NOTION_API_KEY and NOTION_DATABASE_ID required")
        
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.notion_api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    
    def create_or_update_page(
        self,
        result: CategorizedResult,
        parent_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Create or update Notion page for result.
        
        Args:
            result: CategorizedResult to sync
            parent_id: Optional parent page ID
            
        Returns:
            Page ID if successful, None otherwise
        """
        # Check if page exists
        existing_id = self.find_existing_page(result.query, result.category)
        
        if existing_id:
            return self.update_page(existing_id, result)
        else:
            return self.create_page(result, parent_id)
    
    def create_page(
        self,
        result: CategorizedResult,
        parent_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Create new Notion page.
        
        Args:
            result: Result to create
            parent_id: Optional parent page ID
            
        Returns:
            Page ID or None
        """
        emoji = self._get_category_emoji(result.category)
        
        properties = {
            "title": {
                "title": [
                    {
                        "text": {
                            "content": f"{emoji} {result.query}"
                        }
                    }
                ]
            },
            "Category": {
                "select": {
                    "name": result.category.value.upper()
                }
            },
            "Sentiment": {
                "select": {
                    "name": self._sentiment_label(result.sentiment_score)
                }
            },
            "Score": {
                "number": round(result.sentiment_score, 2)
            },
            "Confidence": {
                "number": round(result.confidence, 2)
            },
            "Rank": {
                "number": round(result.rank_score, 1)
            },
            "Tweets": {
                "number": result.tweet_count
            },
            "Themes": {
                "rich_text": [
                    {
                        "text": {
                            "content": ", ".join(result.key_themes)
                        }
                    }
                ]
            },
            "Last Updated": {
                "date": {
                    "start": result.detected_at.isoformat()
                }
            }
        }
        
        # Add parent if provided
        if parent_id:
            properties["Parent"] = {
                "relation": [{"id": parent_id}]
            }
        
        payload = {
            "parent": {
                "database_id": self.database_id
            },
            "properties": properties,
            "children": [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {"text": {"content": "Analysis Summary"}}
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": (
                                        f"Sentiment: {result.sentiment_score:.2f} | "
                                        f"Confidence: {result.confidence:.2f} | "
                                        f"Tweets analyzed: {result.tweet_count}"
                                    )
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        try:
            resp = requests.post(
                f"{self.base_url}/pages",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                page_id = resp.json()["id"]
                logger.info(f"Created Notion page: {page_id}")
                return page_id
            else:
                logger.error(f"Failed to create page: {resp.status_code} - {resp.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating page: {e}")
            return None
    
    def update_page(
        self,
        page_id: str,
        result: CategorizedResult
    ) -> Optional[str]:
        """
        Update existing Notion page.
        
        Args:
            page_id: Page ID to update
            result: New result data
            
        Returns:
            Page ID or None
        """
        properties = {
            "Sentiment": {
                "select": {
                    "name": self._sentiment_label(result.sentiment_score)
                }
            },
            "Score": {
                "number": round(result.sentiment_score, 2)
            },
            "Confidence": {
                "number": round(result.confidence, 2)
            },
            "Rank": {
                "number": round(result.rank_score, 1)
            },
            "Tweets": {
                "number": result.tweet_count
            },
            "Last Updated": {
                "date": {
                    "start": result.detected_at.isoformat()
                }
            }
        }
        
        payload = {
            "properties": properties
        }
        
        try:
            resp = requests.patch(
                f"{self.base_url}/pages/{page_id}",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                logger.info(f"Updated Notion page: {page_id}")
                return page_id
            else:
                logger.error(f"Failed to update page: {resp.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating page: {e}")
            return None
    
    def find_existing_page(
        self,
        query: str,
        category: TweetCategory
    ) -> Optional[str]:
        """
        Find existing page for query/category.
        
        Args:
            query: Search query
            category: Result category
            
        Returns:
            Page ID or None
        """
        filter_obj = {
            "and": [
                {
                    "property": "Category",
                    "select": {
                        "equals": category.value.upper()
                    }
                }
            ]
        }
        
        payload = {
            "filter": filter_obj,
            "page_size": 100
        }
        
        try:
            resp = requests.post(
                f"{self.base_url}/databases/{self.database_id}/query",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                results = resp.json()["results"]
                
                # Find by title
                for page in results:
                    title = self._get_page_title(page)
                    if query.lower() in title.lower():
                        return page["id"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding page: {e}")
            return None
    
    def sync_batch(
        self,
        results: Dict[TweetCategory, List[CategorizedResult]]
    ) -> Dict[str, int]:
        """
        Sync batch of results to Notion.
        
        Args:
            results: Dict of categorized results
            
        Returns:
            Stats dict with counts
        """
        stats = {
            "created": 0,
            "updated": 0,
            "failed": 0
        }
        
        for category, category_results in results.items():
            for result in category_results:
                page_id = self.create_or_update_page(result)
                
                if page_id:
                    # Check if created or updated
                    if self.find_existing_page(result.query, category):
                        stats["updated"] += 1
                    else:
                        stats["created"] += 1
                else:
                    stats["failed"] += 1
        
        logger.info(
            f"Sync complete: {stats['created']} created, "
            f"{stats['updated']} updated, {stats['failed']} failed"
        )
        
        return stats
    
    def create_category_pages(
        self,
        categories: Optional[List[TweetCategory]] = None
    ) -> Dict[TweetCategory, Optional[str]]:
        """
        Create parent pages for each category.
        
        Args:
            categories: Optional list of categories (default: all)
            
        Returns:
            Dict mapping category to page ID
        """
        categories = categories or list(TweetCategory)
        
        results = {}
        
        for category in categories:
            emoji = self._get_category_emoji(category)
            
            payload = {
                "parent": {
                    "database_id": self.database_id
                },
                "properties": {
                    "title": {
                        "title": [
                            {"text": {"content": f"{emoji} {category.value.upper()}"}}
                        ]
                    },
                    "Category": {
                        "select": {"name": category.value.upper()}
                    }
                }
            }
            
            try:
                resp = requests.post(
                    f"{self.base_url}/pages",
                    json=payload,
                    headers=self.headers,
                    timeout=10
                )
                
                if resp.status_code == 200:
                    page_id = resp.json()["id"]
                    results[category] = page_id
                    logger.info(f"Created category page: {category.value}")
                    
            except Exception as e:
                logger.error(f"Error creating category page: {e}")
                results[category] = None
        
        return results
    
    # Helper methods
    
    @staticmethod
    def _get_category_emoji(category: TweetCategory) -> str:
        """Get emoji for category."""
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
    def _sentiment_label(score: float) -> str:
        """Get sentiment label."""
        if score > 0.5:
            return "Very Bullish"
        elif score > 0.1:
            return "Bullish"
        elif score < -0.5:
            return "Very Bearish"
        elif score < -0.1:
            return "Bearish"
        else:
            return "Neutral"
    
    @staticmethod
    def _get_page_title(page: Dict) -> str:
        """Extract title from Notion page."""
        try:
            props = page["properties"]
            if "title" in props:
                title_obj = props["title"]
                if "title" in title_obj and title_obj["title"]:
                    return title_obj["title"][0]["text"]["content"]
        except:
            pass
        
        return ""
