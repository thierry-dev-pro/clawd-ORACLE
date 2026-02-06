# 📊 ORACLE Monitoring & Alerting Setup Guide

## Overview

ORACLE includes comprehensive monitoring with:
- 📊 Real-time metrics collection
- 🏥 Health checks
- 🚨 Alert system
- 📈 Prometheus export
- 🔍 Structured logging
- 📉 Performance tracking

## Quick Start

### 1. Enable Monitoring in main.py

```python
from core.monitoring import setup_logging, metrics_collector, health_checker

# Setup structured logging
setup_logging(settings.LOG_LEVEL)

# Metrics are automatically collected via middleware
# Health checks are registered at startup
```

### 2. Access Metrics Endpoints

```bash
# Get all metrics (JSON)
curl http://localhost:8000/api/metrics

# Get Prometheus format
curl http://localhost:8000/api/metrics/prometheus

# Get alerts
curl http://localhost:8000/api/alerts

# Health check
curl http://localhost:8000/health

# System status
curl http://localhost:8000/status
```

## Metrics Collection

### Automatic Metrics

The `metrics_middleware` automatically tracks:

**Request Metrics**
- Total requests by endpoint
- Status code distribution
- Response time (avg, min, max)
- Error rate
- Requests per minute

**Message Metrics**
- Total messages processed
- Total tokens used
- Average tokens per message
- Processing success/failure rate

**Error Metrics**
- Total errors
- Error rate (%)
- Error types and frequencies
- Recent error traces

**Component Health**
- Database connectivity
- Telegram API status
- AI engine availability
- Cache (Redis) status

### Manual Metrics Recording

```python
from core.monitoring import metrics_collector, RequestMetrics

# Record custom metrics
metrics_collector.message_count += 1
metrics_collector.token_count += tokens

# Record requests
metrics = RequestMetrics(
    timestamp=datetime.utcnow(),
    endpoint="/api/process",
    method="POST",
    status_code=200,
    duration_ms=1250.5,
    user_id=123
)
metrics_collector.record_request(metrics)

# Record errors
metrics_collector.record_error(
    error_type="AI_ERROR",
    message="Claude API timeout",
    context={"model": "claude-3-sonnet", "tokens": 5000}
)
```

## Health Checks

### Available Health Checks

```python
# Registered at startup
health_checker.register_check("database", check_database_health)
health_checker.register_check("telegram", check_telegram_health)
health_checker.register_check("ai_engine", check_ai_engine_health)
```

### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2026-02-02T12:00:00Z",
  "components": {
    "database": "healthy",
    "telegram": "healthy",
    "ai_engine": "degraded"
  },
  "version": "0.2.0-hardened",
  "uptime_seconds": 3600.0
}
```

### Health Status Values
- ✅ `healthy`: Component is working normally
- ⚠️ `degraded`: Component has issues but is operational
- ❌ `unhealthy`: Component is down or non-functional

### Custom Health Checks

```python
async def custom_health_check() -> tuple[str, str]:
    """Custom health check function"""
    try:
        # Your check logic
        result = await check_external_service()
        
        if result.ok:
            return ("healthy", "Service responding normally")
        else:
            return ("degraded", "Service slow response")
    except Exception as e:
        return ("unhealthy", str(e))

# Register the check
health_checker.register_check("custom_service", custom_health_check)
```

## Alerting System

### Alert Levels

- 🟦 **info**: Informational messages
- 🟨 **warning**: Warning conditions
- 🔴 **critical**: Critical issues requiring attention

### Recording Alerts

```python
from core.monitoring import alert_manager

# Add alert
alert_manager.add_alert(
    level="critical",
    title="High Error Rate",
    message="Error rate exceeded 10%",
    context={"error_rate": 0.15}
)
```

### Threshold Configuration

```python
# In core/monitoring.py
alert_manager.thresholds = {
    'error_rate': 0.1,              # 10%
    'response_time_ms': 5000,       # 5 seconds
    'health_check_failures': 2      # consecutive failures
}

