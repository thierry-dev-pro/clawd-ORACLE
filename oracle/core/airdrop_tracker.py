"""
Airdrop Tracker Module - Scrape airdrops actifs de sources publiques
Limite: 2-3 checks/jour (coûts minimaux)
Sources: blockchain news, défi protocols, airdrops.io alternatives
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import httpx
from bs4 import BeautifulSoup
import feedparser
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class Airdrop:
    """Représentation d'un airdrop"""
    id: str
    project_name: str
    token_symbol: str
    description: str
    url: str
    status: str  # "active", "pending", "closed", "completed"
    estimated_value: Optional[float] = None
    requirements: List[str] = None
    ends_at: Optional[datetime] = None
    source: str = "web"
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.requirements is None:
            self.requirements = []
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()


class AirdropTracker:
    """Tracker pour airdrops actifs"""
    
    # Sources de données publiques
    AIRDROP_SOURCES = {
        # RSS feeds pour crypto projects
        "crypto_news": "https://feeds.coindesk.com/api/v1/rss/?category=all",
        "ethereum_announce": "https://feed.ethereum.org/",
        "blockchain_info": "https://www.coinbase.com/feed/rss",
    }
    
    # Keywords d'airdrops
    AIRDROP_KEYWORDS = [
        "airdrop", "token distribution", "free tokens", "claim",
        "eligible", "rewards", "incentive program", "grant",
        "testnet reward", "community reward", "early adopter"
    ]
    
    # Patterns de détection d'airdrops
    AIRDROP_PATTERNS = {
        "testnet_airdrop": {
            "keywords": ["testnet", "airdrop", "rewards"],
            "description": "Testnet airdrop rewards"
        },
        "community_program": {
            "keywords": ["community", "program", "reward", "eligible"],
            "description": "Community reward program"
        },
        "retroactive_airdrop": {
            "keywords": ["retroactive", "airdrop", "snapshot"],
            "description": "Retroactive airdrop based on snapshot"
        },
        "trading_rewards": {
            "keywords": ["trading", "rewards", "incentive"],
            "description": "Trading rewards campaign"
        },
        "staking_rewards": {
            "keywords": ["staking", "rewards", "yield"],
            "description": "Staking rewards program"
        }
    }
    
    def __init__(self, timeout: int = 10):
        """
        Initialize tracker
        
        Args:
            timeout: Timeout HTTP en secondes
        """
        self.timeout = timeout
        self.session = None
        self.last_check = {}
        logger.info("✅ AirdropTracker initialized")
    
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session"""
        if self.session is None:
            self.session = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
        return self.session
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def scrape_crypto_news_feeds(self) -> List[Airdrop]:
        """
        Scrape crypto news feeds pour airdrops
        
        Returns:
            List of airdrops found
        """
        airdrops = []
        
        for source_name, feed_url in self.AIRDROP_SOURCES.items():
            try:
                logger.info(f"📡 Scraping airdrop feed: {source_name}")
                
                feed = feedparser.parse(feed_url)
                
                if feed.bozo:
                    logger.warning(f"⚠️ Feed parsing warning for {source_name}")
                
                # Cherche articles mentionnant "airdrop"
                for entry in feed.entries[:10]:
                    try:
                        title = entry.get('title', '').lower()
                        summary = entry.get('summary', '').lower()
                        full_text = f"{title} {summary}"
                        
                        # Check for airdrop keywords
                        if not any(kw in full_text for kw in self.AIRDROP_KEYWORDS):
                            continue
                        
                        # Extract project name and token
                        project_name = self._extract_project_name(title)
                        token_symbol = self._extract_token_symbol(title)
                        
                        if not project_name:
                            continue
                        
                        # Detect airdrop pattern
                        pattern = self._detect_airdrop_pattern(full_text)
                        
                        airdrop = Airdrop(
                            id=f"{source_name}_{entry.get('id', '')}",
                            project_name=project_name,
                            token_symbol=token_symbol or "UNKNOWN",
                            description=entry.get('summary', ''),
                            url=entry.get('link', ''),
                            status="active",
                            source=source_name,
                            requirements=self._extract_requirements(entry.get('summary', '')),
                            ends_at=self._estimate_end_date(entry.get('published', ''))
                        )
                        
                        airdrops.append(airdrop)
                        logger.info(f"✅ Airdrop found: {project_name}")
                    
                    except Exception as e:
                        logger.warning(f"Error parsing entry: {e}")
                        continue
            
            except Exception as e:
                logger.error(f"❌ Error scraping feed {source_name}: {e}")
                continue
        
        logger.info(f"📊 Found {len(airdrops)} airdrops from feeds")
        return airdrops
    
    async def scrape_blockchain_explorers(self) -> List[Airdrop]:
        """
        Scrape blockchain announcements pour airdrops
        Checks: Ethereum, Polygon, Arbitrum, Optimism official channels
        
        Returns:
            List of airdrops
        """
        airdrops = []
        
        # Public blockchain exploration sources
        sources = {
            "ethereum": "https://ethereum.org/en/community/",
            "polygon": "https://polygon.technology/",
            "arbitrum": "https://arbitrum.io/",
        }
        
        try:
            session = await self._get_session()
            
            for chain_name, url in sources.items():
                try:
                    logger.info(f"🔗 Checking {chain_name} announcements")
                    
                    response = await session.get(url, follow_redirects=True)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find news/announcement sections
                    announcements = soup.find_all(['div', 'section'], class_=['news', 'announcement', 'update'])
                    
                    for announcement in announcements[:5]:
                        try:
                            text = announcement.get_text().lower()
                            
                            # Check for airdrop mentions
                            if not any(kw in text for kw in self.AIRDROP_KEYWORDS):
                                continue
                            
                            project_name = self._extract_project_name(text)
                            if not project_name:
                                continue
                            
                            airdrop = Airdrop(
                                id=f"{chain_name}_{len(airdrops)}",
                                project_name=project_name,
                                token_symbol=self._extract_token_symbol(text) or "UNKNOWN",
                                description=text[:300],
                                url=url,
                                status="active",
                                source=f"{chain_name}_explorer",
                                requirements=self._extract_requirements(text)
                            )
                            
                            airdrops.append(airdrop)
                            logger.info(f"✅ Found {project_name} on {chain_name}")
                        
                        except Exception as e:
                            logger.warning(f"Error parsing announcement: {e}")
                            continue
                
                except Exception as e:
                    logger.warning(f"Could not check {chain_name}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"❌ Error scraping blockchain explorers: {e}")
        
        logger.info(f"📊 Found {len(airdrops)} airdrops from explorers")
        return airdrops
    
    def _extract_project_name(self, text: str) -> Optional[str]:
        """
        Extract project name from text
        
        Args:
            text: Text to analyze
        
        Returns:
            Project name or None
        """
        # Common patterns
        patterns = [
            r'(\w+)\s+(?:airdrop|token|launch)',
            r'(?:on|of)\s+(\w+)',
            r'^(\w+)\s+',
        ]
        
        import re
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1)
                # Filter common words
                if name.lower() not in ['the', 'and', 'or', 'of', 'in', 'to']:
                    return name.capitalize()
        
        return None
    
    def _extract_token_symbol(self, text: str) -> Optional[str]:
        """
        Extract token symbol (usually uppercase 2-5 chars)
        
        Args:
            text: Text to analyze
        
        Returns:
            Token symbol or None
        """
        import re
        
        # Look for patterns like ETH, BTC, USDC
        symbols = re.findall(r'\b([A-Z]{2,5})\b', text)
        
        # Filter to likely token symbols
        common_symbols = {'ETH', 'BTC', 'USDC', 'USDT', 'DAI', 'WETH', 'LINK'}
        
        for symbol in symbols:
            if symbol in common_symbols or len(symbol) == 4:
                return symbol
        
        return symbols[0] if symbols else None
    
    def _detect_airdrop_pattern(self, text: str) -> str:
        """
        Detect which type of airdrop it is
        
        Args:
            text: Text to analyze
        
        Returns:
            Pattern name
        """
        text_lower = text.lower()
        
        for pattern_name, pattern_info in self.AIRDROP_PATTERNS.items():
            if all(kw in text_lower for kw in pattern_info['keywords']):
                return pattern_name
        
        return "unknown"
    
    def _extract_requirements(self, text: str) -> List[str]:
        """
        Extract eligibility requirements
        
        Args:
            text: Text to analyze
        
        Returns:
            List of requirements
        """
        requirements = []
        
        # Common requirements patterns
        requirement_patterns = [
            "hold",
            "stake",
            "participate",
            "kyc",
            "wallet",
            "verification",
            "snapshot",
            "eligible",
            "wallet age",
            "minimum balance"
        ]
        
        text_lower = text.lower()
        for req in requirement_patterns:
            if req in text_lower:
                requirements.append(req)
        
        return requirements
    
    def _estimate_end_date(self, date_str: str) -> Optional[datetime]:
        """
        Estimate airdrop end date
        
        Args:
            date_str: Publication date
        
        Returns:
            Estimated end date or None
        """
        try:
            # Parse publication date
            pub_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Assume airdrop lasts 30-60 days from publication
            end_date = pub_date + timedelta(days=45)
            
            return end_date
        except:
            return None
    
    async def check_all_sources(self) -> List[Airdrop]:
        """
        Check all sources pour airdrops
        Rate limit: 2-3 checks/jour
        
        Returns:
            List of active airdrops
        """
        try:
            airdrops = []
            
            # Scrape feeds
            feed_airdrops = await self.scrape_crypto_news_feeds()
            airdrops.extend(feed_airdrops)
            
            # Scrape blockchain explorers (less frequent)
            if self._can_scrape_explorers():
                explorer_airdrops = await self.scrape_blockchain_explorers()
                airdrops.extend(explorer_airdrops)
            
            # Déduplique
            unique_airdrops = {}
            for airdrop in airdrops:
                key = f"{airdrop.project_name}_{airdrop.token_symbol}"
                if key not in unique_airdrops:
                    unique_airdrops[key] = airdrop
            
            airdrops = list(unique_airdrops.values())
            
            logger.info(f"🎯 Total airdrops found: {len(airdrops)}")
            return airdrops
        
        except Exception as e:
            logger.error(f"❌ Error checking sources: {e}")
            return []
    
    def _can_scrape_explorers(self) -> bool:
        """
        Check rate limiting for explorer scraping
        Max 2-3 checks/jour
        
        Returns:
            True if can scrape
        """
        now = datetime.utcnow()
        last_check = self.last_check.get('explorers', datetime.utcnow() - timedelta(hours=12))
        
        can_check = (now - last_check).total_seconds() > 3600 * 8  # 8 hours between checks
        
        if can_check:
            self.last_check['explorers'] = now
        
        return can_check


class AirdropTrackerDB:
    """Database operations pour airdrops"""
    
    @staticmethod
    def save_airdrops(db: Session, airdrops: List[Airdrop]) -> int:
        """
        Save airdrops to database
        
        Args:
            db: Database session
            airdrops: Airdrops to save
        
        Returns:
            Number saved
        """
        from core.models import AirdropModel
        
        count = 0
        try:
            for airdrop in airdrops:
                # Check if exists
                existing = db.query(AirdropModel).filter(
                    AirdropModel.project_name == airdrop.project_name,
                    AirdropModel.token_symbol == airdrop.token_symbol
                ).first()
                
                if existing:
                    # Update
                    existing.status = airdrop.status
                    existing.description = airdrop.description
                    existing.requirements = airdrop.requirements
                    existing.ends_at = airdrop.ends_at
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new
                    db_airdrop = AirdropModel(
                        external_id=airdrop.id,
                        project_name=airdrop.project_name,
                        token_symbol=airdrop.token_symbol,
                        description=airdrop.description,
                        url=airdrop.url,
                        status=airdrop.status,
                        estimated_value=airdrop.estimated_value,
                        requirements=airdrop.requirements,
                        ends_at=airdrop.ends_at,
                        source=airdrop.source,
                        discovered_at=datetime.utcnow()
                    )
                    db.add(db_airdrop)
                
                count += 1
            
            db.commit()
            logger.info(f"✅ Saved {count} airdrops to database")
            return count
        
        except Exception as e:
            logger.error(f"❌ Error saving airdrops: {e}")
            db.rollback()
            return 0
    
    @staticmethod
    def get_active_airdrops(db: Session, limit: int = 20) -> List[Dict]:
        """
        Get active airdrops
        
        Args:
            db: Database session
            limit: Max results
        
        Returns:
            List of airdrops
        """
        from core.models import AirdropModel
        
        try:
            airdrops = db.query(AirdropModel).filter(
                AirdropModel.status == "active",
                AirdropModel.ends_at > datetime.utcnow()
            ).order_by(
                AirdropModel.discovered_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": a.id,
                    "project_name": a.project_name,
                    "token_symbol": a.token_symbol,
                    "description": a.description[:200],
                    "url": a.url,
                    "status": a.status,
                    "estimated_value": a.estimated_value,
                    "requirements": a.requirements,
                    "ends_at": a.ends_at.isoformat() if a.ends_at else None,
                    "source": a.source
                }
                for a in airdrops
            ]
        
        except Exception as e:
            logger.error(f"❌ Error fetching airdrops: {e}")
            return []
    
    @staticmethod
    def get_airdrops_for_user(
        db: Session,
        user_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get airdrops relevant to user
        
        Args:
            db: Database session
            user_id: User ID
            limit: Max results
        
        Returns:
            List of airdrops
        """
        from core.models import AirdropModel
        
        try:
            airdrops = db.query(AirdropModel).filter(
                AirdropModel.status == "active",
                AirdropModel.ends_at > datetime.utcnow()
            ).order_by(
                AirdropModel.estimated_value.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": a.id,
                    "project_name": a.project_name,
                    "token_symbol": a.token_symbol,
                    "description": a.description,
                    "url": a.url,
                    "estimated_value": a.estimated_value,
                    "requirements": a.requirements,
                    "ends_at": a.ends_at.isoformat() if a.ends_at else None
                }
                for a in airdrops
            ]
        
        except Exception as e:
            logger.error(f"❌ Error fetching user airdrops: {e}")
            return []
    
    @staticmethod
    def mark_claimed(db: Session, airdrop_id: int) -> bool:
        """
        Mark airdrop as claimed
        
        Args:
            db: Database session
            airdrop_id: Airdrop ID
        
        Returns:
            Success status
        """
        from core.models import AirdropModel
        
        try:
            airdrop = db.query(AirdropModel).get(airdrop_id)
            if airdrop:
                airdrop.status = "claimed"
                airdrop.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"✅ Marked airdrop {airdrop_id} as claimed")
                return True
            return False
        
        except Exception as e:
            logger.error(f"❌ Error marking airdrop: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def cleanup_expired(db: Session) -> int:
        """
        Mark expired airdrops as closed
        
        Args:
            db: Database session
        
        Returns:
            Number updated
        """
        from core.models import AirdropModel
        
        try:
            updated = db.query(AirdropModel).filter(
                AirdropModel.status == "active",
                AirdropModel.ends_at < datetime.utcnow()
            ).update({"status": "closed"})
            
            db.commit()
            logger.info(f"✅ Marked {updated} airdrops as closed")
            return updated
        
        except Exception as e:
            logger.error(f"❌ Error cleaning up: {e}")
            db.rollback()
            return 0


# Global instance
airdrop_tracker = AirdropTracker()
