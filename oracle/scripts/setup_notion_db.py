#!/usr/bin/env python3
"""
ORACLE Phase 3: Notion Database Setup Script
Creates Notion database with required schema
"""

import os
import sys
import requests
import json
from pathlib import Path

# Load env
from dotenv import load_dotenv
load_dotenv("../.env.phase3")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
BASE_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def create_notion_database(parent_page_id: str) -> dict:
    """
    Create Notion database with Phase 3 schema
    
    Args:
        parent_page_id: Parent page ID (get from https://notion.so/YOUR_PAGE_ID)
    
    Returns:
        Created database info
    """
    url = f"{BASE_URL}/databases"
    
    payload = {
        "parent": {
            "type": "page_id",
            "page_id": parent_page_id
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": "ORACLE Phase 3 - Twitter Handles"
                }
            }
        ],
        "properties": {
            "Handle": {
                "type": "title",
                "title": {}
            },
            "Name": {
                "type": "rich_text",
                "rich_text": {}
            },
            "Followers": {
                "type": "number",
                "number": {
                    "format": "number"
                }
            },
            "Category": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "bitcoin_news", "color": "orange"},
                        {"name": "trader", "color": "blue"},
                        {"name": "nft_trader", "color": "purple"},
                        {"name": "nft_collector", "color": "purple"},
                        {"name": "nft_artist", "color": "purple"},
                        {"name": "nft_farmer", "color": "purple"},
                        {"name": "nft_project", "color": "purple"},
                        {"name": "influencer", "color": "red"},
                        {"name": "advisor", "color": "green"},
                        {"name": "builder", "color": "yellow"},
                        {"name": "trading", "color": "blue"},
                        {"name": "studio", "color": "gray"},
                        {"name": "ambassador", "color": "pink"},
                        {"name": "layer1_supporter", "color": "orange"},
                        {"name": "vc_defi", "color": "green"},
                        {"name": "social_media_manager", "color": "pink"},
                        {"name": "lab_dao", "color": "green"},
                        {"name": "cybersecurity", "color": "red"},
                        {"name": "music", "color": "purple"},
                        {"name": "general", "color": "gray"}
                    ]
                }
            },
            "Created": {
                "type": "date",
                "date": {}
            },
            "URL": {
                "type": "url",
                "url": {}
            },
            "Status": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "active", "color": "green"},
                        {"name": "archived", "color": "gray"},
                        {"name": "watching", "color": "blue"}
                    ]
                }
            },
            "Last Synced": {
                "type": "date",
                "date": {}
            },
            "Notes": {
                "type": "rich_text",
                "rich_text": {}
            }
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        response.raise_for_status()
        db_info = response.json()
        return {
            "success": True,
            "database_id": db_info["id"],
            "url": db_info["url"]
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    if not NOTION_API_KEY:
        print("❌ NOTION_API_KEY not configured in .env.phase3")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage: python setup_notion_db.py <parent_page_id>")
        print("\nGet your parent page ID from Notion URL:")
        print("  https://notion.so/YOUR_PAGE_ID?v=xxx")
        print("  Extract: YOUR_PAGE_ID")
        sys.exit(1)
    
    parent_page_id = sys.argv[1].replace("-", "")  # Remove hyphens
    
    print("🔄 Creating Notion database...")
    result = create_notion_database(parent_page_id)
    
    if result["success"]:
        print(f"✅ Database created!")
        print(f"   ID: {result['database_id']}")
        print(f"   URL: {result['url']}")
        print(f"\n📝 Update .env.phase3:")
        print(f"   NOTION_DATABASE_ID={result['database_id']}")
    else:
        print(f"❌ Failed: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