# Check thresholds against metrics
alerts = alert_manager.check_thresholds(metrics)
```

### Viewing Alerts

```bash
# Get recent alerts
curl http://localhost:8000/api/alerts?limit=10

# Response
{
  "total": 3,
  "alerts": [
    {
      "timestamp": "2026-02-02T12:00:00Z",
      "level": "critical",
      "title": "High Error Rate",
      "message": "Error rate exceeded 10%",
      "context": {"error_rate": 0.15}
    }
  ]
}
```

## Prometheus Integration

### Export Metrics

```bash
# Get Prometheus format metrics
curl http://localhost:8000/api/metrics/prometheus
```

### Prometheus Response Format

```
# HELP oracle_uptime_seconds Application uptime in seconds
# TYPE oracle_uptime_seconds gauge
oracle_uptime_seconds 3600.0

# HELP oracle_total_requests Total HTTP requests
# TYPE oracle_total_requests counter
oracle_total_requests 1500

# HELP oracle_request_errors Total request errors
# TYPE oracle_request_errors counter
oracle_request_errors 50

# HELP oracle_avg_response_time_ms Average response time
# TYPE oracle_avg_response_time_ms gauge
oracle_avg_response_time_ms 1250.5

# HELP oracle_messages_processed Total processed messages
# TYPE oracle_messages_processed counter
oracle_messages_processed 1000

# HELP oracle_tokens_used Total tokens used
# TYPE oracle_tokens_used counter
oracle_tokens_used 50000
```

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'oracle'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/metrics/prometheus'
    scrape_interval: 10s
```

### Docker Compose Setup

```yaml
version: '3.8'

services:
  oracle:
    image: oracle:latest
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus
```

## Grafana Dashboard Setup

### Step 1: Add Prometheus Data Source

1. Go to http://localhost:3000
2. Login with `admin:admin`
3. Settings → Data Sources → Add Prometheus
4. URL: `http://prometheus:9090`

### Step 2: Import Dashboard

Create a dashboard with panels:

**Panel 1: Request Rate**
```
sum(rate(oracle_total_requests[1m]))
```

**Panel 2: Error Rate**
```
sum(rate(oracle_request_errors[1m])) / sum(rate(oracle_total_requests[1m]))
```

**Panel 3: Response Time**
```
oracle_avg_response_time_ms
```

**Panel 4: Uptime**
```
oracle_uptime_seconds / 3600  # in hours
```

## Structured Logging

### Logger Usage

```python
from core.monitoring import get_logger

logger = get_logger(__name__)

# Set context
logger.set_context(user_id=123, endpoint="/api/telegram")

# Log with context
logger.info("User message received", message_len=100)
# Output: User message received | {"user_id": 123, "endpoint": "/api/telegram", "message_len": 100}

# Clear context
logger.clear_context()
```

### Log Levels

```python
logger.debug("Debug information")       # Low-level details
logger.info("Information message")      # General info
logger.warning("Warning message")       # Warning conditions
logger.error("Error message")           # Error conditions
logger.critical("Critical error")       # Critical failures
```

### Viewing Logs

```bash
# Get recent logs
curl http://localhost:8000/api/logs?limit=50

# Filter by level
curl http://localhost:8000/api/logs?level=ERROR&limit=20

# Response
{
  "total": 50,
  "logs": [
    {
      "level": "ERROR",
      "component": "telegram_bot",
      "message": "Failed to send message",
      "created_at": "2026-02-02T12:00:00Z"
    }
  ]
}
```

## Performance Monitoring

### Slow Request Detection

Requests slower than 5 seconds are logged as warnings:

```
⚠️ Slow request detected: 5250ms | {"endpoint": "/api/process", "method": "POST"}
```

### Response Time Metrics

```python
# From metrics endpoint
{
  "performance": {
    "average_response_time_ms": 1250.5,
    "total_response_time_ms": 1875000.0
  }
}
```

