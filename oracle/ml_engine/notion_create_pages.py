"""
ORACLE Phase 4: Create Notion Pages for ML Influencers
Creates database entries for all influencers with ML scores
"""
import csv
import json
import logging
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class NotionPageCreator:
    """Creates/updates Notion pages with influencer ML data"""
    
    def __init__(self, api_key: str = None, database_id: str = None):
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    
    def load_data(self):
        """Load influencers and ML scores"""
        base_dir = Path(__file__).parent.parent
        
        # Load influencers
        influencers = {}
        with open(base_dir / "data" / "influencers_phase3.csv") as f:
            reader = csv.DictReader(f)
            for row in reader:
                influencers[row['username']] = row
        
        # Load scores
        scores = {}
        with open(base_dir / "data" / "ml_scores_phase4.csv") as f:
            reader = csv.DictReader(f)
            for row in reader:
                scores[row['username']] = row
        
        return influencers, scores
    
    def create_page(self, username: str, inf_data: Dict, score_data: Dict = None) -> Optional[str]:
        """
        Create Notion page for influencer
        
        Returns:
            Page ID if successful
        """
        url = f"{self.base_url}/pages"
        
        # Build properties
        properties = {
            "Name": {
                "title": [{"text": {"content": username}}]
            }
        }
        
        # Add influencer data as rich text fields
        if inf_data:
            properties["Bio"] = {
                "rich_text": [{"text": {"content": inf_data.get('bio', '')[:500]}}]
            }
            
            properties["Followers"] = {
                "number": int(inf_data.get('followers', 0))
            }
            
            properties["Category"] = {
                "rich_text": [{"text": {"content": inf_data.get('category', '')}}]
            }
            
            properties["Twitter URL"] = {
                "url": inf_data.get('url', '')
            }
        
        # Add ML scores
        if score_data:
            # Main ML Score
            try:
                properties["ML Score"] = {
                    "number": float(score_data.get('composite_score', 0))
                }
            except:
                pass
            
            # Engagement
            try:
                properties["Engagement"] = {
                    "number": float(score_data.get('engagement_score', 0))
                }
            except:
                pass
            
            # Sentiment
            try:
                properties["Sentiment"] = {
                    "number": float(score_data.get('sentiment_score', 0))
                }
            except:
                pass
            
            # Airdrop Fit
            try:
                properties["Airdrop Fit"] = {
                    "number": float(score_data.get('airdrop_fit', 0))
                }
            except:
                pass
        
        # Add timestamp
        properties["Updated"] = {
            "date": {"start": datetime.utcnow().isoformat()}
        }
        
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            page_id = response.json().get("id")
            logger.info(f"✅ Created page: {username}")
            return page_id
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Failed to create page for {username}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ Error creating page: {e}")
            return None
    
    def create_all_pages(self) -> Dict[str, int]:
        """
        Create pages for all influencers with ML scores
        
        Returns:
            Stats: {created, failed, total}
        """
        influencers, scores = self.load_data()
        
        stats = {"created": 0, "failed": 0, "total": len(influencers)}
        
        for username, inf_data in list(influencers.items())[:10]:  # First 10
            score_data = scores.get(username)
            
            page_id = self.create_page(username, inf_data, score_data)
            
            if page_id:
                stats["created"] += 1
            else:
                stats["failed"] += 1
        
        return stats


def main():
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "=" * 70)
    print("📄 ORACLE Phase 4: Create Notion Pages")
    print("=" * 70)
    
    creator = NotionPageCreator()
    
    print("\n🔄 Creating influencer pages with ML scores...")
    stats = creator.create_all_pages()
    
    print(f"\n📈 Results:")
    print(f"   Created: {stats['created']}/{stats['total']}")
    print(f"   Failed: {stats['failed']}")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
