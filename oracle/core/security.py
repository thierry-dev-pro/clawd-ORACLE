"""
Security utilities for ORACLE
Includes webhook verification, rate limiting, input sanitization, and API key management
"""
import hmac
import hashlib
import json
import logging
import time
from typing import Optional, Dict, Tuple, Any
from datetime import datetime, timedelta
from functools import wraps
import re
from collections import defaultdict
from threading import RLock

from core.config import settings
from core.exceptions import (
    WebhookSignatureError,
    RateLimitError,
    UnauthorizedError,
    InvalidAPIKeyError
)

logger = logging.getLogger(__name__)


# ==================== WEBHOOK VERIFICATION ====================
class WebhookVerifier:
    """Verify Telegram webhook authenticity"""
    
    SIGNATURE_TIMESTAMP_TOLERANCE = 300  # 5 minutes
    
    @staticmethod
    def verify_signature(
        body: str,
        signature: str,
        token: str = settings.TELEGRAM_TOKEN
    ) -> bool:
        """
        Verify webhook signature using HMAC-SHA256
        
        Args:
            body: Raw request body
            signature: X-Telegram-Bot-Api-Secret-Hash header
            token: Bot token for verification
        
        Returns:
            True if signature is valid
        
        Raises:
            WebhookSignatureError: If signature is invalid
        """
        if not token:
            raise WebhookSignatureError(
                "Telegram token not configured",
                details={"issue": "TELEGRAM_TOKEN not set"}
            )
        
        if not signature:
            raise WebhookSignatureError(
                "Missing signature header",
                details={"missing_header": "X-Telegram-Bot-Api-Secret-Hash"}
            )
        
        # Calculate expected signature
        secret = hashlib.sha256(token.encode()).digest()
        expected_signature = hmac.new(
            secret,
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures (constant-time comparison)
        if not hmac.compare_digest(expected_signature, signature):
            logger.warning(
                f"Invalid webhook signature. Expected: {expected_signature[:8]}..., "
                f"Got: {signature[:8]}..."
            )
            raise WebhookSignatureError(
                "Webhook signature verification failed",
                details={
                    "reason": "Signature does not match expected value",
                    "expected_prefix": expected_signature[:8],
                    "received_prefix": signature[:8]
                }
            )
        
        return True
    
    @staticmethod
    def verify_request(
        body: str,
        signature: str,
        token: Optional[str] = None
    ) -> bool:
        """Verify complete webhook request"""
        return WebhookVerifier.verify_signature(body, signature, token)


# ==================== RATE LIMITING ====================
class RateLimiter:
    """Token bucket based rate limiter"""
    
    def __init__(self):
        self.buckets: Dict[str, Dict[str, Any]] = {}
        self.lock = RLock()
    
    def _get_bucket(self, key: str) -> Dict[str, Any]:
        """Get or create rate limit bucket"""
        with self.lock:
            if key not in self.buckets:
                self.buckets[key] = {
                    "tokens": 1000,  # Start with full bucket
                    "last_refill": time.time(),
                    "capacity": 1000
                }
            return self.buckets[key]
    
    def _refill(self, bucket: Dict[str, Any], tokens_per_second: float) -> None:
        """Refill bucket based on elapsed time"""
        now = time.time()
        elapsed = now - bucket["last_refill"]
        new_tokens = elapsed * tokens_per_second
        bucket["tokens"] = min(bucket["capacity"], bucket["tokens"] + new_tokens)
        bucket["last_refill"] = now
    
    def is_allowed(
        self,
        key: str,
        tokens: int = 1,
        tokens_per_second: float = 10.0
    ) -> bool:
        """
        Check if request is allowed under rate limit
        
        Args:
            key: Unique identifier (user_id, IP, etc.)
            tokens: Number of tokens to consume
            tokens_per_second: Refill rate
        
        Returns:
            True if allowed, False otherwise
        """
        with self.lock:
            bucket = self._get_bucket(key)
            self._refill(bucket, tokens_per_second)
            
            if bucket["tokens"] >= tokens:
                bucket["tokens"] -= tokens
                return True
            return False
    
    def check_limit(
        self,
        key: str,
        tokens: int = 1,
        tokens_per_second: float = 10.0
    ) -> None:
        """
        Check rate limit and raise exception if exceeded
        
        Raises:
            RateLimitError: If rate limit exceeded
        """
        if not self.is_allowed(key, tokens, tokens_per_second):
            raise RateLimitError(
                f"Rate limit exceeded for {key}",
                details={
                    "key": key,
                    "tokens_requested": tokens
                }
            )
    
    def get_status(self, key: str) -> Dict[str, Any]:
        """Get rate limit status for key"""
        bucket = self._get_bucket(key)
        return {
            "tokens_available": int(bucket["tokens"]),
            "capacity": bucket["capacity"],
            "next_refill": bucket["last_refill"] + 1.0  # Refills every second
        }
    
    def reset(self, key: str) -> None:
        """Reset rate limit bucket"""
        with self.lock:
            if key in self.buckets:
                bucket = self.buckets[key]
                bucket["tokens"] = bucket["capacity"]
                bucket["last_refill"] = time.time()


# ==================== INPUT SANITIZATION ====================
class InputSanitizer:
    """Sanitize and validate user inputs"""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|;)",
        r"/\*.*?\*/",
        r"xp_",
        r"sp_"
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"on\w+\s*=",
        r"javascript:",
        r"<iframe",
        r"<object",
        r"<embed"
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$\(\)]",
    ]
    
    @staticmethod
    def sanitize_text(
        text: str,
        max_length: int = 4096,
        allow_newlines: bool = True
    ) -> str:
        """
        Sanitize text input
        
        Args:
            text: Input text
            max_length: Maximum allowed length
            allow_newlines: Allow newline characters
        
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            raise ValueError("Input must be string")
        
        # Remove null bytes
        text = text.replace('\0', '')
        
        # Handle newlines
        if not allow_newlines:
            text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    @staticmethod
    def check_sql_injection(text: str) -> bool:
        """
        Check if text contains SQL injection patterns
        
        Args:
            text: Text to check
        
        Returns:
            True if potential SQL injection detected
        """
        text_upper = text.upper()
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def check_xss(text: str) -> bool:
        """
        Check if text contains XSS patterns
        
        Args:
            text: Text to check
        
        Returns:
            True if potential XSS detected
        """
        for pattern in InputSanitizer.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def check_command_injection(text: str) -> bool:
        """
        Check if text contains command injection patterns
        
        Args:
            text: Text to check
        
        Returns:
            True if potential command injection detected
        """
        for pattern in InputSanitizer.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, text):
                return True
        return False
    
    @staticmethod
    def validate_and_sanitize(
        text: str,
        max_length: int = 4096,
        check_injection: bool = True
    ) -> str:
        """
        Comprehensive input validation and sanitization
        
        Args:
            text: Input text
            max_length: Maximum allowed length
            check_injection: Check for injection attacks
        
        Returns:
            Sanitized and validated text
        
        Raises:
            ValueError: If validation fails
        """
        text = InputSanitizer.sanitize_text(text, max_length)
        
        if check_injection:
            if InputSanitizer.check_sql_injection(text):
                raise ValueError("Potential SQL injection detected")
            if InputSanitizer.check_xss(text):
                raise ValueError("Potential XSS attack detected")
            if InputSanitizer.check_command_injection(text):
                raise ValueError("Potential command injection detected")
        
        return text


# ==================== API KEY MANAGEMENT ====================
class APIKeyManager:
    """Manage API keys for authentication"""
    
    def __init__(self):
        self.keys: Dict[str, Dict[str, Any]] = {}
        self.lock = RLock()
    
    def generate_key(self) -> str:
        """Generate new API key"""
        import secrets
        return f"sk_{secrets.token_urlsafe(32)}"
    
    def add_key(
        self,
        key: str,
        name: str,
        scopes: list = None,
        expires_in_days: Optional[int] = None
    ) -> None:
        """
        Add API key
        
        Args:
            key: API key
            name: Key name
            scopes: List of allowed scopes
            expires_in_days: Expiration time in days
        """
        with self.lock:
            self.keys[key] = {
                "name": name,
                "scopes": scopes or ["read"],
                "created_at": datetime.utcnow(),
                "expires_at": (
                    datetime.utcnow() + timedelta(days=expires_in_days)
                    if expires_in_days else None
                ),
                "last_used": None,
                "active": True
            }
    
    def validate_key(self, key: str, required_scopes: list = None) -> bool:
        """
        Validate API key
        
        Args:
            key: API key to validate
            required_scopes: Required scopes
        
        Returns:
            True if valid
        
        Raises:
            InvalidAPIKeyError: If key is invalid
        """
        if not key or not isinstance(key, str):
            raise InvalidAPIKeyError("Invalid API key format")
        
        with self.lock:
            if key not in self.keys:
                raise InvalidAPIKeyError("API key not found")
            
            key_info = self.keys[key]
            
            # Check if active
            if not key_info.get("active"):
                raise InvalidAPIKeyError("API key is inactive")
            
            # Check expiration
            if key_info.get("expires_at"):
                if datetime.utcnow() > key_info["expires_at"]:
                    raise InvalidAPIKeyError("API key has expired")
            
            # Check scopes
            if required_scopes:
                key_scopes = set(key_info.get("scopes", []))
                if not key_scopes & set(required_scopes):
                    raise InvalidAPIKeyError("API key does not have required scopes")
            
            # Update last used
            key_info["last_used"] = datetime.utcnow()
            
            return True
    
    def revoke_key(self, key: str) -> None:
        """Revoke API key"""
        with self.lock:
            if key in self.keys:
                self.keys[key]["active"] = False
    
    def get_key_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Get key information"""
        with self.lock:
            return self.keys.get(key, {}).copy() if key in self.keys else None


