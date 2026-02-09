# 🔮 ORACLE Phase 4: ML Plan

## Objectifs

- ✅ **Score influencers**: 0-100 based on engagement + sentiment
- ✅ **Prédire airdrops**: Qui bénéficiera d'un airdrop crypto
- 🔄 **Sentiment analysis**: Tweets positif/négatif/neutre
- 🔄 **Arb detection**: Polymarket spread + arbitrage
- 🔄 **Prix prediction**: Mouvement marché (Phase 4+)

## Data Disponible

### Influencers
- **27 handles** trackés
- **62,857 followers** total
- **20 catégories** (trader, NFT, VC, builder...)
- File: `/oracle/data/influencers_phase3.csv`

**Colonnes:**
- username, name, bio, followers, created, url, category, status

### Tweets
- **En attente**: Export depuis Twitter scraper (Phase 2)
- **Métriques attendues**: likes, retweets, replies, posted_at
- **File**: `/oracle/data/tweets_history.csv` (template créé)

## Architecture ML

```
ml_engine/
├── config.py              # Config + paths
├── __init__.py            # Package init
├── influencer_scorer.py   # Engagement + sentiment scoring
├── polymarket_predictor.py # (Phase 4+) Market predictions
├── data_collection.py     # Export CSV from sources
└── utils.py               # Helper functions
```

## Timeline

- **S1-2** (Semaine 1-2):
  - ✅ Setup structure `/ml_engine/`
  - ✅ Export influencers CSV
  - 🔄 Connecter Twitter scraper → tweets CSV
  - 🔄 Premier modèle test

- **S3-4** (Semaine 3-4):
  - Intégration Notion → ML → Telegram
  - Tests scoring sur 27 handles
  - Ajustement weights

- **S5-6** (Semaine 5-6):
  - Polymarket predictions
  - Dashboard UI
  - Production deployment

## Blockers

1. **Tweets CSV**: Besoin d'export depuis Twitter scraper DB
2. **Sentiment model**: Textblob vs Claude API (décider)
3. **Notion API**: Connecter scorer results → Notion DB

## Livrables Cette Semaine

- ✅ Structure `/ml_engine/` créée
- ✅ `influencers_phase3.csv` exporté
- ✅ `influencer_scorer.py` fonctionnel
- ✅ `requirements_ml.txt` (pandas, scikit-learn, etc.)
- ✅ `config.py` avec paths
- 🔄 Connecter tweets scraper
- 🔄 Tester premier score sur 5 handles

## Testing

```bash
cd oracle
python3 -m ml_engine.influencer_scorer  # Test scorer
python3 ml_engine/data_collection.py    # Export data
```

## Ressources

- **Haiku 3.5**: Sentiment fast + lightweight
- **Sonnet 4.5**: Complex analysis fallback
- **scikit-learn**: Engagement model (no LLM cost)

---

**Prochaine étape**: Connecter tweets scraper → `tweets_history.csv`
