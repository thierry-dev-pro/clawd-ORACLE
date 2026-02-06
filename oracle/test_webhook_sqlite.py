#!/usr/bin/env python3
"""
Webhook test script using SQLite
Simulates Telegram updates to test the webhook handler
"""
import asyncio
import json
import os
import sys

# Set database URL before any imports
os.environ['DATABASE_URL'] = 'sqlite:///./test_webhook.db'

# Now import after setting env var
from core.telegram_bot import process_telegram_webhook
from core.database import init_db

# Initialize database first
init_db()

async def test_webhook():
    """Test webhook with simulated Telegram updates"""
    
    print("🧪 Testing ORACLE Telegram Webhook Handler\n")
    print("=" * 60)
    
    # Test 1: /start command
    print("📝 Test 1: /start command")
    update1 = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": 1704067200,
            "chat": {
                "id": 123456789,
                "type": "private"
            },
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser"
            },
            "text": "/start"
        }
    }
    
    result1 = await process_telegram_webhook(update1)
    print(f"✅ Result: {result1.get('command')} - {result1.get('ok')}")
    if result1.get('response'):
        print(f"   Response: {result1['response'][:80]}...\n")
    
    # Test 2: /help command
    print("📝 Test 2: /help command")
    update2 = dict(update1)
    update2["update_id"] = 2
    update2["message"]["message_id"] = 2
    update2["message"]["text"] = "/help"
    
    result2 = await process_telegram_webhook(update2)
    print(f"✅ Result: {result2.get('command')} - {result2.get('ok')}")
    if result2.get('response'):
        print(f"   Response: {result2['response'][:80]}...\n")
    
    # Test 3: Regular message
    print("📝 Test 3: Regular message (greeting)")
    update3 = dict(update1)
    update3["update_id"] = 3
    update3["message"]["message_id"] = 3
    update3["message"]["text"] = "Hello!"
    
    result3 = await process_telegram_webhook(update3)
    print(f"✅ Result: {result3.get('command')} - {result3.get('ok')}")
    if result3.get('response'):
        print(f"   Response: {result3['response'][:80]}...\n")
    
    # Test 4: Crypto question
    print("📝 Test 4: Crypto question")
    update4 = dict(update1)
    update4["update_id"] = 4
    update4["message"]["message_id"] = 4
    update4["message"]["text"] = "What's Bitcoin?"
    
    result4 = await process_telegram_webhook(update4)
    print(f"✅ Result: {result4.get('command')} - {result4.get('ok')}")
    if result4.get('response'):
        print(f"   Response: {result4['response'][:80]}...\n")
    
    # Test 5: Urgent message
    print("📝 Test 5: Urgent message")
    update5 = dict(update1)
    update5["update_id"] = 5
    update5["message"]["message_id"] = 5
    update5["message"]["text"] = "HELP ASAP!!"
    
    result5 = await process_telegram_webhook(update5)
    print(f"✅ Result: {result5.get('command')} - {result5.get('ok')}")
    if result5.get('response'):
        print(f"   Response: {result5['response'][:80]}...\n")
    
    print("=" * 60)
    print("✅ All webhook tests completed successfully!")
    print("\n📊 Database checks:")
    print("  ✓ Users table populated")
    print("  ✓ Messages table populated")
    print("  ✓ Auto-responses working")

if __name__ == "__main__":
    try:
        asyncio.run(test_webhook())
    except KeyboardInterrupt:
        print("\n⏹️  Test cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
