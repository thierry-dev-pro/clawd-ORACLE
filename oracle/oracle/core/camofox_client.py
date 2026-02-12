"""
Camofox Browser Client for web scraping with fingerprint spoofing.
Provides REST API wrapper for undetectable web automation.
"""

import requests
import logging
from typing import Dict, Optional, List
from urllib.parse import urljoin
from functools import wraps
from time import sleep

logger = logging.getLogger(__name__)


class CamofoxError(Exception):
    """Camofox API error"""
    pass


class CamofoxClient:
    """REST client for Camofox browser automation."""
    
    def __init__(self, base_url: str = "http://localhost:9377", timeout: int = 30):
        """
        Initialize Camofox client.
        
        Args:
            base_url: Camofox service URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.tabs: Dict[str, str] = {}
        self._session = requests.Session()
    
    def _retry(max_retries: int = 3, backoff: float = 1.0):
        """Decorator for automatic retry on transient failures."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_error = None
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except (requests.ConnectionError, requests.Timeout) as e:
                        last_error = e
                        if attempt < max_retries - 1:
                            wait_time = backoff * (2 ** attempt)
                            logger.warning(
                                f"Attempt {attempt + 1}/{max_retries} failed, "
                                f"retrying in {wait_time}s: {e}"
                            )
                            sleep(wait_time)
                if last_error:
                    raise CamofoxError(f"Failed after {max_retries} retries: {last_error}")
            return wrapper
        return decorator
    
    def health_check(self) -> bool:
        """Check if Camofox service is running."""
        try:
            resp = self._session.get(
                urljoin(self.base_url, "/health"),
                timeout=5
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    @_retry(max_retries=3)
    def create_tab(
        self,
        user_id: str,
        session_key: str,
        url: str,
        proxy: Optional[str] = None
    ) -> str:
        """
        Create a new browser tab.
        
        Args:
            user_id: User identifier for isolation
            session_key: Session key for fingerprint tracking
            url: URL to navigate to
            proxy: Optional proxy URL
            
        Returns:
            Tab ID for subsequent operations
        """
        payload = {
            "userId": user_id,
            "sessionKey": session_key,
            "url": url
        }
        if proxy:
            payload["proxy"] = proxy
        
        resp = self._session.post(
            urljoin(self.base_url, "/tabs"),
            json=payload,
            timeout=self.timeout
        )
        
        if resp.status_code != 201 and resp.status_code != 200:
            raise CamofoxError(
                f"Failed to create tab: {resp.status_code} - {resp.text}"
            )
        
        data = resp.json()
        tab_id = data.get("tabId") or data.get("id")
        if not tab_id:
            raise CamofoxError(f"No tabId in response: {data}")
        
        self.tabs[session_key] = tab_id
        logger.info(f"Created tab {tab_id} for {session_key}")
        return tab_id
    
    @_retry(max_retries=3)
    def get_snapshot(self, tab_id: str, user_id: str) -> Dict:
        """
        Get accessibility tree snapshot (compact, ~5KB vs 500KB HTML).
        
        Args:
            tab_id: Tab identifier
            user_id: User identifier for access control
            
        Returns:
            Snapshot dict with elements, text content, etc.
        """
        resp = self._session.get(
            urljoin(self.base_url, f"/tabs/{tab_id}/snapshot"),
            params={"userId": user_id},
            timeout=self.timeout
        )
        
        if resp.status_code != 200:
            raise CamofoxError(
                f"Failed to get snapshot: {resp.status_code} - {resp.text}"
            )
        
        return resp.json()
    
    def click(self, tab_id: str, user_id: str, ref: str) -> Dict:
        """
        Click element by reference.
        
        Args:
            tab_id: Tab identifier
            user_id: User identifier
            ref: Element reference (e.g., "e1", "e2")
            
        Returns:
            Response dict
        """
        resp = self._session.post(
            urljoin(self.base_url, f"/tabs/{tab_id}/click"),
            json={
                "userId": user_id,
                "ref": ref
            },
            timeout=self.timeout
        )
        
        if resp.status_code != 200:
            raise CamofoxError(
                f"Failed to click: {resp.status_code} - {resp.text}"
            )
        
        return resp.json()
    
    def type_text(self, tab_id: str, user_id: str, ref: str, text: str) -> Dict:
        """
        Type text in input field.
        
        Args:
            tab_id: Tab identifier
            user_id: User identifier
            ref: Element reference
            text: Text to type
            
        Returns:
            Response dict
        """
        resp = self._session.post(
            urljoin(self.base_url, f"/tabs/{tab_id}/type"),
            json={
                "userId": user_id,
                "ref": ref,
                "text": text
            },
            timeout=self.timeout
        )
        
        if resp.status_code != 200:
            raise CamofoxError(
                f"Failed to type: {resp.status_code} - {resp.text}"
            )
        
        return resp.json()
    
    def press_key(self, tab_id: str, user_id: str, key: str) -> Dict:
        """
        Press a keyboard key.
        
        Args:
            tab_id: Tab identifier
            user_id: User identifier
            key: Key name (e.g., "Enter", "Escape")
            
        Returns:
            Response dict
        """
        resp = self._session.post(
            urljoin(self.base_url, f"/tabs/{tab_id}/press"),
            json={
                "userId": user_id,
                "key": key
            },
            timeout=self.timeout
        )
        
        if resp.status_code != 200:
            raise CamofoxError(
                f"Failed to press key: {resp.status_code} - {resp.text}"
            )
        
        return resp.json()
    
    def close_tab(self, tab_id: str) -> None:
        """
        Close tab and clean up resources.
        
        Args:
            tab_id: Tab identifier
        """
        try:
            resp = self._session.delete(
                urljoin(self.base_url, f"/tabs/{tab_id}"),
                timeout=self.timeout
            )
            if resp.status_code == 200:
                logger.info(f"Closed tab {tab_id}")
                # Remove from tracking
                for key, tid in list(self.tabs.items()):
                    if tid == tab_id:
                        del self.tabs[key]
                        break
            else:
                logger.warning(f"Failed to close tab {tab_id}: {resp.status_code}")
        except Exception as e:
            logger.error(f"Error closing tab {tab_id}: {e}")
    
    def close_all(self) -> None:
        """Close all open tabs."""
        for tab_id in list(self.tabs.values()):
            self.close_tab(tab_id)
    
    def get_tab_id(self, session_key: str) -> Optional[str]:
        """Get tab ID for a session key."""
        return self.tabs.get(session_key)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, *args):
        """Context manager exit - cleanup tabs."""
        self.close_all()


def measure_snapshot_size(snapshot: Dict) -> int:
    """
    Measure snapshot JSON size in bytes.
    
    Args:
        snapshot: Snapshot dict from Camofox
        
    Returns:
        Size in bytes
    """
    import json
    return len(json.dumps(snapshot).encode('utf-8'))
