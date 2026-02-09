"""
ORACLE Phase 4: ML Scores → Notion Sync
Pushes influencer ML scores to Notion database
"""
import csv
import logging
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class NotionMLSync:
    """Syncs ML scores to Notion database"""
    
    def __init__(self, api_key: Optional[str] = None, database_id: Optional[str] = None):
        """
        Initialize Notion sync
        
        Args:
            api_key: Notion API key (NOTION_API_KEY env var)
            database_id: Notion database ID (NOTION_DATABASE_ID env var)
        """
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        if not self.api_key or not self.database_id:
            logger.warning("⚠️  NOTION_API_KEY or NOTION_DATABASE_ID not set")
    
    def load_ml_scores(self, filepath: str) -> List[Dict]:
        """Load ML scores from CSV"""
        scores = []
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return []
        
        with open(filepath) as f:
            reader = csv.DictReader(f)
            for row in reader:
                scores.append(row)
        
        logger.info(f"✅ Loaded {len(scores)} ML scores")
        return scores
    
    def get_page_by_username(self, username: str) -> Optional[str]:
        """
        Find Notion page by Twitter handle
        
        Returns:
            Page ID if found, None otherwise
        """
        url = f"{self.base_url}/databases/{self.database_id}/query"
        
        payload = {
            "filter": {
                "property": "Handle",
                "title": {
                    "equals": username
                }
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            results = response.json().get("results", [])
            if results:
                return results[0]["id"]
        except Exception as e:
            logger.error(f"Error querying page for {username}: {e}")
        
        return None
    
    def update_page_with_scores(self, page_id: str, scores: Dict) -> bool:
        """
        Update Notion page with ML scores
        
        Args:
            page_id: Notion page ID
            scores: Dict with ML scores
        
        Returns:
            True if successful
        """
        url = f"{self.base_url}/pages/{page_id}"
        
        # Map scores to Notion properties
        properties = {}
        
        # Engagement Score
        if "engagement_score" in scores:
            properties["Engagement Score"] = {
                "number": float(scores["engagement_score"])
            }
        
        # Sentiment Score
        if "sentiment_score" in scores:
            properties["Sentiment"] = {
                "number": float(scores["sentiment_score"])
            }
        
        # Composite Score (main ranking)
        if "composite_score" in scores:
            properties["ML Score"] = {
                "number": float(scores["composite_score"])
            }
        
        # Airdrop Fit
        if "airdrop_fit" in scores:
            properties["Airdrop Fit"] = {
                "number": float(scores["airdrop_fit"])
            }
        
        # Confidence
        if "confidence" in scores:
            properties["Confidence"] = {
                "number": float(scores["confidence"])
            }
        
        # Last Updated
        properties["ML Updated"] = {
            "date": {
                "start": datetime.utcnow().isoformat()
            }
        }
        
        payload = {"properties": properties}
        
        try:
            response = requests.patch(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            logger.info(f"✅ Updated page {page_id} with ML scores")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update page: {e}")
            return False
    
    def sync_ml_scores(self, scores_file: str = None) -> Dict[str, int]:
        """
        Sync all ML scores to Notion
        
        Args:
            scores_file: Path to ml_scores CSV
        
        Returns:
            Stats dict {updated, failed, total}
        """
        base_dir = Path(__file__).parent.parent
        scores_file = scores_file or base_dir / "data" / "ml_scores_phase4.csv"
        
        scores_list = self.load_ml_scores(str(scores_file))
        
        stats = {"updated": 0, "failed": 0, "total": len(scores_list)}
        
        for score in scores_list:
            username = score.get("username", "").strip()
            
            # Find page
            page_id = self.get_page_by_username(username)
            
            if not page_id:
                logger.warning(f"⚠️  Page not found for {username} (create manually in Notion)")
                stats["failed"] += 1
                continue
            
            # Update with scores
            if self.update_page_with_scores(page_id, score):
                stats["updated"] += 1
            else:
                stats["failed"] += 1
        
        return stats


def main():
    """CLI entry point"""
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "=" * 70)
    print("📊 ORACLE Phase 4: ML Scores → Notion Sync")
    print("=" * 70)
    
    syncer = NotionMLSync()
    
    # Check credentials
    if not syncer.api_key or not syncer.database_id:
        print("\n❌ Missing credentials:")
        print("   Set NOTION_API_KEY and NOTION_DATABASE_ID in .env")
        return
    
    print("\n✅ Notion credentials found")
    print(f"   Database: {syncer.database_id[:8]}...")
    
    # Sync scores
    print("\n🔄 Syncing ML scores to Notion...")
    stats = syncer.sync_ml_scores()
    
    print(f"\n📈 Results:")
    print(f"   Updated: {stats['updated']}/{stats['total']}")
    print(f"   Failed: {stats['failed']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
