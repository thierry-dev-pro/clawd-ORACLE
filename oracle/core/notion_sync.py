"""
ORACLE Phase 3: Notion Integration Module
Syncs Twitter handles to Notion database hourly
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class NotionSyncHandler:
    """Syncs Twitter handles to Notion database"""
    
    def __init__(self, notion_api_key: Optional[str] = None, database_id: Optional[str] = None):
        """
        Initialize Notion sync handler
        
        Args:
            notion_api_key: Notion API key (from env: NOTION_API_KEY)
            database_id: Notion database ID (from env: NOTION_DATABASE_ID)
        """
        self.notion_api_key = notion_api_key or os.getenv("NOTION_API_KEY")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.notion_api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
    def load_twitter_handles(self, filepath: str = "data/twitter_handles_phase3.json") -> Dict:
        """Load Twitter handles from JSON file"""
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return {}
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def create_notion_page(self, handle_data: Dict) -> Optional[str]:
        """
        Create a Notion page for a Twitter handle
        
        Returns:
            Page ID if successful, None otherwise
        """
        if not self.notion_api_key or not self.database_id:
            logger.warning("NOTION_API_KEY or NOTION_DATABASE_ID not configured")
            return None
        
        url = f"{self.base_url}/pages"
        
        # Properties mapping
        properties = {
            "Handle": {
                "title": [{"text": {"content": handle_data["username"]}}]
            },
            "Name": {
                "rich_text": [{"text": {"content": handle_data["name"]}}]
            },
            "Followers": {
                "number": handle_data["followers"]
            },
            "Category": {
                "select": {"name": handle_data.get("category", "general")}
            },
            "Created": {
                "date": {"start": f"{handle_data['created']}-01-01"}
            },
            "URL": {
                "url": handle_data["url"]
            },
            "Status": {
                "select": {"name": handle_data.get("status", "active")}
            }
        }
        
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json().get("id")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create Notion page: {e}")
            return None
    
    def sync_all_handles(self) -> Dict[str, int]:
        """
        Sync all Twitter handles to Notion
        
        Returns:
            Dict with sync stats (created, failed, total)
        """
        handles_data = self.load_twitter_handles()
        
        if not handles_data.get("handles"):
            logger.error("No handles found in data file")
            return {"created": 0, "failed": 0, "total": 0}
        
        stats = {
            "created": 0,
            "failed": 0,
            "total": len(handles_data["handles"]),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for handle in handles_data["handles"]:
            page_id = self.create_notion_page(handle)
            if page_id:
                stats["created"] += 1
                logger.info(f"Created Notion page for {handle['username']}: {page_id}")
            else:
                stats["failed"] += 1
                logger.warning(f"Failed to create page for {handle['username']}")
        
        return stats
    
    def query_handles_from_notion(self) -> List[Dict]:
        """Query existing handles from Notion database"""
        if not self.notion_api_key or not self.database_id:
            return []
        
        url = f"{self.base_url}/databases/{self.database_id}/query"
        
        try:
            response = requests.post(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            results = response.json().get("results", [])
            
            handles = []
            for page in results:
                props = page.get("properties", {})
                handles.append({
                    "id": page["id"],
                    "handle": props.get("Handle", {}).get("title", [{}])[0].get("text", {}).get("content", ""),
                    "followers": props.get("Followers", {}).get("number", 0)
                })
            
            return handles
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to query Notion: {e}")
            return []


# CLI interface
if __name__ == "__main__":
    import sys
    
    sync = NotionSyncHandler()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "sync":
            stats = sync.sync_all_handles()
            print(f"Sync complete: {stats['created']} created, {stats['failed']} failed")
        elif sys.argv[1] == "query":
            handles = sync.query_handles_from_notion()
            print(f"Found {len(handles)} handles in Notion")
            for h in handles:
                print(f"  - {h['handle']} ({h['followers']} followers)")
    else:
        print("Usage: python notion_sync.py [sync|query]")
