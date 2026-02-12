"""
ORACLE Phase 4: ML Utils
Helper functions for data processing
"""
import csv
import json
import logging
from typing import List, Dict, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


def load_influencers(filepath: str) -> List[Dict]:
    """Load influencers from CSV"""
    influencers = []
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['followers'] = int(row.get('followers', 0))
            influencers.append(row)
    logger.info(f"✅ Loaded {len(influencers)} influencers")
    return influencers


def load_tweets(filepath: str) -> List[Dict]:
    """Load tweets from CSV"""
    tweets = []
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['likes'] = int(row.get('likes', 0))
            row['retweets'] = int(row.get('retweets', 0))
            row['replies'] = int(row.get('replies', 0))
            tweets.append(row)
    logger.info(f"✅ Loaded {len(tweets)} tweets")
    return tweets


def group_tweets_by_author(tweets: List[Dict]) -> Dict[str, List[Dict]]:
    """Group tweets by author (Twitter handle)"""
    grouped = {}
    for tweet in tweets:
        author = tweet.get('author', '').lower()
        if author:
            if author not in grouped:
                grouped[author] = []
            grouped[author].append(tweet)
    return grouped


def calculate_statistics(data: List[Dict], field: str) -> Tuple[float, float, float]:
    """Calculate mean, min, max for a field"""
    values = [float(d.get(field, 0)) for d in data if field in d]
    if not values:
        return 0.0, 0.0, 0.0
    return (
        sum(values) / len(values),  # mean
        min(values),                 # min
        max(values)                  # max
    )


def export_results(results: List[Dict], output_file: str) -> None:
    """Export ML results to CSV"""
    if not results:
        logger.warning("No results to export")
        return
    
    keys = results[0].keys()
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"✅ Exported {len(results)} results → {output_file}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("✅ Utils ready")
