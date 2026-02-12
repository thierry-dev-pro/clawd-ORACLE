"""
Tests for Camofox integration with Oracle.
Validates snapshot parsing, cost reduction, and API correctness.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from oracle.core.camofox_client import (
    CamofoxClient,
    CamofoxError,
    measure_snapshot_size
)


# Mock snapshots for testing
MOCK_TWITTER_SNAPSHOT = {
    "tabId": "tab-123",
    "url": "https://twitter.com/search?q=bitcoin",
    "elements": [
        {
            "ref": "e1",
            "tag": "article",
            "text": "Bitcoin price up 5% today",
            "className": "tweet"
        },
        {
            "ref": "e2",
            "tag": "article",
            "text": "Ethereum breaking new highs",
            "className": "tweet"
        },
    ],
    "title": "Twitter Search"
}

MOCK_POLYMARKET_SNAPSHOT = {
    "tabId": "tab-456",
    "url": "https://polymarket.com",
    "elements": [
        {
            "ref": "e1",
            "tag": "div",
            "text": "TRUMP 2024: 65%",
            "className": "market"
        },
        {
            "ref": "e2",
            "tag": "div",
            "text": "CRYPTO BULL: 72%",
            "className": "market"
        }
    ],
    "title": "Polymarket"
}


class TestCamofoxClient:
    """Test CamofoxClient initialization and basic operations."""
    
    def test_init(self):
        """Test client initialization."""
        client = CamofoxClient(base_url="http://localhost:9377")
        assert client.base_url == "http://localhost:9377"
        assert client.timeout == 30
        assert len(client.tabs) == 0
    
    def test_init_custom_timeout(self):
        """Test client with custom timeout."""
        client = CamofoxClient(timeout=60)
        assert client.timeout == 60
    
    @patch('requests.Session.get')
    def test_health_check_success(self, mock_get):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = CamofoxClient()
        assert client.health_check() is True
    
    @patch('requests.Session.get')
    def test_health_check_failure(self, mock_get):
        """Test failed health check."""
        mock_get.side_effect = Exception("Connection failed")
        
        client = CamofoxClient()
        assert client.health_check() is False


class TestTabOperations:
    """Test tab creation and management."""
    
    @patch('requests.Session.post')
    def test_create_tab(self, mock_post):
        """Test tab creation."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"tabId": "tab-123"}
        mock_post.return_value = mock_response
        
        client = CamofoxClient()
        tab_id = client.create_tab(
            user_id="oracle",
            session_key="test-session",
            url="https://twitter.com"
        )
        
        assert tab_id == "tab-123"
        assert client.tabs["test-session"] == "tab-123"
        mock_post.assert_called_once()
    
    @patch('requests.Session.post')
    def test_create_tab_with_proxy(self, mock_post):
        """Test tab creation with proxy."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"tabId": "tab-456"}
        mock_post.return_value = mock_response
        
        client = CamofoxClient()
        tab_id = client.create_tab(
            user_id="oracle",
            session_key="test-session",
            url="https://twitter.com",
            proxy="http://proxy:8080"
        )
        
        assert tab_id == "tab-456"
        # Verify proxy was passed in request
        call_args = mock_post.call_args
        assert call_args[1]['json']['proxy'] == "http://proxy:8080"
    
    @patch('requests.Session.post')
    def test_create_tab_error(self, mock_post):
        """Test tab creation error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        client = CamofoxClient()
        with pytest.raises(CamofoxError):
            client.create_tab(
                user_id="oracle",
                session_key="test-session",
                url="https://twitter.com"
            )
    
    @patch('requests.Session.delete')
    def test_close_tab(self, mock_delete):
        """Test tab closing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response
        
        client = CamofoxClient()
        client.tabs["test-session"] = "tab-123"
        
        client.close_tab("tab-123")
        
        assert "test-session" not in client.tabs
        mock_delete.assert_called_once()


class TestSnapshotOperations:
    """Test snapshot retrieval and parsing."""
    
    @patch('requests.Session.get')
    def test_get_snapshot(self, mock_get):
        """Test snapshot retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_TWITTER_SNAPSHOT
        mock_get.return_value = mock_response
        
        client = CamofoxClient()
        snapshot = client.get_snapshot(tab_id="tab-123", user_id="oracle")
        
        assert snapshot["tabId"] == "tab-123"
        assert len(snapshot["elements"]) == 2
        assert "Bitcoin" in snapshot["elements"][0]["text"]
    
    @patch('requests.Session.get')
    def test_get_snapshot_error(self, mock_get):
        """Test snapshot error handling."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Tab not found"
        mock_get.return_value = mock_response
        
        client = CamofoxClient()
        with pytest.raises(CamofoxError):
            client.get_snapshot(tab_id="invalid", user_id="oracle")


class TestInputOperations:
    """Test user input operations (click, type)."""
    
    @patch('requests.Session.post')
    def test_click(self, mock_post):
        """Test element click."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response
        
        client = CamofoxClient()
        result = client.click(tab_id="tab-123", user_id="oracle", ref="e1")
        
        assert result["success"] is True
        mock_post.assert_called_once()
    
    @patch('requests.Session.post')
    def test_type_text(self, mock_post):
        """Test text input."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response
        
        client = CamofoxClient()
        result = client.type_text(
            tab_id="tab-123",
            user_id="oracle",
            ref="e1",
            text="bitcoin price"
        )
        
        assert result["success"] is True
    
    @patch('requests.Session.post')
    def test_press_key(self, mock_post):
        """Test key press."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response
        
        client = CamofoxClient()
        result = client.press_key(tab_id="tab-123", user_id="oracle", key="Enter")
        
        assert result["success"] is True


