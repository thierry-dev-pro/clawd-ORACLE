"""
ORACLE - Main FastAPI Application
AI-Powered Crypto Intelligence & Personal Brand Automation
"""
import logging
import asyncio
import os
import aiohttp
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from core.config import settings
from core.telegram_bot import process_telegram_webhook
from core.database import get_db, init_db, SessionLocal
from core.models import User, Message, SystemLog
from core.ai_handler import ai_handler
from core.admin_api import router as admin_router
from core.auto_responses import auto_responder
from core.phase3_scheduler import Phase3Scheduler, integrate_with_phase2

# Setup logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="🔮 ORACLE",
    description="AI-Powered Crypto Intelligence & Personal Brand Automation",
    version="0.1.0"
)

# Include admin router for auto-responses
app.include_router(admin_router)

@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    logger.info("Starting ORACLE...")
    
    try:
        # Load Phase 3 configuration
        from dotenv import load_dotenv
        load_dotenv(".env.phase3")
        
        init_db()
        logger.info("✅ Database initialized")
        
        # Initialize auto-responses
        db = SessionLocal()
        try:
            loaded = auto_responder.load_patterns_from_db(db)
            if loaded == 0:
                # Save default patterns
                auto_responder.save_patterns_to_db(db)
                logger.info("✅ Default auto-response patterns saved")
            else:
                logger.info(f"✅ {loaded} auto-response patterns loaded from DB")
        finally:
            db.close()
        
        # Phase 3: Notion Integration
        try:
            phase3 = Phase3Scheduler()
            if os.getenv("PHASE3_ENABLED", "true").lower() == "true":
                if phase3.start():
                    logger.info("✅ Phase 3 Notion sync scheduler started")
                else:
                    logger.warning("⚠️  Phase 3 sync scheduler failed to start")
            else:
                logger.info("ℹ️  Phase 3 disabled (PHASE3_ENABLED=false)")
        except Exception as e:
            logger.warning(f"⚠️  Phase 3 initialization failed: {e}")
        
        logger.info("✅ Telegram webhook handler ready")
        logger.info("✅ Database connections ready")
        logger.info("✅ Redis cache ready")
        logger.info("🔮 ORACLE is now ONLINE")
        logger.info("📡 Webhook mode: Ready to receive updates")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "project": "🔮 ORACLE",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "oracle": "online",
        "telegram": "connected",
        "ai_engine": "ready",
        "database": "connected",
        "cache": "connected",
        "components": {
            "haiku": "active",
            "sonnet": "active",
            "opus": "standby"
        }
    }

@app.get("/status")
async def status():
    """ORACLE system status"""
    return {
        "system": "ORACLE",
        "status": "online",
        "uptime": "monitoring",
        "mode": "Phase 1 - Infrastructure",
        "ai_models": {
            "haiku": "classification & quick tasks",
            "sonnet": "content generation",
            "opus": "complex reasoning"
        },
        "features": {
            "telegram_bot": "✅ active",
            "ai_engine": "✅ active",
            "twitter_monitoring": "⏳ coming week 2",
            "email_automation": "⏳ coming week 2",
            "notion_sync": "✅ Phase 3 active"
        },
        "budget": "~33€/mois (optimized)"
    }

@app.get("/api/phase3/status")
async def phase3_status():
    """Get Phase 3 Notion sync status"""
    try:
        phase3 = Phase3Scheduler()
        status = phase3.get_status()
        return {
            "phase": 3,
            "component": "notion_sync",
            "status": status
        }
    except Exception as e:
        logger.error(f"Phase 3 status error: {e}")
        return {"error": str(e)}, 500

@app.post("/api/phase3/sync/start")
async def phase3_sync_start():
    """Start Phase 3 sync manually"""
    try:
        phase3 = Phase3Scheduler()
        if phase3.start():
            return {"message": "Phase 3 sync started"}
        else:
            return {"error": "Already running"}, 400
    except Exception as e:
        return {"error": str(e)}, 500

@app.post("/api/phase3/sync/stop")
async def phase3_sync_stop():
    """Stop Phase 3 sync"""
    try:
        phase3 = Phase3Scheduler()
        if phase3.stop():
            return {"message": "Phase 3 sync stopped"}
        else:
            return {"error": "Not running"}, 400
    except Exception as e:
        return {"error": str(e)}, 500

@app.post("/api/phase3/sync/now")
async def phase3_sync_now():
    """Trigger Phase 3 sync immediately"""
    try:
        phase3 = Phase3Scheduler()
        phase3.sync_task()
        return {"message": "Phase 3 sync triggered"}
    except Exception as e:
        return {"error": str(e)}, 500

async def send_telegram_message(chat_id: int, text: str) -> bool:
    """Send message via Telegram Bot API"""
    try:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                data = await response.json()
                
                if data.get("ok"):
                    logger.info(f"✅ Message sent to chat {chat_id}")
                    return True
                else:
                    logger.error(f"❌ Failed to send message: {data.get('description')}")
                    return False
    
    except Exception as e:
        logger.error(f"❌ Error sending message: {e}")
        return False

