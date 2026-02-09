"""
ORACLE Phase 4: ML Signals → Telegram
Sends ML scores and insights to Telegram
"""
import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class TelegramSignalGenerator:
    """Generates trading signals from ML scores"""
    
    def __init__(self):
        self.telegram_token = os.getenv("TELEGRAM_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    def load_scores(self, filepath: str) -> List[Dict]:
        """Load ML scores from CSV"""
        scores = []
        if not os.path.exists(filepath):
            return []
        
        with open(filepath) as f:
            reader = csv.DictReader(f)
            for row in reader:
                scores.append(row)
        
        return scores
    
    def generate_signal(self, score: Dict) -> str:
        """
        Generate trading signal from ML score
        
        Returns:
            Signal message for Telegram
        """
        username = score.get('username', 'Unknown')
        followers = int(score.get('followers', 0))
        composite = float(score.get('composite_score', 0))
        airdrop_fit = float(score.get('airdrop_fit', 0))
        confidence = float(score.get('confidence', 0))
        
        # Rank by score
        if composite >= 80:
            rank = "🟢 STRONG"
        elif composite >= 60:
            rank = "🟡 MODERATE"
        else:
            rank = "🔴 WEAK"
        
        # Airdrop potential
        if airdrop_fit >= 80:
            airdrop = "🎁 High airdrop potential"
        elif airdrop_fit >= 60:
            airdrop = "📦 Moderate airdrop fit"
        else:
            airdrop = "❌ Low airdrop fit"
        
        signal = f"""
{rank} Influencer Signal
━━━━━━━━━━━━━━━━━━
👤 @{username}
👥 {followers:,} followers

📊 Metrics:
• ML Score: {composite:.0f}/100
• {airdrop}
• Confidence: {confidence:.0f}%

📈 Status: Ready for airdrop campaign
🔗 https://twitter.com/{username}
"""
        return signal.strip()
    
    def generate_top_signals(self, limit: int = 5, scores_file: str = None) -> List[str]:
        """
        Generate top N influencer signals
        
        Args:
            limit: Number of top signals
            scores_file: Path to scores CSV
        
        Returns:
            List of signal messages
        """
        base_dir = Path(__file__).parent.parent
        scores_file = scores_file or base_dir / "data" / "ml_scores_phase4.csv"
        
        scores = self.load_scores(str(scores_file))
        
        # Sort by composite_score
        scores.sort(
            key=lambda x: float(x.get('composite_score', 0)),
            reverse=True
        )
        
        signals = []
        for score in scores[:limit]:
            signal = self.generate_signal(score)
            signals.append(signal)
        
        return signals
    
    def format_summary(self, scores: List[Dict]) -> str:
        """
        Format summary of all scores
        
        Returns:
            Summary message
        """
        if not scores:
            return "No scores available"
        
        avg_score = sum(float(s.get('composite_score', 0)) for s in scores) / len(scores)
        
        summary = f"""
🔮 ORACLE ML Analysis Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Influencers Scored: {len(scores)}
📊 Average ML Score: {avg_score:.0f}/100
🎯 Top Performer: {scores[0]['username']} ({scores[0]['composite_score']}/100)
⏰ Timestamp: {datetime.utcnow().isoformat()}

Use /signals to see top influencers
Use /airdrop to filter by airdrop potential
"""
        return summary.strip()


def main():
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "=" * 70)
    print("🚀 ORACLE Phase 4: ML Signals Generator")
    print("=" * 70)
    
    gen = TelegramSignalGenerator()
    
    print("\n🔄 Generating top 5 signals...")
    signals = gen.generate_top_signals(limit=5)
    
    for i, signal in enumerate(signals, 1):
        print(f"\n--- Signal {i} ---")
        print(signal)
    
    # Summary
    scores = gen.load_scores('data/ml_scores_phase4.csv')
    print(f"\n{gen.format_summary(scores)}")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
