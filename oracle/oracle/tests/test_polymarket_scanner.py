"""
Tests for Polymarket arbitrage scanner integration.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from oracle.core.polymarket_scanner import (
    PolymarketScanner,
    Market,
    Arbitrage
)


class TestPolymarketScanner:
    """Test Polymarket scanner."""
    
    @patch('oracle.core.polymarket_scanner.CamofoxClient')
    @patch('oracle.core.polymarket_scanner.anthropic.Anthropic')
    def test_init(self, mock_claude, mock_camofox):
        """Test scanner initialization."""
        scanner = PolymarketScanner()
        
        assert scanner.camofox is not None
        assert scanner.claude_client is not None
        assert scanner.claude_model == "claude-sonnet-4-5-20250929"
    
    def test_extract_price(self):
        """Test price extraction from text."""
        scanner = PolymarketScanner()
        
        # Test various formats
        text1 = "TRUMP 2024: YES 65%, NO 35%"
        assert scanner._extract_price(text1, "yes") == 0.65
        assert scanner._extract_price(text1, "no") == 0.35
        
        text2 = "Bitcoin $100K: YES: 72%, NO: 28%"
        assert scanner._extract_price(text2, "yes") == 0.72
        assert scanner._extract_price(text2, "no") == 0.28
        
        # Test invalid text
        text3 = "Some random text"
        assert scanner._extract_price(text3, "yes") is None
    
    def test_parse_market_element(self):
        """Test market element parsing."""
        scanner = PolymarketScanner()
        
        elem = {
            "ref": "e1",
            "tag": "div",
            "text": "Bitcoin $100K: YES 70%, NO 30%",
            "className": "market"
        }
        
        market = scanner._parse_market_element(elem)
        
        assert market is not None
        assert market.id == "e1"
        assert market.title == "Bitcoin $100K"
        assert market.yes_price == 0.70
        assert market.no_price == 0.30
    
    def test_extract_markets_from_snapshot(self):
        """Test extracting markets from snapshot."""
        scanner = PolymarketScanner()
        
        snapshot = {
            "tabId": "tab-456",
            "elements": [
                {
                    "ref": "e1",
                    "tag": "div",
                    "text": "TRUMP 2024: YES 65%, NO 35%",
                    "className": "market"
                },
                {
                    "ref": "e2",
                    "tag": "div",
                    "text": "Bitcoin $100K: YES 72%, NO 28%",
                    "className": "market-item"
                },
                {
                    "ref": "e3",
                    "tag": "div",
                    "text": "Short",
                    "className": "market"  # Too short, should be filtered
                }
            ]
        }
        
        markets = scanner._extract_markets_from_snapshot(snapshot)
        
        assert len(markets) == 2
        assert markets[0].title == "TRUMP 2024"
        assert markets[1].title == "Bitcoin $100K"
    
    def test_are_related_markets(self):
        """Test market relationship detection."""
        scanner = PolymarketScanner()
        
        m1 = Market(
            id="1",
            title="Bitcoin Price End of 2024",
            description="Will Bitcoin reach $100K?",
            yes_price=0.7,
            no_price=0.3,
            volume=10000,
            liquidity=5000,
            expires_at="2024-12-31"
        )
        
        m2 = Market(
            id="2",
            title="Bitcoin Price End of 2024",
            description="Bitcoin end of year price",
            yes_price=0.65,
            no_price=0.35,
            volume=8000,
            liquidity=4000,
            expires_at="2024-12-31"
        )
        
        m3 = Market(
            id="3",
            title="Ethereum ETH Price Rise",
            description="Will ETH rise?",
            yes_price=0.6,
            no_price=0.4,
            volume=5000,
            liquidity=2000,
            expires_at="2024-12-31"
        )
        
        # Same market (high overlap)
        assert scanner._are_related(m1, m2) is True
        
        # Different markets (low overlap)
        assert scanner._are_related(m1, m3) is False
    
    def test_check_pair_arbitrage(self):
        """Test arbitrage detection in market pair."""
        scanner = PolymarketScanner()
        
        m1 = Market(
            id="1",
            title="Bitcoin $100K",
            description="",
            yes_price=0.70,
            no_price=0.30,
            volume=10000,
            liquidity=5000,
            expires_at=""
        )
        
        m2 = Market(
            id="2",
            title="Bitcoin $100K",
            description="",
            yes_price=0.60,  # Lower YES price = arbitrage
            no_price=0.40,
            volume=8000,
            liquidity=4000,
            expires_at=""
        )
        
        arbs = scanner._check_pair_arbitrage(m1, m2, min_profit_pct=5.0)
        
        assert len(arbs) > 0
        assert arbs[0].profit_pct >= 5.0
    
    @patch('oracle.core.polymarket_scanner.CamofoxClient')
    @patch('oracle.core.polymarket_scanner.anthropic.Anthropic')
    def test_scan_markets(self, mock_claude, mock_camofox):
        """Test market scanning."""
        mock_camofox_instance = Mock()
        mock_camofox_instance.create_tab.return_value = "tab-456"
        mock_camofox_instance.get_snapshot.return_value = {
            "tabId": "tab-456",
            "elements": [
                {
                    "ref": "e1",
                    "text": "Market 1: YES 70%, NO 30%",
                    "className": "market"
                },
                {
                    "ref": "e2",
                    "text": "Market 2: YES 60%, NO 40%",
                    "className": "market"
                }
            ]
        }
        mock_camofox.return_value = mock_camofox_instance
        
        scanner = PolymarketScanner()
        markets = scanner.scan_markets(min_volume=0)
        
        assert len(markets) == 2
        mock_camofox_instance.close_tab.assert_called_once()
    
    def test_rank_opportunities(self):
        """Test opportunity ranking."""
        scanner = PolymarketScanner()
        
        opportunities = [
            Arbitrage(
                market_1=Market("1", "M1", "", 0.7, 0.3, 1000, 500, ""),
                market_2=Market("2", "M2", "", 0.6, 0.4, 1000, 500, ""),
                opportunity_type="yes_yes_arb",
                profit_pct=3.0,
                risk_pct=2.0,
                detected_at=datetime.now()
            ),
            Arbitrage(
                market_1=Market("3", "M3", "", 0.5, 0.5, 1000, 500, ""),
                market_2=Market("4", "M4", "", 0.2, 0.8, 1000, 500, ""),
                opportunity_type="yes_no_arb",
                profit_pct=10.0,
                risk_pct=5.0,
                detected_at=datetime.now()
            ),
            Arbitrage(
                market_1=Market("5", "M5", "", 0.6, 0.4, 1000, 500, ""),
                market_2=Market("6", "M6", "", 0.55, 0.45, 1000, 500, ""),
                opportunity_type="yes_yes_arb",
                profit_pct=5.0,
                risk_pct=3.0,
                detected_at=datetime.now()
            )
        ]
        
        ranked = scanner.rank_opportunities(opportunities, by="profit_pct")
        
        assert ranked[0].profit_pct == 10.0
        assert ranked[1].profit_pct == 5.0
        assert ranked[2].profit_pct == 3.0
    
    def test_get_top_opportunities(self):
        """Test getting top opportunities."""
        scanner = PolymarketScanner()
        
        opportunities = [
            Arbitrage(
                market_1=Market("1", "M1", "", 0.7, 0.3, 1000, 500, ""),
                market_2=Market("2", "M2", "", 0.6, 0.4, 1000, 500, ""),
                opportunity_type="yes_yes_arb",
                profit_pct=float(i),
                risk_pct=1.0,
                detected_at=datetime.now()
            )
            for i in range(20)
        ]
        
        top = scanner.get_top_opportunities(opportunities, top_n=5)
        
        assert len(top) == 5
        assert top[0].profit_pct >= top[1].profit_pct
    
    @patch('oracle.core.polymarket_scanner.CamofoxClient')
    @patch('oracle.core.polymarket_scanner.anthropic.Anthropic')
    def test_detect_arbitrage(self, mock_claude, mock_camofox):
        """Test arbitrage detection."""
        markets = [
            Market(
                id="1",
                title="Bitcoin Price Prediction",
                description="",
                yes_price=0.70,
                no_price=0.30,
                volume=10000,
                liquidity=5000,
                expires_at=""
            ),
            Market(
                id="2",
                title="Bitcoin Price Prediction",
                description="",
                yes_price=0.60,
                no_price=0.40,
                volume=8000,
                liquidity=4000,
                expires_at=""
            )
        ]
        
        scanner = PolymarketScanner()
        opportunities = scanner.detect_arbitrage(markets, min_profit_pct=5.0)
        
        # Should find arbitrage between these two
        assert len(opportunities) > 0


class TestPolymarketIntegration:
    """Integration tests for Polymarket scanner."""
    
    @patch('oracle.core.polymarket_scanner.CamofoxClient')
    @patch('oracle.core.polymarket_scanner.anthropic.Anthropic')
    def test_full_scanning_pipeline(self, mock_claude, mock_camofox):
        """Test complete scanning pipeline."""
        # Setup mocks
        mock_camofox_instance = Mock()
        mock_camofox_instance.create_tab.return_value = "tab-456"
        mock_camofox_instance.get_snapshot.return_value = {
            "tabId": "tab-456",
            "elements": [
                {
                    "ref": "e1",
                    "text": "Bitcoin $100K: YES 65%, NO 35%",
                    "className": "market"
                },
                {
                    "ref": "e2",
                    "text": "Bitcoin Price: YES 60%, NO 40%",
                    "className": "market"
                },
                {
                    "ref": "e3",
                    "text": "Ethereum Price: YES 70%, NO 30%",
                    "className": "market"
                }
            ]
        }
        mock_camofox.return_value = mock_camofox_instance
        
        scanner = PolymarketScanner()
        
        # Scan
        markets = scanner.scan_markets(min_volume=0)
        assert len(markets) == 3
        
        # Detect
        opportunities = scanner.detect_arbitrage(markets, min_profit_pct=3.0)
        assert len(opportunities) > 0
        
        # Rank
        top = scanner.get_top_opportunities(opportunities, top_n=3)
        assert len(top) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
