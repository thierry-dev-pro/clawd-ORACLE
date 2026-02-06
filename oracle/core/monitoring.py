"""
Monitoring, metrics, and structured logging
- Structured logging with context
- Performance metrics collection
- Health status tracking
- Alert generation
"""
import logging
import time
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, asdict
from functools import wraps
from core.config import settings

# ==================== Structured Logger ====================

class StructuredLogger:
    """Logger with structured context support"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context = {}
    
    def _format_message(self, msg: str, context: Dict[str, Any] = None) -> str:
        """Format message with context"""
        try:
            ctx = {**self.context, **(context or {})}
            if ctx:
                return f"{msg} | {json.dumps(ctx)}"
            return msg
        except Exception:
            return msg
    
    def set_context(self, **kwargs):
        """Set context variables"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear context"""
        self.context = {}
    
    def debug(self, msg: str, **kwargs):
        self.logger.debug(self._format_message(msg, kwargs))
    
    def info(self, msg: str, **kwargs):
        self.logger.info(self._format_message(msg, kwargs))
    
    def warning(self, msg: str, **kwargs):
        self.logger.warning(self._format_message(msg, kwargs))
    
    def error(self, msg: str, **kwargs):
        self.logger.error(self._format_message(msg, kwargs))
    
    def critical(self, msg: str, **kwargs):
        self.logger.critical(self._format_message(msg, kwargs))

