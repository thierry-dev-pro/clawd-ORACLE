"""
ORACLE Phase 4: Mock Tweets for ML Testing
Generates test tweet data when scraper DB is empty
"""
import csv
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


def generate_mock_tweets(influencers: List[Dict], tweets_per_author: int = 20) -> List[Dict]:
    """
    Generate realistic test tweets for ML training
    
    Args:
        influencers: List of influencer dicts
        tweets_per_author: Tweets to generate per influencer
    
    Returns:
        List of tweet dicts
    """
    tweets = []
    base_date = datetime.utcnow() - timedelta(days=30)
    
    # Crypto keywords for realistic content
    keywords_pool = {
        "bitcoin": ["bitcoin", "btc", "blockchain", "mining"],
        "ethereum": ["ethereum", "eth", "evm", "defi", "smart contract"],
        "nft": ["nft", "nfts", "opensea", "collection", "mint"],
        "trader": ["trading", "long", "short", "support", "resistance"],
        "general": ["crypto", "web3", "token", "airdrop", "giveaway"],
    }
    
    tweet_templates = {
        "bitcoin": [
            "📈 BTC just broke ${price}! Looking bullish for next week #Bitcoin",
            "⚡ Lightning network transaction confirmed in 2 seconds! #Bitcoin #LN",
            "🔒 Self-custody is the way. Not your keys, not your coins #Bitcoin",
        ],
        "ethereum": [
            "🚀 ETH gas fees down to {gas} gwei, great time to swap! #Ethereum",
            "✨ DeFi TVL up 20% this month, bullish on decentralized finance #Ethereum",
            "🔄 Just deployed a new contract on Arbitrum, feeling the scaling vibes #ETH",
        ],
        "nft": [
            "🎨 New NFT collection dropped! Just minted my first one #NFT #Web3",
            "💎 Rare Punks floor price up 15% 🚀 #NFT #Collectibles",
            "🖼️ Art on blockchain is the future. No middlemen needed! #NFT #Art",
        ],
        "general": [
            "📊 Airdrop season coming! Make sure you're eligible for the big ones",
            "🚀 Web3 development is exploding right now. Building in this space is incredible",
            "💰 Just caught a nice arbitrage on Polymarket. Markets never sleep! #Trading",
        ]
    }
    
    for inf in influencers[:20]:  # First 20 for testing
        author = inf['username']
        category = inf.get('category', 'general')
        
        # Get templates for this category
        templates = tweet_templates.get(category, tweet_templates['general'])
        
        for i in range(tweets_per_author):
            # Randomize engagement
            import random
            
            tweet = {
                'external_id': f"{author}_{i}_{datetime.utcnow().timestamp()}",
                'author': author,
                'content': templates[i % len(templates)],
                'url': f"https://twitter.com/{author}/status/{1000000 + i}",
                'posted_at': (base_date + timedelta(hours=i*2)).isoformat(),
                'source': 'mock',
                'likes': random.randint(10, 500),
                'retweets': random.randint(5, 200),
                'replies': random.randint(2, 50),
                'keywords': ','.join(keywords_pool.get(category, keywords_pool['general'])[:3])
            }
            tweets.append(tweet)
    
    logger.info(f"✅ Generated {len(tweets)} mock tweets")
    return tweets


def export_mock_tweets(output_file: str = None, influencers: List[Dict] = None) -> str:
    """
    Export mock tweets to CSV
    
    Args:
        output_file: Path for CSV
        influencers: Influencers list (loads from CSV if None)
    
    Returns:
        Path to exported CSV
    """
    base_dir = Path(__file__).parent.parent
    output_file = output_file or base_dir / "data" / "tweets_mock.csv"
    
    # Load influencers if not provided
    if influencers is None:
        import csv as csv_module
        influencers = []
        influencers_file = base_dir / "data" / "influencers_phase3.csv"
        with open(influencers_file) as f:
            reader = csv_module.DictReader(f)
            influencers = list(reader)
    
    # Generate tweets
    tweets = generate_mock_tweets(influencers)
    
    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=tweets[0].keys()
        )
        writer.writeheader()
        writer.writerows(tweets)
    
    logger.info(f"✅ Exported {len(tweets)} mock tweets → {output_file}")
    return str(output_file)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n🐦 Mock Tweets Generator")
    print("=" * 60)
    
    path = export_mock_tweets()
    print(f"✅ Created: {path}")
    print("=" * 60)
