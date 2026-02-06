# ORACLE Monitoring & Observability Setup Guide

## Overview

Complete setup guide for monitoring, logging, alerting, and dashboarding the ORACLE system.

---

## 1. Logging Infrastructure

### 1.1 Local Logging Setup

**Enable Structured Logging**:

```python
# main.py
from core.logging_config import initialize_logging

logger = initialize_logging()
logger.info("ORACLE system started", extra={
    "extra_fields": {
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT
    }
})
```

**Log Files Location**:
- `logs/oracle.log` - All messages (rotated, 10MB per file)
- `logs/oracle_errors.log` - Errors only
- `logs/oracle_json.log` - JSON format (production)

**Log Configuration**:
```bash
# In .env
LOG_LEVEL=INFO
ENVIRONMENT=production
DEBUG=false
```

### 1.2 Log Aggregation (ELK Stack)

**Install Elasticsearch Stack**:

```bash
# Docker Compose setup
docker-compose -f docker-compose.monitoring.yml up -d
```

**docker-compose.monitoring.yml**:
```yaml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.0.0
    user: root
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - ./logs:/var/log/oracle:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command: filebeat -e -strict.perms=false

volumes:
  elasticsearch_data:
    driver: local
```

**filebeat.yml**:
```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/oracle/oracle_json.log
  json.message_key: message
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]

logging.level: info
```

**Start Monitoring**:
```bash
# Check logs in Kibana
# Navigate to http://localhost:5601
# Index Pattern: filebeat-* (auto-created)
```

### 1.3 Log Filtering & Alerts

**Create Kibana Alert for Errors**:

```python
# Using Python to query logs
from elasticsearch import Elasticsearch

es = Elasticsearch(['http://localhost:9200'])

# Search for errors in last hour
response = es.search(index="filebeat-*", body={
    "query": {
        "bool": {
            "must": [
                {"match": {"level": "ERROR"}},
                {"range": {"@timestamp": {"gte": "now-1h"}}}
            ]
        }
    },
    "aggs": {
        "error_types": {
            "terms": {"field": "error_code.keyword"}
        }
    }
})

print(f"Errors in last hour: {response['hits']['total']}")
for bucket in response['aggregations']['error_types']['buckets']:
    print(f"  {bucket['key']}: {bucket['doc_count']}")
```

---

## 2. Metrics Collection

### 2.1 Built-in Metrics

**Collect Metrics in Handlers**:

```python
from core.logging_config import metrics_collector
import time

@app.post("/message")
async def handle_message(msg: MessageRequest, user_id: int):
    start = time.time()
    
    try:
        # Process message
        result = await process(msg)
        duration = (time.time() - start) * 1000
        
        # Record metrics
        metrics_collector.record_message()
        metrics_collector.record_response_time(duration)
        
        return {"success": True, "result": result}
    except Exception as e:
        metrics_collector.record_error(type(e).__name__)
        raise
```

**Expose Metrics Endpoint**:

```python
from fastapi import APIRouter
from core.schemas import MetricsResponse
from core.logging_config import metrics_collector

router = APIRouter()

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system metrics"""
    return MetricsResponse(**metrics_collector.get_summary())
```

**Access Metrics**:
```bash
curl http://localhost:8000/metrics
# Returns:
# {
#   "total_messages": 1500,
#   "total_users": 250,
#   "average_response_time_ms": 425.3,
#   "error_rate": 0.0023,
#   "tokens_used": 875000,
#   "cost_usd": 12.45,
#   "uptime_seconds": 86400
# }
```

### 2.2 Prometheus Integration

**Setup Prometheus**:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'oracle'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

**Export Metrics in Prometheus Format**:

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
message_counter = Counter('oracle_messages_total', 'Total messages processed')
error_counter = Counter('oracle_errors_total', 'Total errors', ['error_type'])
response_time = Histogram('oracle_response_time_ms', 'Response time in ms')
active_users = Gauge('oracle_active_users', 'Active users')

# Use in handlers
@app.post("/message")
async def handle_message(msg):
    start = time.time()
    
    try:
        result = await process(msg)
        message_counter.inc()
        response_time.observe((time.time() - start) * 1000)
        return result
    except Exception as e:
        error_counter.labels(error_type=type(e).__name__).inc()
        raise

# Expose /metrics endpoint
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

---

## 3. Health Checks

### 3.1 Health Check Endpoint

**Implement Health Check**:

