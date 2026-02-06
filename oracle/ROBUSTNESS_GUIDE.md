# ORACLE Robustness Enhancement Guide

## Overview

This document outlines the comprehensive robustification of the ORACLE project with focus on three critical areas:

1. **Error Handling + Validation** (Priority 1)
2. **Security** (Priority 2)
3. **Monitoring + Alerts** (Priority 4)

---

## 1. Error Handling + Validation (Priority 1)

### 1.1 Pydantic Models (`core/schemas.py`)

All inputs are now validated through comprehensive Pydantic models:

#### Telegram Message Validation
```python
from core.schemas import TelegramWebhookUpdate

# Automatically validates:
# - User ID format and bounds
# - Username format (5-32 chars, alphanumeric)
# - Message text (1-4096 chars)
# - Chat type (private, group, supergroup, channel)
# - Language codes (ISO 639-1)

update = TelegramWebhookUpdate.parse_obj(webhook_data)
```

#### Command Validation
```python
from core.schemas import CommandRequest, CommandType

cmd = CommandRequest(
    command=CommandType.ALPHA,
    args=["description"],
    raw_text="/alpha description"
)
# Validates: command exists, args count < 10, no empty args
```

#### Alpha Discovery Validation
```python
from core.schemas import AlphaRequest

alpha = AlphaRequest(
    description="BTC price moving up 15%",
    confidence=0.85,
    tags=["bullish", "btc"]
)
# Validates:
# - Description 10-2000 chars
# - No SQL injection patterns
# - Confidence 0.0-1.0
# - Max 10 tags
```

### 1.2 Exception Hierarchy (`core/exceptions.py`)

Comprehensive exception hierarchy with context preservation:

```python
from core.exceptions import (
    OracleException,
    ValidationError,
    SecurityError,
    AIError,
    DatabaseError
)

# All exceptions include:
# - error_code: Unique error identifier
# - message: Technical message
# - user_message: Safe user-facing message
# - details: Additional context
# - context: Operational context
# - timestamp: When error occurred
# - traceback: Exception traceback

try:
    # Operation
except OracleException as e:
    error_dict = e.to_dict()
    e.log(logger)  # Log with full context
```

### 1.3 Systematic Error Handling

**Pattern**: Try/Catch with Graceful Degradation

```python
from core.exceptions import ErrorHandler

# Automatic error handling
result = ErrorHandler.safe_execute(
    dangerous_function,
    default_return=None,
    handle_as=AIError,
    context={"user_id": user_id}
)

# Manual error handling with context
try:
    process_message(msg)
except Exception as e:
    error = ErrorHandler.handle(
        e,
        context={"message_id": msg.id},
        logger_obj=logger
    )
    return error_response(error)
```

### 1.4 Contextual Error Messages

All errors provide context-specific messages:

```python
# Technical logs (for debugging)
logger.error("Database query failed", extra={
    "error_code": "DB_QUERY_ERROR",
    "query": "SELECT * FROM users WHERE id = ?",
    "user_id": 123
})

# User-facing messages (safe, non-technical)
response = {
    "success": False,
    "error": "We're having trouble accessing our database",
    "error_code": "DB_QUERY_ERROR",
    "details": None  # Never expose technical details to users
}
```

---

## 2. Security (Priority 2)

### 2.1 Webhook Authentication

**Telegram Webhook Signature Verification** (`core/security.py`)

```python
from core.security import webhook_verifier

# In FastAPI middleware/route
@app.post("/webhook")
async def handle_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Telegram-Bot-Api-Secret-Hash")
    
    try:
        # Verify signature is valid
        webhook_verifier.verify_signature(body.decode(), signature)
        # Process webhook
    except WebhookSignatureError as e:
        logger.warning(f"Invalid webhook: {e}")
        return {"ok": False}
```

**Implementation Details**:
- Uses HMAC-SHA256 verification
- Constant-time comparison (prevents timing attacks)
- Detailed error logging
- Configurable token

### 2.2 Rate Limiting

**Token Bucket Algorithm** (`core/security.py`)

```python
from core.security import rate_limiter

# Per-user rate limiting
@app.post("/message")
async def handle_message(user_id: int, text: str):
    try:
        # Check: max 10 messages per second per user
        rate_limiter.check_limit(
            f"user_{user_id}",
            tokens_per_second=10.0
        )
        # Process message
    except RateLimitError as e:
        return {
            "success": False,
            "error": "Too many requests",
            "retry_after": 60
        }

# Global rate limiting
@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    try:
        # Check: max 100 requests per second globally
        rate_limiter.check_limit(
            "global_ai_requests",
            tokens_per_second=100.0
        )
    except RateLimitError:
        return {"error": "Service overloaded"}
```

