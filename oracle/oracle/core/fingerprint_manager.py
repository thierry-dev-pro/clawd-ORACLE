"""
Fingerprint Manager for Camofox - Undetectable browser fingerprinting.
Generates unique browser fingerprints per session to avoid bot detection.
"""

import logging
import random
import json
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class OSType(str, Enum):
    """Operating system types."""
    WINDOWS = "Win32"
    MACOS = "MacIntel"
    LINUX = "Linux x86_64"
    IPHONE = "iPhone"
    ANDROID = "Android"


class BrowserType(str, Enum):
    """Browser types."""
    CHROME = "Chrome"
    FIREFOX = "Firefox"
    SAFARI = "Safari"
    EDGE = "Edge"


class TimezoneType(str, Enum):
    """Common timezones."""
    EST = "America/New_York"
    CST = "America/Chicago"
    MST = "America/Denver"
    PST = "America/Los_Angeles"
    GMT = "Europe/London"
    CET = "Europe/Paris"
    AEST = "Australia/Sydney"
    JST = "Asia/Tokyo"
    IST = "Asia/Kolkata"


@dataclass
class BrowserFingerprint:
    """Browser fingerprint for anti-detection."""
    
    # Hardware
    hardware_concurrency: int  # CPU cores: 2-16
    device_memory: int  # RAM in GB: 2-16
    max_touch_points: int  # 0 (desktop) or 10 (mobile)
    
    # Platform
    platform: str  # OS type
    platform_version: str  # OS version
    
    # Browser
    user_agent: str  # Full user agent string
    browser_vendor: str  # "Google Inc." or "Apple Inc."
    
    # Screen
    screen_width: int  # 800-2560
    screen_height: int  # 600-1440
    screen_color_depth: int  # 24 or 32
    
    # Timezone
    timezone: str  # Timezone string
    timezone_offset: int  # Minutes offset from UTC
    
    # Language
    language: str  # "en-US", "fr-FR", etc
    languages: List[str]  # List of accepted languages
    
    # WebGL
    webgl_vendor: str  # "Google Inc.", "Apple Inc.", "NVIDIA"
    webgl_renderer: str  # "ANGLE", "Metal", etc
    
    # Canvas
    canvas_fingerprint: str  # Unique canvas hash
    
    # Features
    do_not_track: Optional[bool]  # None, True, or False
    plugins: List[str]  # List of plugins
    
    # Timestamps
    created_at: datetime
    last_used: datetime
    use_count: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_used'] = self.last_used.isoformat()
        return data


