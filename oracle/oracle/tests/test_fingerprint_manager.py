"""
Tests for fingerprint manager - Anti-bot detection system.
"""

import pytest
from datetime import datetime, timedelta
from oracle.core.fingerprint_manager import (
    FingerprintManager,
    BrowserFingerprint,
    OSType,
    BrowserType,
    TimezoneType,
    create_camofox_fingerprint_config
)


class TestFingerprintGeneration:
    """Test fingerprint generation."""
    
    def test_init(self):
        """Test manager initialization."""
        manager = FingerprintManager()
        assert manager.fingerprints == {}
        assert manager.session_to_fingerprint == {}
    
    def test_generate_fingerprint_chrome_windows(self):
        """Test Chrome on Windows fingerprint."""
        manager = FingerprintManager()
        
        fp = manager.generate_fingerprint(
            "session-1",
            browser="Chrome",
            os_type="Win32",
            timezone="America/New_York"
        )
        
        assert fp.platform == "Win32"
        assert "Chrome" in fp.user_agent
        assert fp.hardware_concurrency >= 4
        assert fp.hardware_concurrency <= 16
        assert fp.device_memory in [4, 8, 16, 32]
        assert fp.language == "en-US"
        assert fp.timezone == "America/New_York"
        assert fp.canvas_fingerprint is not None
        assert len(fp.canvas_fingerprint) == 16
    
    def test_generate_fingerprint_firefox_mac(self):
        """Test Firefox on macOS fingerprint."""
        manager = FingerprintManager()
        
        fp = manager.generate_fingerprint(
            "session-2",
            browser="Firefox",
            os_type="MacIntel",
            timezone="Europe/Paris"
        )
        
        assert fp.platform == "MacIntel"
        assert "Firefox" in fp.user_agent
        assert fp.language == "fr-FR"
        assert fp.timezone == "Europe/Paris"
        assert fp.timezone_offset == 60
    
    def test_generate_fingerprint_safari(self):
        """Test Safari fingerprint."""
        manager = FingerprintManager()
        
        fp = manager.generate_fingerprint(
            "session-3",
            browser="Safari",
            os_type="MacIntel"
        )
        
        assert fp.platform == "MacIntel"
        assert "Safari" in fp.user_agent
        assert fp.browser_vendor == "Apple Inc."
    
    def test_fingerprint_unique(self):
        """Test that fingerprints are unique."""
        manager = FingerprintManager()
        
        fp1 = manager.generate_fingerprint("session-1")
        fp2 = manager.generate_fingerprint("session-2")
        fp3 = manager.generate_fingerprint("session-3")
        
        canvas_hashes = [fp1.canvas_fingerprint, fp2.canvas_fingerprint, fp3.canvas_fingerprint]
        assert len(set(canvas_hashes)) == 3  # All unique


class TestFingerprintStorage:
    """Test fingerprint storage and retrieval."""
    
    def test_store_and_retrieve(self):
        """Test storing and retrieving fingerprints."""
        manager = FingerprintManager()
        
        fp = manager.generate_fingerprint("session-1")
        retrieved = manager.get_fingerprint("session-1")
        
        assert retrieved is not None
        assert retrieved.canvas_fingerprint == fp.canvas_fingerprint
        assert retrieved.use_count == 1  # Incremented on retrieval
    
    def test_get_nonexistent_fingerprint(self):
        """Test retrieving nonexistent fingerprint."""
        manager = FingerprintManager()
        
        result = manager.get_fingerprint("nonexistent")
        assert result is None
    
    def test_fingerprint_use_count(self):
        """Test fingerprint use counting."""
        manager = FingerprintManager()
        
        manager.generate_fingerprint("session-1")
        
        fp1 = manager.get_fingerprint("session-1")
        assert fp1.use_count == 1
        
        fp2 = manager.get_fingerprint("session-1")
        assert fp2.use_count == 2


class TestFingerprintRotation:
    """Test fingerprint rotation."""
    
    def test_rotate_single_fingerprint(self):
        """Test rotating a single fingerprint."""
        manager = FingerprintManager()
        
        fp1 = manager.generate_fingerprint("session-1", browser="Chrome")
        original_hash = fp1.canvas_fingerprint
        
        # Rotate
        manager.rotate_fingerprints(["session-1"], new_browser="Firefox")
        fp2 = manager.get_fingerprint("session-1")
        
        assert fp2.canvas_fingerprint != original_hash
        assert "Firefox" in fp2.user_agent
    
    def test_rotate_multiple_fingerprints(self):
        """Test rotating multiple fingerprints."""
        manager = FingerprintManager()
        
        sessions = [f"session-{i}" for i in range(5)]
        
        # Generate initial
        for session in sessions:
            manager.generate_fingerprint(session, browser="Chrome")
        
        # Rotate all
        results = manager.rotate_fingerprints(sessions)
        
        assert len(results) == 5
        
        # Verify all rotated
        for session in sessions:
            fp = manager.get_fingerprint(session)
            assert fp is not None
    
    def test_rotate_with_new_os(self):
        """Test rotating with new OS."""
        manager = FingerprintManager()
        
        fp1 = manager.generate_fingerprint("session-1", os_type="Win32")
        manager.rotate_fingerprints(["session-1"], new_os="MacIntel")
        
        fp2 = manager.get_fingerprint("session-1")
        assert fp2.platform == "MacIntel"


