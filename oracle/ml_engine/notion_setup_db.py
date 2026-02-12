"""
ORACLE Phase 4: Setup Notion Database Properties
Creates ML score properties in existing database
"""
import logging
import os
import requests

logger = logging.getLogger(__name__)


class NotionDBSetup:
    """Sets up Notion database with ML properties"""
    
    def __init__(self, api_key: str = None, database_id: str = None):
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    
    def add_property(self, property_name: str, property_type: str, **kwargs) -> bool:
        """
        Add property to database
        
        Args:
            property_name: Property name
            property_type: "number", "text", "url", "date", "select", etc.
            **kwargs: Type-specific config
        
        Returns:
            True if successful
        """
        url = f"{self.base_url}/databases/{self.database_id}"
        
        # Build property config based on type
        if property_type == "number":
            prop_config = {"number": {}}
        elif property_type == "text":
            prop_config = {"rich_text": {}}
        elif property_type == "url":
            prop_config = {"url": {}}
        elif property_type == "date":
            prop_config = {"date": {}}
        else:
            prop_config = {property_type: {}}
        
        payload = {
            "properties": {
                property_name: prop_config
            }
        }
        
        try:
            response = requests.patch(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            logger.info(f"✅ Added property: {property_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add {property_name}: {e}")
            return False
    
    def setup_ml_properties(self) -> int:
        """Setup all ML score properties"""
        properties = [
            ("Followers", "number"),
            ("Bio", "text"),
            ("Category", "text"),
            ("Twitter URL", "url"),
            ("ML Score", "number"),
            ("Engagement", "number"),
            ("Sentiment", "number"),
            ("Airdrop Fit", "number"),
            ("Confidence", "number"),
            ("Updated", "date"),
        ]
        
        count = 0
        for prop_name, prop_type in properties:
            if self.add_property(prop_name, prop_type):
                count += 1
        
        return count


def main():
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "=" * 70)
    print("🔧 Setup Notion Database for ORACLE Phase 4")
    print("=" * 70)
    
    setup = NotionDBSetup()
    
    print("\n🔄 Creating ML properties...")
    count = setup.setup_ml_properties()
    
    print(f"\n✅ Created {count} properties")
    print("\n💡 Now you can:")
    print("   1. Create pages in Notion for influencers")
    print("   2. Sync ML scores automatically")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
