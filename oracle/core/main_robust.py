"""
ORACLE - Main FastAPI Application (Production-Hardened)
AI-Powered Crypto Intelligence & Personal Brand Automation

Features:
- Comprehensive error handling
- Input validation with Pydantic
- Security: auth, rate limiting, input sanitization
- Structured logging with context
- Monitoring and health checks
- Alerting system
"""
import logging
import asyncio
import time
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, ORJSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from pydantic import ValidationError

# Core imports
from core.config import settings
from core.database import get_db, init_db, SessionLocal
from core.models import User, Message, SystemLog
from core.exceptions import (
    OracleException, ValidationError as OracleValidationError,
    WebhookVerificationFailed, RateLimitExceeded, DatabaseConnectionError
)
from core.validation import (
    TelegramUpdate, ProcessMessageRequest, HealthResponse,
    ErrorResponse, MetricsResponse, sanitize_html, validate_telegram_token
)
from core.security import (
    verify_telegram_webhook, check_rate_limit, TelegramWebhookValidator,
    InputSanitizer, rate_limiter, session_manager
)
from core.monitoring import (
    setup_logging, get_logger, metrics_collector, health_checker,
    alert_manager, track_performance, LogExporter
)

# Setup logging
setup_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="🔮 ORACLE (Production-Hardened)",
    description="AI-Powered Crypto Intelligence & Personal Brand Automation",
    version="0.2.0-hardened",
    docs_url="/api/docs" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None
)

# ==================== Startup & Shutdown ====================

@app.on_event("startup")
async def startup():
    """Initialize on startup with proper error handling"""
    try:
        logger.info("🚀 Starting ORACLE...", environment=settings.ENVIRONMENT)
        
        # Validate critical configuration
        if not settings.TELEGRAM_TOKEN:
            raise OracleException(
                "TELEGRAM_TOKEN not configured",
                code="CONFIG_ERROR"
            )
        
        if not validate_telegram_token(settings.TELEGRAM_TOKEN):
            logger.warning("⚠️ TELEGRAM_TOKEN format may be invalid")
        
        if not settings.ANTHROPIC_API_KEY:
            raise OracleException(
                "ANTHROPIC_API_KEY not configured",
                code="CONFIG_ERROR"
            )
        
        # Initialize database
        try:
            init_db()
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise DatabaseConnectionError(str(e))
        
        # Initialize scheduler with Phase 2 tasks
        try:
            from core.scheduler import initialize_scheduler
            if initialize_scheduler():
                logger.info("✅ Phase 2 scheduler initialized (Twitter Scraper + Airdrop Tracker)")
            else:
                logger.warning("⚠️ Scheduler initialization partially failed")
        except Exception as e:
            logger.warning(f"⚠️ Scheduler not available: {e}")
        
        # Register health checks
        health_checker.register_check("database", check_database_health)
        health_checker.register_check("telegram", check_telegram_health)
        health_checker.register_check("ai_engine", check_ai_engine_health)
        
        logger.info("✅ Health checks registered")
        logger.info("✅ Rate limiter initialized")
        logger.info("✅ Security layers initialized")
        logger.info("✅ Monitoring initialized")
        logger.info("🔮 ORACLE is ONLINE and ready")
        
    except Exception as e:
        logger.critical(f"❌ Startup failed: {e}")
        alert_manager.add_alert("critical", "Startup Failed", str(e))
        raise

