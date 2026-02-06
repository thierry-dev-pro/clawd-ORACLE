"""
Custom exceptions for ORACLE application
Provides structured error handling and reporting
"""
from typing import Optional, Dict, Any

class OracleException(Exception):
    """Base exception for ORACLE"""
    
    def __init__(
        self,
        message: str,
        code: str = "ORACLE_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response"""
        return {
            "error": self.message,
            "code": self.code,
            "details": self.details,
            "status_code": self.status_code
        }

# ==================== Validation Exceptions ====================

class ValidationError(OracleException):
    """Input validation failed"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        details = {}
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)[:100]
        
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            status_code=422
        )

class InvalidTelegramUpdate(ValidationError):
    """Invalid Telegram update"""
    
    def __init__(self, message: str = "Invalid Telegram update"):
        super().__init__(
            message=message,
            code="INVALID_TELEGRAM_UPDATE",
            status_code=400
        )

class InvalidRequest(ValidationError):
    """Invalid API request"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="INVALID_REQUEST",
            status_code=400
        )

# ==================== Security Exceptions ====================

class SecurityError(OracleException):
    """Security-related error"""
    
    def __init__(self, message: str, code: str = "SECURITY_ERROR"):
        super().__init__(
            message=message,
            code=code,
            status_code=403
        )

class UnauthorizedError(SecurityError):
    """Authentication failed"""
    
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
        )
        self.status_code = 401

class AuthenticationFailed(UnauthorizedError):
    """Authentication failed"""
    
    def __init__(self, reason: str = "Invalid credentials"):
        super().__init__(f"Authentication failed: {reason}")

class WebhookVerificationFailed(UnauthorizedError):
    """Webhook signature verification failed"""
    
    def __init__(self):
        super().__init__("Webhook signature verification failed")

class RateLimitExceeded(SecurityError):
    """Rate limit exceeded"""
    
    def __init__(self, message: str = "Too many requests", retry_after: int = None):
        details = {}
        if retry_after:
            details['retry_after'] = retry_after
        
        super().__init__(message=message, code="RATE_LIMIT_EXCEEDED")
        self.details = details
        self.status_code = 429

class TokenExpired(UnauthorizedError):
    """Session token expired"""
    
    def __init__(self):
        super().__init__("Session token expired")

# ==================== Processing Exceptions ====================

class ProcessingError(OracleException):
    """Error during message/data processing"""
    
    def __init__(self, message: str, component: str = None):
        details = {}
        if component:
            details['component'] = component
        
        super().__init__(
            message=message,
            code="PROCESSING_ERROR",
            details=details,
            status_code=500
        )

class AIEngineError(ProcessingError):
    """Error from AI engine"""
    
    def __init__(self, message: str, model: str = None):
        details = {}
        if model:
            details['model'] = model
        
        exception = OracleException(
            message=message,
            code="AI_ENGINE_ERROR",
            details=details,
            status_code=500
        )
        exception.message = message
        exception.code = "AI_ENGINE_ERROR"
        exception.details = details
        exception.status_code = 500

class TelegramAPIError(ProcessingError):
    """Error from Telegram API"""
    
    def __init__(self, message: str, error_code: int = None):
        details = {}
        if error_code:
            details['telegram_error_code'] = error_code
        
        super().__init__(
            message=message,
            component="telegram_api"
        )
        self.details = details

class DatabaseError(ProcessingError):
    """Database operation error"""
    
    def __init__(self, message: str, operation: str = None):
        details = {}
        if operation:
            details['operation'] = operation
        
        super().__init__(
            message=message,
            component="database"
        )
        self.details = details

# ==================== Resource Exceptions ====================

class ResourceNotFoundError(OracleException):
    """Resource not found"""
    
    def __init__(self, resource_type: str, resource_id: Any = None):
        details = {
            'resource_type': resource_type
        }
        if resource_id is not None:
            details['resource_id'] = str(resource_id)
        
        super().__init__(
            message=f"{resource_type} not found",
            code="RESOURCE_NOT_FOUND",
            details=details,
            status_code=404
        )

class UserNotFound(ResourceNotFoundError):
    """User not found"""
    
    def __init__(self, user_id: int):
        super().__init__("User", user_id)

class MessageNotFound(ResourceNotFoundError):
    """Message not found"""
    
    def __init__(self, message_id: int):
        super().__init__("Message", message_id)

# ==================== Configuration Exceptions ====================

class ConfigurationError(OracleException):
    """Configuration error"""
    
    def __init__(self, message: str, setting: str = None):
        details = {}
        if setting:
            details['setting'] = setting
        
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details=details,
            status_code=500
        )

class MissingEnvironmentVariable(ConfigurationError):
    """Missing required environment variable"""
    
    def __init__(self, variable_name: str):
        super().__init__(
            message=f"Missing required environment variable: {variable_name}",
            setting=variable_name
        )

# ==================== Dependency Exceptions ====================

class DependencyError(OracleException):
    """External dependency error"""
    
    def __init__(self, dependency: str, message: str = None):
        details = {'dependency': dependency}
        
        super().__init__(
            message=message or f"{dependency} is unavailable",
            code="DEPENDENCY_ERROR",
            details=details,
            status_code=503
        )

class RedisConnectionError(DependencyError):
    """Redis connection error"""
    
    def __init__(self, message: str = "Cannot connect to Redis"):
        super().__init__("Redis", message)

class DatabaseConnectionError(DependencyError):
    """Database connection error"""
    
    def __init__(self, message: str = "Cannot connect to database"):
        super().__init__("Database", message)

# ==================== HTTP Exception Mapping ====================

def exception_to_http_status(exc: OracleException) -> tuple[int, Dict]:
    """Convert OracleException to HTTP response"""
    return exc.status_code, exc.to_dict()
