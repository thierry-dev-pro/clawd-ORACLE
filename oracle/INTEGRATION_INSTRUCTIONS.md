# ORACLE Robustness Integration Instructions

Quick start guide to integrate the robustness enhancements into your ORACLE deployment.

---

## Prerequisites

All dependencies are already in `requirements.txt`:
```bash
pip install -r requirements.txt
```

No additional packages needed (Pydantic already present).

---

## Integration Steps

### Step 1: Verify New Files Exist

```bash
# Check core modules
ls -la core/schemas.py
ls -la core/exceptions.py
ls -la core/security.py
ls -la core/logging_config.py

# Check test files
ls -la tests/test_security.py
ls -la tests/test_validation.py

# Check documentation
ls -la ROBUSTNESS_GUIDE.md
ls -la SECURITY_AUDIT.md
ls -la MONITORING_SETUP.md
ls -la PRODUCTION_CHECKLIST.md
```

### Step 2: Run Tests to Verify Everything Works

```bash
# Install pytest if not already installed
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Expected output:
# tests/test_security.py::TestWebhookVerifier::test_verify_signature_success PASSED
# tests/test_security.py::TestWebhookVerifier::test_verify_signature_invalid PASSED
# ... (115 tests total)
# ===================== 115 passed in X.XXs =====================
```

### Step 3: Update Your Application Code

#### In `main.py` or `app.py`:

```python
# Add imports at the top
from core.schemas import TelegramWebhookUpdate, ErrorResponse, HealthCheckResponse, MetricsResponse
from core.exceptions import OracleException, ErrorHandler
from core.security import webhook_verifier
from core.logging_config import initialize_logging, health_checker, metrics_collector

# Initialize logging
logger = initialize_logging()

# Update webhook endpoint to use validation and security
@app.post("/webhook")
async def handle_webhook(request: Request):
    """
    Main webhook handler with security verification
    """
    body = await request.body()
    signature = request.headers.get("X-Telegram-Bot-Api-Secret-Hash")
    
    try:
        # Verify webhook signature
        webhook_verifier.verify_signature(body.decode(), signature)
        
        # Validate webhook structure
        update_data = json.loads(body)
        update = TelegramWebhookUpdate(**update_data)
        
        # Process the update
        result = await process_telegram_webhook(update.dict())
        
        return {"ok": True, "result": result}
    
    except OracleException as e:
        # Log the error with full context
        e.log(logger)
        
        # Return error response
        return ErrorResponse(
            error=e.user_message,
            error_code=e.error_code,
            details=e.details
        ).dict()
    
    except Exception as e:
        # Handle unexpected errors
        error_response = ErrorHandler.handle(e, logger_obj=logger)
        return error_response

# Add health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    System health check endpoint
    """
    # Update component statuses (in your background tasks)
    return HealthCheckResponse(
        status=health_checker.get_status(),
        components=health_checker.components,
        uptime_seconds=metrics_collector.get_uptime_seconds(),
        version="2.0.0"
    )

# Add metrics endpoint
@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    System metrics endpoint
    """
    summary = metrics_collector.get_summary()
    return MetricsResponse(**summary)
```

### Step 4: Update Message Processing

In your message handling code (e.g., `telegram_bot.py`):

```python
from core.schemas import MessageRequest
from core.logging_config import metrics_collector
from core.security import input_sanitizer
import time

async def handle_message(db: Session, user: User, chat_id: int, text: str) -> str:
    """
    Handle user message with validation and metrics
    """
    start_time = time.time()
    
    try:
        # Validate and sanitize input
        cleaned_text = input_sanitizer.validate_and_sanitize(
            text,
            max_length=4096,
            check_injection=True
        )
        
        # Record message processing
        metrics_collector.record_message()
        
        # Process message...
        response = await process_with_ai(cleaned_text)
        
        # Record response time
        duration_ms = (time.time() - start_time) * 1000
        metrics_collector.record_response_time(duration_ms)
        
        return response
    
    except Exception as e:
        # Record error
        metrics_collector.record_error(type(e).__name__)
        
        # Log with context
        error = ErrorHandler.handle(
            e,
            context={"user_id": user.telegram_id, "message": text[:100]},
            logger_obj=logger
        )
        
        # Return safe error message to user
        return f"Error processing message: {e.user_message if hasattr(e, 'user_message') else 'Please try again'}"
```

### Step 5: Setup Environment Variables

