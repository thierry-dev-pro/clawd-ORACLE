"""
Admin API - Endpoints pour gérer les auto-responses
Permet la configuration, monitoring et gestion des patterns
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import get_db
from core.auto_responses import (
    auto_responder, ResponsePattern, MessageType, ResponsePriority
)
from core.models import AutoResponse, AutoResponseStat

logger = logging.getLogger(__name__)

# Pydantic models
class ResponsePatternCreate(BaseModel):
    pattern_id: str
    regex: str
    message_type: str
    description: str
    response_template: str
    priority: int = 3
    keywords: List[str] = []
    requires_context: bool = False
    min_confidence: float = 0.7
    enabled: bool = True


class ResponsePatternUpdate(BaseModel):
    description: Optional[str] = None
    response_template: Optional[str] = None
    priority: Optional[int] = None
    keywords: Optional[List[str]] = None
    enabled: Optional[bool] = None
    min_confidence: Optional[float] = None


class AutoResponseStatResponse(BaseModel):
    id: int
    user_id: int
    pattern_id: str
    message_content: str
    response_content: str
    was_accepted: Optional[bool]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Router
router = APIRouter(prefix="/admin/auto-responses", tags=["admin"])


@router.get("/patterns")
async def list_patterns(
    enabled_only: bool = Query(False),
    db: Session = Depends(get_db)
) -> Dict:
    """Liste tous les patterns de auto-response"""
    try:
        patterns = []
        for pattern_id, pattern in auto_responder.patterns.items():
            if enabled_only and not pattern.enabled:
                continue
            
            patterns.append({
                "pattern_id": pattern.pattern_id,
                "description": pattern.description,
                "message_type": pattern.message_type.value,
                "priority": pattern.priority.name,
                "enabled": pattern.enabled,
                "keywords": pattern.keywords,
                "min_confidence": pattern.min_confidence,
                "requires_context": pattern.requires_context
            })
        
        return {
            "total": len(patterns),
            "patterns": patterns
        }
    except Exception as e:
        logger.error(f"Error listing patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/{pattern_id}")
async def get_pattern(pattern_id: str) -> Dict:
    """Récupère les détails d'un pattern"""
    try:
        if pattern_id not in auto_responder.patterns:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        pattern = auto_responder.patterns[pattern_id]
        
        return {
            "pattern_id": pattern.pattern_id,
            "regex": pattern.regex,
            "description": pattern.description,
            "message_type": pattern.message_type.value,
            "response_template": pattern.response_template,
            "priority": pattern.priority.name,
            "keywords": pattern.keywords,
            "requires_context": pattern.requires_context,
            "enabled": pattern.enabled,
            "min_confidence": pattern.min_confidence
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/patterns")
async def create_pattern(
    pattern_data: ResponsePatternCreate,
    db: Session = Depends(get_db)
) -> Dict:
    """Crée un nouveau pattern"""
    try:
        # Validate pattern_id uniqueness
        if pattern_data.pattern_id in auto_responder.patterns:
            raise HTTPException(status_code=409, detail="Pattern ID already exists")
        
        # Create pattern object
        pattern = ResponsePattern(
            pattern_id=pattern_data.pattern_id,
            regex=pattern_data.regex,
            message_type=MessageType(pattern_data.message_type),
            description=pattern_data.description,
            response_template=pattern_data.response_template,
            priority=ResponsePriority(pattern_data.priority),
            keywords=pattern_data.keywords,
            requires_context=pattern_data.requires_context,
            enabled=pattern_data.enabled,
            min_confidence=pattern_data.min_confidence
        )
        
        # Add to responder
        auto_responder.add_pattern(pattern)
        
        # Save to DB
        auto_responder.save_patterns_to_db(db, overwrite=True)
        
        logger.info(f"✅ Pattern created: {pattern_data.pattern_id}")
        
        return {
            "status": "created",
            "pattern_id": pattern_data.pattern_id,
            "message": f"Pattern {pattern_data.pattern_id} created successfully"
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/patterns/{pattern_id}")
async def update_pattern(
    pattern_id: str,
    pattern_data: ResponsePatternUpdate,
    db: Session = Depends(get_db)
) -> Dict:
    """Met à jour un pattern existant"""
    try:
        if pattern_id not in auto_responder.patterns:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        pattern = auto_responder.patterns[pattern_id]
        
        # Update fields
        if pattern_data.description is not None:
            pattern.description = pattern_data.description
        if pattern_data.response_template is not None:
            pattern.response_template = pattern_data.response_template
        if pattern_data.priority is not None:
            pattern.priority = ResponsePriority(pattern_data.priority)
        if pattern_data.keywords is not None:
            pattern.keywords = pattern_data.keywords
        if pattern_data.enabled is not None:
            pattern.enabled = pattern_data.enabled
        if pattern_data.min_confidence is not None:
            pattern.min_confidence = pattern_data.min_confidence
        
        # Save to DB
        auto_responder.save_patterns_to_db(db, overwrite=True)
        
        logger.info(f"✅ Pattern updated: {pattern_id}")
        
        return {
            "status": "updated",
            "pattern_id": pattern_id,
            "message": f"Pattern {pattern_id} updated successfully"
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/patterns/{pattern_id}")
async def delete_pattern(pattern_id: str) -> Dict:
    """Désactive un pattern"""
    try:
        if not auto_responder.remove_pattern(pattern_id):
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        logger.info(f"✅ Pattern disabled: {pattern_id}")
        
        return {
            "status": "deleted",
            "pattern_id": pattern_id,
            "message": f"Pattern {pattern_id} disabled successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
) -> Dict:
    """Récupère les statistiques des auto-responses"""
    try:
        stats = auto_responder.get_response_stats(db, days=days)
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/pattern/{pattern_id}")
async def get_pattern_stats(
    pattern_id: str,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
) -> Dict:
    """Récupère les statistiques d'un pattern spécifique"""
    try:
        if pattern_id not in auto_responder.patterns:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        from datetime import timedelta
        since = datetime.utcnow() - timedelta(days=days)
        
        stats = db.query(AutoResponseStat).filter(
            AutoResponseStat.pattern_id == pattern_id,
            AutoResponseStat.created_at >= since
        ).all()
        
        total = len(stats)
        accepted = sum(1 for s in stats if s.was_accepted == True)
        rejected = sum(1 for s in stats if s.was_accepted == False)
        pending = sum(1 for s in stats if s.was_accepted is None)
        
        return {
            "pattern_id": pattern_id,
            "period_days": days,
            "total_responses": total,
            "accepted": accepted,
            "rejected": rejected,
            "pending": pending,
            "acceptance_rate": (accepted / total * 100) if total > 0 else 0.0,
            "recent_samples": [
                {
                    "id": s.id,
                    "user_id": s.user_id,
                    "message": s.message_content[:100],
                    "response": s.response_content[:100],
                    "was_accepted": s.was_accepted,
                    "created_at": s.created_at
                }
                for s in stats[-5:]
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pattern stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/patterns/reload")
async def reload_patterns(
    db: Session = Depends(get_db)
) -> Dict:
    """Recharge les patterns depuis la DB"""
    try:
        initial_count = len(auto_responder.patterns)
        auto_responder.patterns.clear()
        loaded = auto_responder.load_patterns_from_db(db)
        
        return {
            "status": "reloaded",
            "patterns_before": initial_count,
            "patterns_loaded": loaded,
            "message": f"Reloaded {loaded} patterns from database"
        }
    except Exception as e:
        logger.error(f"Error reloading patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/patterns/sync")
async def sync_patterns(
    db: Session = Depends(get_db)
) -> Dict:
    """Synchronise les patterns en mémoire vers la DB"""
    try:
        count = auto_responder.save_patterns_to_db(db, overwrite=True)
        
        return {
            "status": "synced",
            "patterns_synced": count,
            "message": f"Synced {count} patterns to database"
        }
    except Exception as e:
        logger.error(f"Error syncing patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stats/feedback/{stat_id}")
async def update_feedback(
    stat_id: int,
    was_accepted: bool,
    feedback: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict:
    """Enregistre le feedback utilisateur sur une auto-response"""
    try:
        stat = db.query(AutoResponseStat).filter(
            AutoResponseStat.id == stat_id
        ).first()
        
        if not stat:
            raise HTTPException(status_code=404, detail="Stat not found")
        
        stat.was_accepted = was_accepted
        if feedback:
            stat.feedback = feedback
        
        db.commit()
        
        logger.info(f"✅ Feedback recorded for stat {stat_id}: accepted={was_accepted}")
        
        return {
            "status": "recorded",
            "stat_id": stat_id,
            "was_accepted": was_accepted,
            "message": "Feedback recorded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_summary(db: Session = Depends(get_db)) -> Dict:
    """Récupère un résumé du système d'auto-responses"""
    try:
        patterns_summary = auto_responder.get_patterns_summary()
        stats = auto_responder.get_response_stats(db, days=7)
        
        return {
            "patterns": patterns_summary,
            "recent_stats": stats,
            "system_status": "operational",
            "last_sync": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
