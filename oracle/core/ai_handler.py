"""
AI Handler - Message processing pipeline
Récupère les messages depuis la DB et les traite avec Claude API
"""
import logging
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from anthropic import Anthropic
from core.config import settings
from core.models import Message, AITask, SystemLog, User
from core.auto_responses import auto_responder, UserContext, ResponsePriority

logger = logging.getLogger(__name__)

class AIHandler:
    """Main AI Handler - processes messages with Claude"""
    
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.system_prompt = """You are ORACLE, an AI-powered crypto intelligence and personal brand automation assistant.
Your role is to:
1. Provide thoughtful analysis and insights
2. Classify messages intelligently
3. Generate quality responses
4. Help with personal branding and crypto strategy

Be concise, insightful, and actionable. Focus on crypto, personal branding, and intelligence gathering."""
        
        # Initialize auto-responder
        logger.info("🔄 Loading auto-response patterns...")
        # Patterns are already initialized in auto_responses.py
    
    def process_message_with_auto_response(
        self,
        db: Session,
        message: Message,
        user: User = None
    ) -> dict:
        """
        Essaie d'abord une auto-response intelligente avant Claude
        
        Retourne: {
            "type": "auto_response" ou "ai_generated",
            "response": texte,
            "pattern_id": si auto_response,
            "confidence": confiance du match,
            "tokens": 0 pour auto, estimé pour Claude
        }
        """
        try:
            # Charge user context
            if not user:
                user = db.query(User).filter(User.telegram_id == message.telegram_user_id).first()
            
            user_ctx = UserContext(
                user_id=message.telegram_user_id,
                is_premium=user.is_premium if user else False,
                message_count=db.query(Message).filter(
                    Message.telegram_user_id == message.telegram_user_id
                ).count(),
                last_interaction=user.updated_at if user else None,
                language_preference=getattr(user, 'language_preference', 'en') if user else 'en'
            )
            
            # Classify message
            message_ctx = auto_responder.classify_message(message.content)
            
            # Get conversation history
            conversation = db.query(Message).filter(
                Message.telegram_user_id == message.telegram_user_id
            ).order_by(Message.created_at.desc()).limit(10).all()
            message_ctx.conversation_length = len(conversation)
            
            # Décide si auto-respond
            should_respond, priority, reason = auto_responder.should_auto_respond(
                message_ctx,
                user_ctx,
                conversation
            )
            
            logger.info(f"📊 Message classification: type={message_ctx.detected_type.value}, "
                       f"confidence={message_ctx.confidence:.2f}, "
                       f"should_respond={should_respond}, priority={priority.name}")
            
            if should_respond and message_ctx.confidence >= 0.7:
                # Génère auto-response
                pattern = None
                for p in auto_responder.patterns.values():
                    if p.enabled:
                        match, conf = p.match(message.content)
                        if match and conf >= message_ctx.confidence:
                            pattern = p
                            break
                
                if pattern:
                    response = auto_responder.generate_contextual_response(
                        message_ctx,
                        user_ctx,
                        pattern,
                        conversation
                    )
                    
                    # Log stat
                    auto_responder.record_auto_response_stat(
                        db,
                        user_id=message.telegram_user_id,
                        pattern_id=pattern.pattern_id,
                        message_content=message.content,
                        response_content=response
                    )
                    
                    logger.info(f"✅ Auto-response triggered: {pattern.pattern_id}")
                    
                    return {
                        "type": "auto_response",
                        "response": response,
                        "pattern_id": pattern.pattern_id,
                        "confidence": message_ctx.confidence,
                        "priority": priority.name,
                        "tokens": 0,
                        "reason": reason
                    }
            
            # Fallback à Claude pour réponse plus complexe
            logger.info(f"⚠️ No suitable auto-response, delegating to Claude (reason: {reason})")
            
            result = self.process_message_with_claude(
                message.content,
                user_id=message.telegram_user_id
            )
            
            result["type"] = "ai_generated"
            result["reason"] = "No auto-response pattern matched"
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Error in auto-response processing: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to Claude
            return {
                "type": "ai_generated",
                "response": "I encountered an issue processing your message. Let me get back to you shortly.",
                "reason": f"Error: {str(e)}"
            }
    
    def get_unprocessed_messages(self, db: Session, limit: int = 10) -> list:
        """
        Récupère les messages non traités depuis la DB
        Filtre: type='user_msg', aucune réponse IA associée
        """
        try:
            messages = db.query(Message).filter(
                Message.message_type == "user_msg",
                Message.model_used.is_(None)  # Not yet processed
            ).order_by(Message.created_at.asc()).limit(limit).all()
            
            logger.info(f"📨 Retrieved {len(messages)} unprocessed messages from DB")
            return messages
        except Exception as e:
            logger.error(f"❌ Error fetching messages: {e}")
            return []
    
    def process_message_with_claude(
        self, 
        message_content: str, 
        user_id: int = None,
        model: str = "haiku"
    ) -> dict:
        """
        Traite un message avec Claude API
        Retourne: {status, response, model, tokens, cost}
        """
        try:
            # Select model based on complexity heuristic
            if len(message_content) > 500 or any(keyword in message_content.lower() 
                for keyword in ["analyze", "strategy", "complex", "research"]):
                selected_model = settings.CLAUDE_MODEL_SONNET
            else:
                selected_model = settings.CLAUDE_MODEL_HAIKU
            
            logger.info(f"🤖 Processing with {selected_model}...")
            
            # Prepare prompt with system context
            full_prompt = f"{self.system_prompt}\n\nUser Message:\n{message_content}"
            
            # Call Claude API using completions (for compatibility)
            try:
                # Try modern messages API first (claude-3.5+)
                response = self.client.messages.create(
                    model=selected_model,
                    max_tokens=1024,
                    system=self.system_prompt,
                    messages=[{
                        "role": "user",
                        "content": message_content
                    }]
                )
                
                # Extract response
                ai_response = response.content[0].text
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                
            except AttributeError:
                # Fallback to completions API
                response = self.client.completions.create(
                    model=selected_model,
                    max_tokens_to_sample=1024,
                    prompt=full_prompt
                )
                
                # Extract response
                ai_response = response.completion
                tokens_used = response.stop_reason == "max_tokens" and 1024 or len(ai_response.split())
                input_tokens = tokens_used // 2
                output_tokens = tokens_used // 2
            
            # Estimate cost (rough)
            cost = self._estimate_cost(selected_model, tokens_used)
            
            logger.info(f"✅ Response generated ({tokens_used} tokens, ~€{cost:.4f})")
            
            return {
                "status": "success",
                "response": ai_response,
                "model": selected_model,
                "tokens": tokens_used,
                "cost": cost,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
        
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "response": None,
                "model": None,
                "tokens": 0,
                "cost": 0,
                "error": str(e)
            }
    
    def _estimate_cost(self, model: str, tokens: int) -> float:
        """
        Estime le coût en euros basé sur le modèle et tokens
        Tarifs Claude 3.5 (input/output tokens):
        - Haiku: €0.0000008 / €0.0000024
        - Sonnet: €0.000003 / €0.000015
        - Opus: €0.000015 / €0.000075
        """
        if "haiku" in model:
            cost = tokens * 0.000001  # Average
        elif "sonnet" in model:
            cost = tokens * 0.000009  # Average
        elif "opus" in model:
            cost = tokens * 0.000045  # Average
        else:
            cost = 0
        
        return cost
    
    def save_ai_response(
        self, 
        db: Session,
        original_message_id: int,
        user_id: int,
        response_text: str,
        model: str,
        tokens: int
    ) -> Message:
        """
        Sauvegarde la réponse IA dans la DB
        Crée un nouveau message avec type='ai_response'
        Met à jour le message original avec model_used
        """
        try:
            # Update original message with model used
            original_msg = db.query(Message).filter(Message.id == original_message_id).first()
            if original_msg:
                original_msg.model_used = model
                original_msg.tokens_used = tokens
            
            # Create new message for AI response
            ai_message = Message(
                telegram_user_id=user_id,
                message_id=0,  # Placeholder - will be set when sent via Telegram
                content=response_text,
                message_type="ai_response",
                model_used=model,
                tokens_used=tokens
            )
            
            db.add(ai_message)
            db.commit()
            db.refresh(ai_message)
            
            logger.info(f"💾 AI response saved to DB (ID: {ai_message.id})")
            return ai_message
        
        except Exception as e:
            logger.error(f"❌ Error saving AI response: {e}")
            db.rollback()
            return None
    
    def log_system_event(
        self,
        db: Session,
        level: str,
        component: str,
        message: str,
        meta: dict = None
    ) -> SystemLog:
        """
        Enregistre un événement système dans la DB
        """
        try:
            log_entry = SystemLog(
                level=level,
                component=component,
                message=message,
                meta=meta or {}
            )
            db.add(log_entry)
            db.commit()
            return log_entry
        except Exception as e:
            logger.error(f"❌ Error logging system event: {e}")
            return None
    
    def process_message_batch(
        self,
        db: Session,
        limit: int = 10,
        auto_respond: bool = False
    ) -> dict:
        """
        Traite un batch de messages non traités
        auto_respond: Si True, crée une tâche pour envoyer la réponse via Telegram
        
        Retour: {
            "total": nombre,
            "processed": nombre traité,
            "failed": nombre échoué,
            "tokens_total": tokens utilisés,
            "cost_total": coût total
        }
        """
        logger.info("🔄 Starting batch message processing...")
        
        unprocessed = self.get_unprocessed_messages(db, limit)
        
        if not unprocessed:
            logger.info("✅ No unprocessed messages to handle")
            return {
                "total": 0,
                "processed": 0,
                "failed": 0,
                "tokens_total": 0,
                "cost_total": 0
            }
        
        stats = {
            "total": len(unprocessed),
            "processed": 0,
            "failed": 0,
            "tokens_total": 0,
            "cost_total": 0,
            "details": []
        }
        
        for msg in unprocessed:
            try:
                logger.info(f"📝 Processing message {msg.id}: {msg.content[:50]}...")
                
                # Process with Claude
                result = self.process_message_with_claude(
                    msg.content,
                    user_id=msg.telegram_user_id
                )
                
                if result["status"] == "success":
                    # Save response
                    ai_response = self.save_ai_response(
                        db=db,
                        original_message_id=msg.id,
                        user_id=msg.telegram_user_id,
                        response_text=result["response"],
                        model=result["model"],
                        tokens=result["tokens"]
                    )
                    
                    if ai_response:
                        stats["processed"] += 1
                        stats["tokens_total"] += result["tokens"]
                        stats["cost_total"] += result["cost"]
                        
                        stats["details"].append({
                            "message_id": msg.id,
                            "user_id": msg.telegram_user_id,
                            "model": result["model"],
                            "tokens": result["tokens"],
                            "cost": result["cost"],
                            "status": "✅ processed"
                        })
                        
                        # Log success
                        self.log_system_event(
                            db=db,
                            level="INFO",
                            component="ai_handler",
                            message=f"Message {msg.id} processed successfully",
                            meta={
                                "message_id": msg.id,
                                "model": result["model"],
                                "tokens": result["tokens"]
                            }
                        )
                else:
                    stats["failed"] += 1
                    stats["details"].append({
                        "message_id": msg.id,
                        "status": "❌ failed",
                        "error": result.get("error", "Unknown error")
                    })
                    
                    # Log error
                    self.log_system_event(
                        db=db,
                        level="ERROR",
                        component="ai_handler",
                        message=f"Failed to process message {msg.id}: {result.get('error')}",
                        meta={"message_id": msg.id}
                    )
            
            except Exception as e:
                stats["failed"] += 1
                logger.error(f"❌ Batch processing error for message {msg.id}: {e}")
                stats["details"].append({
                    "message_id": msg.id,
                    "status": "❌ exception",
                    "error": str(e)
                })
        
        # Final summary
        logger.info(f"✅ Batch processing complete: {stats['processed']} processed, {stats['failed']} failed")
        logger.info(f"📊 Total tokens: {stats['tokens_total']}, Cost: €{stats['cost_total']:.4f}")
        
        return stats


# Global instance
ai_handler = AIHandler()
