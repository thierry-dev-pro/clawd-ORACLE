"""
ORACLE Phase 4: ML Config
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "ml_engine" / "models"

# Ensure directories exist
MODELS_DIR.mkdir(exist_ok=True)

# ML Config
ML_CONFIG = {
    "engagement_weights": {
        "likes": 0.4,
        "retweets": 0.35,
        "replies": 0.25,
    },
    "sentiment_threshold": 0.5,
    "min_tweets_for_score": 10,
    "score_range": (0, 100),
}

# Data files
DATA_FILES = {
    "influencers": DATA_DIR / "influencers_phase3.csv",
    "tweets": DATA_DIR / "tweets_history.csv",
    "model_engagement": MODELS_DIR / "engagement_scorer.pkl",
    "model_sentiment": MODELS_DIR / "sentiment_analyzer.pkl",
}

# API Keys (from env)
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if __name__ == "__main__":
    print("✅ ML Config loaded")
    print(f"Data dir: {DATA_DIR}")
    print(f"Models dir: {MODELS_DIR}")
