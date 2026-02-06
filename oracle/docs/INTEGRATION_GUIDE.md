# Integration Guide - Auto-Responses System

## Quick Start

### 1. Database Setup

```bash
# Migrations are automatic with SQLAlchemy
# When the app starts, tables are created:
# - AutoResponse (patterns config)
# - AutoResponseStat (usage statistics)

python3 main.py
# Tables created automatically
```

### 2. Default Patterns Initialization

Les patterns par défaut sont initialisés au démarrage de l'application:

```python
# core/auto_responses.py already includes:
- greeting_hello (salutations)
- question_what/how (questions)
- command_help/status/config (commandes)
- crypto_btc (sujets crypto)
- feedback_thanks (feedback positif)
- urgent_asap (urgence)
```

### 3. Telegram Webhook Integration

Le système fonctionne automatiquement avec le webhook Telegram:

```python
# core/telegram_bot.py
async def process_update(update: dict):
    # 1. Message reçu
    # 2. check_auto_response() appelé
    # 3. Si pattern match → réponse immédiate
    # 4. Sinon → traitement AI via Claude
```

### 4. Test des Auto-Responses

```bash
python3 test_auto_responses.py
# Output:
# ✅ Passed: 27
# ❌ Failed: 3
# 📈 Success Rate: 90.0%
```

## API Admin Endpoints

### Base URL
```
http://localhost:8000/admin/auto-responses
```

### 1. List Patterns

#### Request
```bash
curl http://localhost:8000/admin/auto-responses/patterns
```

#### Response
```json
{
  "total": 9,
  "patterns": [
    {
      "pattern_id": "greeting_hello",
      "description": "Détecte les salutations",
      "message_type": "greeting",
      "priority": "IMMEDIATE",
      "enabled": true,
      "keywords": ["hello", "hi", "hey"],
      "min_confidence": 0.9
    }
  ]
}
```

### 2. Get Pattern Details

#### Request
```bash
curl http://localhost:8000/admin/auto-responses/patterns/greeting_hello
```

#### Response
```json
{
  "pattern_id": "greeting_hello",
  "regex": "^(hello|hi|hey|greetings|salut|bonjour|bonsoir)",
  "description": "Détecte les salutations",
  "message_type": "greeting",
  "response_template": "👋 Hello! How can I help you today?",
  "priority": "IMMEDIATE",
  "keywords": ["hello", "hi", "hey"],
  "enabled": true,
  "min_confidence": 0.9
}
```

### 3. Create New Pattern

#### Request
```bash
curl -X POST http://localhost:8000/admin/auto-responses/patterns \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "custom_crypto",
    "regex": "(dapp|defi|nft|web3)",
    "message_type": "question",
    "description": "Web3/DApp related questions",
    "response_template": "🌐 Web3 topic detected. Let me analyze...",
    "priority": 3,
    "keywords": ["dapp", "defi", "nft", "web3"],
    "requires_context": false,
    "min_confidence": 0.75,
    "enabled": true
  }'
```

#### Response
```json
{
  "status": "created",
  "pattern_id": "custom_crypto",
  "message": "Pattern custom_crypto created successfully"
}
```

### 4. Update Pattern

#### Request
```bash
curl -X PUT http://localhost:8000/admin/auto-responses/patterns/greeting_hello \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description",
    "response_template": "✨ Hello there! How can I assist you?",
    "priority": 2
  }'
```

#### Response
```json
{
  "status": "updated",
  "pattern_id": "greeting_hello",
  "message": "Pattern greeting_hello updated successfully"
}
```

### 5. Delete Pattern

#### Request
```bash
curl -X DELETE http://localhost:8000/admin/auto-responses/patterns/greeting_hello
```

#### Response
```json
{
  "status": "deleted",
  "pattern_id": "greeting_hello",
  "message": "Pattern greeting_hello disabled successfully"
}
```

### 6. Get Overall Statistics

#### Request
```bash
curl http://localhost:8000/admin/auto-responses/stats?days=7
```

#### Response
```json
{
  "total_responses": 150,
  "accepted": 140,
  "rejected": 5,
  "pending": 5,
  "acceptance_rate": 93.3,
  "patterns": {
    "greeting_hello": {
      "count": 45,
      "accepted": 43
    },
    "question_what": {
      "count": 30,
      "accepted": 28
    }
  },
  "period_days": 7
}
```

### 7. Get Pattern-Specific Statistics

#### Request
```bash
curl http://localhost:8000/admin/auto-responses/stats/pattern/greeting_hello?days=7
```

#### Response
```json
{
  "pattern_id": "greeting_hello",
  "period_days": 7,
  "total_responses": 45,
  "accepted": 43,
  "rejected": 1,
  "pending": 1,
  "acceptance_rate": 95.6,
  "recent_samples": [
    {
      "id": 142,
      "user_id": 12345,
      "message": "Hey there!",
      "response": "👋 Hello! How can I...",
      "was_accepted": true,
      "created_at": "2026-02-02T08:30:00"
    }
  ]
}
```

### 8. Submit User Feedback

#### Request
```bash
curl -X POST http://localhost:8000/admin/auto-responses/stats/feedback/142 \
  -H "Content-Type: application/json" \
  -d '{
    "was_accepted": true,
    "feedback": "Perfect response!"
  }'
```

#### Response
```json
{
  "status": "recorded",
  "stat_id": 142,
  "was_accepted": true,
  "message": "Feedback recorded successfully"
}
```

### 9. Get System Summary

#### Request
```bash
curl http://localhost:8000/admin/auto-responses/summary
```

