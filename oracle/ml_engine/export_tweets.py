"""
ORACLE Phase 4: Export Tweets from PostgreSQL
Exports scraped tweets to CSV for ML training
"""
import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# Database connection
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from core.models import TweetModel
    DB_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Database unavailable: {e}")
    DB_AVAILABLE = False

logger = logging.getLogger(__name__)


def get_db_session():
    """Create DB session from environment"""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/oracle"
    )
    
    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        return Session()
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        return None


def export_tweets_from_db(output_file: str = None) -> str:
    """
    Export tweets from PostgreSQL to CSV
    
    Args:
        output_file: Path for output CSV
    
    Returns:
        Path to exported CSV
    """
    if not DB_AVAILABLE:
        logger.warning("⚠️  Database module not available")
        return None
    
    base_dir = Path(__file__).parent.parent
    output_file = output_file or base_dir / "data" / "tweets_history.csv"
    
    session = get_db_session()
    if not session:
        logger.error("❌ Could not connect to database")
        return None
    
    try:
        # Query all tweets
        tweets = session.query(TweetModel).all()
        
        if not tweets:
            logger.warning("⚠️  No tweets found in database")
            return None
        
        # Write CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    'external_id', 'author', 'content', 'url', 'posted_at',
                    'source', 'likes', 'retweets', 'replies', 'keywords'
                ]
            )
            writer.writeheader()
            
            for tweet in tweets:
                writer.writerow({
                    'external_id': tweet.external_id,
                    'author': tweet.author,
                    'content': tweet.content[:500] if tweet.content else '',  # Truncate
                    'url': tweet.url,
                    'posted_at': tweet.posted_at.isoformat() if tweet.posted_at else '',
                    'source': tweet.source,
                    'likes': tweet.likes,
                    'retweets': tweet.retweets,
                    'replies': tweet.replies,
                    'keywords': ','.join(tweet.keywords) if tweet.keywords else ''
                })
        
        logger.info(f"✅ Exported {len(tweets)} tweets → {output_file}")
        return str(output_file)
    
    except Exception as e:
        logger.error(f"❌ Error exporting tweets: {e}")
        return None
    
    finally:
        session.close()


def export_tweets_by_author(author: str = None, output_file: str = None) -> str:
    """
    Export tweets for specific author(s)
    
    Args:
        author: Twitter handle (or None for all)
        output_file: Path for output CSV
    
    Returns:
        Path to exported CSV
    """
    if not DB_AVAILABLE:
        logger.warning("⚠️  Database module not available")
        return None
    
    base_dir = Path(__file__).parent.parent
    output_file = output_file or base_dir / "data" / f"tweets_{author}.csv"
    
    session = get_db_session()
    if not session:
        return None
    
    try:
        if author:
            tweets = session.query(TweetModel).filter(
                TweetModel.author.ilike(f"%{author}%")
            ).all()
        else:
            tweets = session.query(TweetModel).all()
        
        if not tweets:
            logger.warning(f"⚠️  No tweets found for author: {author}")
            return None
        
        # Write CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    'external_id', 'author', 'content', 'url', 'posted_at',
                    'source', 'likes', 'retweets', 'replies'
                ]
            )
            writer.writeheader()
            
            for tweet in tweets:
                writer.writerow({
                    'external_id': tweet.external_id,
                    'author': tweet.author,
                    'content': tweet.content[:500] if tweet.content else '',
                    'url': tweet.url,
                    'posted_at': tweet.posted_at.isoformat() if tweet.posted_at else '',
                    'source': tweet.source,
                    'likes': tweet.likes,
                    'retweets': tweet.retweets,
                    'replies': tweet.replies,
                })
        
        logger.info(f"✅ Exported {len(tweets)} tweets for {author} → {output_file}")
        return str(output_file)
    
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n📊 Tweet Export Script")
    print("=" * 60)
    
    if DB_AVAILABLE:
        tweets_path = export_tweets_from_db()
        if tweets_path:
            print(f"✅ Tweets exported to: {tweets_path}")
        else:
            print("❌ Export failed")
    else:
        print("⚠️  Database module not available - check PostgreSQL connection")
    
    print("=" * 60)