class FingerprintManager:
    """Generate and manage browser fingerprints."""
    
    # User agents by browser and OS
    USER_AGENTS = {
        ("Chrome", "Win32"): [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        ],
        ("Chrome", "MacIntel"): [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        ],
        ("Firefox", "Win32"): [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        ],
        ("Firefox", "MacIntel"): [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        ],
        ("Safari", "MacIntel"): [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        ],
    }
    
    # WebGL info
    WEBGL_INFO = [
        ("Google Inc.", "ANGLE (Intel HD Graphics 630)"),
        ("Apple Inc.", "Apple M1"),
        ("Intel", "Intel Iris Graphics"),
        ("NVIDIA", "NVIDIA GeForce GTX 1080"),
        ("AMD", "AMD Radeon RX 5700"),
    ]
    
    def __init__(self):
        """Initialize fingerprint manager."""
        self.fingerprints: Dict[str, BrowserFingerprint] = {}
        self.session_to_fingerprint: Dict[str, str] = {}
    
    def generate_fingerprint(
        self,
        session_key: str,
        browser: str = "Chrome",
        os_type: str = "Win32",
        timezone: str = "America/New_York"
    ) -> BrowserFingerprint:
        """
        Generate a new browser fingerprint.
        
        Args:
            session_key: Unique session identifier
            browser: Browser type (Chrome, Firefox, Safari)
            os_type: Operating system
            timezone: Timezone for fingerprint
            
        Returns:
            BrowserFingerprint object
        """
        logger.info(f"Generating fingerprint for session {session_key}")
        
        now = datetime.now()
        
        # Get user agent
        user_agent = self._get_user_agent(browser, os_type)
        
        # Generate fingerprint
        fingerprint = BrowserFingerprint(
            # Hardware
            hardware_concurrency=random.randint(4, 16),
            device_memory=random.choice([4, 8, 16, 32]),
            max_touch_points=0,  # Desktop
            
            # Platform
            platform=os_type,
            platform_version=self._get_platform_version(os_type),
            
            # Browser
            user_agent=user_agent,
            browser_vendor=self._get_browser_vendor(browser),
            
            # Screen
            screen_width=random.choice([1920, 2560, 1440, 1366, 1280]),
            screen_height=random.choice([1080, 1440, 900, 768, 720]),
            screen_color_depth=random.choice([24, 32]),
            
            # Timezone
            timezone=timezone,
            timezone_offset=self._get_timezone_offset(timezone),
            
            # Language
            language=self._get_language_from_timezone(timezone),
            languages=self._get_language_list(timezone),
            
            # WebGL
            webgl_vendor=self._get_webgl_vendor(),
            webgl_renderer=self._get_webgl_renderer(),
            
            # Canvas
            canvas_fingerprint=self._generate_canvas_hash(
                os_type, browser, timezone
            ),
            
            # Features
            do_not_track=random.choice([None, True, False]),
            plugins=self._get_plugins(browser),
            
            # Timestamps
            created_at=now,
            last_used=now
        )
        
        # Store
        self.fingerprints[session_key] = fingerprint
        self.session_to_fingerprint[session_key] = session_key
        
        logger.debug(f"Generated fingerprint: {fingerprint.canvas_fingerprint}")
        
        return fingerprint
    
    def get_fingerprint(self, session_key: str) -> Optional[BrowserFingerprint]:
        """
        Get fingerprint for session (or create new).
        
        Args:
            session_key: Session identifier
            
        Returns:
            BrowserFingerprint or None
        """
        if session_key in self.fingerprints:
            fp = self.fingerprints[session_key]
            fp.last_used = datetime.now()
            fp.use_count += 1
            return fp
        
        return None
    
    def rotate_fingerprints(
        self,
        session_keys: List[str],
        new_browser: Optional[str] = None,
        new_os: Optional[str] = None
    ) -> Dict[str, BrowserFingerprint]:
        """
        Rotate fingerprints for multiple sessions.
        
        Args:
            session_keys: List of session keys
            new_browser: Optional new browser type
            new_os: Optional new OS type
            
        Returns:
            Dict mapping session_key to new fingerprint
        """
        results = {}
        
        for session_key in session_keys:
            browser = new_browser or self._random_browser()
            os_type = new_os or self._random_os()
            timezone = random.choice(list(TimezoneType))
            
            fp = self.generate_fingerprint(
                session_key,
                browser=browser,
                os_type=os_type,
                timezone=timezone
            )
            results[session_key] = fp
        
        logger.info(f"Rotated fingerprints for {len(session_keys)} sessions")
        
        return results
    
    def cleanup_old_fingerprints(self, days_old: int = 7) -> int:
        """
        Remove old fingerprints not used in N days.
        
        Args:
            days_old: Delete fingerprints older than this
            
        Returns:
            Number of fingerprints deleted
        """
        from datetime import timedelta
        
        threshold = datetime.now() - timedelta(days=days_old)
        to_delete = [
            key for key, fp in self.fingerprints.items()
            if fp.last_used < threshold
        ]
        
        for key in to_delete:
            del self.fingerprints[key]
            if key in self.session_to_fingerprint:
                del self.session_to_fingerprint[key]
        
        logger.info(f"Cleaned up {len(to_delete)} old fingerprints")
        
        return len(to_delete)
    
    def get_statistics(self) -> Dict:
        """Get fingerprint statistics."""
        fingerprints = list(self.fingerprints.values())
        
        if not fingerprints:
            return {
                "total": 0,
                "avg_use_count": 0,
                "unique_browsers": 0,
                "unique_os": 0
            }
        
        browsers = set(fp.user_agent.split()[5] for fp in fingerprints)
        os_types = set(fp.platform for fp in fingerprints)
        use_counts = [fp.use_count for fp in fingerprints]
        
        return {
            "total": len(fingerprints),
            "avg_use_count": sum(use_counts) / len(use_counts),
            "unique_browsers": len(browsers),
            "unique_os": len(os_types),
            "browsers": list(browsers),
            "os_types": list(os_types)
        }
    
    # Helper methods
    
    def _get_user_agent(self, browser: str, os_type: str) -> str:
        """Get user agent string."""
        key = (browser, os_type)
        if key in self.USER_AGENTS:
            return random.choice(self.USER_AGENTS[key])
        return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    
    def _get_browser_vendor(self, browser: str) -> str:
        """Get browser vendor string."""
        vendors = {
            "Chrome": "Google Inc.",
            "Firefox": "Mozilla",
            "Safari": "Apple Inc.",
            "Edge": "Microsoft Inc."
        }
        return vendors.get(browser, "Google Inc.")
    
    def _get_platform_version(self, os_type: str) -> str:
        """Get platform version."""
        versions = {
            "Win32": f"10.0",
            "MacIntel": "10.15.7",
            "Linux x86_64": "5.10.0"
        }
        return versions.get(os_type, "10.0")
    
    def _get_timezone_offset(self, timezone: str) -> int:
        """Get timezone offset in minutes."""
        offsets = {
            "America/New_York": -300,
            "America/Chicago": -360,
            "America/Denver": -420,
            "America/Los_Angeles": -480,
            "Europe/London": 0,
            "Europe/Paris": 60,
            "Asia/Tokyo": 540,
            "Asia/Kolkata": 330,
            "Australia/Sydney": 600
        }
        return offsets.get(timezone, 0)
    
    def _get_language_from_timezone(self, timezone: str) -> str:
        """Get primary language from timezone."""
        languages = {
            "America/New_York": "en-US",
            "America/Chicago": "en-US",
            "America/Denver": "en-US",
            "America/Los_Angeles": "en-US",
            "Europe/London": "en-GB",
            "Europe/Paris": "fr-FR",
            "Asia/Tokyo": "ja-JP",
            "Asia/Kolkata": "hi-IN",
            "Australia/Sydney": "en-AU"
        }
        return languages.get(timezone, "en-US")
    
    def _get_language_list(self, timezone: str) -> List[str]:
        """Get list of accepted languages."""
        lang = self._get_language_from_timezone(timezone)
        en = "en-US" if "en" in lang else "en-GB"
        return [lang, en] if lang != en else [lang]
    
    def _get_webgl_vendor(self) -> str:
        """Get WebGL vendor."""
        return random.choice([item[0] for item in self.WEBGL_INFO])
    
    def _get_webgl_renderer(self) -> str:
        """Get WebGL renderer."""
        vendor = self._get_webgl_vendor()
        matching = [item[1] for item in self.WEBGL_INFO if item[0] == vendor]
        return random.choice(matching) if matching else "ANGLE"
    
    def _generate_canvas_hash(
        self,
        os_type: str,
        browser: str,
        timezone: str
    ) -> str:
        """Generate unique canvas fingerprint hash."""
        seed = f"{os_type}-{browser}-{timezone}-{random.random()}".encode()
        return hashlib.sha256(seed).hexdigest()[:16]
    
    def _get_plugins(self, browser: str) -> List[str]:
        """Get browser plugins."""
        if browser == "Chrome":
            return [
                "Chrome PDF Plugin",
                "Chrome PDF Viewer",
                "Native Client Executable"
            ]
        elif browser == "Firefox":
            return ["Shockwave Flash"]
        elif browser == "Safari":
            return ["Java Plug-in 2 for NPAPI"]
        return []
    
    def _random_browser(self) -> str:
        """Get random browser."""
        return random.choice(list(BrowserType)).__value__
    
    def _random_os(self) -> str:
        """Get random OS."""
        return random.choice(list(OSType)).__value__