```python
from core.logging_config import health_checker, metrics_collector
from core.schemas import HealthCheckResponse
from core.database import SessionLocal
import redis

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check system health status"""
    
    # Check database
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_checker.set_component_status("database", "healthy")
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        health_checker.set_component_status("database", "unhealthy")
    
    # Check Redis
    try:
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        health_checker.set_component_status("redis", "healthy")
    except Exception as e:
        logger.error(f"Redis check failed: {e}")
        health_checker.set_component_status("redis", "unhealthy")
    
    # Check AI Engine
    try:
        # Try a lightweight API call
        from core.ai_engine import ai_engine
        ai_engine.classify_message("test")
        health_checker.set_component_status("ai_engine", "healthy")
    except Exception as e:
        logger.error(f"AI check failed: {e}")
        health_checker.set_component_status("ai_engine", "degraded")
    
    report = health_checker.get_report()
    return HealthCheckResponse(
        status=report["status"],
        components=report["components"],
        uptime_seconds=metrics_collector.get_uptime_seconds(),
        version="2.0.0"
    )

# Monitoring service calls health check
# curl http://localhost:8000/health
# {
#   "status": "healthy",
#   "components": {
#     "database": "healthy",
#     "redis": "healthy",
#     "ai_engine": "healthy",
#     "telegram": "healthy",
#     "api": "healthy"
#   },
#   "uptime_seconds": 123456,
#   "version": "2.0.0"
# }
```

### 3.2 Kubernetes Probes

**For Kubernetes Deployments**:

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oracle
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: oracle
        image: oracle:2.0.0
        ports:
        - containerPort: 8000
        
        # Startup probe
        startupProbe:
          httpGet:
            path: /health
            port: 8000
          failureThreshold: 30
          periodSeconds: 10
        
        # Liveness probe
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        
        # Readiness probe
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

---

## 4. Alerting

### 4.1 Setup Alert System

**Configure Alert Handlers**:

```python
from core.logging_config import alert_system
import aiohttp

# Telegram alerts
async def telegram_alert_handler(alert):
    if alert['level_code'] >= 2:  # ERROR or higher
        message = (
            f"🚨 **{alert['level']}**\\n"
            f"{alert['message']}\\n"
            f"Time: {alert['timestamp']}"
        )
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"https://api.telegram.org/bot{ADMIN_TOKEN}/sendMessage",
                json={
                    "chat_id": ADMIN_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML"
                }
            )

# Email alerts
async def email_alert_handler(alert):
    if alert['level'] == 'CRITICAL':
        send_email(
            to=ADMIN_EMAIL,
            subject=f"ORACLE Critical: {alert['message']}",
            body=json.dumps(alert, indent=2)
        )

# Register handlers
alert_system.register_handler(telegram_alert_handler)
alert_system.register_handler(email_alert_handler)
```

**Trigger Alerts**:

```python
from core.logging_config import alert_system

# In error handlers
except AIError as e:
    if "timeout" in str(e).lower():
        alert_system.trigger_alert(
            message=f"AI processing timeout: {e.message}",
            level="ERROR",
            details={"user_id": user_id, "duration": timeout_seconds}
        )
    raise
```

### 4.2 Alert Thresholds

**Define Alert Triggers**:

```python
# Error rate alert
def check_error_rate():
    error_rate = metrics_collector.get_error_rate()
    if error_rate > 0.05:  # 5% error rate
        alert_system.trigger_alert(
            message=f"High error rate detected: {error_rate:.2%}",
            level="WARNING",
            details={"error_rate": error_rate}
        )

# Slow response time alert
def check_response_time():
    avg_time = metrics_collector.get_average_response_time()
    if avg_time > 2000:  # 2 seconds
        alert_system.trigger_alert(
            message=f"Slow response times: {avg_time:.0f}ms average",
            level="WARNING",
            details={"average_response_time_ms": avg_time}
        )

# Database connection alert
def check_database():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception as e:
        alert_system.trigger_alert(
            message="Database connection failed",
            level="CRITICAL",
            details={"error": str(e)}
        )

# Run checks periodically
import asyncio
async def monitor():
    while True:
        check_error_rate()
        check_response_time()
        check_database()
        await asyncio.sleep(60)  # Check every 60 seconds
```

---

## 5. Dashboarding

### 5.1 Grafana Dashboard

**Setup Grafana**:

```bash
docker run -d \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana:latest
```

**Create Dashboard JSON**:

```json
{
  "dashboard": {
    "title": "ORACLE System Monitoring",
    "panels": [
      {
        "title": "Messages Processed",
        "targets": [
          {
            "expr": "oracle_messages_total"
          }
        ]
      },
      {
        "title": "Average Response Time",
        "targets": [
          {
            "expr": "avg(oracle_response_time_ms)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(oracle_errors_total[5m])"
          }
        ]
      },
      {
        "title": "Active Users",
        "targets": [
          {
            "expr": "oracle_active_users"
          }
        ]
      },
      {
        "title": "System Status",
        "targets": [
          {
            "expr": "up{job='oracle'}"
          }
        ]
      }
    ]
  }
}
```

### 5.2 Custom Dashboard (FastAPI)

**Create Web Dashboard**:

