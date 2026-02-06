"""
Structured logging configuration for ORACLE
JSON logging, metrics collection, and health monitoring
"""
import logging
import logging.handlers
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
import sys

from core.config import settings


# ==================== JSON FORMATTER ====================
class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
            "thread_name": record.threadName
        }
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_obj.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"[{timestamp}] {record.levelname:8} | "
            f"{record.name}:{record.funcName}:{record.lineno} | "
            f"{record.getMessage()}"
        )


# ==================== LOGGING SETUP ====================
def setup_logging(
    log_level: str = None,
    log_dir: str = "logs",
    json_format: bool = True
) -> logging.Logger:
    """
    Configure structured logging for ORACLE
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        json_format: Use JSON format (True) or text (False)
    
    Returns:
        Configured logger
    """
    log_level = log_level or settings.LOG_LEVEL
    
    # Create logger
    logger = logging.getLogger("oracle")
    logger.setLevel(getattr(logging, log_level))
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Choose formatter
    if json_format:
        formatter = JSONFormatter()
        file_name = "oracle_json.log"
    else:
        formatter = TextFormatter()
        file_name = "oracle.log"
    
    # File handler (rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / file_name,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(getattr(logging, log_level))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    if json_format:
        console_handler.setFormatter(formatter)
    else:
        console_handler.setFormatter(TextFormatter())
    logger.addHandler(console_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / "oracle_errors.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger


# ==================== METRICS COLLECTOR ====================
class MetricsCollector:
    """Collect and track system metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            "total_messages": 0,
            "total_users": 0,
            "total_ai_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_errors": 0,
            "response_times": [],
            "tokens_used": 0,
            "cost_usd": 0.0
        }
        self.errors_by_type = {}
    
    def record_message(self) -> None:
        """Record message processing"""
        self.metrics["total_messages"] += 1
    
    def record_user(self) -> None:
        """Record new user"""
        self.metrics["total_users"] += 1
    
    def record_ai_task(self, status: str = "pending") -> None:
        """Record AI task"""
        self.metrics["total_ai_tasks"] += 1
        if status == "completed":
            self.metrics["completed_tasks"] += 1
        elif status == "failed":
            self.metrics["failed_tasks"] += 1
    
    def record_response_time(self, duration_ms: float) -> None:
        """Record response time"""
        self.metrics["response_times"].append(duration_ms)
    
    def record_error(self, error_type: str) -> None:
        """Record error"""
        self.metrics["total_errors"] += 1
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
    
    def record_tokens(self, tokens: int, cost: float) -> None:
        """Record token usage"""
        self.metrics["tokens_used"] += tokens
        self.metrics["cost_usd"] += cost
    
    def get_average_response_time(self) -> float:
        """Get average response time in ms"""
        if not self.metrics["response_times"]:
            return 0.0
        return sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
    
    def get_error_rate(self) -> float:
        """Get error rate (0.0 to 1.0)"""
        total = self.metrics["total_messages"] + self.metrics["total_ai_tasks"]
        if total == 0:
            return 0.0
        return self.metrics["total_errors"] / total
    
    def get_uptime_seconds(self) -> int:
        """Get uptime in seconds"""
        return int(time.time() - self.start_time)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            "total_messages": self.metrics["total_messages"],
            "total_users": self.metrics["total_users"],
            "total_ai_tasks": self.metrics["total_ai_tasks"],
            "completed_tasks": self.metrics["completed_tasks"],
            "failed_tasks": self.metrics["failed_tasks"],
            "total_errors": self.metrics["total_errors"],
            "average_response_time_ms": round(self.get_average_response_time(), 2),
            "error_rate": round(self.get_error_rate(), 4),
            "errors_by_type": self.errors_by_type,
            "tokens_used": self.metrics["tokens_used"],
            "cost_usd": round(self.metrics["cost_usd"], 2),
            "uptime_seconds": self.get_uptime_seconds()
        }


# ==================== HEALTH CHECK ====================
class HealthChecker:
    """System health monitoring"""
    
    def __init__(self):
        self.components = {
            "database": "unknown",
            "redis": "unknown",
            "ai_engine": "unknown",
            "telegram": "unknown",
            "api": "healthy"
        }
        self.last_check = datetime.utcnow()
    
    def set_component_status(self, component: str, status: str) -> None:
        """
        Set component status
        
        Args:
            component: Component name
            status: Status (healthy, degraded, unhealthy)
        """
        if component in self.components:
            self.components[component] = status
            self.last_check = datetime.utcnow()
    
    def get_status(self) -> str:
        """
        Get overall system status
        
        Returns:
            Status: healthy, degraded, unhealthy
        """
        statuses = list(self.components.values())
        
        if "unhealthy" in statuses:
            return "unhealthy"
        elif "degraded" in statuses:
            return "degraded"
        else:
            return "healthy"
    
    def get_report(self) -> Dict[str, Any]:
        """Get health check report"""
        return {
            "status": self.get_status(),
            "components": self.components,
            "last_check": self.last_check.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }


# ==================== ALERT SYSTEM ====================
class AlertSystem:
    """Alert system for critical errors"""
    
    ALERT_LEVELS = {
        "INFO": 0,
        "WARNING": 1,
        "ERROR": 2,
        "CRITICAL": 3
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("oracle.alerts")
        self.alerts = []
        self.alert_handlers = []
    
    def register_handler(self, handler) -> None:
        """Register alert handler"""
        self.alert_handlers.append(handler)
    
    def trigger_alert(
        self,
        message: str,
        level: str = "ERROR",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Trigger an alert
        
        Args:
            message: Alert message
            level: Alert level (INFO, WARNING, ERROR, CRITICAL)
            details: Additional details
        """
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "level": level,
            "details": details or {},
            "level_code": self.ALERT_LEVELS.get(level, 0)
        }
        
        self.alerts.append(alert)
        
        # Log alert
        log_method = getattr(self.logger, level.lower(), self.logger.error)
        log_method(f"ALERT [{level}]: {message}", extra={"alert_details": details})
        
        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")
    
    def get_recent_alerts(self, limit: int = 10, min_level: str = "ERROR") -> list:
        """Get recent alerts"""
        min_code = self.ALERT_LEVELS.get(min_level, 0)
        return [
            a for a in self.alerts[-limit:]
            if a["level_code"] >= min_code
        ]


# ==================== SINGLETON INSTANCES ====================
metrics_collector = MetricsCollector()
health_checker = HealthChecker()
alert_system = AlertSystem()


# ==================== INITIALIZATION ====================
def initialize_logging():
    """Initialize logging system"""
    logger = setup_logging(
        log_level=settings.LOG_LEVEL,
        json_format=(settings.ENVIRONMENT != "development")
    )
    return logger