**Configuration**:
```python
from core.schemas import RateLimitConfig

config = RateLimitConfig(
    messages_per_user_per_minute=10,
    messages_per_user_per_hour=500,
    ai_requests_per_user_per_day=100,
    global_requests_per_second=100,
    burst_allowance=1.5
)
```

### 2.3 Input Sanitization

**Multi-Level Validation** (`core/security.py`)

```python
from core.security import input_sanitizer

# Comprehensive validation
text = input_sanitizer.validate_and_sanitize(
    user_input,
    max_length=4096,
    check_injection=True
)

# Individual checks
if input_sanitizer.check_sql_injection(text):
    raise ValueError("Potential SQL injection detected")

if input_sanitizer.check_xss(text):
    raise ValueError("Potential XSS attack detected")

if input_sanitizer.check_command_injection(text):
    raise ValueError("Potential command injection detected")
```

**Protection Patterns**:
- SQL injection: Detects UNION, SELECT, DROP, etc.
- XSS: Detects script tags, event handlers
- Command injection: Detects shell metacharacters
- Special characters: Removes null bytes, controls

### 2.4 Secure Configuration

**Environment Variables (.env)**:

```bash
# Bot Credentials
TELEGRAM_TOKEN=your_bot_token_here
ANTHROPIC_API_KEY=your_api_key_here

# Database (never hardcode)
DATABASE_URL=postgresql://user:pass@localhost/oracle

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
WEBHOOK_SECRET=your_webhook_secret_token
API_KEYS=sk_xxxxx,sk_yyyyy

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

**Load Configuration Safely**:
```python
from core.config import settings

# Settings are loaded from .env
# Never fallback to insecure defaults in production
assert settings.TELEGRAM_TOKEN, "TELEGRAM_TOKEN must be set"
assert settings.ANTHROPIC_API_KEY, "ANTHROPIC_API_KEY must be set"

# All sensitive values are strings, never logged
```

### 2.5 API Key Management

**Generate and Manage API Keys** (`core/security.py`)

```python
from core.security import api_key_manager

# Generate new key
key = api_key_manager.generate_key()  # Returns: sk_xxxxx...

# Add key with scopes and expiration
api_key_manager.add_key(
    key,
    name="Data Analysis API",
    scopes=["read", "analyze"],
    expires_in_days=90
)

# Validate key and scopes
try:
    api_key_manager.validate_key(
        request_key,
        required_scopes=["read"]
    )
except InvalidAPIKeyError as e:
    return {"error": str(e.user_message)}
```

---

## 3. Monitoring + Alerts (Priority 4)

### 3.1 Structured Logging

**JSON Logging** (`core/logging_config.py`)

```python
from core.logging_config import setup_logging

logger = setup_logging(
    log_level="INFO",
    log_dir="logs",
    json_format=True  # JSON in production
)

# Logs automatically include:
# - timestamp
# - level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
# - logger name
# - function + line number
# - process/thread IDs
# - extra fields (custom)

logger.error("Message processing failed", extra={
    "extra_fields": {
        "user_id": 123,
        "message_id": 456,
        "error_type": "ai_timeout"
    }
})
```

**Log Files**:
- `logs/oracle.log` - All logs (rotated at 10MB, 10 backups)
- `logs/oracle_errors.log` - Errors only
- `logs/oracle_json.log` - JSON format (production)

### 3.2 Metrics Collection

**Automatic Metrics** (`core/logging_config.py`)

```python
from core.logging_config import metrics_collector

# Record events (call in handlers)
metrics_collector.record_message()
metrics_collector.record_user()
metrics_collector.record_ai_task(status="completed")
metrics_collector.record_response_time(duration_ms=450)
metrics_collector.record_error(error_type="ai_timeout")
metrics_collector.record_tokens(tokens=2500, cost=0.075)

# Get summary
summary = metrics_collector.get_summary()
# Returns: {
#   "total_messages": 1500,
#   "total_users": 250,
#   "average_response_time_ms": 425.3,
#   "error_rate": 0.0023,
#   "tokens_used": 875000,
#   "cost_usd": 12.45,
#   "uptime_seconds": 86400
# }
```

### 3.3 Health Checks

**System Health Monitoring** (`core/logging_config.py`)

```python
from core.logging_config import health_checker