```python
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from core.logging_config import metrics_collector, health_checker

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """System monitoring dashboard"""
    metrics = metrics_collector.get_summary()
    health = health_checker.get_report()
    
    html = f"""
    <html>
    <head>
        <title>ORACLE Dashboard</title>
        <style>
            body {{ font-family: Arial; margin: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .metric {{ 
                display: inline-block; 
                width: 23%; 
                margin: 1%;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }}
            .metric h3 {{ margin: 0 0 10px 0; }}
            .metric .value {{ font-size: 24px; font-weight: bold; }}
            .status-healthy {{ color: green; }}
            .status-degraded {{ color: orange; }}
            .status-unhealthy {{ color: red; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ORACLE System Dashboard</h1>
            <p>Last Updated: {metrics['uptime_seconds']}s uptime</p>
            
            <div class="metric">
                <h3>Messages</h3>
                <div class="value">{metrics['total_messages']}</div>
            </div>
            
            <div class="metric">
                <h3>Users</h3>
                <div class="value">{metrics['total_users']}</div>
            </div>
            
            <div class="metric">
                <h3>AI Tasks</h3>
                <div class="value">{metrics['total_ai_tasks']}</div>
            </div>
            
            <div class="metric">
                <h3>Success Rate</h3>
                <div class="value">{(1-metrics['error_rate'])*100:.1f}%</div>
            </div>
            
            <div class="metric">
                <h3>Avg Response Time</h3>
                <div class="value">{metrics['average_response_time_ms']:.0f}ms</div>
            </div>
            
            <div class="metric">
                <h3>Tokens Used</h3>
                <div class="value">{metrics['tokens_used']:,}</div>
            </div>
            
            <div class="metric">
                <h3>Cost (USD)</h3>
                <div class="value">${metrics['cost_usd']:.2f}</div>
            </div>
            
            <div class="metric">
                <h3>System Status</h3>
                <div class="value status-{health['status']}">{health['status'].upper()}</div>
            </div>
            
            <h2>Component Status</h2>
            <table border="1" cellpadding="10">
                <tr>
                    <th>Component</th>
                    <th>Status</th>
                </tr>
    """
    
    for component, status in health['components'].items():
        status_class = f"status-{status}"
        html += f"""
                <tr>
                    <td>{component}</td>
                    <td><span class="{status_class}">{status.upper()}</span></td>
                </tr>
        """
    
    html += """
            </table>
        </div>
    </body>
    </html>
    """
    return html
```

---

## 6. Best Practices

### 6.1 Log Retention

```python
# Automatic log rotation
# logs/oracle.log: 10MB per file, 10 backups = 100MB total
# logs/oracle_errors.log: 10MB per file, 10 backups = 100MB total

# Retention policy (in .env)
LOG_RETENTION_DAYS=30  # Delete logs older than 30 days
```

### 6.2 Metric Retention

```python
# Clear metrics periodically
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=0, minute=0)
async def reset_daily_metrics():
    """Reset daily metrics at midnight"""
    metrics_collector.metrics['daily_errors'] = 0
    metrics_collector.metrics['daily_tasks'] = 0
```

### 6.3 Alert Routing

```python
# Route alerts based on severity
def route_alert(alert):
    if alert['level'] == 'CRITICAL':
        # Immediate notification to on-call team
        notify_pagerduty(alert)
    elif alert['level'] == 'ERROR':
        # Slack notification
        notify_slack(alert)
    elif alert['level'] == 'WARNING':
        # Log only
        logger.warning(alert['message'])
```

---

## 7. Troubleshooting

### Common Issues

**Problem**: Logs not appearing in Kibana
```bash
# Check Filebeat status
docker logs filebeat

# Verify Elasticsearch is running
curl http://localhost:9200

# Check index exists
curl http://localhost:9200/_cat/indices
```

**Problem**: High error rate alerts
```python
# Check recent errors
from elasticsearch import Elasticsearch
es = Elasticsearch(['http://localhost:9200'])

errors = es.search(index="filebeat-*", body={
    "query": {"match": {"level": "ERROR"}},
    "size": 100,
    "sort": [{"@timestamp": {"order": "desc"}}]
})

for hit in errors['hits']['hits']:
    print(hit['_source'])
```

**Problem**: Health check failing
```bash
# Test each component manually
curl http://localhost:8000/health

# Check database
psql postgresql://user:pass@localhost/oracle -c "SELECT 1"

# Check Redis
redis-cli ping

# Check Telegram
curl https://api.telegram.org/botTOKEN/getMe
```

---

## 8. Production Deployment

### Pre-Deployment Checklist

- [ ] Elasticsearch cluster configured
- [ ] Kibana dashboards created
- [ ] Prometheus scrape config updated
- [ ] Grafana dashboards imported
- [ ] Alert handlers configured
- [ ] Health check endpoint tested
- [ ] Metrics endpoint tested
- [ ] Log files rotated successfully
- [ ] Dashboard accessible and showing data
- [ ] Alert thresholds configured

### Deployment Command

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services
docker-compose -f docker-compose.monitoring.yml ps

# Check logs
docker-compose -f docker-compose.monitoring.yml logs -f
```

---

## Support

For monitoring issues, check:
1. Service logs: `docker-compose logs SERVICE_NAME`
2. Component health: `curl http://localhost:8000/health`
3. Metrics: `curl http://localhost:8000/metrics`
4. Dashboard: `http://localhost:3000/` (Grafana) or `http://localhost:5601/` (Kibana)

