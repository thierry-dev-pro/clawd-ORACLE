#!/usr/bin/env python3
"""
Verification script for ORACLE hardening implementation
Checks that all components are properly installed and configured
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_imports():
    """Check that all required modules can be imported"""
    print("🔍 Checking imports...")
    
    checks = {
        "Validation": "from core.validation import TelegramUpdate, ProcessMessageRequest",
        "Security": "from core.security import rate_limiter, TelegramWebhookValidator",
        "Exceptions": "from core.exceptions import OracleException",
        "Monitoring": "from core.monitoring import get_logger, metrics_collector",
    }
    
    failed = []
    for name, import_stmt in checks.items():
        try:
            exec(import_stmt)
            print(f"  ✅ {name}")
        except ImportError as e:
            print(f"  ❌ {name}: {e}")
            failed.append(name)
    
    return len(failed) == 0

def check_files():
    """Check that all required files exist"""
    print("\n🔍 Checking files...")
    
    base_path = Path(__file__).parent.parent
    
    files = {
        "core/validation.py": "Pydantic models",
        "core/security.py": "Security layer",
        "core/exceptions.py": "Custom exceptions",
        "core/monitoring.py": "Monitoring & logging",
        "core/main_robust.py": "Production FastAPI app",
        "tests/test_security.py": "Security tests",
        "tests/test_validation.py": "Validation tests",
        "docs/SECURITY_AUDIT.md": "Security documentation",
        "docs/MONITORING_SETUP.md": "Monitoring guide",
        "docs/PRODUCTION_CHECKLIST.md": "Production checklist",
        "docs/ROBUSTNESS_IMPLEMENTATION.md": "Implementation report",
    }
    
    failed = []
    for filepath, description in files.items():
        full_path = base_path / filepath
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✅ {filepath} ({size:,} bytes) - {description}")
        else:
            print(f"  ❌ {filepath} - MISSING")
            failed.append(filepath)
    
    return len(failed) == 0

def check_configuration():
    """Check environment configuration"""
    print("\n🔍 Checking configuration...")
    
    required_env = [
        'TELEGRAM_TOKEN',
        'ANTHROPIC_API_KEY',
    ]
    
    optional_env = [
        'ADMIN_PASSWORD_HASH',
        'LOG_LEVEL',
        'RATE_LIMIT_RPM',
        'RATE_LIMIT_RPH',
    ]
    
    failed = []
    
    # Check required
    for env_var in required_env:
        if os.getenv(env_var):
            value = os.getenv(env_var)
            masked = value[:5] + '*' * (len(value) - 10) + value[-5:]
            print(f"  ✅ {env_var} configured: {masked}")
        else:
            print(f"  ❌ {env_var} - MISSING")
            failed.append(env_var)
    
    # Check optional
    for env_var in optional_env:
        if os.getenv(env_var):
            print(f"  ✅ {env_var} = {os.getenv(env_var)}")
        else:
            print(f"  ⚠️  {env_var} - not set (using defaults)")
    
    return len(failed) == 0

def check_security():
    """Check security components"""
    print("\n🔍 Checking security components...")
    
    try:
        from core.security import (
            rate_limiter, TelegramWebhookValidator,
            InputSanitizer, SessionManager, admin_auth
        )
        from core.validation import validate_telegram_token
        
        # Check rate limiter
        allowed, _ = rate_limiter.is_allowed(user_id=999)
        if allowed:
            print("  ✅ Rate limiter functional")
        else:
            print("  ❌ Rate limiter not working")
            return False
        
        # Check webhook validator
        import hashlib
        test_body = b'test'
        signature = hashlib.sha256(test_body).hexdigest()
        result = TelegramWebhookValidator.verify_telegram_message(test_body, signature)
        if result:
            print("  ✅ Webhook validator functional")
        else:
            print("  ❌ Webhook validator not working")
            return False
        
        # Check input sanitizer
        malicious = "<script>alert(1)</script>"
        sanitized = InputSanitizer.sanitize_message(malicious)
        if "<script>" not in sanitized:
            print("  ✅ Input sanitizer functional")
        else:
            print("  ❌ Input sanitizer not working")
            return False
        
        # Check session manager
        manager = SessionManager()
        token = manager.create_session(user_id=123)
        if token:
            print("  ✅ Session manager functional")
        else:
            print("  ❌ Session manager not working")
            return False
        
        # Check password hashing
        password = "test_password_123"
        hash1 = admin_auth.hash_password(password)
        if admin_auth.verify_password(password, hash1):
            print("  ✅ Password hashing functional")
        else:
            print("  ❌ Password hashing not working")
            return False
        
        # Check token validation
        valid_token = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijk"
        if validate_telegram_token(valid_token):
            print("  ✅ Token validation functional")
        else:
            print("  ❌ Token validation not working")
            return False
        
        return True
    
    except Exception as e:
        print(f"  ❌ Error checking security: {e}")
        return False

def check_monitoring():
    """Check monitoring components"""
    print("\n🔍 Checking monitoring components...")
    
    try:
        from core.monitoring import (
            get_logger, metrics_collector,
            health_checker, alert_manager
        )
        
        # Check logger
        logger = get_logger(__name__)
        logger.info("test")
        print("  ✅ Logger functional")
        
        # Check metrics
        metrics = metrics_collector.get_metrics()
        if 'uptime_seconds' in metrics:
            print("  ✅ Metrics collector functional")
        else:
            print("  ❌ Metrics collector not working")
            return False
        
        # Check health checker
        if hasattr(health_checker, 'checks'):
            print("  ✅ Health checker functional")
        else:
            print("  ❌ Health checker not working")
            return False
        
        # Check alert manager
        if hasattr(alert_manager, 'alerts'):
            print("  ✅ Alert manager functional")
        else:
            print("  ❌ Alert manager not working")
            return False
        
        return True
    
    except Exception as e:
        print(f"  ❌ Error checking monitoring: {e}")
        return False

def check_validation():
    """Check validation components"""
    print("\n🔍 Checking validation components...")
    
    try:
        from pydantic import ValidationError
        from core.validation import (
            TelegramUser, TelegramMessage, TelegramUpdate,
            ProcessMessageRequest
        )
        
        # Check Telegram user validation
        try:
            user = TelegramUser(id=123, first_name="Test")
            print("  ✅ Telegram user validation working")
        except ValidationError as e:
            print(f"  ❌ Telegram user validation failed: {e}")
            return False
        
        # Check invalid user (negative ID)
        try:
            user = TelegramUser(id=-1, first_name="Test")
            print("  ❌ Should have rejected negative ID")
            return False
        except ValidationError:
            print("  ✅ Invalid ID properly rejected")
        
        # Check process message request
        try:
            req = ProcessMessageRequest(limit=10)
            print("  ✅ Process message request validation working")
        except ValidationError as e:
            print(f"  ❌ Process message request failed: {e}")
            return False
        
        # Check XSS detection
        try:
            from core.validation import TelegramChat
            chat = TelegramChat(id=1, type="private")
            msg = TelegramMessage(
                message_id=1,
                date=1234567890,
                chat=chat,
                text="<script>alert(1)</script>"
            )
            print("  ❌ Should have detected XSS")
            return False
        except ValidationError:
            print("  ✅ XSS detection working")
        
        return True
    
    except Exception as e:
        print(f"  ❌ Error checking validation: {e}")
        return False

def check_exceptions():
    """Check exception system"""
    print("\n🔍 Checking exception system...")
    
    try:
        from core.exceptions import (
            OracleException, ValidationError, UnauthorizedError,
            RateLimitExceeded
        )
        
        # Test OracleException
        exc = OracleException("test error", code="TEST", status_code=400)
        if exc.status_code == 400:
            print("  ✅ OracleException working")
        else:
            print("  ❌ OracleException not working")
            return False
        
        # Test exception to dict conversion
        exc_dict = exc.to_dict()
        if 'error' in exc_dict and 'code' in exc_dict:
            print("  ✅ Exception serialization working")
        else:
            print("  ❌ Exception serialization not working")
            return False
        
        # Test RateLimitExceeded
        exc = RateLimitExceeded("Too many requests", retry_after=60)
        if exc.status_code == 429:
            print("  ✅ RateLimitExceeded working")
        else:
            print("  ❌ RateLimitExceeded not working")
            return False
        
        return True
    
    except Exception as e:
        print(f"  ❌ Error checking exceptions: {e}")
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("🔮 ORACLE Hardening Verification")
    print("=" * 60)
    
    results = {
        "Imports": check_imports(),
        "Files": check_files(),
        "Configuration": check_configuration(),
        "Security": check_security(),
        "Monitoring": check_monitoring(),
        "Validation": check_validation(),
        "Exceptions": check_exceptions(),
    }
    
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}: {'PASS' if result else 'FAIL'}")
    
    print("\n" + "=" * 60)
    
    if passed == total:
        print(f"✅ All checks passed! ({passed}/{total})")
        print("\n🚀 ORACLE is ready for deployment!")
        return 0
    else:
        print(f"⚠️  {total - passed} check(s) failed ({passed}/{total})")
        print("\nPlease fix the issues above and retry.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