def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger"""
    return StructuredLogger(name)

# ==================== Metrics Collection ====================

@dataclass
class RequestMetrics:
    """Metrics for a single request"""
    timestamp: datetime
    endpoint: str
    method: str
    status_code: int
    duration_ms: float
    user_id: Optional[int] = None
    error: Optional[str] = None

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time_ms: float
    error: Optional[str] = None
    last_checked: datetime = None
    
    def __post_init__(self):
        if self.last_checked is None:
            self.last_checked = datetime.utcnow()

class MetricsCollector:
    """Collect and aggregate application metrics"""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.requests: List[RequestMetrics] = []
        self.errors: List[Dict[str, Any]] = []
        self.component_health: Dict[str, HealthCheckResult] = {}
        self._start_time = datetime.utcnow()
        
        # Counters
        self.message_count = 0
        self.token_count = 0
        self.error_count = 0
        
        # Time tracking
        self.total_response_time = 0.0
    
    def record_request(self, metrics: RequestMetrics):
        """Record a request metric"""
        try:
            self.requests.append(metrics)
            self.total_response_time += metrics.duration_ms
            
            if metrics.status_code >= 400:
                self.error_count += 1
            
            # Cleanup old records
            cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)
            self.requests = [r for r in self.requests if r.timestamp > cutoff]
        
        except Exception as e:
            logger.error(f"Error recording request metric: {e}")
    
    def record_error(self, error_type: str, message: str, context: Dict[str, Any] = None):
        """Record an error"""
        try:
            self.errors.append({
                'timestamp': datetime.utcnow(),
                'type': error_type,
                'message': message,
                'context': context or {}
            })
            self.error_count += 1
            
            # Cleanup old errors
            cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)
            self.errors = [e for e in self.errors if e['timestamp'] > cutoff]
        
        except Exception as e:
            logger.error(f"Error recording error metric: {e}")
    
    def record_message(self, tokens_used: int):
        """Record a processed message"""
        self.message_count += 1
        self.token_count += tokens_used
    
    def record_component_health(self, component: str, status: str, response_time_ms: float, error: str = None):
        """Record component health status"""
        try:
            self.component_health[component] = HealthCheckResult(
                component=component,
                status=status,
                response_time_ms=response_time_ms,
                error=error,
                last_checked=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error recording component health: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all current metrics"""
        try:
            uptime_seconds = (datetime.utcnow() - self._start_time).total_seconds()
            
            avg_response_time = 0
            if self.requests:
                avg_response_time = self.total_response_time / len(self.requests)
            
            error_rate = 0
            if self.requests:
                errors = sum(1 for r in self.requests if r.status_code >= 400)
                error_rate = errors / len(self.requests)
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'uptime_seconds': uptime_seconds,
                'requests': {
                    'total': len(self.requests),
                    'success': len([r for r in self.requests if r.status_code < 400]),
                    'error': len([r for r in self.requests if r.status_code >= 400]),
                },
                'messages': {
                    'total_processed': self.message_count,
                    'total_tokens': self.token_count,
                    'average_tokens_per_message': (
                        self.token_count / self.message_count
                        if self.message_count > 0 else 0
                    )
                },
                'performance': {
                    'average_response_time_ms': round(avg_response_time, 2),
                    'total_response_time_ms': round(self.total_response_time, 2),
                },
                'errors': {
                    'total_errors': self.error_count,
                    'error_rate': round(error_rate, 4),
                    'recent_errors': self.errors[-10:]  # Last 10
                },
                'components': {
                    component: asdict(health)
                    for component, health in self.component_health.items()
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
    
    def get_requests_by_endpoint(self) -> Dict[str, int]:
        """Get request count by endpoint"""
        counts = defaultdict(int)
        for req in self.requests:
            counts[req.endpoint] += 1
        return dict(counts)
    
    def get_requests_by_status(self) -> Dict[int, int]:
        """Get request count by status code"""
        counts = defaultdict(int)
        for req in self.requests:
            counts[req.status_code] += 1
        return dict(counts)
    
    def reset(self):
        """Reset all metrics (careful!)"""
        self.requests = []
        self.errors = []
        self.message_count = 0
        self.token_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self._start_time = datetime.utcnow()

# Global metrics collector
metrics_collector = MetricsCollector()

# ==================== Health Checks ====================

class HealthChecker:
    """Perform application health checks"""
    
    def __init__(self):
        self.checks: Dict[str, callable] = {}
        self.logger = get_logger(__name__)
    
    def register_check(self, name: str, check_func: callable):
        """Register a health check function"""
        self.checks[name] = check_func
    
    async def run_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        try:
            results = {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': 'healthy',
                'checks': {}
            }
            
            for name, check_func in self.checks.items():
                try:
                    start = time.time()
                    status, message = await check_func()
                    duration_ms = (time.time() - start) * 1000
                    
                    results['checks'][name] = {
                        'status': status,
                        'message': message,
                        'response_time_ms': round(duration_ms, 2)
                    }
                    
                    # Record to metrics
                    metrics_collector.record_component_health(
                        name, status, duration_ms, message if status != 'healthy' else None
                    )
                    
                    if status != 'healthy':
                        results['overall_status'] = 'degraded'
                
                except Exception as e:
                    error_msg = str(e)
                    results['checks'][name] = {
                        'status': 'unhealthy',
                        'message': error_msg,
                        'response_time_ms': 0
                    }
                    results['overall_status'] = 'degraded'
                    
                    metrics_collector.record_component_health(name, 'unhealthy', 0, error_msg)
            
            return results
        
        except Exception as e:
            self.logger.error(f"Error running health checks: {e}")
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': 'unhealthy',
                'error': str(e)
            }

# Global health checker
health_checker = HealthChecker()

# ==================== Alerting ====================

