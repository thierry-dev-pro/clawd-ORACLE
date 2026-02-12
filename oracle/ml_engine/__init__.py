"""
ORACLE Phase 4: ML Engine
Intelligence automation for crypto trading signals
"""

from .config import ML_CONFIG, DATA_FILES
from .influencer_scorer import InfluencerScorer, InfluencerScore

__version__ = "0.1.0"
__all__ = ["ML_CONFIG", "DATA_FILES", "InfluencerScorer", "InfluencerScore"]
