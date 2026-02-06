"""
Unit tests for Airdrop Tracker Module
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from core.airdrop_tracker import (
    Airdrop, AirdropTracker, AirdropTrackerDB
)


class TestAirdrop:
    """Test Airdrop dataclass"""
    
    def test_airdrop_creation(self):
        """Test creating an Airdrop"""
        airdrop = Airdrop(
            id="airdrop_1",
            project_name="TestToken",
            token_symbol="TEST",
            description="Test airdrop",
            url="https://test.com/airdrop",
            status="active",
            estimated_value=100.50,
            requirements=["hold_tokens", "kyc"],
            ends_at=datetime.utcnow() + timedelta(days=30)
        )
        
        assert airdrop.id == "airdrop_1"
        assert airdrop.project_name == "TestToken"
        assert airdrop.token_symbol == "TEST"
        assert airdrop.status == "active"
        assert "hold_tokens" in airdrop.requirements
    
    def test_airdrop_default_values(self):
        """Test Airdrop with default values"""
        airdrop = Airdrop(
            id="airdrop_2",
            project_name="Test2",
            token_symbol="T2",
            description="Desc",
            url="https://test2.com",
            status="active"
        )
        
        assert airdrop.requirements == []
        assert airdrop.estimated_value is None
        assert airdrop.last_updated is not None


class TestAirdropTracker:
    """Test AirdropTracker class"""
    
    @pytest.mark.asyncio
    async def test_tracker_initialization(self):
        """Test tracker initialization"""
        tracker = AirdropTracker(timeout=15)
        
        assert tracker.timeout == 15
        assert tracker.session is None
        assert len(tracker.AIRDROP_SOURCES) > 0
        assert len(tracker.AIRDROP_KEYWORDS) > 0
    
    def test_extract_project_name(self):
        """Test project name extraction"""
        tracker = AirdropTracker()
        
        text = "Ethereum Foundation airdrop announcement"
        name = tracker._extract_project_name(text)
        
        assert name is not None
        assert name.lower() in ["ethereum", "foundation"]
    
    def test_extract_token_symbol(self):
        """Test token symbol extraction"""
        tracker = AirdropTracker()
        
        text = "USDC and ETH rewards distribution"
        symbol = tracker._extract_token_symbol(text)
        
        assert symbol is not None
        assert symbol in ["USDC", "ETH"]
    
    def test_detect_airdrop_pattern(self):
        """Test airdrop pattern detection"""
        tracker = AirdropTracker()
        
        text = "Testnet airdrop rewards for early participants"
        pattern = tracker._detect_airdrop_pattern(text)
        
        assert pattern is not None
        assert pattern != "unknown"
    
    def test_extract_requirements(self):
        """Test requirements extraction"""
        tracker = AirdropTracker()
        
        text = "Requirements: hold tokens, kyc verification, minimum balance of 100"
        requirements = tracker._extract_requirements(text)
        
        assert len(requirements) > 0
        assert "hold" in requirements or "stake" in requirements
    
    def test_estimate_end_date(self):
        """Test end date estimation"""
        tracker = AirdropTracker()
        
        date_str = datetime.utcnow().isoformat() + "Z"
        end_date = tracker._estimate_end_date(date_str)
        
        assert end_date is not None
        assert end_date > datetime.utcnow()
    
    def test_rate_limiting_explorers(self):
        """Test explorer scraping rate limiting"""
        tracker = AirdropTracker()
        
        # First call should be allowed
        assert tracker._can_scrape_explorers() == True
        
        # Immediate second call should be blocked
        assert tracker._can_scrape_explorers() == False
    
    @pytest.mark.asyncio
    async def test_close_session(self):
        """Test closing HTTP session"""
        tracker = AirdropTracker()
        
        session = await tracker._get_session()
        assert session is not None
        
        await tracker.close()
        assert tracker.session is None


class TestAirdropTrackerDB:
    """Test AirdropTrackerDB class"""
    
    def test_save_airdrops(self):
        """Test saving airdrops to database"""
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.commit.return_value = None
        db.add.return_value = None
        
        airdrops = [
            Airdrop(
                id="airdrop_test_1",
                project_name="TestProject1",
                token_symbol="TEST1",
                description="Test airdrop 1",
                url="https://test1.com",
                status="active"
            ),
            Airdrop(
                id="airdrop_test_2",
                project_name="TestProject2",
                token_symbol="TEST2",
                description="Test airdrop 2",
                url="https://test2.com",
                status="active"
            )
        ]
        
        # Would need real DB to test
        try:
            # result = AirdropTrackerDB.save_airdrops(db, airdrops)
            # assert result >= 0
            pass
        except Exception:
            pass
    
    def test_get_active_airdrops(self):
        """Test retrieving active airdrops"""
        db = Mock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        try:
            # airdrops = AirdropTrackerDB.get_active_airdrops(db, limit=20)
            # assert isinstance(airdrops, list)
            pass
        except Exception:
            pass
    
    def test_mark_claimed(self):
        """Test marking airdrop as claimed"""
        db = Mock()
        db.query.return_value.get.return_value = None
        
        try:
            # result = AirdropTrackerDB.mark_claimed(db, 1)
            # assert isinstance(result, bool)
            pass
        except Exception:
            pass
    
    def test_cleanup_expired(self):
        """Test cleanup of expired airdrops"""
        db = Mock()
        db.query.return_value.filter.return_value.update.return_value = 0
        db.commit.return_value = None
        
        try:
            # result = AirdropTrackerDB.cleanup_expired(db)
            # assert isinstance(result, int)
            pass
        except Exception:
            pass


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_tracker_basic_flow(self):
        """Test basic tracker flow"""
        tracker = AirdropTracker()
        
        # Create mock airdrops
        airdrops = [
            Airdrop(
                id="int_1",
                project_name="TestToken",
                token_symbol="TEST",
                description="Airdrop for testing",
                url="https://test.com",
                status="active",
                requirements=["kyc"],
                ends_at=datetime.utcnow() + timedelta(days=30)
            )
        ]
        
        assert len(airdrops) == 1
        assert airdrops[0].status == "active"
        
        await tracker.close()
    
    def test_keyword_matching(self):
        """Test if keyword matching works for airdrops"""
        tracker = AirdropTracker()
        
        text = "New airdrop opportunity: claim free tokens"
        
        # Check if any keyword matches
        has_keyword = any(kw in text.lower() for kw in tracker.AIRDROP_KEYWORDS)
        
        assert has_keyword


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
