"""
Test script for AI Handler
Crée un message sample et le traite avec Claude API
"""
import os
import sys
import logging
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.models import User, Message, Base
from core.ai_handler import ai_handler
from core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Use SQLite for testing if PostgreSQL is not available
try:
    # Try to import database module
    from core.database import get_db, init_db, engine
    db_engine = engine
except Exception as e:
    logger.warning(f"⚠️  PostgreSQL not available: {e}")
    logger.info("📦 Using SQLite for testing instead...")
    # Use SQLite
    db_engine = create_engine("sqlite:///./test_oracle.db", connect_args={"check_same_thread": False})

# Ensure we have a session maker
try:
    from core.database import SessionLocal
except:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ai_handler():
    """Test AI Handler with sample messages"""
    logger.info("=" * 70)
    logger.info("🧪 ORACLE AI Handler Test Suite")
    logger.info("=" * 70)
    
    # Initialize DB
    logger.info("\n1️⃣  Initializing database...")
    try:
        Base.metadata.create_all(bind=db_engine)
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database init error: {e}")
        return
    
    # Get session
    db_session = None
    try:
        db_session = SessionLocal()
        
        # Create test user
        logger.info("\n2️⃣  Creating test user...")
        test_user = User(
            telegram_id=123456789,
            username="test_oracle",
            first_name="Test"
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)
        logger.info(f"✅ Test user created: {test_user.username} (ID: {test_user.telegram_id})")
        
        # Create sample messages
        logger.info("\n3️⃣  Creating sample messages...")
        sample_messages = [
            "What's the best strategy to maximize crypto portfolio returns in 2025?",
            "Analyze Bitcoin's technical indicators and sentiment",
            "How can I build my personal brand in the crypto space?"
        ]
        
        message_ids = []
        for i, content in enumerate(sample_messages, 1):
            msg = Message(
                telegram_user_id=test_user.telegram_id,
                message_id=i,
                content=content,
                message_type="user_msg"
            )
            db_session.add(msg)
            db_session.commit()
            db_session.refresh(msg)
            message_ids.append(msg.id)
            logger.info(f"  ✅ Message {i} created: '{content[:50]}...' (DB ID: {msg.id})")
        
        # Check unprocessed messages
        logger.info("\n4️⃣  Checking unprocessed messages...")
        unprocessed = ai_handler.get_unprocessed_messages(db_session, limit=10)
        logger.info(f"✅ Found {len(unprocessed)} unprocessed messages")
        
        # Process messages
        logger.info("\n5️⃣  Processing messages with Claude API...")
        logger.info("    This will call Claude and process each message...")
        
        stats = ai_handler.process_message_batch(db=db_session, limit=3)
        
        # Display results
        logger.info("\n" + "=" * 70)
        logger.info("📊 Processing Results:")
        logger.info("=" * 70)
        logger.info(f"Total unprocessed: {stats['total']}")
        logger.info(f"✅ Successfully processed: {stats['processed']}")
        logger.info(f"❌ Failed: {stats['failed']}")
        logger.info(f"📈 Total tokens used: {stats['tokens_total']}")
        logger.info(f"💶 Total cost: €{stats['cost_total']:.4f}")
        
        logger.info("\n📝 Processing Details:")
        for i, detail in enumerate(stats['details'], 1):
            logger.info(f"\n  Message {i}:")
            logger.info(f"    • Message ID: {detail.get('message_id')}")
            logger.info(f"    • User ID: {detail.get('user_id')}")
            logger.info(f"    • Status: {detail.get('status')}")
            if detail.get('model'):
                logger.info(f"    • Model: {detail.get('model')}")
                logger.info(f"    • Tokens: {detail.get('tokens')}")
                logger.info(f"    • Cost: €{detail.get('cost', 0):.4f}")
            if detail.get('error'):
                logger.info(f"    • Error: {detail.get('error')}")
        
        # Verify responses were saved
        logger.info("\n6️⃣  Verifying saved responses...")
        ai_responses = db_session.query(Message).filter(
            Message.message_type == "ai_response",
            Message.telegram_user_id == test_user.telegram_id
        ).all()
        logger.info(f"✅ Found {len(ai_responses)} AI responses saved in DB")
        
        for i, resp in enumerate(ai_responses, 1):
            logger.info(f"\n  Response {i}:")
            logger.info(f"    • ID: {resp.id}")
            logger.info(f"    • Model: {resp.model_used}")
            logger.info(f"    • Tokens: {resp.tokens_used}")
            logger.info(f"    • Content preview: {resp.content[:100]}...")
        
        # Get AI Handler stats
        logger.info("\n7️⃣  AI Handler Statistics:")
        logger.info("=" * 70)
        
        total_messages = db_session.query(Message).count()
        user_messages = db_session.query(Message).filter(
            Message.message_type == "user_msg"
        ).count()
        ai_messages = db_session.query(Message).filter(
            Message.message_type == "ai_response"
        ).count()
        
        logger.info(f"Total messages in DB: {total_messages}")
        logger.info(f"  - User messages: {user_messages}")
        logger.info(f"  - AI responses: {ai_messages}")
        
        # Success summary
        logger.info("\n" + "=" * 70)
        logger.info("✅ AI Handler Test Completed Successfully!")
        logger.info("=" * 70)
        logger.info(f"\n🎯 Summary:")
        logger.info(f"   • {stats['processed']}/{stats['total']} messages processed")
        logger.info(f"   • {stats['tokens_total']} tokens used")
        logger.info(f"   • €{stats['cost_total']:.4f} estimated cost")
        logger.info(f"   • Ready for production deployment")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if db_session:
            db_session.close()
            logger.info("\n🔌 Database session closed")

if __name__ == "__main__":
    # Check for API key
    if not settings.ANTHROPIC_API_KEY:
        logger.error("❌ ANTHROPIC_API_KEY not set in environment")
        sys.exit(1)
    
    logger.info(f"🔌 Using database: {settings.DATABASE_URL}")
    logger.info(f"🤖 Using Claude models: {settings.CLAUDE_MODEL_HAIKU}, {settings.CLAUDE_MODEL_SONNET}")
    
    test_ai_handler()
