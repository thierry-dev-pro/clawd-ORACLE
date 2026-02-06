#!/usr/bin/env python3
"""
ORACLE Phase 3: Sync Test Script
Tests Notion sync functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from core.notion_sync import NotionSyncHandler
import json

load_dotenv(".env.phase3")

def test_load_handles():
    """Test 1: Load Twitter handles"""
    print("📥 Test 1: Load Twitter handles...")
    sync = NotionSyncHandler()
    handles = sync.load_twitter_handles()
    
    if handles and "handles" in handles:
        print(f"   ✅ Loaded {len(handles['handles'])} handles")
        return True
    else:
        print("   ❌ Failed to load handles")
        return False

def test_notion_auth():
    """Test 2: Verify Notion API auth"""
    print("🔐 Test 2: Notion API authentication...")
    sync = NotionSyncHandler()
    
    if not sync.notion_api_key:
        print("   ⚠️  NOTION_API_KEY not set")
        return False
    
    if not sync.database_id:
        print("   ⚠️  NOTION_DATABASE_ID not set")
        return False
    
    print("   ✅ API key and Database ID configured")
    return True

def test_single_page_create():
    """Test 3: Create single test page"""
    print("🔨 Test 3: Create test Notion page...")
    sync = NotionSyncHandler()
    
    if not sync.notion_api_key or not sync.database_id:
        print("   ⏭️  Skipped (API not configured)")
        return None
    
    test_handle = {
        "username": "test_oracle_phase3",
        "name": "Test Account",
        "bio": "Testing Phase 3 Notion integration",
        "followers": 9999,
        "created": 2026,
        "url": "https://x.com/test_oracle_phase3",
        "category": "builder",
        "status": "active"
    }
    
    page_id = sync.create_notion_page(test_handle)
    
    if page_id:
        print(f"   ✅ Created test page: {page_id}")
        return True
    else:
        print("   ❌ Failed to create test page")
        return False

def test_query_handles():
    """Test 4: Query handles from Notion"""
    print("📖 Test 4: Query Notion database...")
    sync = NotionSyncHandler()
    
    if not sync.notion_api_key or not sync.database_id:
        print("   ⏭️  Skipped (API not configured)")
        return None
    
    handles = sync.query_handles_from_notion()
    print(f"   ✅ Found {len(handles)} handles in Notion")
    return True

def test_full_sync():
    """Test 5: Full sync simulation"""
    print("⚡ Test 5: Full sync (DRY RUN)...")
    sync = NotionSyncHandler()
    
    if not sync.notion_api_key or not sync.database_id:
        print("   ⏭️  Skipped (API not configured)")
        return None
    
    handles = sync.load_twitter_handles()
    if not handles.get("handles"):
        print("   ❌ No handles to sync")
        return False
    
    print(f"   📊 Would sync {len(handles['handles'])} handles")
    
    # Count by category
    categories = {}
    for h in handles["handles"]:
        cat = h.get("category", "general")
        categories[cat] = categories.get(cat, 0) + 1
    
    print("   Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:5]:
        print(f"      • {cat}: {count}")
    
    return True

def main():
    print("\n" + "="*50)
    print("ORACLE Phase 3 - Sync Test Suite")
    print("="*50 + "\n")
    
    results = {
        "Load Handles": test_load_handles(),
        "Notion Auth": test_notion_auth(),
        "Single Page": test_single_page_create(),
        "Query DB": test_query_handles(),
        "Full Sync": test_full_sync()
    }
    
    print("\n" + "="*50)
    print("Test Results:")
    print("="*50)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⏭️  SKIP"
        print(f"{test_name:20} {status}")
    
    passed = sum(1 for r in results.values() if r is True)
    total = sum(1 for r in results.values() if r is not None)
    
    print(f"\n{passed}/{total} tests passed")
    print("\n✅ Ready for Phase 3 Notion sync!" if passed == total else "\n⚠️  Configure API credentials to continue")

if __name__ == "__main__":
    main()