#### Response
```json
{
  "patterns": {
    "total": 9,
    "active": 9,
    "inactive": 0,
    "patterns": {
      "greeting_hello": {
        "description": "Détecte les salutations",
        "enabled": true,
        "priority": "IMMEDIATE"
      }
    }
  },
  "recent_stats": {
    "total_responses": 150,
    "accepted": 140,
    "acceptance_rate": 93.3
  },
  "system_status": "operational",
  "last_sync": "2026-02-02T08:35:00"
}
```

### 10. Reload Patterns from Database

#### Request
```bash
curl -X POST http://localhost:8000/admin/auto-responses/patterns/reload
```

#### Response
```json
{
  "status": "reloaded",
  "patterns_before": 9,
  "patterns_loaded": 9,
  "message": "Reloaded 9 patterns from database"
}
```

### 11. Sync Patterns to Database

#### Request
```bash
curl -X POST http://localhost:8000/admin/auto-responses/patterns/sync
```

#### Response
```json
{
  "status": "synced",
  "patterns_synced": 9,
  "message": "Synced 9 patterns to database"
}
```

## Python SDK Usage

### Load Patterns
```python
from core.auto_responses import auto_responder
from core.database import SessionLocal

db = SessionLocal()
auto_responder.load_patterns_from_db(db)
db.close()
```

### Classify Message
```python
msg_ctx = auto_responder.classify_message("What is Bitcoin?")
print(f"Type: {msg_ctx.detected_type}")
print(f"Confidence: {msg_ctx.confidence}")
```

### Check Auto-Response
```python
from core.auto_responses import UserContext

user_ctx = UserContext(user_id=12345, is_premium=True)
should_respond, priority, reason = auto_responder.should_auto_respond(
    msg_ctx,
    user_ctx,
    conversation_history=[]
)
```

### Generate Response
```python
response = auto_responder.generate_contextual_response(
    msg_ctx,
    user_ctx,
    pattern=None,
    conversation_history=[]
)
print(response)
```

### Get Statistics
```python
stats = auto_responder.get_response_stats(db, days=7)
print(f"Acceptance rate: {stats['acceptance_rate']:.1f}%")
```

## Telegram Integration Example

### Receive Message → Auto-Response Flow

```
User: "Hello! 👋"
         ↓
Telegram Webhook (main.py)
         ↓
TelegramBotHandler.process_update()
         ↓
check_auto_response() 
         ↓
classify_message() → Type: GREETING, Confidence: 0.85
         ↓
should_auto_respond() → True, Priority: IMMEDIATE
         ↓
generate_contextual_response()
         ↓
Response: "👋 Hello! How can I help you today?"
         ↓
record_auto_response_stat()
         ↓
Return response to Telegram API
         ↓
User receives: "👋 Hello! How can I help you today?"
```

## Monitoring & Maintenance

### Daily Checks
```bash
# Get acceptance rate
curl http://localhost:8000/admin/auto-responses/stats?days=1

# Check patterns status
curl http://localhost:8000/admin/auto-responses/summary
```

### Weekly Analysis
```bash
# Get pattern performance
curl http://localhost:8000/admin/auto-responses/stats?days=7

# Identify low-performing patterns (< 80% acceptance)
# Disable or improve those patterns
```

### Monthly Review
```bash
# Get 30-day statistics
curl http://localhost:8000/admin/auto-responses/stats?days=30

# Export data for analysis
# Adjust configuration based on performance
```

## Troubleshooting

### Auto-Response Not Triggering

1. **Check Pattern Match**
   ```bash
   curl http://localhost:8000/admin/auto-responses/patterns/{pattern_id}
   # Verify regex and keywords
   ```

2. **Check Message Classification**
   ```python
   from core.auto_responses import auto_responder
   msg_ctx = auto_responder.classify_message("your test message")
   print(f"Detected type: {msg_ctx.detected_type}")
   print(f"Confidence: {msg_ctx.confidence}")
   ```

3. **Check User Rate Limiting**
   ```python
   # Review should_auto_respond() logs
   # User might have exceeded rate limit
   ```

### Pattern Not Working Correctly

1. **Test Regex**
   ```python
   import re
   pattern = r"^(hello|hi|hey)"
   match = re.search(pattern, "Hello there!", re.IGNORECASE)
   print(f"Match: {match is not None}")
   ```

2. **Adjust Confidence Threshold**
   ```bash
   curl -X PUT http://localhost:8000/admin/auto-responses/patterns/{pattern_id} \
     -d '{"min_confidence": 0.65}'
   ```

3. **Update Keywords**
   ```bash
   curl -X PUT http://localhost:8000/admin/auto-responses/patterns/{pattern_id} \
     -d '{"keywords": ["hello", "hi", "hey", "greetings"]}'
   ```

## Performance Tips

1. **Use Appropriate Regex** - Complex regex slows down matching
2. **Set Proper min_confidence** - Too low = false positives, too high = misses
3. **Limit Keywords** - More keywords = slower matching
4. **Monitor Feedback** - Disable patterns with < 70% acceptance rate
5. **Regular Cleanup** - Archive old statistics monthly

## Security Considerations

1. **Validate Pattern Regex** - Prevent ReDoS (Regular Expression Denial of Service)
2. **Rate Limit API** - Add authentication to admin endpoints
3. **Log All Changes** - Track who modified patterns
4. **Backup Patterns** - Regular exports to JSON
5. **Monitor Feedback** - Detect malicious patterns in user feedback

---

**Next Steps:**
1. Deploy to production
2. Monitor acceptance rates
3. Collect user feedback
4. Iteratively improve patterns
5. Scale to more message types

For detailed docs, see: `docs/AUTO_RESPONSES.md`
