"""
Polymarket Arbitrage Scanner using Camofox for undetectable scraping.
Identifies arbitrage opportunities across prediction markets.
"""

import logging
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from decimal import Decimal

import anthropic

from .camofox_client import CamofoxClient, CamofoxError

logger = logging.getLogger(__name__)


@dataclass
class Market:
    """Polymarket prediction market."""
    id: str
    title: str
    description: str
    yes_price: float  # Probability 0.0-1.0
    no_price: float
    volume: float
    liquidity: float
    expires_at: str


@dataclass
class Arbitrage:
    """Arbitrage opportunity."""
    market_1: Market
    market_2: Market
    opportunity_type: str  # "yes_yes_arb", "no_no_arb", etc
    profit_pct: float
    risk_pct: float
    detected_at: datetime


class PolymarketScanner:
    """Scan Polymarket for arbitrage opportunities."""
    
    def __init__(
        self,
        camofox_url: str = "http://localhost:9377",
        claude_model: str = "claude-sonnet-4-5-20250929"
    ):
        """
        Initialize Polymarket scanner.
        
        Args:
            camofox_url: Camofox service URL
            claude_model: Claude model for analysis
        """
        self.camofox = CamofoxClient(base_url=camofox_url)
        self.claude_client = anthropic.Anthropic()
        self.claude_model = claude_model
    
    def scan_markets(
        self,
        category: Optional[str] = None,
        min_volume: float = 1000.0,
        proxy: Optional[str] = None
    ) -> List[Market]:
        """
        Scan Polymarket for active markets.
        
        Args:
            category: Optional category filter (e.g., "crypto", "politics")
            min_volume: Minimum trading volume
            proxy: Optional proxy URL
            
        Returns:
            List of Market objects
        """
        logger.info(f"Scanning Polymarket markets (category={category})")
        
        url = "https://polymarket.com"
        if category:
            url += f"?category={category}"
        
        try:
            tab_id = self.camofox.create_tab(
                user_id="oracle",
                session_key=f"polymarket-scan-{category or 'all'}",
                url=url,
                proxy=proxy
            )
            
            # Get snapshot
            snapshot = self.camofox.get_snapshot(tab_id, "oracle")
            
            # Extract market data
            markets = self._extract_markets_from_snapshot(snapshot)
            
            # Filter by volume
            markets = [m for m in markets if m.volume >= min_volume]
            
            logger.info(f"Found {len(markets)} markets")
            
            return markets
            
        finally:
            self.camofox.close_tab(tab_id)
    
    def detect_arbitrage(
        self,
        markets: List[Market],
        min_profit_pct: float = 5.0
    ) -> List[Arbitrage]:
        """
        Detect arbitrage opportunities between markets.
        
        Args:
            markets: List of Market objects
            min_profit_pct: Minimum profit percentage to flag
            
        Returns:
            List of Arbitrage opportunities
        """
        opportunities = []
        
        # Compare all pairs
        for i, market_1 in enumerate(markets):
            for market_2 in markets[i+1:]:
                # Check for related markets (same underlying event)
                if self._are_related(market_1, market_2):
                    arbs = self._check_pair_arbitrage(
                        market_1,
                        market_2,
                        min_profit_pct
                    )
                    opportunities.extend(arbs)
        
        logger.info(f"Detected {len(opportunities)} arbitrage opportunities")
        return opportunities
    
    def _extract_markets_from_snapshot(self, snapshot: Dict) -> List[Market]:
        """
        Extract market data from snapshot.
        
        Args:
            snapshot: Camofox snapshot
            
        Returns:
            List of Market objects
        """
        markets = []
        
        for elem in snapshot.get("elements", []):
            # Polymarket markets are typically in divs with market class
            if "market" in elem.get("className", "").lower():
                try:
                    market = self._parse_market_element(elem)
                    if market:
                        markets.append(market)
                except Exception as e:
                    logger.debug(f"Failed to parse market element: {e}")
        
        return markets
    
    def _parse_market_element(self, elem: Dict) -> Optional[Market]:
        """
        Parse a market element into Market object.
        
        Args:
            elem: Element dict from snapshot
            
        Returns:
            Market object or None
        """
        text = elem.get("text", "").strip()
        
        if not text or len(text) < 10:
            return None
        
        # Try to extract market info from text
        # Format varies, but typically includes title, yes/no prices
        parts = text.split(":")
        
        if len(parts) < 2:
            return None
        
        title = parts[0].strip()
        
        # Extract prices (e.g., "YES: 65%, NO: 35%")
        try:
            price_text = ":".join(parts[1:])
            
            yes_price = self._extract_price(price_text, "yes")
            no_price = self._extract_price(price_text, "no")
            
            if yes_price is not None and no_price is not None:
                return Market(
                    id=elem.get("ref", "unknown"),
                    title=title,
                    description=text,
                    yes_price=yes_price,
                    no_price=no_price,
                    volume=0.0,  # Would need more scraping
                    liquidity=0.0,
                    expires_at=""
                )
        except Exception as e:
            logger.debug(f"Failed to extract prices: {e}")
        
        return None
    
    def _extract_price(self, text: str, side: str) -> Optional[float]:
        """
        Extract price from market text.
        
        Args:
            text: Market text
            side: "yes" or "no"
            
        Returns:
            Price as float 0.0-1.0 or None
        """
        import re
        
        pattern = rf"{side.upper()}\s*[:=]?\s*(\d+(?:\.\d+)?)\s*%?"
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            price = float(match.group(1))
            return price / 100 if price > 1 else price
        
        return None
    
    def _are_related(self, market_1: Market, market_2: Market) -> bool:
        """
        Check if two markets are related (same event).
        
        Args:
            market_1: First market
            market_2: Second market
            
        Returns:
            True if related
        """
        # Simple heuristic: check for common keywords
        keywords_1 = set(market_1.title.lower().split())
        keywords_2 = set(market_2.title.lower().split())
        
        # If >30% overlap, likely related
        overlap = len(keywords_1 & keywords_2) / max(len(keywords_1), len(keywords_2))
        return overlap > 0.3
    
    def _check_pair_arbitrage(
        self,
        m1: Market,
        m2: Market,
        min_profit_pct: float
    ) -> List[Arbitrage]:
        """
        Check for arbitrage in a market pair.
        
        Args:
            m1: First market
            m2: Second market
            min_profit_pct: Minimum profit %
            
        Returns:
            List of Arbitrage opportunities
        """
        opportunities = []
        
        # Check if prices are inconsistent
        # If YES odds don't match across markets, arbitrage possible
        
        yes_diff = abs(m1.yes_price - m2.yes_price)
        no_diff = abs(m1.no_price - m2.no_price)
        
        profit_pct = max(yes_diff, no_diff) * 100
        
        if profit_pct >= min_profit_pct:
            opp = Arbitrage(
                market_1=m1,
                market_2=m2,
                opportunity_type="yes_yes_arb" if m1.yes_price > m2.yes_price else "yes_no_arb",
                profit_pct=profit_pct,
                risk_pct=5.0,  # Placeholder
                detected_at=datetime.now()
            )
            opportunities.append(opp)
        
        return opportunities
    
    def rank_opportunities(
        self,
        opportunities: List[Arbitrage],
        by: str = "profit_pct"
    ) -> List[Arbitrage]:
        """
        Rank arbitrage opportunities.
        
        Args:
            opportunities: List of Arbitrage
            by: Sort key ("profit_pct", "risk_pct", etc)
            
        Returns:
            Sorted list
        """
        return sorted(
            opportunities,
            key=lambda o: getattr(o, by),
            reverse=True
        )
    
    def get_top_opportunities(
        self,
        opportunities: List[Arbitrage],
        top_n: int = 10
    ) -> List[Arbitrage]:
        """
        Get top N opportunities by profit.
        
        Args:
            opportunities: List of Arbitrage
            top_n: Number to return
            
        Returns:
            Top N opportunities
        """
        ranked = self.rank_opportunities(opportunities)
        return ranked[:top_n]


# Example usage
def demo_arbitrage_scanning():
    """Demo arbitrage scanning."""
    scanner = PolymarketScanner()
    
    # Scan crypto markets
    markets = scanner.scan_markets(category="crypto", min_volume=1000)
    print(f"Found {len(markets)} markets")
    
    # Detect arbitrage
    opportunities = scanner.detect_arbitrage(markets, min_profit_pct=5.0)
    
    # Get top opportunities
    top = scanner.get_top_opportunities(opportunities, top_n=5)
    
    for opp in top:
        print(
            f"Arbitrage: {opp.market_1.title} vs {opp.market_2.title} "
            f"({opp.profit_pct:.1f}% profit)"
        )
    
    return opportunities
