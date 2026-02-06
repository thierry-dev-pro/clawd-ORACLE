# Phase 3: Main.py Integration Guide

## Overview
Integrate Phase 3 Notion scheduler into ORACLE main.py startup event

## Implementation Steps

### Step 1: Import Phase 3 modules at top of main.py

```python
# Add after existing imports
from core.phase3_scheduler import Phase3Scheduler, integrate_with_phase2
from core.scheduler import get_scheduler  # Phase 2 scheduler
```

### Step 2: Add Phase 3 initialization in startup event

Add this to the `startup()` function, after Phase 2 scheduler initialization:

```python
        # Phase 3: Notion Integration
        try:
            scheduler_instance = get_scheduler()
            phase3 = integrate_with_phase2(scheduler_instance)
            
            if os.getenv("PHASE3_ENABLED", "true").lower() == "true":
                if phase3.start():
                    logger.info("✅ Phase 3 Notion sync scheduler started")
                else:
                    logger.warning("⚠️  Phase 3 sync scheduler failed to start")
            else:
                logger.info("ℹ️  Phase 3 disabled (PHASE3_ENABLED=false)")
            
            logger.info(f"📊 Phase 3 status: {phase3.get_status()}")
        except Exception as e:
            logger.error(f"⚠️  Phase 3 initialization failed: {e}")
```

### Step 3: Add Phase 3 status endpoint

Add this new endpoint to main.py:

```python
@app.get("/api/phase3/status")
async def phase3_status():
    """Get Phase 3 Notion sync status"""
    try:
        from core.phase3_scheduler import Phase3Scheduler
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
```

### Step 4: Add Phase 3 control endpoints

```python
@app.post("/api/phase3/sync/start")
async def phase3_sync_start():
    """Start Phase 3 sync manually"""
    try:
        from core.phase3_scheduler import Phase3Scheduler
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
        from core.phase3_scheduler import Phase3Scheduler
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
        from core.phase3_scheduler import Phase3Scheduler
        phase3 = Phase3Scheduler()
        phase3.sync_task()
        return {"message": "Phase 3 sync triggered"}
    except Exception as e:
        return {"error": str(e)}, 500
```

### Step 5: Update requirements.txt

Add Phase 3 dependencies:

```
requests>=2.31.0
python-dotenv>=1.0.0
apscheduler>=3.10.4
```

## Full Startup Example

```python
@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    logger.info("Starting ORACLE...")
    
    try:
        init_db()
        logger.info("✅ Database initialized")
        
        # Phase 2: Auto-responses
        db = SessionLocal()
        try:
            loaded = auto_responder.load_patterns_from_db(db)
            if loaded == 0:
                auto_responder.save_patterns_to_db(db)
                logger.info("✅ Default auto-response patterns saved")
            else:
                logger.info(f"✅ {loaded} auto-response patterns loaded from DB")
        finally:
            db.close()
        
        # Phase 3: Notion Integration
        try:
            scheduler_instance = get_scheduler()
            phase3 = integrate_with_phase2(scheduler_instance)
            
            if os.getenv("PHASE3_ENABLED", "true").lower() == "true":
                if phase3.start():
                    logger.info("✅ Phase 3 Notion sync scheduler started")
                    logger.info(f"📊 Phase 3 status: {phase3.get_status()}")
                else:
                    logger.warning("⚠️  Phase 3 sync scheduler failed to start")
            else:
                logger.info("ℹ️  Phase 3 disabled")
        except Exception as e:
            logger.error(f"⚠️  Phase 3 initialization error: {e}")
        
        logger.info("✅ Telegram webhook handler ready")
        logger.info("🔮 ORACLE is now ONLINE")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
```

## Testing Phase 3 Integration

```bash
# Test script
python scripts/test_phase3_sync.py

# Manual sync trigger
curl -X POST http://localhost:8000/api/phase3/sync/now

# Check status
curl http://localhost:8000/api/phase3/status

# Start scheduler
curl -X POST http://localhost:8000/api/phase3/sync/start

# Stop scheduler
curl -X POST http://localhost:8000/api/phase3/sync/stop
```

## Environment Variables

```bash
# In .env or .env.phase3
NOTION_API_KEY=ntn_YOUR_KEY
NOTION_DATABASE_ID=YOUR_ID
PHASE3_ENABLED=true
PHASE3_SYNC_INTERVAL=3600
PHASE3_LOG_LEVEL=INFO
```

## Debugging

```bash
# Check logs
tail -f logs/phase3_sync.log

# Monitor scheduler
curl http://localhost:8000/api/scheduler/status

# Test Notion connectivity
python -c "from core.notion_sync import NotionSyncHandler; NotionSyncHandler().query_handles_from_notion()"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| API Key not found | Check `.env.phase3` or env vars |
| Database not syncing | Verify NOTION_DATABASE_ID is correct |
| Scheduler not starting | Check logs, ensure APScheduler running |
| Timeout errors | Verify internet connection, Notion API status |

---

**Status**: Ready for implementation ✅
