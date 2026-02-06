"""
Validation tests for ORACLE
Tests for Pydantic models and input validation
"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from core.validation import (
    TelegramUser, TelegramChat, TelegramMessage, TelegramUpdate,
    ProcessMessageRequest, HealthResponse, ErrorResponse,
    MetricsResponse, AutoResponsePattern, AdminAuthRequest
)

class TestTelegramUser:
    """Test Telegram user validation"""
    
    def test_valid_user(self):
        """Test valid user"""
        user = TelegramUser(
            id=123456789,
            first_name="John",
            username="john_doe"
        )
        assert user.id == 123456789
        assert user.first_name == "John"
    
    def test_user_invalid_id(self):
        """Test user with invalid ID"""
        with pytest.raises(ValidationError):
            TelegramUser(
                id=-1,  # Invalid: negative ID
                first_name="John"
            )
    
    def test_user_invalid_username(self):
        """Test user with invalid username"""
        with pytest.raises(ValidationError):
            TelegramUser(
                id=123456789,
                first_name="John",
                username="inv@lid"  # Invalid characters
            )
    
    def test_user_missing_first_name(self):
        """Test user with missing first name"""
        with pytest.raises(ValidationError):
            TelegramUser(
                id=123456789,
                first_name=""  # Empty string
            )

class TestTelegramChat:
    """Test Telegram chat validation"""
    
    def test_valid_private_chat(self):
        """Test valid private chat"""
        chat = TelegramChat(
            id=123456789,
            type="private"
        )
        assert chat.type == "private"
    
    def test_valid_group_chat(self):
        """Test valid group chat"""
        chat = TelegramChat(
            id=-987654321,  # Groups have negative IDs
            type="group",
            title="Test Group"
        )
        assert chat.type == "group"
        assert chat.title == "Test Group"
    
    def test_chat_invalid_type(self):
        """Test chat with invalid type"""
        with pytest.raises(ValidationError):
            TelegramChat(
                id=123456789,
                type="invalid_type"
            )

class TestTelegramMessage:
    """Test Telegram message validation"""
    
    def test_valid_message(self):
        """Test valid message"""
        message = TelegramMessage(
            message_id=1,
            date=1234567890,
            chat=TelegramChat(id=123, type="private"),
            text="Hello world"
        )
        assert message.text == "Hello world"
    
    def test_message_without_text(self):
        """Test message without text"""
        message = TelegramMessage(
            message_id=1,
            date=1234567890,
            chat=TelegramChat(id=123, type="private")
        )
        assert message.text is None
    
    def test_message_xss_detection(self):
        """Test XSS detection in message"""
        with pytest.raises(ValidationError):
            TelegramMessage(
                message_id=1,
                date=1234567890,
                chat=TelegramChat(id=123, type="private"),
                text="Normal text <script>alert(1)</script>"
            )
    
    def test_message_javascript_protocol_detection(self):
        """Test javascript: protocol detection"""
        with pytest.raises(ValidationError):
            TelegramMessage(
                message_id=1,
                date=1234567890,
                chat=TelegramChat(id=123, type="private"),
                text='<a href="javascript:alert(1)">click</a>'
            )
    
    def test_message_max_length(self):
        """Test message max length"""
        with pytest.raises(ValidationError):
            TelegramMessage(
                message_id=1,
                date=1234567890,
                chat=TelegramChat(id=123, type="private"),
                text="a" * 5000  # Exceeds 4096 limit
            )

class TestTelegramUpdate:
    """Test Telegram update validation"""
    
    def test_valid_update(self):
        """Test valid update"""
        update = TelegramUpdate(
            update_id=123,
            message=TelegramMessage(
                message_id=1,
                date=1234567890,
                chat=TelegramChat(id=123, type="private"),
                text="Hello"
            )
        )
        assert update.update_id == 123
        assert update.message.text == "Hello"
    
    def test_update_without_message(self):
        """Test update without message"""
        update = TelegramUpdate(update_id=123)
        assert update.message is None
    
    def test_update_invalid_id(self):
        """Test update with invalid ID"""
        with pytest.raises(ValidationError):
            TelegramUpdate(
                update_id=-1  # Invalid: negative
            )

class TestProcessMessageRequest:
    """Test process message request validation"""
    
    def test_valid_request_defaults(self):
        """Test valid request with defaults"""
        request = ProcessMessageRequest()
        assert request.limit == 10
        assert request.user_id is None
    
    def test_valid_request_custom(self):
        """Test valid request with custom values"""
        request = ProcessMessageRequest(limit=50, user_id=123)
        assert request.limit == 50
        assert request.user_id == 123
    
    def test_invalid_limit_too_small(self):
        """Test invalid limit (too small)"""
        with pytest.raises(ValidationError):
            ProcessMessageRequest(limit=0)
    
    def test_invalid_limit_too_large(self):
        """Test invalid limit (too large)"""
        with pytest.raises(ValidationError):
            ProcessMessageRequest(limit=1000)  # Exceeds 100 limit
    
    def test_invalid_user_id(self):
        """Test invalid user ID"""
        with pytest.raises(ValidationError):
            ProcessMessageRequest(user_id=-1)

class TestHealthResponse:
    """Test health response validation"""
    
    def test_valid_health_response(self):
        """Test valid health response"""
        response = HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            components={"database": "ok", "api": "ok"},
            version="1.0.0"
        )
        assert response.status == "healthy"
    
    def test_invalid_status(self):
        """Test invalid status"""
        with pytest.raises(ValidationError):
            HealthResponse(
                status="unknown",
                timestamp=datetime.utcnow(),
                components={},
                version="1.0.0"
            )

class TestErrorResponse:
    """Test error response validation"""
    
    def test_valid_error_response(self):
        """Test valid error response"""
        response = ErrorResponse(
            error="Bad request",
            code="VALIDATION_ERROR",
            timestamp=datetime.utcnow()
        )
        assert response.code == "VALIDATION_ERROR"
    
    def test_invalid_code_format(self):
        """Test invalid code format"""
        with pytest.raises(ValidationError):
            ErrorResponse(
                error="Bad request",
                code="invalid-code",  # Should be uppercase with underscores
                timestamp=datetime.utcnow()
            )

class TestMetricsResponse:
    """Test metrics response validation"""
    
    def test_valid_metrics(self):
        """Test valid metrics"""
        response = MetricsResponse(
            timestamp=datetime.utcnow(),
            total_messages=1000,
            user_messages=600,
            ai_responses=400,
            total_tokens_used=50000,
            average_response_time_ms=1250.5
        )
        assert response.total_messages == 1000
    
    def test_invalid_error_rate(self):
        """Test invalid error rate (out of range)"""
        with pytest.raises(ValidationError):
            MetricsResponse(
                timestamp=datetime.utcnow(),
                total_messages=1000,
                user_messages=600,
                ai_responses=400,
                total_tokens_used=50000,
                average_response_time_ms=1250.5,
                error_rate=1.5  # Out of range [0, 1]
            )

class TestAutoResponsePattern:
    """Test auto-response pattern validation"""
    
    def test_valid_pattern(self):
        """Test valid pattern"""
        pattern = AutoResponsePattern(
            trigger="hello",
            response="Hi there!",
            match_type="contains"
        )
        assert pattern.trigger == "hello"
        assert pattern.enabled is True
    
    def test_invalid_match_type(self):
        """Test invalid match type"""
        with pytest.raises(ValidationError):
            AutoResponsePattern(
                trigger="hello",
                response="Hi there!",
                match_type="invalid"
            )
    
    def test_empty_trigger(self):
        """Test empty trigger"""
        with pytest.raises(ValidationError):
            AutoResponsePattern(
                trigger="",
                response="Hi there!"
            )
    
    def test_trigger_sanitized(self):
        """Test that trigger is sanitized"""
        pattern = AutoResponsePattern(
            trigger="  hello  ",  # Extra whitespace
            response="Hi there!"
        )
        # Should be trimmed
        assert pattern.trigger == "hello"

class TestAdminAuthRequest:
    """Test admin auth request validation"""
    
    def test_valid_password(self):
        """Test valid password"""
        request = AdminAuthRequest(password="secure_password_123")
        assert request.password == "secure_password_123"
    
    def test_password_too_short(self):
        """Test password too short"""
        with pytest.raises(ValidationError):
            AdminAuthRequest(password="short")
    
    def test_password_too_long(self):
        """Test password too long"""
        with pytest.raises(ValidationError):
            AdminAuthRequest(password="a" * 300)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