class TestFingerprintCleanup:
    """Test fingerprint cleanup."""
    
    def test_cleanup_old_fingerprints(self):
        """Test removing old fingerprints."""
        manager = FingerprintManager()
        
        # Create 3 fingerprints
        manager.generate_fingerprint("session-1")
        manager.generate_fingerprint("session-2")
        manager.generate_fingerprint("session-3")
        
        # Mark 2 as old
        manager.fingerprints["session-1"].last_used = datetime.now() - timedelta(days=10)
        manager.fingerprints["session-2"].last_used = datetime.now() - timedelta(days=10)
        
        # Cleanup
        deleted = manager.cleanup_old_fingerprints(days_old=7)
        
        assert deleted == 2
        assert "session-3" in manager.fingerprints
        assert "session-1" not in manager.fingerprints
        assert "session-2" not in manager.fingerprints
    
    def test_cleanup_no_old_fingerprints(self):
        """Test cleanup when no old fingerprints exist."""
        manager = FingerprintManager()
        
        manager.generate_fingerprint("session-1")
        
        deleted = manager.cleanup_old_fingerprints(days_old=7)
        
        assert deleted == 0
        assert "session-1" in manager.fingerprints


class TestFingerprintStatistics:
    """Test fingerprint statistics."""
    
    def test_get_statistics_empty(self):
        """Test statistics on empty manager."""
        manager = FingerprintManager()
        
        stats = manager.get_statistics()
        
        assert stats["total"] == 0
        assert stats["avg_use_count"] == 0
        assert stats["unique_browsers"] == 0
        assert stats["unique_os"] == 0
    
    def test_get_statistics_with_fingerprints(self):
        """Test statistics with fingerprints."""
        manager = FingerprintManager()
        
        manager.generate_fingerprint("session-1", browser="Chrome", os_type="Win32")
        manager.generate_fingerprint("session-2", browser="Firefox", os_type="MacIntel")
        manager.generate_fingerprint("session-3", browser="Chrome", os_type="Win32")
        
        stats = manager.get_statistics()
        
        assert stats["total"] == 3
        assert stats["unique_browsers"] > 0
        assert stats["unique_os"] > 0


class TestFingerprintHelpers:
    """Test fingerprint helper methods."""
    
    def test_get_user_agent_chrome_windows(self):
        """Test user agent retrieval."""
        manager = FingerprintManager()
        
        ua = manager._get_user_agent("Chrome", "Win32")
        assert "Chrome" in ua
        assert "Windows" in ua
    
    def test_get_browser_vendor(self):
        """Test browser vendor."""
        manager = FingerprintManager()
        
        assert manager._get_browser_vendor("Chrome") == "Google Inc."
        assert manager._get_browser_vendor("Firefox") == "Mozilla"
        assert manager._get_browser_vendor("Safari") == "Apple Inc."
    
    def test_get_timezone_offset(self):
        """Test timezone offset calculation."""
        manager = FingerprintManager()
        
        assert manager._get_timezone_offset("America/New_York") == -300
        assert manager._get_timezone_offset("Europe/Paris") == 60
        assert manager._get_timezone_offset("Asia/Tokyo") == 540
    
    def test_get_language_from_timezone(self):
        """Test language detection from timezone."""
        manager = FingerprintManager()
        
        assert manager._get_language_from_timezone("America/New_York") == "en-US"
        assert manager._get_language_from_timezone("Europe/Paris") == "fr-FR"
        assert manager._get_language_from_timezone("Asia/Tokyo") == "ja-JP"
    
    def test_get_language_list(self):
        """Test language list generation."""
        manager = FingerprintManager()
        
        langs = manager._get_language_list("Europe/Paris")
        assert "fr-FR" in langs
        assert "en-US" in langs or "en-GB" in langs


class TestCamofoxConfig:
    """Test Camofox configuration generation."""
    
    def test_create_camofox_fingerprint_config(self):
        """Test creating Camofox-compatible config."""
        manager = FingerprintManager()
        fp = manager.generate_fingerprint("session-1")
        
        config = create_camofox_fingerprint_config(fp)
        
        assert config["userAgent"] == fp.user_agent
        assert config["hardwareConcurrency"] == fp.hardware_concurrency
        assert config["platform"] == fp.platform
        assert config["timezone"] == fp.timezone
        assert config["language"] == fp.language
        assert "languages" in config
        assert "colorDepth" in config
        assert "webglVendor" in config


class TestFingerprintDiversity:
    """Test fingerprint diversity metrics."""
    
    def test_fingerprint_diversity(self):
        """Test that generated fingerprints are diverse."""
        manager = FingerprintManager()
        
        # Generate 20 fingerprints
        for i in range(20):
            manager.generate_fingerprint(f"session-{i}")
        
        stats = manager.get_statistics()
        
        # Should have multiple unique combinations
        assert stats["total"] == 20
        # Hardware concurrency varies
        hardware = [fp.hardware_concurrency for fp in manager.fingerprints.values()]
        assert len(set(hardware)) > 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
