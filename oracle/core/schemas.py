"""
Pydantic models for input validation and serialization
Comprehensive validation for all API requests and message processing
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, field_validator
from enum import Enum
import re


# ==================== ENUMS ====================
class MessageType(str, Enum):
    """Message classification types"""
    USER_MESSAGE = "user_message"
    BOT_RESPONSE = "bot_response"
    SYSTEM_LOG = "system_log"
    COMMAND = "command"
    AUTO_RESPONSE = "auto_response"
    ERROR = "error"


class CommandType(str, Enum):
    """Available commands"""
    START = "start"
    HELP = "help"
    STATUS = "status"
    ALPHA = "alpha"
    ANALYZE = "analyze"
    REPORT = "report"
    POST = "post"
    THREAD = "thread"
    PAUSE = "pause"
    RESUME = "resume"
    SETTINGS = "settings"
    UNKNOWN = "unknown"


class LogLevel(str, Enum):
    """Log levels for system logs"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TaskStatus(str, Enum):
    """AI task status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ==================== TELEGRAM MESSAGE VALIDATION ====================
class TelegramUserData(BaseModel):
    """Telegram user data from webhook"""
    id: int = Field(..., gt=0, description="User ID")
    is_bot: bool = False
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    username: Optional[str] = Field(None, min_length=1, max_length=255)
    language_code: Optional[str] = Field(None, max_length=10)
    is_premium: Optional[bool] = False
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate Telegram username format"""
        if v is None:
            return v
        if not re.match(r'^[a-zA-Z0-9_]{5,32}$', v):
            raise ValueError('Invalid Telegram username format')
        return v.lower()
    
    @field_validator('language_code')
    @classmethod
    def validate_language_code(cls, v):
        """Validate language code format"""
        if v is None:
            return v
        if not re.match(r'^[a-z]{2}(-[A-Z]{2})?$', v):
            raise ValueError('Invalid language code format')
        return v


class TelegramChatData(BaseModel):
    """Telegram chat data from webhook"""
    id: int = Field(..., description="Chat ID")
    type: str = Field(..., regex='^(private|group|supergroup|channel)$')
    title: Optional[str] = None
    username: Optional[str] = None


class TelegramMessageData(BaseModel):
    """Telegram message data from webhook"""
    message_id: int = Field(..., gt=0)
    date: int = Field(..., gt=0, description="Unix timestamp")
    text: Optional[str] = Field(None, min_length=0, max_length=4096)
    chat: TelegramChatData
    from_user: TelegramUserData = Field(..., alias="from")
    reply_to_message: Optional[Dict] = None
    edit_date: Optional[int] = None
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        """Validate and sanitize message text"""
        if v is None:
            return v
        # Remove extra whitespace
        v = ' '.join(v.split())
        if len(v) == 0:
            raise ValueError('Text cannot be empty')
        return v
    
    class Config:
        populate_by_name = True  # Allow 'from' as alias


class TelegramWebhookUpdate(BaseModel):
    """Complete Telegram webhook update"""
    update_id: int = Field(..., gt=0)
    message: Optional[TelegramMessageData] = None
    edited_message: Optional[TelegramMessageData] = None
    callback_query: Optional[Dict] = None
    
    @field_validator('update_id')
    @classmethod
    def validate_update_id(cls, v):
        """Validate update ID"""
        if v < 0:
            raise ValueError('Update ID must be positive')
        return v


# ==================== COMMAND VALIDATION ====================
class CommandRequest(BaseModel):
    """Validated command request"""
    command: CommandType
    args: List[str] = Field(default_factory=list, max_length=10)
    raw_text: str = Field(..., min_length=1, max_length=4096)
    
    @field_validator('args')
    @classmethod
    def validate_args(cls, v):
        """Validate command arguments"""
        for arg in v:
            if not isinstance(arg, str) or len(arg) == 0:
                raise ValueError('Invalid command argument')
        return v


class AlphaRequest(BaseModel):
    """Alpha discovery logging request"""
    description: str = Field(..., min_length=10, max_length=2000)
    category: Optional[str] = Field(None, regex='^[a-z_]+$')
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list, max_length=10)
    
    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v):
        """Sanitize alpha description"""
        # Remove potential SQL injection patterns
        dangerous_patterns = [';', '--', '/*', '*/', 'DROP', 'DELETE', 'INSERT']
        for pattern in dangerous_patterns:
            if pattern.lower() in v.lower():
                raise ValueError(f'Invalid content: {pattern}')
        return v.strip()


class AnalysisRequest(BaseModel):
    """AI analysis request"""
    topic: str = Field(..., min_length=5, max_length=1000)
    context: Optional[str] = Field(None, max_length=2000)
    language: Optional[str] = Field("en", regex='^[a-z]{2}$')
    max_tokens: Optional[int] = Field(None, ge=100, le=4000)


class MessageRequest(BaseModel):
    """Regular message request"""
    content: str = Field(..., min_length=1, max_length=4096)
    message_type: MessageType = MessageType.USER_MESSAGE
    conversation_id: Optional[int] = None


# ==================== DATABASE MODELS (SERIALIZATION) ====================
class UserResponse(BaseModel):
    """User data response"""
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    is_premium: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Message data response"""
    id: int
    telegram_user_id: int
    message_id: int
    content: str
    message_type: str
    model_used: Optional[str]
    tokens_used: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class AITaskResponse(BaseModel):
    """AI task response"""
    id: int
    telegram_user_id: int
    task_type: str
    input_text: str
    output_text: Optional[str]
    model_used: str
    status: TaskStatus
    cost: float
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class SystemLogResponse(BaseModel):
    """System log response"""
    id: int
    level: LogLevel
    component: str
    message: str
    meta: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== API RESPONSE MODELS ====================
class ErrorResponse(BaseModel):
    """Standardized error response"""
    success: bool = False
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standardized success response"""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., regex='^(healthy|degraded|unhealthy)$')
    components: Dict[str, str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    uptime_seconds: Optional[int] = None
    version: Optional[str] = None


class MetricsResponse(BaseModel):
    """System metrics response"""
    total_messages: int = 0
    total_users: int = 0
    total_ai_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_response_time_ms: float = 0.0
    error_rate: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==================== RATE LIMITING ====================
class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""
    messages_per_user_per_minute: int = Field(default=10, ge=1, le=1000)
    messages_per_user_per_hour: int = Field(default=500, ge=1, le=10000)
    ai_requests_per_user_per_day: int = Field(default=100, ge=1, le=10000)
    global_requests_per_second: int = Field(default=100, ge=1, le=10000)
    burst_allowance: float = Field(default=1.5, ge=1.0, le=5.0)


# ==================== SECURITY ====================
class WebhookVerification(BaseModel):
    """Webhook verification data"""
    token: str = Field(..., min_length=20)
    timestamp: int = Field(..., gt=0)
    signature: str = Field(..., min_length=20)


class APIKeyRequest(BaseModel):
    """API key request"""
    key: str = Field(..., min_length=40, max_length=200)
    description: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)


# ==================== PAGINATION ====================
class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", regex='^(asc|desc)$')


# ==================== BATCH OPERATIONS ====================
class BatchMessageRequest(BaseModel):
    """Batch message processing request"""
    messages: List[MessageRequest] = Field(..., max_length=100)
    
    @field_validator('messages')
    @classmethod
    def validate_messages(cls, v):
        """Validate batch size"""
        if len(v) == 0:
            raise ValueError('Batch must contain at least one message')
        return v