class TestSnapshotSizeReduction:
    """Test cost optimization via snapshot size reduction."""
    
    def test_measure_snapshot_size(self):
        """Test snapshot size measurement."""
        size = measure_snapshot_size(MOCK_TWITTER_SNAPSHOT)
        
        # Should be ~500 bytes (not 500KB)
        assert size < 1000
        assert size > 100
    
    def test_snapshot_size_vs_html(self):
        """Test that snapshots are much smaller than HTML."""
        # Simulate HTML content (500KB estimate)
        html_content = "<html>" + "a" * 500000 + "</html>"
        html_size = len(html_content.encode('utf-8'))
        
        snapshot_size = measure_snapshot_size(MOCK_TWITTER_SNAPSHOT)
        
        # Snapshot should be 100x+ smaller
        assert snapshot_size < html_size / 100
        assert snapshot_size < 10000  # < 10KB


class TestContextManager:
    """Test context manager usage."""
    
    @patch('requests.Session.delete')
    def test_context_manager(self, mock_delete):
        """Test automatic cleanup with context manager."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response
        
        with patch('requests.Session.post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {"tabId": "tab-123"}
            
            with CamofoxClient() as client:
                tab_id = client.create_tab(
                    user_id="oracle",
                    session_key="test",
                    url="https://example.com"
                )
                assert tab_id == "tab-123"
        
        # After exiting context, tabs should be closed
        mock_delete.assert_called_once()


class TestIntegrationScenarios:
    """Test realistic scraping scenarios."""
    
    @patch('requests.Session.post')
    @patch('requests.Session.get')
    def test_twitter_sentiment_flow(self, mock_get, mock_post):
        """Test complete Twitter sentiment scraping flow."""
        # Setup mocks
        create_response = Mock()
        create_response.status_code = 201
        create_response.json.return_value = {"tabId": "twitter-tab"}
        mock_post.return_value = create_response
        
        snapshot_response = Mock()
        snapshot_response.status_code = 200
        snapshot_response.json.return_value = MOCK_TWITTER_SNAPSHOT
        mock_get.return_value = snapshot_response
        
        # Execute flow
        client = CamofoxClient()
        tab_id = client.create_tab(
            user_id="oracle",
            session_key="twitter-btc",
            url="https://twitter.com/search?q=bitcoin"
        )
        
        snapshot = client.get_snapshot(tab_id, "oracle")
        
        # Validate
        assert tab_id == "twitter-tab"
        assert len(snapshot["elements"]) > 0
        assert "Bitcoin" in str(snapshot)
    
    @patch('requests.Session.post')
    @patch('requests.Session.get')
    def test_polymarket_scraping_flow(self, mock_get, mock_post):
        """Test complete Polymarket scraping flow."""
        # Setup mocks
        create_response = Mock()
        create_response.status_code = 201
        create_response.json.return_value = {"tabId": "poly-tab"}
        mock_post.return_value = create_response
        
        snapshot_response = Mock()
        snapshot_response.status_code = 200
        snapshot_response.json.return_value = MOCK_POLYMARKET_SNAPSHOT
        mock_get.return_value = snapshot_response
        
        # Execute flow
        client = CamofoxClient()
        tab_id = client.create_tab(
            user_id="oracle",
            session_key="polymarket",
            url="https://polymarket.com"
        )
        
        snapshot = client.get_snapshot(tab_id, "oracle")
        
        # Extract market data
        markets = {
            elem["text"].split(":")[0]: elem["text"].split(":")[1].strip()
            for elem in snapshot["elements"]
            if ":" in elem["text"]
        }
        
        # Validate
        assert "TRUMP 2024" in markets
        assert "65%" in markets["TRUMP 2024"]


class TestErrorHandling:
    """Test error handling and recovery."""
    
    @patch('requests.Session.post')
    @patch('time.sleep')
    def test_retry_on_connection_error(self, mock_sleep, mock_post):
        """Test retry logic on connection failures."""
        # Fail twice, then succeed
        mock_post.side_effect = [
            requests.ConnectionError("Connection failed"),
            requests.ConnectionError("Connection failed"),
            Mock(status_code=201, json=lambda: {"tabId": "tab-123"})
        ]
        
        client = CamofoxClient()
        tab_id = client.create_tab(
            user_id="oracle",
            session_key="test",
            url="https://example.com"
        )
        
        assert tab_id == "tab-123"
        assert mock_post.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