# Update component status
health_checker.set_component_status("database", "healthy")
health_checker.set_component_status("redis", "degraded")
health_checker.set_component_status("ai_engine", "unhealthy")

# Get overall status
status = health_checker.get_status()  # Returns: "unhealthy"

# Get detailed report
report = health_checker.get_report()
# Returns: {
#   "status": "unhealthy",
#   "components": {
#     "database": "healthy",
#     "redis": "degraded",
#     "ai_engine": "unhealthy",
#     "telegram": "healthy",
#     "api": "healthy"
#   },
#   "last_check": "2024-01-15T10:30:00",
#   "timestamp": "2024-01-15T10:31:00"
# }
```

### 3.4 Alert System

**Critical Error Alerts** (`core/logging_config.py`)

```python
from core.logging_config import alert_system

# Register alert handlers
def telegram_alert_handler(alert):
    # Send alert via Telegram
    send_telegram_message(f"🚨 {alert['message']}")

def email_alert_handler(alert):
    # Send alert via Email
    send_email_alert(alert)

alert_system.register_handler(telegram_alert_handler)
alert_system.register_handler(email_alert_handler)

# Trigger alerts
alert_system.trigger_alert(
    message="Database connection failed",
    level="CRITICAL",
    details={"error": "Connection timeout after 30s"}
)

# Get recent critical alerts
critical_alerts = alert_system.get_recent_alerts(
    limit=10,
    min_level="ERROR"
)
```

### 3.5 Health Check Endpoint

**FastAPI Health Endpoint**:

```python
from fastapi import APIRouter
from core.logging_config import health_checker, metrics_collector
from core.schemas import HealthCheckResponse, MetricsResponse

router = APIRouter()

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check system health status"""
    report = health_checker.get_report()
    return HealthCheckResponse(
        status=report["status"],
        components=report["components"],
        uptime_seconds=metrics_collector.get_uptime_seconds(),
        version="2.0.0"
    )

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system metrics"""
    return MetricsResponse(**metrics_collector.get_summary())
```

---

## Implementation Checklist

### Phase 1: Core Infrastructure (Priority 1)
- [x] Create Pydantic schemas for all inputs
- [x] Define exception hierarchy
- [x] Implement error handling utilities
- [x] Add logging configuration
- [ ] Integrate error handling in telegram_bot.py
- [ ] Add validation to all API endpoints

### Phase 2: Security (Priority 2)
- [x] Implement webhook verification
- [x] Create rate limiting system
- [x] Add input sanitization
- [x] Implement API key management
- [ ] Add authentication middleware
- [ ] Implement HTTPS enforcement
- [ ] Add CORS configuration
- [ ] Review and harden all database queries

### Phase 3: Monitoring (Priority 4)
- [x] Set up structured logging
- [x] Implement metrics collection
- [x] Create health check system
- [x] Add alert system
- [ ] Create Grafana dashboard
- [ ] Set up log aggregation (ELK/Loki)
- [ ] Configure monitoring alerts
- [ ] Create runbooks for alerts

### Phase 4: Testing & Documentation
- [x] Create security tests
- [x] Create validation tests
- [ ] Create integration tests
- [ ] Create performance tests
- [ ] Document all error codes
- [ ] Create troubleshooting guide
- [ ] Create deployment guide

---

## Running Tests

```bash
# Install pytest
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_security.py -v

# Run with coverage
pytest tests/ --cov=core --cov-report=html
```

---

## Deployment Checklist

### Pre-Production
- [ ] All tests passing (100% coverage on critical paths)
- [ ] Security audit completed
- [ ] Rate limiting configured appropriately
- [ ] Error messages reviewed (no data leakage)
- [ ] Logging configured for production (JSON format)
- [ ] Health check endpoint verified
- [ ] Metrics collection enabled
- [ ] Alert handlers configured
- [ ] Database backups tested
- [ ] Disaster recovery plan in place

### Production
- [ ] Environment variables set correctly
- [ ] Webhook signature verification enabled
- [ ] Rate limiting active
- [ ] Input sanitization active
- [ ] Monitoring and alerts active
- [ ] Log aggregation working
- [ ] Health checks passing
- [ ] Metrics being collected
- [ ] On-call rotation established
- [ ] Incident response plan ready

---

## Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Logging](https://docs.python.org/3/library/logging.html)

---

## Support

For questions or issues:
1. Check the troubleshooting guide
2. Review logs for error codes and details
3. Consult the error handling documentation
4. Review test cases for usage examples
