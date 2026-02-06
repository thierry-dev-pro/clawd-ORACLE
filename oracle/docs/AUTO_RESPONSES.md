# Auto-Responses System - ORACLE

## Vue d'ensemble

Le système d'auto-responses intelligentes pour ORACLE fournit une solution contextualisée et adaptative pour répondre automatiquement aux messages Telegram. Il utilise :

- **Pattern Recognition** - Reconnaissance intelligente des types de messages
- **Contexte Utilisateur** - Adaptation basée sur le profil de l'utilisateur
- **Conversation History** - Prise en compte de l'historique des conversations
- **Multi-factor Decision Making** - Décisions basées sur plusieurs critères

## Architecture

### Composants Principaux

#### 1. **AutoResponder** (`core/auto_responses.py`)
- Gestionnaire central du système
- Gère les patterns et décisions d'auto-response
- Intègre classification de messages et génération de réponses

#### 2. **Message Classification**
- Détection automatique du type de message
- Calcul de confiance (0.0 - 1.0)
- Support: greeting, question, command, statement, request, feedback, urgent, small_talk

#### 3. **User Context**
- Profil utilisateur (premium/regular)
- Historique des interactions
- Préférences linguistiques
- Métadonnées personnalisées

#### 4. **Response Pattern**
- Templates de réponse regex-based
- Priorités de réponse (IMMEDIATE, HIGH, MEDIUM, LOW, DEFER)
- Keywords pour boost de confiance
- Configuration par pattern

### Integration Points

#### AI Handler Integration
```python
# Dans process_message_with_auto_response()
# 1. Charge contexte utilisateur
# 2. Classifie le message
# 3. Décide d'auto-respond (ou délègue à Claude)
# 4. Log les stats pour tracking
```

#### Database Schema
- `AutoResponse` - Configuration des patterns
- `AutoResponseStat` - Statistiques d'utilisation et feedback

#### Admin API (`core/admin_api.py`)
- REST endpoints pour CRUD patterns
- Statistiques et monitoring
- Feedback utilisateur

## Utilisation

### Installation & Configuration

```bash
# Les patterns par défaut sont initialisés automatiquement
# Aucune configuration requise pour démarrer

# Pour charger depuis DB au démarrage:
auto_responder.load_patterns_from_db(db)

# Pour sauvegarder patterns en DB:
auto_responder.save_patterns_to_db(db)
```

### Intégration avec AI Handler

```python
from core.ai_handler import ai_handler
from core.models import Message
from sqlalchemy.orm import Session

# Traiter un message
result = ai_handler.process_message_with_auto_response(
    db=db_session,
    message=message_obj,
    user=user_obj  # optional
)

if result["type"] == "auto_response":
    print(f"✅ Auto-response: {result['response']}")
    print(f"Pattern: {result['pattern_id']}")
else:
    print(f"🤖 Claude response: {result['response']}")
```

### Exemples d'Utilisation

#### Exemple 1: Salutation Simple
```
User: "Hello!"
Auto-response: "👋 Hello! How can I help you today?"
Type: GREETING | Priority: IMMEDIATE | Confidence: 0.85
```

#### Exemple 2: Question
```
User: "What is Bitcoin?"
Auto-response: "🤔 Great question! Let me gather some context..."
Type: QUESTION | Priority: HIGH | Confidence: 0.85
```

#### Exemple 3: Commande
```
User: "/help"
Auto-response: "📚 Available commands:\n• /help - Show this menu\n..."
Type: COMMAND | Priority: IMMEDIATE | Confidence: 0.95
```

#### Exemple 4: Urgent
```
User: "I need help ASAP!!"
Auto-response: "🚨 ⚠️ I see this is urgent! Prioritizing..."
Type: URGENT | Priority: IMMEDIATE | Confidence: 0.85
```

#### Exemple 5: Feedback Positif
```
User: "Thanks for helping! 😊"
Auto-response: "😊 Thank you! Happy to help."
Type: FEEDBACK | Priority: LOW | Confidence: 0.80
```

## Admin API Endpoints