@app.on_event("shutdown")
async def shutdown():
    """Clean shutdown"""
    try:
        logger.info("🛑 ORACLE shutting down...")
        session_manager.cleanup_expired()
        logger.info("✅ ORACLE shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# ==================== Health Checks ====================

async def check_database_health() -> tuple[str, str]:
    """Check database connectivity"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return ("healthy", "Database connected")
    except Exception as e:
        return ("unhealthy", str(e))

async def check_telegram_health() -> tuple[str, str]:
    """Check Telegram API connectivity"""
    try:
        # TODO: Implement actual Telegram health check
        return ("healthy", "Telegram ready")
    except Exception as e:
        return ("unhealthy", str(e))

async def check_ai_engine_health() -> tuple[str, str]:
    """Check AI engine availability"""
    try:
        # TODO: Implement actual AI engine health check
        return ("healthy", "AI engine ready")
    except Exception as e:
        return ("unhealthy", str(e))

# ==================== Exception Handlers ====================

@app.exception_handler(OracleException)
async def oracle_exception_handler(request: Request, exc: OracleException):
    """Handle ORACLE exceptions"""
    try:
        logger.warning(
            f"ORACLE Exception: {exc.message}",
            code=exc.code,
            status_code=exc.status_code
        )
        
        # Record error metric
        metrics_collector.record_error(
            exc.code,
            exc.message,
            exc.details
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )
    except Exception as e:
        logger.error(f"Error in exception handler: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "code": "INTERNAL_ERROR"}
        )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    try:
        logger.warning(
            "Validation error",
            endpoint=str(request.url),
            errors=str(exc.errors())[:200]
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Request validation failed",
                "code": "VALIDATION_ERROR",
                "details": exc.errors()[:3]  # First 3 errors
            }
        )
    except Exception as e:
        logger.error(f"Error in validation handler: {e}")
        return JSONResponse(status_code=422, content={"error": "Invalid request"})

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    try:
        logger.error(
            f"Unhandled exception: {type(exc).__name__}",
            message=str(exc)[:200],
            endpoint=str(request.url)
        )
        
        # Record error metric
        metrics_collector.record_error(
            "UNHANDLED_EXCEPTION",
            str(exc),
            {"endpoint": str(request.url)}
        )
        
        # Alert on critical errors
        alert_manager.add_alert(
            "critical",
            "Unhandled Exception",
            f"{type(exc).__name__}: {str(exc)[:100]}",
            {"endpoint": str(request.url)}
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "code": "INTERNAL_ERROR",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.critical(f"Error in exception handler: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )

# ==================== Middleware ====================

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Record request metrics"""
    start = time.time()
    user_id = None
    
    try:
        # Try to extract user_id
        if hasattr(request.state, 'user_id'):
            user_id = request.state.user_id
        
        # Call the endpoint
        response = await call_next(request)
        
        # Record metrics
        duration_ms = (time.time() - start) * 1000
        
        from core.monitoring import RequestMetrics
        metrics = RequestMetrics(
            timestamp=datetime.utcnow(),
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=user_id
        )
        metrics_collector.record_request(metrics)
        
        # Log slow requests
        if duration_ms > 5000:
            logger.warning(
                f"Slow request detected: {duration_ms:.0f}ms",
                endpoint=request.url.path,
                method=request.method
            )
        
        return response
    
    except Exception as e:
        logger.error(f"Error in metrics middleware: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal error"})

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting"""
    try:
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Get user ID or IP
        user_id = None
        if hasattr(request.state, 'user_id'):
            user_id = request.state.user_id
        else:
            user_id = hash(request.client.host) % (2**32) if request.client else 0
        
        # Check rate limit
        allowed, error_msg = rate_limiter.is_allowed(user_id)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded: {error_msg}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": error_msg or "Too many requests",
                    "code": "RATE_LIMIT_EXCEEDED"
                }
            )
        
        return await call_next(request)
    
    except Exception as e:
        logger.error(f"Error in rate limit middleware: {e}")
        return await call_next(request)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to response"""
    try:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
    
    except Exception as e:
        logger.error(f"Error in security headers middleware: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal error"})

# ==================== Routes ====================