class AlertManager:
    """Manage alerts for critical conditions"""
    
    def __init__(self):
        self.alerts: List[Dict[str, Any]] = []
        self.logger = get_logger(__name__)
        self.thresholds = {
            'error_rate': 0.1,  # 10%
            'response_time_ms': 5000,  # 5 seconds
            'health_check_failures': 2  # consecutive failures
        }
    
    def check_thresholds(self, metrics: Dict[str, Any]) -> List[str]:
        """Check metrics against thresholds and return alerts"""
        alerts = []
        
        try:
            # Check error rate
            if metrics.get('error_rate', 0) > self.thresholds['error_rate']:
                alert = f"⚠️ ERROR RATE HIGH: {metrics['error_rate']:.1%}"
                alerts.append(alert)
                self.logger.warning(alert)
            
            # Check response time
            avg_time = metrics.get('average_response_time_ms', 0)
            if avg_time > self.thresholds['response_time_ms']:
                alert = f"⚠️ RESPONSE TIME HIGH: {avg_time:.0f}ms"
                alerts.append(alert)
                self.logger.warning(alert)
            
            return alerts
        
        except Exception as e:
            self.logger.error(f"Error checking thresholds: {e}")
            return []
    
    def add_alert(self, level: str, title: str, message: str, context: Dict = None):
        """Add an alert"""
        try:
            alert = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': level,
                'title': title,
                'message': message,
                'context': context or {}
            }
            self.alerts.append(alert)
            
            # Log alert
            if level == 'critical':
                self.logger.critical(f"🚨 {title}: {message}")
            elif level == 'warning':
                self.logger.warning(f"⚠️ {title}: {message}")
            else:
                self.logger.info(f"ℹ️ {title}: {message}")
        
        except Exception as e:
            self.logger.error(f"Error adding alert: {e}")
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return self.alerts[-limit:]
    
    def clear_old_alerts(self, hours: int = 24):
        """Clear alerts older than specified hours"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        self.alerts = [
            a for a in self.alerts
            if datetime.fromisoformat(a['timestamp']) > cutoff
        ]

# Global alert manager
alert_manager = AlertManager()

# ==================== Performance Tracking ====================

def track_performance(endpoint: str):
    """Decorator to track endpoint performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            status_code = 200
            error = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                error = str(e)
                raise
            finally:
                duration_ms = (time.time() - start) * 1000
                
                # Extract user_id if available
                user_id = kwargs.get('user_id')
                
                metrics = RequestMetrics(
                    timestamp=datetime.utcnow(),
                    endpoint=endpoint,
                    method='POST',
                    status_code=status_code,
                    duration_ms=duration_ms,
                    user_id=user_id,
                    error=error
                )
                metrics_collector.record_request(metrics)
        
        return async_wrapper
    return decorator

# ==================== Initialize Logging ====================

def setup_logging(log_level: str = "INFO"):
    """Setup structured logging for the application"""
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler with structured format
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

# Create logger for this module
logger = get_logger(__name__)

# ==================== Log Export ====================

class LogExporter:
    """Export logs for analysis"""
    
    @staticmethod
    def export_metrics_json(metrics: Dict[str, Any]) -> str:
        """Export metrics as JSON"""
        return json.dumps(metrics, indent=2, default=str)
    
    @staticmethod
    def export_prometheus_format(metrics: Dict[str, Any]) -> str:
        """Export metrics in Prometheus format"""
        lines = [
            '# HELP oracle_uptime_seconds Application uptime in seconds',
            '# TYPE oracle_uptime_seconds gauge',
            f'oracle_uptime_seconds {metrics.get("uptime_seconds", 0)}',
            '',
            '# HELP oracle_total_requests Total HTTP requests',
            '# TYPE oracle_total_requests counter',
            f'oracle_total_requests {metrics.get("requests", {}).get("total", 0)}',
            '',
            '# HELP oracle_request_errors Total request errors',
            '# TYPE oracle_request_errors counter',
            f'oracle_request_errors {metrics.get("requests", {}).get("error", 0)}',
            '',
            '# HELP oracle_avg_response_time_ms Average response time',
            '# TYPE oracle_avg_response_time_ms gauge',
            f'oracle_avg_response_time_ms {metrics.get("performance", {}).get("average_response_time_ms", 0)}',
            '',
            '# HELP oracle_messages_processed Total processed messages',
            '# TYPE oracle_messages_processed counter',
            f'oracle_messages_processed {metrics.get("messages", {}).get("total_processed", 0)}',
            '',
            '# HELP oracle_tokens_used Total tokens used',
            '# TYPE oracle_tokens_used counter',
            f'oracle_tokens_used {metrics.get("messages", {}).get("total_tokens", 0)}',
        ]
        return '\n'.join(lines)