# Utility function for Camofox integration
def create_camofox_fingerprint_config(fingerprint: BrowserFingerprint) -> Dict:
    """
    Create Camofox-compatible fingerprint configuration.
    
    Args:
        fingerprint: BrowserFingerprint object
        
    Returns:
        Dict compatible with Camofox API
    """
    return {
        "userAgent": fingerprint.user_agent,
        "hardwareConcurrency": fingerprint.hardware_concurrency,
        "deviceMemory": fingerprint.device_memory,
        "platform": fingerprint.platform,
        "timezone": fingerprint.timezone,
        "timezoneOffset": fingerprint.timezone_offset,
        "language": fingerprint.language,
        "languages": fingerprint.languages,
        "colorDepth": fingerprint.screen_color_depth,
        "screenWidth": fingerprint.screen_width,
        "screenHeight": fingerprint.screen_height,
        "webglVendor": fingerprint.webgl_vendor,
        "webglRenderer": fingerprint.webgl_renderer,
        "doNotTrack": fingerprint.do_not_track,
        "plugins": fingerprint.plugins,
    }


# Example usage
def demo_fingerprint_rotation():
    """Demo fingerprint generation and rotation."""
    manager = FingerprintManager()
    
    # Generate fingerprints for 5 sessions
    sessions = [f"session-{i}" for i in range(5)]
    for session in sessions:
        fp = manager.generate_fingerprint(session)
        print(f"{session}: {fp.user_agent[:60]}...")
    
    # Get statistics
    stats = manager.get_statistics()
    print(f"\nFingerprints: {stats['total']}")
    print(f"Unique browsers: {stats['unique_browsers']}")
    print(f"Unique OS: {stats['unique_os']}")
    
    # Rotate fingerprints
    manager.rotate_fingerprints(sessions)
    
    # Cleanup old ones
    manager.cleanup_old_fingerprints(days_old=7)