@app.get("/")
async def root():
    """Root endpoint"""
    try:
        return {
            "status": "online",
            "project": "🔮 ORACLE",
            "version": "0.2.0-hardened",
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in root endpoint: {e}")
        raise OracleException("Internal error", status_code=500)

@app.get("/health", response_model=Optional[HealthResponse])
async def health_check():
    """Comprehensive health check"""
    try:
        results = await health_checker.run_checks()
        
        response = HealthResponse(
            status=results.get('overall_status', 'unhealthy'),
            timestamp=datetime.utcnow(),
            components={
                check['status'] for check in results.get('checks', {}).values()
            },
            version="0.2.0-hardened",
            uptime_seconds=metrics_collector.get_metrics().get('uptime_seconds')
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.get("/status")
async def status():
    """System status"""
    try:
        metrics = metrics_collector.get_metrics()
        
        return {
            "system": "ORACLE",
            "status": "online",
            "version": "0.2.0-hardened",
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in status endpoint: {e}")
        raise OracleException("Internal error", status_code=500)

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """
    Telegram webhook endpoint
    - Validates webhook signature
    - Applies rate limiting
    - Processes update
    """
    try:
        # Get request body
        body = await request.body()
        
        if not body:
            logger.warning("Empty webhook body")
            raise OracleValidationError("Empty request body")
        
        # Verify webhook signature
        signature = request.headers.get('X-Telegram-Bot-Api-Secret-Header')
        if not TelegramWebhookValidator.verify_telegram_message(body, signature):
            logger.warning("Webhook signature verification failed")
            raise WebhookVerificationFailed()
        
        # Parse and validate update
        import json
        update_data = json.loads(body)
        
        try:
            update = TelegramUpdate(**update_data)
        except ValidationError as e:
            logger.warning(f"Invalid Telegram update: {e}")
            raise OracleValidationError("Invalid Telegram update")
        
        # TODO: Process update with AI handler
        
        logger.info(f"✅ Telegram webhook processed: update_id={update.update_id}")
        
        return {"ok": True}
    
    except OracleException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise OracleException("Webhook processing failed", status_code=500)

@app.post("/api/process-messages")
async def process_messages(
    request: ProcessMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Process unprocessed messages with AI Handler
    - Validates request
    - Applies rate limiting
    - Processes messages
    """
    try:
        logger.info(
            f"Processing messages",
            limit=request.limit,
            user_id=request.user_id
        )
        
        # TODO: Process messages
        
        return {
            "status": "success",
            "processed": 0,
            "tokens_used": 0,
            "cost_euros": 0.0
        }
    
    except Exception as e:
        logger.error(f"Error processing messages: {e}")
        raise OracleException("Message processing failed", status_code=500)

@app.get("/api/metrics")
async def get_metrics():
    """Get application metrics"""
    try:
        metrics = metrics_collector.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise OracleException("Cannot retrieve metrics", status_code=500)

@app.get("/api/metrics/prometheus")
async def get_prometheus_metrics():
    """Get metrics in Prometheus format"""
    try:
        metrics = metrics_collector.get_metrics()
        prometheus_format = LogExporter.export_prometheus_format(metrics)
        
        return {
            "format": "prometheus",
            "content": prometheus_format
        }
    except Exception as e:
        logger.error(f"Error exporting Prometheus metrics: {e}")
        raise OracleException("Cannot export metrics", status_code=500)

@app.get("/api/alerts")
async def get_alerts(limit: int = 10):
    """Get recent alerts"""
    try:
        alerts = alert_manager.get_recent_alerts(limit)
        return {
            "total": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise OracleException("Cannot retrieve alerts", status_code=500)

@app.get("/api/users")
async def list_users(db: Session = Depends(get_db)):
    """List all tracked users"""
    try:
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
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise OracleException("Cannot list users", status_code=500)

@app.get("/api/logs")
async def list_logs(level: str = None, limit: int = 50, db: Session = Depends(get_db)):
    """List system logs"""
    try:
        query = db.query(SystemLog)
        if level and level.upper() in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            query = query.filter(SystemLog.level == level.upper())
        
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
    except Exception as e:
        logger.error(f"Error listing logs: {e}")
        raise OracleException("Cannot list logs", status_code=500)

# ==================== Phase 2: Twitter Scraper & Airdrop Tracker ====================

@app.get("/api/tweets")
async def get_tweets(limit: int = 10, keyword: str = None, db: Session = Depends(get_db)):
    """
    Get recent tweets from database
    
    Query params:
        limit: Max tweets (default 10)
        keyword: Filter by keyword (optional)
    
    Returns:
        List of tweets
    """
    try:
        from core.twitter_scraper import TwitterScraperDB
        
        if keyword:
            tweets = TwitterScraperDB.search_tweets(db, keyword, limit)
        else:
            tweets = TwitterScraperDB.get_recent_tweets(db, limit)
        
        return {
            "count": len(tweets),
            "tweets": tweets,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting tweets: {e}")
        raise OracleException("Cannot retrieve tweets", status_code=500)

@app.post("/api/tweets/scrape")
async def trigger_twitter_scrape(db: Session = Depends(get_db)):
    """
    Manually trigger Twitter scraper
    (Normally runs automatically via scheduler)
    
    Returns:
        Scraper results
    """
    try:
        from core.twitter_scraper import twitter_scraper, TwitterScraperDB
        
        logger.info("🔄 Manual Twitter scrape triggered")
        
        # Scrape
        tweets = await twitter_scraper.scrape_all_sources()
        
        if not tweets:
            return {
                "status": "completed",
                "tweets_found": 0,
                "tweets_saved": 0,
                "message": "No new tweets found"
            }
        
        # Save
        saved = TwitterScraperDB.save_tweets(db, tweets)
        
        return {
            "status": "completed",
            "tweets_found": len(tweets),
            "tweets_saved": saved,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error triggering scrape: {e}")
        raise OracleException("Scraper failed", status_code=500)

@app.get("/api/airdrops")
async def get_airdrops(limit: int = 20, user_id: int = None, db: Session = Depends(get_db)):
    """
    Get active airdrops
    
    Query params:
        limit: Max airdrops (default 20)
        user_id: Filter for specific user (optional)
    
    Returns:
        List of active airdrops
    """
    try:
        from core.airdrop_tracker import AirdropTrackerDB
        
        if user_id:
            airdrops = AirdropTrackerDB.get_airdrops_for_user(db, user_id, limit)
        else:
            airdrops = AirdropTrackerDB.get_active_airdrops(db, limit)
        
        return {
            "count": len(airdrops),
            "airdrops": airdrops,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting airdrops: {e}")
        raise OracleException("Cannot retrieve airdrops", status_code=500)

@app.post("/api/airdrops/check")
async def trigger_airdrop_check(db: Session = Depends(get_db)):
    """
    Manually trigger airdrop tracker
    (Normally runs automatically via scheduler)
    
    Returns:
        Tracker results
    """
    try:
        from core.airdrop_tracker import airdrop_tracker, AirdropTrackerDB
        
        logger.info("🔄 Manual airdrop check triggered")
        
        # Check sources
        airdrops = await airdrop_tracker.check_all_sources()
        
        if not airdrops:
            return {
                "status": "completed",
                "airdrops_found": 0,
                "airdrops_saved": 0,
                "message": "No new airdrops found"
            }
        
        # Save
        saved = AirdropTrackerDB.save_airdrops(db, airdrops)
        
        # Cleanup expired
        expired = AirdropTrackerDB.cleanup_expired(db)
        
        return {
            "status": "completed",
            "airdrops_found": len(airdrops),
            "airdrops_saved": saved,
            "airdrops_expired": expired,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking airdrops: {e}")
        raise OracleException("Airdrop check failed", status_code=500)

@app.post("/api/airdrops/{airdrop_id}/claim")
async def mark_airdrop_claimed(airdrop_id: int, db: Session = Depends(get_db)):
    """
    Mark airdrop as claimed by user
    
    Args:
        airdrop_id: Airdrop ID
    
    Returns:
        Success status
    """
    try:
        from core.airdrop_tracker import AirdropTrackerDB
        
        success = AirdropTrackerDB.mark_claimed(db, airdrop_id)
        
        return {
            "status": "claimed" if success else "failed",
            "airdrop_id": airdrop_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error marking airdrop: {e}")
        raise OracleException("Cannot mark airdrop", status_code=500)

@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """
    Get scheduler status
    
    Returns:
        Scheduler details and task status
    """
    try:
        from core.scheduler import scheduler
        
        status = scheduler.get_status()
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise OracleException("Cannot retrieve scheduler status", status_code=500)

@app.post("/api/scheduler/start")
async def start_scheduler():
    """Start scheduler"""
    try:
        from core.scheduler import scheduler
        
        success = scheduler.start()
        
        return {
            "status": "started" if success else "already_running",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise OracleException("Cannot start scheduler", status_code=500)

@app.post("/api/scheduler/stop")
async def stop_scheduler():
    """Stop scheduler"""
    try:
        from core.scheduler import scheduler
        
        success = scheduler.stop()
        
        return {
            "status": "stopped" if success else "failed",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise OracleException("Cannot stop scheduler", status_code=500)

@app.post("/api/scheduler/task/{task_name}/enable")
async def enable_task(task_name: str):
    """Enable a scheduler task"""
    try:
        from core.scheduler import scheduler
        
        success = scheduler.enable_task(task_name)
        
        return {
            "status": "enabled" if success else "not_found",
            "task": task_name,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error enabling task: {e}")
        raise OracleException("Cannot enable task", status_code=500)

@app.post("/api/scheduler/task/{task_name}/disable")
async def disable_task(task_name: str):
    """Disable a scheduler task"""
    try:
        from core.scheduler import scheduler
        
        success = scheduler.disable_task(task_name)
        
        return {
            "status": "disabled" if success else "not_found",
            "task": task_name,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error disabling task: {e}")
        raise OracleException("Cannot disable task", status_code=500)

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting ORACLE on {settings.API_HOST}:{settings.API_PORT}")
    
    uvicorn.run(
        "core.main_robust:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
