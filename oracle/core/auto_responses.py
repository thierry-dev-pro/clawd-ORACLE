"""
Auto-responses intelligentes - Système contextualisé avec patterns et rules
Gère les réponses automatiques basées sur le contexte utilisateur, type de message et historique
"""
import logging
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from core.models import Message, AutoResponse, AutoResponseStat

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Classification des types de messages"""
    GREETING = "greeting"
    QUESTION = "question"
    STATEMENT = "statement"
    COMMAND = "command"
    REQUEST = "request"
    FEEDBACK = "feedback"
    SMALL_TALK = "small_talk"
    URGENT = "urgent"


class ResponsePriority(Enum):
    """Priorité de réponse automatique"""
    IMMEDIATE = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    DEFER = 5


@dataclass
class ResponsePattern:
    """Pattern de reconnaissance pour auto-response"""
    pattern_id: str
    regex: str
    message_type: MessageType
    description: str
    response_template: str
    priority: ResponsePriority = ResponsePriority.MEDIUM
    keywords: List[str] = field(default_factory=list)
    requires_context: bool = False
    enabled: bool = True
    min_confidence: float = 0.7
    
    def match(self, text: str) -> Tuple[bool, float]:
        """
        Teste si le pattern correspond au texte
        Retourne (match, confidence)
        """
        try:
            match = re.search(self.regex, text, re.IGNORECASE)
            if not match:
                return False, 0.0
            
            # Boost confiance si keywords sont trouvés
            confidence = 0.8
            keyword_matches = sum(1 for kw in self.keywords if kw.lower() in text.lower())
            if keyword_matches > 0:
                confidence = min(1.0, 0.8 + (keyword_matches * 0.05))
            
            return True, confidence
        except Exception as e:
            logger.error(f"Pattern matching error: {e}")
            return False, 0.0


@dataclass
class UserContext:
    """Contexte utilisateur pour décisions intelligentes"""
    user_id: int
    is_premium: bool = False
    message_count: int = 0
    last_interaction: Optional[datetime] = None
    response_frequency: int = 0  # réponses envoyées récemment
    average_response_time: float = 0.0  # en secondes
    language_preference: str = "en"
    timezone: Optional[str] = None
    custom_metadata: Dict = field(default_factory=dict)
    
    def get_time_since_last(self) -> Optional[int]:
        """Secondes depuis dernière interaction"""
        if self.last_interaction:
            return int((datetime.utcnow() - self.last_interaction).total_seconds())
        return None
    
    def should_respond_based_on_frequency(self, max_per_hour: int = 3) -> bool:
        """Limite du taux de réponse"""
        return self.response_frequency < max_per_hour


@dataclass
class MessageContext:
    """Contexte du message"""
    content: str
    detected_type: MessageType
    confidence: float
    is_reply_to_previous: bool = False
    has_mentions: bool = False
    has_urgency_markers: bool = False
    estimated_sentiment: str = "neutral"  # positive, negative, neutral
    keywords_found: List[str] = field(default_factory=list)
    conversation_length: int = 0  # nombre de messages dans le contexte
    
    def should_get_immediate_response(self) -> bool:
        """Détermine si réponse immédiate nécessaire"""
        return (
            self.detected_type == MessageType.URGENT or
            self.has_urgency_markers or
            self.is_reply_to_previous
        )


class AutoResponder:
    """Gestionnaire d'auto-responses intelligentes"""
    
    def __init__(self):
        self.patterns: Dict[str, ResponsePattern] = {}
        self._initialize_default_patterns()
        logger.info("✅ AutoResponder initialized with default patterns")
    
    def _initialize_default_patterns(self):
        """Initialise les patterns par défaut"""
        default_patterns = [
            # Greetings
            ResponsePattern(
                pattern_id="greeting_hello",
                regex=r"^(hello|hi|hey|greetings|salut|bonjour|bonsoir)",
                message_type=MessageType.GREETING,
                description="Détecte les salutations",
                response_template="👋 Hello! How can I help you today?",
                priority=ResponsePriority.IMMEDIATE,
                keywords=["hello", "hi", "hey"],
                min_confidence=0.9
            ),
            
            # Questions rapides
            ResponsePattern(
                pattern_id="question_what",
                regex=r"(^|\s)(what|why|when|which|whose|whom)\s+.*\?",
                message_type=MessageType.QUESTION,
                description="Questions commençant par 'what/why/when/etc'",
                response_template="🤔 Great question! Let me gather some context...",
                priority=ResponsePriority.HIGH,
                keywords=["what", "why", "when", "which"],
                min_confidence=0.75
            ),
            
            ResponsePattern(
                pattern_id="question_how",
                regex=r"(^|\s)how\s+.*\?",
                message_type=MessageType.QUESTION,
                description="Questions commençant par 'how'",
                response_template="💡 Here's what I know about that...",
                priority=ResponsePriority.HIGH,
                keywords=["how"],
                min_confidence=0.75
            ),
            
            # Commands
            ResponsePattern(
                pattern_id="command_help",
                regex=r"^/help",
                message_type=MessageType.COMMAND,
                description="Commande /help",
                response_template="""📚 Available commands:
• /help - Show this menu
• /status - Current status
• /config - Configuration
• /stats - Statistics""",
                priority=ResponsePriority.IMMEDIATE,
                keywords=["/help"],
                min_confidence=0.95
            ),
            
            ResponsePattern(
                pattern_id="command_status",
                regex=r"^/status",
                message_type=MessageType.COMMAND,
                description="Commande /status",
                response_template="✅ System status: Online and operational",
                priority=ResponsePriority.IMMEDIATE,
                keywords=["/status"],
                min_confidence=0.95
            ),
            
            ResponsePattern(
                pattern_id="command_config",
                regex=r"^/config",
                message_type=MessageType.COMMAND,
                description="Commande /config",
                response_template="⚙️ Configuration options available. What would you like to configure?",
                priority=ResponsePriority.HIGH,
                keywords=["/config"],
                min_confidence=0.95
            ),
            
            # Crypto-related
            ResponsePattern(
                pattern_id="crypto_btc",
                regex=r"(bitcoin|btc|crypto|ethereum|eth|blockchain)",
                message_type=MessageType.STATEMENT,
                description="Mention crypto/blockchain",
                response_template="🔗 Crypto topic detected. Analyzing...",
                priority=ResponsePriority.MEDIUM,
                keywords=["bitcoin", "btc", "crypto", "ethereum", "eth", "blockchain"],
                requires_context=True,
                min_confidence=0.7
            ),
            
            # Feedback
            ResponsePattern(
                pattern_id="feedback_thanks",
                regex=r"(thanks|thank you|appreciate|good job|well done)",
                message_type=MessageType.FEEDBACK,
                description="Feedback positif",
                response_template="😊 Thank you! Happy to help.",
                priority=ResponsePriority.LOW,
                keywords=["thanks", "thank you", "appreciate"],
                min_confidence=0.8
            ),
            
            # Urgent markers
            ResponsePattern(
                pattern_id="urgent_asap",
                regex=r"(asap|urgent|emergency|critical|help me now|now\!|\!\!)",
                message_type=MessageType.URGENT,
                description="Marqueurs d'urgence",
                response_template="⚠️ I see this is urgent! Prioritizing...",
                priority=ResponsePriority.IMMEDIATE,
                keywords=["asap", "urgent", "emergency", "critical"],
                min_confidence=0.85
            ),
        ]
        
        for pattern in default_patterns:
            self.patterns[pattern.pattern_id] = pattern
    
    def classify_message(self, text: str) -> MessageContext:
        """
        Classe un message pour déterminer son type et contexte
        Retourne MessageContext avec détection automatique
        """
        text_lower = text.lower()
        
        # Détecte les marqueurs d'urgence
        urgency_markers = ["asap", "urgent", "emergency", "critical", "!!", "now"]
        has_urgency = any(marker in text_lower for marker in urgency_markers)
        
        # Détecte les mentions
        has_mentions = "@" in text or "cc:" in text_lower
        
        # Détecte les sentiments basiques
        sentiment = "neutral"
        if any(word in text_lower for word in ["😊", "🎉", "😍", "thanks", "awesome", "great"]):
            sentiment = "positive"
        elif any(word in text_lower for word in ["😔", "😠", "😤", "bad", "terrible", "hate"]):
            sentiment = "negative"
        
        # Détecte le type de message par patterns
        best_match = None
        best_confidence = 0.0
        
        for pattern in self.patterns.values():
            if not pattern.enabled:
                continue
            
            match, confidence = pattern.match(text)
            if match and confidence > best_confidence:
                best_match = pattern
                best_confidence = confidence
        
        # Type par défaut
        detected_type = best_match.message_type if best_match else MessageType.STATEMENT
        
        # Collecte keywords
        keywords = []
        if best_match:
            keywords = best_match.keywords.copy()
        
        return MessageContext(
            content=text,
            detected_type=detected_type,
            confidence=best_confidence,
            has_mentions=has_mentions,
            has_urgency_markers=has_urgency,
            estimated_sentiment=sentiment,
            keywords_found=keywords
        )
    
    def should_auto_respond(
        self,
        message_ctx: MessageContext,
        user_ctx: UserContext,
        conversation_history: List[Message] = None
    ) -> Tuple[bool, ResponsePriority, str]:
        """
        Décide si une auto-response doit être envoyée
        Retourne (should_respond, priority, reason)
        """
        # Vérification 1: Pattern match
        pattern_match = message_ctx.confidence >= 0.7
        if not pattern_match:
            return False, ResponsePriority.DEFER, "No confident pattern match"
        
        # Vérification 2: Rate limiting pour non-premium
        if not user_ctx.is_premium and not user_ctx.should_respond_based_on_frequency(max_per_hour=2):
            return False, ResponsePriority.DEFER, "Rate limit exceeded for non-premium user"
        
        # Vérification 3: Pas de boucle infinie
        if conversation_history:
            recent_ai_responses = sum(
                1 for m in conversation_history[-5:] 
                if m.message_type == "ai_response"
            )
            if recent_ai_responses >= 2:
                return False, ResponsePriority.DEFER, "Too many recent AI responses"
        
        # Vérification 4: Détermine la priorité
        if message_ctx.should_get_immediate_response():
            return True, ResponsePriority.IMMEDIATE, "Urgent or direct reply needed"
        
        if message_ctx.detected_type == MessageType.QUESTION:
            return True, ResponsePriority.HIGH, "Question detected"
        
        if message_ctx.detected_type == MessageType.COMMAND:
            return True, ResponsePriority.IMMEDIATE, "Command detected"
        
        if message_ctx.estimated_sentiment == "positive":
            return True, ResponsePriority.LOW, "Positive sentiment detected"
        
        return True, ResponsePriority.MEDIUM, "General response suitable"
    
    def generate_contextual_response(
        self,
        message_ctx: MessageContext,
        user_ctx: UserContext,
        pattern: Optional[ResponsePattern] = None,
        conversation_history: List[Message] = None
    ) -> str:
        """
        Génère une réponse contextuelle basée sur templates et contexte
        """
        if not pattern:
            # Trouve le pattern correspondant
            for p in self.patterns.values():
                match, _ = p.match(message_ctx.content)
                if match:
                    pattern = p
                    break
        
        if not pattern:
            return "I appreciate your message. Let me think about that..."
        
        # Customize la réponse template
        response = pattern.response_template
        
        # Ajoute personnalisation premium
        if user_ctx.is_premium:
            response = "✨ " + response  # Premium prefix
        
        # Ajoute contexte conversation
        if conversation_history and len(conversation_history) > 1:
            response += f"\n\n(Based on our conversation so far)"
        
        # Ajoute urgence si détectée
        if message_ctx.has_urgency_markers:
            response = "🚨 " + response
        
        return response
    
    def add_pattern(self, pattern: ResponsePattern) -> bool:
        """Ajoute un nouveau pattern"""
        try:
            if pattern.pattern_id in self.patterns:
                logger.warning(f"Pattern {pattern.pattern_id} already exists, updating...")
            
            self.patterns[pattern.pattern_id] = pattern
            logger.info(f"✅ Pattern added: {pattern.pattern_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error adding pattern: {e}")
            return False
    
    def remove_pattern(self, pattern_id: str) -> bool:
        """Désactive un pattern"""
        try:
            if pattern_id in self.patterns:
                self.patterns[pattern_id].enabled = False
                logger.info(f"✅ Pattern disabled: {pattern_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error removing pattern: {e}")
            return False
    
    def get_patterns_summary(self) -> Dict:
        """Résumé des patterns actifs"""
        active = sum(1 for p in self.patterns.values() if p.enabled)
        return {
            "total": len(self.patterns),
            "active": active,
            "inactive": len(self.patterns) - active,
            "patterns": {
                pid: {
                    "description": p.description,
                    "enabled": p.enabled,
                    "priority": p.priority.name
                }
                for pid, p in self.patterns.items()
            }
        }
    
    def save_patterns_to_db(self, db: Session, overwrite: bool = False) -> int:
        """Sauvegarde les patterns dans la DB"""
        try:
            count = 0
            for pattern in self.patterns.values():
                # Vérifie si existe
                existing = db.query(AutoResponse).filter(
                    AutoResponse.pattern_id == pattern.pattern_id
                ).first()
                
                if existing and not overwrite:
                    continue
                
                if existing:
                    # Mise à jour
                    existing.regex = pattern.regex
                    existing.message_type = pattern.message_type.value
                    existing.description = pattern.description
                    existing.response_template = pattern.response_template
                    existing.priority = pattern.priority.value
                    existing.keywords = pattern.keywords
                    existing.requires_context = pattern.requires_context
                    existing.enabled = pattern.enabled
                    existing.min_confidence = pattern.min_confidence
                    existing.updated_at = datetime.utcnow()
                else:
                    # Création
                    ar = AutoResponse(
                        pattern_id=pattern.pattern_id,
                        regex=pattern.regex,
                        message_type=pattern.message_type.value,
                        description=pattern.description,
                        response_template=pattern.response_template,
                        priority=pattern.priority.value,
                        keywords=pattern.keywords,
                        requires_context=pattern.requires_context,
                        enabled=pattern.enabled,
                        min_confidence=pattern.min_confidence
                    )
                    db.add(ar)
                
                count += 1
            
            db.commit()
            logger.info(f"✅ Saved {count} patterns to DB")
            return count
        except Exception as e:
            logger.error(f"❌ Error saving patterns: {e}")
            db.rollback()
            return 0
    
    def load_patterns_from_db(self, db: Session) -> int:
        """Charge les patterns depuis la DB"""
        try:
            db_patterns = db.query(AutoResponse).filter(
                AutoResponse.enabled == True
            ).all()
            
            count = 0
            for db_pattern in db_patterns:
                pattern = ResponsePattern(
                    pattern_id=db_pattern.pattern_id,
                    regex=db_pattern.regex,
                    message_type=MessageType(db_pattern.message_type),
                    description=db_pattern.description,
                    response_template=db_pattern.response_template,
                    priority=ResponsePriority(db_pattern.priority),
                    keywords=db_pattern.keywords or [],
                    requires_context=db_pattern.requires_context,
                    enabled=db_pattern.enabled,
                    min_confidence=db_pattern.min_confidence
                )
                self.patterns[pattern.pattern_id] = pattern
                count += 1
            
            logger.info(f"✅ Loaded {count} patterns from DB")
            return count
        except Exception as e:
            logger.error(f"❌ Error loading patterns: {e}")
            return 0
    
    def record_auto_response_stat(
        self,
        db: Session,
        user_id: int,
        pattern_id: str,
        message_content: str,
        response_content: str,
        was_accepted: bool = None
    ) -> Optional[AutoResponseStat]:
        """Enregistre les stats d'une auto-response"""
        try:
            stat = AutoResponseStat(
                user_id=user_id,
                pattern_id=pattern_id,
                message_content=message_content[:500],  # Limité
                response_content=response_content[:500],
                was_accepted=was_accepted
            )
            db.add(stat)
            db.commit()
            db.refresh(stat)
            return stat
        except Exception as e:
            logger.error(f"❌ Error recording stat: {e}")
            db.rollback()
            return None
    
    def get_response_stats(self, db: Session, days: int = 7) -> Dict:
        """Récupère les stats des auto-responses"""
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            stats = db.query(AutoResponseStat).filter(
                AutoResponseStat.created_at >= since
            ).all()
            
            if not stats:
                return {
                    "total_responses": 0,
                    "accepted": 0,
                    "rejected": 0,
                    "pending": 0,
                    "acceptance_rate": 0.0,
                    "patterns": {}
                }
            
            total = len(stats)
            accepted = sum(1 for s in stats if s.was_accepted == True)
            rejected = sum(1 for s in stats if s.was_accepted == False)
            pending = sum(1 for s in stats if s.was_accepted is None)
            
            # Par pattern
            patterns_stats = {}
            for stat in stats:
                if stat.pattern_id not in patterns_stats:
                    patterns_stats[stat.pattern_id] = {"count": 0, "accepted": 0}
                patterns_stats[stat.pattern_id]["count"] += 1
                if stat.was_accepted:
                    patterns_stats[stat.pattern_id]["accepted"] += 1
            
            return {
                "total_responses": total,
                "accepted": accepted,
                "rejected": rejected,
                "pending": pending,
                "acceptance_rate": (accepted / total * 100) if total > 0 else 0.0,
                "patterns": patterns_stats,
                "period_days": days
            }
        except Exception as e:
            logger.error(f"❌ Error fetching stats: {e}")
            return {}


# Instance globale
auto_responder = AutoResponder()
