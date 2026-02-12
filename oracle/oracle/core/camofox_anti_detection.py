"""
Anti-Detection Layer for Camofox - Rotation + Proxy Management.
Automatically rotates fingerprints and proxies to avoid detection.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import random

from .camofox_client import CamofoxClient
from .fingerprint_manager import FingerprintManager, create_camofox_fingerprint_config

logger = logging.getLogger(__name__)


class ProxyRotator:
    """Manage proxy rotation for session diversity."""
    
    def __init__(self, proxy_list: Optional[List[str]] = None):
        """
        Initialize proxy rotator.
        
        Args:
            proxy_list: List of proxy URLs (format: http://host:port)
        """
        self.proxies = proxy_list or []
        self.current_index = 0
        self.usage_count: Dict[str, int] = {p: 0 for p in self.proxies}
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy in rotation."""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        self.usage_count[proxy] += 1
        
        logger.debug(f"Using proxy: {proxy}")
        
        return proxy
    
    def get_least_used_proxy(self) -> Optional[str]:
        """Get least used proxy."""
        if not self.proxies:
            return None
        
        proxy = min(self.proxies, key=lambda p: self.usage_count.get(p, 0))
        self.usage_count[proxy] = self.usage_count.get(proxy, 0) + 1
        
        return proxy
    
    def add_proxy(self, proxy: str) -> None:
        """Add proxy to rotation list."""
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            self.usage_count[proxy] = 0
            logger.info(f"Added proxy: {proxy}")
    
    def remove_proxy(self, proxy: str) -> None:
        """Remove proxy from rotation."""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            del self.usage_count[proxy]
            logger.info(f"Removed proxy: {proxy}")
    
    def get_statistics(self) -> Dict:
        """Get proxy usage statistics."""
        if not self.proxies:
            return {"total": 0, "usage": {}}
        
        return {
            "total": len(self.proxies),
            "usage": self.usage_count.copy(),
            "least_used": min(self.proxies, key=lambda p: self.usage_count.get(p, 0)),
            "most_used": max(self.proxies, key=lambda p: self.usage_count.get(p, 0))
        }


class AntiDetectionSession:
    """Session with anti-detection (fingerprint + proxy rotation)."""
    
    def __init__(
        self,
        session_key: str,
        camofox_client: CamofoxClient,
        fingerprint_manager: FingerprintManager,
        proxy_rotator: Optional[ProxyRotator] = None
    ):
        """
        Initialize anti-detection session.
        
        Args:
            session_key: Unique session identifier
            camofox_client: Camofox client instance
            fingerprint_manager: Fingerprint manager instance
            proxy_rotator: Optional proxy rotator
        """
        self.session_key = session_key
        self.camofox = camofox_client
        self.fingerprint_manager = fingerprint_manager
        self.proxy_rotator = proxy_rotator
        
        self.tab_id: Optional[str] = None
        self.fingerprint = None
        self.proxy = None
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
    
    def start(
        self,
        url: str,
        browser: str = "Chrome",
        os_type: str = "Win32",
        timezone: str = "America/New_York",
        rotate_proxy: bool = True
    ) -> str:
        """
        Start session with anti-detection setup.
        
        Args:
            url: URL to navigate to
            browser: Browser type
            os_type: OS type
            timezone: Timezone
            rotate_proxy: Whether to rotate proxy
            
        Returns:
            Tab ID
        """
        # Generate fingerprint
        self.fingerprint = self.fingerprint_manager.generate_fingerprint(
            self.session_key,
            browser=browser,
            os_type=os_type,
            timezone=timezone
        )
        
        # Get proxy if available
        if self.proxy_rotator and rotate_proxy:
            self.proxy = self.proxy_rotator.get_next_proxy()
        
        # Create tab with fingerprint
        fingerprint_config = create_camofox_fingerprint_config(self.fingerprint)
        
        try:
            self.tab_id = self.camofox.create_tab(
                user_id="oracle",
                session_key=self.session_key,
                url=url,
                proxy=self.proxy
            )
            
            logger.info(
                f"Started anti-detection session {self.session_key} "
                f"(browser={self.fingerprint.user_agent[:50]}..., "
                f"proxy={self.proxy or 'none'})"
            )
            
            return self.tab_id
            
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            raise
    
    def get_snapshot(self) -> Dict:
        """Get page snapshot."""
        if not self.tab_id:
            raise ValueError("Session not started")
        
        self.last_activity = datetime.now()
        return self.camofox.get_snapshot(self.tab_id, "oracle")
    
    def rotate_fingerprint(
        self,
        new_browser: Optional[str] = None,
        new_os: Optional[str] = None,
        rotate_proxy: bool = True
    ) -> None:
        """
        Rotate fingerprint and proxy mid-session.
        
        Args:
            new_browser: Optional new browser
            new_os: Optional new OS
            rotate_proxy: Whether to rotate proxy
        """
        if not self.tab_id:
            raise ValueError("Session not started")
        
        # Close current tab
        self.camofox.close_tab(self.tab_id)
        
        # Generate new fingerprint
        browser = new_browser or self._random_browser()
        os_type = new_os or self._random_os()
        timezone = random.choice([
            "America/New_York",
            "Europe/London",
            "Europe/Paris",
            "Asia/Tokyo"
        ])
        
        self.fingerprint = self.fingerprint_manager.generate_fingerprint(
            self.session_key,
            browser=browser,
            os_type=os_type,
            timezone=timezone
        )
        
        # Rotate proxy
        if self.proxy_rotator and rotate_proxy:
            self.proxy = self.proxy_rotator.get_next_proxy()
        
        logger.info(
            f"Rotated fingerprint for {self.session_key} "
            f"(new browser={browser})"
        )
    
    def close(self) -> None:
        """Close session and cleanup."""
        if self.tab_id:
            self.camofox.close_tab(self.tab_id)
        
        logger.info(f"Closed anti-detection session {self.session_key}")
    
    def get_duration(self) -> timedelta:
        """Get session duration."""
        return datetime.now() - self.created_at
    
    def _random_browser(self) -> str:
        """Get random browser."""
        return random.choice(["Chrome", "Firefox", "Safari"])
    
    def _random_os(self) -> str:
        """Get random OS."""
        return random.choice(["Win32", "MacIntel", "Linux x86_64"])


class AntiDetectionPool:
    """Pool of anti-detection sessions for concurrent scraping."""
    
    def __init__(
        self,
        pool_size: int = 10,
        camofox_url: str = "http://localhost:9377",
        proxy_list: Optional[List[str]] = None,
        rotation_interval_minutes: int = 30
    ):
        """
        Initialize anti-detection pool.
        
        Args:
            pool_size: Number of concurrent sessions
            camofox_url: Camofox service URL
            proxy_list: Optional list of proxies
            rotation_interval_minutes: Auto-rotate fingerprints every N minutes
        """
        self.pool_size = pool_size
        self.camofox = CamofoxClient(base_url=camofox_url)
        self.fingerprint_manager = FingerprintManager()
        self.proxy_rotator = ProxyRotator(proxy_list) if proxy_list else None
        self.rotation_interval = rotation_interval_minutes
        
        self.sessions: Dict[str, AntiDetectionSession] = {}
        self.last_rotation = datetime.now()
    
    def acquire_session(self, session_key: str) -> AntiDetectionSession:
        """
        Acquire or create a session.
        
        Args:
            session_key: Session identifier
            
        Returns:
            AntiDetectionSession
        """
        if session_key in self.sessions:
            # Check if rotation needed
            if self._should_rotate():
                self.sessions[session_key].rotate_fingerprint()
            
            return self.sessions[session_key]
        
        # Create new session
        session = AntiDetectionSession(
            session_key,
            self.camofox,
            self.fingerprint_manager,
            self.proxy_rotator
        )
        
        self.sessions[session_key] = session
        logger.info(f"Acquired session {session_key} (pool size: {len(self.sessions)})")
        
        return session
    
    def release_session(self, session_key: str) -> None:
        """Release and close session."""
        if session_key in self.sessions:
            self.sessions[session_key].close()
            del self.sessions[session_key]
            logger.info(f"Released session {session_key}")
    
    def release_all(self) -> None:
        """Release all sessions."""
        for session_key in list(self.sessions.keys()):
            self.release_session(session_key)
    
    def get_statistics(self) -> Dict:
        """Get pool statistics."""
        return {
            "active_sessions": len(self.sessions),
            "pool_size": self.pool_size,
            "capacity_usage": len(self.sessions) / self.pool_size,
            "fingerprints": self.fingerprint_manager.get_statistics(),
            "proxies": self.proxy_rotator.get_statistics() if self.proxy_rotator else None,
            "sessions": {
                key: {
                    "duration_seconds": session.get_duration().total_seconds(),
                    "last_activity": session.last_activity.isoformat(),
                    "fingerprint": session.fingerprint.canvas_fingerprint if session.fingerprint else None,
                    "proxy": session.proxy
                }
                for key, session in self.sessions.items()
            }
        }
    
    def _should_rotate(self) -> bool:
        """Check if fingerprints should be rotated."""
        elapsed = datetime.now() - self.last_rotation
        return elapsed.total_seconds() > (self.rotation_interval * 60)


# Example usage
def demo_anti_detection():
    """Demo anti-detection system."""
    from oracle.core.camofox_client import CamofoxClient
    
    # Setup
    camofox = CamofoxClient()
    fingerprint_mgr = FingerprintManager()
    proxy_rotator = ProxyRotator([
        "http://proxy1.com:8080",
        "http://proxy2.com:8080",
        "http://proxy3.com:8080"
    ])
    
    # Create pool
    pool = AntiDetectionPool(
        pool_size=5,
        proxy_list=proxy_rotator.proxies,
        rotation_interval_minutes=30
    )
    
    # Use sessions
    session1 = pool.acquire_session("twitter-search-1")
    session1.start("https://twitter.com/search?q=bitcoin")
    snapshot = session1.get_snapshot()
    print(f"Snapshot size: {len(str(snapshot))} bytes")
    
    # Rotate fingerprint mid-session
    session1.rotate_fingerprint()
    
    # Stats
    stats = pool.get_statistics()
    print(f"Active sessions: {stats['active_sessions']}/{stats['pool_size']}")
    print(f"Fingerprints: {stats['fingerprints']['total']}")
    
    # Cleanup
    pool.release_all()