# ==================== DECORATORS ====================
def require_api_key(required_scopes: list = None):
    """Decorator to require API key validation"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, api_key: Optional[str] = None, **kwargs):
            if not api_key:
                raise UnauthorizedError("API key required")
            # Validate key
            api_key_manager = APIKeyManager()
            api_key_manager.validate_key(api_key, required_scopes)
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, api_key: Optional[str] = None, **kwargs):
            if not api_key:
                raise UnauthorizedError("API key required")
            # Validate key
            api_key_manager = APIKeyManager()
            api_key_manager.validate_key(api_key, required_scopes)
            return func(*args, **kwargs)
        
        return async_wrapper if hasattr(func, '__await__') else sync_wrapper
    return decorator


def rate_limit(
    tokens_per_second: float = 10.0,
    key_func=None
):
    """Decorator to apply rate limiting"""
    def decorator(func):
        rate_limiter = RateLimiter()
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract key from arguments
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = str(args[0]) if args else "default"
            
            rate_limiter.check_limit(key, tokens_per_second=tokens_per_second)
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = str(args[0]) if args else "default"
            
            rate_limiter.check_limit(key, tokens_per_second=tokens_per_second)
            return func(*args, **kwargs)
        
        return async_wrapper if hasattr(func, '__await__') else sync_wrapper
    return decorator


# ==================== SINGLETON INSTANCES ====================
webhook_verifier = WebhookVerifier()
rate_limiter = RateLimiter()
input_sanitizer = InputSanitizer()
api_key_manager = APIKeyManager()