## Error Tracking

### Error Recording

Errors are automatically tracked:

```python
metrics_collector.record_error(
    error_type="TELEGRAM_API_ERROR",
    message="Failed to send message: timeout",
    context={"chat_id": 123, "retry_count": 3}
)
```

### Error Analytics

```bash
# Get error statistics
curl http://localhost:8000/api/metrics | jq '.errors'

# Response
{
  "total_errors": 50,
  "error_rate": 0.0333,
  "recent_errors": [
    {
      "timestamp": "2026-02-02T12:00:00Z",
      "type": "TELEGRAM_API_ERROR",
      "message": "Failed to send message",
      "context": {"chat_id": 123}
    }
  ]
}
```

## Alerting Integration

### Email Alerts (Setup Required)

```python
# core/monitoring.py (extend AlertManager)
from smtplib import SMTP
from email.mime.text import MIMEText

class EmailAlertHandler:
    def __init__(self, smtp_host, smtp_port, from_email, password):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.from_email = from_email
        self.password = password
    
    def send_alert(self, alert):
        msg = MIMEText(f"Alert: {alert['title']}\n{alert['message']}")
        msg['Subject'] = f"ORACLE Alert: {alert['title']}"
        msg['From'] = self.from_email
        msg['To'] = "admin@example.com"
        
        with SMTP(self.smtp_host, self.smtp_port) as smtp:
            smtp.starttls()
            smtp.login(self.from_email, self.password)
            smtp.send_message(msg)
```

### Slack Alerts (Setup Required)

```python
import httpx

async def send_slack_alert(alert):
    webhook_url = settings.SLACK_WEBHOOK_URL
    
    payload = {
        "text": f"🚨 {alert['title']}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{alert['level'].upper()}*: {alert['title']}\n{alert['message']}"
                }
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=payload)
```

## Best Practices

### 1. Regular Monitoring
- ✅ Check metrics dashboard daily
- ✅ Review error logs
- ✅ Monitor alerts
- ✅ Track trends

### 2. Threshold Tuning
```python
# Adjust thresholds based on your baseline
alert_manager.thresholds = {
    'error_rate': 0.05,        # Stricter: 5%
    'response_time_ms': 3000,  # Faster: 3 seconds
    'health_check_failures': 1  # More sensitive
}
```

### 3. Retention Policies
```python
# Default: 24 hours
metrics_collector = MetricsCollector(retention_hours=72)

# Cleanup old data
@app.on_event("startup")
async def cleanup():
    metrics_collector.cleanup_old_records()
```

### 4. Custom Metrics
```python
# Add custom metrics for your business logic
metrics_collector.record_custom({
    'active_users': get_active_user_count(),
    'pending_messages': get_pending_message_count(),
    'cache_hit_rate': calculate_cache_hits()
})
```

## Troubleshooting

### Health Check Failing

**Problem**: Health check returns "unhealthy"

**Solution**:
1. Check component logs: `curl http://localhost:8000/api/logs?level=ERROR`
2. Verify component connectivity (database, Redis, etc.)
3. Check network connectivity
4. Review error details from alert system

### High Error Rate

**Problem**: Error rate exceeded threshold

**Solution**:
1. Check recent error logs
2. Identify error types and patterns
3. Check for upstream service issues
4. Review rate limiting statistics
5. Check database query performance

### Slow Response Times

**Problem**: Average response time high

**Solution**:
1. Review slow request logs
2. Check database query performance
3. Monitor external API latency
4. Check for resource exhaustion
5. Profile critical endpoints

## Conclusion

ORACLE's monitoring system provides:
- ✅ Real-time metrics
- ✅ Health monitoring
- ✅ Alert system
- ✅ Performance tracking
- ✅ Error analysis
- ✅ Prometheus integration

---

**Last Updated**: 2026-02-02
**Review Schedule**: Monthly
