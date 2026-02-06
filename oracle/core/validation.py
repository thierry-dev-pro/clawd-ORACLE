"""
Pydantic models for input validation
Ensures type safety and validation across the entire application
"""
from pydantic import BaseModel, Field, validator, EmailStr, constr
from typing import Optional, Dict, Any, List
from datetime import datetime
import re

# ==================== Telegram Message Validation ====================

class TelegramUser(BaseModel):
    """Telegram user data validation"""
    id: int = Field(..., gt=0, description="Telegram user ID")
    is_bot: bool = False
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    username: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9_]{5,32}$', description="Valid Telegram username")
    language_code: Optional[str] = Field(None, pattern=r'^[a-z]{2}(?:-[A-Z]{2})?$')
    is_premium: Optional[bool] = False
    
    @validator('first_name')
    def validate_first_name(cls, v):
        if not re.match(r'^[\w\s\-\']+$', v):
            raise ValueError('first_name contains invalid characters')
        return v.strip()
    
    class Config:
        use_enum_values = True

class TelegramChat(BaseModel):
    """Telegram chat data validation"""
    id: int = Field(..., description="Chat ID")
    type: str = Field(..., regex='^(private|group|supergroup|channel)$')
    title: Optional[str] = Field(None, max_length=255)
    username: Optional[str] = None
    first_name: Optional[str] = None
    
    class Config:
        use_enum_values = True

class TelegramMessage(BaseModel):
    """Telegram message data validation"""
    message_id: int = Field(..., gt=0)
    date: int = Field(..., gt=0, description="Unix timestamp")
    chat: TelegramChat
    from_user: Optional[TelegramUser] = Field(None, alias='from')
    text: Optional[str] = Field(None, max_length=4096)
    reply_to_message: Optional[Dict] = None
    edit_date: Optional[int] = None
    
    @validator('text')
    def validate_text(cls, v):
        if v is None:
            return v
        # Check for injection attempts
        dangerous_patterns = ['<script', '<?php', 'javascript:', 'onerror=', 'onclick=']
        text_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in text_lower:
                raise ValueError(f'Dangerous pattern detected: {pattern}')
        return v
    
    class Config:
        use_enum_values = True
        allow_population_by_field_name = True

class TelegramUpdate(BaseModel):
    """Telegram webhook update validation"""
    update_id: int = Field(..., gt=0)
    message: Optional[TelegramMessage] = None
    edited_message: Optional[TelegramMessage] = None
    channel_post: Optional[TelegramMessage] = None
    edited_channel_post: Optional[TelegramMessage] = None
    
    class Config:
        use_enum_values = True

# ==================== API Request/Response Models ====================

class ProcessMessageRequest(BaseModel):
    """Request to process messages"""
    limit: int = Field(default=10, ge=1, le=100)
    user_id: Optional[int] = Field(None, gt=0)
    
    class Config:
        schema_extra = {
            "example": {
                "limit": 10,
                "user_id": None
            }
        }

class MessageResponse(BaseModel):
    """Message response model"""
    id: int
    user_id: int
    content: str = Field(..., max_length=4096)
    message_type: str
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    """User response model"""
    id: int
    telegram_id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class LogResponse(BaseModel):
    """System log response model"""
    id: int
    level: str = Field(..., regex='^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$')
    component: str
    message: str
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., regex='^(healthy|degraded|unhealthy)$')
    timestamp: datetime
    components: Dict[str, str]
    version: str
    uptime_seconds: Optional[float] = None

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    code: str = Field(..., regex='^[A-Z_]+$')
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "error": "Invalid input",
                "code": "VALIDATION_ERROR",
                "details": {"field": "text"},
                "timestamp": "2026-02-02T12:00:00Z"
            }
        }

class MetricsResponse(BaseModel):
    """Application metrics"""
    timestamp: datetime
    total_messages: int
    user_messages: int
    ai_responses: int
    total_tokens_used: int
    average_response_time_ms: float
    error_rate: float = Field(..., ge=0, le=1)
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2026-02-02T12:00:00Z",
                "total_messages": 1000,
                "user_messages": 600,
                "ai_responses": 400,
                "total_tokens_used": 50000,
                "average_response_time_ms": 1250.5,
                "error_rate": 0.02
            }
        }

# ==================== Database Models (Input/Output) ====================

class AutoResponsePattern(BaseModel):
    """Auto-response pattern validation"""
    trigger: str = Field(..., min_length=1, max_length=255, description="Pattern to trigger on")
    response: str = Field(..., min_length=1, max_length=4096)
    enabled: bool = True
    match_type: str = Field(default="contains", regex='^(exact|contains|regex)$')
    
    @validator('trigger')
    def validate_trigger(cls, v):
        if not re.match(r'^[\w\s\-\'\.]+$', v):
            raise ValueError('trigger contains invalid characters')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "trigger": "hello",
                "response": "Hi there!",
                "enabled": True,
                "match_type": "contains"
            }
        }

class AdminAuthRequest(BaseModel):
    """Admin authentication request"""
    password: constr(min_length=8, max_length=255) = Field(...)  # type: ignore
    
    class Config:
        schema_extra = {
            "example": {
                "password": "secure_password_123"
            }
        }

class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""
    requests_per_minute: int = Field(default=60, ge=1)
    requests_per_hour: int = Field(default=1000, ge=1)
    burst_size: int = Field(default=10, ge=1)
    
    class Config:
        schema_extra = {
            "example": {
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "burst_size": 10
            }
        }

# ==================== Utility Validators ====================

class SanitizedString(str):
    """String that has been sanitized for XSS/injection"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        return cls(v)

def sanitize_html(text: str) -> str:
    """Remove potentially dangerous HTML/script content"""
    dangerous_patterns = {
        r'<script[^>]*>.*?</script>': '',
        r'<iframe[^>]*>.*?</iframe>': '',
        r'javascript:': '',
        r'on\w+\s*=': '',
        r'<embed': '',
        r'<object': '',
    }
    
    result = text
    for pattern, replacement in dangerous_patterns.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE | re.DOTALL)
    
    return result

def validate_telegram_token(token: str) -> bool:
    """Validate Telegram bot token format"""
    # Format: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
    pattern = r'^\d{6,}:[a-zA-Z0-9_-]{35,}$'
    return bool(re.match(pattern, token))