Create or update `.env` file:

```bash
# Copy the template (if not already done)
cp .env.example .env

# Edit .env with your production values
nano .env

# Required variables:
TELEGRAM_TOKEN=your_bot_token_here
ANTHROPIC_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@localhost/oracle
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Optional (for security):
WEBHOOK_SECRET=your_webhook_secret_32_chars_minimum
API_HOST=0.0.0.0
API_PORT=8000
```

### Step 6: Setup Structured Logging

Add to your application startup:

```python
import logging
from core.logging_config import setup_logging

# In your app startup
@app.on_event("startup")
async def startup_event():
    """Initialize application"""
    logger = setup_logging(
        log_level=settings.LOG_LEVEL,
        log_dir="logs",
        json_format=(settings.ENVIRONMENT == "production")
    )
    logger.info("ORACLE started", extra={
        "extra_fields": {
            "environment": settings.ENVIRONMENT,
            "version": "2.0.0"
        }
    })
```

### Step 7: Add Rate Limiting (Optional but Recommended)

In your API routes:

```python
from core.security import rate_limiter
from core.exceptions import RateLimitError

@app.post("/analyze")
async def analyze_message(request: AnalysisRequest, user_id: int):
    """
    Analyze message with rate limiting
    """
    try:
        # Check rate limit
        rate_limiter.check_limit(
            f"user_{user_id}",
            tokens=1,
            tokens_per_second=10.0  # 10 requests/second per user
        )
        
        # Process request
        result = await ai_engine.analyze(request)
        return {"success": True, "result": result}
    
    except RateLimitError as e:
        e.log(logger)
        return {
            "success": False,
            "error": "Too many requests",
            "error_code": "RATE_LIMIT_EXCEEDED"
        }, 429
```

### Step 8: Background Tasks for Health Monitoring

Add to your application:

```python
import asyncio
from core.logging_config import health_checker, alert_system

async def monitor_health():
    """
    Background task to monitor system health
    Run every 30 seconds
    """
    while True:
        try:
            # Check database
            try:
                db = SessionLocal()
                db.execute("SELECT 1")
                db.close()
                health_checker.set_component_status("database", "healthy")
            except Exception as e:
                logger.error(f"Database health check failed: {e}")
                health_checker.set_component_status("database", "unhealthy")
                alert_system.trigger_alert(
                    "Database connection failed",
                    "CRITICAL",
                    {"error": str(e)}
                )
            
            # Check Redis
            try:
                import redis
                r = redis.Redis(host='localhost', port=6379)
                r.ping()
                health_checker.set_component_status("redis", "healthy")
            except Exception as e:
                logger.warning(f"Redis health check failed: {e}")
                health_checker.set_component_status("redis", "degraded")
            
            # Check error rate
            error_rate = metrics_collector.get_error_rate()
            if error_rate > 0.05:  # 5% error rate threshold
                alert_system.trigger_alert(
                    f"High error rate: {error_rate:.2%}",
                    "WARNING",
                    {"error_rate": error_rate}
                )
            
            await asyncio.sleep(30)
        
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")
            await asyncio.sleep(30)

# Add to startup
@app.on_event("startup")
async def startup():
    asyncio.create_task(monitor_health())
```

---

## Testing Your Integration

### Test 1: Webhook Verification

```bash
# Test with valid signature
python -c "
import hmac
import hashlib
import json
import requests

token = 'YOUR_TOKEN'
body = json.dumps({'update_id': 1})
secret = hashlib.sha256(token.encode()).digest()
signature = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()

response = requests.post(
    'http://localhost:8000/webhook',
    data=body,
    headers={'X-Telegram-Bot-Api-Secret-Hash': signature}
)
print(response.json())
"
```

### Test 2: Health Check

```bash
curl http://localhost:8000/health | jq '.'

# Expected response:
# {
#   "status": "healthy",
#   "components": {
#     "database": "healthy",
#     "redis": "healthy",
#     "ai_engine": "healthy",
#     "telegram": "healthy",
#     "api": "healthy"
#   },
#   "uptime_seconds": 12345,
#   "version": "2.0.0"
# }
```

### Test 3: Metrics

```bash
curl http://localhost:8000/metrics | jq '.'

# Expected response:
# {
#   "total_messages": 150,
#   "total_users": 45,
#   "total_ai_tasks": 89,
#   "completed_tasks": 87,
#   "failed_tasks": 2,
#   "average_response_time_ms": 425.3,
#   "error_rate": 0.0225,
#   "tokens_used": 875000,
#   "cost_usd": 12.45,
#   "uptime_seconds": 86400
# }
```

