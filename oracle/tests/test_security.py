"""
Security tests for ORACLE
Tests for authentication, rate limiting, input sanitization
"""
import pytest
from core.security import (
    RateLimiter, InputSanitizer, TelegramWebhookValidator,
    APIKeyManager, SessionManager, admin_auth
)
from core.validation import validate_telegram_token, sanitize_html
import hashlib
import time

class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def test_rate_limiter_creation(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter(requests_per_minute=60, requests_per_hour=1000)
        assert limiter.rpm_limit == 60
        assert limiter.rph_limit == 1000
    
    def test_allow_request_within_limit(self):
        """Test allowing request within limit"""
        limiter = RateLimiter(requests_per_minute=5, requests_per_hour=50)
        
        allowed, error = limiter.is_allowed(user_id=123)
        assert allowed is True
        assert error is None
    
    def test_exceed_per_minute_limit(self):
        """Test exceeding per-minute rate limit"""
        limiter = RateLimiter(requests_per_minute=2, requests_per_hour=100)
        
        # Make 3 requests
        limiter.is_allowed(user_id=123)
        limiter.is_allowed(user_id=123)
        allowed, error = limiter.is_allowed(user_id=123)
        
        assert allowed is False
        assert "per-minute" in error.lower()
    
    def test_rate_limit_isolation(self):
        """Test that rate limits are per-user"""
        limiter = RateLimiter(requests_per_minute=2, requests_per_hour=100)
        
        # User 1 makes 2 requests
        limiter.is_allowed(user_id=1)
        limiter.is_allowed(user_id=1)
        
        # User 2 should still be able to make requests
        allowed, _ = limiter.is_allowed(user_id=2)
        assert allowed is True
    
    def test_get_user_stats(self):
        """Test getting rate limit stats"""
        limiter = RateLimiter(requests_per_minute=10, requests_per_hour=100)
        
        limiter.is_allowed(user_id=123)
        limiter.is_allowed(user_id=123)
        
        stats = limiter.get_user_stats(123)
        assert stats['requests_minute'] == 2
        assert stats['limit_minute'] == 10

class TestInputSanitizer:
    """Test input sanitization"""
    
    def test_sanitize_xss_script_tag(self):
        """Test removal of script tags"""
        malicious = "Hello <script>alert('xss')</script> world"
        sanitized = InputSanitizer.sanitize_message(malicious)
        
        assert "<script>" not in sanitized
        assert "alert" not in sanitized
    
    def test_sanitize_javascript_protocol(self):
        """Test removal of javascript: protocol"""
        malicious = '<a href="javascript:alert(1)">click</a>'
        sanitized = InputSanitizer.sanitize_message(malicious)
        
        assert "javascript:" not in sanitized
    
    def test_sanitize_event_handlers(self):
        """Test removal of event handlers"""
        malicious = '<img src=x onerror="alert(1)">'
        sanitized = InputSanitizer.sanitize_message(malicious)
        
        assert "onerror" not in sanitized
    
    def test_sanitize_max_length(self):
        """Test message length limiting"""
        long_text = "a" * 5000
        sanitized = InputSanitizer.sanitize_message(long_text, max_length=1000)
        
        assert len(sanitized) <= 1000
    
    def test_sanitize_null_bytes(self):
        """Test removal of null bytes"""
        malicious = "hello\x00world"
        sanitized = InputSanitizer.sanitize_message(malicious)
        
        assert "\x00" not in sanitized
    
    def test_sanitize_dict_recursive(self):
        """Test recursive dictionary sanitization"""
        data = {
            "text": "<script>bad</script>",
            "nested": {
                "html": '<img onerror="alert(1)">',
                "list": ["<iframe>", "normal"]
            }
        }
        
        sanitized = InputSanitizer.sanitize_dict(data)
        
        assert "<script>" not in sanitized["text"]
        assert "onerror" not in sanitized["nested"]["html"]
        assert "<iframe>" not in sanitized["nested"]["list"][0]

class TestTelegramWebhookValidator:
    """Test Telegram webhook validation"""
    
    def test_verify_webhook_signature(self):
        """Test webhook signature verification"""
        body = b'{"update_id": 123}'
        signature = hashlib.sha256(body).hexdigest()
        
        is_valid = TelegramWebhookValidator.verify_telegram_message(body, signature)
        assert is_valid is True
    
    def test_reject_invalid_signature(self):
        """Test rejection of invalid signature"""
        body = b'{"update_id": 123}'
        invalid_signature = "invalid_signature_here"
        
        is_valid = TelegramWebhookValidator.verify_telegram_message(body, invalid_signature)
        assert is_valid is False
    
    def test_reject_missing_signature(self):
        """Test rejection of missing signature"""
        body = b'{"update_id": 123}'
        
        is_valid = TelegramWebhookValidator.verify_telegram_message(body, None)
        assert is_valid is False
    
    def test_extract_token_from_url(self):
        """Test token extraction from webhook URL"""
        url = "https://example.com/webhook/123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk"
        token = TelegramWebhookValidator.extract_token_from_url(url)
        
        assert token is not None
        assert len(token) > 30

class TestAPIKeyManager:
    """Test API key management"""
    
    def test_generate_api_key(self):
        """Test API key generation"""
        key1 = APIKeyManager.generate_api_key()
        key2 = APIKeyManager.generate_api_key()
        
        assert len(key1) > 30
        assert len(key2) > 30
        assert key1 != key2
    
    def test_hash_api_key(self):
        """Test API key hashing"""
        key = "test_key_12345"
        hash1 = APIKeyManager.hash_key(key)
        hash2 = APIKeyManager.hash_key(key)
        
        # Same key should produce same hash
        assert hash1 == hash2
        # Hash should be hexadecimal
        assert all(c in '0123456789abcdef' for c in hash1)
    
    def test_verify_api_key(self):
        """Test API key verification"""
        key = "test_key_12345"
        key_hash = APIKeyManager.hash_key(key)
        
        is_valid = APIKeyManager.verify_api_key(key, key_hash)
        assert is_valid is True
    
    def test_verify_invalid_api_key(self):
        """Test rejection of invalid API key"""
        key = "test_key_12345"
        key_hash = APIKeyManager.hash_key(key)
        
        is_valid = APIKeyManager.verify_api_key("wrong_key", key_hash)
        assert is_valid is False

class TestSessionManager:
    """Test session management"""
    
    def test_create_session(self):
        """Test session creation"""
        manager = SessionManager()
        token = manager.create_session(user_id=123)
        
        assert token is not None
        assert len(token) > 20
    
    def test_validate_valid_session(self):
        """Test validation of valid session"""
        manager = SessionManager()
        token = manager.create_session(user_id=123)
        
        is_valid, user_id = manager.validate_session(token)
        assert is_valid is True
        assert user_id == 123
    
    def test_validate_invalid_session(self):
        """Test validation of invalid session"""
        manager = SessionManager()
        
        is_valid, user_id = manager.validate_session("invalid_token")
        assert is_valid is False
        assert user_id is None
    
    def test_session_expiration(self):
        """Test session expiration"""
        manager = SessionManager(token_expiry_hours=0)
        token = manager.create_session(user_id=123)
        
        # Wait a bit
        time.sleep(0.1)
        
        is_valid, user_id = manager.validate_session(token)
        assert is_valid is False
    
    def test_revoke_session(self):
        """Test session revocation"""
        manager = SessionManager()
        token = manager.create_session(user_id=123)
        
        manager.revoke_session(token)
        
        is_valid, _ = manager.validate_session(token)
        assert is_valid is False
    
    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions"""
        manager = SessionManager(token_expiry_hours=0)
        
        # Create multiple sessions
        for i in range(5):
            manager.create_session(user_id=i)
        
        time.sleep(0.1)
        
        count = manager.cleanup_expired()
        assert count == 5

class TestAdminAuth:
    """Test admin authentication"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "secure_password_123"
        hash1 = admin_auth.hash_password(password)
        hash2 = admin_auth.hash_password(password)
        
        # Hashes should be different (different salt)
        assert hash1 != hash2
        # But both should verify correctly
        assert admin_auth.verify_password(password, hash1)
        assert admin_auth.verify_password(password, hash2)
    
    def test_verify_correct_password(self):
        """Test password verification"""
        password = "correct_password"
        password_hash = admin_auth.hash_password(password)
        
        is_valid = admin_auth.verify_password(password, password_hash)
        assert is_valid is True
    
    def test_verify_incorrect_password(self):
        """Test rejection of incorrect password"""
        password = "correct_password"
        password_hash = admin_auth.hash_password(password)
        
        is_valid = admin_auth.verify_password("wrong_password", password_hash)
        assert is_valid is False

class TestValidationHelpers:
    """Test validation helper functions"""
    
    def test_validate_telegram_token_valid(self):
        """Test validation of valid Telegram token"""
        valid_token = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk"
        assert validate_telegram_token(valid_token) is True
    
    def test_validate_telegram_token_invalid(self):
        """Test validation of invalid Telegram token"""
        invalid_tokens = [
            "short",
            "12345:invalid",
            "no_colon",
            ""
        ]
        
        for token in invalid_tokens:
            assert validate_telegram_token(token) is False
    
    def test_sanitize_html_removes_scripts(self):
        """Test HTML sanitization"""
        html = '<p>Safe</p><script>bad()</script>'
        sanitized = sanitize_html(html)
        
        assert '<script>' not in sanitized
        assert 'bad()' not in sanitized
    
    def test_sanitize_html_preserves_safe_content(self):
        """Test that safe content is preserved"""
        html = '<p>Safe content</p>'
        sanitized = sanitize_html(html)
        
        assert 'Safe content' in sanitized

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