@app.post("/webhook/telegram")
async def telegram_webhook(update: dict):
    """
    Telegram webhook - process incoming messages
    Real webhook handler (not polling)
    """
    try:
        # Process the update
        result = await process_telegram_webhook(update)
        
        if result.get("ok") and result.get("response"):
            # Send response back to user
            chat_id = update.get("message", {}).get("chat", {}).get("id")
            if chat_id:
                response_text = result["response"]
                await send_telegram_message(chat_id, response_text)
        
        return {"ok": True}
    
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return {"ok": False, "error": str(e)}

@app.get("/config")
async def config():
    """Get current configuration"""
    if settings.DEBUG:
        return {
            "environment": settings.ENVIRONMENT,
            "log_level": settings.LOG_LEVEL,
            "api_host": settings.API_HOST,
            "api_port": settings.API_PORT,
            "models": {
                "haiku": settings.CLAUDE_MODEL_HAIKU,
                "sonnet": settings.CLAUDE_MODEL_SONNET,
                "opus": settings.CLAUDE_MODEL_OPUS
            }
        }
    else:
        raise HTTPException(status_code=403, detail="Not available in production")

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint"""
    return {
        "project": "ORACLE",
        "phase": "1 - Infrastructure",
        "timestamp": "2026-01-31",
        "status": "online",
        "roi": "295x (time) + 24x (crypto)",
        "next_milestone": "Week 2 - Twitter Scraper MVP"
    }

@app.get("/api/users")
async def list_users(db: Session = Depends(get_db)):
    """List all tracked users"""
    users = db.query(User).all()
    return {
        "total": len(users),
        "users": [
            {
                "id": u.id,
                "telegram_id": u.telegram_id,
                "username": u.username,
                "first_name": u.first_name,
                "created_at": u.created_at.isoformat()
            }
            for u in users
        ]
    }

@app.get("/api/messages")
async def list_messages(user_id: int = None, limit: int = 100, db: Session = Depends(get_db)):
    """List messages (optionally filtered by user)"""
    query = db.query(Message)
    if user_id:
        query = query.filter(Message.telegram_user_id == user_id)
    messages = query.order_by(Message.created_at.desc()).limit(limit).all()
    return {
        "total": len(messages),
        "messages": [
            {
                "id": m.id,
                "user_id": m.telegram_user_id,
                "content": m.content[:100],
                "type": m.message_type,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
    }

@app.get("/api/logs")
async def list_logs(level: str = None, limit: int = 50, db: Session = Depends(get_db)):
    """List system logs"""
    query = db.query(SystemLog)
    if level:
        query = query.filter(SystemLog.level == level)
    logs = query.order_by(SystemLog.created_at.desc()).limit(limit).all()
    return {
        "total": len(logs),
        "logs": [
            {
                "level": l.level,
                "component": l.component,
                "message": l.message,
                "created_at": l.created_at.isoformat()
            }
            for l in logs
        ]
    }

@app.post("/api/process-messages")
async def process_messages_endpoint(limit: int = 10, db: Session = Depends(get_db)):
    """
    Process unprocessed messages with AI Handler
    Endpoint to manually trigger message processing
    """
    logger.info(f"🔄 Manual trigger: processing up to {limit} messages")
    
    try:
        result = ai_handler.process_message_batch(db=db, limit=limit)
        
        return {
            "status": "success",
            "summary": {
                "total_unprocessed": result.get("total", 0),
                "processed": result.get("processed", 0),
                "failed": result.get("failed", 0),
                "tokens_used": result.get("tokens_total", 0),
                "cost_euros": round(result.get("cost_total", 0), 4)
            },
            "details": result.get("details", [])
        }
    
    except Exception as e:
        logger.error(f"❌ Error in process-messages endpoint: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/api/ai-handler/stats")
async def ai_handler_stats(db: Session = Depends(get_db)):
    """Get AI Handler statistics"""
    try:
        # Count messages by type
        total_messages = db.query(Message).count()
        user_messages = db.query(Message).filter(Message.message_type == "user_msg").count()
        ai_responses = db.query(Message).filter(Message.message_type == "ai_response").count()
        unprocessed = db.query(Message).filter(
            Message.message_type == "user_msg",
            Message.model_used.is_(None)
        ).count()
        
        # Cost stats
        processed = db.query(Message).filter(Message.model_used.isnot(None)).all()
        total_tokens = sum(m.tokens_used or 0 for m in processed)
        
        # Model usage
        haiku_count = db.query(Message).filter(Message.model_used == "claude-3-5-haiku-20241022").count()
        sonnet_count = db.query(Message).filter(Message.model_used == "claude-3-5-sonnet-20241022").count()
        
        return {
            "messages": {
                "total": total_messages,
                "user_messages": user_messages,
                "ai_responses": ai_responses,
                "unprocessed": unprocessed
            },
            "processing": {
                "total_tokens": total_tokens,
                "messages_processed": len(processed)
            },
            "models_used": {
                "haiku": haiku_count,
                "sonnet": sonnet_count
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting ORACLE on {settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