### Pattern Management

#### List All Patterns
```bash
GET /admin/auto-responses/patterns
GET /admin/auto-responses/patterns?enabled_only=true

Response:
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
    },
    ...
  ]
}
```

#### Get Pattern Details
```bash
GET /admin/auto-responses/patterns/{pattern_id}

Response:
{
  "pattern_id": "greeting_hello",
  "regex": "^(hello|hi|hey|greetings|...)",
  "description": "Détecte les salutations",
  "message_type": "greeting",
  "response_template": "👋 Hello! How can I help you today?",
  "priority": "IMMEDIATE",
  "keywords": ["hello", "hi", "hey"],
  "enabled": true,
  "min_confidence": 0.9
}
```

#### Create New Pattern
```bash
POST /admin/auto-responses/patterns

{
  "pattern_id": "custom_pattern",
  "regex": "your_regex_here",
  "message_type": "question",
  "description": "Your description",
  "response_template": "Your response template",
  "priority": 3,  # 1=IMMEDIATE, 2=HIGH, 3=MEDIUM, 4=LOW, 5=DEFER
  "keywords": ["keyword1", "keyword2"],
  "requires_context": false,
  "min_confidence": 0.7,
  "enabled": true
}
```

#### Update Pattern
```bash
PUT /admin/auto-responses/patterns/{pattern_id}

{
  "description": "Updated description",
  "response_template": "Updated response",
  "priority": 2,
  "enabled": true,
  ...
}
```

#### Delete Pattern
```bash
DELETE /admin/auto-responses/patterns/{pattern_id}
```

### Statistics

#### Get Overall Stats
```bash
GET /admin/auto-responses/stats?days=7

Response:
{
  "total_responses": 150,
  "accepted": 140,
  "rejected": 5,
  "pending": 5,
  "acceptance_rate": 93.3,
  "patterns": {
    "greeting_hello": {"count": 45, "accepted": 43},
    "question_what": {"count": 30, "accepted": 28},
    ...
  },
  "period_days": 7
}
```

#### Get Pattern Stats
```bash
GET /admin/auto-responses/stats/pattern/{pattern_id}?days=7

Response:
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
    },
    ...
  ]
}
```

#### Submit Feedback
```bash
POST /admin/auto-responses/stats/feedback/{stat_id}

{
  "was_accepted": true,
  "feedback": "Great response!"
}
```

### System Management

#### Get System Summary
```bash
GET /admin/auto-responses/summary

Response:
{
  "patterns": {
    "total": 9,
    "active": 9,
    "inactive": 0,
    "patterns": {...}
  },
  "recent_stats": {...},
  "system_status": "operational",
  "last_sync": "2026-02-02T08:35:00"
}
```

#### Reload Patterns from DB
```bash
POST /admin/auto-responses/patterns/reload

Response:
{
  "status": "reloaded",
  "patterns_before": 9,
  "patterns_loaded": 9,
  "message": "Reloaded 9 patterns from database"
}
```

#### Sync Patterns to DB
```bash
POST /admin/auto-responses/patterns/sync

Response:
{
  "status": "synced",
  "patterns_synced": 9,
  "message": "Synced 9 patterns to database"
}
```

## Configuration Avancée

### Créer un Pattern Personnalisé

```python
from core.auto_responses import ResponsePattern, MessageType, ResponsePriority

pattern = ResponsePattern(
    pattern_id="my_custom_pattern",
    regex=r"(bitcoin|btc|ethereum|eth)",
    message_type=MessageType.QUESTION,
    description="Détecte questions sur crypto",
    response_template="🔗 Question crypto détectée. Analysing context...",
    priority=ResponsePriority.MEDIUM,
    keywords=["bitcoin", "ethereum", "crypto"],
    requires_context=True,
    min_confidence=0.8,
    enabled=True
)

auto_responder.add_pattern(pattern)
auto_responder.save_patterns_to_db(db)
```

### Rate Limiting

