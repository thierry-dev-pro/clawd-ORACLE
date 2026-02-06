"""
Test suite pour le système d'auto-responses intelligentes
Tests avec des exemples réalistes
"""
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent to path
sys.path.insert(0, '/Users/clawdbot/clawd/oracle')

from core.auto_responses import (
    auto_responder,
    UserContext,
    MessageType,
    ResponsePriority
)


class TestAutoResponses:
    """Suite de tests pour auto-responses"""
    
    def __init__(self):
        self.test_cases = []
        self.passed = 0
        self.failed = 0
    
    def test_greeting_detection(self):
        """Test: Détection des salutations"""
        test_messages = [
            ("Hello there!", MessageType.GREETING, True),
            ("Hi, how are you?", MessageType.GREETING, True),
            ("Hey everyone!", MessageType.GREETING, True),
            ("Bonjour à tous", MessageType.GREETING, True),
            ("This is a statement", MessageType.STATEMENT, False),
        ]
        
        logger.info("\n" + "="*60)
        logger.info("🧪 TEST: Greeting Detection")
        logger.info("="*60)
        
        for message, expected_type, should_respond in test_messages:
            ctx = auto_responder.classify_message(message)
            
            is_correct = ctx.detected_type == expected_type
            status = "✅ PASS" if is_correct else "❌ FAIL"
            
            logger.info(f"{status} | '{message}'")
            logger.info(f"   → Detected: {ctx.detected_type.value} (confidence: {ctx.confidence:.2f})")
            
            if is_correct:
                self.passed += 1
            else:
                self.failed += 1
    
    def test_question_detection(self):
        """Test: Détection des questions"""
        test_messages = [
            ("What is Bitcoin?", MessageType.QUESTION),
            ("How do I get started with crypto?", MessageType.QUESTION),
            ("Why is Ethereum important?", MessageType.QUESTION),
            ("Can you help me?", MessageType.QUESTION),
        ]
        
        logger.info("\n" + "="*60)
        logger.info("🧪 TEST: Question Detection")
        logger.info("="*60)
        
        for message, expected_type in test_messages:
            ctx = auto_responder.classify_message(message)
            
            is_correct = ctx.detected_type == expected_type
            status = "✅ PASS" if is_correct else "❌ FAIL"
            
            logger.info(f"{status} | '{message}'")
            logger.info(f"   → Detected: {ctx.detected_type.value} (confidence: {ctx.confidence:.2f})")
            
            if is_correct:
                self.passed += 1
            else:
                self.failed += 1
    
    def test_command_detection(self):
        """Test: Détection des commandes"""
        test_messages = [
            "/help",
            "/status",
            "/config",
        ]
        
        logger.info("\n" + "="*60)
        logger.info("🧪 TEST: Command Detection")
        logger.info("="*60)
        
        for message in test_messages:
            ctx = auto_responder.classify_message(message)
            
            is_correct = ctx.detected_type == MessageType.COMMAND
            status = "✅ PASS" if is_correct else "❌ FAIL"
            
            logger.info(f"{status} | '{message}'")
            logger.info(f"   → Detected: {ctx.detected_type.value} (confidence: {ctx.confidence:.2f})")
            
            if is_correct:
                self.passed += 1
            else:
                self.failed += 1
    
    def test_urgency_detection(self):
        """Test: Détection des marqueurs d'urgence"""
        test_messages = [
            ("I need help ASAP!", True),
            ("This is urgent!!", True),
            ("Emergency!! Please respond now", True),
            ("Can you help when you have time?", False),
        ]
        
        logger.info("\n" + "="*60)
        logger.info("🧪 TEST: Urgency Detection")
        logger.info("="*60)
        
        for message, expected_urgency in test_messages:
            ctx = auto_responder.classify_message(message)
            
            is_correct = ctx.has_urgency_markers == expected_urgency
            status = "✅ PASS" if is_correct else "❌ FAIL"
            
            logger.info(f"{status} | '{message}'")
            logger.info(f"   → Urgency: {ctx.has_urgency_markers}")
            
            if is_correct:
                self.passed += 1
            else:
                self.failed += 1
    
    def test_sentiment_detection(self):
        """Test: Détection du sentiment"""
        test_messages = [
            ("Thanks so much! You're awesome! 😊", "positive"),
            ("This is terrible and I hate it 😠", "negative"),
            ("Let me know when you're ready", "neutral"),
        ]
        
        logger.info("\n" + "="*60)
        logger.info("🧪 TEST: Sentiment Detection")
        logger.info("="*60)
        
        for message, expected_sentiment in test_messages:
            ctx = auto_responder.classify_message(message)
            
            is_correct = ctx.estimated_sentiment == expected_sentiment
            status = "✅ PASS" if is_correct else "❌ FAIL"
            
            logger.info(f"{status} | '{message}'")
            logger.info(f"   → Sentiment: {ctx.estimated_sentiment}")
            
            if is_correct:
                self.passed += 1
            else:
                self.failed += 1
    
    def test_auto_respond_decision(self):
        """Test: Décision d'auto-respond"""
        test_cases = [
            {
                "message": "/help",
                "user_premium": True,
                "should_respond": True,
                "priority": ResponsePriority.IMMEDIATE
            },
            {
                "message": "Hello there!",
                "user_premium": False,
                "should_respond": True,
                "priority": ResponsePriority.IMMEDIATE
            },
            {
                "message": "What is Bitcoin?",
                "user_premium": False,
                "should_respond": True,
                "priority": ResponsePriority.HIGH
            },
            {
                "message": "Thanks for helping!",
                "user_premium": False,
                "should_respond": True,
                "priority": ResponsePriority.LOW
            },
        ]
        
        logger.info("\n" + "="*60)
        logger.info("🧪 TEST: Auto-Respond Decision")
        logger.info("="*60)
        
        for test in test_cases:
            message = test["message"]
            user_ctx = UserContext(
                user_id=12345,
                is_premium=test["user_premium"]
            )
            
            msg_ctx = auto_responder.classify_message(message)
            should_respond, priority, reason = auto_responder.should_auto_respond(
                msg_ctx,
                user_ctx,
                conversation_history=[]
            )
            
            is_correct = should_respond == test["should_respond"]
            status = "✅ PASS" if is_correct else "❌ FAIL"
            
            logger.info(f"{status} | '{message}'")
            logger.info(f"   → Should respond: {should_respond}, Priority: {priority.name}")
            logger.info(f"   → Reason: {reason}")
            
            if is_correct:
                self.passed += 1
            else:
                self.failed += 1
    
    def test_response_generation(self):
        """Test: Génération de réponses contextualisées"""
        test_cases = [
            {
                "message": "Hello!",
                "user_premium": True,
                "expected_contains": ["Hello", "help"]
            },
            {
                "message": "/help",
                "user_premium": False,
                "expected_contains": ["/", "help", "commands"]
            },
            {
                "message": "HELP ASAP!!",
                "user_premium": False,
                "expected_contains": ["urgent", "Urgent"]
            },
        ]
        
        logger.info("\n" + "="*60)
        logger.info("🧪 TEST: Response Generation")
        logger.info("="*60)
        
        for test in test_cases:
            message = test["message"]
            user_ctx = UserContext(
                user_id=12345,
                is_premium=test["user_premium"]
            )
            
            msg_ctx = auto_responder.classify_message(message)
            response = auto_responder.generate_contextual_response(
                msg_ctx,
                user_ctx,
                conversation_history=[]
            )
            
            logger.info(f"Message: '{message}'")
            logger.info(f"Response: {response}")
            logger.info("")
            
            self.passed += 1
    
    def test_crypto_detection(self):
        """Test: Détection de sujets crypto"""
        test_messages = [
            ("What's the price of Bitcoin right now?", ["bitcoin", "btc", "crypto"]),
            ("Is Ethereum a good investment?", ["ethereum", "eth", "crypto"]),
            ("Tell me about blockchain technology", ["blockchain", "crypto"]),
        ]
        
        logger.info("\n" + "="*60)
        logger.info("🧪 TEST: Crypto Topic Detection")
        logger.info("="*60)
        
        for message, expected_keywords in test_messages:
            ctx = auto_responder.classify_message(message)
            
            has_keywords = any(kw in message.lower() for kw in expected_keywords)
            status = "✅ PASS" if has_keywords else "❌ FAIL"
            
            logger.info(f"{status} | '{message}'")
            logger.info(f"   → Keywords found: {ctx.keywords_found}")
            
            if has_keywords:
                self.passed += 1
            else:
                self.failed += 1
    
    def test_pattern_summary(self):
        """Test: Résumé des patterns"""
        logger.info("\n" + "="*60)
        logger.info("🧪 TEST: Pattern Summary")
        logger.info("="*60)
        
        summary = auto_responder.get_patterns_summary()
        
        logger.info(f"Total patterns: {summary['total']}")
        logger.info(f"Active patterns: {summary['active']}")
        logger.info(f"Inactive patterns: {summary['inactive']}")
        logger.info(f"\nPattern breakdown:")
        
        for pattern_id, pattern_info in summary['patterns'].items():
            status = "✅" if pattern_info['enabled'] else "❌"
            logger.info(f"  {status} {pattern_id}: {pattern_info['description']}")
        
        self.passed += 1
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        logger.info("\n" + "="*70)
        logger.info("🚀 RUNNING AUTO-RESPONSE INTELLIGENT SYSTEM TESTS")
        logger.info("="*70)
        
        self.test_greeting_detection()
        self.test_question_detection()
        self.test_command_detection()
        self.test_urgency_detection()
        self.test_sentiment_detection()
        self.test_auto_respond_decision()
        self.test_response_generation()
        self.test_crypto_detection()
        self.test_pattern_summary()
        
        # Summary
        logger.info("\n" + "="*70)
        logger.info("📊 TEST SUMMARY")
        logger.info("="*70)
        logger.info(f"✅ Passed: {self.passed}")
        logger.info(f"❌ Failed: {self.failed}")
        logger.info(f"📈 Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        logger.info("="*70 + "\n")
        
        return self.failed == 0


if __name__ == "__main__":
    tester = TestAutoResponses()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)