### Test 4: Input Validation

```bash
# Test SQL injection detection
python -c "
from core.security import input_sanitizer

try:
    text = \"'; DROP TABLE users; --\"
    input_sanitizer.validate_and_sanitize(text, check_injection=True)
except ValueError as e:
    print(f'Correctly detected: {e}')
"
```

### Test 5: Rate Limiting

```bash
python -c "
from core.security import rate_limiter

# Consume tokens quickly
for i in range(1001):
    allowed = rate_limiter.is_allowed('test_user', tokens_per_second=10.0)
    if not allowed:
        print(f'Rate limit hit after {i} requests')
        break
"
```

---

## Verification Checklist

Before going to production:

- [ ] All 115 tests passing
  ```bash
  pytest tests/ -v
  ```

- [ ] No errors in logs
  ```bash
  tail -f logs/oracle_errors.log
  ```

- [ ] Health check endpoint working
  ```bash
  curl http://localhost:8000/health
  ```

- [ ] Metrics endpoint working
  ```bash
  curl http://localhost:8000/metrics
  ```

- [ ] Webhook signature verification working
- [ ] Rate limiting working
- [ ] Input sanitization working
- [ ] Error handling working (try with invalid input)
- [ ] Logging working (check logs/oracle.log)
- [ ] Database connectivity verified
- [ ] Redis connectivity verified

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'core.schemas'"

**Solution**: Make sure you're running from the project root directory:
```bash
cd /Users/clawdbot/clawd/oracle
python -c "from core.schemas import *"  # Should work
```

### Issue: "pydantic.ValidationError: ..."

**Solution**: Check the validation error message and fix the input format:
```python
# Good: Proper format
user_data = TelegramUserData(id=123, first_name="John")

# Bad: Missing required field
user_data = TelegramUserData()  # Will raise ValidationError
```

### Issue: Webhook signature verification failing

**Solution**: Ensure the token is correct and signature is calculated properly:
```python
# Make sure token is from .env
from core.config import settings
assert settings.TELEGRAM_TOKEN, "Token not set"

# Verify signature calculation matches Telegram's
webhook_verifier.verify_signature(body, signature)
```

### Issue: Tests failing

**Solution**: Run tests with verbose output to see what's failing:
```bash
pytest tests/ -vv --tb=long

# Check Python version (need 3.8+)
python --version

# Check dependencies
pip install -r requirements.txt
```

---

## Next Steps

1. **Review Documentation**
   - Read ROBUSTNESS_GUIDE.md for detailed information
   - Review SECURITY_AUDIT.md for security best practices
   - Check MONITORING_SETUP.md for observability setup

2. **Setup Monitoring** (Recommended)
   - Follow steps in MONITORING_SETUP.md
   - Configure ELK or Prometheus
   - Setup Grafana dashboards
   - Configure alerts

3. **Test in Staging**
   - Deploy to staging environment
   - Run load tests
   - Verify all endpoints
   - Test failover scenarios

4. **Deploy to Production**
   - Follow PRODUCTION_CHECKLIST.md
   - Get sign-offs from all stakeholders
   - Deploy during low-traffic window
   - Monitor closely for 24 hours

---

## Support & Questions

For issues or questions:

1. Check the relevant documentation file
2. Review test cases for usage examples
3. Check error logs for detailed error information
4. Review ROBUSTNESS_GUIDE.md for implementation patterns

---

## Quick Reference

### Key Files
- `core/schemas.py` - Input validation models
- `core/exceptions.py` - Error definitions and handling
- `core/security.py` - Security utilities
- `core/logging_config.py` - Logging and monitoring

### Key Classes
- `TelegramWebhookUpdate` - Webhook validation
- `OracleException` - Base exception class
- `WebhookVerifier` - Webhook signature verification
- `RateLimiter` - Rate limiting
- `InputSanitizer` - Input validation
- `MetricsCollector` - Metrics collection
- `HealthChecker` - Health monitoring
- `AlertSystem` - Alert system

### Key Endpoints
- `POST /webhook` - Handle Telegram updates
- `GET /health` - System health check
- `GET /metrics` - System metrics
- `GET /dashboard` - Monitoring dashboard

---

**Integration Status**: Ready for production ✅