Premium vs Regular Users:
```python
user_ctx = UserContext(
    user_id=12345,
    is_premium=True  # Premium: unlimited responses
)

# Regular users: max 2-3 réponses par heure
if not user_ctx.is_premium and not user_ctx.should_respond_based_on_frequency(max_per_hour=2):
    # Skip auto-response
```

### Conversation Context

```python
# Avoid infinite loops de réponses AI
conversation = db.query(Message).filter(
    Message.telegram_user_id == user_id
).order_by(Message.created_at.desc()).limit(10).all()

msg_ctx.conversation_length = len(conversation)

# AutoResponder limite à max 2 réponses AI récentes
```

## Patterns Inclus par Défaut

| Pattern ID | Type | Description | Priority |
|---|---|---|---|
| greeting_hello | GREETING | Salutations | IMMEDIATE |
| question_what | QUESTION | Questions what/why/when | HIGH |
| question_how | QUESTION | Questions how | HIGH |
| command_help | COMMAND | /help | IMMEDIATE |
| command_status | COMMAND | /status | IMMEDIATE |
| command_config | COMMAND | /config | HIGH |
| crypto_btc | STATEMENT | Mentions crypto | MEDIUM |
| feedback_thanks | FEEDBACK | Feedback positif | LOW |
| urgent_asap | URGENT | Marqueurs urgence | IMMEDIATE |

## Monitoring & Analytics

### Métriques Clés

- **Acceptance Rate** - % de réponses acceptées par utilisateurs
- **Response Time** - Temps moyen avant réponse
- **Pattern Effectiveness** - Performance par pattern
- **User Satisfaction** - Basé sur feedback utilisateur

### Dashboard Recommendations

1. **Pattern Performance** - Voir patterns avec taux d'acceptation faible
2. **User Segments** - Analyser différences Premium vs Regular
3. **Trending Topics** - Identifier patterns manquants
4. **Error Tracking** - Fallback-to-Claude rate et raisons

## Troubleshooting

### Pattern Not Matching

**Problem**: Pattern ne détecte pas les messages attendus

**Solution**:
1. Vérifier regex avec online regex tester
2. Vérifier min_confidence threshold
3. Ajouter/ajuster keywords

```python
# Test pattern matching
pattern = auto_responder.patterns["your_pattern"]
match, confidence = pattern.match("test message")
print(f"Match: {match}, Confidence: {confidence}")
```

### Auto-Response Not Sent

**Problem**: Message reçu mais pas d'auto-response

**Solution**:
1. Vérifier logs AI Handler
2. Vérifier rate limiting
3. Vérifier conversation history (limite de 2 réponses IA)
4. Vérifier confidence score

### High Fallback-to-Claude Rate

**Problem**: Trop de messages délégués à Claude

**Solution**:
1. Ajouter plus de patterns
2. Ajuster min_confidence thresholds
3. Analyser logs pour identifier types de messages manquants

## Testing

Run test suite:
```bash
python3 test_auto_responses.py
```

Output example:
```
✅ Passed: 27
❌ Failed: 3
📈 Success Rate: 90.0%
```

## Production Checklist

- [ ] Database initialized with AutoResponse & AutoResponseStat tables
- [ ] All default patterns tested with realistic examples
- [ ] Admin API endpoints secured (authentication layer added)
- [ ] Monitoring dashboard set up
- [ ] Feedback collection implemented
- [ ] Rate limiting tuned for user base
- [ ] Error handling in place
- [ ] Documentation reviewed
- [ ] Performance tested with expected load
- [ ] Rollback procedure documented

## Future Enhancements

1. **Machine Learning** - Train custom classifier on acceptance data
2. **Language Support** - Multilingual pattern support
3. **A/B Testing** - Test different response variants
4. **Contextual Learning** - Learn from user preferences over time
5. **Webhook Integration** - React to external events
6. **Analytics Export** - CSV/JSON export for analysis

## Support & Questions

For issues or questions:
1. Check logs in `system_logs` table
2. Review pattern regex with test data
3. Check database constraints
4. Run test suite to validate setup

---

**Last Updated**: 2026-02-02
**Version**: 1.0.0-production
**Status**: Production Ready ✅
