"""SQLAlchemy models for ORACLE"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON
from core.database import Base

class User(Base):
    """Telegram user"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(Base):
    """Telegram message log"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(Integer, index=True)
    message_id = Column(Integer)
    content = Column(Text)
    message_type = Column(String(50))  # "user_msg", "ai_response", "system"
    model_used = Column(String(50), nullable=True)  # haiku, sonnet, opus
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class AITask(Base):
    """AI processing task"""
    __tablename__ = "ai_tasks"
    
    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(Integer, index=True)
    task_type = Column(String(100))  # "classify", "generate", "analyze"
    input_text = Column(Text)
    output_text = Column(Text, nullable=True)
    model_used = Column(String(50))
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class AirdropTracker(Base):
    """Airdrop opportunity tracker"""
    __tablename__ = "airdrop_tracker"
    
    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(Integer, index=True)
    project_name = Column(String(255))
    token_symbol = Column(String(50))
    estimated_value = Column(Float, nullable=True)
    status = Column(String(50))  # "eligible", "pending", "claimed", "missed"
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemLog(Base):
    """System logs & events"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True)
    level = Column(String(20))  # INFO, WARNING, ERROR, DEBUG
    component = Column(String(100))  # telegram_bot, ai_engine, database, etc
    message = Column(Text)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class Cache(Base):
    """Cache storage for expensive operations"""
    __tablename__ = "cache"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(255), unique=True, index=True)
    value = Column(JSON)
    ttl = Column(Integer)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

class AutoResponse(Base):
    """Auto-response patterns configuration"""
    __tablename__ = "auto_responses"
    
    id = Column(Integer, primary_key=True)
    pattern_id = Column(String(100), unique=True, index=True)
    regex = Column(String(500))
    message_type = Column(String(50))  # greeting, question, command, etc
    description = Column(String(255))
    response_template = Column(Text)
    priority = Column(Integer)  # 1=immediate, 2=high, 3=medium, 4=low, 5=defer
    keywords = Column(JSON)  # List of keywords
    requires_context = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    min_confidence = Column(Float, default=0.7)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AutoResponseStat(Base):
    """Statistics for auto-responses"""
    __tablename__ = "auto_response_stats"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    pattern_id = Column(String(100), index=True)
    message_content = Column(Text)
    response_content = Column(Text)
    was_accepted = Column(Boolean, nullable=True)  # True/False/None (pending)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    feedback = Column(String(500), nullable=True)

class TweetModel(Base):
    """Scraped tweets from crypto news"""
    __tablename__ = "tweets"
    
    id = Column(Integer, primary_key=True)
    external_id = Column(String(255), unique=True, index=True)
    author = Column(String(255))
    content = Column(Text)
    url = Column(String(500), unique=True, index=True)
    posted_at = Column(DateTime, index=True)
    source = Column(String(50))  # "rss", "web_scrape", "api"
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    keywords = Column(JSON)  # List of keywords found
    indexed_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AirdropModel(Base):
    """Active airdrop opportunities"""
    __tablename__ = "airdrops"
    
    id = Column(Integer, primary_key=True)
    external_id = Column(String(255), unique=True, index=True)
    project_name = Column(String(255), index=True)
    token_symbol = Column(String(50), index=True)
    description = Column(Text)
    url = Column(String(500))
    status = Column(String(50), default="active")  # active, pending, closed, claimed
    estimated_value = Column(Float, nullable=True)
    requirements = Column(JSON)  # List of requirements
    ends_at = Column(DateTime, nullable=True, index=True)
    source = Column(String(100))  # web, rss, explorer, api
    discovered_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
