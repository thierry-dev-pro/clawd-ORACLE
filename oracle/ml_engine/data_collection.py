"""
ORACLE Phase 4: Data Collection for ML
Exports Notion + Twitter data to CSV for training
"""
import json
import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def export_influencers_data(input_file: str = None, output_file: str = None) -> str:
    """
    Export influencers from JSON to CSV
    
    Args:
        input_file: Path to twitter_handles_phase3.json
        output_file: Path for output CSV
    
    Returns:
        Path to exported CSV
    """
    base_dir = Path(__file__).parent.parent
    input_file = input_file or base_dir / "data" / "twitter_handles_phase3.json"
    output_file = output_file or base_dir / "data" / "influencers_phase3.csv"
    
    with open(input_file) as f:
        data = json.load(f)
    
    # Write CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data['handles'][0].keys())
        writer.writeheader()
        writer.writerows(data['handles'])
    
    count = len(data['handles'])
    logger.info(f"✅ Exported {count} influencers → {output_file}")
    return str(output_file)


def export_tweets_history(output_file: str = None) -> str:
    """
    Placeholder: Export tweets from DB to CSV
    TODO: Connect to Twitter scraper DB
    
    Expected format:
    id, author, content, posted_at, likes, retweets, replies
    """
    base_dir = Path(__file__).parent.parent
    output_file = output_file or base_dir / "data" / "tweets_history.csv"
    
    # For now, create empty template
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['id', 'author', 'content', 'posted_at', 'likes', 'retweets', 'replies']
        )
        writer.writeheader()
    
    logger.warning(f"⚠️  tweets_history.csv created (empty - awaiting scraper DB)")
    return str(output_file)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("📊 Data Collection")
    print("=" * 50)
    
    influencers_path = export_influencers_data()
    print(f"Influencers: {influencers_path}")
    
    tweets_path = export_tweets_history()
    print(f"Tweets: {tweets_path}")
    
    print("\n✅ Data export complete")
