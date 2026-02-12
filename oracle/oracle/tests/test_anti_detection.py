"""
Tests for anti-detection system - Fingerprint + proxy rotation.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from oracle.core.camofox_anti_detection import (
    ProxyRotator,
    AntiDetectionSession,
    AntiDetectionPool
)


class TestProxyRotator:
    """Test proxy rotator."""
    
    def test_init_empty(self):
        """Test initialization with no proxies."""
        rotator = ProxyRotator()
        assert rotator.proxies == []
    
    def test_init_with_proxies(self):
        """Test initialization with proxies."""
        proxies = ["http://proxy1:8080", "http://proxy2:8080"]
        rotator = ProxyRotator(proxies)
        
        assert rotator.proxies == proxies
        assert len(rotator.usage_count) == 2
    
    def test_get_next_proxy_rotation(self):
        """Test proxy rotation."""
        proxies = ["proxy1", "proxy2", "proxy3"]
        rotator = ProxyRotator(proxies)
        
        assert rotator.get_next_proxy() == "proxy1"
        assert rotator.get_next_proxy() == "proxy2"
        assert rotator.get_next_proxy() == "proxy3"
        assert rotator.get_next_proxy() == "proxy1"  # Cycles back
    
    def test_get_next_proxy_usage_count(self):
        """Test proxy usage counting."""
        proxies = ["proxy1", "proxy2"]
        rotator = ProxyRotator(proxies)
        
        rotator.get_next_proxy()
        rotator.get_next_proxy()
        rotator.get_next_proxy()
        
        assert rotator.usage_count["proxy1"] == 2
        assert rotator.usage_count["proxy2"] == 1
    
    def test_get_least_used_proxy(self):
        """Test getting least used proxy."""
        proxies = ["proxy1", "proxy2", "proxy3"]
        rotator = ProxyRotator(proxies)
        
        # Use proxy1 and proxy2
        rotator.usage_count["proxy1"] = 5
        rotator.usage_count["proxy2"] = 3
        rotator.usage_count["proxy3"] = 0
        
        least = rotator.get_least_used_proxy()
        assert least == "proxy3"
    
    def test_add_proxy(self):
        """Test adding proxy."""
        rotator = ProxyRotator()
        rotator.add_proxy("proxy1")
        
        assert "proxy1" in rotator.proxies
        assert rotator.usage_count["proxy1"] == 0
    
    def test_remove_proxy(self):
        """Test removing proxy."""
        proxies = ["proxy1", "proxy2"]
        rotator = ProxyRotator(proxies)
        
        rotator.remove_proxy("proxy1")
        
        assert "proxy1" not in rotator.proxies
        assert "proxy1" not in rotator.usage_count
    
    def test_get_statistics(self):
        """Test proxy statistics."""
        proxies = ["proxy1", "proxy2"]
        rotator = ProxyRotator(proxies)
        
        rotator.get_next_proxy()
        rotator.get_next_proxy()
        
        stats = rotator.get_statistics()
        
        assert stats["total"] == 2
        assert "usage" in stats
        assert "least_used" in stats
        assert "most_used" in stats


class TestAntiDetectionSession:
    """Test anti-detection session."""
    
    @patch('oracle.core.camofox_anti_detection.CamofoxClient')
    @patch('oracle.core.camofox_anti_detection.FingerprintManager')
    def test_init(self, mock_fp_mgr, mock_camofox):
        """Test session initialization."""
        session = AntiDetectionSession(
            "session-1",
            mock_camofox,
            mock_fp_mgr
        )
        
        assert session.session_key == "session-1"
        assert session.tab_id is None
        assert session.fingerprint is None
        assert session.proxy is None
    
    @patch('oracle.core.camofox_anti_detection.CamofoxClient')
    @patch('oracle.core.camofox_anti_detection.FingerprintManager')
    def test_start_session(self, mock_fp_mgr, mock_camofox):
        """Test starting session."""
        # Setup mocks
        mock_camofox_instance = Mock()
        mock_camofox_instance.create_tab.return_value = "tab-123"
        
        mock_fp_mgr_instance = Mock()
        mock_fp = Mock()
        mock_fp.user_agent = "Mozilla/5.0 Chrome"
        mock_fp_mgr_instance.generate_fingerprint.return_value = mock_fp
        
        session = AntiDetectionSession(
            "session-1",
            mock_camofox_instance,
            mock_fp_mgr_instance
        )
        
        tab_id = session.start("https://example.com")
        
        assert tab_id == "tab-123"
        assert session.tab_id == "tab-123"
        assert session.fingerprint is not None
    
    @patch('oracle.core.camofox_anti_detection.CamofoxClient')
    @patch('oracle.core.camofox_anti_detection.FingerprintManager')
    def test_get_snapshot(self, mock_fp_mgr, mock_camofox):
        """Test getting snapshot."""
        mock_camofox_instance = Mock()
        mock_camofox_instance.create_tab.return_value = "tab-123"
        mock_camofox_instance.get_snapshot.return_value = {"elements": []}
        
        mock_fp_mgr_instance = Mock()
        mock_fp = Mock()
        mock_fp_mgr_instance.generate_fingerprint.return_value = mock_fp
        
        session = AntiDetectionSession(
            "session-1",
            mock_camofox_instance,
            mock_fp_mgr_instance
        )
        
        session.start("https://example.com")
        snapshot = session.get_snapshot()
        
        assert snapshot == {"elements": []}
    
    @patch('oracle.core.camofox_anti_detection.CamofoxClient')
    @patch('oracle.core.camofox_anti_detection.FingerprintManager')
    def test_close_session(self, mock_fp_mgr, mock_camofox):
        """Test closing session."""
        mock_camofox_instance = Mock()
        mock_camofox_instance.create_tab.return_value = "tab-123"
        
        mock_fp_mgr_instance = Mock()
        mock_fp = Mock()
        mock_fp_mgr_instance.generate_fingerprint.return_value = mock_fp
        
        session = AntiDetectionSession(
            "session-1",
            mock_camofox_instance,
            mock_fp_mgr_instance
        )
        
        session.start("https://example.com")
        session.close()
        
        mock_camofox_instance.close_tab.assert_called_once_with("tab-123")
    
    @patch('oracle.core.camofox_anti_detection.CamofoxClient')
    @patch('oracle.core.camofox_anti_detection.FingerprintManager')
    def test_get_duration(self, mock_fp_mgr, mock_camofox):
        """Test getting session duration."""
        mock_camofox_instance = Mock()
        mock_camofox_instance.create_tab.return_value = "tab-123"
        
        mock_fp_mgr_instance = Mock()
        mock_fp = Mock()
        mock_fp_mgr_instance.generate_fingerprint.return_value = mock_fp
        
        session = AntiDetectionSession(
            "session-1",
            mock_camofox_instance,
            mock_fp_mgr_instance
        )
        
        duration = session.get_duration()
        
        assert isinstance(duration, timedelta)
        assert duration.total_seconds() >= 0


class TestAntiDetectionPool:
    """Test anti-detection session pool."""
    
    @patch('oracle.core.camofox_anti_detection.CamofoxClient')
    def test_init(self, mock_camofox):
        """Test pool initialization."""
        pool = AntiDetectionPool(
            pool_size=5,
            proxy_list=["proxy1", "proxy2"]
        )
        
        assert pool.pool_size == 5
        assert pool.sessions == {}
        assert pool.proxy_rotator is not None
    
    @patch('oracle.core.camofox_anti_detection.CamofoxClient')
    def test_acquire_session(self, mock_camofox):
        """Test acquiring session."""
        pool = AntiDetectionPool(pool_size=5)
        
        session = pool.acquire_session("session-1")
        
        assert session is not None
        assert "session-1" in pool.sessions
    
    @patch('oracle.core.camofox_anti_detection.CamofoxClient')
    def test_acquire_same_session_twice(self, mock_camofox):
        """Test acquiring same session returns same instance."""
        pool = AntiDetectionPool(pool_size=5)
        
        session1 = pool.acquire_session("session-1")
        session2 = pool.acquire_session("session-1")
        
        assert session1 is session2
    
    @patch('oracle.core.camofox_anti_detection.CamofoxClient')
    def test_release_session(self, mock_camofox):
        """Test releasing session."""
        pool = AntiDetectionPool(pool_size=5)
        
        pool.acquire_session("session-1")
        assert "session-1" in pool.sessions
        
        pool.release_session("session-1")
        assert "session-1" not in pool.sessions
    
    @patch('oracle.core.camofox_anti_detection.CamofoxClient')
    def test_release_all(self, mock_camofox):
        """Test releasing all sessions."""
        pool = AntiDetectionPool(pool_size=5)
        
        pool.acquire_session("session-1")
        pool.acquire_session("session-2")
        pool.acquire_session("session-3")
        
        assert len(pool.sessions) == 3
        
        pool.release_all()
        
        assert len(pool.sessions) == 0
    
    @patch('oracle.core.camofox_anti_detection.CamofoxClient')
    def test_get_statistics(self, mock_camofox):
        """Test pool statistics."""
        pool = AntiDetectionPool(pool_size=5)
        
        pool.acquire_session("session-1")
        pool.acquire_session("session-2")
        
        stats = pool.get_statistics()
        
        assert stats["active_sessions"] == 2
        assert stats["pool_size"] == 5
        assert stats["capacity_usage"] == 2 / 5


class TestAntiDetectionIntegration:
    """Integration tests for anti-detection system."""
    
    @patch('oracle.core.camofox_anti_detection.CamofoxClient')
    def test_full_anti_detection_flow(self, mock_camofox):
        """Test complete anti-detection flow."""
        # Setup
        mock_camofox_instance = Mock()
        mock_camofox_instance.create_tab.return_value = "tab-123"
        mock_camofox_instance.get_snapshot.return_value = {
            "elements": [
                {"text": "Bitcoin", "ref": "e1"}
            ]
        }
        
        # Create pool
        pool = AntiDetectionPool(
            pool_size=5,
            proxy_list=["proxy1", "proxy2", "proxy3"]
        )
        
        # Acquire session
        session = pool.acquire_session("twitter-search-1")
        assert session is not None
        
        # Check statistics
        stats = pool.get_statistics()
        assert stats["active_sessions"] == 1
        assert stats["pool_size"] == 5
    
    def test_proxy_rotation_with_fingerprints(self):
        """Test proxy rotation coordinated with fingerprints."""
        proxies = ["proxy1", "proxy2", "proxy3"]
        rotator = ProxyRotator(proxies)
        
        # Simulate 10 requests
        for i in range(10):
            proxy = rotator.get_next_proxy()
            assert proxy in proxies
        
        # All should be used
        stats = rotator.get_statistics()
        for usage in stats["usage"].values():
            assert usage > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
